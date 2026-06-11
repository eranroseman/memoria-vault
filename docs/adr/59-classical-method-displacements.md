---
topic: decisions
id: 59
title: Classical method displacements over LLM calls
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [9, 30]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 59
---

# ADR-59: Classical method displacements over LLM calls

## Context

Several tasks are currently routed to an LLM where a classical (deterministic or hybrid) method does the job better — cheaper, faster, reproducible, and auditable. The governing principle (see [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md)) is to **use the simplest tool that produces a reliable answer**: scripts beat NLP beat ML beat LLMs on cost, speed, determinism, and auditability, and the LLM enters only where residual judgment genuinely requires generation. This ADR catalogues the candidate displacements as a single deferred decision; each item carries its own raise-priority condition for the cadence review.

## Decision

Memoria treats the following as the approved direction for displacing LLM calls with classical methods, to be scheduled per-item when its conditions hold:

- **Learning-to-rank for triage.** A learning-to-rank model (e.g., LightGBM LambdaRank) trained on the human's past keep/discard decisions produces a reproducible, personalized triage ordering that sharpens as override history grows — replacing or cold-start-gating the LLM tournament in the triage queue. The scalar ordering or the LLM tournament remains the cold start until enough history exists.
- **Claim-sentence classification.** A rhetorical-zone classifier (CoreSC/ART-style, or citation + hedge + numeric heuristics) locates claim/aspect sentences before the LLM, reducing input from full-paper to candidate sentences — lowering cost, improving precision, and enabling agent-proposed candidate claim notes.
- **Classical prose metrics for the export gate.** Mechanical checks — Flesch–Kincaid readability, passive-voice ratio, citation density, n-gram repetition, sentence-length outliers — run before the LLM-judge gate fires at export, flagging symptoms cheaply while the LLM still owns coherence and tonal drift. This converts the export gate from pure-generative to hybrid.
- **Discovery relevance scoring.** The existing `[!suggestions]` weighted scorer (embedding similarity + citation-graph overlap + topic-tag overlap against `research-focus.md`) ranks nightly discovery candidates deterministically and auditably, with no extra API calls.
- **Keyphrase extraction for tag candidates.** KeyBERT or YAKE extracts candidate tags alongside the existing classifier, mapping extracted phrases onto the human's controlled vocabulary to improve recall on tags the classifier missed.
- **Record linkage for entity deduplication.** ORCID/OpenAlex IDs first, then string-similarity blocking, deduplicate author and venue entities during Librarian ingest instead of asking the LLM whether two entries refer to the same person.

The **NLI-based contradiction proposer** is *not* re-decided here: it is already deferred in [ADR-09](09-contradictions-dashboard.md) as the deterministic candidate-generation engine that populates the contradictions dashboard's v2.

## Consequences

- Each displacement reduces cost and adds determinism, reproducibility, and auditability on a task currently owned by an LLM.
- Several items depend on accumulated history (triage decisions, classifier training, override data); building before that history exists yields a generic or under-trained model — hence the per-item conditions.
- Partial or premature adoption can be worse than none (e.g., a low-confidence NLI false-merge, an under-trained ranker); the conditions guard against that.
- No new subsystems are mandated — most items reuse machinery already present (the `[!suggestions]` scorer, the existing tag classifier, the ingest pipeline).

## When this matters

Per-item conditions that raise priority at the cadence review:

- **Learning-to-rank triage** — the human has made ≥ 300 triage decisions and notices the triage queue ordering feels generic or unconditional on their research priorities.
- **Claim-sentence classification** — agent-proposed candidate claim notes are being piloted *and* the LLM's false-positive rate on non-claim sentences is producing meaningless candidates.
- **Classical prose metrics** — the LLM-judge export gate is live and recurring false alarms on structural issues are dominating the report.
- **Discovery relevance scoring** — the discovery loop is live and morning triage time exceeds 15 minutes because candidates aren't pre-sorted by relevance.
- **Keyphrase extraction** — the classifier has been active ≥ 3 months and the human notices recurrent vocabulary gaps (terms that should appear in `topic:` but don't because the training set didn't see them).
- **Record linkage** — entity notes accumulate duplicate person or venue entries the human notices while cleaning up the graph.

## Related

- **Related decisions / Depends on:** [ADR-09 contradictions dashboard](09-contradictions-dashboard.md) (owns the deferred NLI contradiction proposer); [ADR-30 deterministic ingest pipeline](30-deterministic-ingest-pipeline.md) (the deterministic discipline these displacements extend).
- **Source discussion:** [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).
- **Tracking issue:** [#409](https://github.com/eranroseman/memoria-vault/issues/409) — revisit at each release cadence.
