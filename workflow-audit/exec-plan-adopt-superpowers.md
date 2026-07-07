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
  `memoria-vault`-tracked changes (Layer 2/3, step 16) go through the normal
  worktree → branch → PR flow. This plan file lives on the `scratch` branch
  under `scratch/workflow-audit/`.
- **Related issues / milestone:** — (personal tooling + repo-doc
  consistency, not release-scoped).
- **Started:** 2026-07-06 · **Last updated:** 2026-07-06

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
6. Third-party plugin files are never edited in place.
7. `AGENTS.md`'s own Skills table names only things that actually exist.

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
- **Never edit a third-party plugin's installed/cached files** (`ponytail`,
  `superpowers`, `threat-modeling`, `codex-security`, `interface-design`,
  `the-elements-of-style`, `frontend-design`, `api-design-principles`
  source, `obsidian-skills` upstream). They have upstreams that overwrite
  on update. Route every cross-reference through `~/.claude/CLAUDE.md` or
  `~/.codex/AGENTS.md`. Directly editable (no upstream / user-owned):
  `rethink`, and the loose cherry-picks `grilling` / `caveman` /
  `codebase-design` / `improve`.
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
- **Layer 1 retire + edit editable skills** (steps 9–13): retire tdd +
  grill-me; edit grilling, caveman, improve, rethink.
- **Layer 1 precedence notes** (steps 14–15): `~/.claude/CLAUDE.md`,
  `~/.codex/AGENTS.md`.
- **Layer 2 + 3 repo edits** (step 16): one worktree, one PR.
- **Verify** (step 17).
- **Document the whole stack** (step 18): author `.agents/toolkit.md`.

**Parity ledger** (the R3 answer — Claude | Codex):

| Item | Claude | Codex |
|---|---|---|
| superpowers, ponytail, rethink, grilling, caveman, codebase-design, improve | ✓ | ✓ |
| the-elements-of-style | plugin install | loose vendor |
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
Both tools get the same precedence + vocabulary rules (steps 14–15).

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
  ~/.claude/skills ~/.codex/skills ~/.claude/CLAUDE.md \
  ~/.claude/plugins/marketplaces/rethink ~/.codex/.tmp/marketplaces/rethink \
  2>/dev/null; echo "backup written to ~/"
gh auth status   # must show an account with 'repo' scope for steps 16/18
```

Then add the marketplace and read the cost:

```bash
claude plugin marketplace add obra/superpowers
claude plugin details superpowers@superpowers
```

Expect: backup tarball in `~/`; `gh auth status` shows `repo` scope (if not,
`gh auth login` or route the step-16/18 PRs through the GitHub connector);
`details` prints 14 skills + 1 SessionStart hook and a projected always-on
token cost — if the cost is surprising, stop before step 2.

**Pinned revisions** (reviewed 2026-07-07; the clone steps below check these
out so execution installs exactly what was reviewed, not a later HEAD):
`fr33d3m0n/threat-modeling` `a0962b73`, `Dammyjay93/interface-design`
`2f9be320`, `obra/the-elements-of-style` `6099c505`, `wshobson/agents`
`5cc2549a`, `am-will/codex-skills` `e3437156`. The Claude-side *marketplace
plugin* installs (superpowers, the-elements-of-style, interface-design) pull
marketplace-latest, which the plugin mechanism can't pin — skim each
installed SKILL.md before relying on it.

### Step 2 — Install superpowers (both tools)

```bash
claude plugin install superpowers@superpowers
codex plugin add superpowers@openai-curated
```

Verify: `~/.claude/settings.json` gains
`enabledPlugins["superpowers@superpowers"] = true`; `~/.codex/config.toml`
gains `[plugins."superpowers@openai-curated"] enabled = true`.

### Step 3 — Install the-elements-of-style (both tools)

Claude has a `.claude-plugin` manifest; Codex has none → vendor loose.

```bash
claude plugin marketplace add obra/the-elements-of-style
claude plugin install the-elements-of-style@the-elements-of-style

