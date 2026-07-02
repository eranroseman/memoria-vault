#!/usr/bin/env bash
# =============================================================================
# Memoria bootstrap installer  (Linux/WSL path; Windows uses install.ps1)
# =============================================================================
# One command sets up the standalone Memoria CLI/runtime workspace: clones the
# vault, installs the package into the vault-local venv, wires local integrity
# hooks, and registers qmd search. macOS is not supported.
#
# Inspect-first (recommended):
#   curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
#   less install.sh        # read it
#   bash install.sh        # then run it
#
# Convenience one-liner:
#   curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
#
# Flags:
#   --vault DIR       install the runtime vault here (default: ~/Memoria; prompted otherwise)
#   --with-cluster    install the optional clustering stack (bertopic -> torch, ~2GB)
#   --dry-run         print every command that WOULD run; change nothing
#   --yes             non-interactive: accept all defaults, no prompts (CI)
#   -h | --help       this help
#
# Safety: no silent privilege escalation. Any step needing root prints the exact
# `sudo` command and runs it only on your confirmation (apt will prompt for your
# password). --dry-run echoes everything and touches nothing.
#
# =============================================================================
set -euo pipefail

# --- constants ---------------------------------------------------------------
REPO_URL="https://github.com/eranroseman/memoria-vault.git"
REPO_BRANCH="main"
DEFAULT_TARGET="$HOME/Memoria"
MEMORIA_ENV="${MEMORIA_ENV:-prod}"

# --- flags -------------------------------------------------------------------
DRY_RUN=0
ASSUME_YES=0
WITH_CLUSTER=0
VAULT_OVERRIDE=""

# Resolved during run.
REPO_DIR=""
VAULT_PATH=""
PYTHON=""
VENV_PYTHON=""    # interpreter the MCP deps land in; wired into config.yaml at deploy
STAGING_REPO=""   # set only when WE clone to temp; removed on exit (the runtime vault is the copy)
INSTALL_MODULES_LOADED=0

# --- helpers -----------------------------------------------------------------
say()  { printf '%s\n' "$*"; }
hdr()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[0;31m[X]\033[0m %s\n' "$*" >&2; exit 1; }

# run ARGV  — echo a command, then run it unless --dry-run.
run() {
  printf '  + %s\n' "$*"
  [ "$DRY_RUN" -eq 1 ] || "$@"
}
# run_sh "shell string"  — same, for pipelines/redirections.
run_sh() {
  printf '  + %s\n' "$1"
  [ "$DRY_RUN" -eq 1 ] || bash -c "$1"
}

can_prompt() {
  [ -t 0 ] && return 0
  { : </dev/tty; } 2>/dev/null
}

# ask "prompt" "default"  — echo the answer (default when --yes or no tty).
ask() {
  local prompt="$1" default="${2:-}" reply=""
  if [ "$ASSUME_YES" -eq 1 ]; then printf '%s' "$default"; return; fi
  if ! can_prompt; then printf '%s' "$default"; return; fi
  read -r -p "$prompt " reply </dev/tty || reply=""
  printf '%s' "${reply:-$default}"
}
# confirm "prompt"  — 0 on yes. Defaults to NO unless --yes.
confirm() {
  if [ "$ASSUME_YES" -eq 1 ]; then return 0; fi
  if ! can_prompt; then return 1; fi
  local reply=""
  read -r -p "$1 [y/N] " reply </dev/tty || reply="n"
  case "$reply" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

have() { command -v "$1" >/dev/null 2>&1; }

ensure_git_available() {
  have git || die "Git is required on PATH. Install it (Ubuntu/WSL: sudo apt-get update && sudo apt-get install -y git), then rerun the installer."
}

python_install_guidance() {
  say "Python 3 is required for Memoria's deterministic tools and MCP servers."
  say "Ubuntu/WSL fix:"
  say "    sudo apt-get update && sudo apt-get install -y python3 python3-venv"
  say "Then re-run this installer."
}

# Remove the temp/staging clone on exit (only the one we created — never the
# user's own clone when run inspect-first). The runtime vault is the copy.
# NB: must return 0 — this is the EXIT trap, and its status becomes the script's
# exit code. Without the `return 0`, a successful run from a local clone (where
# STAGING_REPO is empty) would exit 1 on the failed `[ -n "" ]` test.
cleanup() { [ -n "$STAGING_REPO" ] && [ -d "$STAGING_REPO" ] && rm -rf "$STAGING_REPO"; return 0; }
trap cleanup EXIT

detect_python() {
  if have python3; then PYTHON=python3
  elif have python; then PYTHON=python
  else PYTHON=""; fi
}

load_install_modules() {
  [ "$INSTALL_MODULES_LOADED" -eq 1 ] && return 0
  local script_dir candidate
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
  candidate="$script_dir/install"
  if [ ! -d "$candidate" ] && [ -n "$REPO_DIR" ]; then
    candidate="$REPO_DIR/scripts/install"
  fi
  [ -f "$candidate/manifest.sh" ] || die "Installer modules not found under $candidate"
  # shellcheck source=scripts/install/manifest.sh
  source "$candidate/manifest.sh"
  # shellcheck source=scripts/install/runtime-tools.sh
  source "$candidate/runtime-tools.sh"
  INSTALL_MODULES_LOADED=1
}

# =============================================================================
# Arg parsing
# =============================================================================
parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --vault) VAULT_OVERRIDE="${2:-}"; shift 2 ;;
      --vault=*) VAULT_OVERRIDE="${1#*=}"; shift ;;
      --with-cluster) WITH_CLUSTER=1; shift ;;
      --dry-run) DRY_RUN=1; shift ;;
      --yes|-y) ASSUME_YES=1; shift ;;
      -h|--help) awk 'NR>=2 && /^#/{sub(/^# ?/,"");print;next} NR>=2{exit}' "${BASH_SOURCE[0]:-$0}" 2>/dev/null; exit 0 ;;
      *) die "Unknown argument: $1  (try --help)" ;;
    esac
  done
}

