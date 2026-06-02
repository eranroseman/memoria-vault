#Requires -Version 5.1
<#
.SYNOPSIS
    Memoria bootstrap -- thin Windows launcher.

.DESCRIPTION
    Windows is only the editing surface; the Hermes runtime lives in WSL2. This
    launcher does the three Windows-only things, then hands all real work to
    install.sh running inside WSL2:

      1. Gate on WSL2 (no WSL2 -> Microsoft how-to link + exit; install nothing).
      2. Install the GUI apps (Obsidian, Zotero) + Git for Windows via winget -- guided.
      3. Run install.sh inside WSL2 (with --no-apps; the vault path translated to
         a /mnt/c path so both Windows-Obsidian and WSL-Hermes can reach it).

    There is intentionally NO install logic here -- install.sh is the single
    source of truth. Inspect it first:
      https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh

.PARAMETER Vault
    Windows folder for the runtime vault. Default: $env:USERPROFILE\Memoria
    (deliberately OUTSIDE OneDrive -- OneDrive corrupts the .obsidian DB and
    fights Hermes file locks).

.PARAMETER ProfilesOnly
    Skip the bootstrap; just (re)deploy profiles from an existing vault.

.PARAMETER Only
    Restrict the profile step to these profiles (e.g. -Only memoria-linter).
    Pairs with -ProfilesOnly. Forwarded to install.sh as --only.

.PARAMETER DryRun
    Forward --dry-run to install.sh (print commands, change nothing).

.PARAMETER Yes
    Non-interactive: accept defaults, no prompts.

.EXAMPLE
    irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex

.EXAMPLE
    .\install.ps1 -Vault D:\Memoria
#>
[CmdletBinding()]
param(
    [string]$Vault = (Join-Path $env:USERPROFILE 'Memoria'),
    [string[]]$Only,
    [switch]$ProfilesOnly,
    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'
$RawUrl  = 'https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh'
$WslDoc  = 'https://learn.microsoft.com/windows/wsl/install'

function Say  { param($m) Write-Host $m }
function Hdr  { param($m) Write-Host "`n== $m ==" -ForegroundColor Cyan }
function Ok   { param($m) Write-Host "[OK] $m" -ForegroundColor Green }
function Warn { param($m) Write-Host "[!] $m" -ForegroundColor Yellow }
function Die  { param($m) Write-Host "[X] $m" -ForegroundColor Red; exit 1 }

# ============================================================================
# 1. WSL2 gate -- no WSL2 means we install nothing on Windows.
# ============================================================================
Hdr 'WSL2 check'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Say "WSL is not installed. Memoria's runtime (Hermes) requires WSL2."
    Say "Follow the official Microsoft guide, reboot, then re-run this installer:"
    Say "    $WslDoc"
    Die 'No WSL -- nothing installed.'
}

# A working default distro? (`wsl uname -r` succeeds and reports a WSL2 kernel.)
$kernel = ''
try { $kernel = (& wsl.exe -e uname -r) 2>$null } catch { $kernel = '' }
if (-not $kernel) {
    Say "WSL is present but no Linux distro is ready. Install Ubuntu and set WSL2:"
    Say "    wsl --install -d Ubuntu"
    Say "    (full guide: $WslDoc)"
    Die 'No usable WSL2 distro -- nothing installed.'
}
if ($kernel -notmatch 'WSL2|microsoft-standard') {
    Warn "Your default distro may be WSL1 (kernel: $kernel)."
    Warn "Memoria needs WSL2. Convert it:  wsl --set-version <distro> 2   (guide: $WslDoc)"
    if (-not $Yes) {
        $ans = Read-Host 'Continue anyway? [y/N]'
        if ($ans -notmatch '^[Yy]') { Die 'Stopped -- convert the distro to WSL2 and re-run.' }
    }
}
Ok "WSL2 ready (kernel: $kernel)"

# ============================================================================
# 2. Windows GUI apps via winget (guided). install.sh runs with --no-apps.
# ============================================================================
function Install-WingetApp {
    param([string]$Id, [string]$Name, [string]$Fallback)
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Warn "winget not found -- install $Name manually: $Fallback"
        return
    }
    $present = (& winget list --id $Id -e) | Select-String -SimpleMatch $Id -Quiet
    if ($present) { Ok "$Name present"; return }
    Say "$Name is not installed. Command:  winget install --id $Id -e"
    $go = $Yes
    if (-not $Yes) { $go = ((Read-Host "Install $Name now via winget? [y/N]") -match '^[Yy]') }
    if ($go) {
        if ($DryRun) { Say "  + winget install --id $Id -e --source winget" }
        else { & winget install --id $Id -e --source winget --accept-package-agreements --accept-source-agreements }
    } else {
        Say "  Skipped. Install later: $Fallback"
    }
}

