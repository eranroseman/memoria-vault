#Requires -Version 5.1
<#
.SYNOPSIS
    Memoria bootstrap -- native Windows production installer.

.DESCRIPTION
    Production Windows installs run Hermes natively on Windows. The Linux
    installer (scripts/install.sh) remains the testing/WSL path.

    This script:
      1. Guides Windows GUI app installation with winget.
      2. Runs the official native Hermes installer.
      3. Copies src/ into the runtime vault.
      4. Creates the vault-local MCP venv.
      5. Installs the five Hermes profiles with native Windows paths.
      6. Deploys the fail-closed policy-gate plugin per profile.
      7. Wires the deterministic Hermes cron wrappers.

.PARAMETER Vault
    Windows folder for the runtime vault. Default: $env:USERPROFILE\Memoria
    (deliberately outside OneDrive).

.PARAMETER ProfilesOnly
    Skip repo/vault/bootstrap work; just redeploy profile config, profile .env
    values, the policy plugin, and cron wrappers from an existing vault.

.PARAMETER Only
    Restrict the profile step to these profiles. Pairs with -ProfilesOnly.

.PARAMETER NoApps
    Skip Obsidian/Zotero/Git winget guidance.

.PARAMETER DryRun
    Print commands without changing the machine where practical.

.PARAMETER Yes
    Non-interactive: accept defaults and run guided installs.
#>
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '')]
[CmdletBinding()]
param(
    [string]$Vault = (Join-Path $env:USERPROFILE 'Memoria'),
    [string[]]$Only,
    [switch]$ProfilesOnly,
    [switch]$NoApps,
    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

$RepoUrl = 'https://github.com/eranroseman/memoria-vault.git'
$RawHermesInstall = 'https://hermes-agent.nousresearch.com/install.ps1'
$HermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$HermesProfilesDir = Join-Path $HermesHome 'profiles'
$HermesScriptsDir = Join-Path $HermesHome 'scripts'
$HermesExe = $null
$HermesArgsPrefix = @()
$AllProfiles = @('memoria-copi', 'memoria-librarian', 'memoria-writer', 'memoria-peer-reviewer', 'memoria-engineer')
$RequiredFiles = @('SOUL.md', 'config.yaml', 'distribution.yaml')
$VenvPython = $null
$MemoriaEnv = if ($env:MEMORIA_ENV) { $env:MEMORIA_ENV } else { 'prod' }

function Write-Line { param([string]$Message) Write-Host $Message }
function Write-Header { param([string]$Message) Write-Host "`n== $Message ==" -ForegroundColor Cyan }
function Write-Ok { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "[!] $Message" -ForegroundColor Yellow }
function Stop-Install { param([string]$Message) Write-Host "[X] $Message" -ForegroundColor Red; exit 1 }

function Invoke-Logged {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$ArgumentList = @()
    )
    Write-Line ("  + {0} {1}" -f $FilePath, ($ArgumentList -join ' '))
    if ($DryRun) { return }
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        Stop-Install "$FilePath exited with code $LASTEXITCODE."
    }
}

function Invoke-Robocopy {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination,
        [string[]]$ExtraArgs = @()
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $copyArgs = @($Source, $Destination, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP') + $ExtraArgs
    Write-Line ("  + robocopy {0}" -f ($copyArgs -join ' '))
    if ($DryRun) { return }
    & robocopy @copyArgs | Out-Null
    if ($LASTEXITCODE -gt 7) {
        Stop-Install "robocopy failed with code $LASTEXITCODE."
    }
}

function Install-WingetApp {
    param([string]$Id, [string]$Name, [string]$Fallback)
    if ($NoApps) { return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Warn "winget not found -- install $Name manually: $Fallback"
        return
    }
    $present = (& winget list --id $Id -e) | Select-String -SimpleMatch $Id -Quiet
    if ($present) { Write-Ok "$Name present"; return }
    Write-Line "$Name is not installed. Command: winget install --id $Id -e"
    $go = $Yes
    if (-not $Yes) { $go = ((Read-Host "Install $Name now via winget? [y/N]") -match '^[Yy]') }
    if ($go) {
        $wingetArgs = @('install', '--id', $Id, '-e', '--source', 'winget', '--accept-package-agreements', '--accept-source-agreements')
        Write-Line ("  + winget {0}" -f ($wingetArgs -join ' '))
        if (-not $DryRun) {
            & winget @wingetArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Warn "winget could not install $Name (exit $LASTEXITCODE). Continue, then install manually if you need it: $Fallback"
            }
        }
    } else {
        Write-Line "  Skipped. Install later: $Fallback"
    }
}

