# AGENTS.md — working guidelines for AI agents in this repo

For any AI agent (Claude Code, Hermes, etc.) making changes to `eranroseman/memoria-vault`.
Human contributors: see [Contributing to Memoria](CONTRIBUTING.md).

**One principle:** choose the correct long-term solution, never the path of least effort. Surface trade-offs and your recommendation rather than defaulting to the cheap path.

**When presenting options:** give pros/cons and a recommendation for every option — never a bare list.

---

## Working principles

- **Cover the whole scope.** Read, verify, and audit completely — every file and line in scope, no sampling or grep-standing-in-for-a-read. Verify a sub-agent's claimed coverage before reporting done.
- **Zero tolerated contradictions.** Docs must agree with each other and with the implementation — a stale page or a doc describing unbuilt behavior is a defect to fix, not log. Sweep the full surface with [`source-of-truth-map`](.agents/system/source-of-truth-map.md) + [`change-impact-map`](.agents/system/change-impact-map.md); no doc outranks another — research to the true source of truth and fix the stale side.
- **Verify hard conclusions independently.** For an uncertain runtime/architecture call, re-diagnose with a fresh agent (prefer two) and live-test the allowed/denied/fail-closed path before declaring done — don't ship solo reasoning. Ground Hermes claims in the `~/.hermes` docs first.

---

## Where things live

| Piece | Host | Path |
|---|---|---|
| **Dev repo** (`memoria-vault`) | WSL2 · ext4 | `~/memoria-vault` |
| **Hermes runtime** | WSL2 | `~/.hermes/` — profiles, config, MCP venv |
| **Obsidian + runtime vault** | Windows | `~/Memoria` |

- Work **inside WSL2** on ext4 — never `/mnt/c`, never OneDrive.
- Obsidian opens only the *runtime* vault (`~/Memoria`) — never this dev repo.
- WSL2↔Windows bridge (ADR-31): Hermes reaches Obsidian via the Local REST API plugin's **native MCP** over loopback HTTP — `http://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` (default port **27123**; the self-signed HTTPS on 27124 is *not* the Hermes path — Hermes can't verify the cert). Requires the plugin's insecure HTTP server **on**, plus `networkingMode=mirrored` in `%UserProfile%\.wslconfig` + `wsl --shutdown`. `OBSIDIAN_API_KEY` (Bearer) and `OBSIDIAN_MCP_PORT` live in each profile's `.env` — never print or commit the key.

---

## 1. Session isolation — git worktree

**Start every session in its own worktree — always, even solo, before you touch a single file.** A worktree gives you a private working tree *and* index, so a concurrent session's staged files can never be swept into your commit:

```bash
git fetch origin
git worktree add ~/mv-<session> -b agent/<session> origin/main
cd ~/mv-<session>          # all edits, commits, PRs from here
```

Keep worktrees on ext4 (`~/…`), never under `/mnt/c`.

Prefer a worktree **per branch** even working solo: switching becomes `cd`, and a `reset --hard` in one worktree can't reach another's uncommitted work (§4).

## 2. Branch first — always

**Before you edit, stage, or commit *anything*, create your branch as part of the
`git worktree add -b ...` command in §1.** No change — not even a one-line doc
fix — happens on `main`, on the default/shared checkout, or on another session's
branch. Use a descriptive branch name such as `fix/installer-timeout` in place
of `agent/<session>`; do not create a second branch after entering the worktree.

