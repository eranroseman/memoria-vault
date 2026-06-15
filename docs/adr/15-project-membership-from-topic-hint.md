---
topic: decisions
id: 15
title: Project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed
status: accepted
date_proposed: 2026-05-30
date_resolved: 2026-05-30
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 15
---

# ADR-15: project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed

> **Implementation status: built** ([#425](https://github.com/eranroseman/memoria-vault/issues/425)). The classify stage (`classify.py`, wired in `runner.py`) loads the optional `.memoria/project-hints.yaml` and scores each project's `primary_topics` against the paper's OpenAlex topic signals (topic names + subfields, kebab-case normalized; a hint matches a signal when equal or when all the hint's tokens appear in it). The ADR left the proposal rule open, so the implementation picked a conservative one: **every project with ≥ 1 overlapping hint topic is proposed, ranked by overlap count** — safe because it is a proposal the human confirms at triage, never an auto-apply. The proposal lands in `_proposed_classification.projects`; each decision (proposed or no-match) appends one `stage: project_hints` line to `system/logs/classify.jsonl` with the candidates and overlap counts (ADR-51 honesty — counts, not confidence). An absent hints file is a silent no-op (fully manual); a malformed one warns once on stderr and degrades to manual.

## Context

The predecessor vault defined **corpus profiles** — one per research project, each declaring
`expected_study_designs`, `expected_methods`, and `primary_topics`. At ingest the Librarian
scored a paper's abstract against every profile and proposed a `projects` value inside the
classification block, which the human corrected at triage.

In the current design the classification block survives (renamed `_proposed_classification`),
**but its project-scoring input is gone**: the starter vault ships no corpus profiles and no
`expected_*` matrices. So the Librarian can propose `study_design` / `methods` / `topic`, but
the structured signal that let it propose **project membership** specifically was dropped in the
redesign — leaving project assignment either fully manual or driven by an undocumented heuristic.
This ADR resolves which.

Two design forces pull against each other:

- The corpus-profile *scoring matrix* (`expected_study_designs` + `expected_methods` per project)
  is exactly the kind of human-maintained config that **drifts** — the redesign shed similar
  weight elsewhere, and [Frontmatter fields](../reference/frontmatter.md#the-field-kind-grammar)
  deliberately leaves `study_design` / `methods` / `topic` open rather than controlled.
- But "which of my projects does this paper belong to?" is a real, repetitive judgment the agent
  *can* usefully **propose** — losing it entirely pushes pure manual tagging onto the human.

## Decision

**Restore the minimal version, not the matrix.** Add an optional, lightweight per-project hint —
just `primary_topics` (and a free-text `description`) per project — that the Librarian scores by
**topic overlap** to **propose** a `projects` value in `_proposed_classification`. The human
confirms or corrects project membership at triage, exactly as for the other proposed fields.

Explicitly **do not** restore `expected_study_designs` / `expected_methods` scoring — design and
method are already proposed independently, and a per-project expectation matrix is drift-prone
config for marginal gain. A project hint is a *hint*, not a controlled vocabulary, so it does not
reopen the open-by-design choice for `study_design` / `methods` / `topic`.

```yaml
# .memoria/project-hints.yaml  (optional; absent = project membership is fully manual)
# The starter vault ships project-hints.yaml.example — copy to project-hints.yaml and edit.
projects:
  - id: phd-dissertation
    description: HCI + digital health — JITAI, receptivity, health coaching, equity, LLM mHealth.
    primary_topics: [jitai, receptivity-detection, health-coaching, mhealth, sensemaking, health-equity]
  - id: scoping-review
    description: Scoping review (replace with actual topic).
    primary_topics: [jitai, mhealth]
```

## Consequences

- The one capability genuinely lost in the redesign (agent-proposed project membership) is back,
  at minimal config cost — a short topic list per project, not a scoring matrix.
- "Agent proposes, human decides" holds: the `projects` proposal lands in
  `_proposed_classification` and is human-confirmed at triage like every other field.
- No new controlled vocabulary and no drift-prone expectation matrix — `primary_topics` is a hint
  the human edits freely; an absent `project-hints.yaml` simply means manual project tagging.
- The Librarian's classify step needs a small addition: score candidate `topic` values against
  each project's `primary_topics`, propose the best-overlap project(s). This lands with the
  Librarian's classify implementation, not before.

## Alternatives considered

**Restore the full corpus-profile matrix** (`expected_study_designs` + `expected_methods` +
`primary_topics`). Rejected: drift-prone human-maintained config for marginal benefit over topic
overlap; design/method are already proposed separately.

**Declare project assignment human-only; document the gap.** Defensible and zero-config, but
discards a genuinely useful, low-risk proposal the agent can make — it pushes repetitive tagging
fully onto the human for no architectural gain.

**Infer projects implicitly from topic without any hint file.** Rejected: an undocumented
heuristic is exactly the ambiguity this ADR exists to remove; the hint file makes the signal
explicit and auditable.

## Related

- **Source:** the predecessor vault's corpus-profiles mechanism (internal salvage analysis).
- **Profile:** [Librarian](../explanation/profiles/librarian.md) — owns classify / `_proposed_classification`.
- **Schema:** [Frontmatter fields](../reference/frontmatter.md) (`projects`, `_proposed_classification`).
- **Respects:** the open-by-design choice for `study_design` / `methods` / `topic` — see [frontmatter.md controlled vocabularies](../reference/frontmatter.md#the-field-kind-grammar); a project hint is not a controlled vocabulary.
