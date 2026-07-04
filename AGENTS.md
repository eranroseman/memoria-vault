# AGENTS.md — working guidelines for AI agents in this repo

For any AI agent (Claude Code, Hermes, etc.) making changes to `eranroseman/memoria-vault`.
Human contributors: see [Contributing to Memoria](CONTRIBUTING.md).

**When presenting options:** give pros/cons and a recommendation for every option — never a bare list.

---

## Working principles

- **Cover the whole scope.** Read, verify, and audit completely — every file and line in scope, no sampling or grep-standing-in-for-a-read. Verify a sub-agent's claimed coverage before reporting done.
- **Zero tolerated contradictions.** Docs must agree with each other and with the implementation — a stale page or a doc describing unbuilt behavior is a defect to fix, not log. Sweep the full surface with [`source-of-truth-map`](.agents/system/source-of-truth-map.md) + [`change-impact-map`](.agents/system/change-impact-map.md); no doc outranks another — research to the true source of truth and fix the stale side. Mirrors are allowed only as consumer views: they must name the owning source, avoid restating more contract detail than the reader needs, and be generated or covered by a drift check whenever they repeat machine-readable contracts (counts, rosters, fields, scopes, commands, lifecycle values, or required checks).
- **Verify hard conclusions independently.** For an uncertain runtime/architecture call, re-diagnose with a fresh agent (prefer two) and live-test the allowed/denied/fail-closed path before declaring done — don't ship solo reasoning. Ground Hermes claims in the `~/.hermes` docs first.
- **Enforcement is a mechanism, not a label.** A boundary is real only where code
  stops the disallowed path — a gate hook, a path glob, profile/dir isolation.
  A classification, config key, or denylist only describes intent until an
  enforcing line rejects the operation.
  - Before relying on a control or simplifying it away, find the enforcing line
    and test the adversarial path.
  - A `disabled_toolsets` entry only hides a tool from the model
    (`registry.dispatch` still runs any registered tool by name); the policy
    plugin's hard-deny is the boundary.
  - An ADR may describe a boundary, but it must name the enforcing mechanism and
    a check that proves it.

---

## ExecPlans — for complex, multi-hour work

For a complex feature, significant refactor, or multi-step migration, work from
an **ExecPlan**: a single, self-contained, living document that carries the task
from research to a validated, observable result so a stateless agent — or a
novice — can run it top to bottom. Author and run it with the
[ExecPlan playbook](.agents/playbooks/exec-plan.md) (skeleton:
[`.agents/templates/exec-plan.md`](.agents/templates/exec-plan.md)).

An ExecPlan is a **working artifact, not a permanent record.** The instance
lives on the `scratch` branch under `releases/<version>/` for the
current release or checkpoint (tracked for handoff, deleted before that release
closes — `_notes/` is gitignored, so a plan meant to be resumed never lives
there); its durable outputs route as usual — decisions to ADRs, readiness/state
to issues.
Tactical sequencing lives in the plan's Execution log; architectural and product
decisions still go to an ADR (§"ADR template") and are linked, never recorded
only in the plan. Skip the ceremony for small, single-sitting changes — use the
[handoff template](.agents/templates/handoff.md) or just make the change.

---

## Where things live

`~/memoria-vault` is the local single source of truth for this repository's
durable source, worktrees, scratch, and test vaults. Do not save those outside it
without explicit permission.

| Piece | Host | Path |
|---|---|---|
| **Project container** (`memoria-vault`) | WSL2 · ext4 | `~/memoria-vault` |
| **Main checkout** (permanent files) | WSL2 · ext4 | `~/memoria-vault/main` |
| **Scratch checkout** (temporary tracked files; linked worktree) | WSL2 · ext4 | `~/memoria-vault/scratch` |
| **Task worktrees** | WSL2 · ext4 | `~/memoria-vault/worktrees/<session>` |
| **Standalone Memoria sandbox** (disposable runtime/test files) | WSL2 · ext4 for development and tests | `~/memoria-vault/sandbox` |
| **Optional adapters** | Same host as the workspace they read | adapter-owned local config, never the baseline source of truth |

- Work **inside WSL2** on ext4 — never `/mnt/c`, never OneDrive.
- Permanent files go in `~/memoria-vault/main`; temporary tracked files go in
  `~/memoria-vault/scratch`; task checkouts go in `~/memoria-vault/worktrees/`;
  disposable test workspaces go in `~/memoria-vault/sandbox`.