**Why a worktree, not just a branch:** the index is **shared** across a checkout. In a checkout another agent may be using, `git add <your-file>` stages *alongside* their already-staged files, and `git commit` captures the **whole** index — sweeping their work into your commit (this happened 2026-06-09: a one-file config commit swallowed 73 files of another agent's in-flight restructure). Your own worktree has its own index, so this cannot occur. If you ever must share a checkout, run `git diff --cached --name-only` and confirm it lists **only your files** before every commit.

## 3. Stage by explicit path — never `git add -A`

The tree may hold parallel work-in-progress. Stage only what you changed:

```bash
git add scripts/install.sh          # yes
git add -A                          # NO
```

If you find unmerged work you didn't author, preserve it and surface it to the user. Never delete a branch or stash you didn't create without confirming its content is already on `main`.

## 4. Clean tree before you switch or reset

`git switch -c` carries your uncommitted changes onto the new branch — but `git reset --hard`, `git checkout -- <path>`, and `git clean -f` **discard** them with no reflog entry. Before any of those, make the tree clean:

```bash
git stash push -u -m wip     # -u also stashes untracked WIP; restore with: git stash pop
```

The durable fix is a worktree per branch (§1): it turns "switch" into `cd`, so
there's normally no reason to switch or reset inside a task worktree.

---

## PR flow

`main` rejects direct pushes (ruleset GH013). Always open a PR:

```bash
git push -u origin <branch>
gh pr create --base main --fill
gh pr checks <n> --watch
gh pr merge <n> --squash --delete-branch
```

After merge, leave the task worktree, remove it, and fast-forward the dedicated
main checkout. `main` is already checked out at `~/memoria-vault`, so trying to
check it out inside the linked task worktree will fail:

```bash
cd ~/memoria-vault
git worktree remove ~/mv-<session>  # refuses if the task worktree is dirty
git status --short                  # must be empty before resync
git fetch origin
git merge --ff-only origin/main
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
| `lint` | One job for the fast Python checks: `ruff`, `docs-doctor` (docs link text/frontmatter/README), `docs-links` (`docs/` refs under `src/` resolve), `check-test-refs`, `status-doctor` (`docs/` release/test/contributing link/path/flag drift), `agents-doctor` (agent guidance), `github-doctor` (issue-template/dependabot hygiene), `ruleset-doctor` (required-check contract), `test.sh check` (the L0/L1 runner's module paths resolve) |
| `shellcheck (scripts/install.sh)` | Shell lint |
| `PSScriptAnalyzer (scripts/install.ps1)` | PowerShell lint |
| `python-selftest` | the L1 `pytest` suite in `tests/` (vault tooling + repo scripts) |
| `cspell (docs/ + src/ + root markdown)` | Spelling over docs, vault markdown, and root markdown |

**CI invariant:** required-check workflows must have **no** `paths:` filter — a
path-filtered required check permanently blocks PRs that don't touch those
paths. Code-validation checks use
`on: { pull_request:, push: { branches: [main] } }`: unfiltered
`pull_request` reports on every PR, while `push` validates the post-merge state.
Add a `concurrency` group (`cancel-in-progress` except on `main`) so superseded
runs are dropped.

**Exception — `pr-policy`:** `.github/workflows/pr-review-gate.yml` uses
`pull_request_target` rather than `pull_request` because it needs base-repository
write permission to comment and enable auto-merge without checking out PR code.
It remains unfiltered and uses PR-number concurrency, but it does not need a
post-merge `push` run because it classifies PR metadata rather than repository
behavior.

### `pr-policy` tiers

| Decision | Trigger |
|---|---|
| `auto_approve` | Trusted author + all files in safe prose paths (`docs/` except `docs/adr/`, or `_notes/`; `.md`/`.txt` only) |
| `needs_human` | Trusted author on sensitive paths, or untrusted author on safe paths |
| `block` | Untrusted author on sensitive paths |

Sensitive paths: `src/.memoria/`, `scripts/`, `docs/adr/` (the decision record — review-required even though it sits under the otherwise-safe `docs/`), `.github/`, `AGENTS.md`, and agent guidance directories `.agents/`, `.claude/`, `.codex/`, `.kilo/`.
Trusted authors: `eranroseman`, `github-actions[bot]`, `dependabot[bot]`.

On `auto_approve` PRs, the workflow enables squash auto-merge immediately.

---

## Test before opening a PR

- **Shell** (`scripts/install.sh`, `scripts/install/*.sh`): `bash -n scripts/install.sh scripts/install/*.sh` (parse) + an installer `--dry-run` pass when installer behavior changes.
- **Python** (vault tooling + repo scripts): `python -m pytest tests/` (or `scripts/test.sh l1`). The L1 tests live in `tests/`, not inline in the modules (ADR-44).
- **PowerShell** (`scripts/install.ps1`): when `pwsh` is available, run `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error -Settings ./scripts/PSScriptAnalyzerSettings.psd1`; CI enforces it otherwise. `Write-Host` is intentional and excluded via the settings file. Functions must use approved verbs (`Install-`, not `Ensure-`).
- **Installer end-to-end:** `bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test` — never test against the real `~/Memoria`.

---

## Skills

| Stage | Skill | Use when |
|---|---|---|
| Any docs PR | `/docs-review` *(project, when available)* | Before opening — checks quadrant fit, links, indexing, terminology |
| Any PR | `/code-review` *(plugin, when available)* | Before opening — catches bugs and simplification opportunities |
| Deeper review on a dimension | `pr-review-toolkit` agents *(plugin, when available)* | After `/code-review` — probe one lens: `silent-failure-hunter` (error handling), `pr-test-analyzer` (coverage/edge cases), `code-simplifier`, `comment-analyzer`. Conversational — ask for the lens you want |
| Sensitive-path changes | `/security-review` *(plugin, when available)* | PRs touching `scripts/`, `.github/`, `src/.memoria/`, `docs/adr/`, `AGENTS.md`, or agent guidance directories |
| Confirming a fix | `/verify` *(plugin, when available)* | After a change — runs the app to confirm actual behavior |
| New or cut release | `/release` *(project, when available)* | Scaffolds the release folder/plan, milestone (scope), and "Release vX.Y" parent issue with gate/stage sub-issues; release-please owns version/notes |

Skills and plugins are accelerators, not prerequisites. If a named command is
unavailable, perform the equivalent checks directly:

- Docs review: run `python scripts/docs-doctor.py docs`, check links, indexing,
  terminology, and Diátaxis placement.
- Code review: inspect the complete diff for regressions, simplification, error
  handling, and missing tests.
- Security review: trace trust boundaries, secrets, command/input handling,
  network calls, and write scopes; run the relevant security tooling available
  to the agent.
- Verify: reproduce the changed behavior and run the narrow tests plus
  `scripts/test.sh all` when the change warrants the full gate.

Portable, tool-neutral versions of these procedures live in
[`.agents/playbooks/`](.agents/playbooks/) with shared handoff and review
templates under [`.agents/templates/`](.agents/templates/). Cross-cutting
change maps and portable repository skills live under
[`.agents/system/`](.agents/system/) and [`.agents/skills/`](.agents/skills/).
They implement this file's policy; they do not override it.

**Passive, when installed:** the `security-guidance` plugin runs automatic
security scans as you work — a per-edit pattern check plus an LLM review on
`git commit`/`push` (secret leaks, injection, SSRF, weak crypto). It complements
the manual security review and is a first line against the "never commit
`OBSIDIAN_API_KEY`/`.env`" rule. The optional review plugins install from the
`claude-code-plugins` marketplace (`/plugin`).

---

## Platform & runtime facts

- **Hermes config:** consult the local docs at `~/.hermes/hermes-agent/website/docs/`, `cli-config.yaml.example`, and the skills catalogs (`skills-catalog.md`, `optional-skills-catalog.md`) before any Hermes decision. Do not infer from Memoria's existing files — the docs are the source of truth.
- **Line endings:** `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to LF. Working on ext4 avoids CRLF churn.
- **MCP deps:** install into `<vault>/.memoria/.venv`; `mcp_servers` and hooks are wired in `config.yaml` per profile. Hermes never reads a standalone `mcp.json` (ADR-27).
- **Profiles:** `src/.memoria/profiles/memoria-*/` — every profile has
  `SOUL.md`, `config.yaml`, and `distribution.yaml`; profiles with bundled skills
  also have `skills/` (the Engineer intentionally has none). Cron wrappers are
  shared under `src/.memoria/scripts/`, not stored per profile. Keep shared
  profile contracts in sync. No per-profile `mcp.json`.
- **Secrets:** `~/.hermes/profiles/<profile>/.env` and gitignored vault files (shipped as `.example`). Never commit a real key.
- **Build state & gaps:** check open [issues](https://github.com/eranroseman/memoria-vault/issues)
  and the [release index](docs/releasing/README.md), which points to the current
  checkpoint plan, for current blockers and known limitations.

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

- **Links:** `docs/` files → relative links; `src/` (vault-tree) files → absolute website URLs (`https://eranroseman.github.io/memoria-vault/…`).
  - From `docs/`, cross-folder references follow the target's **Pages route**. ADRs (`docs/adr/`) are published, so links to them are ordinary intra-`docs/` relative links. `docs/contributing/`, `docs/releasing/`, and `docs/testing/` are **build-excluded** from the site (see `docs/_config.yml`) — they have no Pages route, so links to them (and to non-doc files under `src/`/`scripts/`) use **GitHub blob URLs** (`https://github.com/eranroseman/memoria-vault/blob/main/…`), same as any other unpublished target.
- **Indexing:** every new page goes in its section README; how-to pages also go in `how-to-guides/README.md`. Assign `nav_order` so the folder reads in logical sequence.
- **How-to titles:** concise, no "How to…" prefix; match the README link text and filename.
- **Citations:** new works go in `reference/bibliography.md` (ACM author-date, `<a id="…"></a>` anchor); link in-text mentions to `[bibliography.md#anchor](../reference/bibliography.md#anchor)`.

### ADR template (`docs/adr/`)

ADRs are the **single home for every decision, at any lifecycle status** — there is no
separate proposals/RFC folder. An open proposal is an ADR with `status: proposed` or
`deferred`; it is revisited each release cycle, never gated on a static adoption
trigger. Full template + nav fields in [`docs/adr/_template.md`](docs/adr/_template.md).

```markdown
---
topic: decisions
id: <NN>
title: <Short title>
status: proposed | accepted | deferred | rejected | superseded
date_proposed: YYYY-MM-DD
date_resolved: YYYY-MM-DD
assumes: []          # ADR/mechanism deps — so a change that invalidates this is detectable
supersedes: []
superseded_by: []
# deferred/proposed ADRs also carry: nav_exclude: true   (unlisted on the site until accepted)
---

# ADR-<NN>: <Title>

## Context
## Decision
## Consequences
## When this matters   # deferred/proposed only — priority context for the cadence review, NOT a gate
## Alternatives considered
```

Background design analysis lives **in the ADR itself** — there is no separate
design-notes folder. A forward-looking or not-yet-built decision is a
`status: deferred` ADR (`nav_exclude: true`) whose Context / Decision /
*When this matters* sections carry the analysis and the revisit triggers.
`docs/` describes only the current system; the decision history lives in the ADRs
(and the full git history). Transient scratch that never graduates to a decision
stays in the gitignored `_notes/`.

### Release plans (`docs/releasing/`)

One folder per version, with a thin `README.md` plus a plan copied from `docs/releasing/release-plan-template.md` — the durable **prose** (what/why, gate rationale). Readiness **state** lives only in the **"Release vX.Y" parent issue and its gate/stage sub-issues**, scope in the milestone + Memoria Issue Tracker Project view, and version/CHANGELOG/Release in release-please — never restated in the plan. `status-doctor` guards the plan against link/path/flag drift. Build gaps go to GitHub issues; scope cuts go to a `deferred`-status ADR in `docs/adr/`. In-work release design notes may live in tracked `docs/releasing/<version>/tmp/` while shaping a release, but they are deleted before that release/checkpoint is done.

---

## Work routing

| Item | Goes to |
|---|---|
| Bug, enhancement, doc fix, question | GitHub issue in Memoria Issue Tracker (Project fields; milestone only if scheduled) |
| Any decision — open proposal *or* closed choice + rationale | ADR in `docs/adr/` (open ones `status: proposed`/`deferred`) |
| Release scope | the GitHub milestone `vX.Y` (assigned issues) + Memoria Issue Tracker view filtered to that milestone |
| Release readiness (gates/stages) | the **"Release vX.Y" parent issue** and its gate/stage sub-issues, *not* the plan §2/§3 |
| Durable analysis behind a decision | the ADR itself (`docs/adr/`; `status: deferred` for forward-looking) |
| In-work release design notes | `docs/releasing/<version>/tmp/` while shaping a release; delete before release/checkpoint completion |
| Transient scratch / personal notes | `_notes/` (gitignored) |

- GitHub Project: "Memoria Issue Tracker" — fields `Status`, `Area`, `Type`, `Priority`; see `docs/contributing/issue-tracking.md`.
- Labels stay minimal: `bug` / `documentation` for repo-wide search plus bot-managed labels (`dependencies`, `python`, `github_actions`, `release`, `autorelease:*`). Type/Area/Status/Priority live in Project fields.
- Milestones are releases. No milestone = unscheduled backlog.
- Never track shared work in `/TODO` or `_notes/` — gitignored and invisible to others.
- Reports: a **durable** analysis behind a decision goes **into the ADR** (`docs/adr/`, `status: deferred` if forward-looking); **in-work release design scratch** goes under that release's tracked `tmp/` folder until the release/checkpoint closes; **transient personal notes** go in `_notes/` (gitignored) — never the repo root.

---

## Merge discipline

- One scope → one branch → one PR → squash-merge → delete. Target ≤1 day or ≤10 commits.
- Rebase onto `origin/main` daily and before every PR: `git fetch && git rebase origin/main`.
- No two branches may implement the same ADR or rewrite the same files.
- Structural/destructive changes (folder moves, deletions, schema bumps) get their own tiny PR, merged first — active branches rebase the same day.
- Stop-check: if `git log -3` shows a co-author who isn't you, you're on someone else's branch — make your own.
