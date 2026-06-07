# AGENTS.md — working guidelines for AI agents in this repo

For any AI agent (Claude Code, Hermes, etc.) making changes to `eranroseman/memoria-vault`.
Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

**One principle:** choose the correct long-term solution, never the path of least effort. Surface trade-offs and your recommendation rather than defaulting to the cheap path.

**When presenting options:** give pros/cons and a recommendation for every option — never a bare list.

---

## Where things live

| Piece | Host | Path |
|---|---|---|
| **Dev repo** (`memoria-vault`) | WSL2 · ext4 | `~/memoria-vault` |
| **Hermes runtime** | WSL2 | `~/.hermes/` — profiles, config, MCP venv |
| **Obsidian + runtime vault** | Windows | `~/Memoria` |

- Work **inside WSL2** on ext4 — never `/mnt/c`, never OneDrive.
- Obsidian opens only the *runtime* vault (`~/Memoria`) — never this dev repo.
- WSL2↔Windows bridge: Obsidian Local REST API at `https://127.0.0.1:27124`, bare endpoint (not `/mcp/`). Requires `networkingMode=mirrored` in `%UserProfile%\.wslconfig` + `wsl --shutdown`. API key lives in the plugin's `data.json` — never print or commit it.

---

## 1. Session isolation — git worktree

When more than one agent/session may touch this repo, each must work in its own worktree:

```bash
git worktree add ~/mv-<session> -b agent/<session> origin/main
cd ~/mv-<session>          # all edits, commits, PRs from here
git worktree remove ~/mv-<session>   # when done
```

Keep worktrees on ext4 (`~/…`), never under `/mnt/c`.

## 2. Branch first — always

```bash
git fetch origin && git switch -c fix/<thing> origin/main
```

Never edit on `main` or on another session's branch.

## 3. Stage by explicit path — never `git add -A`

The tree may hold parallel work-in-progress. Stage only what you changed:

```bash
git add scripts/install.sh          # yes
git add -A                          # NO
```

If you find unmerged work you didn't author, preserve it and surface it to the user. Never delete a branch or stash you didn't create without confirming its content is already on `main`.

---

## PR flow

`main` rejects direct pushes (ruleset GH013). Always open a PR:

```bash
git push -u origin <branch>
gh pr create --base main --fill
gh pr checks <n> --watch
gh pr merge <n> --squash --delete-branch
```

After merge, resync local main:

```bash
git checkout main && git fetch origin && git reset --hard origin/main
```

**Known quirk:** `gh pr merge` may print `fatal: Not possible to fast-forward` — the merge still **succeeds server-side**. Verify with `gh pr view <n> --json state -q .state`, then resync. Don't re-attempt the merge.

If a PR shows `BEHIND`: `gh pr update-branch <n>` (or `gh api -X PUT repos/eranroseman/memoria-vault/pulls/<n>/update-branch`), then wait for checks to re-run.

**Emergency bypass (policy-code deadlock only):** when a PR changes `.github/scripts/` or `.github/workflows/` AND the `pr_policy.py` code itself, temporarily disable "Require a pull request" and "Require status checks" in Settings → Rules → Rulesets → "main", push directly to main, then re-enable both. For policy-code fixes only.

---

## Required CI checks

All must pass before merge:

| Check | Validates |
|---|---|
| `pr-policy` | Three-tier gate: auto-approve docs-only, flag sensitive paths, block untrusted |
| `docs-doctor` | `docs/` + `vault/` link text, broken links, frontmatter, README presence |
| `docs-links` | Every `docs/` reference under `vault/` resolves (`scripts/check-vault-links.sh`) |
| `shellcheck (scripts/install.sh)` | Shell lint |
| `PSScriptAnalyzer (scripts/install.ps1)` | PowerShell lint |
| `python-selftest` | `--self-test` on vault Python tooling |

**CI invariant:** required-check workflows must have **no** `paths:` filter — a path-filtered required check permanently blocks PRs that don't touch those paths.

### `pr-policy` tiers

| Decision | Trigger |
|---|---|
| `auto_approve` | Trusted author + all files in safe paths (`docs/`, `project/releases/`, `project/proposals/`; `.md`/`.txt`) |
| `needs_human` | Trusted author on sensitive paths, or untrusted author on safe paths |
| `block` | Untrusted author on sensitive paths |

Sensitive paths: `vault/.memoria/`, `scripts/`, `project/decisions/`, `.github/`.
Trusted authors: `eranroseman`, `github-actions[bot]`, `dependabot[bot]`.

On `auto_approve` PRs, the workflow enables squash auto-merge immediately.

---

## Test before opening a PR

- **Shell** (`scripts/install.sh`): `bash -n scripts/install.sh` (parse) + a `--dry-run` pass.
- **Python** (`.memoria/mcp/*.py`, `detectors.py`): `python <file> --self-test`.
- **PowerShell** (`scripts/install.ps1`): rely on CI; `Write-Host` is intentional and excluded via `scripts/PSScriptAnalyzerSettings.psd1`. Functions must use approved verbs (`Install-`, not `Ensure-`).
- **Installer end-to-end:** `bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test` — never test against the real `~/Memoria`.

