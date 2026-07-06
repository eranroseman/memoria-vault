# ExecPlan — Adopt github.com/obra/superpowers into the agent skill toolkit

## 0. Metadata

- **Task:** Install the `obra/superpowers` plugin (13 usable skills:
  systematic-debugging, test-driven-development, brainstorming,
  receiving-code-review, requesting-code-review, writing-plans,
  writing-skills, verification-before-completion, using-git-worktrees,
  finishing-a-development-branch, dispatching-parallel-agents,
  subagent-driven-development, executing-plans — plus the bundle's own
  onboarding meta-skill `using-superpowers`) for both Claude Code and Codex;
  retire the superseded local `tdd` skill; **retire, adapt, or cross-reference
  every existing skill and repo convention this bundle collides with or
  duplicates** (not just install the new thing); and verify the combined
  toolkit behaves correctly, not merely that the skill list shows the new
  names.
- **Worktree / branch:** None on `memoria-vault` for the *implementation* —
  the skill/plugin files live under `~/.claude/` and `~/.codex/` (per-user
  tool config, not repo content), so `AGENTS.md` §1's git-worktree setup does
  not apply there. It does apply to two specific `memoria-vault`-tracked
  edits this plan makes (`AGENTS.md` and four files under `.agents/`) — those
  go through the normal worktree → branch → PR flow, not a direct edit on
  `main`. This plan file itself lives on the **`scratch`** branch under
  `scratch/workflow-audit/` (this repo's holding area for cross-cutting,
  non-release-scoped plans).
