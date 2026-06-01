#!/usr/bin/env bash
# =============================================================================
# Memoria bootstrap installer  (Ubuntu/Debian, or WSL2 on Windows via install.ps1)
# =============================================================================
# One command sets up the whole system: clones the vault, installs Hermes + the
# ACP extra, deploys the seven memoria-* profiles, provisions skills, and guides
# the GUI apps (Obsidian, Zotero). macOS is not supported.
#
# Inspect-first (recommended):
#   curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh -o install.sh
#   less install.sh        # read it
#   bash install.sh        # then run it
#
# Convenience one-liner:
#   curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh | bash
#
# Flags:
#   --vault DIR       install the runtime vault here (default: ~/Memoria; prompted otherwise)
#   --profiles-only   skip the bootstrap; just (re)deploy profiles from an existing vault
#                     (the maintenance path — run after editing the vault source)
#   --only NAMES      restrict the profile step to these (comma-separated), e.g.
#                     --only memoria-linter  — pairs with --profiles-only
#   --no-apps         skip the Obsidian/Zotero guidance (headless / server installs)
#   --dry-run         print every command that WOULD run; change nothing
#   --yes             non-interactive: accept all defaults, no prompts (CI)
#   -h | --help       this help
#
# Safety: no silent privilege escalation. Any step needing root prints the exact
# `sudo` command and runs it only on your confirmation (apt will prompt for your
# password). --dry-run echoes everything and touches nothing.
#
# Honors $HERMES_HOME (default ~/.hermes), matching Hermes's own convention.
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

ALL_PROFILES="memoria-librarian memoria-mapper memoria-socratic memoria-writer memoria-verifier memoria-coder memoria-linter"
REQUIRED_FILES="SOUL.md config.yaml mcp.json distribution.yaml"

# Official Hermes skills (bundled with Hermes; allowed by name in the lane-overrides).
# TODO(confirm-at-build): whether these ship bundled or need `hermes skills install`.
# We attempt the install and warn-not-fail, so a bundled Hermes is also fine.
OFFICIAL_SKILLS="official/research/arxiv official/research/llm-wiki official/note-taking/obsidian official/productivity/ocr-and-documents official/github/github-repo-management official/autonomous-ai-agents/codex official/autonomous-ai-agents/claude-code"

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
STAGING_REPO=""   # set only when WE clone to temp; removed on exit (the runtime vault is the copy)

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