function Assert-RequiredCommands {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Install 'Git is required on PATH. Install Git for Windows, open a new PowerShell so PATH refreshes, then rerun the installer.'
    }
}

function Get-RepoRoot {
    if ($PSCommandPath) {
        $scriptRoot = Split-Path -Parent $PSCommandPath
        $localRoot = Split-Path -Parent $scriptRoot
        if (Test-Path (Join-Path $localRoot 'src/.memoria/profiles')) {
            return $localRoot
        }
    }
    $work = Join-Path $env:TEMP ('memoria-vault-' + [guid]::NewGuid().ToString('N'))
    Invoke-Logged -FilePath 'git' -ArgumentList @('clone', '--depth', '1', $RepoUrl, $work)
    return $work
}

function Get-LocalRepoRoot {
    if ($PSCommandPath) {
        $scriptRoot = Split-Path -Parent $PSCommandPath
        $localRoot = Split-Path -Parent $scriptRoot
        if (Test-Path (Join-Path $localRoot 'src/.obsidian')) {
            return $localRoot
        }
    }
    return $null
}

function Get-CommandPath {
    param([string[]]$Candidates)
    foreach ($candidate in $Candidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
        if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
    }
    return $null
}

function Resolve-HermesExe {
    $script:HermesArgsPrefix = @()
    $hermes = Get-CommandPath @('hermes.exe', 'hermes.cmd', 'hermes', (Join-Path $HermesHome 'bin/hermes.exe'), (Join-Path $HermesHome 'bin/hermes.cmd'))
    if ($hermes) {
        return $hermes
    }

    $uv = Get-CommandPath @((Join-Path $HermesHome 'bin/uv.exe'), 'uv.exe')
    $project = Join-Path $HermesHome 'hermes-agent'
    if ($uv -and (Test-Path (Join-Path $project 'pyproject.toml'))) {
        $script:HermesArgsPrefix = @('run', '--project', $project, '--extra', 'mcp', 'hermes')
        return $uv
    }

    return $null
}

function Install-Hermes {
    Write-Header 'Hermes native Windows runtime'
    $script:HermesExe = Resolve-HermesExe
    if ($script:HermesExe) {
        Write-Ok "Hermes command resolved via $script:HermesExe"
        return
    }
    $ps = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command',
        "& ([scriptblock]::Create((irm '$RawHermesInstall'))) -SkipSetup"
    )
    Invoke-Logged -FilePath 'powershell.exe' -ArgumentList $ps
    $script:HermesExe = Resolve-HermesExe
    if ($script:HermesExe) {
        Write-Ok "Hermes command resolved via $script:HermesExe"
    } else {
        Write-Warn 'Open a new PowerShell if hermes is still not on PATH; User PATH changes do not affect existing shells.'
    }
}

function Get-PythonForVenv {
    $uv = Get-CommandPath @((Join-Path $HermesHome 'bin/uv.exe'), 'uv.exe')
    if ($uv) {
        Invoke-Logged -FilePath $uv -ArgumentList @('python', 'install', '3.11')
        return [pscustomobject]@{ Exe = $uv; Prefix = @('run', '--python', '3.11', 'python') }
    }

    $python = Get-CommandPath @('py.exe', 'python.exe', 'python3.exe')
    if (-not $python) {
        Stop-Install 'No uv or Python launcher found. Rerun the Hermes installer or install Python 3.11+, then retry.'
    }
    if ((Split-Path -Leaf $python) -ieq 'py.exe') {
        return [pscustomobject]@{ Exe = $python; Prefix = @('-3.11') }
    }
    return [pscustomobject]@{ Exe = $python; Prefix = @() }
}