- **Related decisions:** One open judgment call this plan surfaces but does
  not resolve unilaterally — see §9 ("ponytail vs. brainstorming process
  ceremony"). Everything else below is a verified conflict or gap with a
  concrete fix, not a product/architecture decision, so no release
  decision-ledger entry is otherwise needed.
- **Related issues / milestone:** — (personal tooling + repo-doc
  consistency, not release-scoped; milestone `0.1.0` is unaffected)
- **Started:** 2026-07-06 · **Last updated:** 2026-07-06 (revised after two
  adversarial cross-check workflows plus direct verification of CLI syntax,
  config state, and the bundle's own onboarding skill)

## 1. Purpose / big picture

Earlier passes of this plan covered "what to add": install `obra/superpowers`,
retire the redundant local `tdd`, done. Two follow-up reviews (prompted by
direct pushback — "your plan includes what needs to be added, but doesn't
include what needs to be retired or adapted... it also doesn't cover
duplicated existing skills") found that framing was incomplete in a way that
would have caused real, observable problems after "successful" installation:
contradictory instructions firing simultaneously (ponytail vs. TDD on test
timing), a design-gate skill silently bypassed (rethink vs. brainstorming), a
routing ambiguity between two interview-style skills (grilling vs.
brainstorming), a vocabulary drift risk in the very addendum this plan
planned to author (a third, inconsistent definition of "seam"), and — found
independently, not by either review — a direct collision between the
bundle's own mandatory onboarding skill and this harness's native Plan Mode
workflow.

What becomes observable when this plan is actually complete: the 13
superpowers skills work in both tools *and* nothing already installed gives
contradictory guidance when they fire together *and* this repo's own
`.agents/` conventions either absorb the new capability with an explicit
cross-reference or explicitly document why they don't need to.

## 2. Context and orientation

**Verified environment facts** (empirically checked this session, not
assumed):

- `claude plugin` subcommands, confirmed via `claude plugin --help` /
  `claude plugin marketplace --help`: `marketplace add <source>`,
  `install|i <plugin>`, `uninstall|remove <plugin>`, `update <plugin>`
  ("restart required to apply"), `details <name>` (component inventory +
  **projected token cost**, always-on vs. on-invoke, per component — ran
  against the already-installed `rethink@rethink` as a dry run: `~223 tok`
  always-on for its 2 skills + 1 hook), `list` (splits "Installed plugins"
  from "Skills-directory plugins (.claude/skills/*)" — the latter only
  auto-detects skill folders that themselves contain a nested plugin
  manifest, e.g. `obsidian-skills`; loose skill folders like `grilling` or
  the soon-to-be-installed superpowers skills' *cherry-picked* siblings do
  **not** appear there — verify those via the "available skills" system
  reminder instead, not `claude plugin list`).
- `~/.claude/settings.json` registers plugins as
  `"enabledPlugins": {"<plugin>@<marketplace>": true}` plus
  `"extraKnownMarketplaces": {"<name>": {"source": {"source": "github",
  "repo": "<owner>/<repo>"}}}` — confirmed by reading the existing
  `ponytail@ponytail` / `rethink@rethink` entries. Installing superpowers
  should add exactly one new key to each map.
- `~/.codex/config.toml` registers the identical shape under
  `[marketplaces.<name>]` / `[plugins."<name>@<name>"]` — confirmed by
  reading the existing `ponytail`/`rethink` sections. `[features]
  multi_agent = true` (required for `dispatching-parallel-agents` and
  `subagent-driven-development` to spawn subagents on Codex, per
  `using-superpowers/references/codex-tools.md`) **is already set** — no
  config change needed there, only verification that it stays set.
- **Hook coexistence is already empirically proven, not a remaining risk**:
  this very session's own SessionStart output showed ponytail's hook
  ("PONYTAIL MODE ACTIVE") and rethink's hook ("RETHINK MODE ACTIVE") fire as
  two independent, additive `<system-reminder>` blocks. Superpowers' third
  `hooks/session-start` (read in full: pure read-and-inject, cross-platform
  output-shape detection, no network calls, no data exfiltration — same risk
  class as the other two) will coexist the same way.
- **`using-superpowers` — the bundle's onboarding meta-skill, installed
  automatically as part of the plugin — is not a passive footnote.** Read in
  full (not just its frontmatter, which is all the earlier passes checked):
  it is a standing, aggressively-worded mandate — *"IF A SKILL APPLIES TO
  YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT... not negotiable...
  you cannot rationalize your way out of this"* — with an explicit line,
  *"Before entering plan mode: if you haven't already brainstormed, invoke
  the brainstorming skill first,"* and a worked example, *"'Let's build X' →
  superpowers:brainstorming first, then implementation skills."* This
  directly targets the same trigger surface as (a) this harness's own
  native Plan Mode workflow (Explore → Design → Review → write a plan file →
  `ExitPlanMode`, used earlier this session for the docs-review task) and
  (b) `rethink`'s own always-on directive ("ACTIVE EVERY RESPONSE for design
  and architecture questions"). Its own text supplies the resolution
  mechanism: *"User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc,
  direct requests) take precedence over skills... Only skip skill workflows
  ... when your human partner has explicitly told you to."* This plan uses
  that mechanism (§4 step 6) rather than editing the vendored skill file.

**What's already installed, for context:**

| Name | Kind | Source |
|---|---|---|
| `ponytail` | plugin (hooks-based, always-on), v4.7.0 | `DietrichGebert/ponytail` |
| `rethink` | plugin (hooks-based, always-on), v1.1.0 | `eranroseman/rethink` (this session's own repo) |
| `grilling` | loose skill | cherry-picked from `mattpocock/skills` |
| `tdd` | loose skill | cherry-picked from `mattpocock/skills` — **retired by this plan** |
| `codebase-design` | loose skill (+2 reference files) | cherry-picked from `mattpocock/skills` |
| `improve` | loose skill (+3 reference files) | cherry-picked from `shadcn/improve` |
| `caveman` | loose skill (skill-only, no hooks/MCP) | cherry-picked from `JuliusBrussee/caveman` |

**What `obra/superpowers` provides**, and the disposition each got after two
rounds of adversarial re-checking against primary sources (full per-skill
role table carried over from the prior revision, omitted here for length —
unchanged): all 13 usable skills clear adoption; the specific conflicts and
gaps found are enumerated in §3.

**Evidence trail:** two Workflow runs —
`wf_dbbeb04c-e04` (personal-skill duplication check, 6 agents, 334,037
tokens) and `wf_4f8a76cf-7c8` (`.agents/` repo-convention cross-check, 8
agents, 449,197 tokens) — plus the earlier `wf_6aecf5d4-a9f` (8-agent
re-verification of the original adopt/decline calls). Full reasoning for
every finding below is in each run's `journal.jsonl` under
`/home/eranr/.claude/projects/-home-eranr-memoria-vault/086d8e17-f30f-4fe2-ae4d-ec173bd1fed8/subagents/workflows/<run-id>/`.

## 3. Plan of work

The work has four parts, in dependency order: (A) install the plugin, (B)
fix what it collides with in the already-installed personal skill layer,
(C) fix what it collides with or should cross-reference in this repo's own
`.agents/` conventions, (D) verify behavior, not just presence.

### A. Install

Standard plugin mechanism for both tools (§4 steps 1–3) — no custom
installer, no forked repo. Before installing, run `claude plugin details`
against the added marketplace to get the actual token-cost projection for
all 14 bundled skills (13 usable + `using-superpowers`), rather than
estimating.

### B. Personal-skill-layer fixes (all verified real, not hypothetical)

1. **`ponytail` vs. `test-driven-development` — a genuine contradiction, not
   overlap.** Ponytail's default is code-first-then-a-trailing-check; TDD's
   Iron Law is test-first-or-delete-and-restart. Same trigger surface
   (any feature/bugfix). Fix durably in `~/.claude/CLAUDE.md` (global,
   update-proof), not in ponytail's vendored `SKILL.md` (gets overwritten on
   `claude plugin update ponytail`): TDD's ordering wins when TDD is in
   effect for a change; ponytail continues to govern the *size/shape* of
   what gets built once that ordering is satisfied.
2. **`rethink`'s standing directive vs. `brainstorming` — a real,
   unresolved double-trigger.** Rethink is "active every response" for
   design questions and would emit a finished recommendation immediately,
   silently pre-empting brainstorming's hard gate (interactive Q&A → written,
   user-approved spec → handoff to `writing-plans`). Fix in
   `rethink`'s own `hooks/directive.md` (this is the user's own repo, safe
   and appropriate to edit directly, unlike a vendored plugin): add a
   "yield to gated design flows" rule.
