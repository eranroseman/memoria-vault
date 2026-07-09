# Harness goal audit — 2026-07-09

Full-stack audit of the agent harness (system prompt, global CLAUDE.md/AGENTS.md
files, hooks, plugins, skills, `.agents/`, GitHub machinery), asking: what is the
harness for, and which parts work against that goal. Evidence: 9-agent parallel
sweep (`wf_d618c956-c73`, 910k tokens, 204 tool calls, full file coverage per
layer; several findings empirically tested — the PreToolUse hook was executed
against real paths, ponytail's mode-state code was traced and observed live).

Supersedes nothing; complements `exec-plan-adopt-superpowers.md` (Jul 6–7, now
retired from this folder, recoverable at scratch commit `06c044e9`), which built
the current toolkit. This audit evaluates that toolkit's result.

---

## 1. Goal characterization (confirmed with Eran, 2026-07-09)

A one-person software organization staffed by AI agents, memoria-vault as
flagship tenant:

- **Superpowers is the spine** — brainstorm → spec → plan → SDD execution →
  two-stage review → verified finish. Ponytail, caveman, grilling, improve are
  enhancers patching specific LLM failure modes. Rethink is a packaged prompt,
  not a pillar.
- **Correctness enforced by mechanism, not trust** — hooks, doctors, CI,
  rulesets, worktree isolation. Also Memoria's product thesis: the repo is a
  proving ground for its own philosophy.
- **Minimal artifacts, unconstrained verification spend** (Eran's explicit
  answer: minimalism is about artifact shape / correctness, not cost).
- **Division of labor, not generic parity**: Claude plans, Codex executes,
  Kilo test-drives models only.
- **Reuse upstream** — adopt maintained plugins, arbitrate locally, keep
  upstream improvements for the major ones.

## 2. Headline finding

The harness holds the repo to two rules — "zero tolerated contradictions" and
"enforcement is a mechanism, not a label" — that the harness layer itself
violates. The instruction stack has no doctor; its contradictions are patched
by an O(N²) pairwise precedence table (10 rules in `~/.claude/CLAUDE.md`, a
diverged 12-rule copy in `~/.codex/AGENTS.md`).

## 3. Ranked findings

### A. Enhancers contaminating the spine

- **Ponytail `/ponytail-review` is a sticky mode** (`ponytail-mode-tracker.js`
  persists mode `review` to the user-global `~/.claude/.ponytail-active`);
  every subsequent subagent — including SDD reviewers and verification agents —
  is injected with a mode whose skill text declares correctness "explicitly out
  of scope." One diff review silently converts the review fleet to
  complexity-only until session end. HIGH.
- Ponytail's SubagentStart hook injects into **every** subagent regardless of
  task, against its own "not for non-coding requests" rule (observed live on
  this audit's own subagents). Mode state is one user-global file, so
  concurrent sessions clobber each other's level.
- Rethink claims "ACTIVE EVERY RESPONSE" but has **no SubagentStart hook** —
  delegated design work runs ponytail-only. Ponytail and rethink give opposite
  orders on read-order (reuse-what-exists-first vs look-at-current-code-last);
  no precedence rule resolves it.
- Interface-design vs ponytail collide on ponytail's canonical example
  (`<input type="date">` native vs "compose a headless primitive").

### B. The spine contradicts repo law

- `finishing-a-development-branch` offers **local merge to main** as option 1
  (ruleset GH013 blocks it only at push time).
- `brainstorming`/`writing-plans` commit specs/plans to
  `docs/superpowers/{specs,plans}/` on the working branch → fails docs-doctor
  CI, violates scratch-branch plan policy.
- `using-git-worktrees` asks consent, defaults to `.worktrees/`, commits
  `.gitignore` changes — vs AGENTS.md's unconditional
  `~/memoria-vault/worktrees/<session>`; `finishing-a-development-branch` then
  claims cleanup ownership of anything under `worktrees/`.
- Internal: SDD task-reviewer prompt says "do not re-run the suite" two
  paragraphs after "treat the implementer's report as unverified claims";
  `verification-before-completion` forbids trusting agent reports. Orphaned
  spec/plan reviewer templates contradict their skills' inline self-review.
- Superpowers enforces via persuasion prose only (its own
  `persuasion-principles.md`); zero mechanical gates.

### C. Stale/foreign machinery

- **pr-review-toolkit**: hard-codes claude-cli-internal (TypeScript/React)
  standards presented as "the established coding standards from CLAUDE.md";
  instructs `git add -A`; competing severity vocabulary; the only major plugin
  the precedence table never routes. HIGH — disable.
- `improve` hard-codes tracked `plans/` output vs scratch-branch policy (needs
  adapter, not removal — named enhancer).
- Dead: `~/.claude/skills/obsidian-skills/` (undiscoverable + shadowed by the
  obsidian plugin), `api-design-principles` (no consumer), ponytail-gain
  (cost-marketing, off-goal per §1), Codex's older maximalist frontend-design
  copy.

### D. Unenforced / misdescribed boundaries (empirically tested)

- The PreToolUse write-perimeter hook, with sessions launched at the container,
  **silently allows** writes into `main/`, `scratch/`, and other sessions'
  worktrees; the container `CLAUDE.md` symlink realpath-resolves into
  `main/AGENTS.md` (pr-policy-sensitive) and is silently allowed. It hard-denies
  editing a policy-legal worktree loader CLAUDE.md. Guards the outside,
  ignores the inside.
- Three-way scratch contradiction: system prompt mandates the session
  scratchpad; global CLAUDE.md forbids it; the hook asks on every scratchpad
  write.
- Plan storage: `plansDirectory: "./claude-plans"` has never existed anywhere;
  10 real plans sit in `~/.claude/plans` (outside the vault); repo policy says
  scratch branch.
- AGENTS.md authority stack says globals carry "cross-project tool routing
  only" — false for `~/.claude/CLAUDE.md` (six behavioral sections), true for
  `~/.codex/AGENTS.md` (which therefore lacks the entire behavioral core).
  12 of 14 `~/.codex/skills` are hand-copied mirrors, already drifting.
- Codex `writable_roots` grants nonexistent `~/Memoria-test` and empty `~/mv`
  (aborted container migration, Jul 4). `.kilo/` carries a firebase MCP with
  zero policy attached.
- Small repo-doc defects: `security-review.md` §4 self-reference; exec-plan
  template cites a renamed playbook heading; toolkit.md "prose-clarity skill"
  alias.

### E. Context tax

Ponytail's hardware paragraph + statusline nag re-injected every session;
superpowers' full using-superpowers text re-injected on every compaction;
threat-modeling's 11 MB consultancy apparatus; account-level MCP connector pile
(PubMed, Clinical Trials, Gmail, Canva…) taxing coding sessions.

## 4. Decision (Eran, 2026-07-09): full alignment with superpowers

Chosen over lane-charter scoping. Superpowers' conventions become the repo's
conventions; the repo supplies only facts (tests + verify command, ~15-line
AGENTS.md, sandbox rule) and one mechanical gate (require-PR + single `verify`
check). Committed dated specs/plans in `docs/superpowers/` are records, not
mirrors — they cannot drift because they never claim to describe the present,
so they need no doctor. Anti-drift machinery, pr-policy tiers, doctors, maps,
scratch branch, ExecPlan playbook, container multi-checkout layout: all retire.
Earn-back triggers recorded in the alignment plan.

Execution: see `superpowers-alignment-plan.md` (same folder).
