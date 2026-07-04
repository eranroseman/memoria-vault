#!/usr/bin/env bash
# Local runtime-tool phases sourced by install.sh after the repository is resolved.
# shellcheck disable=SC2034  # QMD_BIN is consumed by the qmd install phase in install.sh

# Prefer the npm-global qmd binary: an unrelated conda package also installs qmd.
allow_global_tool_install() {
  [ "${MEMORIA_INSTALL_GLOBAL_TOOLS:-0}" = "1" ]
}

resolve_qmd() {
  local npm_qmd=""
  if [ -n "${MEMORIA_QMD_BIN:-}" ]; then
    if [ -x "$MEMORIA_QMD_BIN" ]; then printf '%s' "$MEMORIA_QMD_BIN"; fi
    return
  fi
  if have npm; then npm_qmd="$(npm prefix -g 2>/dev/null)/bin/qmd"; fi
  if [ -n "$npm_qmd" ] && [ -x "$npm_qmd" ]; then printf '%s' "$npm_qmd"; return; fi
}

ensure_qmd() {
  hdr "qmd search engine"
  local q; q="$(resolve_qmd)"
  if [ -x "$q" ] && "$q" --help 2>/dev/null | grep -q "mcp"; then
    ok "qmd present: $q"
  elif allow_global_tool_install && have npm && node --version 2>/dev/null | grep -qE 'v(2[2-9]|[3-9][0-9])'; then
    run npm install -g @tobilu/qmd \
      || warn "qmd install failed — search will not be ready (npm install -g @tobilu/qmd)"
    q="$(resolve_qmd)"
  else
    warn "qmd not installed — search will not be ready until you install qmd or rerun with MEMORIA_INSTALL_GLOBAL_TOOLS=1"
  fi
  QMD_BIN="$q"
  if [ -x "$q" ] && "$q" --help 2>/dev/null | grep -q "mcp"; then
    run mkdir -p "$VAULT_PATH/.memoria/index/qmd/checked"
    run mkdir -p "$VAULT_PATH/.memoria/index/qmd/config"
    run env QMD_CONFIG_DIR="$VAULT_PATH/.memoria/index/qmd/config" \
      INDEX_PATH="$VAULT_PATH/.memoria/index/qmd/index.sqlite" \
      "$q" collection add "$VAULT_PATH/.memoria/index/qmd/checked" \
      --name memoria-checked --mask "**/*.md" \
      || warn "qmd collection add failed — run: memoria workspace rebuild --workspace \"$VAULT_PATH\" --search"
    say "  (registered checked-only qmd input; the worker rebuilds it from checked Concepts)"
  fi
}

wire_commit_gate() {
  if [ -d "$VAULT_PATH/.git" ] || [ "$DRY_RUN" -eq 1 ]; then
    run mkdir -p "$VAULT_PATH/.git/hooks"
    run cp "$VAULT_PATH/.githooks/pre-commit" "$VAULT_PATH/.git/hooks/pre-commit"
    run chmod +x "$VAULT_PATH/.git/hooks/pre-commit"
    ok "pre-commit schema gate wired (.git/hooks/pre-commit)"
  else
    say "  (vault is not a git repo yet — initialize git, then copy .githooks/pre-commit into .git/hooks/pre-commit)"
  fi
}
