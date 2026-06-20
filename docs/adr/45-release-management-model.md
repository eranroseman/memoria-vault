---
topic: decisions
id: 45
title: Release management — gates as a tracking-issue checklist, release-please for versioning
status: accepted
date_proposed: 2026-06-08
date_resolved: 2026-06-08
assumes: [29]
supersedes: []
superseded_by: []
---

# ADR-45: Release management — gates as a tracking-issue checklist, release-please for versioning

## Context

Releases were managed with a **self-contained plan file** per version: one
`release-plan-vX.Y.md` carrying a frontmatter `released:` flag, hand-maintained §2
Gate (`G1–G11`) and §3 Stage (`S0–S5`) state tables, scope, cut procedure, and roadmap,
plus sibling run records — scope in the GitHub milestone, notes in `CHANGELOG.md`, and a
`v*` tag triggering `release.yml`. It was git-tracked, reviewable in PRs, self-contained,
and offline-capable. But it hurt in three observed ways: the hand-maintained markdown
state tables **drifted** (the template itself wished for a future `status-doctor` check;
the `/release` skill and the v0.1 plan accumulated stale path/term references); there was
**no live status surface** (you read a file to know where a release stood); and it took
~8 files per release with two places to keep aligned (plan gates ↔ milestone/issues).

## Decision

Adopt a **tiered, additive** model — stop anywhere, escalate later without rework. **Tier
1 (fix the drift + add `status-doctor`) and Tier 2 are adopted; Tier 3 is deferred.**

- **Readiness state** lives in the **"Release vX.Y" tracking issue** — a gate checklist
  GitHub renders as a progress bar — retiring the hand-maintained §2/§3 markdown tables
  (the main drift source). *(Tracking shape amended by
  [ADR-75: Use GitHub Project fields and release sub-issues for live work
  state](75-github-project-fields-and-release-sub-issues.md): the single-checklist
  tracking issue is replaced by a parent issue plus one sub-issue per gate; the
  milestone-for-scope and release-please-for-versioning decisions here stand.)*
- **Scope** is the GitHub **milestone** (`vX.Y`).
- **Version + CHANGELOG + GitHub Release** are owned by **release-please** (manifest mode)
  from Conventional Commits, replacing the tag-only `release.yml`. Don't hand-edit
  `CHANGELOG.md` or tag by hand.
- **Prose** (scope summary, cut procedure, known-limitations) stays in
  `docs/releasing/<version>/`, guarded by `status-doctor` against link/path/flag drift.
- The in-flight **alpha.1** plan keeps its §2/§3 tables as the at-cut record (with a pointer
  to its tracking issue); **alpha.2+** uses the checklist model from the start.

The live process this produced is documented in [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md) and
scaffolded by the `/release` skill.

## Consequences

- Live status for free (progress bar + milestone %); the hand-table drift source is gone.
- The record **splits**: prose in git, gate/stage state in GitHub — offline gate-state
  visibility is lost (an accepted trade at solo cadence).
- release-please is opinionated and now owns versioning/notes; merging its "Release vX.Y"
  PR cuts the tag. (Operational caveat: its PR needs Actions PR-review permission / a
  scoped `RELEASE_PLEASE_TOKEN` — tracked separately.)
- The release **cut** now includes an ADR retire-sweep (see [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md)).

## Alternatives considered

The gate/stage *vocabulary* comes from the layered testing framework ([ADR-29](29-testing-framework.md));
this decision is only about *where release state and versioning live*.

- **Stay file-folders + add `status-doctor`** (Tier 1 alone). Lowest effort, kills the
  drift, stays in git — but adds no live surface and the gate state stays hand-edited
  markdown. Kept as the floor; Tier 2 is layered on top.
- **GitHub-native gates** (chosen, Tier 2). Gates as a tracking-issue checklist + milestone
  for scope: live status for free, no markdown state tables. Cost: state leaves git
  (GitHub-only), offline visibility lost — acceptable for one operator.
- **VS Code GitHub extension.** Rejected as the system of record — it's a viewer/UI over
  whichever model you pick, never the model itself.
- **release-please** (chosen for the notes/versioning half). Automates version + CHANGELOG +
  Release PR; opinionated, replaces `release.yml`. It automates only versioning/notes, **not
  readiness** — which is why it pairs with the tracking-issue gates rather than replacing them.
- **Tier 3 — Projects "Release" view + `scripts/release.sh` cut script.** Deferred: richest
  dashboard and a one-command cut, but the Projects field/view config isn't in git, it's the
  most moving parts, and the dashboard is marginal at solo cadence. Revisit if cadence rises;
  the cut **script** (the higher-value half) can be pulled in standalone.

## Related

- **Live process:** [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md); the `/release` skill scaffolds it.
- **Gate/stage model:** [ADR-29](29-testing-framework.md) (the layers/matrix the gates map to).
- **Amended by:** [ADR-75: Use GitHub Project fields and release sub-issues for live
  work state](75-github-project-fields-and-release-sub-issues.md) — replaces the
  single-checklist tracking shape with a parent issue plus one sub-issue per gate.