- The only nested standalone `.git` expected under this tree is a disposable
  installed vault such as `~/memoria-vault/sandbox/vault`; it is runtime state,
  not repository source.
- Tool caches are not source-of-truth content. Pre-commit, pip, npm, and similar
  disposable caches may live in normal OS cache locations such as
  `~/.cache/pre-commit`; keep them untracked, and only place them under
  `~/memoria-vault/.cache` when a sandbox or local permission rule requires it.
- Alpha.15's required surface is the `memoria` CLI plus the local workspace
  engine. Obsidian, Hermes, MCP, and installed profiles are optional adapter
  concerns only.
- Test only against disposable workspaces under `~/memoria-vault/sandbox`; never use a
  personal workspace as a test target.
- Provider keys and optional adapter secrets live in local, gitignored config or
  environment files (shipped only as `.example` templates). Never print or
  commit them.

---

## 1. Session isolation — git worktree

**Start every session in its own worktree — always, even solo, before you touch a single file.** A worktree gives you a private working tree *and* index, so a concurrent session's staged files can never be swept into your commit.

```bash
git -C ~/memoria-vault/main fetch origin
git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/<session> -b agent/<session> origin/main
cd ~/memoria-vault/worktrees/<session>          # all edits, commits, PRs from here
```

Keep all session worktrees under one parent on ext4 — `~/memoria-vault/worktrees/<session>` — never under `/mnt/c`. The canonical main checkout stays at `~/memoria-vault/main`; `~/memoria-vault/worktrees/` holds task worktrees, so one project container is easy to list and prune.

Prefer a worktree **per branch** even working solo: switching becomes `cd`, and a `reset --hard` in one worktree can't reach another's uncommitted work (§4).

## 2. Branch first — always

**Before you edit, stage, or commit *anything*, create your branch as part of the
`git worktree add -b ...` command in §1.** No change — not even a one-line doc
fix — happens on `main`, on the default/shared checkout, or on another session's
branch. Use a descriptive branch name such as `fix/installer-timeout` in place
of `agent/<session>`; do not create a second branch after entering the worktree.

**Why a worktree, not just a branch:** the index is **shared** across a checkout. In a checkout another agent may be using, `git add <your-file>` stages alongside their already-staged files, and `git commit` captures the **whole** index. Your own worktree has its own index, so this cannot occur. If you ever must share a checkout, run `git diff --cached --name-only` and confirm it lists **only your files** before every commit.

## 3. Stage by explicit path — never `git add -A`

The tree may hold parallel work-in-progress. Stage only what you changed.

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

`main` rejects direct pushes (ruleset GH013). Always open a PR.

```bash
git push -u origin <branch>
gh pr create --base main --fill
gh pr checks <n> --watch
```

Run the merge from the dedicated main checkout, not the task worktree, then
remove the task worktree and fast-forward.

```bash
cd ~/memoria-vault/main
gh pr merge <n> --squash --delete-branch
git worktree remove ~/memoria-vault/worktrees/<session>  # refuses if the task worktree is dirty
git branch -D <branch>              # after verifying the PR is merged; squash merges are not ancestry-merged
git status --short                  # must be empty before resync
git fetch origin
git merge --ff-only origin/main
```

If a PR shows `BEHIND`: `gh pr update-branch <n>` (or `gh api -X PUT repos/eranroseman/memoria-vault/pulls/<n>/update-branch`), then wait for checks to re-run.

**Emergency bypass (policy-code deadlock only):** when a PR changes `.github/scripts/` or `.github/workflows/` AND the `pr_policy.py` code itself, temporarily disable "Require a pull request" and "Require status checks" in Settings → Rules → Rulesets → "main", push directly to main, then re-enable both. For policy-code fixes only.

---

## Scratch branch flow

`scratch/` is ephemeral working material and lives on the dedicated orphan
`scratch` branch, not on `main`. The branch's tracked tree contains only
`releases/`, `workflow-audit/`, and other scratch-only roots; it does not carry the repository source tree. Authorized
contributors with repository write access may push scratch-only commits directly
to that branch; no PR or required CI is expected there.

Locally, `~/memoria-vault/scratch` is the locked linked worktree for the
`scratch` branch, owned by `~/memoria-vault/main`. Do not replace it with a
second clone or standalone `.git`; hooks stay disabled there via
`~/memoria-vault/.cache/git-hooks-disabled`.

For scratch-only work, use a reusable scratch worktree and push directly to the
shared remote branch. This path intentionally has **no PR** and no required CI.