3. **`rethink-audit` vs. `brainstorming`, separately** — `rethink-audit` is
   self-contained and doesn't inherit `directive.md`'s Rules section, so
   fix #2 doesn't reach it; needs its own boundary clause.
4. **`rethink-audit`'s `migrate:` step vs. `writing-plans`** — `migrate:` is
   plan-*shaped* output (a sequencing sketch) but has none of `writing-plans`'
   file-structure/interfaces/TDD-cadence discipline; nothing currently flags
   it as a sketch rather than an executable plan. Real risk: it gets handed
   straight to an implementer skipping proper decomposition. Fix: a
   one-line boundary in `rethink-audit`'s own `SKILL.md`.
5. **`grilling` vs. `brainstorming` — a real routing ambiguity.** Both
   interview the user one question at a time with a recommended answer per
   question; the actual discriminator (does a plan/design already exist, or
   are we building one from scratch) is stated in neither skill's
   description, so a request like "grill me on my idea for X" could launch
   grilling's interview and converge to "enact the plan" without ever
   passing through brainstorming's hard gate (written, approved spec).
   Fix: sharpen `grilling`'s description to explicitly require an existing
   plan/design, and add one line routing bare-idea requests to brainstorming
   first.
6. **`caveman` vs. `brainstorming`/`writing-plans` — a narrow, real gap.**
   Caveman's persisted-artifact exemption ("Code/commits/PRs: write normal")
   doesn't cover the *other* class of persisted project artifact these new
   skills produce — written design specs and implementation plans — so a
   strict reading would compress the substantive content of a spec/plan
   file the same way it compresses ephemeral chat prose. Fix: extend the
   exemption.
7. **`tdd` retirement's planned "seams" addendum — corrected, not just
   ported.** The local `tdd` skill's "Seams" section is itself a loose
   paraphrase of `codebase-design`'s carefully-defined vocabulary (which
   explicitly lists "boundary" under *Avoid*). Porting it into
   `test-driven-development` without a cross-reference would create a
   *third*, inconsistent definition of the same term. Fix: the addendum
   must open with `**REQUIRED BACKGROUND:** codebase-design`'s vocabulary,
   using "module"/"seam" — not reintroduce "boundary" as a synonym. The
   same drift already exists independently in `brainstorming`'s "Design for
   isolation and clarity" section and `writing-plans`' "File Structure"
   section (both say "unit"/"boundaries" instead of "module"/"seam") — fix
   both with the same one-line cross-reference while editing these files
   anyway.
