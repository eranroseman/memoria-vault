# AGENTS.md — working guidelines for AI agents in this repo

Conventions for any AI agent (Claude Code, Hermes, etc.) making changes to
`eranroseman/memoria-vault`. Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

This file encodes hazards learned the hard way. Following it avoids the failure
modes that bite agents here: **concurrent sessions** sharing one working tree, the
**auto-commit hook** entangling your work, **branch protection** rejecting direct
pushes, and the **Windows ↔ WSL2 split** the project runs across.

**One principle above all the mechanics below: decide for the best long-term
solution, not the least work.** At every design choice, weigh the options by what is
correct and maintainable for the long run — never pick the one that just minimizes
your own effort. "That breaks N references," "the current pattern is X," or "it's more
files to touch" are mechanics to handle, not reasons to settle for a worse design. If
the better solution costs an hour now, spend it; surface the trade-off and your
recommendation rather than quietly defaulting to the cheap path.

**When you present options to the human, give the pros and cons of each** — never a
bare list of choices. Spell out the trade-offs (cost, risk, reversibility, long-term
fit) for every option, and say which you recommend and why, so the decision is informed
rather than handed back undifferentiated.

---

## Where things live

The project spans two hosts. Know which side you're on before you touch anything.

| Piece | Host | Path | Who works here |
| --- | --- | --- | --- |
| **This dev repo** (`memoria-vault`) | **WSL2** · ext4 | e.g. `~/memoria-vault` | VSCode (Remote-WSL), git, **agents** |
| **Hermes runtime** | **WSL2** · Linux | `~/.hermes/` — profiles, config, MCP venv | the agent runtime |
| **Obsidian + runtime vault** | **Windows** | `~/Memoria` (the installed artifact) | the human, in the Obsidian GUI |

- You work **inside WSL2** on the ext4 copy of this repo — never `/mnt/c`, never OneDrive.
- **Obsidian stays on Windows** and opens the *runtime* vault (`~/Memoria`), **never this dev repo**.
- **Integration boundary.** WSL2-Hermes reaches Windows-Obsidian through the Obsidian
  **Local REST API** at `https://127.0.0.1:27124`. That works only with WSL2
  **mirrored networking** — set `networkingMode=mirrored` in `%UserProfile%\.wslconfig`,
  then `wsl --shutdown` — so both sides share `127.0.0.1`. Without it, Hermes gets
  `HTTP 000`. Use the bare `…:27124/` REST endpoint, not `…/mcp/`; the API key lives in
  the Obsidian plugin's `data.json` (never print or commit it).

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
so parallel sessions can't trample each other:

```bash
# one-time per session, on the WSL2 ext4 filesystem (NOT /mnt/c):
git worktree add ~/mv-<session> -b agent/<session> origin/main
cd ~/mv-<session>          # do ALL your work here
# ... branch, edit, commit, PR from here ...
git worktree remove ~/mv-<session>   # when done (or leave it for next time)
```

Keep worktrees on **ext4** (`~/…`), never under `/mnt/c`: Windows-mounted paths are
slow and break git's permission/inode assumptions. `core.hooksPath` and
`.gitattributes` are inherited, so the pre-commit guard and LF rules apply in the
worktree too.

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
(`~/Memoria` on Windows), where auto-backup is a wanted feature. It turns hostile
only if someone **opens a checkout of this dev repo as an Obsidian vault** (e.g.
points Windows-Obsidian at a `\\wsl$\…\memoria-vault` path) — then the timer
auto-commits the entire source tree (`scripts/install.sh`, `project-files/`, `docs/`…),
bundling your in-progress edits with unrelated work and sometimes spawning phantom
branches that orphan work.

**Two defenses:**

1. **Never open this dev repo as an Obsidian vault.** Edit it in VSCode (Remote-WSL);
   Obsidian opens only the *runtime* vault (`~/Memoria`).
2. **Always create your own branch before editing** (above). A dedicated branch
   keeps your change isolated and reviewable even if a stray auto-commit fires.

Do **not** "fix" this by editing the shipped `data.json` — it is correct for
deployment (see `docs/reference/obsidian-plugins.md`); the problem is *where*
Obsidian is pointed, not the config.

