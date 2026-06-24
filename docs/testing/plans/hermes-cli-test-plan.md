---
title: Hermes CLI test plan
status: draft
created: 2026-06-02
parent: Test plans
grand_parent: Testing
nav_order: 17
---

# Hermes CLI test plan

A procedure for exercising **every Hermes CLI command documented in
[Hermes CLI](../../reference/hermes-cli.md)** against a disposable
test vault, on a cheap model, and verifying each result deterministically (file
written, frontmatter correct, card transitioned, audit entry logged, or — for
read-only/dry-run commands — *nothing* written).

> **Scope.** This plan covers behaviour and wiring, not model quality. On the
> cheap test model the *prose* a command emits will be weaker than production; what
> we assert is that the command **runs, writes to the right place under the policy
> gate, and produces the right artifact shape** — never the eloquence of the output.

---

## 1. Test environment setup

### 1.1 Switch all agents to the test model

Run the suite against the Linux/WSL test overlay so the test run does not mutate
the production model tiers. The supported path is installer-owned: do not hand-edit
the five profile `config.yaml` files.

Render all profiles through the test overlay:

```bash
MEMORIA_ENV=test bash scripts/install.sh --profiles-only --vault ~/Memoria-test
hermes profile show memoria-librarian | grep -i model
```

Expected model block: `provider: kilocode`,
`base_url: https://api.kilo.ai/api/gateway`, and
`default: meta-llama/llama-4-scout`. Override with
`MEMORIA_MODEL_PROVIDER=custom`, `MEMORIA_MODEL_BASE_URL`, `MEMORIA_MODEL_NAME`,
or `MEMORIA_MODEL_CONTEXT_LENGTH` for an explicit local endpoint.

> Auxiliary slots (title/approval/mcp/skills-hub/compression) are already cheap and
> set in the **global** `~/.hermes/config.yaml`; leave them. See
> [configuration.md § Auxiliary models](../../how-to-guides/hermes-agent/configuration.md).

### 1.2 Runtime prerequisites

| Prereq | Check |
|---|---|
| Hermes ≥ 0.17 installed; 5 `memoria-*` profiles registered | `hermes profile list` shows all five |
| Obsidian open on the test vault with Local REST API HTTPS on `127.0.0.1:27124`, `OBSIDIAN_API_KEY` and `OBSIDIAN_MCP_SSL_VERIFY` set | For WSL2/ext4 test vaults, start Linux Obsidian on the native path (`obsidian ~/Memoria-test`), not Windows Obsidian over `\\wsl.localhost`. From a non-interactive WSLg shell, run it with `DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir PULSE_SERVER=/mnt/wslg/PulseServer`. Then `curl --cacert "$OBSIDIAN_MCP_SSL_VERIFY" -s https://127.0.0.1:27124/ -H "Authorization: Bearer $OBSIDIAN_API_KEY"` returns JSON. If Hermes gets TLS/401 errors, refresh the exported PEM/API key from Obsidian and re-run `--profiles-only`. |
| Hermes gateway on `:8642` (needed for `kanban dispatch`) | `hermes gateway status` |
| Zotero running with Better BibTeX; `.memoria/memoria.bib` present | file exists, contains the F1 citekeys |
| `OPENALEX_API_KEY` set per profile `.env`; `KILOCODE_API_KEY` only needed when testing production model wiring | `hermes profile show memoria-librarian` lists the keys (values redacted) |
| **Disposable test vault** (clone/fixture, never the real research vault) | `HERMES_HOME` / vault path points at the test copy |

### 1.3 Test fixtures (create once, referenced by ID below)

