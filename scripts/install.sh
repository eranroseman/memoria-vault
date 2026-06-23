#!/usr/bin/env bash
# =============================================================================
# Memoria bootstrap installer  (Linux/WSL testing path; Windows production uses install.ps1)
# =============================================================================
# One command sets up the Linux/WSL test system: clones the vault, installs Hermes,
# verifies ACP, deploys the five memoria-* profiles, provisions skills, and guides
# the GUI app (Obsidian). macOS is not supported. (Zotero: see the tutorial.)
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
#   --profiles-only   skip the bootstrap; just (re)deploy profiles from an existing vault
#                     (the maintenance path — run after editing the vault source)
#   --only NAMES      restrict the profile step to these (comma-separated), e.g.
#                     --only memoria-librarian — pairs with --profiles-only
#   --no-apps         skip the Obsidian guidance (headless / server installs)
#   --dry-run         print every command that WOULD run; change nothing
#   --yes             non-interactive: accept all defaults, no prompts (CI)
#   -h | --help       this help
#
# Safety: no silent privilege escalation. Any step needing root prints the exact
# `sudo` command and runs it only on your confirmation (apt will prompt for your
# password). --dry-run echoes everything and touches nothing.
#
# Honors $HERMES_HOME (default ~/.hermes), matching Hermes's own convention.
# Honors $MEMORIA_ENV for Linux/WSL test profile model wiring:
#   prod (default) -> shipped Kilo Code gateway tiers
#   test           -> local OpenAI-compatible Ollama endpoint
# =============================================================================
set -euo pipefail

# --- constants ---------------------------------------------------------------
REPO_URL="https://github.com/eranroseman/memoria-vault.git"
REPO_BRANCH="main"
KDENSE_URL="https://github.com/K-Dense-AI/scientific-agent-skills"
HERMES_DOCS="https://hermes-agent.nousresearch.com/docs/getting-started/installation"
ACP_DOCS="https://hermes-agent.nousresearch.com/docs/integrations/acp"
DEFAULT_TARGET="$HOME/Memoria"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_PROFILES_DIR="$HERMES_HOME/profiles"
HERMES_SKILLS_DIR="$HERMES_HOME/skills"
MEMORIA_ENV="${MEMORIA_ENV:-prod}"

ALL_PROFILES="memoria-copi memoria-librarian memoria-writer memoria-peer-reviewer memoria-engineer"
REQUIRED_FILES="SOUL.md config.yaml distribution.yaml"

# Official Hermes skills we rely on, allowed by name in the lane-overrides. Per the
# official catalog (skills-catalog.md) these are BUNDLED: the Hermes install (step 3)
# copies them to ~/.hermes/skills/<category>/<name>. They are NOT on the skills hub, so
# `hermes skills install official/...` 404s on them (#59) — we verify presence, never fetch.
# Paths are on-disk relative (no `official/` prefix), matching the bundled layout.
BUNDLED_SKILLS="research/arxiv research/llm-wiki note-taking/obsidian productivity/ocr-and-documents github/github-repo-management autonomous-ai-agents/codex autonomous-ai-agents/claude-code"
OPTIONAL_SKILLS="research/qmd"

# Official Hermes installer (Linux/WSL2) — provisions uv-Python, Node, git-bash, ripgrep, ffmpeg.
HERMES_INSTALL_URL="https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh"

# --- flags -------------------------------------------------------------------
DRY_RUN=0
ASSUME_YES=0
PROFILES_ONLY=0
NO_APPS=0
VAULT_OVERRIDE=""
ONLY=""

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

# Escape a value for use as the replacement side of s|needle|replacement|g.
sed_repl() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
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

ensure_memoria_css_snippets() {
  local src="${REPO_DIR:-}/src"
  if [ ! -d "$src/.obsidian" ]; then
    local script_dir=""
    if [ -f "${BASH_SOURCE[0]:-}" ]; then
      script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    fi
    if [ -n "$script_dir" ] && [ -d "$script_dir/../src/.obsidian" ]; then
      src="$(cd "$script_dir/.." && pwd)/src"
    else
      src="$VAULT_PATH"
    fi
  fi
  local appearance="$VAULT_PATH/.obsidian/appearance.json"
  local snippet_dir="$VAULT_PATH/.obsidian/snippets"
  local snippet

  run mkdir -p "$snippet_dir"
  for snippet in memoria-link-colors.css memoria-property-badges.css; do
    if [ -f "$src/.obsidian/snippets/$snippet" ] && [ ! -f "$snippet_dir/$snippet" ]; then
      run cp "$src/.obsidian/snippets/$snippet" "$snippet_dir/$snippet"
    fi
  done

  if [ "$DRY_RUN" -eq 1 ]; then
    run "${PYTHON:-python3}" - "$appearance" memoria-link-colors memoria-property-badges
    return
  fi

  "${PYTHON:-python3}" - "$appearance" memoria-link-colors memoria-property-badges <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
required = sys.argv[2:]
path.parent.mkdir(parents=True, exist_ok=True)
try:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
except json.JSONDecodeError as exc:
    raise SystemExit(f"{path} is not valid JSON; fix it or remove it, then rerun the installer: {exc}")
enabled = data.get("enabledCssSnippets")
if not isinstance(enabled, list):
    enabled = []
for snippet in required:
    if snippet not in enabled:
        enabled.append(snippet)
data["enabledCssSnippets"] = enabled
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
  ok "Memoria CSS snippets enabled in .obsidian/appearance.json"
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
      --only) ONLY="${2:-}"; shift 2 ;;
      --only=*) ONLY="${1#*=}"; shift ;;
      --profiles-only) PROFILES_ONLY=1; shift ;;
      --no-apps) NO_APPS=1; shift ;;
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
  say "This will, with your confirmation at each external step:"
  say "  1. ensure prerequisites (git, pandoc)"
  say "  2. fetch the Memoria vault repo"
  say "  3. install Hermes (official installer) + verify ACP"
  say "  4. copy the runtime vault to your chosen folder"
  say "  5. install MCP server dependencies (pip)"
  say "  6. deploy the five memoria-* Hermes profiles"
  say "  7. provision skills (K-Dense clone, official qmd optional skill, kepano hub skill)"
  say "  8. guide the Obsidian install (Zotero moved to the tutorial)"
  say "  9. print where to put your API keys + next steps"
  [ "$DRY_RUN" -eq 1 ] && { say ""; warn "DRY RUN — nothing will be changed."; }
  return 0
  say ""
}