# =============================================================================
# Plan + consent
# =============================================================================
print_plan() {
  hdr "Memoria installer"
  say "This will set up the standalone CLI/runtime workspace:"
  say "  1. ensure prerequisites (git, Python 3 + venv; pandoc optional for exports)"
  say "  2. fetch the Memoria vault repo"
  say "  3. copy the runtime vault to your chosen folder"
  say "  4. install runtime dependencies + the memoria CLI into .memoria/.venv"
  say "  5. register qmd search, initialize git, and wire local hooks"
  say "  6. print CLI next steps"
  [ "$DRY_RUN" -eq 1 ] && { say ""; warn "DRY RUN — nothing will be changed."; }
  return 0
}

# =============================================================================
# Step 1 — prerequisites
# =============================================================================
ensure_prereqs() {
  hdr "Prerequisites"
  local missing=""
  have git    || missing="$missing git"
  # We install MCP deps into a venv (Step 5). Debian/Ubuntu ship the `venv` module
  # but withhold `ensurepip` until python3-venv is installed, so a venv created
  # without it has no pip. Probe ensurepip (not just venv) and add the package if
  # apt is available — far cleaner than the --break-system-packages fallback.
  detect_python
  if [ -z "$PYTHON" ]; then
    missing="$missing python3"
  elif ! "$PYTHON" -c "import ensurepip" >/dev/null 2>&1 && have apt-get; then
    missing="$missing python3-venv"
  fi
  if [ -z "$missing" ]; then
    ok "git and venv support present"
    have pandoc || warn "Pandoc not found — DOCX/PDF exports are unavailable until installed."
    return
  fi

  warn "Missing:$missing"
  case " $missing " in
    *" python3 "*|*" python3-venv "*) python_install_guidance ;;
  esac
  if have apt-get; then
    say "The recommended install (needs root):"
    say "    sudo apt-get update && sudo apt-get install -y$missing"
    if [ "$DRY_RUN" -eq 1 ]; then warn "(dry-run) would run the install command above"; return; fi
    if confirm "Run it now?"; then
      run_sh "sudo apt-get update"
      run_sh "sudo apt-get install -y$missing"
    else
      die "Install$missing and re-run (Memoria needs them)."
    fi
  else
    die "No apt-get found. This installer supports Ubuntu/Debian (or WSL2). Install$missing manually; if Python is missing, install Python 3.11+ plus venv support first."
  fi
  have pandoc || warn "Pandoc not found — DOCX/PDF exports are unavailable until installed."
}

# =============================================================================
# Step 2 — locate or clone the repo  (sets REPO_DIR)
# =============================================================================
resolve_repo() {
  hdr "Memoria vault source"
  # Running from inside a clone? (script dir or cwd has vault-template/.memoria)
  local sdir=""
  if [ -f "${BASH_SOURCE[0]:-}" ]; then
    sdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [ -n "$sdir" ] && [ -d "$sdir/vault-template/.memoria" ]; then
    REPO_DIR="$sdir"; ok "Using the clone this script lives in: $REPO_DIR"; return
  fi
  if [ -d "./vault-template/.memoria" ]; then
    REPO_DIR="$(pwd)"; ok "Using the clone in the current directory: $REPO_DIR"; return
  fi
  # Piped (curl | bash): clone fresh into a temp/staging dir (removed on exit).
  REPO_DIR="$(mktemp -d "${TMPDIR:-/tmp}/memoria-repo-XXXXXXXX")"
  STAGING_REPO="$REPO_DIR"
  say "Not run from a clone — fetching the repo to a staging dir."
  run git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
  [ "$DRY_RUN" -eq 1 ] || [ -d "$REPO_DIR/vault-template/.memoria" ] || die "Clone did not contain vault-template/.memoria."
  ok "Cloned to $REPO_DIR"
}

