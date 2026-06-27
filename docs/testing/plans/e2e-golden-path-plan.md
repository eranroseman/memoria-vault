---
topic: tests
title: Golden-path end-to-end test plan
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 12
---

# Golden-path E2E test plan — v0.1 (L4)

One source carried through the **whole lifecycle** — capture → ingest → classify → discuss → synthesize → map → draft → verify → export — across all five profiles, the Kanban board, and the review gate, as a single trace. Where the [Hermes CLI plan](hermes-cli-test-plan.md) tests each command in isolation, this asserts the **handoffs compose**: board memory travels lane-to-lane, the review gate holds at the synthesis/deliverable boundary, and an artifact actually reaches a deliverable. Like the CLI plan, it asserts *artifact shape and gate decisions, not prose quality* (quality is the [eval harness](../../adr/11-vault-eval-maintenance.md), L5).

**Where to run.** The integrated stack: Obsidian open (REST bridge up) + Hermes in WSL2 + a **disposable** vault seeded with the CLI plan's fixtures (F1–F8). Run it after the CLI and GUI plans pass — this is the capstone.

**Automated Phase 1 slice.** The [test-env harness](test-env-harness-plan.md) replays
the model-free ADR-80 cassette for the same source → classify → discuss → claim →
Project space → draft → verify → export shape and is wired into
[`scripts/e2e-smoke.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/e2e-smoke.sh).
Use this page for the attended runtime path; use the harness for per-PR deterministic
coverage.

**How to read each step.** **Action** → **✓ Pass** → **✗ If it fails**. Each stage's output is the next stage's input; a stage failing **blocks** the rest — record where the chain broke.

---

## 0. Preconditions

- [ ] CLI plan green (commands work individually) and GUI plan green (bridge + dashboards).
- [ ] Disposable vault with fixtures F1 (`smithA` w/ PDF), F2 (`research-focus`), F4 (project `test-proj`).
- [ ] Gateway up (`hermes gateway status`) for `kanban dispatch`; cron tickable.

---

## Part A — Capture → ingest → classify (Librarian)

**A1. Ingest a real source.** `hermes -p memoria-librarian chat -s ingest smithA`
- ✓ Pass: `catalog/papers/smithA.md` (`type: paper`, `citekey`, `_proposed_classification`, `_enrichment`, `[!brief]`); Marker extract in `.memoria/data/extracts/`; `allow_with_log` row in `audit.jsonl`.

**A2. Human classifies.** Set `lifecycle: current` + a `methodology` from vocab on `smithA.md`.
- ✓ Pass: it now surfaces in the Library space's Reading pipeline — proves the source entered the human's pipeline.

---

## Part B — Discuss (Co-PI questioning, read-only)

**B1.** `hermes -p memoria-copi chat catalog/papers/smithA.md` (a Co-PI questioning pass)
- ✓ Pass: questioning turns only; **zero** vault writes (no `memoria-copi` `allow_with_log` row) — the write-wall holds mid-pipeline.

---

## Part C — Synthesize (human claim) → map (Librarian, map lane)

**C1. Human writes a claim** in `notes/claims/` citing `smithA` (this is human territory — agents can't).
- ✓ Pass: claim note created (human write, not gated as an agent).

**C2. Map the corpus.** `hermes -p memoria-librarian chat -s scope-project --project test-proj --output projects/test-proj/map/corpus-map.md`
- ✓ Pass: `corpus-map.md` under `map/`; audit row scoped to `map/`; **no** write outside it (map-lane write-wall).

---

## Part D — Draft → verify (Writer → Peer-reviewer)

**D1. Draft.** `hermes -p memoria-writer chat -s draft "<question over the claim>"`
- ✓ Pass: `answer-note` in `inbox/`; its card → `done` and queued for review (lifecycle stays `proposed`); audit row.

**D2. Cite-check the draft.** `hermes -p memoria-peer-reviewer chat -s cite-check <draft path>` (draft cites `smithA` + a bogus key)
- ✓ Pass: report flags the bogus cite, passes `smithA`; **dry-run** — draft byte-identical after (`git diff` empty).

---

## Part E — Review gate → promote → export

**E1. Promotion is gated.** `hermes -p memoria-writer chat -s promote <claim>`
- ✓ Pass: the write into `notes/claims/` logs as **`dry_run`** in `audit.jsonl` — *no real write* without human approval. (The gate's whole point.)

**E2. Human approves, then export.** Approve the card (advance its lifecycle to `current`), then `hermes -p memoria-engineer chat -s …` export to `projects/`.
- ✓ Pass: after approval the gated write becomes `allow_with_log`; a deliverable lands in `projects/`. The chain reached the end.

---

## Part F — The trace held together

| # | Cross-cutting check | ✓ Pass |
| --- | --- | --- |
| F1 | **Board carried the work** | each stage's card moved lane-to-lane; transitions in `board-transitions.jsonl`; `board-state.md` reflects it |
| F2 | **Audit pairing intact** | every `allow_with_log` row has `before_hash`/`after_hash`; `lint`'s `audit-unpaired-writes` clean |
| F3 | **Gate held at the boundary** | the only `dry_run`→`allow_with_log` transitions are the human-approved promotions (E1→E2); no agent wrote canon unapproved |
| F4 | **Dashboards reflect reality** | the rail Now badges, `audit-log`, and Library's Reading pipeline all show the run's activity |

---

## Results

| Stage | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | ingest + classify → pipeline | | |
| B | Co-PI read-only mid-pipeline | | |
| C | human claim + Librarian (map lane) scope | | |
| D | draft + cite-check (dry-run) | | |
| E | gate blocks promote → approve → export | | |
| F | board / audit / gate / dashboards held | | |

**L4 green** when one source traverses A→E end-to-end and all F invariants hold. Record the result in the relevant readiness/stage sub-issue under the current release parent issue; preserve run details in that release folder's `validation-log.md` only when a curated summary is worth keeping.
