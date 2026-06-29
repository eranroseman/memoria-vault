# Classification (`_proposed_classification`) — automated, audited metadata

The classification step runs on every new source, so it is built to be cheap and
correctable rather than clever: it reuses the OpenAlex **topics already in the enrichment
payload** (no extra network call) and audits every decision. Classification is **not a gate**
(D16 / D21 / ADR-54) — the values land in the note's `_proposed_classification` block; the
human-owned main fields stay empty until PI direction accepts or edits them.

## How a value is chosen

1. **`research_area` — from the enrichment topics.** The clear-winning OpenAlex topic in the
   merged enrichment payload becomes the `research_area` proposal. Values are constrained to
   `system/vocabulary.md`.
2. **`methodology` — from the S2 publication types (when derivable).** A conservative,
   deterministic map turns Semantic Scholar `publicationTypes` into a methodology facet:
   `review → review`, `metaanalysis → meta-analysis`, `clinicaltrial → clinical-trial`,
   `casereport → case-report`, `dataset → dataset`. Venue-ish types (JournalArticle, Editorial,
   News, …) are *not* a methodology and stay unmapped.
3. **Project membership (ADR-15, optional).** When `.memoria/project-hints.yaml` exists, the
   step also proposes project membership by topic overlap into
   `_proposed_classification.projects` — for human confirmation at triage, never written
   straight to the `projects` field. No hints file = fully manual project tagging (silent no-op).

## The decision doctrine

- **Clear winner** → apply the proposal silently.
- **Near-tie or below the calibration floor** → leave the field unset and raise **one** Inbox
  `flag` card (honesty rules: what was ambiguous plus the top candidates with their scores —
  never a verdict).
- **Enrichment off / no topic data** → no-op.

Thresholds live in `.memoria/schemas/calibration.yaml` under `classify:` (`confidence_floor`,
default `0.60`; `near_tie_margin`, default `0.15`), mirroring `entity_resolution` (ADR-56).
Every applied or flagged decision appends one line to `system/logs/classify.jsonl` — the audit
trail that makes the automation correctable.

## What this is *not*

There is **no trained classifier, no softmax probability, no LLM fallback, and no retraining
loop**, and **no confidence threshold above which the main fields are filled automatically** —
that "classification-confidence" auto-accept is a deliberately dropped anti-pattern (see the
sibling `catalog-classify-source` skill, Honesty rules). Calibrated topic scores *propose*; the
human *promotes*. The `research_area` and `methodology` values in `_proposed_classification` are
always a proposal, never canonical.