| ID | Fixture |
|---|---|
| **F1** | Two Zotero items with pinned BBT citekeys exported to `.memoria/memoria.bib` — one with an open-access PDF (call it `smithA`) and one without (`jonesB`). |
| **F2** | `research-focus.md` with ≥ 1 concrete priority topic. |
| **F3** | ≥ 5 claim notes (`type: claim`) in `notes/claims/` on a shared topic (for Librarian map lane/Writer/Peer-reviewer). |
| **F4** | A project at `projects/test-proj/` with a `README.md` (project note), a `map/` folder, and a `code/` folder. |
| **F5** | A draft `projects/test-proj/draft.md` citing both a **resolvable** citekey (`smithA`) and a **bogus** one (`@nope1999`). |
| **F6** | Two near-duplicate claim notes (`type: claim`, same idea, different wording) for `verify-propose-fix`. |
| **F7** | One paper entry (`type: paper`) whose `enriched_date` is > 180 days old (for `enrich`/staleness). |
| **F8** | One retracted-DOI paper entry (`type: paper`, or a known retracted DOI) for the retraction sweep. |

### 1.4 Verification toolbox (how every test is checked)

- **Vault write** → the file exists at the expected path with the expected frontmatter/body; e.g. `grep -l '^type: paper' catalog/papers/smithA.md`.
- **Policy gate** → `system/logs/audit.jsonl` gains a row: `decision: allow_with_log` (permitted) or `deny` (forbidden), each carrying `before_hash`/`after_hash`. `tail -1 system/logs/audit.jsonl | jq`.
- **Board state** → `hermes kanban show <id>` / `kanban list`; transitions also land in `system/logs/board-transitions.jsonl`.
- **Telemetry** → `disposition.jsonl`, `cost.jsonl`, `lint-findings.jsonl` per [Telemetry & logs](../../reference/telemetry.md).
- **Read-only / dry-run** → assert the **inverse**: no new file, and **no** `allow_with_log` write row for that lane in `audit.jsonl`.

### 1.5 Reset after testing

Discard the disposable test vault or redeploy production wiring with `MEMORIA_ENV=prod
bash scripts/install.sh --profiles-only --vault <vault>`.

---

## 2. Running and recording a case

Per-profile commands run as `hermes -p memoria-<name> chat -s <command> [args]` (an
interactive ACP session — you observe the turn, then check the vault/logs). Board and
admin commands are non-interactive. Record each row **PASS / FAIL / BLOCKED** with the
observed artifact, in the results log (§6).

Each case below gives: **Setup** (fixtures/preconditions) · **Run** (invocation) ·
**Pass criteria** (the deterministic check).

---

## 3. Smoke test (run first — ~5 min)

| # | Run | Pass criteria |
|---|---|---|
| S1 | `hermes profile list` | all 5 `memoria-*` profiles listed, status OK |
| S2 | `hermes profile show memoria-engineer \| grep -i model` | model = `meta-llama/llama-4-scout` (test config is live) |
| S3 | `hermes -p memoria-librarian chat -s catalog-find-source "<F2 topic>"` | returns ranked results; **no** write row in `audit.jsonl` |
| S4 | `hermes -p memoria-librarian chat -s catalog-enrich-record smithA` | `catalog/papers/smithA.md` created; `allow_with_log` row in `audit.jsonl` |
| S5 | `hermes -p memoria-copi chat -s ask-question-source catalog/papers/smithA.md` then ask it to "write a note" | questions only; **`deny`** (or no write) for `memoria-copi` in `audit.jsonl` — write-wall holds |

If S1–S5 pass, proceed to the full matrix.

---

## 4. Command test cases

