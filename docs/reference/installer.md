---
title: Installer (bootstrap)
parent: Reference
---

# Installer (bootstrap)

The bootstrap installer ([scripts/install.sh](../../scripts/install.sh); Windows runs it under WSL2 via `install.ps1`): what each step does, the flags, and the crons it wires. The install model is **scaffold → populate → golden copy** ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the repo ships the vault under `src/`, the installer creates the schema-checked folder skeleton in your runtime vault, fills it from `src/`, and stages a restorable golden copy of every system file.

Safety posture: no silent privilege escalation (every `sudo` is printed and confirmed), `--dry-run` echoes everything and touches nothing, and the recommended invocation is inspect-first (`curl -o install.sh`, read it, then run it).

---

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` | Install the runtime vault here (default `~/Memoria`; prompted otherwise). Pick a folder outside any cloud-synced tree. |
| `--profiles-only` | Skip the bootstrap; just (re)deploy MCP deps, profiles, and crons from an existing vault — **the maintenance path** after editing the vault source or adding keys to `~/.hermes/.env`. |
| `--only NAMES` | Restrict the profile step to a comma-separated subset (e.g. `--only memoria-librarian`); pairs with `--profiles-only`. |
| `--no-apps` | Skip the Obsidian guidance (headless / server installs). |
| `--dry-run` | Print every command that would run; change nothing. |
| `--yes` / `-y` | Non-interactive: accept all defaults, no prompts (CI). |

---

## The install flow

| Step | What happens |
| --- | --- |
| 1. Prerequisites | Ensures `git` and `pandoc` (Hermes provisions uv-Python, Node, ripgrep, ffmpeg itself). |
| 2. Fetch the repo | Clones `memoria-vault` to a temp staging dir (or uses a local checkout). |
| 3. Hermes | Runs the official Hermes installer; verifies the ACP extra. |
| 4. Scaffold + populate | Copies `src/` to the vault (rsync — a refresh overwrites author files, keeps your notes and `.env`), then recreates the empty-folder **skeleton** (the `SKELETON_DIRS` list mirrors `folders.yaml`'s `skeleton:` block). |
| 4a. Golden copy | Stages a canonical copy of every system file with a SHA-256 manifest at `.memoria/golden/` — the Linter's restore source (`golden.py stage`). |
| 4b. Pre-commit gate | If the vault is a git repo, wires `.memoria/engines/linter/pre-commit` into `.git/hooks/` — every staged note must pass its schema. (The vault is _your_ repo; the installer never `git init`s for you.) |
| 5. MCP dependencies | Creates the vault-local venv at `.memoria/.venv` and pip-installs `mcp/requirements.txt`. The **clustering stack is opt-in**: a confirm prompt offers `requirements-cluster.txt` (bertopic → torch, ~2 GB); skipping it leaves graph tools working and `cluster_model_topics` erroring cleanly. |
| 6. Profiles | Deploys the **five** profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`): substitutes `{{PYTHON}}` (the venv interpreter) and `{{VAULT_PATH}}` into each `config.yaml`, runs `hermes profile install`, bootstraps `.env` from `.env.EXAMPLE`, propagates shared secrets from `~/.hermes/.env` (profile runs read only their own `.env`), and deploys the `memoria-policy-gate` write-gate plugin per lane. Then **prunes stale profiles** from previous installs (`mapper` / `socratic` / `verifier` / `coder` / `linter`). |
| 7. Skills | Clones the K-Dense bundle, verifies the bundled official Hermes skills, and installs the hub skills (`obsidian-markdown`, `qmd`). |
| 8. Obsidian | Guided, not silent: detects Obsidian or offers the Flatpak; reminds you to turn off Restricted mode. **Zotero is no longer provisioned** — it moved to the bring-in-a-paper tutorial (it's the PI's bibliographic-backbone choice, not core provisioning). |
| 9. Secrets + next steps | Prints where keys go (`~/.hermes/.env` → re-run `--profiles-only` to propagate) and the first-session checklist (open the co-PI pane, switch to the Library workspace). |

---

## The crons it wires

All four are deterministic, no-LLM `hermes cron … --no-agent` jobs; the wrappers are substituted into `~/.hermes/scripts/` and the job creation is idempotent.

| Cron | Schedule | Runs | Effect |
| --- | --- | --- | --- |
| `memoria-board-export` | `* * * * *` | `board_export.py` (+ metrics) | Projects the live kanban board into `system/board/` and appends the six-signal telemetry. |
| `memoria-sweeps` | `*/15 * * * *` | `engines/sweeps/reconcile.py` | Recovers stalled captures: enqueues idempotent re-ingest cards (see [Ingest routing](ingest.md)). |
| `memoria-lint` | `0 6 * * *` | `engines/linter/detectors.py` + `golden.py check` | The daily monitor: structural detectors + golden-copy drift (see [Linter: detectors and auto-fix](linter.md)). |
| `memoria-metrics` | `30 6 * * 1` | `mcp/metrics_aggregate.py` | Weekly fleet health: rolls the audit log, the Hermes board, and lint findings into per-lane trust-score notes under `system/metrics/` (read by the fleet-health dashboard). |

A fourth wrapper ships for the monthly Retraction Watch refresh ([src/.memoria/scripts/refresh-retraction-watch.sh](../../src/.memoria/scripts/refresh-retraction-watch.sh) — `retraction.py --refresh` + `--sweep`).

---

## What the user still supplies

| Item | Where |
| --- | --- |
| `KILOCODE_API_KEY` (model access), `OBSIDIAN_API_KEY` (Local REST API), `OPENALEX_API_KEY` (required since 2026-02) | `~/.hermes/.env`, then `bash scripts/install.sh --profiles-only --vault <vault>` to propagate |
| Obsidian first launch | Open the vault folder; disable Restricted mode so the bundled plugins load |
| git in the vault | `git init && git add -A && git commit` — obsidian-git and the pre-commit gate need a repo |
| Zotero (optional) | The bring-in-a-paper tutorial on the docs site |

---

## Related

- What the populated tree looks like: [On-disk layout](on-disk-layout.md)
- The five profiles the install deploys: [Profile capabilities](profiles.md)
- The gate and plugin the installer wires per lane: [Policy MCP](policy-mcp.md)
