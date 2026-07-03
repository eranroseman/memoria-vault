---
title: Configure project hints
parent: Setup
grand_parent: How-to guides
nav_order: 6
---


# Configure project hints

`project-hints.yaml` gives the ingest classify step a lightweight per-project
topic list so it can **propose** which project a newly ingested paper belongs
to. You confirm or correct that at triage, exactly like every other proposed
field. It is **optional**: with no file, project membership is tagged fully by
hand. This guide creates it from the shipped example and tunes it.

A hint is just a topic list — no weights, no expected-method/design fields. Don't turn it into a scoring matrix ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)).

## Prerequisites

- The starter vault (ships `.memoria/project-hints.yaml.example`)
- The auto-proposal takes effect once the ingest `classify` step runs; the file is editable any time before that

## Steps

**1. Copy the example into place.**

```bash
cp .memoria/project-hints.yaml.example .memoria/project-hints.yaml
```

Copy-on-first-use. An absent `project-hints.yaml` simply means manual project
tagging — nothing breaks without it.

**2. Declare one entry per active project.**

```yaml
projects:
  - id: phd-dissertation
    description: HCI + digital health — JITAI, receptivity, health coaching, equity, LLM mHealth.
    primary_topics: [jitai, receptivity-detection, health-coaching, mhealth, sensemaking, health-equity]
  - id: scoping-review
    description: Scoping review of just-in-time adaptive interventions in mHealth.
    primary_topics: [jitai, mhealth]
```

- `id` — a stable slug; this is the value that lands in a note's `projects` field.
- `description` — a one-line scope, free text. For your reference; not scored.
- `primary_topics` — the topic terms papers in this project tend to carry.

**3. Draw `primary_topics` from the topic signals papers actually carry.**

Prefer terms that appear verbatim in the OpenAlex topics your papers resolve to (use `mhealth`, not `just-in-time-adaptive-interventions`) — at classify time hints are matched against those signals by simple overlap, so a term that never shows up in them contributes nothing ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)). Keep to the ~30-term vocabulary discipline ([Wikilink and link conventions](../../reference/wikilink-and-link-conventions.md#vocabulary-discipline)).

**4. Keep it a hint, not a matrix.**

Do **not** add `expected_study_designs` or `expected_methods` blocks ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)) — study design and method are proposed independently. There are no weights to tune; overlap is the whole mechanism.

**5. Re-tune when classification mis-routes.**

This is the file to edit when the symptom appears: if classify keeps proposing
the wrong project (or none) for papers that clearly belong somewhere, broaden or
narrow that project's `primary_topics` so the overlap reflects how you actually
tag. It's a hint you edit freely — no migration, no schema bump.

## Verify

- `.memoria/project-hints.yaml` exists (not just the `.example`).
- Each project entry has an `id` and a non-empty `primary_topics` list.
- After the next ingest + classify, the note's `_proposed_classification` proposes a `projects` value you can confirm at triage.

## Related

- Where the proposed project is confirmed: [Classify a source](../library/classify-a-source.md)
- Topic vocabulary discipline: [Wikilink and link conventions — Vocabulary discipline](../../reference/wikilink-and-link-conventions.md#vocabulary-discipline)
- The operation posture behind intake: [The Librarian](../../explanation/profiles/librarian.md)
- The ~30-term topic vocabulary discipline: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- The decision and its rationale: [ADR-15](../../adr/15-project-membership-from-topic-hint.md)
