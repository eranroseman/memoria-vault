# ExecPlan — Adopt `obra/superpowers` as the base agent-skill toolkit

## 0. Metadata

- **Task:** Build one coherent agent-skill toolkit on `obra/superpowers`,
  identical across Claude Code and Codex as far as each tool allows: install
  superpowers + gap-filling plugins, retire what's now redundant, reconcile
  every collision (personal skills, this repo's `.agents/`/`AGENTS.md`), and
  make `AGENTS.md` loadable by both tools.
- **Decisions & rationale:** all in
  [`decisions-adopt-superpowers.md`](decisions-adopt-superpowers.md). This
  file is execution only — commands, exact insert-text, verification.
- **Worktree / branch:** the `~/.claude/` and `~/.codex/` changes are
  per-user tool config, not repo content — no worktree needed. The
  `memoria-vault`-tracked changes (Layer 2/3, step 12) go through the normal
  worktree → branch → PR flow. This plan file lives on the `scratch` branch
  under `scratch/workflow-audit/`.
- **Related issues / milestone:** — (personal tooling + repo-doc
  consistency, not release-scoped).
- **Started:** 2026-07-06 · **Last updated:** 2026-07-07

## 1. Purpose / big picture

Three layers, executed in dependency order (§4):

- **Layer 1 — generic process** (`~/.claude/`, `~/.codex/`): superpowers +
  the gap-filling plugins + the kept personal skills. Cross-tool precedence
  rules live in `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.
- **Layer 2 — repo policy** (`AGENTS.md`, `.agents/`): memoria-vault's own
  conventions, cross-referencing Layer 1 by name, never duplicating it.
- **Layer 3 — discovery** (`main/CLAUDE.md` → `@AGENTS.md`): so Claude Code
  loads `AGENTS.md` (it reads `CLAUDE.md`, not `AGENTS.md`, natively).

Requirements this plan must satisfy (traced in §5):

1. superpowers installed on both tools.
2. Redundant items retired (not just conflict-patched).
3. Claude and Codex end states as close to identical as each tool allows;
   every asymmetry decided, not accidental.
4. Capability gaps superpowers doesn't cover are filled (frontend/UI,
   deep security, technical writing, API design).
5. No contradictory guidance when skills fire together.
6. No plugin or skill component is edited in place — third-party or your own.
7. `AGENTS.md`'s own Skills table names only things that actually exist.
8. Agents use the Memoria Issue Tracker as the work-state loop, not only as an
   output sink: before work, identify the owning issue or explicit exception;
   during/after work, update Project state; close only when resolved,
   obsolete, or fully subsumed.

## 2. Context (facts an executor needs)

- **Claude install shape:** `~/.claude/settings.json` →
  `enabledPlugins["<plugin>@<marketplace>"] = true` +
  `extraKnownMarketplaces["<name>"]`. Marketplace add + install is the
  mechanism (matches existing `ponytail`/`rethink`).
- **Codex install shape:** `~/.codex/config.toml` →
  `[marketplaces.<name>]` + `[plugins."<name>@<name>"]`. `[features]
  multi_agent = true` is already set (needed for
  `dispatching-parallel-agents` / `subagent-driven-development`) — leave it.
- **Loose skills** (no plugin manifest) live directly under
  `~/.claude/skills/<name>/` and `~/.codex/skills/<name>/` and are loaded by
  folder presence. This is the fallback when a source has no `.codex-plugin`
  manifest.
- **Never edit any plugin or skill component in place** — not the marketplace
  plugins (`ponytail`, `rethink`, `superpowers`, `codex-security`,
  `interface-design`, `frontend-design`, `pr-review-toolkit`,
  `security-guidance`), and not the loose vendored/cherry-picked skills either
  (`threat-modeling`, `the-elements-of-style`, `api-design-principles`,
  `obsidian-skills`, and the MIT cherry-picks `grilling` / `caveman` /
  `codebase-design` / `improve`). Editing them isn't *necessary*: every needed
  rule (routing, precedence, exemption) goes in `~/.claude/CLAUDE.md` /
  `~/.codex/AGENTS.md` instead. **This plan edits zero components** — including
  `rethink` (your own published plugin), which is used as-is.
- **Already installed** — Claude: `ponytail`, `rethink`, `pr-review-toolkit`,
  `security-guidance`, `obsidian-skills`, `grilling`, `codebase-design`,
  `improve`, `caveman`, `tdd`, `grill-me`. Codex: `ponytail`, `rethink`,
  `caveman`, `codebase-design`, `grilling`, `improve`, `tdd`. superpowers is
  available on Codex as `superpowers@openai-curated` v5.1.3 (pre-vetted, no
  marketplace-add needed); `codex-security@openai-curated` v0.1.10 and a
  native `security-threat-model` skill (`~/.codex/vendor_imports/skills/
  skills/.curated/security-threat-model`) are also available on Codex.

## 3. Plan of work

§4 is the single authoritative step sequence. Overview:

- **Layer 1 install** (steps 1–8): superpowers, the-elements-of-style,
  api-design-principles, threat-modeling, codex-security, interface-design +
  frontend-design, obsidian-skills.
- **Layer 1 retire** (step 9): retire tdd + grill-me. No component is edited —
  grilling/caveman/improve/rethink are all used as-is; their routing rules go
  in CLAUDE.md/AGENTS.md (steps 10–11).
- **Layer 1 precedence notes** (steps 10–11): `~/.claude/CLAUDE.md`,
  `~/.codex/AGENTS.md` — all cross-skill routing lives here.
- **Layer 2 + 3 repo edits** (step 12): one worktree; no PR until step 14.
  This includes the issue-tracker operating loop and the PR/template/checker
  guardrails that make it hard for agents to over-close issues.
- **Verify** (step 13).
- **Document + merge repo work** (step 14): author `.agents/toolkit.md`, then
  open and merge the single repo PR.

**Parity ledger** (the R3 answer — Claude | Codex):

| Item | Claude | Codex |
|---|---|---|
| superpowers, ponytail, rethink, grilling, caveman, codebase-design, improve | ✓ | ✓ |
| the-elements-of-style | loose vendor | loose vendor |
| api-design-principles | loose vendor | loose vendor |
| obsidian-skills | nested plugin | loose vendor |
| threat-modeling | git clone | git clone (mirrored — same skill) |
| interface-design | plugin install | loose vendor (skill) |
| frontend-design (distinctive UI) | Anthropic plugin | am-will skill + native GPT-5.5 |
| PR review | pr-review-toolkit (6-agent plugin) | native Codex review (6-dim map → stack doc) |
| active security review | security-review playbook + threat-modeling | codex-security + threat-modeling |
| passive always-on security scan | security-guidance (hooks) | — no equivalent (documented) |
| tdd, grill-me | retired | retired / never present |

**Capability-parity** (chosen model): a capability counts as covered on a
tool if a plugin *or* a native feature provides it. Under it, every
capability is covered on both tools **except passive always-on security
scanning** (Claude's `security-guidance` hooks; Codex has no passive
equivalent — active `codex-security` scans instead). Two invocation-surface
differences remain, not capability gaps: interface-design's slash-commands
(Claude-only; Codex runs the review inline) and `frontend-design` being an
Anthropic plugin on Claude vs. a community skill + native model on Codex.
Both tools get the same precedence + vocabulary rules (steps 10–11).

**Declined (never install):** the official Anthropic `code-review`
marketplace plugin; `coderabbit@openai-curated`. **Left unedited** (repo
files with no superpowers overlap): `.agents/playbooks/{design-history,
release}.md`, `.agents/templates/review-report.md`, `.agents/system/*`
(regenerated from `change-impact.yaml`, never hand-edited),
`.agents/skills/{policy-change-review,schema-change}/SKILL.md`.

## 4. Concrete steps

Each step is self-contained: run it with only the text in that step. Steps
are contiguous and run in order.

### Step 1 — Pre-flight: back up, check auth, read cost

Back up everything this plan edits or deletes, so any step is recoverable:

```bash
tar czf ~/toolkit-backup-$(date +%Y%m%d-%H%M%S).tgz \
  ~/.claude/skills ~/.codex/skills ~/.claude/CLAUDE.md ~/.codex/AGENTS.md \
  ~/.claude/settings.json ~/.codex/config.toml \
  || { echo "BACKUP FAILED — stop; do not run any later rm -rf"; exit 1; }
ls -lh ~/toolkit-backup-*.tgz | tail -1
gh auth status || { echo "GH AUTH FAILED — run: gh auth refresh -h github.com"; exit 1; }
```

Then add the marketplace and read the cost:

```bash
claude plugin marketplace add obra/superpowers
claude plugin details superpowers@superpowers-dev
```

Expect: a backup tarball listed in `~/` (the `||` aborts if `tar` fails —
fail closed before any deletion); `gh auth status` succeeds with `repo` scope
(if not, `gh auth refresh -h github.com`, `gh auth login`, or route the
step-14 PR through the GitHub connector);
`details` prints **14 skill files** — the **13 usable workflow skills** plus
the `using-superpowers` dispatcher (a SessionStart bootstrap/reminder, not a
skill you invoke for a task) — plus 1 SessionStart hook and a projected
always-on token cost. If the cost is surprising, stop before step 2.

**Pinned revisions** (reviewed 2026-07-07; the clone steps below check these
out so execution installs exactly what was reviewed, not a later HEAD):
`fr33d3m0n/threat-modeling` `a0962b73`, `Dammyjay93/interface-design`
`2f9be320`, `obra/the-elements-of-style` `6099c505`, `wshobson/agents`
`5cc2549a`, `am-will/codex-skills` `e3437156`. The Claude-side *marketplace
plugin* installs (superpowers and interface-design) pull marketplace-latest,
which the plugin mechanism can't pin — skim each installed SKILL.md before
relying on it.

### Step 2 — Install superpowers (both tools)

```bash
claude plugin install superpowers@superpowers-dev
codex plugin add superpowers@openai-curated
```

Verify: `~/.claude/settings.json` gains
`enabledPlugins["superpowers@superpowers-dev"] = true`; `~/.codex/config.toml`
gains `[plugins."superpowers@openai-curated"] enabled = true`.

### Step 3 — Install the-elements-of-style (both tools)

Vendor the reviewed `writing-clearly-and-concisely` skill loose on both tools.
The pinned repo has `.claude-plugin/plugin.json` but no installable
`.claude-plugin/marketplace.json` for Claude's marketplace flow.

```bash
rm -rf ~/.claude/skills/writing-clearly-and-concisely ~/.codex/skills/writing-clearly-and-concisely ~/.codex/skills/.eos-src
git clone https://github.com/obra/the-elements-of-style ~/.codex/skills/.eos-src
git -C ~/.codex/skills/.eos-src checkout 6099c505
cp -a ~/.codex/skills/.eos-src/skills/writing-clearly-and-concisely ~/.claude/skills/
cp -a ~/.codex/skills/.eos-src/skills/writing-clearly-and-concisely ~/.codex/skills/
rm -rf ~/.codex/skills/.eos-src
```

Verify: `ls ~/.claude/skills/writing-clearly-and-concisely/SKILL.md
~/.codex/skills/writing-clearly-and-concisely/SKILL.md`.

### Step 4 — Vendor api-design-principles (both tools, one skill only)

Do NOT install the whole `backend-development` plugin (it bundles 9 skills +
TDD-orchestration that conflict with the tdd retirement).

```bash
rm -rf ~/.claude/skills/api-design-principles ~/.codex/skills/api-design-principles ~/.claude/skills/.api-src
git clone https://github.com/wshobson/agents ~/.claude/skills/.api-src
git -C ~/.claude/skills/.api-src checkout 5cc2549a
cp -a ~/.claude/skills/.api-src/plugins/backend-development/skills/api-design-principles ~/.claude/skills/
cp -a ~/.claude/skills/.api-src/plugins/backend-development/skills/api-design-principles ~/.codex/skills/
rm -rf ~/.claude/skills/.api-src
```

Verify: `ls ~/.claude/skills/api-design-principles/SKILL.md
~/.codex/skills/api-design-principles/SKILL.md`.

### Step 5 — Install threat-modeling (both tools, mirrored)

Mirror the same skill to both tools (identical end states — chosen over
Codex's native `security-threat-model`, which is a different skill).

```bash
rm -rf ~/.claude/skills/threat-modeling ~/.codex/skills/threat-modeling
git clone https://github.com/fr33d3m0n/threat-modeling ~/.claude/skills/threat-modeling
git -C ~/.claude/skills/threat-modeling checkout a0962b73
git clone https://github.com/fr33d3m0n/threat-modeling ~/.codex/skills/threat-modeling
git -C ~/.codex/skills/threat-modeling checkout a0962b73
```

Verify: `ls ~/.claude/skills/threat-modeling/SKILL.md
~/.codex/skills/threat-modeling/SKILL.md`. (Confirm `~/.claude/skills/` /
`~/.codex/skills/` are the loose-skill roots on this machine first.)

### Step 6 — Install codex-security (Codex only)

```bash
codex plugin add codex-security@openai-curated
```

Verify: `codex plugin list` shows `codex-security@openai-curated` enabled.

### Step 7 — Install interface-design (both tools) + enable frontend-design (Claude)

Claude — plugin install (skill + both commands):

```bash
claude plugin marketplace add Dammyjay93/interface-design
claude plugin install interface-design@interface-design
claude plugin install frontend-design@claude-code-plugins   # it's in the marketplace but not installed; install (then `claude plugin enable frontend-design@claude-code-plugins` only if it lands disabled)
```

Codex — vendor both skills loose (no `.codex-plugin` manifests). interface-design
(its `agents/openai.yaml` shim is the Codex loader), plus `am-will/codex-skills`'
`frontend-design` as the Codex counterpart to Anthropic's frontend-design:

```bash
rm -rf ~/.codex/skills/interface-design ~/.codex/skills/.ifd-src
git clone https://github.com/Dammyjay93/interface-design ~/.codex/skills/.ifd-src
git -C ~/.codex/skills/.ifd-src checkout 2f9be320
cp -a ~/.codex/skills/.ifd-src/.claude/skills/interface-design ~/.codex/skills/
rm -rf ~/.codex/skills/.ifd-src

rm -rf ~/.codex/skills/frontend-design ~/.codex/skills/.fd-src
git clone https://github.com/am-will/codex-skills ~/.codex/skills/.fd-src
git -C ~/.codex/skills/.fd-src checkout e3437156
cp -a ~/.codex/skills/.fd-src/skills/frontend-design ~/.codex/skills/
rm -rf ~/.codex/skills/.fd-src
```

`am-will/codex-skills` has **no license** — this is a personal-use copy, not
redistributable; note it in the toolkit doc (final step). Codex's native GPT-5.5
frontend generation is the always-current fallback. Residual asymmetry:
interface-design's `design-review`/`design-deslop` slash-commands are
Claude-only (Codex runs the equivalent review inline from the skill).

Verify: `claude plugin list` shows `interface-design` + `frontend-design`;
`ls ~/.codex/skills/interface-design/SKILL.md ~/.codex/skills/frontend-design/SKILL.md`.

### Step 8 — Port obsidian-skills to Codex

```bash
for s in obsidian-cli json-canvas obsidian-bases defuddle obsidian-markdown; do
  rm -rf ~/.codex/skills/$s
  cp -a ~/.claude/skills/obsidian-skills/skills/$s ~/.codex/skills/
done
```

Verify: `ls ~/.codex/skills/` lists all five. (`defuddle` needs
`npm install -g defuddle` to function — same as on Claude today; not
introduced here.)

### Step 9 — Retire tdd and grill-me

```bash
rm -rf ~/.claude/skills/tdd ~/.codex/skills/tdd ~/.claude/skills/grill-me
```

Verify: none of the three paths exist. (`grill-me` was never on Codex.)

### Step 10 — Amend the loader rule + add precedence + vocabulary to `~/.claude/CLAUDE.md`

**First, a policy amendment (decided: keep the loader bridge).** The step-12a
`main/CLAUDE.md` links to `AGENTS.md` only (`@AGENTS.md`) — a pure loader with
no instructions of its own. `~/.claude/CLAUDE.md` rule 1 says "no local
CLAUDE.md files"; amend it so a link-only loader is explicitly allowed (it
just makes Claude Code read the project's `AGENTS.md`, which the same rule
already endorses: "checks its own folder for context"). Change rule 1's
"no local CLAUDE.md files" to:

```
no local CLAUDE.md files (exception: a repo-root CLAUDE.md whose entire content is `@AGENTS.md` — a loader so Claude Code reads the project's AGENTS.md, since it doesn't read AGENTS.md natively; it holds no instructions of its own)
```

**Then**, append both sections:

```markdown
## Skill precedence

- **Plan Mode:** this harness's native Plan Mode workflow governs entering plan mode. `using-superpowers`'s "brainstorm before plan mode" mandate does not apply here.
- **ponytail vs. brainstorming:** route to brainstorming's design gate only when the request needs a new dependency (fails ponytail's rung 4) or spans multiple independent subsystems or has genuine ambiguity about purpose/constraints/success criteria. Everything else — single-function changes, config tweaks, stdlib/native/existing-dependency solutions — stays on ponytail's fast path.
- **rethink / rethink-audit vs. brainstorming + writing-plans:** new-feature/component/from-scratch design → brainstorming's gated flow, not rethink (rethink's own directive stays "active every response for design"; this rule carves out new-build). Narrower tactical-but-architectural questions (sync vs. async, API shape) → rethink. `rethink-audit`'s `migrate:` output is a sequencing sketch, not an executable plan — route it to `superpowers:writing-plans` before any code; don't execute its steps directly.
- **TDD vs. ponytail:** when `superpowers:test-driven-development` is in effect, its test-first ordering wins over ponytail's code-first default; ponytail still governs size/shape once a test exists.
- **threat-modeling vs. a single finding:** answer a follow-up about one already-flagged finding directly, scoped to it — do NOT launch threat-modeling's 8-phase run. Invoke threat-modeling only for a deliberate whole-codebase audit. (Its own SKILL.md has an upstream; keep this rule here, not there.)
- **caveman scope:** caveman compresses live chat only — never persisted files (code, commits, PRs, docs, specs, plans, reports, UI strings). `the-elements-of-style` governs the quality of those durable artifacts.
- **grilling vs. brainstorming:** grilling stress-tests an EXISTING plan/design decision-by-decision. If the user has only a bare idea with no plan yet, use brainstorming first to produce and approve a plan, then grilling to interrogate it.
- **improve vs. subagent-driven-development:** a single already-identified audit finding → `improve`'s own `execute` (one dispatch, disposable review worktree, human decides whether to apply the diff). A spec-derived multi-task implementation plan → `superpowers:subagent-driven-development` (multi-task, two-stage review, mergeable branch).
- **interface-design vs. frontend-design:** review/critique/audit/de-slop of existing UI → interface-design (only it has review commands). New UI: product/dashboard/SaaS/admin/tool/data → interface-design; marketing/landing/campaign/brand → frontend-design; ambiguous → ask.

## Design vocabulary

- `codebase-design`'s module/interface/seam/adapter/leverage/locality terms are canonical when any skill decomposes work into units — read "unit"/"boundary" in `brainstorming`/`writing-plans` as module/seam.
- Before writing a RED test (`superpowers:test-driven-development`), name and confirm the test's seam (per `codebase-design`) first; test only at pre-agreed seams.
```

### Step 11 — Write `~/.codex/AGENTS.md` (currently empty)

Codex gets the same precedence + vocabulary rules as Claude (step 10),
adapted for Codex's toolset, plus the Codex-only security routing.

```markdown
## Skill precedence

- **Planning:** your own planning workflow governs; `using-superpowers`'s "brainstorm before planning" mandate does not override it.
- **ponytail vs. brainstorming:** route to brainstorming's design gate only when the request needs a new dependency (fails ponytail's rung 4) or spans multiple independent subsystems or has genuine ambiguity about purpose/constraints/success criteria. Everything else — single-function changes, config tweaks, stdlib/native/existing-dependency solutions — stays on ponytail's fast path.
- **rethink / rethink-audit vs. brainstorming + writing-plans:** new-feature/component/from-scratch design → brainstorming's gated flow, not rethink. Narrower tactical-but-architectural questions (sync vs. async, API shape) → rethink. `rethink-audit`'s `migrate:` output is a sequencing sketch, not an executable plan — route it to `superpowers:writing-plans` before any code; don't execute its steps directly.
- **TDD vs. ponytail:** when `superpowers:test-driven-development` is in effect, its test-first ordering wins over ponytail's code-first default; ponytail still governs size/shape once a test exists.
- **threat-modeling vs. a single finding:** answer a follow-up about one already-flagged finding (including a codex-security finding) directly, scoped to it — do NOT launch threat-modeling's 8-phase run. Invoke threat-modeling only for a deliberate whole-codebase audit.
- **caveman scope:** caveman compresses live chat only — never persisted files (code, commits, PRs, docs, specs, plans, reports, UI strings). `the-elements-of-style` governs the quality of those durable artifacts.
- **grilling vs. brainstorming:** grilling stress-tests an EXISTING plan/design decision-by-decision. If the user has only a bare idea with no plan yet, use brainstorming first to produce and approve a plan, then grilling to interrogate it.
- **improve vs. subagent-driven-development:** a single already-identified audit finding → `improve`'s own `execute` (one dispatch, disposable review worktree). A spec-derived multi-task implementation plan → `superpowers:subagent-driven-development` (multi-task, two-stage review, mergeable branch).
- **UI design:** product/dashboard/SaaS/admin/tool UI + review/critique/audit → interface-design (its slash-commands are Claude-only; run the equivalent review inline from the skill). Marketing/landing/brand/distinctive UI → `frontend-design` (am-will skill) or Codex's native frontend generation.
- **PR review:** Codex's native review is the platform for PR review here; it covers the same dimensions pr-review-toolkit does on Claude (comments, tests, errors, types, quality, security). See the stack/toolkit guide for the dimension mapping.

## Design vocabulary

- `codebase-design`'s module/interface/seam/adapter/leverage/locality terms are canonical when any skill decomposes work into units — read "unit"/"boundary" in `brainstorming`/`writing-plans` as module/seam.
- Before writing a RED test (`superpowers:test-driven-development`), name and confirm the test's seam (per `codebase-design`) first; test only at pre-agreed seams.

## Security tooling routing

`codex-security`'s scan family (`security-scan`, `security-diff-scan`, `deep-security-scan`, `finding-discovery`) and its internal `threat-model` phase all use broad triggers. Treat that internal `threat-model` phase as scan-internal only. Route any standalone request to build/update/review a threat model (STRIDE, trust boundaries, attack surface) that is not part of an active codex-security scan to the `threat-modeling` skill instead.

Known asymmetry: Claude Code's `security-guidance` runs passive, automatic checks on every edit/commit/push. Codex has no equivalent — `codex-security` is active/explicit-invocation only. Codex does not get an always-on security net without an explicit scan.

Known friction: `codex-security`'s `deep-security-scan` requires agent depth ≥ 2 at `block` severity; this machine's `agents.max_depth = 1` trips a remediation dialogue for that one scan mode. `security-scan`/`security-diff-scan` are unaffected.
```

### Step 12 — Repo edits (Layer 2 + 3), one worktree, no PR yet

```bash
git fetch origin
git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/adopt-superpowers -b docs/adopt-superpowers origin/main
cd ~/memoria-vault/worktrees/adopt-superpowers
```

**12a — new file `CLAUDE.md` at repo root** — links to `AGENTS.md` only
(enabled by step 10's rule-1 carve-out). Its entire content is:

```markdown
@AGENTS.md
```

**12b — `AGENTS.md`: replace the entire Skills table** with:

```markdown
| Stage | Skill | Use when |
|---|---|---|
| Whole-docs audit | [`docs-audit`](.agents/playbooks/docs-audit.md) | Fresh Diátaxis, consistency, generated-reference, terminology, coverage, and live-link audit across `docs/` |
| Any docs PR | [`docs-review`](.agents/playbooks/docs-review.md), plus `the-elements-of-style` for prose clarity | Before opening — quadrant fit, links, indexing, terminology, sentence-level clarity |
| Any PR | [`code-review`](.agents/playbooks/code-review.md), which invokes `superpowers:requesting-code-review` (both tools) plus, **on Claude**, `pr-review-toolkit:code-reviewer`, and **on Codex**, native review — run independently, don't substitute one for another | Before opening — bugs, compliance, plan alignment, production-readiness |
| Deeper review on a dimension | **Claude:** `pr-review-toolkit` agents (`silent-failure-hunter`, `pr-test-analyzer`, `code-simplifier`, `comment-analyzer`, `type-design-analyzer`). **Codex:** native review covers the same six dimensions (see `.agents/toolkit.md` for the mapping) | After the above — probe one lens |
| Sensitive-path changes | [`security-review`](.agents/playbooks/security-review.md), plus `security-guidance` (passive) and `threat-modeling` (full audit, only when escalation is warranted) | PRs touching `scripts/`, `.github/`, `vault-template/.memoria/`, `design-history/`, `AGENTS.md`, or agent guidance |
| Confirming a fix | [`verify-change`](.agents/playbooks/verify-change.md), plus `superpowers:verification-before-completion` | After a change — confirm actual behavior |
| New or cut release | [`release`](.agents/playbooks/release.md) | Scaffolds the release folder/plan, milestone, and parent issue; release-please owns version/notes |
```

Add directly under the table:

```
This repo's own Critical/High/Medium/Low severity vocabulary is lighter than `requesting-code-review`'s Critical/Important/Minor scale — never mix the two inside one persisted report, issue, or PR comment.
```

In the "Passive, when installed" paragraph below the table, name each
security tool with the tool it runs on: `security-guidance` (Claude,
passive), `codex-security` (Codex, active), `threat-modeling` (both, on
demand) — so a reader knows which apply to the tool they're using.

Add a new subsection near "Work routing" named `### Issue tracker loop`:

```markdown
### Issue tracker loop

The Memoria Issue Tracker is the live work-state owner, not an after-the-fact
log. For any non-trivial bug, enhancement, documentation change, release task,
or design decision:

1. **Before work:** identify the owning issue. If none exists, either create one
   or state explicitly why the work is too small or too local to track.
2. **During work:** update only Project `Status` and `Readiness`; do not create
   ad-hoc labels or milestones. Labels stay minimal, and milestones are release
   scope only.
3. **In PRs:** use `Refs #NN` for partial, preparatory, folded, or follow-up
   work. Use `Closes #NN` only when the PR fully satisfies that issue's close
   condition.
4. **At close:** close an issue only when it is resolved by merged work,
   explicitly obsolete, or fully subsumed by another open issue with no
   independent decision left. Leave folded-but-unresolved issues open until the
   absorbing issue lands the actual decision or implementation.
5. **Final report:** say which issue state changed, or state `Issue tracker:
   no change` when no tracker update was needed.
```

**12c — `.github/pull_request_template.md`.** Replace the Related issues
section with:

```markdown
## Related issues

Refs #<!-- issue number -->

<!-- Use "Closes #..." only when this PR fully satisfies the issue's close condition.
For partial, folded, preparatory, or design-only work, use "Refs #..." and leave
the issue open. -->

Issue tracker updated: <!-- yes / no / N/A, with reason -->
```

**12d — `scripts/checks/github_doctor.py` + `tests/test_github_doctor.py`.**
Extend `github-doctor` with one small PR-template guard:

- fail if `.github/pull_request_template.md` is missing;
- fail if the template contains `Closes #` but no `Refs #`;
- fail if it does not mention `Issue tracker updated`.

Add one focused test that builds a temporary `.github/pull_request_template.md`
with only `Closes #` alongside otherwise-valid issue-template/dependabot
fixtures, then asserts the new error fires. Reuse the existing
`github_doctor.check()` pattern; do not add a new checker.

**12e — `.agents/playbooks/code-review.md`.** After "## 1. Establish scope",
new final paragraph:

```
**Dispatching this as an isolated review.** When reviewing your own recent work, follow `superpowers:requesting-code-review`'s context-isolation mechanic: dispatch reviewers given only the base/head SHAs and requirements, never your session history. Run `superpowers:requesting-code-review` on both tools. On Claude, also run `pr-review-toolkit:code-reviewer` independently for compliance + bug scan; on Codex, use native review for that role. Do not substitute one for another. This playbook's own criteria and report format stay authoritative over all reviewers.
```

At the end of "## 4. Report", new bullet:

```
- After presenting findings, apply `superpowers:receiving-code-review`'s discipline: fix Critical immediately, Important before proceeding, note Minor for later, and push back (with reasoning) on a finding that looks wrong.
```

**12f — `.agents/playbooks/verify-change.md`.** One line appended at the end:

```
*(If `superpowers:verification-before-completion` is installed, its claim-honesty discipline complements this playbook. These steps remain authoritative regardless.)*
```

**12g — `.agents/playbooks/exec-plan.md`.** New item 5 in "## Authoring":

```
5. Size tasks using `superpowers:writing-plans`' right-sizing rule (each task independently testable and revertable) — but the deliverable still lands in this file's own template, never a new `docs/superpowers/plans/` file.
```

New section after "## Running", before "## Validating":

```
## Reusing superpowers execution techniques

An ExecPlan's Concrete steps may be executed via `superpowers:subagent-driven-development` (per-task implementer + two-stage reviewer) or `superpowers:executing-plans` (separate-session handoff). This file's own Validation, Progress, Execution log, and Surprises sections remain authoritative — neither technique's plan-file or recovery ledger substitutes for this file's record.
```

**12h — `.agents/templates/exec-plan.md`.** Update the metadata line so
`Related issues / milestone` records the intended issue disposition, not just
issue numbers:

```markdown
- **Related issues / milestone:** {{ #NN + intended disposition:
  refs/closes/folded into #NN/no tracker change; 0.1.0 or — }}
```

Add one line in the "Concrete steps" guidance comment:

```
See ../playbooks/exec-plan.md → "Authoring" item 5 and "Reusing superpowers execution techniques" for optional sizing/execution engines.
```

**12i — `.agents/templates/handoff.md`.** Add a `## Tracker` section after
`## Scope`:

```markdown
## Tracker

Owning issue: <!-- #NN or N/A with reason -->
Intended disposition: <!-- refs / closes / folded into #NN / no tracker change -->
Close condition: <!-- observable condition for closing, or N/A -->
```

Append a `## Result` section at the end:

```
## Result

<!-- Filled by the RECEIVER after completing the handoff, not the dispatcher. -->

**Status:** DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED

<!-- What was actually done, any deviation from Expected outputs, and why. -->
```

**12j — `.agents/playbooks/docs-review.md`.** One line at the end of
"## 4. Check terminology and claims":

```
If `the-elements-of-style` is installed, apply its `writing-clearly-and-concisely` rules (active voice, omit needless words) as a prose-clarity pass over changed pages — complementary to this section's terminology and citation checks.
```

**12k — `.agents/playbooks/security-review.md`.** New section appended:

```
## 5. Escalate to a full audit

This playbook is scoped to the current diff. If review surfaces something beyond one change — systemic exposure, unclear trust boundaries, or a request for a standalone assessment — and the `threat-modeling` skill is installed, it runs a full 8-phase STRIDE model as a separate, deliberately-requested activity. Do not reach for it to answer single-finding follow-ups here — resolve those per section 4.
```

Do not commit or open the PR yet. Step 14 adds `.agents/toolkit.md` in this
same worktree and opens one PR containing both `AGENTS.md`'s toolkit reference
and the file it points to.

```bash
git status --short
```

### Step 13 — Verify (fresh sessions)

Run §5 in a fresh Claude Code session and a fresh Codex session (plugin and
skill changes need a restart to load).

### Step 14 — Author the toolkit stack document (last step)

Once the stack is installed and verified (steps 1–13), document the whole
thing at **`.agents/toolkit.md`** in the **same step-12 worktree** — the repo's
agent-guidance home, so it's durable, discoverable, and PR-reviewed;
`AGENTS.md` stays the authority/policy, `toolkit.md` is the "what's available
and how to use it" map.

The document covers the **entire** stack, grouped by layer:

- **Layer 1 — generic process (`~/.claude/`, `~/.codex/`):** every plugin and
  skill, one line each on what it does and when to reach for it, with its
  Claude|Codex coverage — `superpowers` (all 13 skills + `using-superpowers`),
  `ponytail`, `rethink`, `grilling`, `caveman`, `codebase-design`, `improve`,
  `interface-design`, `frontend-design`, `the-elements-of-style`,
  `api-design-principles`, `threat-modeling`, `codex-security`,
  `pr-review-toolkit`, `security-guidance`, `obsidian-skills`. Do not list
  optional tools like `dataviz`, `artifact-design`, or Figma unless
  `claude plugin list`, `codex plugin list`, or MCP config proves they are
  actually installed/configured on this machine.
- **Layer 2 — repo policy (`.agents/`):** every playbook (`code-review`,
  `verify-change`, `exec-plan`, `docs-review`, `docs-audit`,
  `security-review`, `design-history`, `release`), every template
  (`exec-plan`, `handoff`, `review-report`, `release-plan`), the system maps
  (`source-of-truth-map`, `change-impact-map`, `test-selection`), and the
  domain skills (`policy-change-review`, `schema-change`) — what each owns.
- **Layer 3 — discovery:** `main/CLAUDE.md` → `@AGENTS.md`; `~/.claude/CLAUDE.md`
  / `~/.codex/AGENTS.md` precedence + vocabulary.

Plus:

- **The parity ledger** (§3) — how each capability is covered on Claude vs.
  Codex (plugin or native), and the residual asymmetries.
- **How the pieces interlock** — the precedence rules (which skill wins when
  two fire), the "reference by name, don't duplicate" rule, and the
  never-edit-vendored rule.
- **Best practices per capability** — e.g. TDD's seam-first discipline;
  ponytail's ladder; brainstorming's design gate; interface-design's
  avoid-AI-slop review; the pr-review-toolkit six-dimension ↔ Codex-native
  review mapping (comments, tests, errors, types, quality, security).
- **Sourcing + caveats** — which items are marketplace plugins, which are
  loose-vendored, which are unlicensed (`am-will/codex-skills`
  personal-use-only); discovery via `openai/plugins` and
  `hashgraph-online/awesome-codex-plugins`.

Then open, verify, merge, and clean up the single repo PR (re-confirm auth
first — `gh auth status` must show `repo` scope, or route creation through the
GitHub connector):

```bash
gh auth status || { echo "GH AUTH FAILED — run: gh auth refresh -h github.com"; exit 1; }
git add CLAUDE.md AGENTS.md .agents/toolkit.md .agents/playbooks/code-review.md .agents/playbooks/verify-change.md .agents/playbooks/exec-plan.md .agents/templates/exec-plan.md .agents/templates/handoff.md .agents/playbooks/docs-review.md .agents/playbooks/security-review.md .github/pull_request_template.md scripts/checks/github_doctor.py tests/test_github_doctor.py
git diff --cached --name-only
git commit -m "docs: adopt superpowers and tracker-loop conventions"
git push -u origin docs/adopt-superpowers
gh pr create --base main --fill
pr_number=$(gh pr view --json number -q .number)
gh pr checks "$pr_number" --watch
cd ~/memoria-vault/main
gh pr merge "$pr_number" --squash --delete-branch
git worktree remove ~/memoria-vault/worktrees/adopt-superpowers
git branch -D docs/adopt-superpowers
git status --short
git fetch origin
git merge --ff-only origin/main
```

Verify: `ls .agents/toolkit.md`; every plugin/skill/playbook/template listed
above appears; PR checks pass; the PR is merged; `~/memoria-vault/main` is
fast-forwarded to `origin/main`; `git worktree list --porcelain` no longer
lists `~/memoria-vault/worktrees/adopt-superpowers`.

## 5. Validation and acceptance

Presence:

- **superpowers loads (both tools):** fresh Claude session — `claude plugin
  list` shows `superpowers@superpowers-dev` enabled and the skill reminder lists
  the 13 usable `superpowers:` workflow skills (`using-superpowers` is the
  SessionStart dispatcher — it fires as a reminder, not a separately-listed
  invocable skill, so 13 here, 14 skill files on disk); fresh Codex session —
  `codex plugin list` shows `superpowers@openai-curated` enabled.
- **gap plugins present:** `ls` confirms
  `~/.claude/skills/{writing-clearly-and-concisely,threat-modeling,api-design-principles}`,
  `~/.codex/skills/{writing-clearly-and-concisely,api-design-principles,
  threat-modeling,interface-design,frontend-design}`, the five
  `~/.codex/skills/obsidian-*`/`json-canvas`/`defuddle` folders, and
  `interface-design`/`frontend-design` in `claude plugin list`.
- **api-design-principles is one skill only:** `find ~/.claude/skills
  ~/.codex/skills -iname SKILL.md` shows no `architecture-patterns`,
  `microservices-patterns`, `cqrs-implementation`, `event-store-design`,
  `projection-patterns`, `saga-orchestration`, `temporal-python-testing`,
  `workflow-orchestration-patterns`, `tdd-orchestrator`, or `test-automator`.
- **retirements + declines:** `tdd`/`grill-me` absent both tools;
  `code-review`/`coderabbit` absent from `claude plugin list`/`codex plugin
  list`.
- **AGENTS.md table is real (per-tool):** every row's linked file exists
  (`ls`), and every named plugin/skill is either installed on the tool
  you're validating or named there as a known cross-tool asymmetry
  (`codex-security` = Codex-only; `security-guidance` and
  `pr-review-toolkit` = Claude-only; `frontend-design` exists on both tools
  with different install shapes). No row names something that is neither
  installed nor a documented asymmetry.
- **Layer 3:** in a fresh Claude session opened in `~/memoria-vault/main`, an
  early answer cites an `AGENTS.md`-only fact (e.g. the worktree-first rule)
  before any tool reads `AGENTS.md`.

Behavior (paste transcripts):

- Feature needing TDD → agent writes a failing test before implementation
  (TDD wins over ponytail).
- "add a small utility function" → ponytail fast path, no brainstorming gate.
- "build a new module needing a new charting library" → brainstorming gate
  before code.
- "should this endpoint be async or sync" → rethink answers; brainstorming's
  gate does not fire.
- "build a new dashboard widget" → brainstorming runs; rethink stays quiet.
- "grill me on my rough idea for X" (no plan yet) → routes to brainstorming
  first, not grilling.
- "build me a dashboard" (both UI plugins active) → routes to
  `interface-design` (or asks), not both.
- follow-up "is this finding exploitable?" → direct scoped answer, no 8-phase
  threat-modeling run.
- Codex: standalone "build a threat model for this repo" → routes to
  `threat-modeling`, not codex-security's internal phase.

Repo PR:

- `pr-policy` / `lint` / `cspell` / `markdownlint` pass, the
  single repo PR is merged, and `~/memoria-vault/main` fast-forwards cleanly to
  `origin/main`.
- `python3 -m pytest tests/test_github_doctor.py` passes, and
  `python3 scripts/checks/github_doctor.py` passes with the updated PR template.
- The PR body uses `Refs #...` by default and records whether the issue tracker
  was updated; no template text nudges agents to close partial work.
- `AGENTS.md`, `.agents/templates/handoff.md`, and
  `.agents/templates/exec-plan.md` all require an owning issue or explicit
  no-tracker reason for non-trivial work.

Toolkit doc (step 14):

- `.agents/toolkit.md` exists and lists every Layer-1 plugin/skill, every
  Layer-2 playbook/template/system-map/domain-skill, and the parity ledger —
  cross-check each name against `claude plugin list`, `codex plugin list`,
  and `ls ~/.claude/skills ~/.codex/skills .agents/`.

## 6. Idempotence and recovery

- **Re-runnable:** every clone/copy step (3–8) removes its target with
  `rm -rf` **before** the `git clone`/`cp -a`, so a re-run is clean — no
  "clone fails, dir exists" and no stale-content merge. Marketplace
  add/install are idempotent. The `rm -rf` in step 9 is safe to re-run. The
  file edits (steps 10–12) and doc authoring (step 14) overwrite cleanly
  when re-applied.
- **Rollback:** step 1 writes a full backup tarball
  (`~/toolkit-backup-*.tgz`, covering both `skills/` dirs,
  `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.claude/settings.json`,
  `~/.codex/config.toml`) — restore from it to undo any local change. Also:
  `claude plugin uninstall` / `codex plugin remove` reverse the installs;
  every file edit's exact pre-edit text is in §4. The repo PR reverts by
  closing unmerged or reverting the squash commit.

## 7. Progress

- [x] 2026-07-07 16:15 CDT — 1 — pre-flight backup/auth/cost read completed.
- [x] 2026-07-07 16:15 CDT — 2 — superpowers installed on both tools
      (`superpowers@superpowers-dev` on Claude, `superpowers@openai-curated`
      on Codex).
- [x] 2026-07-07 16:15 CDT — 3 — the-elements-of-style installed as the loose
      `writing-clearly-and-concisely` skill on both tools; Claude marketplace
      install was unavailable (see §9).
- [x] 2026-07-07 16:15 CDT — 4 — api-design-principles vendored to both tools
      as one loose skill.
- [x] 2026-07-07 16:15 CDT — 5 — threat-modeling cloned to both tools at
      `a0962b7`.
- [x] 2026-07-07 16:15 CDT — 6 — codex-security installed on Codex.
- [x] 2026-07-07 16:15 CDT — 7 — interface-design installed on Claude and
      vendored to Codex; frontend-design installed on Claude and vendored to
      Codex.
- [x] 2026-07-07 16:15 CDT — 8 — obsidian-skills ported to Codex.
- [x] 2026-07-07 16:15 CDT — 9 — loose tdd + grill-me retired.
- [x] 2026-07-07 16:15 CDT — 10 — `~/.claude/CLAUDE.md` precedence +
      vocabulary added.
- [x] 2026-07-07 16:15 CDT — 11 — `~/.codex/AGENTS.md` written.
- [x] 2026-07-07 16:15 CDT — 12 — repo worktree edits completed and merged via
      PR #1310.
- [ ] 2026-07-07 16:15 CDT — 13 — installed-state and repo/CI validation
      completed; Codex fresh prompt context was verified locally with
      `codex debug prompt-input`; Claude behavior-prompt transcript remains
      blocked because the approval reviewer rejected transmitting repo guidance
      to an external model service and Claude exposes no local prompt renderer.
- [x] 2026-07-07 16:15 CDT — 14 — `.agents/toolkit.md` authored, PR #1310
      merged, `main` fast-forwarded to `528ddf6c`, and
      `worktrees/adopt-superpowers` removed.

## 8. Execution log

- 2026-07-07 — Created backup
  `~/toolkit-backup-20260707-155353.tgz` before any local tool-config edits.
- 2026-07-07 — `obra/superpowers` registered in Claude as marketplace
  `superpowers-dev`, so Claude installed `superpowers@superpowers-dev` instead
  of the plan's `superpowers@superpowers` spelling. Codex installed
  `superpowers@openai-curated`.
- 2026-07-07 — `obra/the-elements-of-style` did not expose
  `.claude-plugin/marketplace.json`; installed the reviewed
  `writing-clearly-and-concisely` skill loose on Claude and Codex instead.
- 2026-07-07 — Repo changes went through PR #1310 and squash-merged as
  `528ddf6c docs: adopt superpowers and tracker-loop conventions (#1310)`.
- 2026-07-07 — A fresh Claude `-p` smoke prompt was rejected by the approval
  reviewer because it would transmit private repo guidance to an external model
  service; retained safer local/plugin/CI validation only.
- 2026-07-07 — Used `codex debug prompt-input` from `main` as a local-only fresh
  Codex context check. The rendered model-visible input contained
  `superpowers:brainstorming`, `codex-security:security-scan`,
  `interface-design`, global `## Skill precedence`, the repo worktree-first
  rule, and `### Issue tracker loop`.

## 9. Surprises & discoveries

- **Watch during validation:** if brainstorming's low invocation bar absorbs
  the tactical middle-band questions rethink's narrowed trigger reserves for
  it, the carve-out is illusory — reconsider fully retiring rethink's
  standing directive.
- **Open, not resolved:** `using-superpowers`'s `<SUBAGENT-STOP>` means its
  mandate doesn't engage in subagent-dispatched work; its "Skill Priority"
  section never orders two competing *process* skills. Neither blocks
  shipping.
- **interface-design slash-commands are Claude-only:** on Codex the review
  runs inline from the vendored skill (which its own text supports), not via
  a `/interface-design:design-review` command. Verify this holds if Codex
  gains a command mechanism later.
- **superpowers Claude marketplace name drifted:** `claude plugin marketplace
  add obra/superpowers` registered `superpowers-dev`; install/details use
  `superpowers@superpowers-dev`.
- **the-elements-of-style marketplace install unavailable:** the pinned repo had
  `.claude-plugin/plugin.json` but no `.claude-plugin/marketplace.json`, so the
  prose skill was installed loose on both tools.

## 10. Interfaces & dependencies

- **Edited in place:** none — this plan edits zero plugin/skill components.
- **Used as-is, no file edit — routing/precedence goes in CLAUDE.md/AGENTS.md:**
  every component, including `rethink` (your own plugin), the loose MIT
  cherry-picks `grilling` / `caveman` / `improve` / `codebase-design`, and the
  marketplace/vendored ones `ponytail`, `superpowers`, `threat-modeling`,
  `codex-security`, `interface-design`, `frontend-design`,
  `the-elements-of-style`, `obsidian-skills`, `api-design-principles`.
- **New tool-config files:** `~/.codex/AGENTS.md` (was empty).
- **Installed/vendored:** superpowers (both), the-elements-of-style (loose
  both), api-design-principles (loose both), threat-modeling
  (Claude clone + Codex mirror), codex-security (Codex), interface-design
  (Claude plugin + Codex loose), frontend-design (Claude enable + Codex
  `am-will/codex-skills` loose, unlicensed/personal-use), obsidian-skills
  (Codex loose copy).
- **Repo files (one PR, steps 12 + 14):** new `CLAUDE.md`, `AGENTS.md`,
  `.agents/playbooks/{code-review,verify-change,exec-plan,docs-review,
  security-review}.md`, `.agents/templates/{exec-plan,handoff}.md`,
  `.github/pull_request_template.md`, `scripts/checks/github_doctor.py`,
  `tests/test_github_doctor.py`, and new `.agents/toolkit.md` documenting the
  whole stack — all in one worktree, one PR.
- **Retired:** `~/.claude/skills/{tdd,grill-me}`, `~/.codex/skills/tdd`.
- **Declined, never installed:** official Anthropic `code-review` plugin;
  `coderabbit@openai-curated`.

## 11. Artifacts & notes

- Backup: `~/toolkit-backup-20260707-155353.tgz`.
- Installed-state checks:
  `claude plugin list` shows `superpowers@superpowers-dev`,
  `interface-design@interface-design`, `frontend-design@claude-code-plugins`,
  `pr-review-toolkit@claude-code-plugins`, `security-guidance@claude-code-plugins`,
  `ponytail@ponytail`, and `rethink@rethink`; `codex plugin list` shows
  `superpowers@openai-curated` and `codex-security@openai-curated` installed.
- Claude local plugin details: `claude plugin details superpowers@superpowers-dev`
  reports 14 skills and one SessionStart hook; interface-design and
  frontend-design details report their expected skill inventories.
- Codex local fresh-context check: `codex debug prompt-input` rendered
  model-visible context containing the new Codex skills, global precedence
  rules, and repo `AGENTS.md` work-routing/tracker rules without model access.
- Focused checks: `python3 -m pytest tests/test_github_doctor.py` passed
  (`3 passed`); `python3 scripts/checks/github_doctor.py` printed
  `github-doctor: ok`.
- Repo gate: `python3 scripts/verify pr` passed; final run reported
  `107 passed, 533 deselected` for static tests and
  `296 passed, 7 skipped, 337 deselected` for unit/contract tests.
- Separate prose gates: `npm run spellcheck` passed with `0` issues;
  `npm run markdownlint` passed.
- GitHub checks on PR #1310 passed:
  `pr-policy`, `lint`, `cspell`, `markdownlint`, `python-selftest`,
  `gitleaks`, `lint-config`, `PSScriptAnalyzer`, and `shellcheck`.

## 12. Outcomes & retrospective

- **Shipped:** Layer-1 toolkit installs/config updates, Layer-2/3 repo guidance,
  `.agents/toolkit.md`, PR-template tracker guardrails, and
  `github_doctor` validation. PR #1310 is merged and `main` is fast-forwarded to
  `origin/main`.
- **Still open:** the Claude fresh-session behavior transcript from §5 requires
  explicit approval to send repo guidance to an external Claude model service.
  Codex fresh context was verified locally with `codex debug prompt-input`. No
  issue tracker state changed.
- **Lessons:** prefer verifying marketplace manifest shape before promising a
  Claude plugin install path; record actual installed ids (`superpowers-dev`,
  loose Elements of Style) in durable docs.