## 2. Stage by explicit path — never `git add -A`

The working tree may hold the user's parallel work-in-progress or hook-generated
churn. Stage only the files you changed:

```bash
git add scripts/install.sh                      # yes — explicit
git add project-files/decisions/24-*.md # yes
git add -A                              # NO — sweeps in others' work
```

If you find unmerged work you didn't author tangled into a branch (new ADRs,
renames, a stash), **preserve it** (back it up / leave the stash) and surface it
to the user. Never delete a branch or stash that holds work you didn't create
without confirming its content is already on `main`.

## 3. `main` is protected by a ruleset — use the PR flow

Direct `git push origin main` is **rejected** by a repository ruleset (`GH013`:
"Changes must be made through a pull request" + required status checks). The flow is:

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

**Emergency bypass (deadlock only):** when a PR touches `.github/scripts/` or
`.github/workflows/` AND changes the `pr_policy.py` policy code itself, a circular
dependency exists — `pr-policy` blocks changes to the policy. Temporarily disable
the ruleset's **"Require a pull request before merging"** and **"Require status
checks to pass"** restrictions, push the fix to main directly, then re-enable both.
This is for policy-code fixes only — never for regular changes.

## 4. Required status checks

These checks are **required** by the ruleset and must all pass:

| Check | Runs |
| --- | --- |
| `pr-policy` | three-tier gate: auto-approves docs-only PRs, blocks untrusted sensitive-path changes, flags everything else for human review (see below) |
| `docs-doctor` | structural lint of `docs/` + `vault/` link text (broken links/anchors, README presence, frontmatter keys, link text = page title) |
| `shellcheck (scripts/install.sh)` | shell lint |
| `PSScriptAnalyzer (scripts/install.ps1)` | PowerShell lint |
| `python-selftest` | `--self-test` of the vault Python tooling (policy gate, board export, metrics, detectors) |
| `docs-links` | every `docs/` reference under `vault/` resolves (Pages URLs map to a real doc; no banned blob URLs) — `scripts/check-vault-links.sh` |

**CI invariant — do not break this:** a workflow that backs a *required* status
check must **not** have a `paths:` filter. A path-filtered required check never
reports on PRs that don't touch those paths, leaving them permanently `BLOCKED`.
Both `docs-doctor.yml` and `lint-installers.yml` therefore run on every push/PR
unconditionally. If you add a new required check, follow the same rule.

**Linter notes:** `scripts/install.ps1` is an interactive installer, so `Write-Host` is
intentional and excluded via `scripts/PSScriptAnalyzerSettings.psd1`; PowerShell
functions must use approved verbs (`Install-`, not `Ensure-`).

### PR gate policy — how `pr-policy` decides

The `pr-policy` check (`pr-review-gate.yml` + `pr_policy.py`) implements a
three-tier gate based on path sensitivity and author trust:

| Decision | Trigger | Effect |
|---|---|---|
| `auto_approve` | Trusted author + all files in safe paths (`docs/`, `project-files/releases/`, `project-files/proposals/`; `.md`, `.txt` suffixes) | Enables squash auto-merge **after Kilo Code Review passes clean** (see below) |
| `needs_human` | Safe paths but untrusted author, OR trusted author on sensitive paths (`vault/.memoria/`, `scripts/`, `project-files/decisions/`, `.github/`) | Check passes — human reviews and merges manually |
| `block` | Untrusted author touching sensitive paths | Check fails — merge impossible |

**Trusted authors:** `eranroseman`, `github-actions[bot]`.

**Kilo Code Review integration:** on `auto_approve` PRs, the workflow polls the
`Kilo Code Review` cloud check for up to 12 minutes. If the review finds warnings
or above (based on the configured threshold at `app.kilo.ai/code-reviews`),
`pr-policy` fails and blocks the merge. Clean reviews allow auto-merge to proceed.

Kilo Code Reviews is configured at `app.kilo.ai/code-reviews`:
- Model: Claude Sonnet 4.5, style: Balanced, focus: security / bugs / documentation
- Threshold: Warnings and above
- Markdown review: enabled
- Custom instructions tuned to this repo's conventions (Diátaxis, terminology,
  profile sync, ADR format, indexing rules)

