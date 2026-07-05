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
      4. Ensures the folder skeleton and wires Git hooks.
      5. Prints CLI next steps.

.PARAMETER Vault
    Windows folder for the runtime vault. Default: $env:USERPROFILE\Memoria
    (deliberately outside OneDrive).

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
        Invoke-Logged -FilePath $uv -ArgumentList @('python', 'install', '3.12')
        return [pscustomobject]@{ Exe = $uv; Prefix = @('run', '--python', '3.12', 'python') }
    }

    $python = Get-CommandPath @('py.exe', 'python.exe', 'python3.exe')
    if (-not $python) {
        Stop-Install 'No uv or Python launcher found. Install uv or Python 3.12+, then retry.'
    }
    if ((Split-Path -Leaf $python) -ieq 'py.exe') {
        return [pscustomobject]@{ Exe = $python; Prefix = @('-3.12') }
    }
    return [pscustomobject]@{ Exe = $python; Prefix = @() }
}

function Invoke-Python {
    param([pscustomobject]$PythonSpec, [string[]]$ArgumentList)
    $exe = $PythonSpec.Exe
    $prefix = @($PythonSpec.Prefix)
    Invoke-Logged -FilePath $exe -ArgumentList ($prefix + $ArgumentList)
}

function Assert-PythonRuntime {
    param([pscustomobject]$PythonSpec)
    $exe = $PythonSpec.Exe
    $prefix = @($PythonSpec.Prefix)
    $code = 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'
    $versionArgs = $prefix + @('-c', $code)
    Write-Line ("  + {0} {1}" -f $exe, ($versionArgs -join ' '))
    if ($DryRun) { return }
    & $exe @versionArgs
    if ($LASTEXITCODE -ne 0) {
        Stop-Install 'Memoria requires Python 3.12+. Install uv or Python 3.12+, then retry.'
    }
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
    if (-not $DryRun) {
        if (-not (Test-Path $gitDir)) { Stop-Install "Vault is not a Git repo: $Vault" }
        if (-not (Test-Path $preCommit)) { Stop-Install "Missing pre-commit hook at $preCommit" }
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
        Copy-Item $preCommit (Join-Path $hooksDir 'pre-commit') -Force
    }
    Write-Line "  + copy $preCommit -> $hooksDir\pre-commit"
    Write-Ok 'Vault pre-commit hook wired'
}

function Install-RuntimeDeps {
    param([string]$RepoRoot)
    Write-Header 'Runtime dependencies'
    $venv = Join-Path $Vault '.memoria/.venv'
    $script:VenvPython = Join-Path $venv 'Scripts/python.exe'
    if ($DryRun) {
        Write-Line "  + would create venv $venv and install Memoria from $RepoRoot"
        return
    }
    if (-not (Test-Path $script:VenvPython)) {
        $py = Get-PythonForVenv
        Assert-PythonRuntime -PythonSpec $py
        Invoke-Python -PythonSpec $py -ArgumentList @('-m', 'venv', $venv)
    }
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Logged -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', $RepoRoot)
    Write-Ok "Runtime deps installed in $venv"
}

function Install-RuntimeScaffold {
    Write-Header 'Runtime scaffold'
    $script:VenvPython = if ($script:VenvPython) { $script:VenvPython } else { Join-Path $Vault '.memoria/.venv/Scripts/python.exe' }
    $schema = Join-Path $Vault '.memoria/schemas/folders.yaml'
    if ($DryRun) {
        Write-Line "  + ensure skeleton directories from $schema"
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
}

function Write-CliNextSteps {
    Write-Header 'Next steps'
    $py = if ($script:VenvPython) { $script:VenvPython } else { Join-Path $Vault '.memoria/.venv/Scripts/python.exe' }
    $memoria = Join-Path (Split-Path -Parent $py) 'memoria.exe'
    Write-Line "  Workspace: $Vault"
    Write-Line "  1. Check the bundle:  `"$memoria`" doctor bundle --workspace `"$Vault`""
    Write-Line "  2. Rebuild search:    `"$memoria`" workspace rebuild --workspace `"$Vault`" --search"
    Write-Line "  3. Ask from CLI:      `"$memoria`" ask --workspace `"$Vault`" --question `"What needs attention?`""
    Write-Line "  4. First checkpoint:  cd `"$Vault`"; git add -A; git commit -m `"Initial Memoria vault`""
    if ($DryRun) { Write-Warn 'This was a DRY RUN -- nothing above was actually changed.' }
}

function Invoke-Main {
    Write-Header 'Memoria Windows installer'
    Write-Line 'Default path: standalone CLI/runtime workspace.'

    Assert-RequiredCommands
    $repoRoot = Get-RepoRoot
    Copy-VaultSource -RepoRoot $repoRoot
    Install-RuntimeDeps -RepoRoot $repoRoot
    Install-RuntimeScaffold
    Initialize-VaultGit
    Install-VaultHooks
    Write-CliNextSteps
    Write-Header 'Done'
}

Invoke-Main
