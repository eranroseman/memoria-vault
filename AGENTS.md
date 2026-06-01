# AGENTS.md — working guidelines for AI agents in this repo

Conventions for any AI agent (Claude Code, Hermes, etc.) making changes to
`eranroseman/memoria-vault`. Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

This file encodes hazards learned the hard way. Following it avoids the failure
modes that bite agents here: **concurrent sessions** sharing one working tree, the
**auto-commit hook** entangling your work, and **branch protection** rejecting
direct pushes.

---

## 0. Isolate your session in a git worktree

**If more than one agent/session may touch this repo, each must work in its own
[git worktree](https://git-scm.com/docs/git-worktree) — never the same checkout.**

Two sessions sharing one working directory **corrupt each other**: they run
`git switch` / `git reset --hard origin/main` and (with the obsidian-git
auto-backup) commit the tree, so one session's `checkout`/`reset` silently moves
the other's HEAD and reverts its uncommitted edits mid-task. This is not
hypothetical — it happened repeatedly (HEAD jumping branches, edits vanishing,
one session's work bundled into another's PR).

A worktree shares the same `.git` history but has its own HEAD, branch, and files,
so sessions can't trample each other:

```bash
# one-time per session, OUTSIDE OneDrive (OneDrive sync fights git):
git worktree add ~/mv-<session> -b agent/<session> origin/main
cd ~/mv-<session>          # do ALL your work here
# ... branch, edit, commit, PR from here ...
git worktree remove ~/mv-<session>   # when done (or leave it for next time)
```

`core.hooksPath` and `.gitattributes` are inherited, so the pre-commit guard and
LF rules apply in the worktree too. The shared canonical checkout
(`…/OneDrive/…/memoria-vault`) is **also inside OneDrive** — a second reason to
do real work in a worktree outside it.

## 1. Branch before you edit — always

**Create your own branch as the first action of any edit task**, off the latest
`origin/main`:

```bash
git fetch origin && git switch -c fix/<thing> origin/main
```

**Why this is non-negotiable here:** the **obsidian-git** plugin's auto-backup
(`autoSaveInterval: 30` in `vault/.obsidian/plugins/obsidian-git/data.json`)
commits the whole git working tree every ~30 min — you'll see commits titled
`vault: <timestamp> N files`. That config ships *for the end-user's runtime vault*
(`~/Memoria`), where auto-backup is a wanted feature. It becomes hostile only when
someone **opens this dev repo (`memoria-vault/`) itself as an Obsidian vault** —
then the timer auto-commits the entire source tree (`install.sh`, `project-files/`,
`docs/`…), bundling your in-progress edits with the user's unrelated work and
sometimes spawning phantom branches that orphan work.

**Two defenses:**

1. **Don't open `memoria-vault/` as an Obsidian vault.** Edit the source repo with
   a normal editor; open the *runtime* vault (`~/Memoria`) in Obsidian instead.
2. **Always create your own branch before editing** (above). A dedicated branch
   keeps your change isolated and reviewable even if a stray auto-commit fires.

Do **not** "fix" this by editing the shipped `data.json` — it is correct for
deployment (see `docs/reference/obsidian-plugins.md`); the problem is *where*
Obsidian is pointed, not the config.

## 2. Stage by explicit path — never `git add -A`

The working tree may hold the user's parallel work-in-progress or hook-generated
churn. Stage only the files you changed:

```bash
git add install.sh                      # yes — explicit
git add project-files/decisions/24-*.md # yes
git add -A                              # NO — sweeps in others' work
```

If you find unmerged work you didn't author tangled into a branch (new ADRs,
renames, a stash), **preserve it** (back it up / leave the stash) and surface it
to the user. Never delete a branch or stash that holds work you didn't create
without confirming its content is already on `main`.

## 3. `main` is protected — use the PR flow

Direct `git push origin main` is **rejected** (`GH013` — repository ruleset). The
flow is:

```bash
git push -u origin <branch>
gh pr create --base main --fill          # or --title/--body
gh pr checks <n> --watch                  # wait for green (see §4)
gh pr merge <n> --squash --delete-branch
```

Then resync local main:

```bash
git checkout main && git fetch origin && git reset --hard origin/main
```

**Known quirk:** `gh pr merge` may print `fatal: Not possible to fast-forward,
aborting` — this is `gh` failing to update your *local* main; the merge still
**succeeds server-side**. Verify with `gh pr view <n> --json state -q .state`
(expect `MERGED`), then resync as above. Don't re-attempt the merge.

If a PR shows `BEHIND` (strict checks require an up-to-date branch), run
`gh pr update-branch <n>` and wait for checks to re-run.

## 4. Required status checks

These checks are **required** by the branch ruleset and must all pass:

