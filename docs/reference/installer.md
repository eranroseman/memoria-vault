---
title: Installer (bootstrap)
parent: System and infrastructure
grand_parent: Reference
---

# Installer (bootstrap)

The bootstrap installers (`scripts/install.sh` for Linux/WSL and `scripts/install.ps1` for Windows): what each step does, the flags, and the optional crons they wire. The default path is a standalone CLI/runtime workspace. The install model is **scaffold → populate → golden copy** ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the repo ships the vault under `vault-template/`, the installer creates the schema-checked folder skeleton in your runtime vault, fills it from `vault-template/`, and stages a restorable golden copy of every system file.

Safety features: no silent privilege escalation, `--dry-run` echoes commands and touches nothing, and `--yes` is the only non-interactive path.

---

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` / `-Vault DIR` | Install the runtime vault here (default `~/Memoria` on Linux/WSL, `%USERPROFILE%\Memoria` on Windows). Pick a folder outside any cloud-synced tree. |
| `--with-hermes` / `-WithHermes` | Adapter path: also install Hermes, deploy the five profiles, wire Hermes crons, install or refresh profile skills, and guide Obsidian setup. |
| `--with-cluster` / `-WithCluster` | Install the optional clustering stack (`bertopic` → `torch`, about 2 GB). Without this flag, graph tools still work and topic modeling errors cleanly. |
| `--profiles-only` / `-ProfilesOnly` | Skip fresh vault creation; just deploy runtime deps, the five profiles, and crons from an existing vault after editing profile source or adding keys to the Hermes `.env`. |
| `--only NAMES` / `-Only NAMES` | Restrict the profile step to a comma-separated subset (e.g. `--only memoria-librarian`); pairs with `--profiles-only`. |
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
installer so commit hooks are wired, runs `scripts/install.sh --with-hermes --vault ... --no-apps --yes` with `MEMORIA_ENV=test` and the custom model overlay, creates the baseline
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
| `MEMORIA_ENV=test` | Test overlay for the Hermes adapter. Renders every profile to `kilocode` + `https://api.kilo.ai/api/gateway` + `meta-llama/llama-4-scout`. |
| `MEMORIA_MODEL_PROVIDER` | Overrides the test overlay provider. Use `custom` for a local OpenAI-compatible endpoint. |
| `MEMORIA_MODEL_BASE_URL` | Overrides the test overlay endpoint. |
| `MEMORIA_MODEL_NAME` | Overrides the test overlay model name. |
| `MEMORIA_MODEL_CONTEXT_LENGTH` | Adds rendered `context_length` and `ollama_num_ctx` when `MEMORIA_ENV=test` and `MEMORIA_MODEL_PROVIDER=custom`. |

The model overlay changes only the Hermes model block in the `--with-hermes` adapter path. The standalone runtime reads provider configuration from the workspace/runtime configuration instead of Hermes profile `.env` files. When the Hermes adapter is used, the Obsidian MCP remains verified loopback HTTPS and still requires `OBSIDIAN_MCP_PORT`, `OBSIDIAN_MCP_SSL_VERIFY`, and `OBSIDIAN_API_KEY` in each profile's `.env`.

---

## The install flow