8. **`improve` vs. `subagent-driven-development`/`writing-plans`/
   `verification-before-completion` — checked in depth, no fix required.**
   Surface similarity (dispatch-review-verdict-loop) is real, but every
   load-bearing mechanic diverges (single-plan-single-verdict vs.
   multi-task-two-verdict; disposable vs. mergeable worktree; different plan
   template shapes). Optional, non-blocking: one sentence in `improve`'s
   `SKILL.md` naming the precedence (single audit finding → `improve`'s own
   `execute`; a spec-derived multi-task plan → `subagent-driven-development`)
   — deferred, not required for success.

### C. Repo-convention fixes in `memoria-vault` itself

1. **`AGENTS.md`'s Skills table** needs exactly two new rows
   (`requesting-code-review` for mid-task/self-review checkpoints;
   `receiving-code-review` for processing any review's findings) and exactly
   two new paragraphs, **consolidated into one place** (per the workflow's
   own explicit warning against scattering near-duplicate notes across
   parallel findings): `verification-before-completion` as a complementary
   claim-honesty gate (not a fourth verification mechanism), and a
   severity-vocabulary reconciliation note (this repo's Critical/High/
   Medium/Low vs. `requesting-code-review`'s lighter Critical/Important/
   Minor — never mix the two inside one persisted report/issue/PR comment).
   Two things checked and confirmed **not** needed, despite initially
   suspecting otherwise: a footnote distinguishing "personal, cross-repo
   skills" from repo-installed plugins (empirically false premise — the
   table already mixes both under identical `(plugin, when available)`
   phrasing, e.g. `pr-review-toolkit`/`security-guidance` are also
   user-scope), and a superpowers-specific precedence clause (the existing
   "Skills and plugins... they do not override it" sentence already binds
   grammatically to *any* skill/plugin, not just table-named ones).
2. **`.agents/playbooks/code-review.md`** needs two additions: a paragraph
   after "Establish scope" routing self-review to `requesting-code-review`'s
   context-isolation mechanic (giving a dispatched reviewer only SHAs +
   requirements, never the requester's own session history), and a bullet
   in "Report" routing received findings through `receiving-code-review`'s
   verify-before-acting discipline. The playbook's own review criteria/
   checks/report-format sections stay authoritative — the two skills supply
   mechanics, not the domain-specific policy.
3. **`.agents/playbooks/verify-change.md`** — checked, **no edit**: it's an
   explicitly plugin-independent portable playbook; naming a specific
   optional plugin skill inside it would break that portability contract
   for no correctness gain (its own procedure already produces the
   fresh-evidence discipline `verification-before-completion` demands).
4. **`.agents/playbooks/exec-plan.md`** — the highest-stakes repo-side item.
   Needs two additions: an appended 5th item to "Authoring" naming
   `writing-plans`' task right-sizing rule as sizing guidance only (the
   deliverable still lands in this file's own template, never a new
   `docs/superpowers/plans/` file), and a new section, "Reusing superpowers
   execution techniques," after "Running" and before "Validating," naming
   `subagent-driven-development` (per-step implementer + reviewer subagent
   pattern, with its own model-tiering) and `executing-plans`
   (separate-session handoff) as optional *execution engines* for an
   ExecPlan's own Concrete steps — explicit that the ExecPlan's own
   Validation/Progress/Execution-log/Surprises sections remain authoritative
   and that neither skill's plan-file default or recovery ledger substitutes
   for this file's own record.
5. **`.agents/templates/exec-plan.md`** — one-sentence pointer in the
   "Concrete steps" guidance comment to the two new playbook sections above,
   so the template stays in sync without duplicating the guidance text into
   the skeleton itself.