| Check | Runs |
| --- | --- |
| `docs-doctor` | structural lint of `docs/` (broken links, misfiled files) |
| `shellcheck (install.sh)` | shell lint |
| `PSScriptAnalyzer (install.ps1)` | PowerShell lint |
| `python-selftest` | `--self-test` of the vault Python tooling (policy gate, board export, metrics, detectors) |

**CI invariant — do not break this:** a workflow that backs a *required* status
check must **not** have a `paths:` filter. A path-filtered required check never
reports on PRs that don't touch those paths, leaving them permanently `BLOCKED`.
Both `docs-doctor.yml` and `lint-installers.yml` therefore run on every push/PR
unconditionally. If you add a new required check, follow the same rule.

**Linter notes:** `install.ps1` is an interactive installer, so `Write-Host` is
intentional and excluded via `PSScriptAnalyzerSettings.psd1`; PowerShell
functions must use approved verbs (`Install-`, not `Ensure-`).

## 5. Test before you commit

Every installer bug in this repo's history was caught by *running* the code, not
reading it. Before opening a PR:

- **Shell** (`install.sh`): `bash -n install.sh` (parse) + a `--dry-run` pass.
- **PowerShell** (`install.ps1`): `Invoke-ScriptAnalyzer -Settings ./PSScriptAnalyzerSettings.psd1`.
- **Python** (`.memoria/mcp/*.py`, `detectors.py`): run `--self-test`
  (`policy_mcp.py`, `policy_hook.py`, `board_export.py`, `metrics_aggregate.py`,
  `detectors.py` all support it).
- **Installer end-to-end:** deploy into a *throwaway* vault
  (`bash install.sh --yes --no-apps --vault ~/Memoria-test`), verify, then clean
  up — never test against the real `~/Memoria`.

## 6. Runtime / platform facts

- The Hermes runtime runs on **Linux/WSL2**; Windows is only the editing surface.
  `install.ps1` is a thin launcher that hands off to `install.sh` inside WSL2.
- Line endings: `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to **LF**
  (a CRLF in `install.sh` breaks the WSL2 shebang). Don't override it.
- MCP deps install into a vault-local venv (`<vault>/.memoria/.venv`); the
  installer wires that interpreter into each profile's `mcp.json`/`config.yaml`.
- Secrets live only in `~/.hermes/profiles/<profile>/.env` and gitignored vault
  files (shipped as `.example`). **Never** commit a real key; if one leaks,
  rotate it.

## 7. Profiles and the vault

- Agent profiles live under `vault/.memoria/profiles/memoria-*/` and follow the
  `SOUL.md` / `AGENTS.md` / `config.yaml` / `mcp.json` / `distribution.yaml`
  structure. Keep the seven in sync.
- Authoritative design is in `docs/` (Diátaxis) and `project-files/decisions/`
  (ADRs). `notes/` and working reports are scratch — don't treat them as canon.

## 8. Writing and editing docs

### `docs/` — every file must sit in exactly one Diátaxis quadrant

| Quadrant | Folder | The file answers… | Must not contain |
|---|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" | Explanation, reference lookup |
| How-to guide | `docs/how-to-guides/` | "How do I accomplish X?" | Why things work, conceptual background |
| Reference | `docs/reference/` | "What is the exact value / schema / command?" | Instructional steps, rationale |
| Explanation | `docs/explanation/` | "Why is it designed this way?" | Step-by-step instructions, lookup tables |

**Quadrant test before writing.** Ask: "Would a reader come here to *do* something, to *learn* something, to *look something up*, or to *understand* something?" Route accordingly. Mixed-quadrant pages are always wrong — split them.

**Link rules.**

- `docs/` files → **relative links** (developers have the full repo locally).
- `vault/` files → **absolute website URLs** (`https://eranroseman.github.io/memoria-vault/…`) because the vault installs standalone to `~/Memoria` where repo-relative paths don't resolve.

**Indexing.** Every new page must be added to its section README. New subsections need a `README.md` with `parent`, `has_children: true`, and an explicit `permalink`.

### `project-files/decisions/` — ADR template

```markdown
---
topic: decisions
id: <NN>
title: <Short title>
status: accepted | rejected | superseded
date_proposed: YYYY-MM-DD
date_resolved: YYYY-MM-DD
supersedes: []
superseded_by: []
---

# ADR-<NN>: <Title>

## Context
## Decision
## Why
## Consequences
## Alternatives considered
```

### `project-files/proposals/` — PROP template

```markdown
---
topic: proposals
id: PROP-<NN>
title: <Short title>
status: open | deferred | adopted | rejected
created: YYYY-MM-DD
---

# PROP-<NN>: <Title>

## What
## Why
## Trade-offs
## Adoption trigger
## Guard
## Alternatives considered
## Related
```