```bash
cd ~/memoria-vault/scratch
git pull --ff-only origin scratch
# edit scratch branch files only, such as releases/<version>/...
git add releases/<path>
git commit -m "scratch: <short description>"
git push origin HEAD:scratch
```

Run repo audits and implementation analysis from a worktree of the code branch
under review (`main` by default), never from the scratch worktree. The scratch
worktree has no tracked `.agents/`, `.github/`, `docs/`, `scripts/`, `src/`,
`tests/`, or `vault-template/` tree to analyze.

Never merge the `scratch` branch into `main`. Promote durable content by copying
it into `docs/`, `docs/adr/`, issues, or release notes on a normal `main` PR.
The `pr-policy` check blocks `scratch/` paths in PRs targeting `main`.

---

## Required CI checks

All must pass before merge.

The check-name roster is owned by
[`.github/ruleset-contract.yaml`](.github/ruleset-contract.yaml). This table is
a reader mirror guarded by `python scripts/agents_doctor.py`.

| Check | Validates |
|---|---|
| `pr-policy` | Three-tier PR policy: auto-approve docs-only, flag sensitive paths, block untrusted |
| `lint` | Runs `scripts/test.sh l0`: `ruff`, `ruff format --check`, `docs-doctor` (docs link text/frontmatter/README plus `vault-template/` docs refs), `status-doctor` (release/test/contributor link/path drift), `agents-doctor` (agent guidance), `github-doctor` (issue-template/dependabot hygiene), `ruleset-doctor` (required-check contract), syntax checks, generated-reference checks, and schema/design drift checks |
| `shellcheck (scripts/install.sh)` | Shell lint |
| `PSScriptAnalyzer (scripts/install.ps1)` | PowerShell lint |
| `python-selftest` | the L1 `pytest` suite in `tests/` (vault tooling + repo scripts) |
| `cspell` | Spelling over tracked prose markdown; scope and exclusions live in `cspell.json` |
| `lint-config` | YAML, GitHub Actions workflow, and authored JSON syntax |
| `markdownlint` | Structural Markdown rendering rules over `docs/` |

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

This reader mirror is owned by `.github/scripts/pr_policy.py` and covered by
`tests/test_pr_policy.py`.

| Decision | Trigger |
|---|---|
| `auto_approve` | Trusted author + all files in safe prose paths (`docs/` except `docs/adr/`, or `_notes/`; `.md`/`.txt` only) |
| `needs_human` | Manual merge required: trusted author on sensitive paths, untrusted author on safe paths, draft PRs, or application/unclassified paths. This classification disables auto-merge; it is not a GitHub approval gate by itself. |
| `block` | Untrusted author on sensitive paths, or any PR that includes `scratch/` paths |

Sensitive paths: `.github/`, `.agents/`, `.claude/`, `.codex/`, `.kilo/`,
`scripts/`, `src/memoria_vault/runtime/policy/`,
`src/memoria_vault/runtime/subsystems/`, `vault-template/.memoria/`,
`docs/adr/` (the decision record — review-required even though it sits under
the otherwise-safe docs tree), and `AGENTS.md`.
Trusted authors: `eranroseman`, `github-actions[bot]`, `dependabot[bot]`.

On `auto_approve` PRs, the workflow enables squash auto-merge immediately. On
`needs_human` PRs, the check passes but leaves merge timing and review judgment
to the maintainer.

---

## Python style

**Docstrings** — module docstrings are mandatory; function/class docstrings are
judgment-based:

- Every module gets a docstring. One line is enough; name the file's role and reference an ADR when one governs it.
- Functions and classes get a docstring only when the name and signature don't tell the full story — a non-obvious invariant, a surprising side-effect, or a constraint the caller must know. If removing the docstring would leave a reader confused, write one; otherwise omit it.

No Args:/Returns:/Raises: sections. If the parameter contract needs prose, the function is too complex — split it first.

`D` (pydocstyle) rules are deliberately off in ruff (`pyproject.toml`).
Function/class docstring presence is a judgment call, not a lint gate.

**Inline comments** — write a comment only when the WHY is non-obvious:

- A hidden constraint or domain invariant (a threshold calibrated against real data, a penalty formula, an ordering that must not change)
- A workaround for an external system quirk (API idiosyncrasy, platform difference, known bug)
- A one-shot or ordering invariant that would surprise a reader (e.g. `pop()` vs `get()` for single-use semantics)
- A security or safety reason behind an otherwise-odd choice

