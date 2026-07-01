---
title: Installer (bootstrap)
parent: System and infrastructure
grand_parent: Reference
---

# Installer (bootstrap)

The bootstrap installers (`scripts/install.ps1` for native Windows production; `scripts/install.sh` for Linux/WSL testing): what each step does, the flags, and the crons they wire. The install model is **scaffold → populate → golden copy** ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the repo ships the vault under `vault-template/`, the installer creates the schema-checked folder skeleton in your runtime vault, fills it from `vault-template/`, and stages a restorable golden copy of every system file.

Safety features: no silent privilege escalation, `--dry-run` echoes commands and touches nothing, and `--yes` is the only non-interactive path.

---

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` | Install the runtime vault here (default `~/Memoria`; prompted otherwise). Pick a folder outside any cloud-synced tree. |
| `--profiles-only` | Skip fresh vault creation; just deploy MCP deps, the five profiles, and crons from an existing vault after editing profile source or adding keys to `~/.hermes/.env`. |
| `--only NAMES` | Restrict the profile step to a comma-separated subset (e.g. `--only memoria-librarian`); pairs with `--profiles-only`. |
| `--no-apps` / `-NoApps` | Skip the Obsidian guidance (headless / server installs). |
| `--dry-run` | Print every command that would run; change nothing. |
| `--yes` / `-y` | Non-interactive: accept all defaults, no prompts (CI). |

## Disposable local-LLM install smoke

For a release-candidate proof on Linux/WSL, use:

```bash
bash scripts/install-test-vault-local-llm.sh
```

The harness treats `~/Memoria-test` as disposable and installs the real vault at
`~/Memoria-test/vault` so tool-managed files at the root do not collide with the
vault's own `.git`. Every run wipes that child vault, initializes Git before the
installer so commit hooks are wired, runs `scripts/install.sh --vault ... --no-apps
--yes` with `MEMORIA_ENV=test` and the custom model overlay, creates the baseline
commit, then checks package import, golden-copy drift, detectors, Hermes profile
and cron registration, and the real-model L2 smoke.

Defaults target an Ollama/OpenAI-compatible endpoint:

| Setting | Default |
| --- | --- |
| Test root | `~/Memoria-test` |
| Vault path | `~/Memoria-test/vault` |
| Base URL | `http://127.0.0.1:11434/v1` |
| Model | `memoria-qwen2.5:7b-64k` |
| Context length | `65536` |

Override them with `--root`, `--vault`, `--base-url`, `--model`, and `--context`,
or the matching `MEMORIA_TEST_*` environment variables. Use `--skip-live-llm` only
when validating installer mechanics without a running local model.

## Environment overlays

| Variable | Effect |
| --- | --- |
| `MEMORIA_ENV=prod` | Default. Renders the shipped Kilo Code gateway model tiers: Co-PI and Peer-reviewer on Opus, Writer on Sonnet, Librarian and Engineer on Haiku. |
| `MEMORIA_ENV=test` | Linux/WSL test overlay. Renders every profile to `kilocode` + `https://api.kilo.ai/api/gateway` + `meta-llama/llama-4-scout`. |
| `MEMORIA_MODEL_PROVIDER` | Overrides the test overlay provider. Use `custom` for a local OpenAI-compatible endpoint. |
| `MEMORIA_MODEL_BASE_URL` | Overrides the test overlay endpoint. |
| `MEMORIA_MODEL_NAME` | Overrides the test overlay model name. |
| `MEMORIA_MODEL_CONTEXT_LENGTH` | Adds rendered `context_length` and `ollama_num_ctx` when `MEMORIA_ENV=test` and `MEMORIA_MODEL_PROVIDER=custom`. |

The model overlay changes only the Hermes model block. The Obsidian MCP remains verified loopback HTTPS and still requires `OBSIDIAN_MCP_PORT`, `OBSIDIAN_MCP_SSL_VERIFY`, and `OBSIDIAN_API_KEY` in each profile's `.env`.

---

## The install flow

