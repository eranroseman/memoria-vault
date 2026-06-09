---
topic: decisions
id: 04
title: Folders encode lifecycle stage, not subject area
status: accepted
date_proposed: 2026-05-01
date_resolved: 2026-05-01
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 4
---

# ADR-04: Folders encode lifecycle stage, not subject area

## Context

The vault needs an organizing principle for its folder structure. The obvious choice is subject area — put all cognitive science notes in `cognitive-science/`. The alternative is lifecycle stage — put all sources in `20-sources/`, all synthesis in `30-synthesis/`, regardless of topic.

## Decision

Top-level vault folders encode **lifecycle stage**, not subject area. A paper about attention lives in `20-sources/01-papers/`, not `cognitive-science/`. Topics live in frontmatter (`topic:`, `methods:`, `domain:`). The folder says "what this note is"; frontmatter says "what it's about."

The one exception is `40-workbench/`: its unit is the **project** (a bounded transient effort), not the lifecycle stage. Within a project folder, artifacts are organized by sub-stage (`01-map/`, `02-framing/`, etc.).

## Why

Topic folders fail because topics are many-to-many: a paper on attention and working memory belongs in `cognitive-science/` and `neuroscience/` and `HCI/`. Either you duplicate the note (it immediately diverges), pick one folder arbitrarily (you lose the other connections), or accept that the folder adds no information (so why have it?).

Lifecycle stage is one-to-one: a note is at exactly one stage. This makes the folder load-bearing — it tells the agent and the human what kind of thing a note is, not what it's about. Agent permissions align with stages (`Librarian` writes to `20-sources/`, never to `30-synthesis/`). Queries separate cleanly: "what notes are in the inbox?" uses the folder; "what notes are about attention?" uses frontmatter.

## Consequences

- Six numbered top-level folders: `00-meta/`, `10-inbox/`, `20-sources/`, `30-synthesis/`, `40-workbench/`, `50-deliverables/`.
- Topics, methods, domains belong in YAML frontmatter, not folder paths.
- The Linter validates that notes are in their correct lifecycle folder; a `claim-note` in the inbox or a `paper-note` in synthesis is a structural error.
- Navigation by topic is via Maps of Content (MOCs) in `30-synthesis/03-moc/`, not folder hierarchy.

## Alternatives considered

**Topic folders** — many-to-many problem produces duplication or meaningless catch-alls; agent permissions become ambiguous (the agent's permission must span all topic folders, which is the same as "all paths").

**Hybrid (topic + stage)** — adds complexity with no benefit; the topic dimension belongs in frontmatter where it can be queried correctly.
