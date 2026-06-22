---
title: Releasing
nav_order: 7
has_children: true
permalink: /releasing/
topic: releases
---

# Releasing

One folder per version, `docs/releasing/<version>/`, holding the **prose** of that cut (scope,
known limitations, documentation/runtime quality bars, close-out procedure, roadmap). Live state
lives in GitHub. The reusable body is [Release plan — vX.Y.Z](release-plan-template.md);
the active draft checkpoint is [v0.1.0-alpha.10](0.1.0-alpha.10/), and the latest
completed checkpoint is [v0.1.0-alpha.9](0.1.0-alpha.9/), with earlier checkpoints
under the same folder. Alpha checkpoints are internal milestones, not formal
releases. The *live readiness state* lives outside the file — see below.

## Where each thing lives (single source of state)

| Thing | Lives in |
|---|---|
| **Scope** (what's in this release) | the GitHub **milestone** `vX.Y` plus the [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1) view filtered to that milestone |
| **Readiness** (gate + validation-stage state) | the parent **"Release vX.Y"** issue and its gate/stage sub-issues |
| **Prose** (scope summary, limitations, cut steps, roadmap) | `docs/releasing/<version>/release-plan-<version>.md` |
| **Build gaps** | GitHub issues |
| **Scope cuts** | GitHub issues with Readiness `Later`; ADRs only when the cut records a decision or durable rationale |
| **Version + notes** | `release-please` (CHANGELOG + tag + GitHub Release) |
| **Automated test evidence** | GitHub Actions runs and artifacts |
| **In-work release design notes** | `docs/releasing/<version>/tmp/` while the release is being designed; delete this folder when the release is done |
| **Close-out evidence worth preserving** | the relevant issue comments, Actions artifacts, or optional `validation-log.md` |

The plan file holds **prose, not state tables**. Gate/stage state is in the release
issue/sub-issues; routine automated evidence is in Actions. Everything else points,
never restates.

## Starting a new release — vX.Y

1. **Folder + plan.** Create `docs/releasing/<version>/README.md` (thin index) and copy
   [Release plan — vX.Y.Z](release-plan-template.md) →
   `docs/releasing/<version>/release-plan-<version>.md`. Fill the prose; set frontmatter
   `status: draft`, `released: false`.
2. **Milestone + Project view = scope.** Create the `vX.Y` milestone
   (`gh api repos/eranroseman/memoria-vault/milestones -f title=vX.Y`) and assign the
   issues that scope it. In [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1),
   use a table filtered to the milestone and sorted by Priority as the live release plan.
3. **Parent issue + sub-issues = readiness.** Open a **"Release vX.Y"** issue
   (label `release`, milestone `vX.Y`). Add one sub-issue per gate/stage (`G#`,
   `S#`) so GitHub shows sub-issue progress and each gate can carry its own evidence,
   owner, and comments. Do not hand-maintain a markdown state table.
4. **In-work design notes** (optional) → `tmp/`. These files are tracked so a branch
   can cite design research while the release is being shaped, but they are not
   published release artifacts. Keep links portable within the repo and delete
   `tmp/` when the release is done.
5. **Overflow** (optional) → `release-plan-<version>-appendix.md`.

## Cutting a release

1. Every gate/stage sub-issue is closed; required CI green on `main`; no open High-priority blocker.
2. **Documentation integrity is complete.** Shipped functionality is covered in
   how-to/reference docs, explanatory context is current, contradiction/completion/duplication
   scans are resolved, Diataxis placement is checked, related links and terminology are
   reviewed, and third-party/example claims are current.
3. **Runtime readiness is complete.** Fresh-clone validation, installer checks, target
   WSL/Linux state, Hermes profiles, local services, and changed Obsidian/plugin behavior
   are verified with evidence in the issue trail, Actions, or `validation-log.md`.
4. **Disposition tracked `tmp/` files.** Implemented scratch is captured in ADRs or system
   documentation; unfinished scratch is moved to the next release `tmp/` or to a GitHub
   issue with the right Readiness; completed-release `tmp/` folders are deleted only
   after that disposition.
5. **Retire-sweep the ADRs.** Delete any ADR whose question this release dissolved or whose
   decision it superseded — keep the *Alternatives considered* memory; leave the number gap.
   See the [retirement criteria](../adr/README.md#when-to-retire-an-adr). (Lands as its own
   small PR before the cut when it is not purely mechanical.)
6. **Formal release:** merge the **release-please** "Release vX.Y" PR — it bumps
   `CHANGELOG.md`, tags `vX.Y`, and publishes the GitHub Release with curated notes
   (fold in the plan's known-limitations). Set the plan frontmatter to `status: released`,
   `released: true`.
7. **Internal checkpoint:** do not cut a tag or GitHub Release. Set the plan frontmatter to
   `status: complete`, `released: false` after the parent issue is closed.
8. Close the milestone and the release parent issue; roll unfinished issues forward.
9. Confirm the release work is committed, merged through PR, the remote branch is deleted, the
   task worktree is removed, and the dedicated main checkout is fast-forwarded with a clean status.

## Standard contents of a `docs/releasing/<version>/` folder

| File | Holds |
|---|---|
| `README.md` | Thin index of this release's files |
| `release-plan-<version>.md` | Prose: scope, gate/stage *definitions*, docs/runtime bars, blockers rule, cut procedure, roadmap |
| `release-plan-<version>-appendix.md` | *(optional)* phase roadmap + investigation detail |
| `validation-log.md` | *(optional)* curated release evidence worth preserving after the GitHub issue/Actions trail |
| `tmp/` | *(temporary)* tracked in-work design notes; remove when the release is done |
