---
topic: releases
---

# Starting a new release — vX.Y

Each release gets its own folder, `releases/vX.Y/`. This file is the scaffold for
that folder; the reusable plan body lives in
[release-plan-template.md](release-plan-template.md).

## Steps

1. **Create the folder** `releases/vX.Y/` and a `README.md` (copy an existing
   release README; it's a thin index of the files below).
2. **Copy the plan:** [release-plan-template.md](release-plan-template.md) →
   `releases/vX.Y/release-plan-vX.Y.md`. Reset every Gate (`G#`) and Tier (`T#`)
   state to `todo`; set frontmatter `status: draft`, `released: false`.
3. **Create the GitHub milestone** `vX.Y` and assign the issues that scope it
   (see [AGENTS.md §10](../../AGENTS.md)). The milestone — not this folder — is the
   live scope list; the plan's §4 Blockers *links* the release-blocking issues.
4. **Add detail overflow** (optional) to `release-plan-vX.Y-spillover.md` when the
   plan's phase/exit-criteria detail gets too long for a crisp plan.

## Standard contents of a `releases/vX.Y/` folder

| File | What it holds |
|---|---|
| `README.md` | Thin index of this release's files |
| `release-plan-vX.Y.md` | The plan: scope, gates (G#), tiers (T#), blockers, cut procedure, roadmap |
| `release-plan-vX.Y-spillover.md` | *(optional)* phase roadmap + investigation detail the plan summarizes |
| *run records* | *(optional)* completed test-protocol runs and sign-off sheets for the cut (the reusable protocols live in [../tests/](../tests/)) |

## Single source of state

Gate/tier state lives **only** in the plan's §2/§3; build gaps live **only** in
GitHub issues; scope cuts in `proposals/`. Everything else points — never restates.