function Invoke-Python {
    param([pscustomobject]$PythonSpec, [string[]]$ArgumentList)
    $exe = $PythonSpec.Exe
    $prefix = @($PythonSpec.Prefix)
    Invoke-Logged -FilePath $exe -ArgumentList ($prefix + $ArgumentList)
}

function Copy-VaultSource {
    param([string]$RepoRoot)
    Write-Header 'Scaffold and populate vault'
    $src = Join-Path $RepoRoot 'src'
    if (-not (Test-Path $src)) { Stop-Install "Missing src tree at $src." }
    if (Test-Path (Join-Path $Vault '.memoria')) {
        Stop-Install "$Vault is already a Memoria vault. This installer is fresh-install only; choose an empty target or move the existing vault aside."
    }
    New-Item -ItemType Directory -Path $Vault -Force | Out-Null
    Invoke-Robocopy -Source $src -Destination $Vault -ExtraArgs @('/XD', '.git', '/XF', '.env', 'data.json', 'appearance.json')
    Write-Ok "Vault populated at $Vault"
}

function Enable-MemoriaCssSnippets {
    param([string]$RepoRoot)
    Write-Header 'Obsidian CSS snippets'
    $srcSnippets = if ($RepoRoot) { Join-Path $RepoRoot 'src/.obsidian/snippets' } else { Join-Path $Vault '.obsidian/snippets' }
    $dstSnippets = Join-Path $Vault '.obsidian/snippets'
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $dstSnippets -Force | Out-Null
    }
    foreach ($snippetFile in @('memoria-link-colors.css', 'memoria-property-badges.css')) {
        $srcFile = Join-Path $srcSnippets $snippetFile
        $dstFile = Join-Path $dstSnippets $snippetFile
        if ((Test-Path $srcFile) -and -not (Test-Path $dstFile)) {
            Write-Line "  + copy missing $snippetFile"
            if (-not $DryRun) { Copy-Item $srcFile $dstFile -Force }
        }
    }

    $appearance = Join-Path $Vault '.obsidian/appearance.json'
    if ($DryRun) {
        Write-Line "  + ensure enabledCssSnippets contains memoria-link-colors, memoria-property-badges in $appearance"
        return
    }
    $data = [ordered]@{}
    if (Test-Path $appearance) {
        try {
            $parsed = Get-Content -Raw -Path $appearance | ConvertFrom-Json
            foreach ($property in $parsed.PSObject.Properties) {
                $data[$property.Name] = $property.Value
            }
        } catch {
            Stop-Install "$appearance is not valid JSON. Fix it or remove it, then rerun the installer. $($_.Exception.Message)"
        }
    }
    $enabled = @()
    if ($data.Contains('enabledCssSnippets') -and $data['enabledCssSnippets']) {
        $enabled = @($data['enabledCssSnippets'])
    }
    foreach ($snippet in @('memoria-link-colors', 'memoria-property-badges')) {
        if ($enabled -notcontains $snippet) { $enabled += $snippet }
    }
    $data['enabledCssSnippets'] = $enabled
    New-Item -ItemType Directory -Path (Split-Path -Parent $appearance) -Force | Out-Null
    $data | ConvertTo-Json -Depth 10 | Set-Content -Path $appearance -Encoding UTF8
    Write-Ok 'Memoria CSS snippets enabled in .obsidian/appearance.json'
}

function Install-McpDeps {
    param([string]$RepoRoot)
    Write-Header 'MCP server dependencies'
    $reqs = Join-Path $Vault '.memoria/mcp/requirements.txt'
    $venv = Join-Path $Vault '.memoria/.venv'
    $script:VenvPython = Join-Path $venv 'Scripts/python.exe'
    if ($DryRun) {
        Write-Line "  + would create venv $venv and install $reqs plus Memoria from $RepoRoot"
        return
    }
    if (-not (Test-Path $reqs)) { Write-Warn "No requirements file at $reqs"; return }
    if (-not (Test-Path $script:VenvPython)) {
        $py = Get-PythonForVenv
        Invoke-Python -PythonSpec $py -ArgumentList @('-m', 'venv', $venv)
    }
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '-r', $reqs)
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', $RepoRoot)
    Write-Ok "MCP deps installed in $venv"
}