Don't explain what the code does — well-named identifiers already do that. Don't reference the task, PR, or caller ("added for X", "used by Y").

Every `# noqa` suppression must have a rationale on the same line: `# noqa: BLE001 -- config load with import-inside-try; degrade to default`.

**Line length** — 100 characters (`ruff format`, `pyproject.toml`). The formatter owns layout; don't fight it.

---

## Test before opening a PR

- **Shell** (`scripts/install.sh`, `scripts/install/*.sh`): `bash -n scripts/install.sh scripts/install/*.sh` (parse) + an installer `--dry-run` pass when installer behavior changes.
- **Python** (vault tooling + repo scripts): `python -m pytest tests/` (or `scripts/test.sh l1`). The L1 tests live in `tests/`, not inline in the modules.
- **Standard PR verification:** `scripts/verify pr` runs the source checks (`scripts/test.sh all`) and writes a JSON evidence bundle. Use `scripts/verify package` for changes that affect the shipped vault, installer skeleton, hooks, plugins, or workflow replay; `scripts/verify runtime` / `scripts/verify rc` add the opt-in local runtime smoke (standalone `memoria` CLI/worker/gate pytest replay) when prerequisites are available.
- **PowerShell** (`scripts/install.ps1`): when `pwsh` is available, run `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error -Settings ./scripts/PSScriptAnalyzerSettings.psd1`; CI enforces it otherwise. `Write-Host` is intentional and excluded via the settings file. Functions must use approved verbs (`Install-`, not `Ensure-`).
- **Installer end-to-end:** `bash scripts/install-test-vault-local-llm.sh --root ~/memoria-vault/sandbox` — never test against the real `~/Memoria`.

---

## Skills

| Stage | Skill | Use when |
|---|---|---|
| Whole-docs audit | [`docs-audit`](.agents/playbooks/docs-audit.md) *(portable playbook)* | Fresh Diátaxis, consistency, generated-reference, terminology, coverage, and live-link audit across `docs/` |
| Any docs PR | `/docs-review` *(project, when available)* | Before opening — checks quadrant fit, links, indexing, terminology |
| Any PR | `/code-review` *(plugin, when available)* | Before opening — catches bugs and simplification opportunities |
| Deeper review on a dimension | `pr-review-toolkit` agents *(plugin, when available)* | After `/code-review` — probe one lens: `silent-failure-hunter` (error handling), `pr-test-analyzer` (coverage/edge cases), `code-simplifier`, `comment-analyzer`. Conversational — ask for the lens you want |
| Sensitive-path changes | `/security-review` *(plugin, when available)* | PRs touching `scripts/`, `.github/`, `vault-template/.memoria/`, `docs/adr/`, `AGENTS.md`, or agent guidance directories |
| Confirming a fix | `/verify` *(plugin, when available)* | After a change — runs the app to confirm actual behavior |
| New or cut release | `/release` *(project, when available)* | Scaffolds the release folder/plan, milestone (scope), and "Release <version>" parent issue with readiness/stage sub-issues; release-please owns version/notes |

Skills and plugins are accelerators, not prerequisites. If a named command is
unavailable, use the matching portable playbook under
[`.agents/playbooks/`](.agents/playbooks/) and the checks in
[`.agents/system/`](.agents/system/). They implement this file's policy; they do
not override it.

**Passive, when installed:** the `security-guidance` plugin runs automatic
security scans as you work — a per-edit pattern check plus an LLM review on
`git commit`/`push` (secret leaks, injection, SSRF, weak crypto). It complements
the manual security review and is a first line against the "never commit
`OBSIDIAN_API_KEY`/`.env`" rule. The optional review plugins install from the
`claude-code-plugins` marketplace (`/plugin`).

---

## Platform & runtime facts

- **Standalone baseline:** alpha.15 is a local `memoria` CLI/runtime workspace.
  Hermes, Obsidian, Zotero live APIs, installed profiles, and external adapter
  APIs are optional edges, not required product dependencies.
- **Hermes adapter decisions:** if a future optional Hermes adapter is discussed,
  consult the local docs at `~/.hermes/hermes-agent/website/docs/`,
  `cli-config.yaml.example`, and the skills catalogs before making claims. Do
  not infer Hermes behavior from Memoria's old files.