# =============================================================================
# Step 1 — prerequisites (Hermes provisions uv/python/node/ripgrep/ffmpeg itself)
# =============================================================================
ensure_prereqs() {
  hdr "Prerequisites"
  local missing=""
  have git    || missing="$missing git"
  have pandoc || missing="$missing pandoc"
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
  if [ -z "$missing" ]; then ok "git, pandoc, and venv support present"; return; fi

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
}

# =============================================================================
# Step 2 — locate or clone the repo  (sets REPO_DIR)
# =============================================================================
resolve_repo() {
  hdr "Memoria vault source"
  # Running from inside a clone? (script dir or cwd has src/.memoria)
  local sdir=""
  if [ -f "${BASH_SOURCE[0]:-}" ]; then
    sdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [ -n "$sdir" ] && [ -d "$sdir/src/.memoria" ]; then
    REPO_DIR="$sdir"; ok "Using the clone this script lives in: $REPO_DIR"; return
  fi
  if [ -d "./src/.memoria" ]; then
    REPO_DIR="$(pwd)"; ok "Using the clone in the current directory: $REPO_DIR"; return
  fi
  # Piped (curl | bash): clone fresh into a temp/staging dir (removed on exit).
  REPO_DIR="$(mktemp -d "${TMPDIR:-/tmp}/memoria-repo-XXXXXXXX")"
  STAGING_REPO="$REPO_DIR"
  say "Not run from a clone — fetching the repo to a staging dir."
  run git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
  [ "$DRY_RUN" -eq 1 ] || [ -d "$REPO_DIR/src/.memoria" ] || die "Clone did not contain src/.memoria."
  ok "Cloned to $REPO_DIR"
}