function ConvertTo-ForwardPath {
    param([string]$Path)
    return ($Path -replace '\\', '/')
}

function Get-ProfileModelDefault {
    param([string]$ProfileName)
    switch ($ProfileName) {
        { $_ -in @('memoria-copi', 'memoria-peer-reviewer') } { return '~anthropic/claude-opus-latest' }
        'memoria-writer' { return '~anthropic/claude-sonnet-latest' }
        { $_ -in @('memoria-librarian', 'memoria-engineer') } { return '~anthropic/claude-haiku-latest' }
        default { Stop-Install "Unknown profile for model overlay: $ProfileName" }
    }
}

function Get-ProfileModelOverlay {
    param([string]$ProfileName)
    switch ($script:MemoriaEnv) {
        { $_ -eq 'prod' -or $_ -eq '' } {
            return @{
                Provider = 'kilocode'
                BaseUrl = 'https://api.kilo.ai/api/gateway'
                Default = Get-ProfileModelDefault -ProfileName $ProfileName
                Context = ''
            }
        }
        'test' {
            $baseUrl = if ($env:MEMORIA_MODEL_BASE_URL) { $env:MEMORIA_MODEL_BASE_URL } else { 'http://127.0.0.1:11434/v1' }
            $modelName = if ($env:MEMORIA_MODEL_NAME) { $env:MEMORIA_MODEL_NAME } else { 'qwen2.5:7b' }
            $context = if ($env:MEMORIA_MODEL_CONTEXT_LENGTH) { $env:MEMORIA_MODEL_CONTEXT_LENGTH } else { '65536' }
            return @{
                Provider = 'custom'
                BaseUrl = $baseUrl
                Default = $modelName
                Context = "  context_length: $context`n  ollama_num_ctx: $context`n"
            }
        }
        default {
            Stop-Install "Unsupported MEMORIA_ENV=$script:MemoriaEnv (expected prod or test)."
        }
    }
}

function Set-TemplateValues {
    param([string]$Path, [string]$ProfileName = '')
    $text = Get-Content -Raw -Path $Path
    $py = if ($script:VenvPython) { ConvertTo-ForwardPath $script:VenvPython } else { 'python' }
    $vaultPath = ConvertTo-ForwardPath (Resolve-Path $Vault).Path
    $qmd = Get-CommandPath @('qmd.cmd', 'qmd.exe', 'qmd')
    if (-not $qmd) { $qmd = 'qmd' }
    $text = $text.Replace('{{PYTHON}}', $py)
    $text = $text.Replace('{{VAULT_PATH}}', $vaultPath)
    $text = $text.Replace('{{QMD}}', (ConvertTo-ForwardPath $qmd))
    $text = $text.Replace('{{PROFILE}}', $ProfileName)
    if ($ProfileName) {
        $model = Get-ProfileModelOverlay -ProfileName $ProfileName
        $text = $text.Replace('{{MODEL_PROVIDER}}', $model.Provider)
        $text = $text.Replace('{{MODEL_BASE_URL}}', $model.BaseUrl)
        $text = $text.Replace('{{MODEL_DEFAULT}}', $model.Default)
        $text = $text.Replace("  # {{MODEL_LOCAL_CONTEXT}}`n", $model.Context)
    }
    Set-Content -Path $Path -Value $text -NoNewline -Encoding UTF8
}