### 4.1 Librarian — `hermes -p memoria-librarian chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| L1 | `catalog-find-source` | F2 | `catalog-find-source "<topic>"` | ≥1 candidate card in `inbox/` with `type: candidate`, `source: find`; `allow_with_log` write row |
| L2 | `catalog-enrich-record` | F1 (`smithA`) | `catalog-enrich-record smithA` | `catalog/papers/smithA.md` with `type: paper`, `citekey`, `_proposed_classification`, `_enrichment`, top-of-body `[!brief]` callout; Marker extract in `.memoria/data/extracts/smithA.md`; audit write row |
| L3 | `catalog-enrich-record` (no PDF) | F1 (`jonesB`) | `catalog-enrich-record jonesB` | note created; `extract_path` blank (not aborted); ingest still completes |
| L4 | `catalog-enrich-record` | F1 (`smithA`, delete the L2 note first) | `catalog-enrich-record smithA` | same as L2 — full pipeline incl. `[!brief]` (this is the skill `ingest` wraps) |
| L5 | `catalog-enrich-record` refresh | F7 | `catalog-enrich-record <citekey>` | `_enrichment` refreshed, top-level `enriched_date` = today; audit write row; main human fields untouched |
| L6 | `catalog-classify-source` | a paper entry (`type: paper`) with empty/low-confidence `_proposed_classification` | `catalog-classify-source <citekey>` | `_proposed_classification` re-proposed (values from the controlled vocabulary — [Frontmatter fields](../../reference/frontmatter.md)); human fields still empty |
| L7 | `link-suggest-claim` | F3 | `link-suggest-claim "<claim topic>"` | ranked matches returned; **read-only** — no write row in `audit.jsonl` |
| L8 | `catalog-rank-candidate` | F3 + candidate sources | `catalog-rank-candidate <candidate-ref>` | candidate ranking returned or staged according to the skill output contract; writes stay inside the Librarian lane scope |

### 4.2 Librarian (map lane) — `hermes -p memoria-librarian chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| M1 | `map-scope-project` | F3 + F4 | `map-scope-project --project test-proj --output projects/test-proj/map/corpus-map.md` | `corpus-map.md` written under `map/`; `sources:` frontmatter names what was scanned; audit write row scoped to `map/` |
| M2 | `map-report-coverage` | F3 + F4 | `map-report-coverage --project test-proj` | `gap-report.md` in `map/` listing thin-coverage topics |
| M3 | `map-cluster-corpus` | F3 | `map-cluster-corpus "<topic>"` | density/recency artifact in `map/cluster-maps/` (table/figure, not prose) |
| M4 | **map-lane write-wall** | — | (during M1) attempt/observe any write outside `map/` | none occurs; if forced, `deny` row for `memoria-librarian` (the map lane is read-only across `catalog/`, `notes/`, etc.) |

### 4.3 Co-PI — `hermes -p memoria-copi chat -s …` (read-only)

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| C1 | `ask-question-source` | F1 note | `ask-question-source catalog/papers/smithA.md` | questioning turns only; **zero** vault writes; any write attempt → `deny` for `memoria-copi` |
| C2 | `ask-read-lens` | a lens slug exists | `ask-read-lens <author>-<concept>` on a note | questions framed by the lens; still no writes |

### 4.4 Writer — `hermes -p memoria-writer chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| W1 | `draft-write-section` | F3 | `draft-write-section "<question over F3 claims>"` | an answer card in `inbox/`; card → `done`, queued for review (lifecycle stays `proposed`); audit write row |
| W2 | `draft-outline-argument` | F3 | `draft-outline-argument "<term>"` | outline artifact/card follows the Writer output contract; writes stay review-gated |
| W3 | `draft-score-outline` | a draft outline | `draft-score-outline <draft-or-outline>` | scoring output follows the Writer skill contract; any durable write is review-gated and scoped to the Writer lane |
| W4 | `draft-bind-citation` | a draft with citations | `draft-bind-citation <draft>` | citation binding output is staged for review; no ungated write to `notes/claims/` or canonical source records occurs |

### 4.5 Peer-reviewer — `hermes -p memoria-peer-reviewer chat -s …` (dry-run by default)

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| V1 | `verify-check-citation` | F5 | `verify-check-citation projects/test-proj/draft.md` | report/`[!verification]` flags `@nope1999` as unresolved, `smithA` as OK; **no edit to the draft** (dry-run) |
| V2 | `verify-trace-claim` | F5 + F3 | `verify-trace-claim projects/test-proj/draft.md` | per-claim trace; each unsupported claim spawns a gap card in `inbox/` (`type: gap`, `source: gap`); only the gap-card write appears in audit |
| V3 | `verify-card-gap` | F3 + a gap card | `verify-card-gap <gap-card>` | gap assessment is reported or staged as an Inbox card; existing notes are not merged |
| V4 | `verify-propose-fix` | F6 | `verify-propose-fix <target-card>` | fix proposal is staged for review; no auto-merge |
| V5 | Retraction operation | F8 | `python src/.memoria/operations/integrity/retraction/retraction.py --sweep --vault <vault>` | the retracted paper raises an Inbox alert; the source note lifecycle is unchanged |

