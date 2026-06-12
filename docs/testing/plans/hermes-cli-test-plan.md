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

### 1.1 Switch all agents to the cheapest test model

Run the suite on the **cheapest paid, tool-capable model on the KiloCode gateway**,
confirmed **2026-06-02** against `GET https://api.kilo.ai/api/gateway/models` (no auth;
the gateway returns live per-token prices). Method: rank the catalog by input price,
drop free models and the pass-through routers (`openrouter/auto` et al., sentinel-priced),
and keep only models whose `supported_parameters` include tool calling — an agent **must**
call MCP tools, so a model without tool support can't run the suite at all.

| Model | Input $/1M | Output $/1M | Context | Tools | Note |
|---|---|---|---|---|---|
| **`inclusionai/ling-2.6-flash`** | **0.010** | **0.030** | 262K | yes | **chosen — cheapest on input, output, and blended** |
| `meta-llama/llama-3.1-8b-instruct` | 0.020 | 0.050 | 131K | yes | fallback #1 |
| `openai/gpt-oss-20b` | 0.029 | 0.140 | 131K | yes | fallback #2 |
| `z-ai/glm-4.7-flash` | 0.070 | 0.400 | 203K | yes | the originally-suggested example — **~7×/13× more expensive, not cheapest** |

The gateway already reaches `inclusionai/ling-2.6-flash` via your existing
`KILOCODE_API_KEY` — no new provider or key.

> **Tool-use caveat.** Ultra-cheap models tool-call less reliably than the Claude tiers.
> If a command fails on the *model's* tool-use (malformed MCP call, refusal to emit the
> write) rather than the wiring, step down the fallback list above before concluding the
> command is broken. Re-confirm prices at run time — the catalog changes.

For each of the five profiles, edit `vault/.memoria/profiles/memoria-<name>/config.yaml`
and set the **main** model:

```yaml
model:
  provider: kilocode
  base_url: https://api.kilo.ai/api/gateway
  default: inclusionai/ling-2.6-flash   # TEST MODEL — production is ~anthropic/claude-<tier>-latest
```

Production tiers to restore afterwards: Librarian/Engineer `claude-haiku-latest`,
Writer `claude-sonnet-latest`, co-PI/Peer-reviewer `claude-opus-latest`.

Then **deploy** the source to the runtime copies and confirm:

```bash
bash scripts/install.sh --profiles-only      # .\scripts\install.ps1 -ProfilesOnly on Windows
hermes profile show memoria-librarian | grep -i model   # expect inclusionai/ling-2.6-flash
```

> Auxiliary slots (title/approval/mcp/skills-hub/compression) are already cheap and
> set in the **global** `~/.hermes/config.yaml`; leave them. See
> [configuration.md § Auxiliary models](../../how-to-guides/hermes-agent/configuration.md).

### 1.2 Runtime prerequisites

| Prereq | Check |
|---|---|
| Hermes ≥ 0.12 installed; 5 `memoria-*` profiles registered | `hermes profile list` shows all five |
| Obsidian open with Local REST API on `127.0.0.1:27124`, `OBSIDIAN_API_KEY` set | `curl -sk https://127.0.0.1:27124/ -H "Authorization: Bearer $OBSIDIAN_API_KEY"` returns JSON |
| Hermes gateway on `:8642` (needed for `kanban dispatch`) | `hermes gateway status` |
| Zotero running with Better BibTeX; `.memoria/memoria.bib` present | file exists, contains the F1 citekeys |
| `KILOCODE_API_KEY`, `OPENALEX_API_KEY` set per profile `.env` | `hermes profile show memoria-librarian` lists the keys (values redacted) |
| **Disposable test vault** (clone/fixture, never the real research vault) | `HERMES_HOME` / vault path points at the test copy |

### 1.3 Test fixtures (create once, referenced by ID below)