**Ruleset configuration** (`Settings → Rules → Rulesets → "main"`):
- Required checks (6): `pr-policy`, `docs-doctor`, `docs-links`, `python-selftest`,
  `shellcheck (scripts/install.sh)`, `PSScriptAnalyzer (scripts/install.ps1)`
- "Require a pull request before merging": ON
- "Require status checks to pass": ON
- Approving reviews: NOT required (sole maintainer cannot self-approve)

## 5. Test before you commit

Every installer bug in this repo's history was caught by *running* the code, not
reading it. Before opening a PR:

- **Shell** (`scripts/install.sh`): `bash -n scripts/install.sh` (parse) + a `--dry-run` pass.
- **PowerShell** (`scripts/install.ps1`): the CI **`PSScriptAnalyzer`** check is the gate —
  a WSL2 agent usually has no `pwsh`, so lean on CI but still read the script when you
  change its logic.
- **Python** (`.memoria/mcp/*.py`, `detectors.py`): run `--self-test`
  (`policy_mcp.py`, `policy_hook.py`, `board_export.py`, `metrics_aggregate.py`,
  `detectors.py` all support it).
- **Installer end-to-end:** deploy into a *throwaway* vault
  (`bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test`), verify, then clean
  up — never test against the real `~/Memoria`.

## 6. Runtime / platform facts

- **Check the official Hermes resources before ANY Hermes decision.** No choice about
  Hermes config, skills, profiles, hooks, MCP, or runtime is made without first
  consulting the authoritative sources — the local docs (`~/.hermes/hermes-agent/website/docs/`),
  `cli-config.yaml.example`, and the bundled + optional **skills catalogs**
  (`skills-catalog.md` and `optional-skills-catalog.md`, in the `reference/` folder of
  the Hermes docs above — **not** Memoria's `docs/`). Do **not** guess
  where Hermes reads config or infer it from Memoria's existing files — Memoria has
  repeatedly mis-guessed (mcp.json never loaded; per-profile `.env`; the `obsidian.*`
  fullmatch; `ocr-and-documents`/`github-repo-management` are official *bundled* skills,
  not missing). The docs are the source of truth; verify against them, then decide.
- The dev repo and the **Hermes runtime both run in WSL2** (Linux); you edit and run
  everything from the WSL2 side (VSCode Remote-WSL). **Obsidian and the runtime vault
  stay on Windows** — see *Where things live*.
- **`scripts/install.ps1` is the end-user Windows launcher**: it `wslpath`-converts the
  Windows vault path and hands off to `scripts/install.sh` inside WSL2. For dev work, run
  `scripts/install.sh` directly in WSL2; you rarely touch `scripts/install.ps1` except to lint it.
- **Line endings:** `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to **LF**
  (a CRLF in `scripts/install.sh` breaks the WSL2 shebang). Never override it — working on
  ext4 in WSL2 avoids the CRLF churn that `/mnt/c` + Windows editors introduce.
- **Obsidian REST bridge** (integration work): needs WSL2 `networkingMode=mirrored`
  for `https://127.0.0.1:27124` to resolve across the boundary — full setup in
  *Where things live*.
- MCP deps install into a vault-local venv (`<vault>/.memoria/.venv`); the installer
  wires that interpreter into each profile's `config.yaml` (`mcp_servers` + hooks live
  there — Hermes never reads a standalone `mcp.json`; ADR-27).
- Secrets live only in `~/.hermes/profiles/<profile>/.env` and gitignored vault
  files (shipped as `.example`). **Never** commit a real key; if one leaks, rotate it.