6. **`.agents/templates/handoff.md`** needs a narrow, real addition: a new
   "Result" section for the *receiver* to report back status (adopting
   `subagent-driven-development`'s four-way vocabulary — DONE /
   DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED). Confirmed gap: the
   template today is entirely one-directional (dispatcher fills every
   section; nothing captures what the receiver reports). Its
   compaction-recovery ledger, by contrast, is **not** adopted — that solves
   a different-shaped problem (a tight, same-sitting, many-fresh-subagent
   fan-out loop) this repo's guidance doesn't have a matching workflow for
   today, and importing it would be speculative machinery for work this
   repo doesn't do.
7. **`.agents/playbooks/design-history.md`, `release.md`,
   `security-review.md`, `.agents/templates/review-report.md`,
   `.agents/system/*.md` (three maps), `.agents/skills/policy-change-review/
   SKILL.md`, `.agents/skills/schema-change/SKILL.md`** — all checked in
   full against every plausibly-overlapping superpowers skill; all confirmed
   **leave-alone** with specific, verified reasoning per file (distinct
   artifact/audience/trigger, or the repo's own version is already stronger/
   more specific than the generic vendor equivalent, or citing an optional
   plugin by name inside a leaf procedure file would create a dead
   reference when the plugin isn't installed). No edits.

### D. Verification, not just presence-checking

Checking that 13 new names appear in a skill list proves the files parsed,
not that the skills behave correctly or that the fixes in B/C actually
resolved the conflicts they target. §5 adds an actual smoke-test: trigger at
least one skill from each of the three fixed conflict pairs (TDD vs.
ponytail; a design request, to confirm rethink now yields to brainstorming's
gate when appropriate; grilling vs. brainstorming routing) and read the
transcript, not just the skill-list membership.

## 4. Concrete steps

1. **Update and re-push this plan file** (already done for the structural
   rewrite; re-run only if resuming after this point):

   ```bash
   cd ~/memoria-vault/scratch
   git pull --ff-only origin scratch
   git add scratch/workflow-audit/exec-plan-adopt-superpowers.md
   git commit -m "scratch: expand adopt-superpowers exec-plan with retire/adapt/conflict findings"
   git push origin HEAD:scratch
   ```

2. **Pre-flight: add the marketplace and inspect cost/inventory before
   installing anything:**

   ```bash
   claude plugin marketplace add obra/superpowers
   claude plugin details superpowers@superpowers
   ```

   Expected: marketplace registers; `details` prints the component
   inventory (14 skills, 1 SessionStart hook, harness-only cost for the
   hook) and a projected always-on token cost. Read this before proceeding
   — if the always-on cost is surprising, stop and reconsider scope before
   `install`.

3. **Install for Claude Code, then Codex:**

   ```bash
   claude plugin install superpowers@superpowers
   codex plugin marketplace add obra/superpowers
   codex plugin add superpowers@superpowers
   ```

   Expected: `~/.claude/settings.json` gains
   `enabledPlugins["superpowers@superpowers"] = true` and
   `extraKnownMarketplaces["superpowers"]`; `~/.codex/config.toml` gains
   `[marketplaces.superpowers]` and `[plugins."superpowers@superpowers"]`,
   matching the existing `ponytail`/`rethink` entries' shape.

4. **Retire the standalone `tdd` skill, with the corrected addendum.** In
   the installed `test-driven-development/SKILL.md` (both tools), insert
   after "When to Use" / before "The Iron Law":

   ```markdown
   ## Seams — Where Tests Go

   **REQUIRED BACKGROUND:** You must understand the `codebase-design`
   skill's module/interface/seam vocabulary — use it as defined there, not
   synonyms like "boundary."

   A test exercises a module through its seam, never through internals.
   Before writing the RED test, name the seam under test and confirm it
   with your human partner; test only at pre-agreed seams.
   ```

   Mark this with an inline comment noting it's a local patch that must be
   reapplied after `claude plugin update superpowers`. Then remove the
   superseded skill:

   ```bash
   rm -rf ~/.claude/skills/tdd ~/.codex/skills/tdd
   ```

5. **Fix the terminology drift in `brainstorming` and `writing-plans`**
   (both tools' installed copies). In `brainstorming/SKILL.md`, under
   "Design for isolation and clarity," before its bullet list, add:
   `**REQUIRED BACKGROUND:** Use the codebase-design skill's vocabulary
   here — "unit" below means module, "boundaries" means seam/interface
   placement.` In `writing-plans/SKILL.md`, change the "File Structure"
   bullet "Design units with clear boundaries and well-defined interfaces"
   to add `(see the codebase-design skill: unit ≈ module, boundary ≈ seam)`.

6. **Fix `grilling`'s routing ambiguity** (`~/.claude/skills/grilling/
   SKILL.md` and the Codex copy). Change the frontmatter `description` to:
   `Grill the user relentlessly about a plan or design that already exists
   (their own draft, notes, or a prior spec). Use when the user wants to
   stress-test an EXISTING plan before building, or uses any 'grill' trigger
   phrases. Not for building a design from scratch — use brainstorming for
   that.` Add one line to the body: `If no plan or design exists yet — only
   a bare idea — use the brainstorming skill first to produce and get
   approval on one; grilling assumes a plan is already in hand to
   interrogate, not that one needs to be created.`

7. **Fix `caveman`'s persisted-artifact exemption** (both tools). Change the
   Boundaries section's first sentence to: `Code/commits/PRs/persisted
   design docs, specs, and plans (files saved to disk as project artifacts,
   e.g. docs/superpowers/specs/*.md, docs/superpowers/plans/*.md): write
   normal.`

8. **Fix `rethink`'s double-trigger with `brainstorming`**
   (`~/.claude/plugins/marketplaces/rethink/plugins/rethink/`). In
   `hooks/directive.md`, under `## Rules`, add: `- **Yield to gated design
   flows:** if a loaded skill hard-gates a finished design behind
   interactive requirements-gathering and user approval (e.g. a
   brainstorming-style skill), do not emit a standalone design/
   recommendation for that request. Feed rethink's method — requirements,
   prior-art research, first-principles design, trade-offs — into that
   skill's approach-proposal and design-presentation steps instead, and let
   its Q&A and approval gate govern pacing.` In `skills/rethink-audit/
   SKILL.md`, under `## Boundaries`, add the matching clause (rethink-audit
   is self-contained and doesn't inherit `directive.md`), plus, at the end
   of `## Output`: `migrate: is a sequencing sketch, not an implementation
   plan — it has no file-level structure, task interfaces, or test steps.
   Before any code is written, route the target design plus gap: to
   superpowers:writing-plans (or to brainstorming first if requirements are
   still unclear) to lock in file structure and bite-sized TDD tasks; do
   not execute migrate: steps directly.` Bump `plugin.json`/`.codex-plugin/
   plugin.json` versions (1.1.0 → 1.2.0, additive) as done for the earlier
   rethink revision this session.

9. **Add the global precedence note** (`~/.claude/CLAUDE.md` — durable,
   update-proof, and this is exactly the mechanism `using-superpowers`'s own
   text defers to: *"User instructions... take precedence over skills"*).
   Add a new section:

   ```markdown
   ## Skill precedence

   - **Plan Mode:** this harness's native Plan Mode workflow (Explore →
     Design → Review → write plan → ExitPlanMode) governs entering plan
     mode. The `obra/superpowers` plugin's `using-superpowers` skill says to
     invoke `brainstorming` before entering plan mode — that mandate does
     not apply here; a more specific native mechanism already exists.
   - **Design/architecture reasoning:** `rethink` governs standing
     first-principles design reasoning in any response. `brainstorming` is
     available on explicit request for an interactive idea-to-approved-spec
     dialogue, but is not a mandatory blocking gate before every
     creative-work request in this environment.
   - **Test-first ordering:** when TDD (`superpowers:test-driven-development`)
     is in effect for a change, its test-first ordering wins over
     `ponytail`'s default code-first-then-check sequencing.
   ```

10. **Repo-side edits on `memoria-vault`.** Isolate first (`AGENTS.md` §1):

    ```bash
    git fetch origin
    git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/adopt-superpowers-docs -b docs/adopt-superpowers-repo-notes origin/main
    cd ~/memoria-vault/worktrees/adopt-superpowers-docs
    ```

    Apply, in this worktree: the two `AGENTS.md` Skills-table rows plus the
    two consolidated paragraphs (§3.C.1); `.agents/playbooks/code-review.md`'s
    two additions (§3.C.2); `.agents/playbooks/exec-plan.md`'s two additions
    (§3.C.4); `.agents/templates/exec-plan.md`'s one-line pointer (§3.C.5);
    `.agents/templates/handoff.md`'s new "Result" section (§3.C.6). Exact
    text for every edit is quoted verbatim in §3 above and in the source
    workflow findings cited in §2.

11. **Verify** — see §5 in full; run in a **fresh** Claude Code session and
    a **fresh** Codex session (plugin/skill changes require a new session,
    confirmed via `claude plugin update`'s own "restart required to apply"
    note and this session's earlier finding that Codex needs a restart to
    pick up new skill folders).

## 5. Validation and acceptance

- **Claim:** Given the plugin installed for Claude Code, when a fresh
  session starts, then `claude plugin list` shows `superpowers@superpowers`
  enabled, and the "available skills" reminder lists all 13 usable
  superpowers skills (13, not 14 — `using-superpowers` is a SessionStart
  injection, not a separately-listed invocable skill).
  - **Prove with:** `claude plugin list` transcript; `grep -c
    "superpowers:"` on the skill-list reminder → `13`.
- **Claim:** Given the plugin installed for Codex, the same 13 skills are
  discoverable there too.
  - **Prove with:** fresh `codex` session; skill list inspection, or
    `find ~/.codex/plugins/cache/superpowers -iname SKILL.md | wc -l` → `14`.
- **Claim:** Given `tdd` is retired, no unnamespaced `tdd` entry remains in
  either tool, and `superpowers:test-driven-development`'s installed copy
  contains the corrected seams addendum.
  - **Prove with:** `ls ~/.claude/skills/ ~/.codex/skills/` (absent); `grep
    -A5 "REQUIRED BACKGROUND.*codebase-design" <installed test-driven-development path>`
    on both tools.
- **Claim (real behavior, not presence):** Given a request that would
  previously have triggered `ponytail`'s ship-first default on a feature
  requiring TDD, when the fixed precedence note is in effect, then the
  agent writes a failing test before implementation.
  - **Prove with:** in the fresh session, ask for a small new feature in a
    disposable scratch repo/file; observe and paste the transcript showing
    RED before GREEN.
- **Claim (real behavior):** Given a "let's design X" request, when
  `rethink`'s directive and `brainstorming` are both loaded, then the agent
  either runs brainstorming's interactive Q&A (not an immediate finished
  recommendation) or explicitly explains why it judged the request as
  tactical/out of brainstorming's scope.
  - **Prove with:** transcript of one such request in the fresh session.
- **Claim (real behavior):** Given a request phrased as "grill me on my
  rough idea for X" (bare idea, no existing plan), when `grilling`'s fixed
  description is in effect, then the agent routes to `brainstorming` first
  rather than launching grilling's interview directly.
  - **Prove with:** transcript of one such request.
- **Claim:** Given the repo-side edits (step 10), when a PR is opened, then
  `pr-policy`/`lint`/`cspell`/`markdownlint` all pass (these are pure
  documentation additions, no code paths touched).
  - **Prove with:** `gh pr checks <n> --watch` transcript.

## 6. Idempotence and recovery

- **Safe to re-run:** `claude plugin marketplace add`/`install` are
  idempotent. Step 4's `rm -rf` on `tdd` is safe to re-run. Steps 5–9 are
  plain text edits — re-running with the same target text is a no-op diff.
- **Rollback:** `claude plugin uninstall superpowers@superpowers` +
  `claude plugin marketplace remove obra/superpowers` (and Codex
  equivalents) reverse step 3. Reverting steps 4–9 means restoring each
  edited file's pre-edit text (this plan quotes every exact edit, so a
  revert is a direct copy-back, not a reconstruction). Step 10's repo-side
  edits revert via normal PR/branch discipline (close without merging, or
  revert the merge commit).

## 7. Progress

- [ ] plan file updated and pushed to `origin/scratch`
- [ ] pre-flight `plugin details` reviewed (cost/inventory)
- [ ] plugin installed for Claude Code and Codex
- [ ] `tdd` retired with corrected seams addendum (both tools)
- [ ] brainstorming/writing-plans terminology drift fixed (both tools)
- [ ] grilling description/routing fixed (both tools)
- [ ] caveman persisted-artifact exemption extended (both tools)
- [ ] rethink directive.md + rethink-audit fixes applied, version bumped
- [ ] global `~/.claude/CLAUDE.md` precedence section added
- [ ] repo-side worktree opened, AGENTS.md + 4 `.agents/` files edited, PR opened and merged
- [ ] all §5 claims proven, transcripts pasted into §11
- [ ] release/checkpoint close only — N/A (no `design-history/` update needed)

## 8. Execution log

- {{ to be filled while running }}

## 9. Surprises & discoveries

- Two structural misreadings from the very first pass of this plan were
  caught only by adversarial re-verification, not by careful initial
  reading: `using-git-worktrees`'s generic default was mistaken for its
  actual (instruction-deferring) behavior, and `finishing-a-development-branch`'s
  "merge locally" option was mistaken for something that pushes to `main`.
  Neither survived a direct re-read of the primary text. Kept here so a
  future reader doesn't re-derive the same mistakes from a stale summary.
- **Open decision, not resolved here:** ponytail's "ship the lazy version,
  question it in the same response" instinct and brainstorming's "every
  project needs an approved design, even a single-function utility" hard
  gate are in genuine tension, not just overlap. This plan does not pick a
  side — flagging it in `~/.claude/CLAUDE.md`'s new precedence section (step
  9) covers the two *resolved* conflicts (Plan Mode, TDD timing) but
  deliberately leaves this third one for you to decide and add a line for,
  once you've seen how the two skills actually behave together in practice.
- `using-superpowers`'s aggressive mandatory-invocation framing was found by
  directly reading its full body, not by either cross-check workflow —
  neither workflow was scoped to include it, since earlier passes treated it
  as "not independently meaningful." Worth remembering as a process lesson:
  the skill most likely to collide with existing always-on directives was
  the one initially read least carefully (frontmatter + 8 lines, not the
  full ~50-line body).

## 10. Interfaces & dependencies

- **Plugin source:** `github.com/obra/superpowers`, MIT license. Manifests:
  `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` (Claude
  Code), `.codex-plugin/plugin.json` (Codex).
- **Files edited outside `memoria-vault`** (no git history inside this
  repo; recovery is this plan's own quoted exact-edit text): `~/.claude/
  skills/{grilling,caveman}/SKILL.md` + Codex copies; `~/.claude/CLAUDE.md`;
  `~/.claude/plugins/marketplaces/rethink/plugins/rethink/{hooks/
  directive.md, skills/rethink-audit/SKILL.md, .claude-plugin/plugin.json,
  .codex-plugin/plugin.json}`; the installed `superpowers` plugin's
  `test-driven-development`, `brainstorming`, `writing-plans` skill files
  (both tools — noted as needing reapplication after `claude plugin update
  superpowers`).
- **Files edited inside `memoria-vault`** (normal git history, PR-reviewed):
  `AGENTS.md`; `.agents/playbooks/code-review.md`; `.agents/playbooks/
  exec-plan.md`; `.agents/templates/exec-plan.md`; `.agents/templates/
  handoff.md`.
- **Superseded local skill:** `~/.claude/skills/tdd/` and `~/.codex/skills/
  tdd/` (adapted earlier this session from `mattpocock/skills`). Retired by
  step 4.
- **Checked and left alone, with reasons on file:** `.agents/playbooks/
  {design-history,release,security-review,verify-change}.md`, `.agents/
  templates/review-report.md`, `.agents/system/*.md` (three maps), `.agents/
  skills/{policy-change-review,schema-change}/SKILL.md`, `improve`,
  `codebase-design`.

## 11. Artifacts & notes

- {{ command transcripts pasted here as the plan runs }}

## 12. Outcomes & retrospective

- **Shipped:** {{ fill at close }}
- **Still open:** {{ fill at close — including the ponytail/brainstorming
  judgment call from §9 }}
- **Routed to:** N/A for decisions/design-history; repo-side doc edits go
  through a normal PR
- **Lessons:** {{ fill at close }}