| ID | Fixture |
|---|---|
| **F1** | Two Zotero items with pinned BBT citekeys exported to `.memoria/memoria.bib` — one with an open-access PDF (call it `smithA`) and one without (`jonesB`). |
| **F2** | `research-focus.md` with ≥ 1 concrete priority topic. |
| **F3** | ≥ 5 claim notes (`type: claim`) in `notes/claims/` on a shared topic (for Librarian map lane/Writer/Peer-reviewer). |
| **F4** | A project at `projects/test-proj/` with a `README.md` (project note) and the canonical subfolders `01-map … 06-code`. |
| **F5** | A draft `projects/test-proj/04-drafts/draft.md` citing both a **resolvable** citekey (`smithA`) and a **bogus** one (`@nope1999`). |
| **F6** | Two near-duplicate claim notes (`type: claim`, same idea, different wording) for `find-duplicates`. |
| **F7** | One paper entry (`type: paper`) whose `enriched_date` is > 180 days old (for `enrich`/staleness). |
| **F8** | One retracted-DOI paper entry (`type: paper`, or a known retracted DOI) for `retraction-check`. |

### 1.4 Verification toolbox (how every test is checked)

- **Vault write** → the file exists at the expected path with the expected frontmatter/body; e.g. `grep -l '^type: paper' catalog/papers/smithA.md`.
- **Policy gate** → `system/logs/audit.jsonl` gains a row: `decision: allow_with_log` (permitted) or `deny` (forbidden), each carrying `before_hash`/`after_hash`. `tail -1 system/logs/audit.jsonl | jq`.
- **Board state** → `hermes kanban show <id>` / `kanban list`; transitions also land in `system/logs/board-transitions.jsonl`.
- **Telemetry** → `disposition.jsonl`, `cost.jsonl`, `lint-findings.jsonl` per [Telemetry & logs](../../reference/telemetry.md).
- **Read-only / dry-run** → assert the **inverse**: no new file, and **no** `allow_with_log` write row for that lane in `audit.jsonl`.

### 1.5 Reset after testing

```bash
git checkout -- vault/.memoria/profiles/memoria-*/config.yaml   # restore production model tiers
bash scripts/install.sh --profiles-only                          # redeploy production config
# discard the disposable test vault
```

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
| S2 | `hermes profile show memoria-engineer \| grep -i model` | model = `inclusionai/ling-2.6-flash` (test config is live) |
| S3 | `hermes -p memoria-librarian chat -s query "<F2 topic>"` | returns ranked results; **no** write row in `audit.jsonl` |
| S4 | `hermes -p memoria-librarian chat -s ingest smithA` | `catalog/papers/smithA.md` created; `allow_with_log` row in `audit.jsonl` |
| S5 | `hermes -p memoria-copi chat -s socratic-processing catalog/papers/smithA.md` then ask it to "write a note" | questions only; **`deny`** (or no write) for `memoria-copi` in `audit.jsonl` — write-wall holds |

If S1–S5 pass, proceed to the full matrix.

---

## 4. Command test cases

### 4.1 Librarian — `hermes -p memoria-librarian chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| L1 | `find` | F2 | `find "<topic>"` | ≥1 candidate card in `inbox/` with `type: candidate`, `source: find`; `allow_with_log` write row |
| L2 | `ingest` | F1 (`smithA`) | `ingest smithA` | `catalog/papers/smithA.md` with `type: paper`, `citekey`, `_proposed_classification`, `_enrichment`, top-of-body `[!brief]` callout; Marker extract in `.memoria/data/extracts/smithA.md`; audit write row |
| L3 | `ingest` (no PDF) | F1 (`jonesB`) | `ingest jonesB` | note created; `extract_path` blank (not aborted); ingest still completes |
| L4 | `obsidian-paper-note` | F1 (`smithA`, delete the L2 note first) | `obsidian-paper-note smithA` | same as L2 — full pipeline incl. `[!brief]` (this is the skill `ingest` wraps) |
| L5 | `enrich` | F7 | `enrich <citekey>` | `_enrichment` refreshed, top-level `enriched_date` = today; audit write row; main human fields untouched |
| L6 | `classify` | a paper entry (`type: paper`) with empty/low-confidence `_proposed_classification` | `classify <citekey>` | `_proposed_classification` re-proposed (values from the controlled vocabulary — [Frontmatter fields](../../reference/frontmatter.md)); human fields still empty |
| L7 | `query` | F3 | `query "<claim topic>"` | ranked matches returned; **read-only** — no write row in `audit.jsonl` |
| L8 | `export prior-labels` | F3 + some paper entries | `export prior-labels` | an ASReview-format priors file produced; row count = # matching the frontmatter filter |