### 4.6 Engineer profile invariants

`memoria-engineer` intentionally ships no chat skills. It is the MCP-only code lane for scoped handoff/provenance notes under `projects/*/code/`; substantive coding, git commits, and reverts happen in an external coding agent, not through Hermes chat skills.

| ID | Test | Setup | Run | Pass criteria |
|---|---|---|---|---|
| K1 | Skill absence | — | `hermes profile show memoria-engineer` | no bundled skills are listed for the Engineer profile |
| K2 | Direct-world ceiling | — | inspect rendered profile config or `hermes profile show memoria-engineer` | no `terminal`, `file`, `code_execution`, `browser`, `web`, or `computer_use` toolset is enabled |
| K3 | Write scope | F4 | force or simulate an Obsidian write outside `projects/test-proj/code/` | policy gate records `deny`; no file is written |
| K4 | Allowed handoff scope | F4 | create a code-lane handoff/provenance note through the supported delegation path | audit row is scoped to `projects/*/code/`; no repository files are edited by Hermes |

### 4.7 Deterministic operations (report-only or generated)

These are deterministic operation entry points, not chat profile skills. They are covered here so the CLI test plan exercises the current implementation surface in [Operations](../../reference/operations.md).

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| O1 | Linter | a vault with a planted defect (e.g. broken wikilink) | `python src/.memoria/operations/integrity/linter/detectors.py --vault <vault>` | findings written to `system/logs/lint-findings.jsonl`; the planted defect appears; report-only (no fixes) |
| O2 | Schema check | a note with an out-of-vocab `methodology` | linter schema detector via the supported linter command | the schema violation flagged; no auto-fix |
| O3 | Schema migration | a field rename scenario | supported migration script with `--dry-run` | a **dry-run** proposal of the changes; **no** write until run without `--dry-run` (always dry-run first) |
| O4 | Graph analysis | F3 + an orphan note | linter graph-health detector via the supported linter command | graph-health output: orphan list, hubs, link density; orphan note appears |
| O5 | Fleet metrics | exported board state and logs | `python src/.memoria/mcp/metrics_aggregate.py --vault <vault>` | a verdict band `PASS` / `REVIEW` / `FAIL` rolled from current findings |
| O6 | Session digest *(deferred)* | — | daily lint cron invokes `session_summary.py` | a per-session digest at `system/logs/sessions/<timestamp>.jsonl` — written by the Linter's `session_summary.py` on the daily lint cron, not by a `session-log` CLI command ([ADR-25](../../adr/25-session-logging-two-logs.md)); sessions are digested after a 24 h quiet window |
| O7 | Dry-run | — | operation-specific `--dry-run` where available | runs any check report-only; confirm no writes besides the findings log |
| O8 | **Linter scope** | — | during O1 | only `system/logs/**` writes occur for the Linter operation; cosmetic/log auto-fixes only |

### 4.8 Board management — `hermes kanban …` (non-interactive)

| ID | Run | Pass criteria |
|---|---|---|
| B1 | `hermes kanban create "test card" --assignee memoria-librarian` | new card appears in `triage`; note its `<id>` |
| B2 | `hermes kanban list` | the B1 card listed with status `triage` |
| B3 | `hermes kanban show <id>` | full state: status, retry count, blocker, handoff summary |
| B4 | `hermes kanban specify <id>` | card fleshed out → `todo` |
| B5 | `hermes kanban release <id>` | card → `ready` |
| B6 | `hermes kanban dispatch` | dispatcher claims `ready` cards on matching lanes → `running`; transition logged in `board-transitions.jsonl` |
| B7 | `hermes kanban claim <id>` | manual claim succeeds (debug path) |
| B8 | `hermes kanban decompose <id>` (on a `triage` card) | child task cards created and linked to the parent |
| B9 | `hermes kanban edit <id> --assignee memoria-writer` | assignee corrected on the card |
| B10 | `hermes kanban unblock <id>` (on a `blocked` card) | card → `ready` |
| B11 | `hermes kanban archive <id> --reason "test cleanup"` | card archived (terminal) with the reason recorded |
| B12 | review-gate check: `hermes kanban` action advancing a card out of `done` before it is approved (lifecycle still `proposed`) | refused — the gate is a dispatch precondition (see [Policy MCP](../../reference/policy-mcp.md)) |