- **Build state & known gaps:** before relying on live agent writes, consult the
  open [issues](https://github.com/eranroseman/memoria-vault/issues) (build gaps) and
  the [v0.1 release plan](project-files/releases/v0.1/release-plan-v0.1.md) (gates,
  blockers, known limitations) rather than any list restated here. (#39/#51/#58 are
  closed — ADR-27 made the review gate enforce live in all run modes; obsidian is each
  lane's only write path.)

## 7. Profiles and the vault

- Agent profiles live under `vault/.memoria/profiles/memoria-*/` and follow the
  `SOUL.md` / `config.yaml` / `distribution.yaml` structure (+ `cron/`, `skills/`).
  Keep the seven in sync. There is no per-profile `mcp.json` — `config.yaml` carries
  `mcp_servers` (ADR-27).
- Authoritative design is in `docs/` (Diátaxis) and `project-files/decisions/`
  (ADRs); current build state is tracked in the open issues + the
  [v0.1 release plan](project-files/releases/v0.1/release-plan-v0.1.md).
- **Generated reports go in `_reports/`, never the tracked tree.** Analysis,
  findings, and distillation reports you produce belong in `_reports/` at the repo
  root — a gitignored scratch dir (alongside `_notes/`, `_papers/`). Don't write a
  report to the repo root or into `project-files/`: those are canon, `_reports/` is
  scratch. Once its findings are integrated into docs/ADRs/proposals, the report has
  served its purpose. Treat nothing under `_reports/` / `_notes/` as canon.

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

**Indexing & ordering.** Every new page must be added to its section README — and, if it's a how-to, to the guide map in `how-to-guides/README.md` too (keep that map complete). New subsections need a `README.md` with `parent`, `has_children: true`, and an explicit `permalink`. Section READMEs are **navigation hubs**: a brief intro + a described child table + an optional "where to go next" — not article-length prose (that belongs in the child pages). Give every page a `nav_order` so each folder reads top-to-bottom in a logical sequence, and keep the README child-table order matching that sidebar order. How-to page titles are **concise** (no "How to …" prefix) and match their README link text and filename.

**Adding a citation to `reference/bibliography.md`.** When a doc cites a new work, add its ACM author-date entry with an `<a id="…"></a>` anchor and link the in-text mention to `[bibliography.md#anchor](../reference/bibliography.md#anchor)` (relative path from the citing file).

### Terminology — name the two flows correctly

Memoria's **knowledge cycle** has two flows: **Compile** (knowledge *in* — sources are found, captured, enriched, classified, distilled, and connected into claims) and **Compose** (knowledge *out* — claims are assessed, framed, drafted, verified, and exported). "Compile" is deliberate: it echoes the *compiled memory* thesis (Karpathy's LLM-wiki) the design is built on. Each flow has one reflective phase the human engages by judgment — `discuss` (Compile) and `sketch` (Compose) — not optional extras but where the method's thinking happens.

- **Never** name these the "upstream/downstream pipeline" or "the two pipelines" — that naming was retired (see [compile-and-compose.md](docs/explanation/workflows/compile-and-compose.md)). Use **Compile flow** / **Compose flow**, or **the knowledge cycle** for the pair.
- `pipeline`, `upstream`, `downstream` stay fine in *other* senses — the ingest pipeline, a Pandoc/export pipeline, an upstream dependency, a downstream consumer. The rule is narrow: don't use them to name the two flows.

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

### `project-files/proposals/` — RFC template

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

### `project-files/releases/` — release-plan template

One **single-file release plan per version**, structured by what a release needs.
Full skeleton: `project-files/releases/release-plan-template.md` (copy it per
release; reset every Gate/Tier State to `todo`).

```markdown
---
release: vX.Y.Z
status: draft        # draft | candidate | released
released: false      # cut-flag; true only when every gate is `done`
---
# Release plan — vX.Y.Z
## 1. Scope   ## 2. Gates (G# state)   ## 3. Tiers (T# state)   ## 4. Blockers
## 5. Deferred   ## 6. Known limitations   ## 7. Cut procedure   ## 8. Roadmap   ## 9. Appendix
```

**Single source of state — prevents drift.** Gate/tier state lives ONLY in §2/§3 of
the release-plan file; build *gaps* are GitHub issues; scope *cuts* are proposals.
Every other doc *points* — never restates. Detail too long for a crisp plan (full
phase steps, investigation notes) goes to a sibling `release-plan-<version>-appendix.md`.

The current release plan is [`release-plan-v0.1.md`](project-files/releases/v0.1/release-plan-v0.1.md)
(+ its `-appendix.md`).

## 9. Integration cadence — merge small, merge often

The expensive failures here are not bad merges — they're *late* merges. Three
branches once grew off a frozen `main` in parallel (60 + 9 + 12 commits, none
merged back), all touching the same ADR and files — ADR-27 was implemented
*twice* — so consolidating them became a ~30-conflict semantic reconciliation,
not a merge. Full post-mortem + human walkthrough:
[git-workflow.md](project-files/git-workflow.md). The rules:

- **Keep `main` moving.** A branch is one coherent unit → PR → squash-merge →
  delete. If it passes ~1 day or ~10 unmerged commits, it's already too big —
  split it and land it. Never let a branch hoard weeks of sweeping work.
- **Rebase onto `origin/main` constantly** — daily and before every PR
  (`git fetch && git rebase origin/main`). A branch cut from a stale base and
  never updated is the divergence engine.
- **One scope → one branch → one owner, claimed up front.** No two branches may
  implement the same ADR or rewrite the same files. (ADR-27 built on two branches
  was the single most expensive collision in this repo.)
- **Land structural/destructive changes FIRST, alone, fast.** Folder moves, file
  deletions, schema bumps get their own tiny PR, merged immediately and announced;
  every active branch rebases to absorb them the same day. A deletion that lives
  only on a side branch resurrects the file when another branch merges.
- **Serialize when parallel is unavoidable (a merge train).** First branch merges
  to `main`; the rest rebase onto the new `main` immediately, then the next merges.
  Don't grow competing mega-branches.
- **One worktree + one branch per agent session (see §0).** Two engines on one
  branch fuse into an un-sliceable history and race each other's HEAD (we hit
  mis-amends, vanished edits, a file deleted twice). Stop-check: if `git log -3` on
  the tip shows a co-author who isn't you, you're on someone else's branch — make
  your own.