function Assert-ProfileObsidianMcpHttps {
    param([string]$ConfigPath, [string]$ProfileName)
    $text = Get-Content -Raw -Path $ConfigPath
    if ($text -notmatch 'url:\s*"https://127\.0\.0\.1:\$\{OBSIDIAN_MCP_PORT\}/mcp"') {
        Stop-Install "$ProfileName config.yaml must use https://127.0.0.1:`${OBSIDIAN_MCP_PORT}/mcp for the Obsidian MCP."
    }
    if ($text -notmatch 'ssl_verify:\s*"\$\{OBSIDIAN_MCP_SSL_VERIFY\}"') {
        Stop-Install "$ProfileName config.yaml must set obsidian ssl_verify to `${OBSIDIAN_MCP_SSL_VERIFY}."
    }
}

function Read-DotEnv {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path $Path)) { return $values }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $values[$Matches[1]] = $Matches[2].Trim()
        }
    }
    return $values
}

function Test-PlaceholderValue {
    param([string]$Value)
    if (-not $Value) { return $true }
    return ($Value -match '<[^>]+>' -or $Value -match '\\path\\to\\' -or $Value -match '(^|/)path/to/' -or $Value -match '^\.\.\.$')
}

function Assert-ObsidianMcpEnv {
    param([string]$ProfileDir)
    $envFile = Join-Path $ProfileDir '.env'
    $values = Read-DotEnv -Path $envFile
    $missing = @()
    foreach ($key in @('OBSIDIAN_API_KEY', 'OBSIDIAN_MCP_PORT', 'OBSIDIAN_MCP_SSL_VERIFY')) {
        if (-not $values.ContainsKey($key) -or (Test-PlaceholderValue -Value $values[$key])) {
            $missing += $key
        }
    }
    if ($values.ContainsKey('OBSIDIAN_MCP_SSL_VERIFY') -and -not (Test-PlaceholderValue -Value $values['OBSIDIAN_MCP_SSL_VERIFY'])) {
        if (-not (Test-Path $values['OBSIDIAN_MCP_SSL_VERIFY'])) {
            $missing += 'OBSIDIAN_MCP_SSL_VERIFY file'
        }
    }
    if ($values.ContainsKey('OBSIDIAN_MCP_PORT') -and -not (Test-PlaceholderValue -Value $values['OBSIDIAN_MCP_PORT'])) {
        if ($values['OBSIDIAN_MCP_PORT'] -notmatch '^[0-9]+$') {
            $missing += 'OBSIDIAN_MCP_PORT numeric value'
        }
    }
    if ($missing.Count -gt 0) {
        $globalEnv = Join-Path $HermesHome '.env'
        Stop-Install ("Obsidian HTTPS MCP settings are missing or placeholders in {0}: {1}. Put real values in {2}, then rerun -ProfilesOnly." -f $envFile, (($missing | Sort-Object -Unique) -join ', '), $globalEnv)
    }
}

function Copy-EnvValues {
    param([string]$ProfileDir)
    $example = Join-Path $ProfileDir '.env.EXAMPLE'
    $envFile = Join-Path $ProfileDir '.env'
    $globalEnv = Join-Path $HermesHome '.env'
    if (-not (Test-Path $example)) { return }
    if (-not (Test-Path $envFile)) {
        if (-not $DryRun) {
            Get-Content $example | Where-Object { $_ -notmatch '^[A-Za-z_][A-Za-z0-9_]*=\s*$' } | Set-Content -Path $envFile -Encoding UTF8
        }
        Write-Line '    created .env from .env.EXAMPLE'
    }
    $existing = @{}
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=') { $existing[$Matches[1]] = $true }
        }
    }
    $declared = @()
    Get-Content $example | ForEach-Object {
        if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=') { $declared += $Matches[1] }
    }
    $global = Read-DotEnv -Path $globalEnv
    $seedKeys = @($declared + @('OBSIDIAN_API_KEY', 'OBSIDIAN_MCP_PORT', 'OBSIDIAN_MCP_SSL_VERIFY')) | Select-Object -Unique
    $toAdd = @()
    foreach ($key in $seedKeys) {
        if (-not $existing.ContainsKey($key) -and $global.ContainsKey($key) -and -not (Test-PlaceholderValue -Value $global[$key])) {
            $toAdd += "$key=$($global[$key])"
        }
    }
    if ($toAdd.Count -gt 0 -and -not $DryRun) {
        Add-Content -Path $envFile -Value $toAdd -Encoding UTF8
    }
    if ($toAdd.Count -gt 0) { Write-Line "    seeded $($toAdd.Count) shared key(s) from $globalEnv" }
    Assert-ObsidianMcpEnv -ProfileDir $ProfileDir
}