---

## Skills

| Stage | Skill | Use when |
|---|---|---|
| Any docs PR | `/docs-review` *(project)* | Before opening — checks quadrant fit, links, indexing, terminology |
| Any PR | `/code-review` | Before opening — catches bugs and simplification opportunities |
| Sensitive-path changes | `/security-review` | PRs touching `scripts/`, `.github/`, `vault/.memoria/` |
| Confirming a fix | `/verify` | After a change — runs the app to confirm actual behavior |
| New or cut release | `/release` *(project)* | Scaffolds release folder, milestone, and plan |

---

## Platform & runtime facts

- **Hermes config:** consult the local docs at `~/.hermes/hermes-agent/website/docs/`, `cli-config.yaml.example`, and the skills catalogs (`skills-catalog.md`, `optional-skills-catalog.md`) before any Hermes decision. Do not infer from Memoria's existing files — the docs are the source of truth.
- **Line endings:** `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to LF. Working on ext4 avoids CRLF churn.
- **MCP deps:** install into `<vault>/.memoria/.venv`; `mcp_servers` and hooks are wired in `config.yaml` per profile. Hermes never reads a standalone `mcp.json` (ADR-27).
- **Profiles:** `vault/.memoria/profiles/memoria-*/` — `SOUL.md` / `config.yaml` / `distribution.yaml` + `cron/` / `skills/`. Keep all in sync. No per-profile `mcp.json`.
- **Secrets:** `~/.hermes/profiles/<profile>/.env` and gitignored vault files (shipped as `.example`). Never commit a real key.
- **Build state & gaps:** check open [issues](https://github.com/eranroseman/memoria-vault/issues) and the [v0.1 release plan](project/releases/v0.1/release-plan-v0.1.md) for current blockers and known limitations.

---

## Writing docs

### Diátaxis quadrant routing

| Quadrant | Folder | Answers |
|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" |
| How-to | `docs/how-to-guides/` | "How do I accomplish X?" |
| Reference | `docs/reference/` | "What is the exact value/command?" |
| Explanation | `docs/explanation/` | "Why is it designed this way?" |

Mixed-quadrant pages are wrong — split them.

- **Links:** `docs/` files → relative links; `vault/` files → absolute website URLs (`https://eranroseman.github.io/memoria-vault/…`).
- **Indexing:** every new page goes in its section README; how-to pages also go in `how-to-guides/README.md`. Assign `nav_order` so the folder reads in logical sequence.
- **How-to titles:** concise, no "How to…" prefix; match the README link text and filename.
- **Citations:** new works go in `reference/bibliography.md` (ACM author-date, `<a id="…"></a>` anchor); link in-text mentions to `[bibliography.md#anchor](../reference/bibliography.md#anchor)`.

### Terminology

Two flows: **Compile** (knowledge in) and **Compose** (knowledge out). Together: **the knowledge cycle**.
Never name these "upstream/downstream pipeline" or "the two pipelines". `pipeline`, `upstream`, `downstream` are fine in all other senses.

### ADR template (`project/decisions/`)

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

### RFC template (`project/proposals/`)

```markdown
---
topic: proposals
id: RFC-<NN>
title: <Short title>
status: open | deferred | adopted | rejected
created: YYYY-MM-DD
---

# RFC-<NN>: <Title>

## What
## Why
## Trade-offs
## Adoption trigger
## Guard
## Alternatives considered
## Related
```

### Release plans (`project/releases/`)

One file per version, copied from `project/releases/release-plan-template.md`. Gate/tier state lives **only** in §2/§3 of the release-plan file — never restated elsewhere. Build gaps go to GitHub issues; scope cuts go to proposals.

---

## Work routing

| Item | Goes to |
|---|---|
| Bug, enhancement, doc fix, question | GitHub issue (label; milestone only if scheduled) |
| Large capability worth weighing trade-offs | RFC in `project/proposals/` |
| Closed decision + rationale | ADR in `project/decisions/` |
| Release gate/tier readiness | `release-plan-<v>.md` §2/§3 |
| Analysis, findings, scratch | `_reports/` / `_notes/` (gitignored) |

- GitHub project board: "Memoria backlog" — Inbox → Scheduled → In progress → In review → Done.
- Labels: `bug` / `enhancement` / `documentation` / `question` / `research` + priority `P0`/`P1`/`P2`.
- Milestones are releases. No milestone = unscheduled backlog.
- Never track shared work in `/TODO` or `_notes/` — gitignored and invisible to others.
- Generated reports go in `_reports/`, never in `project/` or the repo root.

---

## Merge discipline

- One scope → one branch → one PR → squash-merge → delete. Target ≤1 day or ≤10 commits.
- Rebase onto `origin/main` daily and before every PR: `git fetch && git rebase origin/main`.
- No two branches may implement the same ADR or rewrite the same files.
- Structural/destructive changes (folder moves, deletions, schema bumps) get their own tiny PR, merged first — active branches rebase the same day.
- Stop-check: if `git log -3` shows a co-author who isn't you, you're on someone else's branch — make your own.
