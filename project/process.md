# Contributing workflow

How work moves from a branch onto `main`. Rules are authoritative in **AGENTS.md** (§§1–3, "PR flow", "Merge discipline"); this file is the human-facing complement with checklists and recovery.

## Branch discipline

- **One scope per branch.** Claim it via the issue before starting — two branches must never implement the same ADR or rewrite the same files.
- **Keep it small.** ≤1 day or ≤10 commits. Split and land if it grows beyond that.
- **Stay current.** `git fetch origin && git rebase origin/main` daily and before every PR.
- **Structural changes first.** Folder moves, deletions, schema bumps get their own tiny PR, merged and announced — every active branch rebases the same day.
- **One worktree per session.** See AGENTS.md §1 for setup. Never share a branch or checkout between sessions.

## Issue and board flow

Every actionable item is a GitHub issue. The board is **"Memoria backlog"** at <https://github.com/users/eranroseman/projects/1>.

| Column | State |
|---|---|
| Inbox | Filed, unscheduled |
| Scheduled | Assigned to a milestone |
| In progress | Branch open |
| In review | PR open |
| Done | Merged / closed |

Pick an issue → move to **In progress**, open a branch. Open the PR with `Closes #N` → **In review**. Squash-merge → issue auto-closes → **Done**.

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
- [ ] required checks green (AGENTS.md §5)
- [ ] `gh pr merge --squash --delete-branch`
- [ ] `git checkout main && git fetch origin && git reset --hard origin/main`

## Divergence recovery

If branches have grown in parallel and overlap:

1. Pick the **canonical** branch — the one with the most recent structural state.
2. Diff each other branch against it: what would it **add** vs **regress**?
3. Adds nothing unique → close its PR. Has unique bits → cherry-pick just those onto canonical.
4. PR canonical → `main`, merge, delete the rest.
5. Return to small branches immediately.
