#Requires -Version 5.1
<#
.SYNOPSIS
    Memoria bootstrap -- native Windows installer.

.DESCRIPTION
    Sets up a standalone Memoria CLI/runtime workspace.

    This script:
      1. Copies vault-template/ into the runtime vault.
      2. Creates the vault-local runtime venv.
      3. Installs the Memoria package.
      4. Stages the golden copy and wires Git hooks.
      5. Registers the workspace-local qmd search collection.
      6. Prints CLI next steps.

.PARAMETER Vault
    Windows folder for the runtime vault. Default: $env:USERPROFILE\Memoria
    (deliberately outside OneDrive).

.PARAMETER WithCluster
    Install the optional clustering stack.

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
    [switch]$WithCluster,
    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

$RepoUrl = 'https://github.com/eranroseman/memoria-vault.git'
$VenvPython = $null

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

function Assert-RequiredCommands {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-Install 'Git is required on PATH. Install Git for Windows, open a new PowerShell so PATH refreshes, then rerun the installer.'
    }
}

function Get-RepoRoot {
    if ($PSCommandPath) {
        $scriptRoot = Split-Path -Parent $PSCommandPath
        $localRoot = Split-Path -Parent $scriptRoot
        if (Test-Path (Join-Path $localRoot 'vault-template/.memoria')) {
            return $localRoot
        }
    }
    $work = Join-Path $env:TEMP ('memoria-vault-' + [guid]::NewGuid().ToString('N'))
    Invoke-Logged -FilePath 'git' -ArgumentList @('clone', '--depth', '1', $RepoUrl, $work)
    return $work
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

function Get-PythonForVenv {
    $uv = Get-CommandPath @('uv.exe', 'uv')
    if ($uv) {
        Invoke-Logged -FilePath $uv -ArgumentList @('python', 'install', '3.11')
        return [pscustomobject]@{ Exe = $uv; Prefix = @('run', '--python', '3.11', 'python') }
    }

    $python = Get-CommandPath @('py.exe', 'python.exe', 'python3.exe')
    if (-not $python) {
        Stop-Install 'No uv or Python launcher found. Install uv or Python 3.11+, then retry.'
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
    $src = Join-Path $RepoRoot 'vault-template'
    if (-not (Test-Path $src)) { Stop-Install "Missing vault-template tree at $src." }
    if (Test-Path (Join-Path $Vault '.memoria')) {
        Stop-Install "$Vault is already a Memoria vault. This installer is fresh-install only; choose an empty target or move the existing vault aside."
    }
    New-Item -ItemType Directory -Path $Vault -Force | Out-Null
    Invoke-Robocopy -Source $src -Destination $Vault -ExtraArgs @('/XD', '.git', '/XF', '.env', 'data.json', 'appearance.json')
    Write-Ok "Vault populated at $Vault"
}

function Initialize-VaultGit {
    Write-Header 'Vault Git repo'
    $gitDir = Join-Path $Vault '.git'
    if (Test-Path $gitDir) {
        Write-Ok "Git repo already present at $Vault"
        return
    }
    Invoke-Logged -FilePath 'git' -ArgumentList @('-C', $Vault, 'init', '-q')
    Invoke-Logged -FilePath 'git' -ArgumentList @('-C', $Vault, 'branch', '-M', 'main')
    Write-Ok 'Git repo initialized for checkpoints and hooks'
}

function Install-VaultHooks {
    Write-Header 'Vault Git hooks'
    $gitDir = Join-Path $Vault '.git'
    $hooksDir = Join-Path $gitDir 'hooks'
    $preCommit = Join-Path $Vault '.githooks/pre-commit'
    $postCommit = Join-Path $Vault '.githooks/post-commit'
    if (-not $DryRun) {
        if (-not (Test-Path $gitDir)) { Stop-Install "Vault is not a Git repo: $Vault" }
        if (-not (Test-Path $preCommit)) { Stop-Install "Missing pre-commit hook at $preCommit" }
        if (-not (Test-Path $postCommit)) { Stop-Install "Missing post-commit hook at $postCommit" }
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
        Copy-Item $preCommit (Join-Path $hooksDir 'pre-commit') -Force
        Copy-Item $postCommit (Join-Path $hooksDir 'post-commit') -Force
    }
    Write-Line "  + copy $preCommit -> $hooksDir\pre-commit"
    Write-Line "  + copy $postCommit -> $hooksDir\post-commit"
    Write-Ok 'Vault hooks wired'
}

function Install-McpDeps {
    param([string]$RepoRoot)
    Write-Header 'Runtime dependencies'
    $reqs = Join-Path $Vault '.memoria/mcp/requirements.txt'
    $clusterReqs = Join-Path $Vault '.memoria/mcp/requirements-cluster.txt'
    $venv = Join-Path $Vault '.memoria/.venv'
    $script:VenvPython = Join-Path $venv 'Scripts/python.exe'
    if ($DryRun) {
        Write-Line "  + would create venv $venv and install $reqs plus Memoria from $RepoRoot"
        if ($WithCluster) { Write-Line "  + would install optional cluster deps from $clusterReqs" }
        return
    }
    if (-not (Test-Path $reqs)) { Write-Warn "No requirements file at $reqs"; return }
    if (-not (Test-Path $script:VenvPython)) {
        $py = Get-PythonForVenv
        Invoke-Python -PythonSpec $py -ArgumentList @('-m', 'venv', $venv)
    }
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '-r', $reqs)
    if ($WithCluster) {
        if (-not (Test-Path $clusterReqs)) { Stop-Install "Missing optional cluster requirements at $clusterReqs" }
        Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '-r', $clusterReqs)
    }
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', $RepoRoot)
    Write-Ok "Runtime deps installed in $venv"
}

