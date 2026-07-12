# Incorporating Karpathy's autoresearch pattern — 2026-07-09

Where and how Memoria adopts the autoresearch loop (agent edits one file →
fixed-budget run → one metric → keep/discard → overnight log; human programs
`program.md`). Companion to `product-statement.md` (axioms, roadmap) and
`promise-audit.md` (findings referenced below).

## Why the pattern is axiom-native

Autoresearch's epistemology is Memoria's axioms applied to code: the loop
never asks "is this change good?" (a judgment), only "what did the metric
do?" (a grounded consequence) — and keep/discard is origin-neutral: nobody
cares that an LLM wrote the diff. The authority split matches too: human
programs the program (judgment at org level), agent edits the artifact
(execution), metric disposes (mechanical). The pattern transfers only where
a cheap, deterministic, Goodhart-resistant scalar exists. Memoria has
exactly two such places, both already built.

## The mapping

| autoresearch | Memoria counterpart | Status |
|---|---|---|
| `prepare.py` (fixed harness) | Seeded sandbox vault + `seeded_errors.py` battery + `eval_score.py` + frozen bars | Built |
| `train.py` (single mutable file) | One bounded module: lint detectors / tier-1 claim comparator / gap-severity scoring / dedup thresholds | Built; needs extraction into one file |
| `val_bpb` (single metric) | Seeded-error recall at fixed FPR (frozen bars as no-regression constraints); or `eval_score` support_rate | Built ("no fake scores") |
| 5-minute budget | One battery run on a fixed seeded vault (~minutes; comparable across experiments) | Built |
| `program.md` | Human-edited org file, e.g. `experiments/program.md` — the instrument-research analog of `steering.md` | Missing (small) |
| The overnight loop | Nothing — `eval_dispatch` is a stub, no scheduler ships (promise-audit finding) | Missing |

## Incorporation points, in order

1. **Instrument autoresearch (first — everything exists except the loop).**
   Mutable artifact: the deterministic instrument layer (detectors, tier-1
   lexical-NLI stand-in, gap scoring, dedup thresholds), extracted into one
   reviewable module. Harness: the seeded-error battery on a disposable
   sandbox vault, run in a fresh worktree per experiment. Keep if the
   scalar improves and no frozen bar regresses; discard otherwise; log
   every experiment. Kept diffs still land via verify + PR — Karpathy
   disables permissions; Memoria doesn't need to, because worktree +
   sandbox + ruleset are the permission model. This is also the honest
   upgrade path for the tier-1 NLI stand-in: the overnight org grinds on
   it instead of a someday hand-replacement.
2. **Prompt autoresearch (needs gold tasks).** Fill the `eval_dispatch`
   stub minimally: ship a small gold-task set harvested from real vault
   use. Mutable artifact: one operation's prompt manifest (digest
   compilation or red-team-argument; `prompt_version` bump = experiment).
   Metric: `eval_score` support_rate / recall@k. Directly raises co-PI
   quality per experiment.
3. **Nightly cadence — sibling, not autoresearch** (now Tier C of the
   reactive substrate, roadmap item 12). Fixed-budget overnight
   runs of the proposal backlog (gap analysis, surface-tensions,
   undigested-source digestion) with a morning log solve the "nothing
   initiates" finding — but the disposer is the PI at the inbox, not a
   metric. Content has no `val_bpb`; that is the axiom line.

## What not to do

- **No metric-driven optimization of vault content** — Goodhart applied to
  one's own knowledge, and a violation of judgment ownership. The loop
  optimizes the instrument that assesses grounding, never the knowledge
  being assessed.
- **No autoresearch on the dev harness/process** — no cheap scalar exists;
  forcing one optimizes noise.

## Roadmap placement

An accelerator for the instrument layer, not a substitute for the design
decisions ahead of it: the warrant ontology and structural_impact wiring
(product-statement roadmap items) are design/wiring work with no metric to
optimize. Once wired, their heuristics (impact scoring, argument-health
thresholds) join the mutable surface of point 1. Point 1 itself is a
well-shaped superpowers feature: brainstorm → spec (mostly the extraction
of the tunable surface into one file — the "single file to modify" rule) →
SDD; the loop driver is ~50 lines or none (agent + program.md suffices).