### 4.2 Librarian (map lane) — `hermes -p memoria-librarian chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| M1 | `scope-project` | F3 + F4 | `scope-project --project test-proj --output projects/test-proj/01-map/corpus-map.md` | `corpus-map.md` written under `01-map/`; `sources:` frontmatter names what was scanned; audit write row scoped to `01-map/` |
| M2 | `gap-report` | F3 + F4 | `gap-report --project test-proj` | `gap-report.md` in `01-map/` listing thin-coverage topics |
| M3 | `cluster-map` | F3 | `cluster-map "<topic>"` | density/recency artifact in `01-map/cluster-maps/` (table/figure, not prose) |
| M4 | **map-lane write-wall** | — | (during M1) attempt/observe any write outside `01-map/` | none occurs; if forced, `deny` row for `memoria-librarian` (the map lane is read-only across `catalog/`, `notes/`, etc.) |

### 4.3 co-PI — `hermes -p memoria-copi chat -s …` (read-only)

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| C1 | `socratic-processing` | F1 note | `socratic-processing catalog/papers/smithA.md` | questioning turns only; **zero** vault writes; any write attempt → `deny` for `memoria-copi` |
| C2 | `lens-reading` | a lens slug exists | `lens-reading <author>-<concept>` on a note | questions framed by the lens; still no writes |

### 4.4 Writer — `hermes -p memoria-writer chat -s …`

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| W1 | `draft` | F3 | `draft "<question over F3 claims>"` | an answer card in `inbox/`; card → `done`, queued for review (lifecycle stays `proposed`); audit write row |
| W2 | `query` | F3 | `query "<term>"` | ranked results; read-only (no write row) |
| W3 | `lint` (handoff) | a draft | `lint` | a Linter-engine request/card is raised; **Writer writes nothing to logs** — the Linter engine executes (verify no Writer lint output, a handoff card instead) |
| W4 | `promote` (handoff) | an evergreen claim (`type: claim`, `maturity: evergreen`) | `promote <claim>` | a promotion proposal surfaces; the write into `notes/claims/` is **review-gated → `dry_run`** in `audit.jsonl` (no real write until human approves) |

### 4.5 Peer-reviewer — `hermes -p memoria-peer-reviewer chat -s …` (dry-run by default)

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| V1 | `cite-check` | F5 | `cite-check projects/test-proj/04-drafts/draft.md` | report/`[!verification]` flags `@nope1999` as unresolved, `smithA` as OK; **no edit to the draft** (dry-run) |
| V2 | `claim-trace` | F5 + F3 | `claim-trace …/draft.md` | per-claim trace; each unsupported claim spawns a gap card in `inbox/` (`type: gap`, `source: gap`); only the gap-card write appears in audit |
| V3 | `similarity-check` | F3 + a new claim | `similarity-check "<new claim>"` | top-N with scores; flags ≥ ~0.8; **never merges** (no write to existing notes) |
| V4 | `find-duplicates` | F6 | `find-duplicates` | the F6 pair surfaced as a merge candidate; no auto-merge |
| V5 | `retraction-check` | F8 | `retraction-check` | the retracted paper flagged against Zotero/CrossRef; dry-run (report only) |

### 4.6 Engineer — `hermes -p memoria-engineer chat -s …` (MCP-only; no terminal/file)

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| K1 | `scaffold` | F4 | `scaffold --project test-proj` | code-note skeleton from template under `projects/test-proj/06-code/`; audit write row scoped to `06-code/` |
| K2 | `code` | F4 | `code "<task>"` | a code-note handoff scaffolded with vault context (sources, purpose); external-agent handoff recorded, not run by Memoria |
| K3 | `commit` | a change in `06-code/` | `commit` | exactly one logical git commit created (one change per call) |
| K4 | `revert` | a prior K3 commit | `revert <commit>` | that commit reverted; scope small; no other files touched |
| K5 | `workspace` | F4 | `workspace` | VS Code workspace set up with vault **read-only** and the `06-code/` zone writable |
| K6 | **Engineer write-wall** | — | (during K1) | writes confined to `projects/*/06-code/`; any write elsewhere → `deny` |

