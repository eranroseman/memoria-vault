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
lives in GitHub. The reusable body is the [release plan template](release-plan-template.md);
the active draft checkpoint is
[Release plan -- 0.1.0-alpha.11](0.1.0-alpha.11/release-plan-0.1.0-alpha.11.md),
and the latest completed checkpoint record is
[Release plan -- 0.1.0-alpha.10](0.1.0-alpha.10/release-plan-0.1.0-alpha.10.md).
Alpha checkpoints are internal milestones, not formal releases. The *live readiness state*
lives outside the file — see below.

## Where each thing lives (single source of state)

| Thing | Lives in |
|---|---|
| **Scope** (what's in this release) | the GitHub **milestone** named for the SemVer release, such as `0.1.0` or `0.1.0-alpha.11`, plus the Memoria Issue Tracker project view filtered to that milestone |
| **Readiness** (promotion-gate + validation-stage state) | the parent **"Release <version>"** issue and its readiness/stage sub-issues |
| **Prose** (scope summary, limitations, cut steps, roadmap) | `docs/releasing/<version>/release-plan-<version>.md` |
| **Build gaps** | GitHub issues |
| **Scope cuts** | GitHub issues with Readiness `Later`; ADRs only when the cut records a decision or durable rationale |
| **Version + notes** | `release-please` (CHANGELOG + tag + GitHub Release) |
| **Automated test evidence** | GitHub Actions runs and artifacts |
| **Local gate evidence** | `scripts/verify` JSON bundles, normally under `/tmp/memoria-verify/` or attached to the release issue |
| **In-work release design notes** | `docs/releasing/<version>/tmp/` while the release is being designed; delete this folder when the release is done |
| **Close-out evidence worth preserving** | the relevant issue comments, Actions artifacts, or optional `validation-log.md` |

The plan file holds **prose, not state tables**. Readiness/stage state is in the release
issue/sub-issues; routine automated evidence is in Actions. Everything else points,
never restates.

## Starting a new release

1. **Folder + plan.** Create `docs/releasing/<version>/` and copy
   the [release plan template](release-plan-template.md) →
   `docs/releasing/<version>/release-plan-<version>.md`. Fill the prose; set frontmatter
   `status: draft`, `released: false`.
2. **Milestone + Project view = scope.** Create the SemVer milestone
   (`gh api repos/eranroseman/memoria-vault/milestones -f title=0.1.0`) and assign
   the issues that scope it. In the Memoria Issue Tracker project,
   use a table filtered to the milestone and sorted by Priority as the live release plan.
3. **Parent issue + sub-issues = readiness.** Open a **"Release <version>"** issue
   (for example, `Release 0.1.0`; label `release`, milestone `<version>`). Add one sub-issue per release gate or
   validation stage (`G#`, `S#`) so GitHub shows sub-issue progress and each gate can carry its own evidence,
   owner, and comments. Do not hand-maintain a markdown state table.
4. **In-work design notes** (optional) → `tmp/`. These files are tracked so a branch
   can cite design research while the release is being shaped, but they are not
   published release artifacts. Keep links portable within the repo and delete
   `tmp/` when the release is done.
5. **Overflow** (optional) → `release-plan-<version>-appendix.md`.

## Cutting a release

1. Every readiness/stage sub-issue is closed; required CI green on `main`; no open High-priority blocker.
   The automated prefix for the candidate is `scripts/verify rc`; attach or link its
   `summary.json` evidence from the release issue.
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
6. **Formal release:** merge the release-please release PR — it bumps
   `CHANGELOG.md`, tags the release, and publishes the GitHub Release with curated notes
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
| `release-plan-<version>.md` | Prose: scope, readiness/stage *definitions*, docs/runtime bars, blockers rule, cut procedure, roadmap |
| `release-plan-<version>-appendix.md` | *(optional)* phase roadmap + investigation detail |
| `validation-log.md` | *(optional)* curated release evidence worth preserving after the GitHub issue/Actions trail |
| `tmp/` | *(temporary)* tracked in-work design notes; remove when the release is done |
