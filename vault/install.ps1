#Requires -Version 5.1

<#
.SYNOPSIS
    Memoria installer -- set up the seven Hermes profiles from this vault.

.DESCRIPTION
    Idempotent. Always overwrites profile directories under
    ~/.hermes/profiles/memoria-*/ from the source in .memoria/profiles/.
    Preserves human-owned .env files. Gracefully skips profiles whose
    source is incomplete (missing required files) -- useful while the v0.1
    scaffold is still being filled in.

    Substitutes {{VAULT_PATH}} placeholders in each profile's mcp.json with
    this vault's absolute path (forward-slash form) before installing.

.PARAMETER Only
    If specified, install only these profile names (comma-separated).
    Example: ./install.ps1 -Only memoria-librarian,memoria-linter

.PARAMETER SkipHermesCheck
    Skip the Hermes-on-PATH check (use if Hermes is installed but not on PATH).

.PARAMETER SkipPythonCheck
    Skip the Python check (use during early v0.1 when no MCP server source
    has been authored yet).

.EXAMPLE
    ./install.ps1
    Install all seven profiles whose source files are complete.

.EXAMPLE
    ./install.ps1 -Only memoria-linter
    Install just the Linter (useful for incremental development).
#>

[CmdletBinding()]
param(
    [string[]]$Only,
    [switch]$SkipHermesCheck,
    [switch]$SkipPythonCheck
)

$ErrorActionPreference = 'Stop'

# ============================================================================
# Paths and constants
# ============================================================================
$VaultPath         = $PSScriptRoot
$MemoriaPath       = Join-Path $VaultPath '.memoria'
$ProfilesSourceDir = Join-Path $MemoriaPath 'profiles'
$McpRequirements   = Join-Path $MemoriaPath 'mcp\requirements.txt'
$HermesProfilesDir = Join-Path $env:USERPROFILE '.hermes\profiles'

$AllProfiles = @(
    'memoria-librarian',
    'memoria-mapper',
    'memoria-socratic',
    'memoria-writer',
    'memoria-verifier',
    'memoria-coder',
    'memoria-linter'
)

# Minimum file set a profile needs to be installable. SOUL.md ships in the v0.1
# scaffold; the other three are the v0.2 wiring that hermes profile install
# requires.
$RequiredFiles = @('SOUL.md', 'config.yaml', 'mcp.json', 'distribution.yaml')

$Targets = if ($Only) {
    $AllProfiles | Where-Object { $_ -in $Only }
} else {
    $AllProfiles
}

Write-Host "Memoria installer" -ForegroundColor Cyan
Write-Host "  Vault path:   $VaultPath"
Write-Host "  Hermes home:  $HermesProfilesDir"
Write-Host "  Targets:      $($Targets -join ', ')"
Write-Host ""

# ============================================================================
# Prerequisites
# ============================================================================
if (-not $SkipHermesCheck) {
    $hermes = Get-Command hermes -ErrorAction SilentlyContinue
    if (-not $hermes) {
        Write-Host "[X] Hermes not found on PATH." -ForegroundColor Red
        Write-Host "    Install: https://hermes-agent.nousresearch.com/docs/getting-started/installation"
        Write-Host "    If Hermes is installed but not on PATH, re-run with -SkipHermesCheck."
        exit 1
    }
    Write-Host "[OK] Hermes found at $($hermes.Source)" -ForegroundColor Green
}

if (-not $SkipPythonCheck) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Host "[X] Python not found on PATH. Required for the MCP servers." -ForegroundColor Red
        Write-Host "    If you don't need MCP servers yet (early v0.1 scaffold),"
        Write-Host "    re-run with -SkipPythonCheck."
        exit 1
    }
    Write-Host "[OK] Python found: $(& python --version 2>&1)" -ForegroundColor Green
}

# ============================================================================
# MCP dependencies (skipped gracefully if requirements.txt isn't authored yet)
# ============================================================================
if (Test-Path $McpRequirements) {
    Write-Host ""
    Write-Host "Installing MCP server dependencies from .memoria/mcp/requirements.txt..."
    & python -m pip install --quiet -r $McpRequirements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] pip install failed (exit $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] MCP dependencies installed" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Warning "No requirements.txt at $McpRequirements -- MCP install skipped."
    Write-Warning "Expected once .memoria/mcp/ is authored. (Not in v0.1 scaffold.)"
}

