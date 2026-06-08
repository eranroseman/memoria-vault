# Contributing workflow

How work moves from a branch onto `main`. Rules are authoritative in **AGENTS.md** (§§1–3, "PR flow", "Merge discipline"); this file is the human-facing complement with checklists and recovery.

## Branch discipline

- **One scope per branch.** Claim it via the issue before starting — two branches must never implement the same ADR or rewrite the same files.
- **Keep it small.** ≤1 day or ≤10 commits. Split and land if it grows beyond that.
- **Stay current.** `git fetch origin && git rebase origin/main` daily and before every PR.
- **Structural changes first.** Folder moves, deletions, schema bumps get their own tiny PR, merged and announced — every active branch rebases the same day.
- **One worktree per session.** See AGENTS.md §1 for setup. Never share a branch or checkout between sessions.
- **Commit or stash before you switch.** `reset --hard` / `checkout -- <path>` / `clean -f` discard uncommitted work with no reflog; clean the tree (`git stash -u`) first, or keep a worktree per branch so there's nothing to lose. See AGENTS.md §4.

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

### Board automation

The board's **Status** field is kept in sync by the Project's built-in workflows
(Project → ⚙ Settings → Workflows) — don't hand-move cards for these transitions:

| Automation (enabled) | Effect |
|---|---|
| Auto-add to project / Auto-add sub-issues | Every new repo issue (and sub-issue) lands on the board |
| Item added to project | New item → **Inbox** |
| Pull request linked to issue | Issue with an open linked PR → **In review** |
| Item closed / Pull request merged | → **Done** |
| Auto-close issue | Setting Status **Done** closes the issue |

Only two steps are manual: **Inbox → Scheduled** (assigning a milestone *is* the
scheduling act — see AGENTS.md "Work routing") and **Scheduled → In progress**
(when you open the branch). Everything downstream of opening a PR is automatic.

## Issue triage

Triage keeps the backlog actionable. The label set is defined in AGENTS.md ("Work routing").

- **New issue** (within ~48h): add a category label, set a priority, and assign a milestone only if it's scheduled (no milestone = unscheduled backlog).
- **Weekly:** groom the Inbox — move ready, milestoned items to Scheduled; re-prioritize.
- **Monthly:** sweep stale issues (no activity in 30+ days) — close or refresh.

Priority labels:

| Label | Criteria |
|---|---|
| `P0` | Blocks a core workflow or risks data loss |
| `P1` | Significantly degrades a workflow; no workaround |
| `P2` | Minor inconvenience or future improvement |

Duplicates → close the newer issue with `Duplicate of #X` and the `duplicate` label. Won't-fix → close with `wontfix` and a brief reason (keeps the decision on record).

## Versioning

- Stay on `v0.x` while pre-stable; `v1.0.0` signals the agent architecture and workflow are stable.
- `fix` → patch, `feat` → minor, breaking change → major (post-stable). Pre-release suffixes (`-alpha`/`-beta`/`-rc`) are fine for experimental builds.
- Cut a release at the end of a meaningful milestone, not on a calendar cadence. Milestones are releases (AGENTS.md "Work routing").
- A **breaking change** in Memoria is: renaming a profile `config.yaml` field, restructuring the vault folder layout, removing a profile capability or skill, or changing ADR-frontmatter required fields.

**How a release runs** (the `/release` skill scaffolds it):

- **Scope** is the GitHub milestone `vX.Y` — the issues it must ship.
- **Readiness** lives in one **"Release vX.Y" tracking issue** — a gate checklist whose progress bar *is* the status. Don't track gate state in the plan file.
- **Prose** (what/why, gate rationale) lives in `project/release/<v>/`; `status-doctor` (a required check) guards it against stale links and path drift.
- **Version + CHANGELOG + the GitHub Release** are owned by **release-please** (manifest mode) — opened automatically from Conventional Commits on `main`; merging its PR cuts the tag. Don't hand-edit `CHANGELOG.md` or tag by hand. See `project/release/README.md`.

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
- [ ] `git checkout main && git fetch origin && git reset --hard origin/main`

## Divergence recovery

If branches have grown in parallel and overlap:

1. Pick the **canonical** branch — the one with the most recent structural state.
2. Diff each other branch against it: what would it **add** vs **regress**?
3. Adds nothing unique → close its PR. Has unique bits → cherry-pick just those onto canonical.
4. PR canonical → `main`, merge, delete the rest.
5. Return to small branches immediately.