# ask "prompt" "default"  — echo the answer (default when --yes or no tty).
ask() {
  local prompt="$1" default="${2:-}" reply=""
  if [ "$ASSUME_YES" -eq 1 ]; then printf '%s' "$default"; return; fi
  if [ ! -t 0 ] && [ ! -r /dev/tty ]; then printf '%s' "$default"; return; fi
  read -r -p "$prompt " reply </dev/tty || reply=""
  printf '%s' "${reply:-$default}"
}
# confirm "prompt"  — 0 on yes. Defaults to NO unless --yes.
confirm() {
  if [ "$ASSUME_YES" -eq 1 ]; then return 0; fi
  if [ ! -t 0 ] && [ ! -r /dev/tty ]; then return 1; fi
  local reply=""
  read -r -p "$1 [y/N] " reply </dev/tty || reply="n"
  case "$reply" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

have() { command -v "$1" >/dev/null 2>&1; }

# Remove the temp/staging clone on exit (only the one we created — never the
# user's own clone when run inspect-first). The runtime vault is the copy.
cleanup() { [ -n "$STAGING_REPO" ] && [ -d "$STAGING_REPO" ] && rm -rf "$STAGING_REPO"; }
trap cleanup EXIT

detect_python() {
  if have python3; then PYTHON=python3
  elif have python; then PYTHON=python
  else PYTHON=""; fi
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
  say "  6. deploy the seven memoria-* Hermes profiles"
  say "  7. provision skills (K-Dense clone + official/kepano/qmd)"
  say "  8. guide the Obsidian and Zotero installs"
  say "  9. print where to put your API keys + next steps"
  [ "$DRY_RUN" -eq 1 ] && say "" && warn "DRY RUN — nothing will be changed."
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
  if [ -z "$missing" ]; then ok "git and pandoc present"; return; fi

  warn "Missing:$missing"
  if [ "$DRY_RUN" -eq 1 ]; then warn "(dry-run) would install:$missing"; return; fi
  if have apt-get; then
    say "The recommended install (needs root):"
    say "    sudo apt-get update && sudo apt-get install -y$missing"
    if confirm "Run it now?"; then
      run_sh "sudo apt-get update"
      run_sh "sudo apt-get install -y$missing"
    else
      die "Install$missing and re-run (Memoria needs them)."
    fi
  else
    die "No apt-get found. This installer supports Ubuntu/Debian (or WSL2). Install$missing manually."
  fi
}

# =============================================================================
# Step 2 — locate or clone the repo  (sets REPO_DIR)
# =============================================================================
resolve_repo() {
  hdr "Memoria vault source"
  # Running from inside a clone? (script dir or cwd has vault/.memoria)
  local sdir=""
  if [ -f "${BASH_SOURCE[0]:-}" ]; then
    sdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [ -n "$sdir" ] && [ -d "$sdir/vault/.memoria" ]; then
    REPO_DIR="$sdir"; ok "Using the clone this script lives in: $REPO_DIR"; return
  fi
  if [ -d "./vault/.memoria" ]; then
    REPO_DIR="$(pwd)"; ok "Using the clone in the current directory: $REPO_DIR"; return
  fi
  # Piped (curl | bash): clone fresh into a temp/staging dir (removed on exit).
  REPO_DIR="$(mktemp -d "${TMPDIR:-/tmp}/memoria-repo-XXXXXXXX")"
  STAGING_REPO="$REPO_DIR"
  say "Not run from a clone — fetching the repo to a staging dir."
  run git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
  [ "$DRY_RUN" -eq 1 ] || [ -d "$REPO_DIR/vault/.memoria" ] || die "Clone did not contain vault/.memoria."
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
        warn "Open a NEW shell, then finish with:  bash install.sh --profiles-only --vault \"${VAULT_OVERRIDE:-~/Memoria}\""
      fi
    else
      die "Install Hermes (see $HERMES_DOCS), then re-run with --profiles-only to finish."
    fi
  fi
  # The agent-client Obsidian pane needs `hermes acp`. The official installer may already
  # include it; verify rather than pip-install into the wrong (uv-managed) environment.
  # TODO(confirm-at-build): exact way to add the [acp] extra to the official install.
  if [ "$DRY_RUN" -eq 0 ] && have hermes; then
    if hermes acp --help >/dev/null 2>&1; then
      ok "ACP available (hermes acp)"
    else
      warn "hermes acp not available — add the ACP extra to Hermes's env (pip install 'hermes-agent[acp]'). Docs: $ACP_DOCS"
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

  local src="$REPO_DIR/vault"
  [ -d "$src/.memoria" ] || die "No vault at $src (.memoria missing)."

  if [ -d "$VAULT_PATH/.memoria" ]; then
    warn "$VAULT_PATH is already a Memoria vault."
    confirm "Refresh it from the repo (author files overwritten; your notes & .env kept)?" \
      || { ok "Keeping the existing vault as-is."; return; }
  fi

  run mkdir -p "$VAULT_PATH"
  # rsync preserves user notes/.env on refresh; fall back to cp on a clean target.
  if have rsync; then
    run rsync -a --exclude '.git' "$src"/ "$VAULT_PATH"/
  else
    run_sh "cp -R \"$src\"/. \"$VAULT_PATH\"/"
  fi
  ok "Vault deployed to $VAULT_PATH"

  # The runtime vault is the user's own repo — they set up git themselves, with
  # their own identity and remote. We don't `git init`/commit under a synthetic
  # author. obsidian-git needs a repo to commit into, so point the way:
  if [ ! -d "$VAULT_PATH/.git" ]; then
    say "  This folder is your vault — set up your own git here (obsidian-git needs a repo):"
    say "      cd \"$VAULT_PATH\""
    say "      git init && git add -A && git commit -m \"Initial Memoria vault\""
    say "      git remote add origin <your-repo-url>   # optional — backup / multi-machine sync"
  fi
}

# =============================================================================
# Step 5 — MCP server dependencies
# =============================================================================
install_mcp_deps() {
  hdr "MCP server dependencies"
  detect_python
  local reqs="$VAULT_PATH/.memoria/mcp/requirements.txt"
  if [ ! -f "$reqs" ]; then warn "No $reqs — skipping."; return; fi
  if [ -z "$PYTHON" ]; then warn "No Python found — skipping MCP deps (install later: pip install -r $reqs)."; return; fi
  run "$PYTHON" -m pip install --quiet -r "$reqs" || die "pip install of MCP deps failed."
  ok "MCP dependencies installed"
}

# =============================================================================
# Step 6 — deploy the seven profiles  (the original profile-installer logic)
# =============================================================================
install_profiles() {
  hdr "Hermes profiles"
  local profiles_src="$VAULT_PATH/.memoria/profiles"
  if [ ! -d "$profiles_src" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then warn "(dry-run) vault not copied yet; would deploy from $profiles_src"; return; fi
    die "No profiles at $profiles_src."
  fi
  if ! have hermes; then
    warn "Hermes not on PATH — cannot deploy profiles. Install Hermes, then: bash install.sh --profiles-only --vault \"$VAULT_PATH\""
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

  local p src missing f dst fname env_example env_file
  for p in $targets; do
    src="$profiles_src/$p"
    if [ ! -d "$src" ]; then skipped="$skipped\n    [-] $p: source missing"; continue; fi

    missing=""
    for f in $REQUIRED_FILES; do [ -f "$src/$f" ] || missing="$missing $f"; done
    if [ -n "$missing" ]; then skipped="$skipped\n    [-] $p: missing$missing"; continue; fi

    say "  staging $p"
    dst="$staging/$p"
    run cp -R "$src" "$dst"
    # Substitute {{VAULT_PATH}} in the files that reference the vault by absolute
    # path: mcp.json (server commands) + config.yaml (policy-gate hook). POSIX
    # paths are already forward-slash, so no conversion is needed.
    for fname in mcp.json config.yaml; do
      [ -f "$dst/$fname" ] || continue
      run_sh "sed 's|{{VAULT_PATH}}|$VAULT_PATH|g' \"$dst/$fname\" > \"$dst/$fname.tmp\" && mv \"$dst/$fname.tmp\" \"$dst/$fname\""
    done

    say "  installing $p"
    if run hermes profile install "$dst" --alias "$p" --force --yes; then
      installed="$installed $p"
      # Bootstrap .env from .env.EXAMPLE on FIRST install only (never clobber creds).
      env_example="$HERMES_PROFILES_DIR/$p/.env.EXAMPLE"
      env_file="$HERMES_PROFILES_DIR/$p/.env"
      if [ "$DRY_RUN" -eq 0 ] && [ -f "$env_example" ] && [ ! -f "$env_file" ]; then
        cp "$env_example" "$env_file"
        say "    created .env from .env.EXAMPLE (fill in real values)"
      fi
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
# Step 7 — skills  (see project-files/proposals/bootstrap-installer.md, "Pinned skill install IDs")
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

  # B. Official Hermes skills. TODO(confirm-at-build): bundled vs install — warn-not-fail.
  if have hermes; then
    local s
    for s in $OFFICIAL_SKILLS; do
      run hermes skills install "$s" || warn "skill '$s' not installed (may already be bundled with Hermes)"
    done
    # kepano obsidian-markdown
    run hermes skills install kepano/obsidian-skills/skills/obsidian-markdown \
      || warn "kepano obsidian-markdown not installed — see the design doc for the clone fallback"
    # qmd — TODO(confirm-at-build): packaging is fragmented (skills.sh vs tobi/qmd CLI).
    run hermes skills install skills-sh/moltbot/skills/qmd \
      || warn "qmd skill not installed — confirm packaging (skills.sh 'skills-sh/moltbot/skills/qmd'; CLI: github.com/tobi/qmd)"
  else
    warn "Hermes not on PATH — skipped official/kepano/qmd skill installs."
  fi

  say "  (obsidian-paper-note + retraction-check ship inside the vault profiles — nothing to fetch.)"
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
  say "  On first launch: turn off Restricted mode so the eight bundled plugins load."
}

ensure_zotero() {
  hdr "Zotero"
  if have zotero || (have flatpak && flatpak info org.zotero.Zotero >/dev/null 2>&1); then
    ok "Zotero present"
  else
    say "Zotero is a GUI app — install it yourself:"
    if have flatpak; then
      say "  Flatpak:  flatpak install -y flathub org.zotero.Zotero"
      confirm "Install via Flatpak now?" && run flatpak install -y flathub org.zotero.Zotero
    else
      say "  Download: https://www.zotero.org/download/"
      say "  Or the apt repo (zotero-deb):  https://github.com/retorquere/zotero-deb"
    fi
  fi
}

zotero_plugins() {
  hdr "Zotero add-ons (manual — Zotero installs .xpi from the GUI)"
  say "Install these in Zotero -> Tools -> Add-ons -> gear -> Install Add-on From File:"
  say "  - Better BibTeX (REQUIRED): https://github.com/retorquere/zotero-better-bibtex/releases/latest"
  say "  - MarkDB-Connect (recommended): https://github.com/daeh/zotero-markdb-connect/releases/latest"
  say ""
  say "Then configure Better BibTeX:"
  say "  - Citation key formula: stable author+year (see set-up-zotero.md)"
  say "  - Auto-export your library as BibLaTeX to:  $VAULT_PATH/.memoria/library.bib"
  say "    (this overwrites the empty stub the vault ships with)"
}

# =============================================================================
# Step 9 — secrets + next steps
# =============================================================================
print_secrets_guidance() {
  hdr "API keys (you add these — never commit them)"
  say "Each profile has a .env at  $HERMES_PROFILES_DIR/<profile>/.env"
  say "The Librarian needs the most; the rest share a minimum set. Set at least:"
  say "    KILOCODE_API_KEY=...        # model access (shipped provider: kilocode / kilo.ai)"
  say "    OBSIDIAN_API_KEY=...        # 64-char hex from the Obsidian REST API plugin"
  say "    OPENALEX_EMAIL=you@x.com    # Librarian only — polite-pool header"
  say "Full guide: docs/how-to-guides/setup/set-up-hermes.md"
}

print_next_steps() {
  hdr "Next steps"
  local first; first="$(printf '%s' "$ALL_PROFILES" | awk '{print $1}')"
  say "  1. Fill in the .env secrets (above)."
  [ -n "$VAULT_PATH" ] && say "  2. Open this folder in Obsidian as your vault:  $VAULT_PATH"
  say "  3. Verify the profiles:        hermes profile list"
  say "  4. Smoke-test the ACP pane:    hermes -p memoria-socratic acp"
  say "  5. Try a session:              hermes -p $first chat"
  say ""
  say "Re-deploy after editing the vault source:  bash install.sh --profiles-only --vault \"${VAULT_PATH:-<vault>}\""
  [ "$DRY_RUN" -eq 1 ] && warn "This was a DRY RUN — nothing above was actually changed."
}

# =============================================================================
# --profiles-only: resolve which vault to deploy from, then deploy.
# =============================================================================
resolve_vault_for_profiles() {
  if [ -n "$VAULT_OVERRIDE" ]; then VAULT_PATH="$VAULT_OVERRIDE"
  elif [ -d "./vault/.memoria" ]; then VAULT_PATH="$(cd ./vault && pwd)"
  elif [ -d "$DEFAULT_TARGET/.memoria" ]; then VAULT_PATH="$DEFAULT_TARGET"
  else die "Cannot find a vault. Pass --vault DIR (the folder containing .memoria/)."; fi
  case "$VAULT_PATH" in "~"/*) VAULT_PATH="$HOME/${VAULT_PATH#~/}" ;; esac
  ok "Deploying profiles from $VAULT_PATH"
}

# =============================================================================
# main  (wrapped so a truncated `curl | bash` download can't execute a partial run)
# =============================================================================
main() {
  parse_args "$@"

  if [ "$PROFILES_ONLY" -eq 1 ]; then
    resolve_vault_for_profiles
    install_mcp_deps
    install_profiles
    print_next_steps
    return
  fi

  print_plan
  confirm "Proceed with the full Memoria install?" || die "Aborted — nothing changed."
  ensure_prereqs
  resolve_repo
  ensure_hermes
  copy_vault
  install_mcp_deps
  install_profiles
  install_skills
  if [ "$NO_APPS" -eq 0 ]; then
    ensure_obsidian
    ensure_zotero
    zotero_plugins
  fi
  print_secrets_guidance
  print_next_steps
  hdr "Done"
}

main "$@"
