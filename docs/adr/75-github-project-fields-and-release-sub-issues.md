---
topic: decisions
id: 75
title: Use GitHub Project fields and release sub-issues for live work state
nav_exclude: true
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [45]
supersedes: []
superseded_by: []
---

# ADR-75: Use GitHub Project fields and release sub-issues for live work state

## Context

[ADR-45](45-release-management-model.md) moved release readiness out of
hand-maintained markdown tables and into GitHub. The first shape used a single
"Release vX.Y" tracking issue as a gate checklist. That removed file drift, but it
made each gate a checkbox rather than a work item with its own owner, comments,
evidence, blocking discussion, and Project metadata. In parallel, labels had started
to carry too many meanings: type, area, priority, triage state, and bot automation.
That made issue search noisy and made release planning depend on conventions that
GitHub Projects models more directly.

## Decision

Memoria uses GitHub issues as the atomic unit of work, the **Memoria Issue Tracker**
Project as the live planning surface, milestones as release scope, and ADRs as the
decision record. Project fields carry `Status`, `Area`, `Type`, and `Priority`;
labels stay minimal and are reserved for repo-wide search chips or bot automation.
Release readiness lives in a **"Release vX.Y" parent issue** with one sub-issue per
gate or validation stage, instead of a single checklist embedded in the release
plan or parent issue body.

> **Current field set (see [Issue tracking](../contributing/issue-tracking.md)):**
> the live Project carries `Status` and `Readiness` only. The original `Area`, `Type`,
> and `Priority` fields were retired as unused planning overhead, and `Readiness` was
> added to separate "is it decided" from "is it ready to build." The decision to model
> planning state in Project fields — not labels or markdown — is unchanged.

## Consequences

- Each release gate/stage can have its own evidence trail, assignee, comments, and
  close condition.
- The Project table becomes the source for triage, priority, and release views;
  process docs point to it instead of copying its state.
- Labels are simpler and less likely to conflict with Project fields or automation.
- Some live state remains GitHub-only. That is acceptable for planning metadata, while
  durable rationale still belongs in ADRs and durable process prose remains in `docs/`.
- GitHub Project field configuration is not versioned in this repository, so
  `docs/contributing/issue-tracking.md` documents the expected field vocabulary and
  colors for human repair.

## Alternatives considered

**Keep the single release tracking issue checklist.** Rejected as too flat: it shows
progress, but it does not give each gate a first-class place for evidence, ownership,
or blocked discussion.

**Use labels for Type, Area, Status, and Priority.** Rejected because labels are global
repo search metadata and bot hooks, not a planning schema. Project fields model this
more directly and avoid a large label taxonomy.

**Track planning state in markdown under `docs/`.** Rejected for live state because it
reintroduces the drift class ADR-45 removed. Markdown remains the home for durable
process and decision prose, not the live board.

## Related

- **Workflows affected:** [Issue tracking](../contributing/issue-tracking.md),
  [Releasing](../releasing/README.md)
- **Related decisions / Depends on:** [ADR-45](45-release-management-model.md)