function Install-RuntimeScaffold {
    Write-Header 'Runtime scaffold'
    $script:VenvPython = if ($script:VenvPython) { $script:VenvPython } else { Join-Path $Vault '.memoria/.venv/Scripts/python.exe' }
    $schema = Join-Path $Vault '.memoria/schemas/folders.yaml'
    $goldenModule = 'memoria_vault.runtime.subsystems.integrity.linter.golden_restore'
    if ($DryRun) {
        Write-Line "  + ensure skeleton directories from $schema"
        Write-Line "  + $script:VenvPython -m $goldenModule --vault $Vault stage"
        return
    }
    if (-not (Test-Path $script:VenvPython)) { Stop-Install "Missing venv Python at $script:VenvPython" }
    if (-not (Test-Path $schema)) { Stop-Install "Missing folders schema at $schema" }
    $code = "import sys,yaml; from pathlib import Path; " +
        "v=Path(sys.argv[1]); " +
        "data=yaml.safe_load((v/'.memoria/schemas/folders.yaml').read_text(encoding='utf-8')) or {}; " +
        "[(v/d).mkdir(parents=True, exist_ok=True) for d in (data.get('skeleton') or [])]"
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-c', $code, $Vault)
    Write-Ok 'Folder skeleton ensured from folders.yaml'
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @(
        '-m',
        $goldenModule,
        '--vault',
        $Vault,
        'stage'
    )
    Write-Ok 'Golden copy staged (.memoria/golden/)'
}

function Resolve-Qmd {
    if ($env:MEMORIA_QMD_BIN) {
        if ([System.IO.Path]::IsPathRooted($env:MEMORIA_QMD_BIN) -and (Test-Path -Path $env:MEMORIA_QMD_BIN -PathType Leaf)) {
            return (Resolve-Path $env:MEMORIA_QMD_BIN).Path
        }
        return $null
    }
    $npm = Get-CommandPath @('npm.cmd', 'npm.exe', 'npm')
    if (-not $npm -or $DryRun) { return $null }
    $prefix = (& $npm prefix -g 2>$null | Select-Object -First 1)
    if (-not $prefix) { return $null }
    return Get-CommandPath @(
        (Join-Path $prefix 'qmd.cmd'),
        (Join-Path $prefix 'qmd.exe'),
        (Join-Path $prefix 'bin/qmd')
    )
}

