# ADR review — gap analysis, trigger re-verification, and Memoria-way defaults

Working note (alpha.5 `tmp/`). Consolidates a full ADR audit done 2026-06-15:
a status-vs-implementation gap analysis across all 76 ADRs, a skeptical
re-verification of every deferral trigger ("don't assume the author was right"),
and researched "Memoria way" replacements for the triggers that depended on
PI eyeballing. Recommendations only — no ADRs were edited. Delete before the
alpha.5 checkpoint closes; route durable changes into the ADRs themselves.

Method: parallel sub-agent audit (7 agents over the 76 ADRs), independent
spot-verification of the headline gaps, 3 skeptical agents re-checking triggers,
and 5 research agents grounding the Memoria-way defaults in our docs + external
best practice (citations inline).

---

## 1. Status ↔ implementation gaps

The corpus is healthy: almost every `accepted` ADR is genuinely built, all 7
`superseded` ADRs have their superseding mechanism live, and `deferred` ADRs are
correctly unbuilt. Three real gaps, a few cosmetic, three accepted-but-partial
by design.

### 1.1 Real gaps — status changes warranted

- **ADR-17 (shared candidate frontmatter) — silently superseded.** The shipped
  type is `type: candidate` (decision-card fields); ADR-17's normative schema
  (`candidate-note`, `source`/`candidate_status`/`exclusion_reason`, folder
  `99-system/`) does not exist — replaced by ADR-50/51. Its `superseded_by:` is
  `[]`. **Fix:** set `superseded_by: [50, 51]` (or a status banner) and drop the
  stale schema text. *Verified: `type: candidate`, none of ADR-17's fields
  present.*
- **ADR-62 (measurement harnesses) — deferred-but-built.** The "fleet
  observability aggregator" it lists as deferred is built and cron-wired
  (`src/.memoria/mcp/metrics_aggregate.py` + `metrics-cron.sh` →
  `fleet-health.md`); the other five harnesses remain genuinely deferred.
  **Fix:** mark that one item adopted/implemented (trust-score weights + `pass^k`
  are still TODO) or amend the "until the aggregator exists, the dashboard is
  empty" line. *Verified: all three files exist.*
- **ADR-44 (L1 tests in pytest tree) — end-state not met.** Claims "the deployed
  vault carries zero test code," but 7 shipped modules still carry inline
  `_self_test()`: `engines/lib/schema.py`, `engines/lib/inbox.py`,
  `engines/linter/golden.py`, `engines/linter/precommit_check.py`,
  `mcp/cluster_mcp.py`, `mcp/tasks_mcp.py`, `mcp/patterns_mcp.py` (two —
  `precommit_check`, `patterns_mcp` — have no `tests/` equivalent, so stripping
  now loses coverage). **Fix:** finish the migration (add the 2 missing test
  files first, then strip the 7) or amend the "zero test code" consequence.
  *Verified: all 7 present.*

### 1.2 Minor / cosmetic

- **ADR-30** — `ingest_status` is written by engine code but not declared in
  `paper.yaml`, so it escapes schema validation. Add the enum.
- **ADR-18** — residual `agent_verdict` back-compat fallback in `board_export.py`
  contradicts "only this ADR retains the old name." Drop it or note it's
  intentional.
- **ADR-54** — batch worklist ships as a fleeting note + one aggregate card, not
  the per-row-toggle Bases surface the prose describes. One-line clarification.
- **ADR-16** — `accepted` but functionally "accepted-that-we-defer"; could read
  more honestly as deferred. Low priority.

### 1.3 Verify (claims not confirmable from the audit)

- **ADR-21** — the "overnight → `inbox/` only" rule was not found inline in
  `policy_mcp.py`; likely enforced via `lane-overrides/`. Confirm.
- **ADR-38** — cites a `find-duplicates` retrospective sweep as already existing;
  no such engine/script was found in `engines/`/`scripts/`. Confirm (aspirational
  vs. lives elsewhere).