rm -rf ~/.codex/skills/writing-clearly-and-concisely ~/.codex/skills/.eos-src
git clone https://github.com/obra/the-elements-of-style ~/.codex/skills/.eos-src
git -C ~/.codex/skills/.eos-src checkout 6099c505
cp -a ~/.codex/skills/.eos-src/skills/writing-clearly-and-concisely ~/.codex/skills/
rm -rf ~/.codex/skills/.eos-src
```

Verify: `ls ~/.codex/skills/writing-clearly-and-concisely/SKILL.md`.

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
claude plugin enable frontend-design@claude-plugins-official
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

### Step 10 — Edit grilling (both tools)

In `~/.claude/skills/grilling/SKILL.md` and `~/.codex/skills/grilling/SKILL.md`:

Set the frontmatter `description` to:

```
Grill the user relentlessly about a plan or design that already exists (their own draft, notes, or a prior spec). Use when the user wants to stress-test an EXISTING plan before building, or uses any 'grill' trigger phrases. Not for building a design from scratch — use brainstorming for that.
```

Append to the body:

```
If no plan or design exists yet — only a bare idea — use the brainstorming skill first to produce and get approval on one; grilling assumes a plan is already in hand to interrogate, not that one needs to be created.
```

### Step 11 — Edit caveman (both tools)

In `~/.claude/skills/caveman/SKILL.md` and `~/.codex/skills/caveman/SKILL.md`,
change the Boundaries section's first sentence to:

```
Code/commits/PRs/persisted design docs, specs, and plans (any file saved to disk as a project artifact): write normal.
```

### Step 12 — Edit improve (both tools)

In `~/.claude/skills/improve/SKILL.md` and `~/.codex/skills/improve/SKILL.md`,
add to the Hard Rules (or Invocation-variants) section:

```
Precedence: a single already-identified audit finding → this skill's own `execute` (one dispatch, disposable review worktree, human decides whether to apply the diff). A spec-derived multi-task implementation plan → superpowers:subagent-driven-development (multi-task, two-stage review, mergeable branch) instead.
```

### Step 13 — Reconcile, edit, release rethink; update both tools

rethink is your own plugin (`eranroseman/rethink`). **Preflight — the source
is currently messy, don't treat this as clean future work:** `claude plugin
list` reports rethink **1.0.1 installed on both tools**, but the Claude
marketplace clone at `~/.claude/plugins/marketplaces/rethink/` is **dirty**
(uncommitted edits to `plugins/rethink/{hooks/directive.md,
.claude-plugin/plugin.json,.codex-plugin/plugin.json}`, its plugin.json
already bumped to 1.1.0) and **1 commit ahead** of `origin/master`; the Codex
clone is at 1.0.1. Inspect it first:

```bash
git -C ~/.claude/plugins/marketplaces/rethink status --short --branch
git -C ~/.claude/plugins/marketplaces/rethink log --oneline origin/master..HEAD
git -C ~/.claude/plugins/marketplaces/rethink diff -- plugins/rethink
```

That unreleased 1.1.0 work is earlier-session rethink editing. Do **not**
layer the edits below onto the dirty clone blindly — work from a clean
`eranroseman/rethink` checkout, fold the existing 1.1.0 changes together with
the narrowing edits below into one coherent release, then push + tag + update
both tools. Make these edits (in the source):

In `hooks/directive.md`, replace the Persistence section:

```
ACTIVE EVERY RESPONSE for design and architecture questions. No drift back to "here's how to tweak the current code." Still active if unsure.
```

with:

```
ACTIVE EVERY RESPONSE for design and architecture questions — except creating a new feature, building a new component, or adding new functionality from scratch: that territory belongs to obra/superpowers' brainstorming skill, which this plugin is designed to pair with. Rethink still governs narrower tactical-but-architectural questions (e.g. "async or sync," "how should this API be shaped"). No drift back to "here's how to tweak the current code." Still active if unsure. Off only: "stop rethink" / "normal mode".
```

In `skills/rethink-audit/SKILL.md`, add under `## Boundaries`:

```
- **Yield to gated design flows:** if a loaded skill hard-gates a finished design behind interactive requirements-gathering and user approval (e.g. brainstorming) for a new-build request, don't emit a standalone recommendation for it. This audit's niche (clean-slate redesign of an EXISTING subsystem) is distinct from new-build design.
```

and at the end of `## Output`:

```
migrate: is a sequencing sketch, not an implementation plan — no file-level structure, task interfaces, or test steps. Before any code, route the target design + gap to superpowers:writing-plans (or brainstorming first if requirements are unclear); do not execute migrate: steps directly.
```

Append to the `description` field in `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, and `skills/rethink/SKILL.md` frontmatter:

```
 — designed to pair with obra/superpowers' brainstorming skill for new-feature/component design; rethink covers first-principles reasoning for narrower architectural questions.
```

Set one release version in both `.claude-plugin/plugin.json` and
`.codex-plugin/plugin.json` — `1.2.0` if you keep the existing dirty edits as
the (never-released) 1.1.0 content and this narrowing as 1.2.0; pick a single
clean number and make both files agree. Commit, push, and tag on
`eranroseman/rethink`, then update both installs off the pushed release:

```bash
claude plugin marketplace update rethink && claude plugin update rethink@rethink
codex plugin marketplace update rethink && codex plugin update rethink@rethink
```

Verify: both tools report the **same** new version (no longer 1.0.1 vs.
1.1.0), the marketplace clones are clean (`git status` empty, not ahead), and
each tool's loaded `hooks/directive.md` shows the narrowed Persistence
trigger.

### Step 14 — Amend the loader rule + add precedence + vocabulary to `~/.claude/CLAUDE.md`

**First, a policy amendment (your call — it changes your own global rule).**
`~/.claude/CLAUDE.md` rule 1 says "no local CLAUDE.md files," which the
step-16a `main/CLAUDE.md` bridge would violate. But that bridge is a pure
loader (`@AGENTS.md`) — it carries no instructions and doesn't fragment them;
it just makes Claude Code read the project's `AGENTS.md` (which the same rule
already says to do: "checks its own folder for context"). Amend rule 1's
"no local CLAUDE.md files" to:

```
no local CLAUDE.md files (exception: a repo-root CLAUDE.md whose entire content is `@AGENTS.md` — a loader so Claude Code reads the project's AGENTS.md, since it doesn't read AGENTS.md natively; it holds no instructions of its own)
```

If you'd rather not touch the global rule, drop step 16a instead and accept
that Claude Code won't auto-load `AGENTS.md` in this repo (Codex still does,
natively) — a documented Layer-3 gap.

**Then**, append both sections:

```markdown
## Skill precedence

- **Plan Mode:** this harness's native Plan Mode workflow governs entering plan mode. `using-superpowers`'s "brainstorm before plan mode" mandate does not apply here.
- **ponytail vs. brainstorming:** route to brainstorming's design gate only when the request needs a new dependency (fails ponytail's rung 4) or spans multiple independent subsystems or has genuine ambiguity about purpose/constraints/success criteria. Everything else — single-function changes, config tweaks, stdlib/native/existing-dependency solutions — stays on ponytail's fast path.
- **rethink vs. brainstorming:** new-feature/component/from-scratch design → brainstorming's gated flow. Narrower tactical-but-architectural questions (sync vs. async, API shape) → rethink.
- **TDD vs. ponytail:** when `superpowers:test-driven-development` is in effect, its test-first ordering wins over ponytail's code-first default; ponytail still governs size/shape once a test exists.
- **threat-modeling vs. a single finding:** answer a follow-up about one already-flagged finding directly, scoped to it — do NOT launch threat-modeling's 8-phase run. Invoke threat-modeling only for a deliberate whole-codebase audit. (Its own SKILL.md has an upstream; keep this rule here, not there.)
- **caveman vs. the-elements-of-style:** caveman governs live chat terseness only; `the-elements-of-style` governs durable written prose (docs, commit messages, PR/issue text, reports, UI strings) regardless of caveman state.
- **interface-design vs. frontend-design:** review/critique/audit/de-slop of existing UI → interface-design (only it has review commands). New UI: product/dashboard/SaaS/admin/tool/data → interface-design; marketing/landing/campaign/brand → frontend-design; ambiguous → ask.

## Design vocabulary

- `codebase-design`'s module/interface/seam/adapter/leverage/locality terms are canonical when any skill decomposes work into units — read "unit"/"boundary" in `brainstorming`/`writing-plans` as module/seam.
- Before writing a RED test (`superpowers:test-driven-development`), name and confirm the test's seam (per `codebase-design`) first; test only at pre-agreed seams.
```

### Step 15 — Write `~/.codex/AGENTS.md` (currently empty)

Codex gets the same precedence + vocabulary rules as Claude (step 14),
adapted for Codex's toolset, plus the Codex-only security routing.

```markdown
## Skill precedence