### 4.9 Profile management

| ID | Run | Pass criteria |
|---|---|---|
| P1 | `hermes profile list` | all 5 `memoria-*`: alias, status, installed path |
| P2 | `hermes profile show memoria-peer-reviewer` | shows `SOUL.md`, MCP servers (`policy`, `obsidian`), allowed skills, `.env` key **names** (values redacted), and model = `meta-llama/llama-4-scout` |
| P3 | `bash scripts/install.sh --profiles-only` (the supported form of `profile install`) | deploys vault source → `~/.hermes/profiles/`; re-run `profile show` reflects the change |
| P4 | `hermes profile remove memoria-<tmp>` (on a throwaway alias) | registration removed; vault source under `.memoria/profiles/` **untouched** |

### 4.10 Skills

| ID | Run | Pass criteria |
|---|---|---|
| SK1 | `hermes skills list` | available skills listed |
| SK2 | `hermes profile show memoria-librarian \| grep -i skill` | the Librarian's loaded skills incl. `catalog-enrich-record`, `qmd` |
| SK3 | `hermes skills install <skill>` (a test skill) | skill installs and then appears in `skills list` |

### 4.11 Scheduled tasks (cron)

| ID | Run | Pass criteria |
|---|---|---|
| CR1 | `hermes cron list` | scheduled tasks with next-run times (e.g. the Librarian map-lane weekly cluster scan, board-export) |
| CR2 | `hermes cron run <task>` | task runs immediately; its expected artifact/log appears |
| CR3 | `hermes cron disable <task>` then `cron list` | task shows disabled |
| CR4 | `hermes cron enable <task>` then `cron list` | task re-enabled with a next-run |

---

## 5. Cross-cutting invariant tests

These assert the *architecture*, independent of any one command — run after the matrix.

| ID | Test | Pass criteria |
|---|---|---|
| X1 | **Deny path** — force a Librarian write to `notes/claims/` | `decision: deny` row for `memoria-librarian` in `audit.jsonl`; no file written |
| X2 | **Co-PI write-wall** — any Co-PI write attempt | `deny` (or structurally impossible — `policy.allow.write: []`) |
| X3 | **Review-gate degradation** — Writer/agent write to `notes/claims/` or `notes/hubs/` | logged as `dry_run`, not `allow_with_log` — no real write without human approval |
| X4 | **Audit pairing integrity** — after a batch of writes | every `allow_with_log` row carries `before_hash`/`after_hash` and a paired `write_complete` (`lint`'s `audit-unpaired-writes` reports clean) |
| X5 | **Dry-run safety** — Peer-reviewer skills and deterministic operations with `--dry-run` | produce reports but leave target files byte-identical (`git diff` empty for those paths) |
| X6 | **Per-lane write scope** — sample each lane's audit rows | every `allow_with_log` path falls inside that lane's declared write scope ([Profiles](../../reference/profiles.md)) |
| X7 | **Model in effect** — `profile show` for all 5 | all on `meta-llama/llama-4-scout` during the run; restored to Claude tiers after (§1.5) |

---

## 6. Results log (template)

| Test ID | Date | Result (PASS/FAIL/BLOCKED) | Observed artifact / audit row | Notes |
|---|---|---|---|---|
| S1 | | | | |
| … | | | | |

**Exit criteria.** Every per-profile command produced its expected artifact (or, for
read-only/dry-run, provably wrote nothing); every board/admin/cron command returned the
expected state; all X-series invariants held. Any `FAIL` is filed as an issue with the
command, the expected vs. observed artifact, and the relevant `audit.jsonl` row.
