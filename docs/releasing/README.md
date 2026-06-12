---
title: Releasing
nav_order: 7
has_children: true
permalink: /releasing/
topic: releases
---

# Releasing

One folder per version, `releasing/vX.Y/`, holding the **prose** of that cut (scope,
known limitations, cut procedure, roadmap). The reusable body is
[Release plan — vX.Y.Z](release-plan-template.md); the current release is
[the v0.1 release](0.1.0/). The *live readiness state* lives outside the file — see below.

## Where each thing lives (single source of state)

| Thing | Lives in |
|---|---|
| **Scope** (what's in this release) | the GitHub **milestone** `vX.Y` (assigned issues) |
| **Readiness** (gate + validation-stage state) | the **"Release vX.Y" tracking issue** — a gate checklist GitHub renders as a progress bar |
| **Prose** (scope summary, limitations, cut steps, roadmap) | `release/vX.Y/release-plan-vX.Y.md` |
| **Build gaps** | GitHub issues |
| **Scope cuts** | `docs/adr/` (deferred-status ADRs) |
| **Version + notes** | `release-please` (CHANGELOG + tag + GitHub Release) |

The plan file holds **prose, not state tables**. Gate/stage state is the checklist
in the tracking issue; everything else points — never restates.

## Starting a new release — vX.Y

1. **Folder + plan.** Create `release/vX.Y/README.md` (thin index) and copy
   [Release plan — vX.Y.Z](release-plan-template.md) →
   `release/vX.Y/release-plan-vX.Y.md`. Fill the prose; set frontmatter
   `status: draft`, `released: false`.
2. **Milestone = scope.** Create the `vX.Y` milestone
   (`gh api repos/eranroseman/memoria-vault/milestones -f title=vX.Y`) and assign the
   issues that scope it (AGENTS.md "Work routing").
3. **Tracking issue = readiness.** Open a **"Release vX.Y"** issue (label `release`,
   milestone `vX.Y`) whose body is the **gate checklist** (one `- [ ]` per gate
   `G#` and validation stage `S#`). GitHub shows the progress bar; tick boxes as
   gates go green — no markdown state table to hand-edit.
4. **Overflow** (optional) → `release-plan-vX.Y-appendix.md`.

## Cutting a release

1. Every gate/stage box in the tracking issue ticked; required CI green on `main`; no open **P0**.
2. **Retire-sweep the ADRs.** Delete any ADR whose question this release dissolved or whose decision it superseded — keep the *Alternatives considered* memory; leave the number gap. See the [retirement criteria](../adr/README.md#when-to-retire-an-adr). (Lands as its own small PR before the cut.)
3. Merge the **release-please** "Release vX.Y" PR — it bumps `CHANGELOG.md`, tags
   `vX.Y`, and publishes the GitHub Release with curated notes (fold in the plan's
   known-limitations).
4. Set the plan frontmatter `status: released`, `released: true`.
5. Close the milestone and the tracking issue; roll unfinished issues forward.

## Standard contents of a `release/vX.Y/` folder

| File | Holds |
|---|---|
| `README.md` | Thin index of this release's files |
| `release-plan-vX.Y.md` | Prose: scope, gate/stage *definitions*, blockers rule, cut procedure, roadmap |
| `release-plan-vX.Y-appendix.md` | *(optional)* phase roadmap + investigation detail |
| *run records* | *(optional)* completed test-plan runs + sign-off sheets (reusable plans live in [Testing](../testing/)) |
