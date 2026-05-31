---
topic: reference
---

# Controlled-vocabulary example (HCI + digital health)

> **This is one worked example, not a Memoria default.** [frontmatter-schema.md](frontmatter-schema.md#controlled-vocabularies)
> deliberately leaves `study_design`, `methods`, and `topic` **open** — they are absent from
> its controlled-vocabularies table, so you define them as your research evolves. This page
> exists only so a user who doesn't want to invent a taxonomy from a blank page has a concrete
> starting point. **Copy what fits, edit freely, delete the rest.** Nothing here is enforced.

Keep a working `topic` list to ~30 terms — a smaller vocabulary produces more consistent
classification. Richer taxonomy (MeSH, ACM CCS, OpenAlex concepts) belongs in `_enrichment`
(auto-populated from APIs), not in this hand-curated list.

## `topic` (example — ~30 terms)

```yaml
topic_vocabulary:
  # Intervention design
  - jitai                     # Just-in-Time Adaptive Interventions
  - ema-experience-sampling   # Ecological momentary assessment / experience sampling
  - receptivity-detection     # Optimal-moment detection for delivery
  - behavior-change           # Behavior change theory and mechanisms
  - implementation-science    # CFIR, implementation strategies
  # Health domains
  - self-management           # Chronic condition self-management
  - health-coaching           # Professional / digital health coaching
  - motivational-interviewing
  - mental-health-wellbeing
  - chronic-disease
  - mhealth                   # Mobile health; app-based interventions
  # Research methods (conceptual)
  - hci-methods               # Think-aloud, contextual inquiry, diary study
  - design-science
  - causal-inference
  - qualitative-methods
  # Systems and technology
  - conversational-agents
  - wearables-sensors
  - digital-phenotyping
  - ubicomp
  - llm-ai-health
  # Knowledge and equity
  - sensemaking
  - health-equity
  - health-informatics
  - patient-provider
```

## `study_design` (example — one value per note, most specific that applies)

```yaml
study_design_vocabulary:
  - RCT
  - controlled-experiment
  - quasi-experimental
  - observational
  - systematic-review
  - meta-analysis
  - qualitative
  - mixed-methods
  - design-science
  - technical          # algorithm/model/benchmark — no human participants
  - theoretical        # framework / conceptual / position paper
  - secondary-analysis
```

## `methods` (example — list-valued)

```yaml
methods_vocabulary:
  # Data collection
  - semi-structured-interview
  - survey
  - diary-study
  - ema-probe
  - log-analysis
  - biometric-sensing
  - think-aloud
  # Analysis
  - thematic-analysis
  - grounded-theory
  - content-analysis
  - statistical-modelling
  - machine-learning
  - nlp-text-analysis
  - causal-dag
  # Design and evaluation
  - participatory-design
  - usability-testing
  - field-deployment
  - wizard-of-oz
  - ab-test
```

## Refinement vocabularies (these *are* Memoria conventions, not just examples)

Unlike the three open fields above, `maturity` and MOC `scope` are fixed in
[frontmatter-schema.md](frontmatter-schema.md#controlled-vocabularies) — repeated here for convenience:

```yaml
maturity_vocabulary:       # on claim-note
  - seedling   # single source idea; not yet cross-referenced
  - budding    # developed across sources; linked in ≥1 MOC
  - evergreen  # stable, well-linked; ready to promote to reference

moc_scope_vocabulary:      # on moc
  - topic    # conceptual cluster
  - domain   # broad research area
  - project  # per-project synthesis hub
  - child    # narrower MOC nested under a parent
```

## How to use this

1. Copy the three open vocabularies into wherever you keep classification hints (or into a comment
   in your vault's `00-meta/04-reference/schema-reference.md`).
2. Cut every term that doesn't match your field; rename the rest.
3. Let the Librarian propose from your edited list at classify time; promote at triage.
4. Consolidate as the corpus grows — free-tag first, tighten the list around ~50 papers.

**Related:** [frontmatter-schema.md](frontmatter-schema.md) (the open-by-design choice this example
serves, and the controlled vocabularies it does not), [note-types.md](note-types.md), and — for
per-project topic hints that drive `projects` proposals — [ADR-30](../project/decisions/30-project-auto-classification.md).