# =============================================================================
# Step 4 — copy the runtime vault to its target  (sets VAULT_PATH)
# =============================================================================
copy_vault() {
  hdr "Runtime vault"
  local target="$VAULT_OVERRIDE"
  if [ -z "$target" ]; then
    say "Pick a folder OUTSIDE any cloud-synced tree (OneDrive/Dropbox break the .obsidian DB and Hermes file locks)."
    target="$(ask "Vault folder [$DEFAULT_TARGET]:" "$DEFAULT_TARGET")"
  fi
  # Expand a leading ~.
  case "$target" in "~"/*) target="$HOME/${target#~/}" ;; "~") target="$HOME" ;; esac
  VAULT_PATH="$target"

  local src="$REPO_DIR/vault-template"
  [ -d "$src/.memoria" ] || die "No vault template at $src (.memoria missing)."

  if [ -d "$VAULT_PATH/.memoria" ]; then
    die "$VAULT_PATH is already a Memoria vault. This installer is fresh-install only; choose an empty target or move the existing vault aside."
  fi

  run mkdir -p "$VAULT_PATH"
  if have rsync; then
    run rsync -a --exclude '.git' "$src"/ "$VAULT_PATH"/
  else
    run_sh "cp -R \"$src\"/. \"$VAULT_PATH\"/"
  fi
  ok "Vault deployed to $VAULT_PATH"

  # Recreate the empty-folder skeleton. The repo no longer ships `.keep`
  # placeholders, so these dirs would otherwise be missing on a fresh target.
  local d
  for d in "${SKELETON_DIRS[@]}"; do
    run mkdir -p "$VAULT_PATH/$d"
  done
  ok "Folder skeleton ensured (${#SKELETON_DIRS[@]} dirs)"

  if [ ! -d "$VAULT_PATH/.git" ]; then
    run git -C "$VAULT_PATH" init -q
    run git -C "$VAULT_PATH" branch -M main
    ok "Git repo initialized for checkpoints and hooks"
  fi

  wire_commit_gate
  wire_verify_on_commit_hook

  # The runtime vault is the user's own repo — the installer initializes Git so
  # hooks can be wired, but it never commits or sets identity/remotes.
  say "  Create your first checkpoint when ready:"
  say "      cd \"$VAULT_PATH\""
  say "      git add -A && git commit -m \"Initial Memoria vault\""
  say "      git remote add origin <your-repo-url>   # optional — backup / multi-machine sync"
}

# =============================================================================
# Step 5 — runtime dependencies
# =============================================================================
# Deps go into a vault-local venv ($VAULT_PATH/.memoria/.venv). This sidesteps
# modern Ubuntu/Debian's PEP-668 "externally-managed-environment" pip block, keeps
# Memoria's deps off the system site-packages, and gives a stable interpreter path
install_mcp_deps() {
  hdr "Runtime dependencies"
  detect_python
  local reqs="$VAULT_PATH/.memoria/mcp/requirements.txt"
  # In --dry-run the vault was not actually copied, so reqs won't exist yet —
  # report what WOULD happen rather than a misleading "missing file" skip.
  if [ "$DRY_RUN" -eq 1 ]; then
    VENV_PYTHON="$VAULT_PATH/.memoria/.venv/bin/python"
    warn "(dry-run) would create venv at $VAULT_PATH/.memoria/.venv, pip install from $reqs, and install Memoria from $REPO_DIR"
    return
  fi
  if [ ! -f "$reqs" ]; then warn "No $reqs — skipping."; return; fi
  if [ -z "$PYTHON" ]; then
    python_install_guidance
    die "No Python found. Install python3 (for Ubuntu/WSL: sudo apt-get install -y python3 python3-venv), then re-run the installer."
  fi

  local venv="$VAULT_PATH/.memoria/.venv"
  # A venv is "usable" only if it has a working pip. Debian's `venv` without
  # `ensurepip` (python3-venv not installed) creates bin/python but no pip, so
  # checking for bin/python alone is not enough — verify pip, and discard a
  # half-built venv so we don't keep reusing a broken one.
  if [ -x "$venv/bin/python" ] && ! "$venv/bin/python" -m pip --version >/dev/null 2>&1; then
    warn "Existing venv at $venv has no pip — rebuilding."
    rm -rf "$venv"
  fi
  if [ ! -x "$venv/bin/python" ]; then
    if "$PYTHON" -m venv "$venv" >/dev/null 2>&1 && "$venv/bin/python" -m pip --version >/dev/null 2>&1; then
      ok "Created venv at $venv"
    else
      # venv unavailable/broken (missing ensurepip). ensure_prereqs tries to add
      # python3-venv; if that didn't happen, --break-system-packages is the only
      # pip target left on a PEP-668 system (plain --user is also blocked).
      rm -rf "$venv"
      warn "Could not create a working venv (missing ensurepip / python3-venv)."
      warn "Falling back to: $PYTHON -m pip install --user --break-system-packages"
      run "$PYTHON" -m pip install --user --break-system-packages --quiet -r "$reqs" \
        || die "pip fallback failed. Install python3-venv (apt install python3-venv), then re-run."
      run "$PYTHON" -m pip install --user --break-system-packages --quiet "$REPO_DIR" \
        || die "Memoria package install failed. Re-run from a clean checkout or install python3-venv."
      VENV_PYTHON="$PYTHON"   # runtime uses the same interpreter the deps landed in
      ok "Runtime dependencies installed (user site-packages, system override)"
      return
    fi
  fi
  VENV_PYTHON="$venv/bin/python"
  run "$VENV_PYTHON" -m pip install --quiet --upgrade pip
  run "$VENV_PYTHON" -m pip install --quiet -r "$reqs" || die "pip install of MCP deps into the venv failed."
  run "$VENV_PYTHON" -m pip install --quiet "$REPO_DIR" || die "Memoria package install into the venv failed."
  ok "Runtime dependencies installed into $venv"

  # Optional heavy stack (ADR-33): the cluster MCP's topic modeling needs
  # bertopic (-> torch). Graph tools work without it; require an explicit flag.
  if [ -f "$VAULT_PATH/.memoria/mcp/requirements-cluster.txt" ]; then
    if [ "$WITH_CLUSTER" -eq 1 ]; then
      run "$VENV_PYTHON" -m pip install --quiet -r "$VAULT_PATH/.memoria/mcp/requirements-cluster.txt" \
        || warn "cluster deps failed — install later: $VENV_PYTHON -m pip install -r .memoria/mcp/requirements-cluster.txt"
    else
      say "  (skipped optional clustering stack — rerun with --with-cluster if topic modeling needs bertopic/torch)"
    fi
  fi
}

stage_golden_copy() {
  hdr "Golden copy"
  local pybin="${VENV_PYTHON:-python3}"
  run "$pybin" -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault "$VAULT_PATH" stage \
    || warn "golden copy not staged — run memoria runtime golden_restore stage manually (lint:restore needs it)"
  ok "Golden copy staged (.memoria/golden/)"
}

print_cli_next_steps() {
  hdr "Next steps"
  local pycmd="${VENV_PYTHON:-$VAULT_PATH/.memoria/.venv/bin/python}"
  [ -n "$VAULT_PATH" ] && say "  Workspace: $VAULT_PATH"
  say "  1. Check the bundle:  \"$pycmd\" -m memoria_vault.cli doctor bundle --workspace \"$VAULT_PATH\""
  say "  2. Rebuild search:    \"$pycmd\" -m memoria_vault.cli workspace rebuild --workspace \"$VAULT_PATH\" --search"
  say "  3. Ask from CLI:      \"$pycmd\" -m memoria_vault.cli ask --workspace \"$VAULT_PATH\" --question \"What needs attention?\""
  say "  4. First checkpoint:  cd \"$VAULT_PATH\" && git add -A && git commit -m \"Initial Memoria vault\""
  [ "$DRY_RUN" -eq 1 ] && warn "This was a DRY RUN — nothing above was actually changed."
  return 0
}

# =============================================================================
# main  (wrapped so a truncated `curl | bash` download can't execute a partial run)
# =============================================================================
main() {
  parse_args "$@"

  print_plan
  confirm "Proceed with the standalone Memoria install?" || die "Aborted — nothing changed."
  ensure_prereqs
  resolve_repo
  load_install_modules
  copy_vault
  install_mcp_deps
  stage_golden_copy
  ensure_qmd
  print_cli_next_steps
  hdr "Done"
}

main "$@"