if (-not $ProfilesOnly) {
    Hdr 'Windows GUI apps'
    Install-WingetApp -Id 'Obsidian.Obsidian' -Name 'Obsidian' -Fallback 'https://obsidian.md/download'
    Install-WingetApp -Id 'Zotero.Zotero'     -Name 'Zotero'   -Fallback 'https://www.zotero.org/download/'
    # Git for Windows -- the obsidian-git plugin shells out to it; without a Windows
    # git binary the Source Control view shows "git not found". (WSL2 git is separate.)
    Install-WingetApp -Id 'Git.Git'           -Name 'Git for Windows' -Fallback 'https://git-scm.com/download/win'
    Say ''
    Say 'Zotero add-ons (install from Zotero -> Tools -> Add-ons -> Install From File):'
    Say '  - Better BibTeX (REQUIRED): https://github.com/retorquere/zotero-better-bibtex/releases/latest'
    Say '  - MarkDB-Connect (recommended): https://github.com/daeh/zotero-markdb-connect/releases/latest'
    Say 'On first Obsidian launch: turn off Restricted mode so the bundled plugins load.'
}

# ============================================================================
# 3. Translate the vault path and hand off to install.sh inside WSL2.
# ============================================================================
Hdr 'Handing off to WSL2'

# Confirm or override the target folder (unless -Vault was given, or -Yes).
# Default %USERPROFILE%\Memoria is deliberately OUTSIDE OneDrive.
if (-not $PSBoundParameters.ContainsKey('Vault') -and -not $Yes) {
    Say 'Pick a folder OUTSIDE OneDrive (it corrupts the Obsidian index and fights Hermes file locks).'
    $ans = Read-Host "Vault folder [$Vault]"
    if ($ans) { $Vault = $ans }
}

# Windows path -> /mnt/c/... so Windows-Obsidian and WSL-Hermes share one vault.
New-Item -ItemType Directory -Path $Vault -Force | Out-Null
# Pass a forward-slash path to wslpath: when a backslash Windows path is marshalled
# to wsl.exe the backslashes are eaten (C:\Users\x -> C:Usersx), so wslpath fails.
# wslpath accepts C:/Users/x and returns /mnt/c/Users/x correctly.
$wslVault = (& wsl.exe wslpath -a ($Vault -replace '\\','/')).Trim()
Ok "Vault (Windows): $Vault"
Ok "Vault (WSL):     $wslVault"

# Forwarded flags. Always --no-apps (Windows handled the GUI apps above).
$fwd = @('--no-apps', '--vault', $wslVault)
if ($ProfilesOnly) { $fwd += '--profiles-only' }
if ($Only)         { $fwd += @('--only', ($Only -join ',')) }
if ($DryRun)       { $fwd += '--dry-run' }
if ($Yes)          { $fwd += '--yes' }
$fwdStr = ($fwd -join ' ')

# Prefer a local install.sh (running from a clone); else curl it in WSL.
$localSh = Join-Path $PSScriptRoot 'install.sh'
# install.sh writes its progress (warn/hdr) to stderr. Under the script's
# ErrorActionPreference='Stop', PowerShell 5.1 wraps each native-exe stderr line
# as a terminating error and would abort here even though wsl.exe returned 0.
# Relax to 'Continue' just around the handoff, then restore + check the real code.
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
if (Test-Path $localSh) {
    $wslSh = (& wsl.exe wslpath -a ($localSh -replace '\\','/')).Trim()
    Say "Running: wsl bash $wslSh $fwdStr"
    & wsl.exe -e bash "$wslSh" @fwd
} else {
    Say "Running (piped): wsl bash <(curl $RawUrl) $fwdStr"
    & wsl.exe -e bash -c "curl -fsSL '$RawUrl' | bash -s -- $fwdStr"
}
$code = $LASTEXITCODE
$ErrorActionPreference = $savedEAP

if ($code -ne 0) { Die "install.sh exited with code $code." }

Hdr 'Done'
Say "Open this folder in Obsidian as your vault:  $Vault"
Say "Hermes runs inside WSL2 -- open a WSL shell for 'hermes ...' commands."