# ============================================================================
# Stage + install each target profile
# ============================================================================
$StagingDir = Join-Path $env:TEMP "memoria-staging-$([guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

$installed = @()
$skipped   = @()
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

try {
    foreach ($p in $Targets) {
        $src = Join-Path $ProfilesSourceDir $p

        if (-not (Test-Path $src)) {
            $skipped += [PSCustomObject]@{ Profile = $p; Reason = "source directory missing at $src" }
            continue
        }

        # Check required files
        $missing = @()
        foreach ($f in $RequiredFiles) {
            if (-not (Test-Path (Join-Path $src $f))) {
                $missing += $f
            }
        }
        if ($missing.Count -gt 0) {
            $skipped += [PSCustomObject]@{
                Profile = $p
                Reason  = "incomplete source -- missing: $($missing -join ', ')"
            }
            continue
        }

        Write-Host ""
        Write-Host "Staging $p..."

        $dst = Join-Path $StagingDir $p
        Copy-Item -Path $src -Destination $dst -Recurse -Force

        # Substitute {{VAULT_PATH}} in mcp.json. Write UTF-8 no-BOM because
        # JSON parsers can choke on a BOM.
        $mcpJson = Join-Path $dst 'mcp.json'
        if (Test-Path $mcpJson) {
            $content = Get-Content -Path $mcpJson -Raw
            $vaultPathForward = $VaultPath -replace '\\', '/'
            $content = $content -replace '\{\{VAULT_PATH\}\}', $vaultPathForward
            [System.IO.File]::WriteAllText($mcpJson, $content, $utf8NoBom)
        }

        Write-Host "Installing $p..."
        & hermes profile install $dst --alias $p --force --yes
        if ($LASTEXITCODE -ne 0) {
            $skipped += [PSCustomObject]@{
                Profile = $p
                Reason  = "hermes profile install failed (exit $LASTEXITCODE)"
            }
            continue
        }

        $installed += $p

        # Bootstrap .env from .env.EXAMPLE on first install. .env is human-
        # owned and Hermes preserves it across re-installs; we only create it
        # if absent so re-running this script never clobbers credentials.
        $envExample = Join-Path $HermesProfilesDir "$p\.env.EXAMPLE"
        $envFile    = Join-Path $HermesProfilesDir "$p\.env"
        if ((Test-Path $envExample) -and -not (Test-Path $envFile)) {
            Copy-Item $envExample $envFile
            Write-Host "  Created .env from .env.EXAMPLE (fill in real values)"
        }
    }
}
finally {
    if (Test-Path $StagingDir) {
        Remove-Item -Path $StagingDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "=== Install summary ===" -ForegroundColor Cyan
Write-Host "  Installed: $($installed.Count) of $($Targets.Count) targeted"
foreach ($p in $installed) {
    Write-Host "    [+] $p" -ForegroundColor Green
}
if ($skipped.Count -gt 0) {
    Write-Host "  Skipped:"
    foreach ($s in $skipped) {
        Write-Host "    [-] $($s.Profile): $($s.Reason)" -ForegroundColor Yellow
    }
}

if ($installed.Count -eq 0) {
    Write-Host ""
    Write-Host "No profiles installed. The v0.1 scaffold ships SOUL.md prompts" -ForegroundColor Yellow
    Write-Host "but not the wiring (config.yaml, mcp.json, distribution.yaml)."   -ForegroundColor Yellow
    Write-Host "Author the missing files for at least one profile, then re-run."  -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Fill in credentials in each installed profile's .env file:"
foreach ($p in $installed) {
    Write-Host "       $(Join-Path $HermesProfilesDir "$p\.env")"
}
Write-Host ""
Write-Host "  2. Open this folder in Obsidian as your vault."
Write-Host "       Folder: $VaultPath"
Write-Host ""
Write-Host "  3. Try a session:"
Write-Host "       hermes -p $($installed[0]) chat"
Write-Host ""
Write-Host "Re-run this script after 'git pull' to refresh installed profiles."        -ForegroundColor DarkGray
Write-Host "Author-owned files (SOUL.md, config.yaml, mcp.json, skills/, cron/)"        -ForegroundColor DarkGray
Write-Host "are overwritten; human-owned .env files are preserved."                  -ForegroundColor DarkGray
