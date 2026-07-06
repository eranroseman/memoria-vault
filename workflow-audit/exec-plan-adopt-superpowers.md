# ExecPlan — Adopt github.com/obra/superpowers into the agent skill toolkit

## 0. Metadata

- **Task:** Install the `obra/superpowers` Claude Code plugin (skills:
  systematic-debugging, TDD, brainstorming, code-review discipline, plan
  writing/execution, git-worktree/branch-finishing helpers, writing-skills) for
  both Claude Code and Codex, retire the now-superseded local `tdd` skill, and
  verify the combined toolkit triggers cleanly.
- **Worktree / branch:** None on `memoria-vault` — this task's deliverable is
  entirely outside this repository's tracked tree (`~/.claude/skills/`,
  `~/.claude/plugins/`, `~/.codex/skills/`, `~/.codex/plugins/` are per-user
  tool configuration, not repo content), so `AGENTS.md` §1's git-worktree setup
  does not apply to the *implementation* steps. It does apply to this plan
  file itself: authored and committed on the **`scratch`** branch at
  `~/memoria-vault/scratch`, per "Scratch branch flow" — filed under
  `scratch/workflow-audit/` (this repo's holding area for cross-cutting,
  non-release-scoped plans), not under a `releases/<version>/` folder.
- **Related decisions:** — (this is agent-tooling/workflow adoption, not a
  Memoria product or architecture decision, so it does not require a release
  decision-ledger entry; if any step here turns out to affect how a *shipped*
  Memoria feature works, capture that separately in the active release's
  `decisions.md`, e.g. `releases/0.1.0-alpha.17/decisions.md`, first)
- **Related issues / milestone:** — (personal tooling, not release-scoped;
  milestone `0.1.0` is unaffected)
- **Started:** 2026-07-06 · **Last updated:** 2026-07-06

## 1. Purpose / big picture

