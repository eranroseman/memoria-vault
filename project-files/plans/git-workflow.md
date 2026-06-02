# Git workflow — branch, integrate, merge

How work gets from a branch onto `main` without the big-bang merge that bit us.
This is the human walkthrough; the terse agent version is **AGENTS.md §9** (and
§0–§3 for worktrees, branching, staging, and the PR flow).

## What went wrong (post-mortem, 2026-06-01/02)

Three branches were cut from the *same* `main` commit (`11e03e2`) and grown in
parallel while `main` never moved:

| Branch | Commits | Scope |
|---|---|---|
| `feat/adr-27-config` | 60 (two AI sessions) | template reorg, 99-system, reference dissolution, ADR-27, link fixes, renames |
| #60 `chore/scripts-move…` | 9 | per-release plan structure |
| #61 `docs/plans-migration` | 12 | a *second* ADR-27 implementation, on an older base |

They overlapped on the same files (ADR-27, on-disk-layout, frontmatter,
structural-detectors), **ADR-27 was implemented twice**, and feat *deleted* files
(`04-reference`, `schema-reference`) that #61 still carried. Consolidating became a
~30-conflict semantic reconciliation — several conflicts being "which design wins,"
not "which line wins."

**Root cause:** long-lived parallel branches off a frozen trunk, with overlapping
scope and structural changes that lived on only one branch. Two AI sessions also
shared one branch and working tree, fusing their work into a history that couldn't
be sliced apart (and racing each other's HEAD — mis-amends, vanished edits, a file
deleted twice).

## The workflow

### 1. Merge small, merge often — keep `main` moving
A branch is *one coherent unit of work*. Open a PR, squash-merge, delete the
branch. If a branch passes **~1 day** or **~10 commits** without landing, it's
already too big — split it and merge the pieces. (feat reached 60 commits over
20+ hours. That is the anti-pattern, not the norm.)

### 2. Stay current — rebase on `origin/main` constantly
`git fetch origin && git rebase origin/main` daily and before every PR. A branch
that drifts from its base is the divergence engine. If you can't keep it current,
it's too big.

### 3. One scope, one branch, one owner — claim it first
Before starting, claim the ADR / subsystem / file-set (the issue, or a one-line
note somewhere visible). **Two branches must never implement the same ADR or
rewrite the same files.** Building ADR-27 twice was the costliest mistake here.

### 4. Structural & destructive changes go FIRST, alone, fast
Folder moves, file deletions, schema bumps → their own tiny PR, merged immediately
and announced. Every active branch then rebases to absorb them the same day. A
deletion or reorg that lives only on a side branch *resurrects* the old state when
another branch merges (that's exactly how `schema-reference` tried to come back).

### 5. Serialize parallel work — a merge train
When two branches must run at once: the first merges to `main`; the rest
immediately rebase onto the new `main`; then the next merges. Never let parallel
branches grow into competing mega-branches.

### 6. One worktree + one branch per agent/session
Never two people (or two AI sessions) on one branch in one checkout — it fuses
their work and races HEAD. Each session gets its own
[git worktree](https://git-scm.com/docs/git-worktree), its own branch, its own
scope. See AGENTS.md §0. (A local `git reset` in a shared checkout also silently
reverts the other session's uncommitted edits — commit and push early.)

## Checklists

**Starting a branch**
- [ ] `git fetch origin` — cut from the *latest* `origin/main`
- [ ] scope claimed; no other active branch owns these files / this ADR
- [ ] my own worktree + branch (not shared)

**Daily / before opening a PR**
- [ ] `git fetch origin && git rebase origin/main`
- [ ] still small? (< ~1 day, < ~10 commits) — if not, split
- [ ] any structural change already landed in its own PR?

**Landing it** (`main` is protected — no direct push; see AGENTS.md §3)
- [ ] `git push -u origin <branch>` → `gh pr create --base main`
- [ ] required checks green
- [ ] `gh pr merge --squash --delete-branch`
- [ ] `git checkout main && git fetch origin && git reset --hard origin/main`

## If you're already in a divergence mess

1. Pick the **canonical** branch — usually the one with the newest structural state.
2. Diff each other branch against it: what would it **add** vs **regress**?
3. Adds nothing unique → close its PR. Has unique bits → cherry-pick just those onto
   canonical.
4. PR canonical → `main`, merge, delete the rest.
5. Then return to small branches so it never recurs.
