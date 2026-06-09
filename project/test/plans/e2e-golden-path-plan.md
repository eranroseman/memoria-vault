---
topic: tests
title: Golden-path end-to-end test plan
status: draft
---

# Golden-path E2E test plan — v0.1 (L4)

One source carried through the **whole lifecycle** — capture → ingest → classify → discuss → synthesize → map → draft → verify → export — across all seven profiles, the Kanban board, and the review gate, as a single trace. Where the [Hermes CLI plan](hermes-cli-test-plan.md) tests each command in isolation, this asserts the **handoffs compose**: board memory travels lane-to-lane, the review gate holds at the synthesis/deliverable boundary, and an artifact actually reaches a deliverable. Like the CLI plan, it asserts *artifact shape and gate decisions, not prose quality* (quality is the [eval harness](../../../docs/adr/11-vault-eval-integration.md), L5).

**Where to run.** The integrated stack: Obsidian open (REST bridge up) + Hermes in WSL2 + a **disposable** vault seeded with the CLI plan's fixtures (F1–F8). Run it after the CLI and GUI plans pass — this is the capstone.

**How to read each step.** **Action** → **✓ Pass** → **✗ If it fails**. Each stage's output is the next stage's input; a stage failing **blocks** the rest — record where the chain broke.

---

## 0. Preconditions

- [ ] CLI plan green (commands work individually) and GUI plan green (bridge + dashboards).
- [ ] Disposable vault with fixtures F1 (`smithA` w/ PDF), F2 (`research-focus`), F4 (project `test-proj`).
- [ ] Gateway up (`hermes gateway status`) for `kanban dispatch`; cron tickable.

---

## Part A — Capture → ingest → classify (Librarian)

**A1. Ingest a real source.** `hermes -p memoria-librarian chat -s ingest smithA`
- ✓ Pass: `20-sources/01-papers/smithA.md` (`type: paper-note`, `citekey`, `_proposed_classification`, `_enrichment`, `[!brief]`); Marker extract in `90-assets/extracts/`; `allow_with_log` row in `audit.jsonl`.

**A2. Human classifies.** Set `lifecycle: current` + a `study_design` from vocab on `smithA.md`.
- ✓ Pass: it now surfaces in `reading-pipeline.md` (open the dashboard) — proves the source entered the human's pipeline.

---

## Part B — Discuss (Socratic, read-only)

**B1.** `hermes -p memoria-socratic chat -s socratic-processing 20-sources/01-papers/smithA.md`
- ✓ Pass: questioning turns only; **zero** vault writes (no `memoria-socratic` `allow_with_log` row) — the write-wall holds mid-pipeline.

---

## Part C — Synthesize (human claim) → map (Mapper)

**C1. Human writes a claim** in `30-synthesis/01-claims/` citing `smithA` (this is human territory — agents can't).
- ✓ Pass: claim note created (human write, not gated as an agent).

**C2. Map the corpus.** `hermes -p memoria-mapper chat -s scope-project --project test-proj --output 40-workbench/test-proj/01-map/corpus-map.md`
- ✓ Pass: `corpus-map.md` under `01-map/`; audit row scoped to `01-map/`; **no** write outside it (Mapper write-wall).

---

## Part D — Draft → verify (Writer → Verifier)

**D1. Draft.** `hermes -p memoria-writer chat -s draft "<question over the claim>"`
- ✓ Pass: `answer-note` in `10-inbox/02-answers/`; its card → `done`, `review_status: requested`; audit row.

**D2. Cite-check the draft.** `hermes -p memoria-verifier chat -s cite-check <draft path>` (draft cites `smithA` + a bogus key)
- ✓ Pass: report flags the bogus cite, passes `smithA`; **dry-run** — draft byte-identical after (`git diff` empty).

---

## Part E — Review gate → promote → export

**E1. Promotion is gated.** `hermes -p memoria-writer chat -s promote <claim>`
- ✓ Pass: the write into `30-synthesis/02-reference/` logs as **`dry_run`** in `audit.jsonl` — *no real write* without human approval. (The gate's whole point.)

**E2. Human approves, then export.** Approve the card (`review_status: approved`), then `hermes -p memoria-coder chat -s …` export to `50-deliverables/`.
- ✓ Pass: after approval the gated write becomes `allow_with_log`; a deliverable lands in `50-deliverables/`. The chain reached the end.

---

## Part F — The trace held together

| # | Cross-cutting check | ✓ Pass |
| --- | --- | --- |
| F1 | **Board carried the work** | each stage's card moved lane-to-lane; transitions in `board-transitions.jsonl`; `board-state.md` reflects it |
| F2 | **Audit chain unbroken** | every `allow_with_log` row has `before_hash`/`after_hash`; `lint`'s `vault-hash-drift` clean |
| F3 | **Gate held at the boundary** | the only `dry_run`→`allow_with_log` transitions are the human-approved promotions (E1→E2); no agent wrote canon unapproved |
| F4 | **Dashboards reflect reality** | `daily-health`, `audit-log`, `reading-pipeline` all show the run's activity |

---

## Results

| Stage | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | ingest + classify → pipeline | | |
| B | Socratic read-only mid-pipeline | | |
| C | human claim + Mapper scope | | |
| D | draft + cite-check (dry-run) | | |
| E | gate blocks promote → approve → export | | |
| F | board / audit / gate / dashboards held | | |

**L4 green** when one source traverses A→E end-to-end and all F invariants hold. Record in [Release plan — v0.1.0](../../release/v0.1/release-plan-v0.1.md).
