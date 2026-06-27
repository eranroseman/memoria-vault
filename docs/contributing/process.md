---
title: Contributing workflow
parent: Contributing
nav_order: 1
---
# Contributing workflow

How work moves from a branch onto `main`. Rules are authoritative in **AGENTS.md** ("Session isolation", "Branch first", "Stage by explicit path", "PR flow", "Merge discipline"); this file is the human-facing complement with checklists and recovery.

## Branch discipline

The branch, isolation, and merge-discipline rules are authoritative in **AGENTS.md** ("Session isolation", "Branch first", "Stage by explicit path", "Clean tree before you switch or reset", "Merge discipline") and not restated here: one scope per branch, keep it small (≤1 day or ≤10 commits), rebase onto `origin/main` daily and before every PR, land structural changes in their own tiny PR first, and work each session in its own worktree with a clean tree before any `reset --hard`/`switch`. The checklists below turn those rules into a working routine.

## Issue and Project flow

Every actionable item is a GitHub issue in
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1). The full
field model is in [Issue tracking](issue-tracking.md); this page only summarizes
the working loop.

Pick an issue with Status `Backlog` and Readiness `Ready`, move it to
`In progress`, and open a branch. Open the PR with `Closes #N` so the linked
issue moves to `In review`. Squash-merge when checks pass, then close the issue
as `Done` once acceptance criteria are met.

### Board automation

The Project's **Status** field is kept in sync by built-in workflows
(Project → Settings → Workflows) for the common transitions:

| Automation (enabled) | Effect |
|---|---|
| Auto-add to project / Auto-add sub-issues | Every new repo issue (and sub-issue) lands on the board |
| Item added to project | New item → **Backlog** |
| Pull request linked to issue | Issue with an open linked PR → **In review** |
| Item closed / Pull request merged | → **Done** |
| Auto-close issue | Setting Status **Done** closes the issue |

Scheduling is the milestone, not a Status or Readiness value. No milestone means
unscheduled backlog; a milestone means the issue is scoped to that release phase.

## Issue triage

Triage keeps the backlog actionable. The Project fields are defined in
[Issue tracking](issue-tracking.md).

- **New issue** (within ~48h): set Readiness and Status `Backlog`; assign a milestone only if scheduled.
- **Weekly:** groom Backlog — fill missing Readiness values and split oversized work.
- **Monthly:** sweep stale issues (no activity in 30+ days) — close or refresh.

Duplicates → close the newer issue with `Duplicate of #X` and the `duplicate` label. Won't-fix → close with `wontfix` and a brief reason (keeps the decision on record).

## Versioning

- Stay on `v0.x` while pre-stable; `v1.0.0` signals the agent architecture and workflow are stable.
- `fix` → patch, `feat` → minor, breaking change → major (post-stable). Pre-release suffixes (`-alpha`/`-beta`/`-rc`) are fine for experimental builds.
- Cut a release at the end of a meaningful milestone, not on a calendar cadence. Milestones are releases (AGENTS.md "Work routing").
- A **breaking change** in Memoria is: renaming a profile `config.yaml` field, restructuring the vault folder layout, removing a profile capability or skill, or changing ADR-frontmatter required fields.

**How a release runs:** scope is the GitHub milestone and Project view, readiness is
the parent "Release vX.Y" issue plus readiness/stage sub-issues, prose lives in
`docs/releasing/<version>/`, and version/CHANGELOG/Release are owned by release-please.
That model is defined in AGENTS.md ("Release plans") and [Releasing](../releasing/README.md).

## Checklists

**Starting a branch**
- [ ] `git fetch origin` — cut from the latest `origin/main`
- [ ] scope claimed in the issue; no other active branch owns these files or this ADR
- [ ] own worktree and branch (not shared with another session)

**Daily / before opening a PR**
- [ ] `git fetch origin && git rebase origin/main`
- [ ] still small? (< ~1 day, < ~10 commits) — if not, split
- [ ] any structural change already landed in its own PR?

**Landing** (`main` is protected — no direct push; see AGENTS.md "PR flow")
- [ ] `git push -u origin <branch>` → `gh pr create --base main`
- [ ] required checks green (AGENTS.md "Required CI checks")
- [ ] `gh pr merge --squash --delete-branch`
- [ ] local `main` tree is clean and your work is merged upstream
- [ ] `git checkout main && git fetch origin && git reset --hard origin/main`

## Divergence recovery

If branches have grown in parallel and overlap:

1. Pick the **canonical** branch — the one with the most recent structural state.
2. Diff each other branch against it: what would it **add** vs **regress**?
3. Adds nothing unique → close its PR. Has unique bits → cherry-pick just those onto canonical.
4. PR canonical → `main`, merge, delete the rest.
5. Return to small branches immediately.