- **Planning:** your own planning workflow governs; `using-superpowers`'s "brainstorm before planning" mandate does not override it.
- **ponytail vs. brainstorming:** route to brainstorming's design gate only when the request needs a new dependency (fails ponytail's rung 4) or spans multiple independent subsystems or has genuine ambiguity about purpose/constraints/success criteria. Everything else — single-function changes, config tweaks, stdlib/native/existing-dependency solutions — stays on ponytail's fast path.
- **rethink vs. brainstorming:** new-feature/component/from-scratch design → brainstorming's gated flow. Narrower tactical-but-architectural questions (sync vs. async, API shape) → rethink.
- **TDD vs. ponytail:** when `superpowers:test-driven-development` is in effect, its test-first ordering wins over ponytail's code-first default; ponytail still governs size/shape once a test exists.
- **threat-modeling vs. a single finding:** answer a follow-up about one already-flagged finding (including a codex-security finding) directly, scoped to it — do NOT launch threat-modeling's 8-phase run. Invoke threat-modeling only for a deliberate whole-codebase audit.
- **caveman vs. the-elements-of-style:** caveman governs live chat terseness only; `the-elements-of-style` governs durable written prose (docs, commit messages, PR/issue text, reports, UI strings) regardless of caveman state.
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

### Step 16 — Repo edits (Layer 2 + 3), one worktree, one PR

```bash
git fetch origin
git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/adopt-superpowers -b docs/adopt-superpowers origin/main
cd ~/memoria-vault/worktrees/adopt-superpowers
```

**16a — new file `CLAUDE.md` at repo root** (depends on step 14's global-rule
amendment; skip this sub-step if you chose not to amend the rule), containing
exactly:

```markdown
@AGENTS.md
```

**16b — `AGENTS.md`: replace the entire Skills table** with:

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

**16c — `.agents/playbooks/code-review.md`.** After "## 1. Establish scope",
new final paragraph:

```
**Dispatching this as an isolated review.** When reviewing your own recent work, follow `superpowers:requesting-code-review`'s context-isolation mechanic: dispatch reviewers given only the base/head SHAs and requirements, never your session history. `superpowers:requesting-code-review` (plan-alignment, architecture, production-readiness, merge verdict) and `pr-review-toolkit:code-reviewer` (compliance + bug scan, confidence-gated) run independently — use both, don't substitute one for the other. This playbook's own criteria and report format stay authoritative over both.
```

At the end of "## 4. Report", new bullet:

```
- After presenting findings, apply `superpowers:receiving-code-review`'s discipline: fix Critical immediately, Important before proceeding, note Minor for later, and push back (with reasoning) on a finding that looks wrong.
```

**16d — `.agents/playbooks/verify-change.md`.** One line appended at the end:

```
*(If `superpowers:verification-before-completion` is installed, its claim-honesty discipline complements this playbook. These steps remain authoritative regardless.)*
```

**16e — `.agents/playbooks/exec-plan.md`.** New item 5 in "## Authoring":

```
5. Size tasks using `superpowers:writing-plans`' right-sizing rule (each task independently testable and revertable) — but the deliverable still lands in this file's own template, never a new `docs/superpowers/plans/` file.
```

New section after "## Running", before "## Validating":

```
## Reusing superpowers execution techniques

An ExecPlan's Concrete steps may be executed via `superpowers:subagent-driven-development` (per-task implementer + two-stage reviewer) or `superpowers:executing-plans` (separate-session handoff). This file's own Validation, Progress, Execution log, and Surprises sections remain authoritative — neither technique's plan-file or recovery ledger substitutes for this file's record.
```

**16f — `.agents/templates/exec-plan.md`.** One line in the "Concrete steps"
guidance comment:

```
See ../playbooks/exec-plan.md → "Authoring" item 5 and "Reusing superpowers execution techniques" for optional sizing/execution engines.
```

**16g — `.agents/templates/handoff.md`.** New section appended at the end:

```
## Result

<!-- Filled by the RECEIVER after completing the handoff, not the dispatcher. -->

**Status:** DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED

<!-- What was actually done, any deviation from Expected outputs, and why. -->
```

**16h — `.agents/playbooks/docs-review.md`.** One line at the end of
"## 4. Check terminology and claims":

```
If `the-elements-of-style` is installed, apply its `writing-clearly-and-concisely` rules (active voice, omit needless words) as a prose-clarity pass over changed pages — complementary to this section's terminology and citation checks.
```

**16i — `.agents/playbooks/security-review.md`.** New section appended:

```
## 5. Escalate to a full audit

This playbook is scoped to the current diff. If review surfaces something beyond one change — systemic exposure, unclear trust boundaries, or a request for a standalone assessment — and the `threat-modeling` skill is installed, it runs a full 8-phase STRIDE model as a separate, deliberately-requested activity. Do not reach for it to answer single-finding follow-ups here — resolve those per section 4.
```

Then open the PR (re-confirm auth first — `gh auth status` must show `repo`
scope, or route creation through the GitHub connector):

```bash
gh auth status
git add CLAUDE.md AGENTS.md .agents/playbooks/code-review.md .agents/playbooks/verify-change.md .agents/playbooks/exec-plan.md .agents/templates/exec-plan.md .agents/templates/handoff.md .agents/playbooks/docs-review.md .agents/playbooks/security-review.md
git commit -m "docs: adopt superpowers into AGENTS.md + .agents/ conventions"
git push -u origin docs/adopt-superpowers
gh pr create --base main --fill
gh pr checks --watch
```

### Step 17 — Verify (fresh sessions)

Run §5 in a fresh Claude Code session and a fresh Codex session (plugin and
skill changes need a restart to load).

### Step 18 — Author the toolkit stack document (last step)

Once the stack is installed and verified (steps 1–17), document the whole
thing at **`.agents/toolkit.md`** on `main` — the repo's agent-guidance
home, so it's durable, discoverable, and PR-reviewed; `AGENTS.md` stays the
authority/policy, `toolkit.md` is the "what's available and how to use it"
map. Author it in a worktree and open a PR (`AGENTS.md` §1; `.agents/` is a
sensitive path).

The document covers the **entire** stack, grouped by layer:

- **Layer 1 — generic process (`~/.claude/`, `~/.codex/`):** every plugin and
  skill, one line each on what it does and when to reach for it, with its
  Claude|Codex coverage — `superpowers` (all 13 skills + `using-superpowers`),
  `ponytail`, `rethink`, `grilling`, `caveman`, `codebase-design`, `improve`,
  `interface-design`, `frontend-design`, `the-elements-of-style`,
  `api-design-principles`, `threat-modeling`, `codex-security`,
  `pr-review-toolkit`, `security-guidance`, `obsidian-skills`, plus the
  already-present `dataviz` / `artifact-design` and the Figma MCP.
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
  Codex (plugin or native), and the four residual asymmetries.
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

Verify: `ls .agents/toolkit.md`; every plugin/skill/playbook/template listed
above appears; PR checks pass.

## 5. Validation and acceptance

Presence:

- **superpowers loads (both tools):** fresh Claude session — `claude plugin
  list` shows `superpowers@superpowers` enabled and the skill reminder lists
  13 `superpowers:` skills; fresh Codex session — `codex plugin list` shows
  `superpowers@openai-curated` enabled.
- **gap plugins present:** `ls` confirms
  `~/.claude/skills/{threat-modeling,api-design-principles}`,
  `~/.codex/skills/{writing-clearly-and-concisely,api-design-principles,
  threat-modeling,interface-design,frontend-design}`, the five
  `~/.codex/skills/obsidian-*`/`json-canvas`/`defuddle` folders, and
  `interface-design`/`frontend-design`/`the-elements-of-style` in
  `claude plugin list`.
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
  (`codex-security` = Codex-only; `security-guidance`/`frontend-design` =
  Claude-only). No row names something that is neither installed nor a
  documented asymmetry.
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

- `pr-policy` / `lint` / `cspell` / `markdownlint` pass (docs-only change).

Toolkit doc (step 18):