## 10. Tracking work — transient goes to GitHub, durable stays in the repo

One rule resolves where a piece of work lives: **transient, discrete work → GitHub;
durable rationale and state → the repo.** Don't recreate a flat `TODO` brain-dump —
that swamp (release tasks, bugs, research, and ideas in one ungoverned list) is what
this section retires.

**GitHub is the single inbox for actionable work** — every bug, enhancement,
question, or doc fix is an **issue**, never a line in a file.

- **Labels** classify: `bug` / `enhancement` / `documentation` / `question` +
  `research` (open-ended investigation) + priority `P0` / `P1` / `P2`.
- **Milestones are releases** (`v0.1`, `v0.2`, …). *No milestone = unscheduled
  backlog.* Assigning a milestone **is** the act of scheduling — that scoping
  decision is made per release (review ADRs + proposals + docs, then assign), not by
  defaulting everything into the next version.
- **One Project board** (`Inbox → Scheduled → In progress → In review → Done`) is the
  kanban view over the issues — fitting, since the product itself is kanban-driven.
- Issue templates live in `.github/ISSUE_TEMPLATE/` (`bug_report.yml`,
  `feature_request.yml`). A bug report states **Expected / Actual / Vault state**.

**The repo holds only durable artifacts — each with one job, none restating another:**

| Artifact | Holds | Not for |
| --- | --- | --- |
| `project-files/decisions/` (ADR-NN) | *Why* — closed decisions + rationale | open work |
| `project-files/proposals/` (RFC-NN) | Big deferred *ideas* — the strategic backlog | discrete tasks |
| `release-plan-<v>.md` §2/§3 | Gate/tier readiness state | build gaps (→ issues) |
| `_reports/`, `_notes/`, `/TODO` | Gitignored personal scratch | anything canonical or shared |

**Routing a new item:** discrete and actionable → **issue** (label it; milestone only
if scheduled). A big capability worth weighing trade-offs on → **RFC** (it graduates
to issues + a milestone when scheduled). A choice just made → **ADR**. Release
readiness → the **release plan**. A release-blocking issue is linked from the release
plan §4 (Blockers); issues reference the relevant ADR / RFC / gate IDs — keep both directions.

**Never** track shared work in `/TODO` or `_notes/` — they are gitignored scratch and
invisible to everyone else. If you find actionable work there, move it to an issue.