| Step | What happens |
| --- | --- |
| 1. Prerequisites | Ensures `git` and `pandoc` (Hermes provisions uv-Python, Node, ripgrep, ffmpeg itself). |
| 2. Fetch the repo | Clones `memoria-vault` to a temp staging dir (or uses a local checkout). |
| 3. Hermes | Runs the official Hermes installer for the host OS. On Windows this is Hermes's native PowerShell installer; on Linux/WSL this is the shell installer. |
| 4. Scaffold + populate | Copies `vault-template/` into a new vault, then recreates the empty-folder **skeleton** (the `SKELETON_DIRS` list mirrors `folders.yaml`'s `skeleton:` block). A full install refuses an existing Memoria vault; use a fresh target for a new release. |
| 4a. Golden copy | Stages the shipped system files and SHA-256 manifest at `.memoria/golden/` — the Linter's restore source (`golden_restore.py stage`). |
| 4b. Git hooks | If the vault is a git repo, wires `.memoria/operations/integrity/linter/pre-commit` into `.git/hooks/pre-commit` so staged notes pass schema validation, and `.githooks/post-commit` into `.git/hooks/post-commit` so committed project drafts enqueue Peer-reviewer verification. (The vault is _your_ repo; the installer never `git init`s for you.) |
| 4c. Obsidian CSS snippets | Preserves `.obsidian/appearance.json` but reconciles `enabledCssSnippets` so the Memoria link-color and property-badge snippets are on by default. Missing shipped snippet files are copied back; other appearance settings are left alone. |
| 5. MCP dependencies + package | Creates the vault-local venv at `.memoria/.venv`, pip-installs `mcp/requirements.txt`, and installs the Memoria package from the release root (`pip install <release_root>`). The **clustering stack is opt-in**: a confirm prompt offers `requirements-cluster.txt` (bertopic → torch, ~2 GB); skipping it leaves graph tools working and `cluster_model_topics` erroring cleanly. |
| 5b. qmd search engine | Installs `@tobilu/qmd` (npm, Node ≥22) if missing, registers `.memoria/index/qmd/checked` as the checked-only qmd collection, and leaves vector embedding unbuilt. Resolves the absolute binary path into each profile's `{{QMD}}` slot — a conda package also ships a `qmd`, so PATH lookup is unsafe. |
| 6. Profiles | Deploys the **five** profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`): substitutes `{{PYTHON}}` (the venv interpreter), `{{VAULT_PATH}}`, `{{QMD}}`, and the `{{MODEL_*}}` slots into each `config.yaml`, verifies the generated Obsidian MCP config still uses `https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` with `ssl_verify: ${OBSIDIAN_MCP_SSL_VERIFY}`, runs `hermes profile install`, refreshes the rendered deployed `config.yaml`, reconciles the source-owned `skills/` directory (including clearing stale bundled skills from profiles that opt out), bootstraps `.env` from `.env.EXAMPLE`, propagates shared secrets from `~/.hermes/.env` (profile runs read only their own `.env`), and deploys the `memoria-policy-gate` write-gate plugin per lane. |
| 7. Skills | Clones the K-Dense bundle, verifies bundled official Hermes skills, installs the official optional `research/qmd` skill, and installs the `obsidian-markdown` hub skill. |
| 8. Obsidian | Guided, not silent: Windows offers `winget`; Linux offers the Flatpak/AppImage path. **Zotero is no longer provisioned by the Linux test installer** — Windows production still offers winget guidance because Zotero is the expected production bibliography surface. |
| 9. Secrets + next steps | Prints where keys go (`~/.hermes/.env` -> re-run `--profiles-only` to propagate) and the first-session checklist (use the left-pane rail to open Library, then open the Agent Client pane when you want conversational help). |

---

## The crons it wires

All six are deterministic, no-LLM `hermes cron … --no-agent` jobs; the wrappers are substituted into `~/.hermes/scripts/` and the job creation is idempotent.

| Cron | Schedule | Runs | Effect |
| --- | --- | --- | --- |
| `memoria-board-export` | `* * * * *` | `board_export.py` | Projects the live kanban board into `system/board/` and appends its telemetry logs (metrics aggregation is the separate weekly `memoria-metrics` job). |
| `memoria-sweeps` | `*/15 * * * *` | `operations/cleanup/reconcile.py` | Recovers stalled captures: enqueues idempotent re-ingest cards (see [Ingest routing](ingest.md)). |
| `memoria-worker` | `* * * * *` | `memoria_vault.runtime.worker` | Observes direct PI edits and drains up to 10 pending SQLite request jobs through the worker/trusted-writer boundary. |
| `memoria-lint` | `0 6 * * *` | `operations/integrity/linter/detectors.py` + `golden_restore.py check` | The daily monitor: structural detectors + golden-copy drift (see [Linter: detectors and auto-fix](linter.md)). |
| `memoria-metrics` | `30 6 * * 1` | `mcp/metrics_aggregate.py` | Weekly fleet health: rolls the audit log, the Hermes board, and lint findings into per-lane trust-score notes under `system/metrics/` (read by the fleet-health dashboard). |
| `memoria-eval` | `0 7 1 */3 *` | `operations/telemetry/eval/eval_score.py` + `eval_dispatch.py` | Quarterly vault-eval: scores the previous quarter's run into `system/metrics/eval/runs.jsonl`, then fans the `system/eval/` gold set out as one idempotent eval card per task — diagnostic, never gating (see [Vault eval](vault-eval.md)). |

A further wrapper ships for the monthly Retraction Watch refresh (`vault-template/.memoria/scripts/retraction-refresh-cron.sh` — `retraction.py --refresh` + `--sweep`).

---

## What the user still supplies

| Item | Where |
| --- | --- |
| `KILOCODE_API_KEY` (production model access; not used by the `MEMORIA_ENV=test` local model block), `OBSIDIAN_API_KEY` + `OBSIDIAN_MCP_PORT` + `OBSIDIAN_MCP_SSL_VERIFY` (Local REST API HTTPS/native MCP), `OPENALEX_API_KEY` (required since 2026-02) | `$env:LOCALAPPDATA\hermes\.env` on Windows or `~/.hermes/.env` on Linux/WSL, then rerun the matching installer with `-ProfilesOnly` / `--profiles-only` to propagate |
| Obsidian first launch | Open the vault folder and allow the bundled community plugins to load |
| git binary + git in the vault | The host or sandbox must have `git` on `PATH`; manual Obsidian Git checkpoints, hooks, rollback, and history need the runtime vault to be a repo. |
| Zotero (optional) | The bring-in-a-paper tutorial on the docs site |

---

## Related

- What the populated tree looks like: [On-disk layout](on-disk-layout.md)
- The five profiles the install deploys: [Profile capabilities](profile-capabilities.md)
- The gate and plugin the installer wires per lane: [Policy MCP](policy-mcp.md)