- **Line endings:** `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to LF. Working on ext4 avoids CRLF churn.
- **Runtime deps:** install into `<workspace>/.memoria/.venv` from
  `pyproject.toml`; the runtime package owns policy hooks, worker operations, and
  deterministic subsystems.
- **Scheduled wrappers:** shared wrappers live under
  `vault-template/.memoria/scripts/` and call the CLI/runtime package. A local
  scheduler may invoke them, but no scheduler is required for one-shot CLI use.
- **Build state & gaps:** check open [issues](https://github.com/eranroseman/memoria-vault/issues)
  and [milestones](https://github.com/eranroseman/memoria-vault/milestones) for
  current blockers, checkpoint scope, and known limitations.

### Searching the codebase (qmd)

The repo carries an optional **project-local qmd index** (`./.qmd/`, gitignored) for
hybrid keyword+semantic code search — separate from the runtime/vault qmd, and indexing
this repo only. Set it up once with `bash scripts/dev-setup.sh` (or `npm install &&
bash scripts/qmd-codebase-index.sh`); needs Node ≥22.

- **Keyword:** `npx qmd search "<terms>"` — BM25, instant, no models.
- **Semantic:** `npx qmd query "<intent>"` — needs vectors first: `bash scripts/qmd-codebase-index.sh --embed`.
- **Open a hit:** `npx qmd get <file>`.
- **Rebuild after large changes:** `bash scripts/qmd-codebase-index.sh --embed`.
- **Auto-refresh (optional):** `bash scripts/qmd-install-hooks.sh` (or `dev-setup.sh --with-hooks`)
  wires git hooks that refresh the index after commits/merges/branch switches — non-blocking,
  and a no-op until the index exists. Remove with `bash scripts/qmd-install-hooks.sh --uninstall`.

GPU is auto-detected (leave `QMD_LLAMA_GPU` unset). On WSL/Linux with an NVIDIA card,
semantic search needs the CUDA 13 runtime (`libcudart.so.13` + `libcublas.so.13`);
without it qmd falls back to CPU (slower, still works).

---

## Writing docs

### Documentation routing

| Section | Folder | Answers |
|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" |
| How-to | `docs/how-to-guides/` | "How do I accomplish X?" |
| Reference | `docs/reference/` | "What is the exact value/command?" |
| Explanation | `docs/explanation/` | "How does this part of the system work?" |
| Design Book | `docs/design/` | "Why is it designed this way?" |

Mixed-purpose pages are wrong — split them.

- **Links:** `docs/` files → relative links; `vault-template/` files → absolute website URLs (`https://eranroseman.github.io/memoria-vault/…`).
  - From `docs/`, cross-folder references follow the target's **Pages route**. ADRs (`docs/adr/`) are published, so links to them are ordinary intra-`docs/` relative links. Root files such as `CONTRIBUTING.md`, agent playbooks, and other unpublished targets use **GitHub blob URLs** (`https://github.com/eranroseman/memoria-vault/blob/main/…`).
  - Never relative-link into `src/` from a published page — those paths 404 on the site. Cite a source file as an **inline-code path** (`` `vault-template/.memoria/…` ``), or an absolute tag-pinned `blob/<tag>/…` URL only when a click genuinely adds value.
  - **ADR references** belong only in **explanation** prose (inline, or an optional per-page footer "Decisions" list), always as **title-text links** — never bare `(ADR-NN)` codes, and not in tutorial / how-to / reference body text.
- **Indexing:** every new page goes in its section README; how-to pages also go in `how-to-guides/README.md`. Assign `nav_order` so the folder reads in logical sequence.
- **How-to titles:** concise, no "How to…" prefix; match the README link text and filename.
- **Citations:** new works go in `reference/bibliography.md` (ACM author-date, `<a id="…"></a>` anchor); docs pages link in-text mentions to the published bibliography anchor for their folder depth.
- **Spelling:** American English only — `-ize`/`-or` endings, not `-ise`/`-our` (write "behavior", "normalize"). `cspell` is the gate. Never suppress a flag with an inline `<!-- cspell:words … -->` / `<!-- cspell:ignore … -->` tag — for each unknown word, either **reword the prose** or, if it's a real term (proper noun, tool name, code token, jargon), **add it to `project-words.txt`** (one lowercase word per line, sorted; a lowercase entry matches every casing).

### ADR template (`docs/adr/`)