The agent's personal skill toolkit already includes `ponytail` (anti-over-
engineering), `rethink` (this session's own first-principles design plugin),
and five individually cherry-picked skills adopted earlier this session:
`grilling`, `tdd`, `codebase-design`, `improve`, `caveman`. This plan adds
`obra/superpowers` — a mature, ~1M-install Claude Code plugin (v6.1.1, MIT,
maintained by Jesse Vincent) bundling 14 skills for systematic debugging,
test-driven development, idea-to-spec brainstorming, code-review discipline
(both requesting and receiving), plan writing/execution, git-worktree setup,
branch-finishing, and skill-authoring itself.

What becomes observable: after this plan, `/superpowers:systematic-debugging`,
`/superpowers:test-driven-development`, and the other eleven adopted skills
appear in the "available skills" list for both Claude Code and Codex sessions
in this environment, the standalone `tdd` skill (adapted earlier from
`mattpocock/skills`) is gone (its two unique ideas folded into the superseding
skill), and no skill in the combined toolkit has a dangling cross-reference to
a name that doesn't exist.

**Why the earlier plan (hand-cherry-pick individual files) was abandoned:** an
adversarial re-verification (8 independent agents, each re-reading primary
sources rather than trusting the prior summary) found that 13 of the 14
superpowers skills clear the adoption bar — including two cases
(`using-git-worktrees`, `finishing-a-development-branch`) where the original
"structural conflict with this repo's conventions" claim was an outright
misreading of the skill's own text, not a real conflict. Once nearly the
whole bundle clears, hand-copying 13 individually-adapted files is needless
duplication of effort the plugin mechanism already solves — `obra/superpowers`
ships its own `.claude-plugin/marketplace.json` **and** `.codex-plugin/
plugin.json`, so installing it as an actual plugin (not loose skill files)
gets both tools, working internal cross-references between its own skills,
and update tracking for free.

## 2. Context and orientation

**What a "skill" is here:** a folder under a tool's skills directory
(`~/.claude/skills/<name>/` for Claude Code, `~/.codex/skills/<name>/` for
Codex) containing a `SKILL.md` file with a YAML frontmatter `name` +
`description` (the trigger the model matches against) and a markdown body
(loaded only once triggered). A "plugin" is a bundle of skills plus optional
hooks/scripts, installable as one unit via a marketplace manifest.

**What's already installed, for context (not touched by this plan):**

| Name | Kind | Source |
|---|---|---|
| `ponytail` | plugin (hooks-based, always-on) | `DietrichGebert/ponytail` |
| `rethink` | plugin (hooks-based, always-on) | `eranroseman/rethink` (this session's own repo) |
| `grilling` | loose skill | cherry-picked from `mattpocock/skills` |
| `tdd` | loose skill | cherry-picked from `mattpocock/skills` — **retired by this plan** |
| `codebase-design` | loose skill (+2 reference files) | cherry-picked from `mattpocock/skills` |
| `improve` | loose skill (+3 reference files) | cherry-picked from `shadcn/improve` |
| `caveman` | loose skill (skill-only, no hooks/MCP) | cherry-picked from `JuliusBrussee/caveman` |

Each loose skill above lives identically at both
`~/.claude/skills/<name>/SKILL.md` and `~/.codex/skills/<name>/SKILL.md`
(Codex confirmed via its own `skill-creator`/`skill-installer` system skills
to auto-discover `$CODEX_HOME/skills/<name>/SKILL.md`, defaulting to
`~/.codex/skills` — the same shape as Claude Code's convention).

**What `obra/superpowers` provides (the 14 skills, all now verified to clear
adoption — see the re-verification results below):**

| Skill | Role |
|---|---|
| `systematic-debugging` | root-cause-first debugging discipline (4-phase method) — the original reason this plugin was flagged |
| `test-driven-development` | red-green-refactor discipline — **supersedes** the locally cherry-picked `tdd` |
| `brainstorming` | idea → written, committed design spec, before any implementation skill runs |
| `receiving-code-review` | how to evaluate feedback (verify, push back with reasoning) — distinct from every review skill that *produces* reviews |
| `requesting-code-review` | dispatch a reviewer subagent with plan-alignment checking and explicit context isolation |
| `writing-plans` | spec → rigorously decomposed, TDD-disciplined implementation plan (pre-code entry point; distinct from `improve`'s post-audit-finding plan template) |
| `writing-skills` | TDD-for-skill-authoring; the Skill Discovery Optimization section is a genuinely sharp, evidence-backed insight (a description that summarizes a skill's workflow causes the model to follow the shorter description instead of reading the skill body) |
| `verification-before-completion` | broader "no completion claims without fresh evidence" rule — complements, doesn't duplicate, the existing narrower `verify` skill |
| `using-git-worktrees` | isolated-workspace setup; its own priority order ("check your instructions for a declared preference first") already defers to `AGENTS.md`'s worktree convention before ever reaching its generic default |
| `finishing-a-development-branch` | branch-completion menu (merge/PR/keep/discard); one behavioral note applies in this repo, see §9 |
| `dispatching-parallel-agents` | judgment layer for parallel subagent dispatch (independence criteria, prompt-construction discipline) — complementary to, not redundant with, this environment's Workflow tool mechanics |
| `subagent-driven-development` | same-session plan execution: two-axis per-task review, model-tiering, file-based task-brief/report handoffs, compaction-recovery ledger |
| `executing-plans` | separate/parallel-session plan execution with human checkpoints — the other branch of the same decision tree as `subagent-driven-development`, not an inferior fallback |
| `using-superpowers` | the bundle's own onboarding/skill-discovery meta-skill; installed automatically as part of the plugin, not independently meaningful |

**Re-verification evidence (why every "decline" from the first pass was
overturned):** a Workflow run (`wf_6aecf5d4-a9f`, 8 parallel agents,
317,981 tokens, 45 tool calls) re-checked every contested skill against
primary sources. Full verdicts are in that run's `journal.jsonl`
(`/home/eranr/.claude/projects/-home-eranr-memoria-vault/086d8e17-f30f-4fe2-ae4d-ec173bd1fed8/subagents/workflows/wf_6aecf5d4-a9f/journal.jsonl`);
the two corrected misreadings worth remembering verbatim:

- `using-git-worktrees`'s Step 1b priority order is *"1. Check your
  instructions for a declared worktree directory preference... 2. Check for
  an existing project-local worktree directory... 3. If there is no other
  guidance available, default to `.worktrees/`."* Item 3 (the one the first
  pass treated as the skill's behavior) is structurally unreachable in this
  repo, because `AGENTS.md` always satisfies item 1.
- `finishing-a-development-branch`'s "Option 1: Merge locally" executes
  `git checkout <base>; git pull; git merge <feature>; <test>; git branch -d`
  — it never pushes. The claimed GH013 (no-direct-push-to-main) failure
  cannot occur because nothing in that option pushes.

## 3. Plan of work

Install `obra/superpowers` as an actual plugin on both Claude Code and Codex,
rather than hand-copying files — this preserves the bundle's own internal
cross-references (e.g. `subagent-driven-development` calling out to
`superpowers:test-driven-development`, `superpowers:using-git-worktrees`,
etc.) for free, since every skill it references is being installed under its
original name.

The one real consolidation this plan performs is retiring the standalone
`tdd` skill: `test-driven-development` from superpowers covers the same
discipline with more agentic-context rigor (an explicit "Iron Law," an
11-row rationalization table, a debugging-integration cross-reference to
`systematic-debugging`), and two other newly-installed skills already
address it by that exact name. `tdd` has two ideas the superpowers version
lacks — pre-agreeing test "seams" (boundaries) with the user before writing
any test, and an explicit anti-pattern name for horizontal-slicing (writing
all tests before all implementation) — small enough to fold into the
installed skill as a short addendum rather than justifying two competing
TDD skills.

Two items surfaced by the re-verification are **behavioral notes for this
repo, not file edits**, so they are recorded here rather than as a
implementation step: (1) `finishing-a-development-branch`'s "Option 1: merge
locally" is technically valid but produces a local, unpushed merge commit
that doesn't fit this repo's squash-via-PR-only convention — treat it as not
applicable here and route to Option 2, then continue into `AGENTS.md`'s real
PR flow (`gh pr create` → `gh pr checks --watch` → `gh pr merge --squash
--delete-branch` from `~/memoria-vault/main`); (2) the skill's "keep options
concise, no explanation" menu style is subordinate to `AGENTS.md` line 6
("give pros/cons and a recommendation for every option"), which `AGENTS.md`
itself licenses overriding ("skills implement this file's policy; they do
not override it").

`dispatching-parallel-agents` describes its parallel-dispatch mechanic as
"issue all subagent dispatches in the same response" — accurate for vanilla
Claude Code, and still functionally correct here (multiple `Agent` tool
calls in one response do run concurrently in this environment too), so no
edit is required; the Workflow tool's `parallel()`/`pipeline()` are an
additional, more structured option worth knowing about but not a
correctness fix.

## 4. Concrete steps

1. **Commit and push this plan file** (scratch branch flow, `AGENTS.md` →
   "Scratch branch flow" — this step has already run for the file you are
   reading; skip if resuming):

   ```bash
   cd ~/memoria-vault/scratch
   git pull --ff-only origin scratch
   git add scratch/workflow-audit/exec-plan-adopt-superpowers.md
   git commit -m "scratch: exec-plan for adopting obra/superpowers"
   git push origin HEAD:scratch
   ```

   Expected: push succeeds, no conflicts (only this plan's own new file is
   staged — do not `git add -A`; an unrelated uncommitted file,
   `releases/0.1.0-alpha.17/0.1.0-alpha.17-host-stack-evaluation.md`, is
   present in this shared scratch worktree from other in-progress work and
   must be left untouched).

2. **Install the plugin for Claude Code:**

   ```bash
   claude plugin marketplace add obra/superpowers
   claude plugin install superpowers@superpowers
   ```

   Expected: marketplace registers `superpowers` (owner Jesse Vincent,
   v6.1.1); plugin installs 14 skills under
   `~/.claude/plugins/cache/superpowers/superpowers/<version>/skills/`.

3. **Install the plugin for Codex:**

   ```bash
   codex plugin marketplace add obra/superpowers
   codex plugin add superpowers@superpowers
   ```

   Expected: same 14 skills registered under Codex's plugin cache
   (`~/.codex/plugins/cache/superpowers/...`), using the repo's own
   `.codex-plugin/plugin.json`.

4. **Retire the standalone `tdd` skill, folding in its two unique ideas.**
   First locate the installed `test-driven-development/SKILL.md` under the
   Claude Code plugin cache from step 2 (path includes the installed
   version, e.g. `.../superpowers/6.1.1/skills/test-driven-development/
   SKILL.md`) and read `~/.claude/skills/tdd/SKILL.md` for the "Seams" and
   horizontal-vs-vertical-slicing sections to port over. Add a short
   `## Seams (this environment's addendum)` section covering: pre-agree
   testing boundaries with the user before writing the first test; don't
   write all tests before all implementation (one seam → one test → one
   minimal implementation per cycle, a "tracer bullet"). Mark the addition
   with an inline comment noting it is a local patch that may need
   reapplying after a future `claude plugin update superpowers` (the
   ceiling of this shortcut, named per this environment's own
   deliberate-shortcut convention). Repeat the same short addition on the
   Codex-side installed copy.

   Then remove the superseded standalone skill from both tools:

   ```bash
   rm -rf ~/.claude/skills/tdd
   rm -rf ~/.codex/skills/tdd
   ```

5. **Verify the combined skill list.** Start a fresh Claude Code session in
   this repo and confirm the "available skills" system reminder lists
   `superpowers:systematic-debugging`, `superpowers:test-driven-development`,
   `superpowers:brainstorming`, `superpowers:receiving-code-review`,
   `superpowers:requesting-code-review`, `superpowers:writing-plans`,
   `superpowers:writing-skills`, `superpowers:verification-before-
   completion`, `superpowers:using-git-worktrees`, `superpowers:finishing-a-
   development-branch`, `superpowers:dispatching-parallel-agents`,
   `superpowers:subagent-driven-development`, `superpowers:executing-plans`
   — and that `tdd` (unnamespaced) is absent. Repeat for a fresh Codex
   session.

## 5. Validation and acceptance

- **Claim:** Given the plugin installed for Claude Code, when a new session
  starts, then the skill list includes all 13 superpowers skills listed in
  §2 (excluding the meta-skill `using-superpowers`, which is not separately
  invoked).
  - **Prove with:** start a fresh session in `~/memoria-vault/main`; capture
    the "available skills" system-reminder text; `grep -c "superpowers:"` on
    it should return `13`.
- **Claim:** Given the plugin installed for Codex, when a new session
  starts, then the equivalent 13 skills are discoverable.
  - **Prove with:** `codex` session start; inspect the skill list the same
    way, or `find ~/.codex/plugins/cache/superpowers -iname SKILL.md | wc -l`
    → `14` (includes `using-superpowers`).
- **Claim:** Given `tdd` is retired, when either tool's skill list is
  checked, then no unnamespaced `tdd` entry remains.
  - **Prove with:** `ls ~/.claude/skills/ ~/.codex/skills/` — `tdd` absent
    from both; `superpowers:test-driven-development` present in the skill
    list instead.
- **Claim:** Given the seams/vertical-slicing addendum was folded in, when
  the installed `test-driven-development/SKILL.md` is read, then it contains
  both the original superpowers content and the addendum section.
  - **Prove with:** `grep -A5 "Seams (this environment" <installed-path>`
    on both tools' copies.
- **Claim:** Given no skill in the combined toolkit has a dangling
  cross-reference, when every "superpowers:<name>" or bare skill-name
  reference inside any installed SKILL.md is checked, then each resolves to
  an actually-installed skill.
  - **Prove with:** `grep -rhoE 'superpowers:[a-z-]+' ~/.claude/plugins/cache/superpowers/*/skills/*/SKILL.md | sort -u`, cross-check each name against the installed skill directory listing.

## 6. Idempotence and recovery

- **Safe to re-run:** `claude plugin marketplace add`/`install` are
  idempotent (re-running against an already-added marketplace/installed
  plugin is a no-op or version-check, not a duplicate install). Step 4's
  `rm -rf` on `tdd` is safe to re-run (no-op if already removed).
- **Rollback:** `claude plugin uninstall superpowers@superpowers` and
  `claude plugin marketplace remove obra/superpowers` (and Codex
  equivalents) fully reverse steps 2–3. To restore the retired `tdd` skill,
  its content is preserved in this plan's git history (this repo's own
  `scratch` branch commit that authored `~/.claude/skills/tdd/SKILL.md`
  originally — recover via the session transcript or by re-adapting from
  `mattpocock/skills` `skills/engineering/tdd/` per the earlier session's
  process) — since `~/.claude/skills/` is outside this repo, there is no
  git history for the file itself, only this plan's record of its origin.

## 7. Progress

- [ ] {{ fill in when run }} — plan file committed and pushed to `origin/scratch`
- [ ] {{ fill in when run }} — plugin installed for Claude Code, marketplace + `superpowers@superpowers`
- [ ] {{ fill in when run }} — plugin installed for Codex
- [ ] {{ fill in when run }} — seams/vertical-slicing addendum folded into installed `test-driven-development` (both tools)
- [ ] {{ fill in when run }} — standalone `tdd` removed from both tools
- [ ] {{ fill in when run }} — skill-list verification claims in §5 all proven, transcripts pasted into §11
- [ ] release/checkpoint close only — N/A (personal tooling, not a Memoria release deliverable; no `design-history/` update needed)

## 8. Execution log

- {{ to be filled while running — tactical/sequencing choices only;
  architectural decisions go to a release decision ledger, not here, and
  none are expected for this task }}

## 9. Surprises & discoveries

- {{ to be filled while running }}
- (Carried in from research, not a surprise during *this* plan's execution,
  but worth keeping visible: two of the original decline verdicts for
  `using-git-worktrees` and `finishing-a-development-branch` were outright
  misreadings of the skill text, not defensible caution — see §2's
  re-verification note. Recorded here so a future reader doesn't re-derive
  the same mistake from a stale summary.)

## 10. Interfaces & dependencies

- **Plugin source:** `github.com/obra/superpowers`, v6.1.1, MIT license.
  Manifests: `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`
  (Claude Code), `.codex-plugin/plugin.json` (Codex). Also ships
  `.cursor-plugin/`, `.kimi-plugin/`, `.opencode/`, `.pi/extensions/` —
  irrelevant to this plan (this environment only uses Claude Code + Codex).
- **Hook installed:** `hooks/session-start` (bash) — injects
  `skills/using-superpowers/SKILL.md` as SessionStart context, cross-platform
  (Cursor/Claude/Copilot output-shape detection). Read and verified
  benign — no network calls, no data exfiltration, matches the risk profile
  of the already-installed `rethink`/`ponytail` session-start hooks.
  Contrast with the `JuliusBrussee/caveman` plugin evaluated earlier this
  session, which was *not* installed as a full plugin because its hooks
  additionally bundle an MCP server and cross-tool config installer — no
  such additional surface exists in `obra/superpowers`.
- **Superseded local skill:** `~/.claude/skills/tdd/` and
  `~/.codex/skills/tdd/` (adapted earlier this session from
  `mattpocock/skills` `skills/engineering/tdd/`, MIT). Retired by step 4.
- **Untouched local skills (verified no new conflict):** `grilling`,
  `codebase-design`, `improve`, `caveman` — none share a trigger-description
  niche with any of the 13 adopted superpowers skills (spot-checked during
  the original adoption pass and again during the re-verification; no
  overlap surfaced).
- **This repo's conventions superpowers skills must respect (behavioral,
  not code):** `AGENTS.md` §1 (worktree isolation — `using-git-worktrees`
  already defers to it), "PR flow" + "Merge discipline" (squash-only, via
  PR — `finishing-a-development-branch`'s Option 1 is not applicable here),
  line 6 ("pros/cons + recommendation for every option" — overrides the
  skill's default concise-menu style).

## 11. Artifacts & notes

- {{ command transcripts from steps 2-5, pasted here as the plan runs }}

## 12. Outcomes & retrospective

- **Shipped:** {{ fill at close }}
- **Still open:** {{ fill at close — e.g. any skill-list verification that
  didn't pass, follow-up issues }}
- **Routed to:** N/A — no decision-ledger or design-history entries expected
  for this task (personal tooling adoption, not a Memoria product change)
- **Lessons:** {{ fill at close — e.g. the value of adversarial
  re-verification before declining a well-adopted external tool on a first
  read }}