### 1.4 Accepted-but-partial — by design, already tracked

ADR-69 (engines→operations rename not executed — sequenced; Workstream H in the
alpha.4 ExecPlan), ADR-70 (Knowledge-gate dashboard + status-bar indicator #375),
ADR-71 (schema↔form parity test + per-type forms). Open work inside in-progress
alpha ADRs, not status drift.

---

## 2. Deferral-trigger re-verification (skeptical pass)

Several triggers do not hold up when challenged.

### 2.1 Stale / already fired

- **ADR-62** — fleet aggregator built; deferral + "dashboard empty until
  aggregator exists" is stale (see 1.1).
- **ADR-38(a)** — "live qmd in the agent retrieval path" is now satisfied (qmd is
  wired into the Librarian's `catalog-rank-candidate` and `map-scope-project`
  skills). Only part (b) corpus density remains. Mark (a) met in the ADR.

### 2.2 Gating on the wrong signal — rescope

- **ADR-74 (plugin provenance) — wrong signal.** "Revisit when a security
  advisory hits" inverts a supply-chain control (you want provenance *before* an
  incident). 12 executable plugins are vendored under `src/.obsidian/plugins/`
  with zero pinned commit/SHA/license today. → Land the static lock manifest now
  [S]; defer the updater + CI doctor.
- **ADR-39 — arbitrary threshold holds the cheap half hostage.** "50+ claim
  notes" gates everything, but the mechanically-checkable criteria are
  template-derivable now. → Split (see 3.2).
- **ADR-61 (nightly loop) — false dependency.** Requires "always-on
  Syncthing+VPS," but a single non-sleeping workstation suffices; it imports
  ADR-63's heaviest topology. → Rescope to "any always-on machine" (doc-only).
- **ADR-59 (discovery relevance scorer) — over-coupled.** Gated on ADR-61's loop,
  but the deterministic scorer already ships and could apply to *reactive* find
  today. → Decouple.
- **ADR-40 (admin GUI) — gates on the wrong thing.** Waits on a hackathon tool's
  stars/maintainers; the real objection is architectural (a second un-gated write
  surface). → Re-point at "does the ADR-58 read-only Inspector cover the forensic
  gap?"

### 2.3 Cheap, safe, author-blessed slices sitting undone — pick up now

- **ADR-76 step-1** — the ADR labels the tooling-only `pyproject.toml` (+ delete
  the `conftest.py` `sys.path` block) "safe to land anytime"; still undone. [S]
  (Full wheel stays deferred behind the ADR-69 rename + policy-gate decision.)
- **ADR-41 stamping sliver** — stamp `review_mode: blocking` + bump
  `schema_version` now (attribution is non-backfillable); advisory *behavior*
  stays deferred. [S]

### 2.4 Triggers that hold up — keep deferred

ADR-58, 60, 63, 64 (gated on Hermes native-Windows GA — an external claim the
author already flagged contested), 66 (operational-load gates guarding real
calibration hazards), 16/35 (felt-need, sound). Deferral discipline
(anti-premature-infra guards) is good. **ADR-34 and ADR-40 — previously deferred
— are now approved for retirement (see §5), not kept on the cadence list.**

### 2.5 Doc-integrity bugs found

- **ADR-65** lists `assumes: [8]` and calls superseded ADR-08 its "base" →
  re-point to **ADR-52** (the superseder; substance unaffected).
- **ADR-61** Related section cites ADR-37 as the find mechanism, but ADR-37 is
  superseded by ADR-48 (capability ships as `catalog-find-source`).
- **ADR-38 / ADR-62** carry stale "waiting for…" text (see 2.1).

---

## 3. Memoria-way researched defaults (turn NEEDS-PI triggers self-determining)

### 3.1 The principle (what the research converged on)

