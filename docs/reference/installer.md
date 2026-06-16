---
title: Installer (bootstrap)
parent: Reference
---

# Installer (bootstrap)

The bootstrap installers (`scripts/install.ps1` for native Windows production; `scripts/install.sh` for Linux/WSL testing): what each step does, the flags, and the crons they wire. The install model is **scaffold → populate → golden copy** ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the repo ships the vault under `src/`, the installer creates the schema-checked folder skeleton in your runtime vault, fills it from `src/`, and stages a restorable golden copy of every system file.

Safety posture: no silent privilege escalation (every `sudo` is printed and confirmed), `--dry-run` echoes everything and touches nothing, and the recommended invocation is inspect-first (`curl -o install.sh`, read it, then run it).

---

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` | Install the runtime vault here (default `~/Memoria`; prompted otherwise). Pick a folder outside any cloud-synced tree. |
| `--profiles-only` | Skip the bootstrap; just (re)deploy MCP deps, profiles, and crons from an existing vault — **the maintenance path** after editing the vault source or adding keys to `~/.hermes/.env`. |
| `--only NAMES` | Restrict the profile step to a comma-separated subset (e.g. `--only memoria-librarian`); pairs with `--profiles-only`. |
| `--no-apps` / `-NoApps` | Skip the Obsidian guidance (headless / server installs). |
| `--dry-run` | Print every command that would run; change nothing. |
| `--yes` / `-y` | Non-interactive: accept all defaults, no prompts (CI). |

---

## The install flow

| Step | What happens |
| --- | --- |
| 1. Prerequisites | Ensures `git` and `pandoc` (Hermes provisions uv-Python, Node, ripgrep, ffmpeg itself). |
| 2. Fetch the repo | Clones `memoria-vault` to a temp staging dir (or uses a local checkout). |
| 3. Hermes | Runs the official Hermes installer for the host OS. On Windows this is Hermes's native PowerShell installer; on Linux/WSL this is the shell installer. |
| 4. Scaffold + populate | Copies `src/` to the vault (rsync — a refresh overwrites author files, keeps your notes and `.env`), then recreates the empty-folder **skeleton** (the `SKELETON_DIRS` list mirrors `folders.yaml`'s `skeleton:` block). |
| 4a. Golden copy | Reconciles shipped system files against the previous golden baseline and stages the new SHA-256 manifest at `.memoria/golden/` — the Linter's restore source (`golden_restore.py upgrade --source SRC --apply`). |
| 4b. Git hooks | If the vault is a git repo, wires `.memoria/operations/integrity/linter/pre-commit` into `.git/hooks/pre-commit` so staged notes pass schema validation, and `.githooks/post-commit` into `.git/hooks/post-commit` so committed project drafts enqueue Peer-reviewer verification. (The vault is _your_ repo; the installer never `git init`s for you.) |
| 5. MCP dependencies | Creates the vault-local venv at `.memoria/.venv` and pip-installs `mcp/requirements.txt`. The **clustering stack is opt-in**: a confirm prompt offers `requirements-cluster.txt` (bertopic → torch, ~2 GB); skipping it leaves graph tools working and `cluster_model_topics` erroring cleanly. |
| 5b. qmd search engine | Installs `@tobilu/qmd` (npm, Node ≥22) if missing, registers the vault as a qmd collection (BM25 works immediately), and offers the ~2GB vector-model embed as an opt-in. Resolves the absolute binary path into each profile's `{{QMD}}` slot — a conda package also ships a `qmd`, so PATH lookup is unsafe. |
| 6. Profiles | Deploys the **five** profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`): substitutes `{{PYTHON}}` (the venv interpreter) and `{{VAULT_PATH}}` into each `config.yaml`, runs `hermes profile install`, bootstraps `.env` from `.env.EXAMPLE`, propagates shared secrets from `~/.hermes/.env` (profile runs read only their own `.env`), and deploys the `memoria-policy-gate` write-gate plugin per lane. Then **prunes stale profiles** from previous installs (`mapper` / `socratic` / `verifier` / `coder` / `linter`). |
| 7. Skills | Clones the K-Dense bundle, verifies the bundled official Hermes skills, and installs the hub skills (`obsidian-markdown`, `qmd`). |
| 8. Obsidian | Guided, not silent: Windows offers `winget`; Linux offers the Flatpak/AppImage path. **Zotero is no longer provisioned by the Linux test installer** — Windows production still offers winget guidance because Zotero is the expected production bibliography surface. |
| 9. Secrets + next steps | Prints where keys go (`~/.hermes/.env` → re-run `--profiles-only` to propagate) and the first-session checklist (open the Co-PI pane, switch to the Library workspace). |

---

## The crons it wires

All five are deterministic, no-LLM `hermes cron … --no-agent` jobs; the wrappers are substituted into `~/.hermes/scripts/` and the job creation is idempotent.

| Cron | Schedule | Runs | Effect |
| --- | --- | --- | --- |
| `memoria-board-export` | `* * * * *` | `board_export.py` | Projects the live kanban board into `system/board/` and appends its telemetry logs (metrics aggregation is the separate weekly `memoria-metrics` job). |
| `memoria-sweeps` | `*/15 * * * *` | `operations/cleanup/reconcile.py` | Recovers stalled captures: enqueues idempotent re-ingest cards (see [Ingest routing](ingest.md)). |
| `memoria-lint` | `0 6 * * *` | `operations/integrity/linter/detectors.py` + `golden_restore.py check` | The daily monitor: structural detectors + golden-copy drift (see [Linter: detectors and auto-fix](linter.md)). |
| `memoria-metrics` | `30 6 * * 1` | `mcp/metrics_aggregate.py` | Weekly fleet health: rolls the audit log, the Hermes board, and lint findings into per-lane trust-score notes under `system/metrics/` (read by the fleet-health dashboard). |
| `memoria-eval` | `0 7 1 */3 *` | `operations/telemetry/eval/eval_score.py` + `eval_dispatch.py` | Quarterly vault-eval: scores the previous quarter's run into `system/metrics/eval/runs.jsonl`, then fans the `system/eval/` gold set out as one idempotent eval card per task — diagnostic, never gating (see [Vault eval](vault-eval.md)). |

A further wrapper ships for the monthly Retraction Watch refresh (`src/.memoria/scripts/retraction-refresh-cron.sh` — `retraction.py --refresh` + `--sweep`).

---

## What the user still supplies

| Item | Where |
| --- | --- |
| `KILOCODE_API_KEY` (model access), `OBSIDIAN_API_KEY` + `OBSIDIAN_MCP_SSL_VERIFY` (Local REST API HTTPS), `OPENALEX_API_KEY` (required since 2026-02) | `$env:LOCALAPPDATA\hermes\.env` on Windows or `~/.hermes/.env` on Linux/WSL, then rerun the matching installer with `-ProfilesOnly` / `--profiles-only` to propagate |
| Obsidian first launch | Open the vault folder; disable Restricted mode so the bundled plugins load |
| git in the vault | `git init && git add -A && git commit` — obsidian-git, the pre-commit gate, and verify-on-commit need a repo |
| Zotero (optional) | The bring-in-a-paper tutorial on the docs site |

---

## Related

- What the populated tree looks like: [On-disk layout](on-disk-layout.md)
- The five profiles the install deploys: [Profile capabilities](profiles.md)
- The gate and plugin the installer wires per lane: [Policy MCP](policy-mcp.md)