# =============================================================================
# Step 3 — Hermes + ACP
# =============================================================================
ensure_hermes() {
  hdr "Hermes runtime"
  detect_python
  if have hermes; then
    ok "Hermes found at $(command -v hermes)"
  else
    warn "Hermes is not on PATH."
    say "Installing via the official installer (provisions uv-Python, Node, git-bash, ripgrep, ffmpeg)."
    say "Docs: $HERMES_DOCS"
    if confirm "Install Hermes now (curl $HERMES_INSTALL_URL | bash)?"; then
      run_sh "curl -fsSL '$HERMES_INSTALL_URL' | bash"
      detect_python
      if [ "$DRY_RUN" -eq 0 ] && ! have hermes; then
        warn "Hermes installed, but not on PATH in this shell (the installer edits PATH)."
        warn "Open a NEW shell, then finish with:  bash scripts/install.sh --profiles-only --vault \"${VAULT_OVERRIDE:-~/Memoria}\""
      fi
    else
      die "Install Hermes (see $HERMES_DOCS), then re-run with --profiles-only to finish."
    fi
  fi
  # The agent-client Obsidian pane needs `hermes acp`. The official installer with
  # [all] includes it; nonstandard installs add it in Hermes's uv environment.
  if [ "$DRY_RUN" -eq 0 ] && have hermes; then
    if hermes acp --help >/dev/null 2>&1; then
      ok "ACP available (hermes acp)"
    else
      warn "hermes acp not available — run: cd \"$HERMES_HOME/hermes-agent\" && uv pip install -e '.[acp]'  Docs: $ACP_DOCS"
    fi
  fi
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

  local src="$REPO_DIR/src"
  [ -d "$src/.memoria" ] || die "No vault at $src (.memoria missing)."

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

  # Stage the golden copy (ADR-55): a canonical copy of every system file with a
  # hash manifest at <vault>/.memoria/golden/.
  local pybin="${VENV_PYTHON:-python3}"
  run "$pybin" "$VAULT_PATH/.memoria/operations/integrity/linter/golden_restore.py" --vault "$VAULT_PATH" stage \
    || warn "golden copy not staged — run golden_restore.py stage manually (lint:restore needs it)"
  ok "Golden copy staged (.memoria/golden/)"

  ensure_memoria_css_snippets

  wire_commit_gate
  wire_verify_on_commit_hook

  # Seed the per-machine Obsidian plugin config that does NOT self-generate.
  # `obsidian-local-rest-api` regenerates its own data.json (apiKey + TLS material)
  # on first Obsidian launch, so we leave it alone. `agent-client` does not — seed
  # it from the example. First-install only; never clobber an edited one.
  # `windowsWslMode` is only for the Linux/WSL test path where Obsidian is on
  # Windows but Hermes runs inside WSL. Production Windows uses install.ps1 and
  # leaves the shipped native-Hermes default alone.
  local acp_dir="$VAULT_PATH/.obsidian/plugins/agent-client"
  if [ -f "$acp_dir/data.json.example" ] && [ ! -f "$acp_dir/data.json" ]; then
    local wsl_mode=false
    if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || [ -n "${WSL_DISTRO_NAME:-}" ]; then
      wsl_mode=true
    fi
    run_sh "sed -e 's|{{HOME}}|$HOME|g' -e 's|\"windowsWslMode\": false|\"windowsWslMode\": $wsl_mode|' \
                \"$acp_dir/data.json.example\" > \"$acp_dir/data.json\""
    say "  seeded agent-client/data.json from its example ({{HOME}} -> $HOME, windowsWslMode: $wsl_mode)"
  fi

  # The runtime vault is the user's own repo — they set up git themselves, with
  # their own identity and remote. We don't `git init`/commit under a synthetic
  # author. obsidian-git needs a repo to commit into, so point the way:
  if [ ! -d "$VAULT_PATH/.git" ]; then
    say "  This folder is your vault — set up your own git here (obsidian-git needs a repo):"
    say "      cd \"$VAULT_PATH\""
    say "      git init && git add -A && git commit -m \"Initial Memoria vault\""
    say "      (then re-run with --profiles-only to wire the git hooks)"
    say "      git remote add origin <your-repo-url>   # optional — backup / multi-machine sync"
  fi
}

# =============================================================================
# Step 5 — MCP server dependencies
# =============================================================================
# Deps go into a vault-local venv ($VAULT_PATH/.memoria/.venv). This sidesteps
# modern Ubuntu/Debian's PEP-668 "externally-managed-environment" pip block, keeps
# Memoria's deps off the system site-packages, and gives a stable interpreter path
# that install_profiles wires into config.yaml (see PYTHON_BIN below).
install_mcp_deps() {
  hdr "MCP server dependencies"
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
      ok "MCP dependencies installed (user site-packages, system override)"
      return
    fi
  fi
  VENV_PYTHON="$venv/bin/python"
  run "$VENV_PYTHON" -m pip install --quiet --upgrade pip
  run "$VENV_PYTHON" -m pip install --quiet -r "$reqs" || die "pip install of MCP deps into the venv failed."
  run "$VENV_PYTHON" -m pip install --quiet "$REPO_DIR" || die "Memoria package install into the venv failed."
  ok "MCP dependencies installed into $venv"

  # Optional heavy stack (ADR-33): the cluster MCP's topic modeling needs
  # bertopic (-> torch). Graph tools work without it; offer, don't force.
  if [ -f "$VAULT_PATH/.memoria/mcp/requirements-cluster.txt" ]; then
    if confirm "Install the OPTIONAL clustering stack (bertopic -> torch, ~2GB)? Topic modeling needs it; graph analysis does not."; then
      run "$VENV_PYTHON" -m pip install --quiet -r "$VAULT_PATH/.memoria/mcp/requirements-cluster.txt" \
        || warn "cluster deps failed — install later: $VENV_PYTHON -m pip install -r .memoria/mcp/requirements-cluster.txt"
    else
      say "  (skipped — cluster_model_topics will error cleanly until installed)"
    fi
  fi
}

