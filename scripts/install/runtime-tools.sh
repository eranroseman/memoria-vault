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
    say "  (vault is not a git repo yet — re-run with --profiles-only after git init to wire the pre-commit hook)"
  fi
}

wire_verify_on_commit_hook() {
  if [ -d "$VAULT_PATH/.git" ]; then
    run mkdir -p "$VAULT_PATH/.git/hooks"
    run cp "$VAULT_PATH/.githooks/post-commit" "$VAULT_PATH/.git/hooks/post-commit"
    run chmod +x "$VAULT_PATH/.git/hooks/post-commit"
    ok "post-commit verify trigger wired (.git/hooks/post-commit)"
  else
    say "  (vault is not a git repo yet — re-run with --profiles-only after git init to wire the post-commit verify trigger)"
  fi
}

install_hermes_cron() {
  local header="$1" skip_label="$2" source_name="$3" dest_name="$4" schedule="$5" job_name="$6"
  local present_label="$7" missing_label="$8" missing_job_label="$9" manual_hint="${10}"
  local note="${11}" ok_label="${12}"

  hdr "$header"
  if ! have hermes; then warn "Hermes not on PATH — skipping the $skip_label cron."; return 0; fi
  local src="$VAULT_PATH/.memoria/scripts/$source_name"
  local scripts_dir="$HERMES_HOME/scripts"
  local dst="$scripts_dir/$dest_name"
  if [ ! -f "$src" ]; then
    warn "$missing_label cron wrapper missing at $src — $missing_job_label cron NOT wired."
    return 0
  fi
  run mkdir -p "$scripts_dir"
  local pybin="${VENV_PYTHON:-python}"
  local pybin_esc vault_esc
  pybin_esc="$(sed_repl "$pybin")"
  vault_esc="$(sed_repl "$VAULT_PATH")"
  run_sh "sed -e 's|{{PYTHON}}|$pybin_esc|g' -e 's|{{VAULT_PATH}}|$vault_esc|g' \"$src\" > \"$dst\""
  run chmod +x "$dst"
  if [ "$DRY_RUN" -eq 0 ] && hermes cron list 2>/dev/null | grep -q "$job_name"; then
    say "  $present_label cron already present — wrapper refreshed, job left as-is"
  else
    run hermes cron create "$schedule" --script "$dest_name" --no-agent \
      --name "$job_name" --deliver local \
      || warn "could not create the $present_label cron — create it manually$manual_hint"
  fi
  say "  ($note)"
  ok "$ok_label cron wired"
}
