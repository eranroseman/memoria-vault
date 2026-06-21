---
topic: tests
title: Release-candidate run runbook
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 19
---

# Release-candidate run runbook

The reusable, version-agnostic run sheet that takes a **fresh clone on a clean
Ubuntu/WSL2 box** through stages **S0–S5** and the operability gates **G9–G11**,
recording each [gate](../../adr/29-testing-framework.md) green. Work top
to bottom; if a step fails, stop and file it — a candidate is green only when
every row is.

**Per release:** record each result in the relevant gate/stage sub-issue under the
release parent issue. Copy the [sign-off template](#sign-off-template) into that
release's `validation-log.md` only when the issue/Actions trail needs a curated
long-lived summary. Gate/stage **state** never lives in this file (the procedure)
or the release plan (the prose/definitions).

The per-area detail lives in the linked plan docs; this sheet sequences them and
adds the exact commands plus the ingest/runtime setup.

This runbook is the `release-acceptance` layer. It consumes green PR-required
`static-contract`, `component`, `vault-assembly`, and `workflow-replay` evidence,
then adds the non-PR `runtime-integration` checks: live Hermes, the Obsidian bridge,
local services, GUI/Bases/dashboards, and model connectivity.

## 0. Preconditions

- [ ] Clean **native Windows production** box for the attended production install, plus a clean **Ubuntu / WSL2** box for the Linux test installer.
- [ ] Local REST API HTTPS configured with `OBSIDIAN_MCP_PORT` and `OBSIDIAN_MCP_SSL_VERIFY`. On the WSL test box only, mirrored networking must be on if Obsidian runs on Windows.
- [ ] Hermes installed and on `PATH` (`hermes version`).
- [ ] A **throwaway vault** dir for the install, e.g. `export RV=$HOME/Memoria-candidate`.
- [ ] Fresh clone: `git clone https://github.com/eranroseman/memoria-vault.git && cd memoria-vault` — record the commit (`git rev-parse --short HEAD`).
- [ ] The Hermes global `.env` has the scholarly-API keys (`S2_API_KEY`, `OPENALEX_API_KEY`, `NCBI_EMAIL`), `OBSIDIAN_API_KEY`, `OBSIDIAN_MCP_PORT`, and `OBSIDIAN_MCP_SSL_VERIFY`; the installer propagates them per profile. **Never print key values.**

## S0–S1 — static-contract + component  → records G6 (partial), S0, S1

```bash
bash scripts/test.sh all          # l1 (component tests, pytest) + l0 (static)
```

- [ ] **S0 / static-contract** static (parse, LF endings, profile files present) — PASS.
- [ ] **S1 / component** the component test suite green (`scripts/test.sh l1` → `pytest tests/`): `policy_mcp`, `policy_hook`, `board_export`, `metrics_aggregate`, `retraction`, `detectors`, **and the ingest spine** (`ingest_paper`, `resolve_merge`, `link`, `extract`, `pipeline`, `sweeps`, `ingest_mcp`).
- [ ] Confirm CI is green on the same commit (the required checks gate — G6): `gh pr checks` / the Actions tab.

## PR-safe smoke — vault-assembly + workflow-replay  → records G6 (partial)

```bash
bash scripts/e2e-smoke.sh
python3 scripts/test_env_harness.py replay --json
```

- [ ] **vault-assembly** builds a disposable vault, initializes git, wires executable hooks, verifies default CSS snippets and bundled plugins, and finishes fresh-vault integrity cleanly.
- [ ] **workflow-replay** reaches the ADR-80 Phase 1 model-free path, writes the expected artifacts, denies the known forbidden write with an audit row, and leaves no forbidden file.

## S2 — installer dry-run  → records S2

```bash
bash scripts/install.sh --dry-run --vault "$RV"
```

- [ ] Prints `DRY RUN — nothing will be changed`; `{{VAULT_PATH}}` / `{{PYTHON}}` substitutions resolve; no errors.

## S3 — real install into the throwaway vault  → records S3, G1

```bash
bash scripts/install.sh --vault "$RV"      # full install
hermes profile list                         # expect all 5
bash scripts/install.sh --vault "$RV"      # re-run: must be idempotent (no errors, no dupes)
```

- [ ] **G1 / S3** — installer completes; **all 5 profiles register** (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`); the vault venv exists (`$RV/.memoria/.venv`); idempotent re-run is clean.
- [ ] `memoria-policy-gate` plugin deployed + enabled for all 5 (substituted `{{PROFILE}}`/`{{VAULT_PATH}}` per lane).
- [ ] Bundled official skills verified present (no hub-install 404s).
- [ ] Telemetry + sweeps crons wired: `hermes cron list` shows `memoria-board-export` and `memoria-sweeps`.
- [ ] **Ingest runtime deps:** `"$RV/.memoria/.venv/bin/python" -c "import pymupdf4llm"` succeeds (local-PDF extraction; from `requirements.txt`).

Detail: [Installer test plan](installer-test-plan.md).

## S4 — runtime-integration: model, bridge, gate enforcement  → records G2, G3, S4

- [ ] **Model connectivity** — a trivial `hermes` chat/zero-shot returns (provider reachable).
- [ ] **REST bridge (G3)** — the obsidian MCP reads **and** writes the vault via the Local REST API plugin's **native MCP over verified HTTPS** ([ADR-31](../../adr/31-native-obsidian-mcp.md)): set `OBSIDIAN_MCP_PORT` and `OBSIDIAN_MCP_SSL_VERIFY` in `~/.hermes/.env`, enable the plugin's HTTPS server on that port, reload the Obsidian window to bind it. The port lives in the URL, so the candidate and any other vault coexist on different ports — no need to close another vault.
- [ ] **Gate enforcement (G2)** in **all three run modes** — `hermes -z`, gateway (api_server), and cron — on installer-deployed lanes: an allowed write logs `allow` + `write_complete`; a denied/`dry_run` write is blocked with **no file**; a reached-but-erroring gate decision **fails closed**. A missing/unregistered plugin is a deploy failure, not a runtime policy outage.
- [ ] **Gate contract — Hermes drift:** `python src/.memoria/mcp/hermes_contract_doctor.py --vault ~/Memoria-test` exits 0 — every direct-capability and egress/side-effect tool the *installed* Hermes ships (file/terminal/code_execution/web/browser/messaging/computer_use/delegation/media/Home Assistant/spotify/cronjob toolsets) is hard-denied, and the deployed `policy_hook.py` matches `src/`. **Re-run after every Hermes upgrade**; this is what catches a new tool like `process` the denylist doesn't yet know. WARN lines for dead names are informational.
- [ ] **Local services** — local LLM endpoint, MCP servers, and Obsidian bridge checks are recorded as manual/nightly evidence, not as PR-required CI, until a stable self-hosted runner exists.

Detail: [Hermes CLI test plan](hermes-cli-test-plan.md), [Headless test plan](headless-test-plan.md).

## G9 — deterministic spine (zero-LLM card)  → records G9

- [ ] A *dispatched, zero-LLM* card (Linter operation `health-report` or Peer-reviewer `similarity-check`) completes live: dispatch → claim → run → **gated write** → audit → `done`.

Detail: [Deterministic-spine test plan (G9)](g9-spine-plan.md).

## G10 — ingest value loop (the product)  → records G10

**Ingest setup (once):**

- [ ] Better BibTeX **postscript** applied so the export carries `zoteroselect` (gives `zotero_uri` with no Zotero API) — snippet in [Ingest routing](../../reference/ingest.md#frontmatter-written-at-ingest). Re-export the `.bib`.
- [ ] A seeded `system/vocabulary.md` is present (ships with the vault).

**Run a real paper end-to-end** (Zotero capture → card, or a manual ingest card):

- [ ] Dispatch ingests through the `ingest_pipeline` MCP tool → the Librarian fills the two holes (vocabulary-constrained `_proposed_classification`; comparative `[!brief]`) → gated write → `lifecycle: proposed`, `ingest_status: complete`.
- [ ] Note is complete: identity + merged metadata (S2/OpenAlex/Crossref), stable IDs (`openalex_id`/`semantic_scholar_id`/`pmid`/`pmcid`), `zotero_uri` + `pdf_uri`, full-text extract under `.memoria/data/extracts/`, ID-keyed entity notes under `catalog/`, `[!brief]` leads the body.

Detail: [Ingest-value-loop test plan (G10)](g10-ingest-plan.md).

## G11 — review loop closes  → records G11

- [ ] Card reaches `done` with the review requested; a **human review** promotes `_proposed_classification` into the main `research_area`/`methodology` fields, removes the proposal block, and flips `lifecycle: proposed → current`. Observed end-to-end.

## S5 — Obsidian + Zotero GUI  → records S5, G4

Run the [GUI test plan](gui-test-plan.md) on the Windows side and **fully complete its Results table**:

- [ ] **Part A** — all bundled plugins load/enable; REST round-trip; settings verified (no "didn't verify" caveat).
- [ ] **Part B** — Zotero + Better BibTeX export works; the capture macro fires.
- [ ] **Part C (G4)** — **all thirteen support dashboards render** on real data (Dataview queries resolve), including the ingested note + entities from G10.
- [ ] **Part D — Bases render check.** Open every shipped `.base` in Obsidian and confirm each view renders without a YAML/format error: `catalog/catalog.base` (entity views), `inbox/inbox.base` ("Needs me" + "All cards" — also embedded by the Inbox space), `notes/hubs/hubs.base`, `projects/projects.base`, `system/board/board.base`, `system/dashboards/claims.base` / `sources.base` / `fleeting.base` / `project-gate.base`, `system/patterns/patterns.base`, `system/worklists/worklists.base`. The format is young and our CI only schema-syncs properties — rendering is verifiable only in the app.

## G5 — telemetry signals  → records G5

```bash
hermes cron run memoria-board-export        # or: hermes cron tick
python src/.memoria/mcp/board_export.py --cost-doctor
ls -l "$RV/system/logs/"{board-state,board-transitions,audit,lint-findings,cost}.jsonl
```

- [ ] `board-state`, `board-transitions`, `audit`, and `lint-findings` all gain rows from the live activity above.
- [ ] The cost doctor passes before live export trusts the Hermes session-store join; any missing cost rows are counted in `cost-misses.jsonl`, not treated as zero.
- [ ] Resolve at least one `work-prompt` through `Memoria: resolve inbox card` and confirm `disposition.jsonl` gains an `accepted`, `edited`, or `rejected` row from the human action surface.

## G7 — no High-priority blockers

- [ ] Memoria Issue Tracker has no open issue with Priority `High` that blocks the release.

## G8 + cut mechanics  → records G8, then ships

Only after every row above is green:

- [ ] Confirm `version: vX.Y.0` across the five `src/.memoria/profiles/*/distribution.yaml`.
- [ ] **Version + CHANGELOG + tag + GitHub Release** are owned by **release-please** — merge its open release PR; that cuts the tag, finalizes `CHANGELOG [vX.Y.0]`, and publishes the Release. Don't hand-tag or hand-edit the CHANGELOG. (See [Releases](../../releasing/README.md).)
- [ ] Flip `released: false → true` / `status: draft → released` in that release's `release-plan-<v>.md` frontmatter.
- [ ] Close the release's **"Release vX.Y" parent issue** + the milestone, rolling any unfinished issues to the next milestone.

## Sign-off template

Record these results in the relevant release gate/stage sub-issues. Copy this table
into the release's `validation-log.md` only when a curated summary is worth keeping.
Record commit `__________` and date `__________`.

| Gate / stage | Records | Result | Notes |
| --- | --- | --- | --- |
| S0 | static-contract | ☐ | |
| S1 | component | ☐ | |
| G6 | required CI green, including vault-assembly + workflow-replay | ☐ | |
| S2 | dry-run install | ☐ | |
| S3 / G1 | real install, 5 profiles, idempotent | ☐ | |
| S4 / G3 | runtime-integration: model + REST bridge live | ☐ | |
| G2 | gate enforced (`-z` / gateway / cron) | ☐ | |
| G9 | deterministic spine card | ☐ | |
| G10 | ingest value loop end-to-end | ☐ | |
| G11 | review loop closes | ☐ | |
| S5 / G4 | GUI + 13 support dashboards render | ☐ | |
| G5 | four telemetry signals emit | ☐ | disposition/cost = known limitation |
| G7 | no High-priority blockers | ☐ | |
| G8 | version + CHANGELOG cut | ☐ | at cut |

When every row is checked, proceed to the cut mechanics above.