# Seed shared secrets into a profile's .env. Hermes profile runs read ONLY the
# profile's own .env -- there is NO global ~/.hermes/.env inheritance (confirmed
# live, Tier-4: `hermes -p <p> config env-path` resolves to the profile .env, and a
# profile run with keys only in the global .env fails "no API key found"). So every
# shared key (model + obsidian + per-lane API keys) must live in EACH profile's
# .env. Copy each key the profile declares in its .env.EXAMPLE from the global
# ~/.hermes/.env when the global has a non-empty value, without overwriting a value
# already present in the profile .env. Idempotent -- the maintenance path is to put
# keys in $HERMES_HOME/.env, then re-run `--profiles-only` to propagate them.
seed_profile_env() {
  local pdir="$1" name; name=$(basename "$pdir")
  local penv="$pdir/.env" pexample="$pdir/.env.EXAMPLE" globalenv="$HERMES_HOME/.env"
  if [ "$DRY_RUN" -eq 1 ]; then printf '  + (dry-run) would seed %s/.env from %s\n' "$name" "$globalenv"; return 0; fi
  [ -f "$globalenv" ] && [ -f "$pexample" ] || return 0
  local seeded=0 k line
  for k in $(grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' "$pexample" | tr -d '='); do
    grep -qE "^$k=" "$penv" 2>/dev/null && continue          # already set in the profile .env
    # a NON-empty value in the global .env (|| true: missing key must not abort under set -e+pipefail)
    line=$(grep -E "^$k=.+" "$globalenv" | head -1 || true)
    [ -n "$line" ] && { printf '%s\n' "$line" >> "$penv"; seeded=$((seeded + 1)); }
  done
  [ "$seeded" -gt 0 ] && say "    seeded $seeded shared key(s) into $name/.env from $HERMES_HOME/.env"
  return 0
}

# deploy_policy_plugin PROFILE_DIR PROFILE  — install the policy-gate plugin into
# a deployed profile's plugins/ dir, substituting the per-lane placeholders.
#
# This is the vault WRITE GATE (ADR-28). It replaces the old `hooks:` shell hook,
# which never fired: Hermes registers MCP tools as `mcp_<server>_<tool>` (the
# obsidian write is `mcp_obsidian_obsidian_append_content`), the shell-hook
# matcher uses `re.fullmatch`, so `obsidian.*` matched nothing — and shell hooks
# are consent-gated + fail-OPEN. The plugin runs in-process in every mode
# (-z/gateway/cron/ACP), matches in Python, gets the task_id, and is fail-CLOSED.
# Enabled per lane via `plugins.enabled` in the deployed config.yaml.
deploy_policy_plugin() {
  local profile_dir="$1" prof="$2"
  local plugin_src="$VAULT_PATH/.memoria/plugins/memoria-policy-gate"
  local plugin_dst="$profile_dir/plugins/memoria-policy-gate"
  if [ ! -d "$plugin_src" ]; then
    die "policy-gate plugin source missing at $plugin_src — refusing to deploy $prof without the write gate"
  fi
  run mkdir -p "$plugin_dst"
  run cp "$plugin_src/plugin.yaml" "$plugin_dst/plugin.yaml"
  # Substitute {{PROFILE}} and {{VAULT_PATH}} into the plugin code (mirrors the
  # config.yaml substitution; the plugin runs in the Hermes process, so no PYTHON).
  if [ -f "$plugin_src/__init__.py" ]; then
    local prof_esc vault_esc
    prof_esc="$(sed_repl "$prof")"
    vault_esc="$(sed_repl "$VAULT_PATH")"
    run_sh "sed -e 's|{{PROFILE}}|$prof_esc|g' -e 's|{{VAULT_PATH}}|$vault_esc|g' \
                \"$plugin_src/__init__.py\" > \"$plugin_dst/__init__.py\""
  fi
  say "    deployed write-gate plugin (memoria-policy-gate)"
}

sync_profile_skills() {
  local staged_profile="$1" profile_dir="$2"
  local staged_skills="$staged_profile/skills"
  local profile_skills="$profile_dir/skills"

  case "$profile_dir" in
    "$HERMES_PROFILES_DIR"/*) ;;
    *) die "Refusing to reconcile skills outside $HERMES_PROFILES_DIR: $profile_dir" ;;
  esac

  if [ -d "$staged_skills" ]; then
    run rm -rf "$profile_skills"
    run mkdir -p "$profile_skills"
    if have rsync; then
      run rsync -a "$staged_skills"/ "$profile_skills"/
    else
      run_sh "cp -R \"$staged_skills\"/. \"$profile_skills\"/"
    fi
    say "    refreshed profile skills from source"
  elif [ -f "$staged_profile/.no-bundled-skills" ]; then
    run rm -rf "$profile_skills"
    run mkdir -p "$profile_skills"
    say "    cleared profile skills (source opts out of bundled skills)"
  fi
}

remove_legacy_profile_mcp_json() {
  local profile_dir="$1"
  case "$profile_dir" in
    "$HERMES_PROFILES_DIR"/*) ;;
    *) die "Refusing to remove legacy mcp.json outside $HERMES_PROFILES_DIR: $profile_dir" ;;
  esac
  if [ -e "$profile_dir/mcp.json" ]; then
    run rm -f "$profile_dir/mcp.json"
    say "    removed legacy mcp.json (config.yaml owns MCP servers)"
  fi
}

verify_profile_obsidian_mcp() {
  local cfg="$1" prof="$2"
  [ -f "$cfg" ] || die "$prof config.yaml missing after staging."
  grep -q 'url: "https://127\.0\.0\.1:${OBSIDIAN_MCP_PORT}/mcp"' "$cfg" \
    || die "$prof config.yaml must use https://127.0.0.1:\${OBSIDIAN_MCP_PORT}/mcp for the Obsidian MCP."
  grep -q 'ssl_verify: "${OBSIDIAN_MCP_SSL_VERIFY}"' "$cfg" \
    || die "$prof config.yaml must set obsidian ssl_verify to \${OBSIDIAN_MCP_SSL_VERIFY}."
}

profile_model_default() {
  case "$1" in
    memoria-copi|memoria-peer-reviewer) printf '%s' '~anthropic/claude-opus-latest' ;;
    memoria-writer) printf '%s' '~anthropic/claude-sonnet-latest' ;;
    memoria-librarian|memoria-engineer) printf '%s' '~anthropic/claude-haiku-latest' ;;
    *) die "Unknown profile for model overlay: $1" ;;
  esac
}

profile_model_overlay() {
  local prof="$1"
  MODEL_PROVIDER=""
  MODEL_BASE_URL=""
  MODEL_DEFAULT=""
  MODEL_CONTEXT_LENGTH=""

  case "$MEMORIA_ENV" in
    prod|"")
      MODEL_PROVIDER="kilocode"
      MODEL_BASE_URL="https://api.kilo.ai/api/gateway"
      MODEL_DEFAULT="$(profile_model_default "$prof")"
      MODEL_CONTEXT_LENGTH=""
      ;;
    test)
      MODEL_PROVIDER="custom"
      MODEL_BASE_URL="${MEMORIA_MODEL_BASE_URL:-http://127.0.0.1:11434/v1}"
      MODEL_DEFAULT="${MEMORIA_MODEL_NAME:-qwen2.5:7b}"
      MODEL_CONTEXT_LENGTH="${MEMORIA_MODEL_CONTEXT_LENGTH:-65536}"
      ;;
    *)
      die "Unsupported MEMORIA_ENV=$MEMORIA_ENV (expected prod or test)."
      ;;
  esac
}

# =============================================================================
# Step 6 — deploy the five profiles  (the original profile-installer logic)
# =============================================================================
install_profiles() {
  hdr "Hermes profiles"
  local profiles_src="$VAULT_PATH/.memoria/profiles"
  if [ ! -d "$profiles_src" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then warn "(dry-run) vault not copied yet; would deploy from $profiles_src"; return; fi
    die "No profiles at $profiles_src."
  fi
  if ! have hermes; then
    warn "Hermes not on PATH — cannot deploy profiles. Install Hermes, then: bash scripts/install.sh --profiles-only --vault \"$VAULT_PATH\""
    return
  fi

  # Resolve which profiles to (re)deploy: all, or the --only subset.
  local targets="$ALL_PROFILES"
  if [ -n "$ONLY" ]; then
    targets=""
    local want
    for want in $(printf '%s' "$ONLY" | tr ',' ' '); do
      case " $ALL_PROFILES " in *" $want "*) targets="$targets $want" ;;
        *) warn "Unknown profile in --only: $want (ignored)" ;; esac
    done
    [ -n "$targets" ] || die "--only matched no known profiles."
  fi

  local staging installed="" skipped=""
  staging="$(mktemp -d "${TMPDIR:-/tmp}/memoria-staging-XXXXXXXX")"
  # shellcheck disable=SC2064
  trap "rm -rf '$staging'" RETURN

  local p src missing f dst env_example env_file
  for p in $targets; do
    src="$profiles_src/$p"
    if [ ! -d "$src" ]; then skipped="$skipped\n    [-] $p: source missing"; continue; fi

    missing=""
    for f in $REQUIRED_FILES; do [ -f "$src/$f" ] || missing="$missing $f"; done
    if [ -n "$missing" ]; then skipped="$skipped\n    [-] $p: missing$missing"; continue; fi

    say "  staging $p"
    dst="$staging/$p"
    run cp -R "$src" "$dst"
    # Substitute placeholders in config.yaml — the single file Hermes reads for
    # model / mcp_servers / plugins / agent / terminal (ADR-27; a
    # standalone mcp.json is never loaded, so it is not shipped). POSIX paths are
    # already forward-slash, so no conversion is needed.
    #   - {{PYTHON}}     -> the venv interpreter, so the policy MCP server + the
    #                       policy hook import mcp+PyYAML from where install_mcp_deps
    #                       put them (not bare system python).
    #   - {{VAULT_PATH}} -> the real vault path.
    #   - {{MODEL_*}}    -> prod cloud tiers by default, or local Ollama-compatible
    #                       wiring when MEMORIA_ENV=test.
    local pybin="${VENV_PYTHON:-python}"
    if [ -f "$dst/config.yaml" ]; then
      local pybin_esc vault_esc qmd_esc model_provider_esc model_base_url_esc model_default_esc
      profile_model_overlay "$p"
      pybin_esc="$(sed_repl "$pybin")"
      vault_esc="$(sed_repl "$VAULT_PATH")"
      qmd_esc="$(sed_repl "${QMD_BIN:-qmd}")"
      model_provider_esc="$(sed_repl "$MODEL_PROVIDER")"
      model_base_url_esc="$(sed_repl "$MODEL_BASE_URL")"
      model_default_esc="$(sed_repl "$MODEL_DEFAULT")"
      run_sh "sed -e 's|{{PYTHON}}|$pybin_esc|g' \
                  -e 's|{{VAULT_PATH}}|$vault_esc|g' \
                  -e 's|{{QMD}}|$qmd_esc|g' \
                  -e 's|{{MODEL_PROVIDER}}|$model_provider_esc|g' \
                  -e 's|{{MODEL_BASE_URL}}|$model_base_url_esc|g' \
                  -e 's|{{MODEL_DEFAULT}}|$model_default_esc|g' \
                  \"$dst/config.yaml\" > \"$dst/config.yaml.tmp\" && mv \"$dst/config.yaml.tmp\" \"$dst/config.yaml\""
      run_sh "awk -v ctx=\"$MODEL_CONTEXT_LENGTH\" '
                  /# \\{\\{MODEL_LOCAL_CONTEXT\\}\\}/ {
                    if (ctx != \"\") {
                      print \"  context_length: \" ctx
                      print \"  ollama_num_ctx: \" ctx
                    }
                    next
                  }
                  { print }
                ' \"$dst/config.yaml\" > \"$dst/config.yaml.tmp\" && mv \"$dst/config.yaml.tmp\" \"$dst/config.yaml\""
      verify_profile_obsidian_mcp "$dst/config.yaml" "$p"
    fi

    say "  installing $p"
    # `hermes profile install` takes the name from the manifest (or --name to
    # override); --alias is a BARE flag (create a shell wrapper), NOT --alias NAME.
    # Passing `--alias "$p"` made Hermes treat "$p" as a stray positional and the
    # whole install errored out ("unrecognized arguments"). Use --name explicitly.
    if run hermes profile install "$dst" --name "$p" --alias --force --yes; then
      installed="$installed $p"
      # Hermes preserves some deployed profile files as user-owned. Memoria owns
      # the rendered config.yaml because it carries the vault path, MCP commands,
      # policy plugin enablement, and MEMORIA_ENV model overlay; refresh it
      # explicitly so --profiles-only cannot leave stale host-side model wiring.
      run cp "$dst/config.yaml" "$HERMES_PROFILES_DIR/$p/config.yaml"
      remove_legacy_profile_mcp_json "$HERMES_PROFILES_DIR/$p"
      # Memoria owns each shipped profile's skills directory. Hermes preserves
      # absent distribution paths on force-install, so reconcile it explicitly to
      # remove stale bundled skills from profiles that opt out.
      sync_profile_skills "$dst" "$HERMES_PROFILES_DIR/$p"
      # Capability layer (ADR-27): each profile's config.yaml already carries
      # positive platform_toolsets plus a small disabled_toolsets backstop, so
      # the only vault-write path is the gated obsidian MCP. It ships in the
      # source config — nothing to inject here.
      # Bootstrap .env from .env.EXAMPLE on FIRST install only (never clobber creds).
      env_example="$HERMES_PROFILES_DIR/$p/.env.EXAMPLE"
      env_file="$HERMES_PROFILES_DIR/$p/.env"
      if [ "$DRY_RUN" -eq 0 ] && [ -f "$env_example" ] && [ ! -f "$env_file" ]; then
        # Copy the template but DROP empty-valued lines (`FOO=`) so the profile .env
        # starts with no blank keys. Real values are seeded next from the global env.
        grep -vE '^[A-Za-z_][A-Za-z0-9_]*=[[:space:]]*$' "$env_example" > "$env_file" || :
        say "    created .env from .env.EXAMPLE"
      fi
      # Propagate shared secrets from $HERMES_HOME/.env into this profile's .env --
      # profile runs do NOT read the global .env (Tier-4), so keys must be per-profile.
      # Runs every install (idempotent): fill the global .env, re-run --profiles-only.
      seed_profile_env "$HERMES_PROFILES_DIR/$p"
      # Deploy the write-gate plugin (ADR-28) into this profile, substituted per lane.
      # `plugins.enabled` in the deployed config.yaml turns it on.
      deploy_policy_plugin "$HERMES_PROFILES_DIR/$p" "$p"
    else
      skipped="$skipped\n    [-] $p: hermes profile install failed"
    fi
  done

  local count=0; for p in $installed; do count=$((count + 1)); done
  ok "Profiles installed: $count"
  for p in $installed; do say "    [+] $p"; done
  [ -n "$skipped" ] && printf '  Skipped:%b\n' "$skipped"
  trap - RETURN
  rm -rf "$staging"

}

# =============================================================================
# Step 7 — skills  (see docs/explanation/deployment/bootstrap-installer.md, "Pinned skill install IDs")
# =============================================================================
install_skills() {
  hdr "Skills"
  if ! have hermes && ! have git; then warn "Neither hermes nor git — skipping skills."; return; fi
  run mkdir -p "$HERMES_SKILLS_DIR"

  # A. K-Dense bundle (paper-lookup, pyzotero, citation-management, literature-review,
  #    scientific-writing, scikit-learn, umap-learn) — a clone; auto-discovered.
  local kdense_dir="$HERMES_SKILLS_DIR/scientific-agent-skills"
  if [ -d "$kdense_dir/.git" ]; then
    say "  K-Dense present — updating"
    run_sh "git -C \"$kdense_dir\" pull --ff-only || true"
  else
    run git clone --depth 1 "$KDENSE_URL" "$kdense_dir" || warn "K-Dense clone failed — clone it manually into $HERMES_SKILLS_DIR"
  fi

  # B. Official bundled skills — verify, do NOT install. These ship with Hermes
  # (step 3 copies them into ~/.hermes/skills/); they are not on the hub, so
  # `hermes skills install` 404s on them (#59). Just confirm they landed.
  local s
  for s in $BUNDLED_SKILLS; do
    if [ -f "$HERMES_SKILLS_DIR/$s/SKILL.md" ]; then
      say "  bundled present — $s"
    else
      warn "bundled skill '$s' not found under $HERMES_SKILLS_DIR — re-run the Hermes installer (step 3); it ships this skill."
    fi
  done
  for s in $OPTIONAL_SKILLS; do
    if [ -f "$HERMES_SKILLS_DIR/$s/SKILL.md" ]; then
      say "  optional present — $s"
    elif have hermes; then
      run hermes skills install "official/$s" --yes \
        || warn "official optional skill '$s' not installed — install manually: hermes skills install official/$s --yes"
    else
      warn "Hermes not on PATH — skipped official optional skill '$s'."
    fi
  done

  # C. Hub skills — these ARE on the skills hub and must be fetched. --yes skips
  # the per-skill confirm prompt (non-interactive; without it Hermes auto-cancels
  # with no tty). We deliberately do NOT pass --force: a skill the scanner flags
  # DANGEROUS should stay blocked — warn-not-fail and move on.
  if have hermes; then
    # kepano obsidian-markdown
    run hermes skills install kepano/obsidian-skills/skills/obsidian-markdown --yes \
      || warn "kepano obsidian-markdown not installed — see the design doc for the clone fallback"
  else
    warn "Hermes not on PATH — skipped kepano hub-skill install."
  fi

  say "  (the memoria <task>:<verb>-<object> skills — catalog-enrich-record, verify-check-citation, … — ship inside the vault profiles; nothing to fetch.)"
  ok "Skills step complete"
}

# =============================================================================
# Step 8 — GUI apps (guided, not silent)
# =============================================================================
ensure_obsidian() {
  hdr "Obsidian"
  if have obsidian || (have flatpak && flatpak info md.obsidian.Obsidian >/dev/null 2>&1); then
    ok "Obsidian present"
  else
    say "Obsidian is a GUI app — install it yourself, then open the vault at:"
    say "    $VAULT_PATH"
    if have flatpak; then
      say "  Flatpak:  flatpak install -y flathub md.obsidian.Obsidian"
      confirm "Install via Flatpak now?" && run flatpak install -y flathub md.obsidian.Obsidian
    else
      say "  Download the .deb / AppImage: https://obsidian.md/download"
      say "  (.deb:  sudo apt-get install -y ./Obsidian-*.deb )"
    fi
  fi
  say "  On first launch: turn off Restricted mode so the nine bundled plugins load."
}



# =============================================================================
# Step 9 — secrets + next steps
# =============================================================================
print_secrets_guidance() {
  hdr "API keys (you add these — never commit them)"
  say "1. Put your keys in  $HERMES_HOME/.env  (the global file):"
  say "    KILOCODE_API_KEY=...        # model access (shipped provider: kilocode / kilo.ai)"
  say "    OBSIDIAN_API_KEY=...        # 64-char hex from the Obsidian REST API plugin"
  say "    OPENALEX_API_KEY=...        # Librarian — openalex.org/settings/api (required since 2026-02)"
  say "2. Propagate them into every profile (Hermes profile runs read ONLY the"
  say "   profile's own .env — there is no global fallback):"
  say "       bash scripts/install.sh --profiles-only --vault \"${VAULT_PATH:-<vault>}\""
  say "   (re-run this any time you add or rotate a key in $HERMES_HOME/.env.)"
  say "Full guide: https://eranroseman.github.io/memoria-vault/how-to-guides/setup/set-up-hermes/"
}

print_next_steps() {
  hdr "Next steps"

  say "  1. Fill in the .env secrets (above)."
  [ -n "$VAULT_PATH" ] && say "  2. Open this folder in Obsidian as your vault:  $VAULT_PATH"
  say "  3. Verify the profiles:        hermes profile list"
  say "  4. Open the Agent Client pane in Obsidian, or test it with: hermes -p memoria-copi acp"
  say "  5. Open the Library gate from the Obsidian gate nav row"
  say "  6. Zotero (optional backbone): see the bring-in-a-paper tutorial on the docs site"
  # obsidian-git needs a repo to commit into; we deliberately don't auto-init (the
  # vault is the user's own repo). Surface the one-liner only if it's not a repo yet.
  if [ -n "$VAULT_PATH" ] && [ ! -d "$VAULT_PATH/.git" ]; then
    say ""
    say "  Tip: obsidian-git needs the vault to be a git repo (we don't auto-init — it's yours):"
    say "         cd \"$VAULT_PATH\" && git init && git add -A && git commit -m \"Initial Memoria vault\""
    say "         (then: bash scripts/install.sh --profiles-only --vault \"$VAULT_PATH\" — wires the pre-commit schema gate)"
  fi
  say ""
  say "Re-deploy after editing the vault source:  bash scripts/install.sh --profiles-only --vault \"${VAULT_PATH:-<vault>}\""
  # NB: trailing `&&` test must not become the function's (and script's) exit
  # status — on a real run [ "$DRY_RUN" -eq 1 ] is false and would exit 1.
  [ "$DRY_RUN" -eq 1 ] && warn "This was a DRY RUN — nothing above was actually changed."
  return 0
}

# =============================================================================
# --profiles-only: resolve which vault to deploy from, then deploy.
# =============================================================================
resolve_vault_for_profiles() {
  if [ -n "$VAULT_OVERRIDE" ]; then VAULT_PATH="$VAULT_OVERRIDE"
  elif [ -d "./src/.memoria" ]; then VAULT_PATH="$(cd ./src && pwd)"
  elif [ -d "$DEFAULT_TARGET/.memoria" ]; then VAULT_PATH="$DEFAULT_TARGET"
  else die "Cannot find a vault. Pass --vault DIR (the folder containing .memoria/)."; fi
  case "$VAULT_PATH" in "~"/*) VAULT_PATH="$HOME/${VAULT_PATH#~/}" ;; esac
  ok "Deploying profiles from $VAULT_PATH"
}

# =============================================================================
# Step 6b — telemetry cron (board export). Wires the six-signal telemetry: a
# deterministic, no-LLM cron that projects the live Hermes kanban board to the
# vault and appends the operational logs. Global (not per-lane). Idempotent.
# =============================================================================
wire_telemetry_cron() {
  install_hermes_cron \
    "Telemetry cron (board export)" "telemetry" \
    "board-export-cron.sh" "memoria-board-export.sh" '* * * * *' "memoria-board-export" \
    "board-export" "telemetry" "board-export" " (see project-files/plans)" \
    "emits the six-signal telemetry; fires whenever the Hermes scheduler/gateway runs" \
    "Telemetry"
}

# =============================================================================
# Step 6c — re-ingest sweeps cron (ADR-30). A deterministic, no-LLM cron that
# runs the two backstops (reconcile + retry), each enqueueing idempotent
# re-ingest cards. Global (not per-lane). Idempotent.
# =============================================================================
wire_sweeps_cron() {
  install_hermes_cron \
    "Re-ingest sweeps cron" "sweeps" \
    "sweeps-cron.sh" "memoria-sweeps.sh" '*/15 * * * *' "memoria-sweeps" \
    "sweeps" "sweeps" "sweeps" " (see docs/reference/ingest.md)" \
    "recovers stalled captures every 15 min via idempotent re-ingest cards" \
    "Sweeps"
}

wire_lint_cron() {
  install_hermes_cron \
    "Linter cron" "lint" \
    "lint-cron.sh" "memoria-lint.sh" '0 6 * * *' "memoria-lint" \
    "lint" "lint" "lint" "" \
    "the engine monitors between commits: detectors + golden-copy drift, daily" \
    "Lint"
}

wire_metrics_cron() {
  install_hermes_cron \
    "Metrics cron (fleet health)" "metrics" \
    "metrics-cron.sh" "memoria-metrics.sh" '30 6 * * 1' "memoria-metrics" \
    "metrics" "metrics" "metrics" "" \
    "rolls audit + board + lint logs into system/metrics/ weekly for fleet-health" \
    "Metrics"
}

wire_eval_cron() {
  install_hermes_cron \
    "Eval cron (vault-eval, ADR-11)" "eval" \
    "eval-cron.sh" "memoria-eval.sh" '0 7 1 */3 *' "memoria-eval" \
    "eval" "eval" "eval" "" \
    "quarterly: fans the system/eval/ gold set out as idempotent eval cards — diagnostic, never gating" \
    "Eval"
}

# =============================================================================
# main  (wrapped so a truncated `curl | bash` download can't execute a partial run)
# =============================================================================
main() {
  parse_args "$@"

  if [ "$PROFILES_ONLY" -eq 1 ]; then
    load_install_modules
    ensure_git_available
    resolve_repo            # Memoria package install (install_mcp_deps) needs REPO_DIR
    resolve_vault_for_profiles
    install_mcp_deps
    ensure_memoria_css_snippets
    ensure_qmd
    install_profiles
    wire_telemetry_cron
    wire_sweeps_cron
    wire_lint_cron
    wire_metrics_cron
    wire_eval_cron
    wire_commit_gate
    wire_verify_on_commit_hook
    print_next_steps
    return
  fi

  print_plan
  confirm "Proceed with the full Memoria install?" || die "Aborted — nothing changed."
  ensure_prereqs
  resolve_repo
  load_install_modules
  ensure_hermes
  copy_vault
  install_mcp_deps
  ensure_qmd
  install_profiles
  install_skills
  wire_telemetry_cron
  wire_sweeps_cron
  wire_lint_cron
  wire_metrics_cron
  wire_eval_cron
  if [ "$NO_APPS" -eq 0 ]; then
    ensure_obsidian
    # Zotero setup moved to the tutorial (ADR-55) — it's the PI's bibliographic
    # backbone choice, not core provisioning.
  fi
  print_secrets_guidance
  print_next_steps
  hdr "Done"
}

main "$@"