function Deploy-PolicyPlugin {
    param([string]$ProfileDir, [string]$ProfileName)
    $src = Join-Path $Vault '.memoria/plugins/memoria-policy-gate'
    if (-not (Test-Path $src)) {
        Stop-Install "policy-gate plugin source missing at $src - refusing to deploy $ProfileName without the write gate"
    }
    $dst = Join-Path $ProfileDir 'plugins/memoria-policy-gate'
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $dst -Force | Out-Null
        Copy-Item (Join-Path $src 'plugin.yaml') (Join-Path $dst 'plugin.yaml') -Force
        Copy-Item (Join-Path $src '__init__.py') (Join-Path $dst '__init__.py') -Force
        Set-TemplateValues -Path (Join-Path $dst '__init__.py') -ProfileName $ProfileName
    }
    Write-Line '    deployed write-gate plugin (memoria-policy-gate)'
}

function Install-Profiles {
    Write-Header 'Hermes profiles'
    $profilesSrc = Join-Path $Vault '.memoria/profiles'
    if (-not (Test-Path $profilesSrc)) { Stop-Install "No profiles at $profilesSrc." }
    if (-not $script:HermesExe) { $script:HermesExe = Resolve-HermesExe }
    if (-not $script:HermesExe) {
        Write-Warn 'Hermes not on PATH - install Hermes or open a new PowerShell, then rerun -ProfilesOnly.'
        return
    }
    $targets = if ($Only) { $Only } else { $AllProfiles }
    $targets = $targets | Where-Object {
        if ($AllProfiles -contains $_) { $true } else { Write-Warn "Unknown profile in -Only: $_"; $false }
    }
    if (-not $targets) { Stop-Install '-Only matched no shipped profiles.' }

    $staging = Join-Path $env:TEMP ('memoria-profiles-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $staging -Force | Out-Null
    foreach ($profileName in $targets) {
        $src = Join-Path $profilesSrc $profileName
        foreach ($file in $RequiredFiles) {
            if (-not (Test-Path (Join-Path $src $file))) { Stop-Install "$profileName missing $file." }
        }
        Write-Line "  staging $profileName"
        $dst = Join-Path $staging $profileName
        Copy-Item $src $dst -Recurse -Force
        Set-TemplateValues -Path (Join-Path $dst 'config.yaml') -ProfileName $profileName
        Assert-ProfileObsidianMcpHttps -ConfigPath (Join-Path $dst 'config.yaml') -ProfileName $profileName
        Invoke-Logged -FilePath $script:HermesExe -ArgumentList ($script:HermesArgsPrefix + @('profile', 'install', $dst, '--name', $profileName, '--alias', '--force', '--yes'))
        $deployed = Join-Path $HermesProfilesDir $profileName
        if (-not $DryRun) {
            Copy-Item (Join-Path $dst 'config.yaml') (Join-Path $deployed 'config.yaml') -Force
        }
        Copy-EnvValues -ProfileDir $deployed
        Deploy-PolicyPlugin -ProfileDir $deployed -ProfileName $profileName
    }
    Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
    Write-Ok "Profiles installed: $($targets.Count)"
}

function Install-Cron {
    param([string]$SourceName, [string]$DestName, [string]$Schedule, [string]$JobName)
    if (-not $script:HermesExe) { $script:HermesExe = Resolve-HermesExe }
    if (-not $script:HermesExe) {
        Write-Warn "Hermes not on PATH - skipping $JobName cron."
        return
    }
    $src = Join-Path $Vault ".memoria/scripts/$SourceName"
    if (-not (Test-Path $src)) {
        Write-Warn "cron wrapper missing at $src"
        return
    }
    New-Item -ItemType Directory -Path $HermesScriptsDir -Force | Out-Null
    $dst = Join-Path $HermesScriptsDir $DestName
    Copy-Item $src $dst -Force
    Set-TemplateValues -Path $dst
    $list = if ($DryRun) { '' } else { (& $script:HermesExe @script:HermesArgsPrefix cron list 2>$null | Out-String) }
    if ($list -match [regex]::Escape($JobName)) {
        Write-Line "  $JobName cron already present - wrapper refreshed"
        return
    }
    Invoke-Logged -FilePath $script:HermesExe -ArgumentList ($script:HermesArgsPrefix + @('cron', 'create', $Schedule, '--script', $DestName, '--no-agent', '--name', $JobName, '--deliver', 'local'))
}

function Install-Crons {
    Write-Header 'Hermes cron wrappers'
    Install-Cron -SourceName 'board-export-cron.sh' -DestName 'memoria-board-export.sh' -Schedule '* * * * *' -JobName 'memoria-board-export'
    Install-Cron -SourceName 'sweeps-cron.sh' -DestName 'memoria-sweeps.sh' -Schedule '*/15 * * * *' -JobName 'memoria-sweeps'
    Install-Cron -SourceName 'lint-cron.sh' -DestName 'memoria-lint.sh' -Schedule '0 6 * * *' -JobName 'memoria-lint'
    Install-Cron -SourceName 'metrics-cron.sh' -DestName 'memoria-metrics.sh' -Schedule '30 6 * * 1' -JobName 'memoria-metrics'
    Install-Cron -SourceName 'eval-cron.sh' -DestName 'memoria-eval.sh' -Schedule '0 7 1 */3 *' -JobName 'memoria-eval'
}

function Write-SecretsGuidance {
    Write-Header 'API keys'
    Write-Line "Put shared values in $HermesHome\.env, then rerun:"
    Write-Line "  .\scripts\install.ps1 -ProfilesOnly -Vault `"$Vault`""
    Write-Line ''
    Write-Line 'Required core values:'
    Write-Line '  KILOCODE_API_KEY=...'
    Write-Line '  OBSIDIAN_API_KEY=...'
    Write-Line '  OBSIDIAN_MCP_PORT=27124'
    Write-Line '  OBSIDIAN_MCP_SSL_VERIFY=C:\path\to\obsidian-local-rest-api.pem'
    Write-Line '  OPENALEX_API_KEY=...'
}

function Invoke-Main {
    Write-Header 'Memoria Windows installer'
    Write-Line 'Production Windows path: native Hermes, native Obsidian, native vault.'
    Write-Line 'Linux/WSL install.sh remains the testing path.'

    if (-not $ProfilesOnly) {
        if (-not $NoApps) {
            Write-Header 'Windows apps'
            Install-WingetApp -Id 'Obsidian.Obsidian' -Name 'Obsidian' -Fallback 'https://obsidian.md/download'
            Install-WingetApp -Id 'Zotero.Zotero' -Name 'Zotero' -Fallback 'https://www.zotero.org/download/'
            Install-WingetApp -Id 'Git.Git' -Name 'Git for Windows' -Fallback 'https://git-scm.com/download/win'
        }
        Assert-RequiredCommands
        Install-Hermes
        $repoRoot = Get-RepoRoot
        Copy-VaultSource -RepoRoot $repoRoot
        Enable-MemoriaCssSnippets -RepoRoot $repoRoot
        Install-McpDeps -RepoRoot $repoRoot
    } else {
        Assert-RequiredCommands
        $script:VenvPython = Join-Path $Vault '.memoria/.venv/Scripts/python.exe'
        Enable-MemoriaCssSnippets -RepoRoot (Get-LocalRepoRoot)
    }

    Install-Profiles
    Install-Crons
    Write-SecretsGuidance

    Write-Header 'Done'
    Write-Line "Open this folder in Obsidian as your production vault: $Vault"
    Write-Line 'Then enable community plugins and configure the Local REST API HTTPS cert path.'
}

Invoke-Main