function Install-Qmd {
    Write-Header 'qmd search engine'
    $qmd = Resolve-Qmd
    if ($qmd) {
        Write-Ok "qmd present: $qmd"
    } else {
        $npm = Get-CommandPath @('npm.cmd', 'npm.exe', 'npm')
        $node = Get-CommandPath @('node.exe', 'node')
        $nodeVersion = if ($node -and -not $DryRun) { (& $node --version 2>$null | Select-Object -First 1) } else { '' }
        if ($npm -and ($DryRun -or $nodeVersion -match '^v(2[2-9]|[3-9][0-9])')) {
            Invoke-Logged -FilePath $npm -ArgumentList @('install', '-g', '@tobilu/qmd')
            $qmd = Resolve-Qmd
        }
        if (-not $qmd) {
            Write-Warn 'qmd not installed and Node >=22 unavailable -- search will not be ready until you run: npm install -g @tobilu/qmd'
            return
        }
    }
    $script:QmdBin = $qmd

    $checked = Join-Path $Vault '.memoria/index/qmd/checked'
    $config = Join-Path $Vault '.memoria/index/qmd/config'
    $index = Join-Path $Vault '.memoria/index/qmd/index.sqlite'
    Write-Line "  + QMD_CONFIG_DIR=$config INDEX_PATH=$index $qmd collection add $checked --name memoria-checked --mask **/*.md"
    if ($DryRun) { return }
    New-Item -ItemType Directory -Path $checked -Force | Out-Null
    New-Item -ItemType Directory -Path $config -Force | Out-Null
    $oldConfig = $env:QMD_CONFIG_DIR
    $oldIndex = $env:INDEX_PATH
    try {
        $env:QMD_CONFIG_DIR = $config
        $env:INDEX_PATH = $index
        & $qmd collection add $checked --name memoria-checked --mask '**/*.md'
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "qmd collection add failed -- run: memoria workspace rebuild --workspace `"$Vault`" --search"
        }
    } finally {
        if ($null -eq $oldConfig) { Remove-Item Env:QMD_CONFIG_DIR -ErrorAction SilentlyContinue } else { $env:QMD_CONFIG_DIR = $oldConfig }
        if ($null -eq $oldIndex) { Remove-Item Env:INDEX_PATH -ErrorAction SilentlyContinue } else { $env:INDEX_PATH = $oldIndex }
    }
    Write-Line '  (registered checked-only qmd input; the worker rebuilds it from checked Concepts)'
}

function Write-CliNextSteps {
    Write-Header 'Next steps'
    $py = if ($script:VenvPython) { $script:VenvPython } else { Join-Path $Vault '.memoria/.venv/Scripts/python.exe' }
    Write-Line "  Workspace: $Vault"
    Write-Line "  1. Check the bundle:  `"$py`" -m memoria_vault.cli doctor bundle --workspace `"$Vault`""
    Write-Line "  2. Rebuild search:    `"$py`" -m memoria_vault.cli workspace rebuild --workspace `"$Vault`" --search"
    Write-Line "  3. Ask from CLI:      `"$py`" -m memoria_vault.cli ask --workspace `"$Vault`" --question `"What needs attention?`""
    Write-Line "  4. First checkpoint:  cd `"$Vault`"; git add -A; git commit -m `"Initial Memoria vault`""
    if ($DryRun) { Write-Warn 'This was a DRY RUN -- nothing above was actually changed.' }
}

function Invoke-Main {
    Write-Header 'Memoria Windows installer'
    Write-Line 'Default path: standalone CLI/runtime workspace.'

    Assert-RequiredCommands
    $repoRoot = Get-RepoRoot
    Copy-VaultSource -RepoRoot $repoRoot
    Install-McpDeps -RepoRoot $repoRoot
    Install-RuntimeScaffold
    Initialize-VaultGit
    Install-VaultHooks
    Install-Qmd
    Write-CliNextSteps
    Write-Header 'Done'
}

Invoke-Main
