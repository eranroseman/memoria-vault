#!/usr/bin/env bash
# Retraction Watch dataset refresh cron. Downloads the Crossref-owned Retraction
# Watch CSV (gitlab.com/crossref/retraction-watch-data, CC) to
# .memoria/data/retraction_watch.csv — the authoritative source the verify MCP's
# retraction_check(doi) indexes by OriginalPaperDOI.
#
# Deterministic, read-only fetch — no LLM, no vault writes. Monthly is plenty (the
# dataset changes slowly; CrossRef update-to covers the real-time delta between
# refreshes). Wired by the installer, e.g.:
#   hermes cron create '0 3 1 * *' --script memoria-refresh-rw.sh --no-agent \
#     --name memoria-refresh-rw --deliver local
# stdout is discarded; its effect is the refreshed CSV. A failed fetch is non-fatal
# (the MCP degrades to the live CrossRef + Open Retractions sources).
#
# The installer substitutes {{PYTHON}} (the vault venv interpreter) and {{VAULT_PATH}}
# when it copies this to ~/.hermes/scripts/memoria-refresh-rw.sh.
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/engines/sweeps/retraction.py" --refresh >/dev/null || true
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/engines/sweeps/retraction.py" --sweep --vault "{{VAULT_PATH}}" >/dev/null || true