- `.agents/toolkit.md` exists and lists every Layer-1 plugin/skill, every
  Layer-2 playbook/template/system-map/domain-skill, and the parity ledger —
  cross-check each name against `claude plugin list` / `ls ~/.claude/skills
  ~/.codex/skills .agents/`.

## 6. Idempotence and recovery

- **Re-runnable:** every clone/copy step (3–8) removes its target with
  `rm -rf` **before** the `git clone`/`cp -a`, so a re-run is clean — no
  "clone fails, dir exists" and no stale-content merge. Marketplace
  add/install are idempotent. The `rm -rf` in step 9 is safe to re-run. The
  text edits (steps 10–16) and doc authoring (step 18) overwrite cleanly
  when re-applied.
- **Rollback:** step 1 writes a full backup tarball
  (`~/toolkit-backup-*.tgz`, covering both `skills/` dirs, `~/.claude/CLAUDE.md`,
  and both rethink marketplace clones) — restore from it to undo any
  local change. Also: `claude plugin uninstall` / `codex plugin remove`
  reverse the installs; every file edit's exact pre-edit text is in §4. The
  repo PRs (steps 16, 18) revert by closing unmerged or reverting the squash
  commit.

## 7. Progress

- [ ] 1 — pre-flight cost read
- [ ] 2 — superpowers installed (both tools)
- [ ] 3 — the-elements-of-style installed (Claude plugin, Codex loose)
- [ ] 4 — api-design-principles vendored (both, one skill)
- [ ] 5 — threat-modeling cloned to both tools (mirrored)
- [ ] 6 — codex-security installed (Codex)
- [ ] 7 — interface-design installed (Claude plugin + Codex loose) + frontend-design enabled
- [ ] 8 — obsidian-skills ported to Codex
- [ ] 9 — tdd + grill-me retired
- [ ] 10 — grilling edited (both)
- [ ] 11 — caveman edited (both)
- [ ] 12 — improve edited (both)
- [ ] 13 — rethink edited + version bumped
- [ ] 14 — `~/.claude/CLAUDE.md` precedence + vocabulary added
- [ ] 15 — `~/.codex/AGENTS.md` written
- [ ] 16 — repo worktree, CLAUDE.md + AGENTS.md + 8 `.agents/` files, PR merged
- [ ] 17 — §5 validated in fresh sessions, transcripts in §11
- [ ] 18 — `.agents/toolkit.md` authored (entire stack), PR merged

## 8. Execution log

- {{ filled while running }}

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

## 10. Interfaces & dependencies

- **Edited in place (directly editable, no upstream):** `rethink` (its
  marketplace repo); loose skills `grilling`, `caveman`, `improve`.
- **Never edited (third-party upstreams):** `ponytail`, `superpowers`,
  `threat-modeling`, `codex-security`, `interface-design`, `frontend-design`,
  `the-elements-of-style`, `obsidian-skills`, `api-design-principles` source.
  Cross-references for these go in `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`.
- **New tool-config files:** `~/.codex/AGENTS.md` (was empty).
- **Installed/vendored:** superpowers (both), the-elements-of-style (Claude
  plugin + Codex loose), api-design-principles (loose both), threat-modeling
  (Claude clone + Codex mirror), codex-security (Codex), interface-design
  (Claude plugin + Codex loose), frontend-design (Claude enable + Codex
  `am-will/codex-skills` loose, unlicensed/personal-use), obsidian-skills
  (Codex loose copy).
- **Repo files:** new `CLAUDE.md`, `AGENTS.md`,
  `.agents/playbooks/{code-review,verify-change,exec-plan,docs-review,
  security-review}.md`, `.agents/templates/{exec-plan,handoff}.md` (one PR,
  step 16); new `.agents/toolkit.md` documenting the whole stack (a second
  PR, step 18).
- **Retired:** `~/.claude/skills/{tdd,grill-me}`, `~/.codex/skills/tdd`.
- **Declined, never installed:** official Anthropic `code-review` plugin;
  `coderabbit@openai-curated`.

## 11. Artifacts & notes

- {{ command transcripts pasted here as the plan runs }}

## 12. Outcomes & retrospective

- **Shipped:** {{ fill at close }}
- **Still open:** {{ fill at close — including the step-5/step-7 decisions }}
- **Lessons:** {{ fill at close }}
