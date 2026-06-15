#!/usr/bin/env bash
# Local runtime-tool phases sourced by install.sh after the repository is resolved.
# shellcheck disable=SC2034  # QMD_BIN is consumed by install_profiles in install.sh

# Prefer the npm-global qmd binary: an unrelated conda package also installs qmd.
resolve_qmd() {
  local npm_qmd=""
  if have npm; then npm_qmd="$(npm prefix -g 2>/dev/null)/bin/qmd"; fi
  if [ -n "$npm_qmd" ] && [ -x "$npm_qmd" ]; then printf '%s' "$npm_qmd"; return; fi
  command -v qmd 2>/dev/null || printf 'qmd'
}

ensure_qmd() {
  hdr "qmd search engine"
  local q; q="$(resolve_qmd)"
  if [ -x "$q" ] && "$q" --help 2>/dev/null | grep -q "mcp"; then
    ok "qmd present: $q"
  elif have npm && node --version 2>/dev/null | grep -qE 'v(2[2-9]|[3-9][0-9])'; then
    run npm install -g @tobilu/qmd \
      || warn "qmd install failed — search MCP will not serve (npm install -g @tobilu/qmd)"
    q="$(resolve_qmd)"
  else
    warn "qmd not installed and Node >=22 unavailable — search MCP will not serve until you: npm install -g @tobilu/qmd"
  fi
  QMD_BIN="$q"
  if [ -x "$q" ] && "$q" --help 2>/dev/null | grep -q "mcp"; then
    run "$q" collection add "$VAULT_PATH" --name vault \
      || warn "qmd collection add failed — register manually: qmd collection add \"$VAULT_PATH\" --name vault"
    if confirm "Build the qmd vector index now (first run downloads ~2GB of local models)?"; then
      run "$q" embed || warn "qmd embed failed — re-run later: qmd embed"
    else
      say "  (skipped — BM25 search works now; run 'qmd embed' later for semantic search)"
    fi
  fi
}

wire_commit_gate() {
  if [ -d "$VAULT_PATH/.git" ]; then
    run mkdir -p "$VAULT_PATH/.git/hooks"
    run cp "$VAULT_PATH/.memoria/operations/integrity/linter/pre-commit" "$VAULT_PATH/.git/hooks/pre-commit"
    run chmod +x "$VAULT_PATH/.git/hooks/pre-commit"
    ok "pre-commit schema gate wired (.git/hooks/pre-commit)"
  else
    say "  (vault is not a git repo yet — re-run with --profiles-only after git init to wire the pre-commit gate)"
  fi
}
