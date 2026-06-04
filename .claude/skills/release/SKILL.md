---
name: release
description: Scaffold and track a new Memoria release (vX.Y) — create the release folder + plan from the template, set up the GitHub milestone, and reset gates. Use when starting a new version or cutting an existing one.
---

# release

Stand up or cut a Memoria release. The conventions are in [AGENTS.md](../../../AGENTS.md) §10 (tracking) and the scaffold is [project-files/releases/_template.md](../../../project-files/releases/_template.md).

## Starting a new release vX.Y

1. **Folder + plan.** Create `project-files/releases/vX.Y/` with a thin `README.md`. Copy `project-files/releases/release-plan-template.md` → `releases/vX.Y/release-plan-vX.Y.md`. Reset every Gate (`G#`) and Tier (`T#`) to `todo`; frontmatter `status: draft`, `released: false`.
2. **Milestone = scope.** Create the GitHub milestone `vX.Y` (`gh api repos/eranroseman/memoria-vault/milestones -f title=vX.Y`). Assigning an issue to it is how it gets scheduled — the milestone, not the plan, is the live scope list. Link release-blocking issues from the plan's §4 Blockers.
3. **Overflow** (optional) goes in `release-plan-vX.Y-spillover.md`.

## Single source of state

- Gate/tier state lives **only** in the plan §2/§3.
- Build gaps are tracked as GitHub issues; release validation lives in the gates/tiers.
- Everything else points — never restates.

## Cutting a release

- All gates `done`; required CI checks green on `main`.
- Set the plan frontmatter `status: released`, `released: true`.
- Update `CHANGELOG.md`.
- Close the milestone; roll unfinished issues to the next milestone.

## PR flow reminder

Changes land via the PR flow (branch → PR → squash; main is a protected ruleset). Release-plan + status edits are `.md` under safe paths, so they auto-merge after Kilo; anything touching `vault/`, `scripts/`, `.github/`, or `decisions/` is `needs_human`. See AGENTS.md §3–4.
