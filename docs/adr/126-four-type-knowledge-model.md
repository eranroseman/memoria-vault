---
topic: decisions
id: 126
title: Four concept types, meaning-only frontmatter, hub-owns-tag, project layer
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [125]
supersedes: [14, 15, 19, 47, 50, 52, 71, 77, 78, 79, 83, 100, 117, 119]
superseded_by: []
---

<!-- cspell:words flippable journaled -->

# ADR-126: Four concept types, meaning-only frontmatter, hub-owns-tag, project layer

Consolidation ADR (see ADR-125 preamble). This is the knowledge model; it
replaces the accreted type zoo (12+ types across three bundles) with four
types and relocations, and moves every verdict out of the files.

## Context

The type roster grew by accretion (47, 50, 78, 117, 119): claim, question,
excerpt, synthesis, thesis, steering, vocabulary, asset, digest, fleeting —
each with folder homes, lifecycle fields, and per-type rules. The multiplicity
itself caused drift and confusion. Meanwhile `check_status` lived in
frontmatter, so checking a note rewrote it, hand-edits forged status, and
every consumer had to distrust the file it was reading.

## Decision

**Four knowledge concept types** — the discriminator is "a fundamentally
different artifact"; a different check regime that is a flippable state is a
*mode*, and one on a different layer is not a knowledge type:

- `note` — one atomic thought; optional `mode: claim | question` — a mode is
  **declared intent creating obligations the gap engine feeds on** (a claim
  without evidence is an `under-warranted` gap; an open question is a
  compose-flow lead — field-derived typing could not tell a plain thought from
  a claim missing its evidence). Modes flip
  on the same id via a journaled change; a `question` carries
  `question_status: open | resolved`, orthogonal to checked/unchecked; a
  `claim` carries warrant obligations plus claim-context fields
  `temporal_scope`/`tense`/`qualifier`).
- `work` — a source's subjective digest + tags, 1:1 with the catalog work
  (`work_id`); the objective record stays in SQLite (ADR-124/125).
- `hub` — a topic's authored home; **owns exactly one ID-backed
  controlled-vocabulary tag; membership is everywhere that checked tag
  appears**. Curation lives in the hub's prose (ordering, featuring), never in
  membership filtering — this answers ADR-19's recorded hazard ("a generated
  list that looks curated") by splitting membership (mechanical, inclusive)
  from salience (human, curated). Only checked tags confer membership.
- `project` — the compose-flow working frame: a nested, detachable sub-bundle
  with **one-way project→corpus references**, `outcome_frame`/`paper_plan`,
  a thesis-**role** link to a central note, gap/saturation analysis, and
  deliverable targets (`outline`/`section`/`figure`/`code` — **artifacts, not
  Concepts**: a Concept is what participates in the checked knowledge graph;
  outline/section are export-gate-validated files, figure/code are
  manifest+blobs, gaps/saturation are DB projections). This absorbs 77
  (project gate), 79 (the argument graph, `warrant`, and the saturation floor —
  ≥1 addressed support AND ≥1 counterpoint — now the gap engine's saturation
  block, ADR-129), and 78 — thesis is a role, not a type; 78's protections
  survive as checks (no note is born thesis-designated-and-checked; a falsified
  thesis is a preserved result via the refuting subgraph). Agent-proposed
  project membership (15) returns as project-side candidates through attention.

**Relocations, not types**: excerpt → a W3C TextQuoteSelector `anchor` on a
note/work; index → generated views; fleeting → an unchecked note; steering →
the `instructions` user config; synthesis → hub prose or the work digest; asset → a same-stem
content-addressed attachment on a note/work; reminders → GFM task markers;
exploration traces (100) → project working notes, never auto-promoted.

**Meaning-only frontmatter** (supersedes 50's lifecycle-in-frontmatter and
119's generated-form targets while keeping 119's principle — the schema is the
single declarative contract, now pydantic in product code): ULID `id`
(identity ≠ filename ≠ title), `type`, `title`, `tags`, typed
`links: [{rel, to, why?}]`, `aliases`, optional `archived: true`, plus
per-type fields. **No verdict or derived field is ever written to a file**;
`check_status`, materialization, and derived signals are DB-only. Supersession
is a `superseded-by` typed link plus DB composition; a superseded or retracted
item is never presented as current but stays first-class retrievable, tagged.
ADR-52's distinction is carried verbatim: authored `links:` are the human/
argument layer in frontmatter; given `relationships` are engine-built records
in the DB. ADR-117's naming rule (singular noun, kind-scoped, no collisions)
is carried and applied to the four types; its 26-type roster validation is
superseded.

**Creation surfaces**: schema-driven scaffolds replace form plugins (71);
`new note|hub|project` authors, `work add` registers; `vocab` mints and
manages tag IDs. Deliverable export is terminal and frozen (14's principle
carried into `project export`).

## Consequences

- Adding a type later adds zero commands and one schema.
- Files never churn on checking; the content hash is the file.
- The template, validators, read-API projections, and scan/rebuild are
  rewritten to this model (exec-plan PR-B2), with the alpha.14 surface
  retirement enforced by a negative gate.

## Alternatives considered

- **Keep claim/question/thesis as types** — rejected: flippable states and
  roles, not artifacts; separate types make the question→claim transition
  destructive.
- **Frontmatter `check_status` as a generated-but-ignored projection** —
  rejected: hash churn plus a forged-status foot-gun; meaning-only is stronger.
- **Hand-curated hub membership** — rejected: it rots (every relevant new note
  requires a hub edit); the owned checked tag is maintained at write time.

## Related

- Design §3/§4/§5/§10; ADR-125; ADR-127 (who may set verdicts); ADR-129
  (edge extraction and the supersession comparator).
