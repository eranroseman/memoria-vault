---
title: v0.1.0 release-candidate run checklist
status: draft
---

# v0.1.0 release-candidate run checklist

A mechanical, ordered run sheet to take a **fresh clone on a clean Ubuntu/WSL2 box**
through tiers **T0–T5** and the operability gates **G9–G11**, recording each
[release gate](release-plan-v0.1.md#2-definition-of-done--gates) green. Work top to
bottom; record outcomes in the [sign-off table](#sign-off) at the end. If a step
fails, stop and file it — a candidate is green only when every row is.

The per-area detail lives in the linked protocol docs; this sheet sequences them
and adds the exact commands plus the ingest/runtime setup the older protocols
predate.

## 0. Preconditions

- [ ] Clean **Ubuntu / WSL2** box (Hermes runs in WSL2; Obsidian/Zotero on the Windows side).
- [ ] WSL2 **mirrored networking** on (`networkingMode=mirrored` in `.wslconfig`) — required for the agent to reach the Obsidian Local REST API on `127.0.0.1` (the native-MCP HTTP port `OBSIDIAN_MCP_PORT`, and the REST bridge on 27124).
- [ ] Hermes installed and on `PATH` (`hermes version`).
- [ ] A **throwaway vault** dir for the install, e.g. `export RV=$HOME/Memoria-candidate`.
- [ ] Fresh clone: `git clone https://github.com/eranroseman/memoria-vault.git && cd memoria-vault` — record the commit (`git rev-parse --short HEAD`).
- [ ] `~/.hermes/.env` has the scholarly-API keys (`S2_API_KEY`, `OPENALEX_API_KEY`, `NCBI_EMAIL`) and `OBSIDIAN_API_KEY`; the installer sets `OBSIDIAN_VAULT_PATH`. **Never print key values.**

## T0–T1 — static + self-tests  → records G6 (partial), T0, T1

```bash
bash scripts/test.sh all          # l1 (all --self-test suites) + l0 (static)
```

- [ ] **T0** static (parse, LF endings, profile files present) — PASS.
- [ ] **T1** every Python `--self-test` green: `policy_mcp`, `policy_hook`, `board_export`, `metrics_aggregate`, `detectors`, **and the ingest spine** (`ingest_paper`, `resolve_merge`, `link`, `extract`, `pipeline`, `sweeps`, `ingest_mcp`).
- [ ] Confirm CI is green on the same commit (the required checks gate — G6): `gh pr checks` / the Actions tab.

## T2 — installer dry-run  → records T2

```bash
bash scripts/install.sh --dry-run --vault "$RV"
```

- [ ] Prints `DRY RUN — nothing will be changed`; `{{VAULT_PATH}}` / `{{PYTHON}}` substitutions resolve; no errors.

## T3 — real install into the throwaway vault  → records T3, G1

```bash
bash scripts/install.sh --vault "$RV"      # full install
hermes profile list                         # expect all 7
bash scripts/install.sh --vault "$RV"      # re-run: must be idempotent (no errors, no dupes)
```

- [ ] **G1 / T3** — installer completes; **all 7 profiles register** (`librarian`, `mapper`, `socratic`, `writer`, `verifier`, `coder`, `linter`); the vault venv exists (`$RV/.memoria/.venv`); idempotent re-run is clean.
- [ ] `memoria-policy-gate` plugin deployed + enabled for all 7 (substituted `{{PROFILE}}`/`{{VAULT_PATH}}` per lane).
- [ ] Bundled official skills verified present (no hub-install 404s) — [#59](https://github.com/eranroseman/memoria-vault/issues/59).
- [ ] Telemetry + sweeps crons wired: `hermes cron list` shows `memoria-board-export` and `memoria-sweeps`.
- [ ] **Ingest runtime deps:** `"$RV/.memoria/.venv/bin/python" -c "import pymupdf4llm"` succeeds (local-PDF extraction; from `requirements.txt`).

Detail: [installer-test-protocol.md](../../tests/installer-test-protocol.md).

## T4 — live: model, bridge, gate enforcement  → records G2, G3, T4

- [ ] **Model connectivity** — a trivial `hermes` chat/zero-shot returns (provider reachable).
- [ ] **REST bridge (G3)** — the obsidian MCP reads **and** writes the vault. The agent uses the Local REST API plugin's **native MCP over HTTP** ([ADR-31](../../decisions/31-native-obsidian-mcp.md)): set `OBSIDIAN_MCP_PORT` in `~/.hermes/.env`, enable the plugin's HTTP server on that port, and reload the Obsidian window to bind it. Because the port lives in the URL, the candidate and any other vault coexist on different ports — no need to close another vault.
- [ ] **Gate enforcement (G2)** in **all three run modes** — `hermes -z`, gateway (api_server), and cron — on installer-deployed lanes: an allowed write logs `allow` + `write_complete`; a denied/`dry_run` write is blocked with **no file**; a simulated policy outage **fails closed**.

Detail: [hermes-cli-test-protocol.md](../../tests/hermes-cli-test-protocol.md), [headless-test-protocol.md](../../tests/headless-test-protocol.md).

## G9 — deterministic spine (zero-LLM card)  → records G9

```bash
hermes kanban create "spine check" --assignee memoria-linter --skill <health-report> ...
```

- [ ] A *dispatched, zero-LLM* card (Linter `health-report` or Verifier `similarity-check`) completes live: dispatch → claim → run → **gated write** → audit → `done`.

Detail: [g9-spine-protocol.md](../../tests/g9-spine-protocol.md).

## G10 — ingest value loop (the product)  → records G10

**Ingest setup (once):**

- [ ] Better BibTeX **postscript** applied (Zotero → Better BibTeX → Preferences → Export → Postscript) so the export carries `zoteroselect` (gives `zotero_uri` with no Zotero API) — snippet in [ingest.md](../../../docs/reference/ingest.md#zotero-fields-without-the-zotero-api). Re-export the `.bib`.
- [ ] A seeded `00-meta/vocabulary.md` is present (ships with the vault).

**Run a real paper end-to-end** (Zotero capture → card, or a manual ingest card):

- [ ] Dispatch ingests through the `ingest_pipeline` MCP tool → the Librarian fills the two holes (vocabulary-constrained `_proposed_classification`; comparative `[!brief]`) → gated write → `lifecycle: proposed`, `ingest_status: complete`.
- [ ] Note is complete: identity + merged metadata (S2/OpenAlex/Crossref), stable IDs (`openalex_id`/`semantic_scholar_id`/`pmid`/`pmcid`), `zotero_uri` + `pdf_uri`, full-text extract saved under `90-assets/extracts/`, ID-keyed entity notes (`03-entities/<id>.md`), `[!brief]` leads the body.

Detail: [g10-ingest-protocol.md](../../tests/g10-ingest-protocol.md).

## G11 — review loop closes  → records G11

- [ ] Card reaches `done` with the review requested; a **human review** promotes `_proposed_classification` into the main `study_design`/`methods`/`topic` fields, removes the proposal block, and flips `lifecycle: proposed → current`. Observed end-to-end.

## T5 — Obsidian + Zotero GUI  → records T5, G4

Run [gui-test-protocol.md](../../tests/gui-test-protocol.md) on the Windows side and **fully complete its Results table**:

- [ ] **Part A** — all bundled plugins load/enable; REST round-trip; settings verified (no "didn't verify" caveat).
- [ ] **Part B** — Zotero + Better BibTeX export works; the capture macro fires.
- [ ] **Part C (G4)** — **all eleven dashboards render** on real data (Dataview queries resolve), including the ingested note + entities from G10.

## G5 — telemetry signals  → records G5 (four working signals)

```bash
hermes cron run memoria-board-export        # or: hermes cron tick
ls -l "$RV/99-system/logs/"{board-state,board-transitions,audit,lint-findings}.jsonl
```

- [ ] `board-state`, `board-transitions` (status), `audit` (deny-reasons / write-complete), and `lint-findings` (FAMA) all gain rows from the live activity above.
- [ ] **Known limitation (not a defect):** `disposition.jsonl` + `cost.jsonl` stay empty — they read the card `metadata` overlay the current Hermes doesn't surface; `board_export.py` is ready to emit them when it does. See [§6](release-plan-v0.1.md#6-known-limitations-state-in-the-release-notes).

## G7 — no open P0

- [ ] `gh issue list --label P0 --state open` is empty.

## G8 + cut mechanics  → records G8, then ships

Only after every row above is green:

- [ ] Confirm `version: 0.1.0` across the seven `vault/.memoria/profiles/*/distribution.yaml`.
- [ ] Cut `CHANGELOG.md`: move `[Unreleased]` items into a dated `[0.1.0]` section; re-point the links.
- [ ] Flip `released: false → true` in `release-plan-v0.1.md` frontmatter.
- [ ] Tag `v0.1.0`; create the GitHub release with the curated notes (§6 limitations included).
- [ ] Flip the relevant `shipped` rows to `approved` in [implementation-status.md](../../plans/implementation-status.md).

## Sign-off

Record commit `__________` and date `__________`.

| Gate / tier | Records | Result | Notes |
| --- | --- | --- | --- |
| T0 | static | ☐ | |
| T1 | self-tests | ☐ | |
| T2 | dry-run install | ☐ | |
| T3 / G1 | real install, 7 profiles, idempotent | ☐ | |
| T4 / G3 | model + REST bridge live | ☐ | |
| G2 | gate enforced (`-z` / gateway / cron) | ☐ | |
| G9 | deterministic spine card | ☐ | |
| G10 | ingest value loop end-to-end | ☐ | |
| G11 | review loop closes | ☐ | |
| T5 / G4 | GUI + 11 dashboards render | ☐ | |
| G5 | four telemetry signals emit | ☐ | disposition/cost = known limitation |
| G6 | CI green on the commit | ☐ | |
| G7 | no open P0 | ☐ | |
| G8 | version + CHANGELOG cut | ☐ | at cut |

When every row is checked, proceed to the [cut procedure (§7)](release-plan-v0.1.md#7-cut-procedure).