| Step | What happens |
| --- | --- |
| 1. Prerequisites | Ensures `git` and Python 3 with venv support. `pandoc` is optional and only needed for DOCX/PDF exports. |
| 2. Fetch the repo | Clones `memoria-vault` to a temp staging dir (or uses a local checkout). |
| 3. Scaffold + populate | Copies `vault-template/` into a new vault, then recreates the empty-folder **skeleton** (the `SKELETON_DIRS` list mirrors `folders.yaml`'s `skeleton:` block). A full install refuses an existing Memoria vault; use a fresh target for a new release. |
| 3a. Golden copy | Stages the shipped system files and SHA-256 manifest at `.memoria/golden/` — the Linter's restore source (`golden_restore.py stage`). |
| 3b. Git repo + hooks | Initializes Git when needed, wires `.githooks/pre-commit` into `.git/hooks/pre-commit` so staged notes pass schema validation, and `.githooks/post-commit` into `.git/hooks/post-commit` so committed project drafts enqueue verification. The vault is _your_ repo: the installer never commits, sets identity, or adds a remote. |
| 4. Runtime dependencies + package | Creates the vault-local venv at `.memoria/.venv`, pip-installs `mcp/requirements.txt`, and installs the Memoria package from the release root (`pip install <release_root>`). The **clustering stack is opt-in**: add `--with-cluster` to install `requirements-cluster.txt` (bertopic → torch, ~2 GB); skipping it leaves graph tools working and `cluster_model_topics` erroring cleanly. |
| 5. qmd search engine | Installs `@tobilu/qmd` (npm, Node ≥22) if missing and registers `.memoria/index/qmd/checked` as the checked-only qmd collection using workspace-local qmd config/index paths. |
| 6. CLI next steps | Prints the exact vault-local Python commands for `memoria doctor bundle --workspace ...`, `memoria workspace rebuild --search`, and `memoria ask`. |

With `--with-hermes` / `-WithHermes`, the installers add the adapter steps after the standalone runtime is installed:

| Adapter step | What happens |
| --- | --- |
| Hermes | Runs the official Hermes installer and verifies ACP. |
| Obsidian CSS and agent-client seed | Reconciles the Memoria CSS snippets and seeds `agent-client/data.json` for the WSL test path. |
| Profiles | Deploys the **five** profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`): substitutes `{{PYTHON}}` (the venv interpreter), `{{VAULT_PATH}}`, `{{QMD}}`, and the `{{MODEL_*}}` slots into each `config.yaml`, verifies the generated Obsidian MCP config still uses `https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` with `ssl_verify: ${OBSIDIAN_MCP_SSL_VERIFY}`, runs `hermes profile install`, refreshes the rendered deployed `config.yaml`, reconciles profile-owned skills, bootstraps `.env`, propagates shared secrets from `~/.hermes/.env`, and deploys the `memoria-policy-gate` write-gate plugin per lane. |
| Skills | Linux/WSL clones the K-Dense bundle, verifies bundled official Hermes skills, installs the official optional `research/qmd` skill, and installs the `obsidian-markdown` hub skill. Windows refreshes the bundled profile skills from the vault source. |
| Obsidian | Guided, not silent: Linux offers the Flatpak/AppImage path; Windows offers winget guidance. Zotero is not provisioned. |
| Secrets + next steps | Prints where Hermes profile keys go (`~/.hermes/.env` -> re-run `--profiles-only` to propagate) and the first-session checklist. |

---

## The crons it wires

With `--with-hermes` / `-WithHermes`, all six are deterministic, no-LLM `hermes cron … --no-agent` jobs; the wrappers are substituted into the Hermes scripts directory and the job creation is idempotent. The standalone CLI/runtime path does not wire Hermes crons.

| Cron | Schedule | Runs | Effect |
| --- | --- | --- | --- |
| `memoria-board-export` | `* * * * *` | `board_export.py` | Projects the live kanban board into `system/board/` and appends its telemetry logs (metrics aggregation is the separate weekly `memoria-metrics` job). |
| `memoria-sweeps` | `*/15 * * * *` | `memoria_vault.runtime.subsystems.cleanup.reconcile` | Recovers stalled captures: enqueues idempotent re-ingest requests (see [Ingest routing](ingest.md)). |
| `memoria-worker` | `* * * * *` | `memoria_vault.runtime.worker` | Observes direct PI edits and drains up to 10 pending SQLite request jobs through the worker/trusted-writer boundary. |
| `memoria-lint` | `0 6 * * *` | `memoria_vault.runtime.subsystems.integrity.linter.detectors` + `golden_restore check` | The daily monitor: structural detectors + golden-copy drift (see [Linter: detectors and auto-fix](linter.md)). |
| `memoria-metrics` | `30 6 * * 1` | `mcp/metrics_aggregate.py` | Weekly fleet health: rolls the audit log, the Hermes board, and lint findings into per-lane trust-score notes under `system/metrics/` (read by the fleet-health dashboard). |
| `memoria-eval` | `0 7 1 */3 *` | `memoria eval run` | Quarterly vault-eval dispatch: fans the `system/eval/` gold set out as one idempotent eval task per current task — diagnostic, never gating (see [Vault eval](vault-eval.md)). |

A further wrapper ships for the monthly Retraction Watch refresh (`vault-template/.memoria/scripts/retraction-refresh-cron.sh` — runtime retraction `--refresh` + `--sweep`).

---

## What the user still supplies

| Item | Where |
| --- | --- |
| Runtime provider keys | Shell environment or workspace runtime configuration consumed by the standalone CLI. |
| Hermes/Obsidian keys, only when using the adapter | `KILOCODE_API_KEY`, `OBSIDIAN_API_KEY`, `OBSIDIAN_MCP_PORT`, `OBSIDIAN_MCP_SSL_VERIFY`, and `OPENALEX_API_KEY` in `$env:LOCALAPPDATA\hermes\.env` on Windows or `~/.hermes/.env` on Linux/WSL, then rerun the matching installer with `-ProfilesOnly` / `--profiles-only` to propagate. |
| Obsidian first launch, only when using the UI adapter | Open the vault folder and allow the bundled community plugins to load. |
| git binary + git in the vault | The host or sandbox must have `git` on `PATH`; checkpoints, hooks, rollback, and history need the runtime vault to be a repo. |
| Zotero (optional) | The bring-in-a-paper tutorial on the docs site |

---

## Related

- What the populated tree looks like: [On-disk layout](on-disk-layout.md)
- The five profiles the install deploys: [Profile capabilities](profile-capabilities.md)
- The gate and plugin the installer wires per lane: [Policy MCP](policy-mcp.md)