Replace every "when the PI feels it" trigger with: (1) **a count over a log the
vault already writes** (`classify.jsonl`, the dup sweep, `link.py`'s
`recorded_by_name`, audit log, Git author metadata, session logs, the tag/link
graph) so the system surfaces "trigger ready"; (2) **shadow-first calibration** —
run the scorer silently, log, label a sample, pin the threshold in
`calibration.yaml` (corpus- and model-specific, never borrowed); (3) **cheapest
reversible step first**; (4) **propose as an Inbox flag, never auto-apply**
(ADR-56/57). Corollary action: **start the cheap logs now** even while the
feature waits — without them the trigger can never self-detect.

### 3.2 Per item (best-practice number → Memoria-way trigger)

- **ADR-38 — pre-file dedup.** Near-dup cosine **~0.8–0.825**, but corpus-specific
  (optimal cutoffs span 0.33–0.87 across model/dataset — calibrate on your own
  corpus+model; NeMo SemDedup; MDPI 2025, https://www.mdpi.com/2073-431X/14/9/385).
  Duplicate risk follows a power-law that accelerates with size. **Memoria way:**
  mechanism half-exists (peer-reviewer `similarity-check` ~0.8). Trigger = the
  monthly dup sweep catches **born-duplicate pairs in ≥2 of 3 consecutive
  months** (with a ~50-claim pre-filter floor); shadow-log neighbors now,
  calibrate a `similarity_gate:` block in `calibration.yaml`, output a flag never
  a merge. [S–M]
- **ADR-39 — acceptance checklists.** **30–100 labeled examples** to ground a
  rubric; binary beats Likert (Twine; GoDaddy; arXiv 2501.00274). **Memoria way:
  split** — mechanical criteria (citekey present, <250 words, title=claim) ship
  now as a Linter flag (template-derivable); soft criteria gate on **≥30
  PI-blessed exemplars + a recurring quality miss**, then shadow-calibrate a
  binary rubric. Drop the arbitrary "50." [S now / M later]
- **ADR-65 — schema extensions.** Property/schema completeness is a measurable
  defect (Hogan et al., https://arxiv.org/pdf/2003.02320); add relation types
  incrementally with type constraints; MASSW keeps key_idea/method/outcome
  (Zhang et al. 2024, arXiv:2406.06357); search provenance ~87–94% irreproducible
  → PRISMA-S / PROV-O structured capture. **Memoria way** (copies ADR-19
  report-only count + ADR-38 shadow + ADR-56 floor): `similar` → shadow proposer
  now (qmd already in retrieval), adopt when it would be non-sparse on day one
  (≥~30 confirmable pairs, shadow precision ≥~0.7); `_aspects` → shadow-extract
  over `_papers/` now, wire at **~50 papers + ≥0.8 sample accuracy**,
  confidence→flag; exploration traces → capture by default now (engine-written),
  re-exploration detector reuses the qmd threshold. **Doc fix:** `assumes`
  `[8]`→`[52]`. [M / M–L / S–M]
- **ADR-16 — systematic-review tooling.** PRISMA 2020 permits
  single-screening-with-verification (PMC8005925); κ **≥0.6** substantial
  (Landis & Koch); ASReview SAFE stop ~**50–100 consecutive irrelevant**, ~95%
  recall (Syst Rev 2024); RoB 2 / ROBINS-I / GRADE per included study (Cochrane
  Handbook Ch. 8). **Memoria way:** the protocol note's frontmatter is the
  recordable switch — `review_mode: systematic-review` is the master trigger.
  Screening → batch-import ASReview output into `candidate` cards (mostly built
  on ADR-17); PRISMA fields on the protocol note only + a Linter count-reconcile
  check; RoB/GRADE optional fields on in-review papers only (agent proposes,
  human verdicts). **Dual-rater reframed for single-researcher: AI-as-second
  screener with κ computed deterministically** (PRISMA-legitimate). [S–M]
- **ADR-59 — classical displacements.** (1) Learning-to-rank's edge is *features,
  not volume*; works on small sets (~40 *queries* × dozens of judgments;
  softwaredoug LambdaMART). "≥300 decisions" conflates decisions with queries →
  reframe to **≥30 batches × ≥10 judgments, kept-rate 10–90%**, shadow NDCG@10 vs
  heuristic. (5) Keyphrase: KeyBERT ~40–45% F1 (candidate-gen, not decider), YAKE
  ~30× faster — trigger on a **measured miss rate** (human adds a `topic:` the
  classifier missed in ≥20% of last 50), not a 3-month timer; YAKE-first. (6)
  Record linkage: best practice is blocking→matching, deterministic ID-first —
  which `link.py` already implements to best practice (close that sub-item); only
  no-ID Fellegi-Sunter dedup waits, triggered by a **collision counter (≥25
  colliding by-name clusters)**, proposing merges as flags. [logs S / engines M]
- **ADR-35 — meta-memory.** CoALA semantic memory (arXiv 2309.02427); Reflexion
  (flat append-only NL self-critique, 91% vs 80% pass@1, arXiv 2303.11366);
  Generative Agents (reflection needs episodic density). **Memoria way: scope to
  one failure mode** (classifier mis-fires) — trigger = the same
  (signal→wrong-label) override **≥5× across ≥3 projects** in `classify.jsonl`;
  minimal Reflexion-shaped insight in `00-meta/skill-insights/`, surfaced as an
  Inbox card. Recurrence sweep buildable now. [S / M]
- **ADR-63 / ADR-60 — multi-machine / cross-vault.** Single-writer is the
  cheapest correctness guarantee; per-session-file logging (already Memoria's
  pattern) avoids sync conflicts; a VPS is justified only by
  workstation-independence; cross-read gives ~11.4% (AgentRxiv, arXiv 2503.18102)
  but pays off on **concept overlap, not project count** (Matuschak); transclude,
  don't copy. **Memoria way:** retie each trigger to recordable evidence —
  local-mesh on **≥2 machines committing in a 7-day window** (first step:
  `.gitattributes merge=union` + pull-before-push, no Syncthing yet); always-on
  on a **recorded cron miss with sleep already disabled**; cross-project on **≥2
  projects sharing ≥K concept tags** (overlap, dry-run scan first); cross-vault
  on a recordable **"miss → found-in-B"** event (read-only mount first). [S–M / M]

### 3.3 "Start now" instrumentation (each ~S, makes the rest self-detecting)

- triage-decision log (`system/logs/triage.jsonl`) — feeds ADR-59(1), ADR-66
- classify-miss counter over `classify.jsonl` — feeds ADR-59(5), ADR-35
- by-name collision counter over `link.py`'s `recorded_by_name` — feeds ADR-59(6)
- shadow-log on the dup sweep — feeds ADR-38
- `similar` shadow proposer + `_aspects` shadow extraction (read-only) — feeds ADR-65
- cron heartbeat (last-successful-run timestamp) — feeds ADR-63 always-on

---

## 4. Consolidated action list

### 4.1 One `docs/adr/` PR — status fixes + trigger rescopes + doc-integrity

- Retirements (see §5, approved 2026-06-15): ADR-17 → superseded by [50,51];
  ADR-34 → rejected; ADR-40 → rejected.
- Status fixes: ADR-62 split out the built aggregator; ADR-44 reconcile the
  "zero test code" consequence (or finish migration).
- Trigger rescopes (replace eyeball with the §3.2 self-detecting conditions):
  ADR-38, 39, 59 (decouple discovery scorer), 61 (drop VPS dependency), 65,
  16, 35, 60, 63, 74.
- Doc-integrity: ADR-65 `assumes` `[8]`→`[52]`; ADR-61 ADR-37→ADR-48 reference;
  ADR-38/62 stale "waiting for" text.
- Minor: ADR-30 schema enum, ADR-18 alias note, ADR-54 worklist clarification.

### 4.2 Now-implementable (small PRs)

- ADR-76 step-1 tooling `pyproject.toml` + delete conftest `sys.path` block [S]
- ADR-41 stamp `review_mode: blocking` + `schema_version` bump [S]
- ADR-74 static plugin provenance manifest (12 vendored plugins) [S]
- ADR-39 mechanical checklist as a Linter flag [S]
- ADR-59(6) no-ID Fellegi-Sunter dedup proposer once the collision counter trips
- The §3.3 "start now" logs/counters [S each]

### 4.3 Still genuinely needs PI input (live `~/Memoria`, not in the repo)

Even with self-detecting triggers, the eventual calibration needs real-vault
data the repo cannot see: rough claim/hub corpus size; whether a formal
systematic review is active; triage-decision volume + classifier age + any
duplicate entity sightings; whether a second device or ≥3 overlapping projects
exist. The §3 instrumentation is what makes these answerable from logs rather
than memory.

### 4.4 Verify (from §1.3)

ADR-21 overnight-inbox enforcement location; ADR-38's `find-duplicates` sweep
existence.

---

## 5. Retirements — approved 2026-06-15 (execute later; no ADRs edited yet)

Three ADRs are approved to retire. Mechanics + ripple edits captured here so the
eventual `docs/adr/` PR is clean and `gen_adr_index.py` passes (it requires
rejected/superseded ADRs to set `date_resolved`, and superseded to set
`superseded_by`; run `python scripts/gen_adr_index.py` after to refresh the index
table in `docs/adr/README.md`).

### ADR-17 — Shared candidate frontmatter format → superseded

- `status: accepted` → `superseded`; `superseded_by: [50, 51]`;
  `date_resolved: 2026-06-15`.
- Replace the "Accepted / implemented in v0.1" banner with a "Superseded by
  ADR-50/51 — the shipped candidate type is the ADR-51 honesty card" note; drop
  the stale `candidate-note`/`candidate_status`/`source` schema body.
- Bidirectional bookkeeping: add `supersedes: [17]` to ADR-50 and ADR-51
  (both currently `supersedes: []`).
- Ripple: ADR-61 cites ADR-17 as "the shared candidate schema" in prose (~line 31)
  and its Related block (~line 49) → re-point to ADR-51 (+ADR-50).

### ADR-34 — Code-artifact autopilot → rejected

- `status: deferred` → `rejected`; set `date_resolved: 2026-06-15`; keep
  `nav_exclude: true`.
- Rationale to record in the ADR: structurally precluded by ADR-21 (L3 ceiling),
  and any code-lane execution is the #369 "define the code lane" decision — not an
  autopilot. Declined, not parked.
- Ripple: ADR-61 `assumes: [34, 37, 21]` → drop 34 (and 37 is already superseded
  by 48 — re-point to 48); ADR-61 Related block cites ADR-34 → update.

### ADR-40 — Admin/forensic GUI (hermes-workspace) → rejected

- `status: deferred` → `rejected`; set `date_resolved: 2026-06-15`; keep
  `nav_exclude: true`.
- Rationale to record: the forensic need is met by the CLI + dashboards now and
  the (deferred) ADR-58 read-only Inspector later; an external admin GUI would add
  a second un-gated write surface — declined on architecture, not tool maturity.
- Ripple: ADR-58 `assumes: [40, 32]` → drop 40 (ADR-58 must not depend on a
  rejected ADR; its read-only Inspector item stands on its own).

### After editing (validation)

- `python scripts/gen_adr_index.py` to regenerate `docs/adr/README.md`
  (the `adr-index` pre-commit hook enforces freshness).
- Confirm: every retired ADR has `date_resolved`; ADR-17 has `superseded_by`;
  no remaining `assumes:`/prose reference to 17 (→50/51), 34, 40, or superseded 37
  (→48).