### 4.7 Linter engine (report-only)

The Linter is an **engine** the Librarian/system invokes, not a chat profile —
`memoria-linter` is retired. These checks run as engine passes (report-only); the
findings land in the logs below.

| ID | Command | Setup | Run | Pass criteria |
|---|---|---|---|---|
| S1 | `lint` | a vault with a planted defect (e.g. broken wikilink) | `lint` | findings written to `system/logs/lint-findings.jsonl`; the planted defect appears; report-only (no fixes) |
| S2 | `schema-check` | a note with an out-of-vocab `methodology` | `schema-check` | the schema violation flagged; no auto-fix |
| S3 | `schema-migrate` | a field rename scenario | `schema-migrate --field X --from a --to b --dry-run` | a **dry-run** proposal of the changes; **no** write until run without `--dry-run` (always dry-run first) |
| S4 | `graph-analyze` | F3 + an orphan note | `graph-analyze` | graph-health output: orphan list, hubs, link density; orphan note appears |
| S5 | `health-report` | — | `health-report` | a verdict band `PASS` / `REVIEW` / `FAIL` rolled from current findings |
| T6 | `session-log` *(deferred)* | — | `session-log` | a per-session summary at `system/logs/sessions/<id>.jsonl` — **deferred: no `session-log` command or writer ships in 0.1.0-alpha.1 ([ADR-25](../../adr/25-session-logging-two-logs.md)); skip until built** |
| T7 | `dry-run` | — | `dry-run lint` | runs any check report-only; confirm no writes besides the findings log |
| T8 | **Linter scope** | — | (during S1) | only `system/logs/**` writes occur for the Linter engine; cosmetic/log auto-fixes only |

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
| P2 | `hermes profile show memoria-peer-reviewer` | shows `SOUL.md`, MCP servers (`policy`, `obsidian`), allowed skills, `.env` key **names** (values redacted), and model = `inclusionai/ling-2.6-flash` |
| P3 | `bash scripts/install.sh --profiles-only` (the supported form of `profile install`) | deploys vault source → `~/.hermes/profiles/`; re-run `profile show` reflects the change |
| P4 | `hermes profile remove memoria-<tmp>` (on a throwaway alias) | registration removed; vault source under `.memoria/profiles/` **untouched** |

### 4.10 Skills

| ID | Run | Pass criteria |
|---|---|---|
| SK1 | `hermes skills list` | available skills listed |
| SK2 | `hermes profile show memoria-librarian \| grep -i skill` | the Librarian's loaded skills incl. `obsidian-paper-note`, `qmd` |
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
| X2 | **co-PI write-wall** — any co-PI write attempt | `deny` (or structurally impossible — `policy.allow.write: []`) |
| X3 | **Review-gate degradation** — Writer/agent write to `notes/claims/` or `notes/hubs/` | logged as `dry_run`, not `allow_with_log` — no real write without human approval |
| X4 | **Audit pairing integrity** — after a batch of writes | every `allow_with_log` row carries `before_hash`/`after_hash` and a paired `write_complete` (`lint`'s `audit-unpaired-writes` reports clean) |
| X5 | **Dry-run safety** — all Peer-reviewer/Linter-engine default-dry-run commands | produce reports but leave target files byte-identical (`git diff` empty for those paths) |
| X6 | **Per-lane write scope** — sample each lane's audit rows | every `allow_with_log` path falls inside that lane's declared write scope ([Profiles](../../reference/profiles.md)) |
| X7 | **Model in effect** — `profile show` for all 5 | all on `inclusionai/ling-2.6-flash` during the run; restored to Claude tiers after (§1.5) |

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