ADRs are the **single home for every live decision** — there is no separate
proposals/RFC folder. An open proposal is an ADR with `status: proposed`; accepted
future direction is `status: accepted` even when implementation is later; a
considered-and-declined option is `status: rejected`. There is no `superseded`
status: a replaced decision's ADR is **deleted** so only live decisions sit on
`main`. Its successor records what it absorbed via `supersedes:` and prose; the
original — with its `superseded_by`/`supersedes` lineage — stays recoverable in git
history for later investigation.
Scheduling and readiness live in GitHub issues, not ADR status. Every proposed ADR
gets a linked GitHub issue in the Memoria Issue Tracker, normally `Status: Backlog`
and `Readiness: Needs shaping`; when a decision is accepted and implemented, its
implementation issue is closed `Done`, or a separate implementation issue remains
open with the correct Readiness. Full template + nav fields in
[`docs/adr/_template.md`](docs/adr/_template.md).

```markdown
---
topic: decisions
id: <NN>
title: <Short title>
status: proposed | accepted | rejected
date_proposed: YYYY-MM-DD
date_resolved: YYYY-MM-DD
assumes: []          # ADR/mechanism deps — so a change that invalidates this is detectable
supersedes: []
superseded_by: []
# proposed ADRs also carry: nav_exclude: true   (unlisted on the site until accepted)
---

# ADR-<NN>: <Title>

## Context
## Decision
## Consequences
## When this matters   # proposed only — priority context for the cadence review, NOT a gate
## Alternatives considered
```

Background design analysis lives **in the ADR itself** — there is no separate
design-notes folder. Forward-looking work uses `status: proposed` until the
decision is made; once the choice is made, the ADR becomes `accepted` even if the
implementation issue has Readiness `Later`. `docs/` describes only the current
system; the decision history lives in the ADRs (and the full git history).
Transient scratch that never graduates to a decision stays in the gitignored
`_notes/`.

### Release process

Release scope lives in the GitHub milestone and Memoria Issue Tracker project view.
Readiness lives only in the **"Release <version>" parent issue and its readiness/stage
sub-issues**. Version, changelog, tag, and GitHub Release are owned by
release-please. Use the portable [release playbook](.agents/playbooks/release.md)
and [release plan template](.agents/templates/release-plan.md) to draft issue
prose; do not create a repository release-plan folder.

---

## Work routing

| Item | Goes to |
|---|---|
| Complex feature, refactor, or migration (multi-hour) | An [ExecPlan](.agents/playbooks/exec-plan.md) working doc on the `scratch` branch in `releases/<version>/` (deleted before the release closes); its decisions still go to ADRs, state to issues |
| Bug, enhancement, doc fix, question | GitHub issue in Memoria Issue Tracker (Project fields; milestone only if scheduled) |
| Any decision — open proposal *or* closed choice + rationale | ADR in `docs/adr/` (open ones `status: proposed`) |
| Release scope | the GitHub milestone named for the SemVer version, such as `0.1.0` or `0.1.0-alpha.11`, plus Memoria Issue Tracker view filtered to that milestone |
| Release readiness | the **"Release <version>" parent issue** and its readiness/stage sub-issues, not markdown plan sections |
| Durable analysis behind a decision | the ADR itself (`docs/adr/`; `status: proposed` until decided) |
| Transient scratch / personal notes | `_notes/` (gitignored) |

- GitHub Project: "Memoria Issue Tracker" — fields `Status` and `Readiness`; see [CONTRIBUTING.md](CONTRIBUTING.md).
- Labels stay minimal: `bug` / `documentation` for repo-wide search plus bot-managed labels (`dependencies`, `python`, `github_actions`, `release`, `autorelease:*`). Status and Readiness live in Project fields; release scope lives in milestones.
- Milestones are releases. No milestone = unscheduled backlog.
- ADR/issue alignment: proposed ADRs link open shaping issues; accepted implemented
  ADRs link closed `Done` issues or an explicit open implementation issue; superseded
  ADR bundles link their replacement ADRs and close any replaced umbrella issues.
- Never track shared work in `/TODO` or `_notes/` — gitignored and invisible to others.

---

## Merge discipline

- One scope → one branch → one PR → squash-merge → delete. Target ≤1 day or ≤10 commits.
- Rebase onto `origin/main` daily and before every PR: `git fetch && git rebase origin/main`.
- No two branches may implement the same ADR or rewrite the same files.
- Structural/destructive changes (folder moves, deletions, schema bumps) get their own tiny PR, merged first — active branches rebase the same day.
- Stop-check: if `git log -3` shows a co-author who isn't you, you're on someone else's branch — make your own.
