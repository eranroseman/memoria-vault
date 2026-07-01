#!/usr/bin/env bash
# Local runtime-tool phases sourced by install.sh after the repository is resolved.
# shellcheck disable=SC2034  # QMD_BIN is consumed by install_profiles in install.sh

# Prefer the npm-global qmd binary: an unrelated conda package also installs qmd.
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
  elif have npm && node --version 2>/dev/null | grep -qE 'v(2[2-9]|[3-9][0-9])'; then
    run npm install -g @tobilu/qmd \
      || warn "qmd install failed — search will not be ready (npm install -g @tobilu/qmd)"
    q="$(resolve_qmd)"
  else
    warn "qmd not installed and Node >=22 unavailable — search will not be ready until you: npm install -g @tobilu/qmd"
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
    run cp "$VAULT_PATH/.memoria/operations/integrity/linter/pre-commit" "$VAULT_PATH/.git/hooks/pre-commit"
    run chmod +x "$VAULT_PATH/.git/hooks/pre-commit"
    ok "pre-commit schema gate wired (.git/hooks/pre-commit)"
  else
    say "  (vault is not a git repo yet — initialize git, then copy .memoria/operations/integrity/linter/pre-commit into .git/hooks/pre-commit)"
  fi
}

wire_verify_on_commit_hook() {
  if [ -d "$VAULT_PATH/.git" ] || [ "$DRY_RUN" -eq 1 ]; then
    run mkdir -p "$VAULT_PATH/.git/hooks"
    run cp "$VAULT_PATH/.githooks/post-commit" "$VAULT_PATH/.git/hooks/post-commit"
    run chmod +x "$VAULT_PATH/.git/hooks/post-commit"
    ok "post-commit verify trigger wired (.git/hooks/post-commit)"
  else
    say "  (vault is not a git repo yet — initialize git, then copy .githooks/post-commit into .git/hooks/post-commit)"
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
  if [ "$DRY_RUN" -eq 0 ] && hermes cron list --all 2>/dev/null | grep -q "$job_name"; then
    say "  $present_label cron already present — wrapper refreshed, job left as-is"
  else
    run hermes cron create "$schedule" --script "$dest_name" --no-agent \
      --name "$job_name" --deliver local \
      || warn "could not create the $present_label cron — create it manually$manual_hint"
  fi
  say "  ($note)"
  ok "$ok_label cron wired"
}
