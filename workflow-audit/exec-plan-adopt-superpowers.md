# ExecPlan — Build the complete agent skill workflow, with `obra/superpowers` as the base

## 0. Metadata

- **Task:** Originally scoped to installing `obra/superpowers` alone;
  broadened per explicit direction ("the scope is the entire workflow with
  superpowers as the base") to cover the full agent-skill toolkit, and then
  broadened again per explicit direction to (a) evaluate every existing
  skill and plugin for retirement, not just conflicts, since some of what
  was called "hand-authored" loose skills are actually cherry-picked from
  third parties and deserve the same scrutiny as any adopted capability,
  and (b) make Claude Code's and Codex's end states as close to identical
  as possible. Concretely: install the `obra/superpowers` plugin (13 usable
  skills: systematic-debugging, test-driven-development, brainstorming,
  receiving-code-review, requesting-code-review, writing-plans,
  writing-skills, verification-before-completion, using-git-worktrees,
  finishing-a-development-branch, dispatching-parallel-agents,
  subagent-driven-development, executing-plans — plus the bundle's own
  onboarding meta-skill `using-superpowers`) for both Claude Code and Codex;
  retire the superseded local `tdd` skill and the redundant `grill-me`
  pointer; install five gap-filling plugins across four bundles (§3.E) —
  `interface-design` + Anthropic's official `frontend-design`,
  `threat-modeling`, `the-elements-of-style`, `api-design-principles`
  (vendored as a single skill, not the whole host plugin); close two
  cross-tool parity gaps by installing `codex-security` on Codex and
  porting `obsidian-skills` to Codex (§3.G); explicitly decline three
  candidates that would not actually improve anything (the official
  `code-review` marketplace plugin, `coderabbit` on Codex, a runtime
  conditional guard on rethink's fix); **retire, adapt, or cross-reference
  every existing skill, plugin, and repo convention any of this collides
  with or duplicates** (not just install the new things); and verify the
  combined toolkit behaves correctly on both tools, not merely that the
  skill lists show the new names.
- **Worktree / branch:** None on `memoria-vault` for the *implementation* —
  the skill/plugin files live under `~/.claude/` and `~/.codex/` (per-user
  tool config, not repo content), so `AGENTS.md` §1's git-worktree setup does
  not apply there. It does apply to two specific `memoria-vault`-tracked
  edits this plan makes (`AGENTS.md` and five files under `.agents/`) — those
  go through the normal worktree → branch → PR flow, not a direct edit on
  `main`. This plan file itself lives on the **`scratch`** branch under
  `scratch/workflow-audit/` (this repo's holding area for cross-cutting,
  non-release-scoped plans).
- **Related decisions:** Two judgment calls this plan originally surfaced
  without resolving — the ponytail-vs-brainstorming process-ceremony
  threshold, and the scope of rethink's retirement/narrowing — are both
  resolved as of this revision, via a Generate→Verify workflow (2
  independent option-generation agents, then 2 adversarial verification
  agents re-checking every quoted claim against ponytail's, brainstorming's,
  and rethink's actual source text). See §9 for the decisions taken, the
  corrections verification forced, and the residual known-unknowns each
  recommendation flagged explicitly rather than papering over. Everything
  else below is a verified conflict or gap with a concrete fix, not a
  product/architecture decision, so no release decision-ledger entry is
  otherwise needed.
- **Related issues / milestone:** — (personal tooling + repo-doc
  consistency, not release-scoped; milestone `0.1.0` is unaffected)
- **Started:** 2026-07-06 · **Last updated:** 2026-07-06 (revised again to
  resolve both open decisions via an adversarially-verified pros/cons
  workflow, after the earlier revision's two adversarial cross-check
  workflows plus direct verification of CLI syntax, config state, and the
  bundle's own onboarding skill)

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
  that mechanism (§4 step 8) rather than editing the vendored skill file —
  the same rule this plan applies to every superpowers fix: **never edit a
  file under the plugin's own installed/cached path** (it's overwritten on
  `claude plugin update superpowers`); route any needed cross-reference or
  precedence rule through the durable, update-proof `~/.claude/CLAUDE.md`
  instead. This is unlike `rethink` (the user's own plugin, released by
  them, safe to edit directly) or `grilling`/`caveman`/`codebase-design`/
  `improve`/`tdd` (hand-authored loose files with no upstream update
  mechanism at all) — `ponytail` and `superpowers` are the two third-party,
  independently-updated plugins in this toolkit, and both get the
  CLAUDE.md-note treatment, never a direct file edit.

**What's already installed, for context.** Correction applied this revision:
skills previously described as "hand-authored" are not — they are cherry-picked
FROM third-party repos and installed as loose files with no live
auto-update mechanism (unlike a real marketplace-managed plugin). They are
safe to edit directly for that reason, but were still evaluated for
retirement with the same rigor as any adopted capability, not assumed safe
by default:

**Claude Code** (`claude plugin list` + `~/.claude/skills/`):

| Name | Kind | Source |
|---|---|---|
| `ponytail` | plugin (hooks-based, always-on), v4.7.0 | `DietrichGebert/ponytail` |
| `rethink` | plugin (hooks-based, always-on), v1.1.0 | `eranroseman/rethink` (this session's own repo) |
| `pr-review-toolkit` | plugin (6 subagents), v1.0.0 | official Anthropic (`claude-code-plugins` marketplace) — **not previously tracked in this plan; evaluated in §3.B.9** |
| `security-guidance` | plugin (hooks-only, passive), v2.0.0 | official Anthropic (`claude-code-plugins` marketplace) — **not previously tracked in this plan; evaluated in §3.E (threat-modeling bundle)** |
| `obsidian-skills` (`obsidian:*`) | nested plugin (skills-directory auto-detect), 5 sub-skills | `kepano/obsidian-skills` (Steph Ango) — **Codex-porting evaluated in §3.G** |
| `grilling` | loose skill, cherry-picked | `mattpocock/skills` |
| `tdd` | loose skill, cherry-picked | `mattpocock/skills` — **retired by this plan** |
| `codebase-design` | loose skill (+2 reference files), cherry-picked | `mattpocock/skills` |
| `improve` | loose skill (+3 reference files), cherry-picked | `shadcn/improve` |
| `caveman` | loose skill (skill-only, no hooks/MCP), cherry-picked | `JuliusBrussee/caveman` |
| `grill-me` | loose skill, Claude-only thin pointer to `/grilling` | — **retired by this plan (§3.F), not ported to Codex** |

**Codex** (`codex plugin list` + `~/.codex/skills/`): `ponytail` v4.8.4,
`rethink` v1.0.1 (installed, enabled); `caveman`, `codebase-design`,
`grilling`, `improve`, `tdd` (same cherry-picks, no `grill-me`); no
`pr-review-toolkit`/`security-guidance`/`obsidian-skills` equivalent
installed. Three configured marketplaces: `ponytail`, `rethink`,
`openai-curated` (~180 pre-vetted plugins, all "not installed" except
ponytail/rethink). Relevant `openai-curated` entries, not yet installed:
`superpowers@openai-curated` v5.1.3 (obra/superpowers itself — all 13
skills + `using-superpowers` confirmed present, a simpler install path than
adding a new marketplace), `codex-security@openai-curated` v0.1.10
(official OpenAI security-scan suite — **installed for parity, §3.G**),
`coderabbit@openai-curated` v1.1.4 (third-party, external-service-backed —
**evaluated and declined, §3.G**). Also present, pre-dating this session
(mtime 2026-06-18): an official OpenAI-curated `security-threat-model`
skill at `~/.codex/vendor_imports/skills/skills/.curated/security-threat-model`,
installable via Codex's native `$skill-installer` — a lower-friction,
higher-trust alternative to cloning the third-party `fr33d3m0n/threat-modeling`
repo, surfaced only during the retirement/parity audit and weighed in §3.G.

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
2. **`rethink`'s standing directive vs. `brainstorming` — resolved: narrow
   rethink's trigger, don't just add a yield rule.** Rethink is "active
   every response" for design questions and would emit a finished
   recommendation immediately, silently pre-empting brainstorming's hard
   gate (interactive Q&A → written, user-approved spec → handoff to
   `writing-plans`). Of three options weighed (keep-and-yield / full
   retirement / narrow-the-trigger), narrowing wins: it preserves rethink's
   citation-grounded method completely undiluted for the tactical-but-
   architectural middle band neither `brainstorming` nor rethink's own
   existing "scoped, tactical question" exclusion covers (e.g. "should this
   be async or sync"), without full retirement's dependency on an
   unsolicited upstream PR into `obra/superpowers`, and without paying a
   live "should-I-yield" judgment call on every single response the way the
   smaller patch would. Fix in `rethink`'s own `hooks/directive.md` (the
   user's own repo, safe and appropriate to edit directly): narrow the
   Persistence trigger, unconditionally, to exclude brainstorming's exact
   stated territory ("creating features, building components, adding
   functionality, or modifying behavior"), and update rethink's own
   description (`plugin.json` + `skills/rethink/SKILL.md` frontmatter) to
   state plainly that it's designed to pair with `obra/superpowers`.
   **No runtime conditional guard, and deliberately so:** rethink is a
   homebrew, single-user plugin — there is no install base of other users
   running it standalone without superpowers to protect against
   regression, so a live "is brainstorming installed this session" check
   would be solving a non-problem at the cost of real complexity. This
   plan's earlier revision proposed exactly that conditional guard
   (framed around a hypothetical "solo-rethink installer"); it's removed
   here as unnecessary machinery once that premise is corrected.
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
7. **`tdd` retirement's "seams" idea, and a terminology drift in
   `brainstorming`/`writing-plans` — real content gaps, but delivered
   without touching any superpowers file.** The local `tdd` skill's "Seams"
   section (pre-agree test boundaries before writing a test) has no
   equivalent in `test-driven-development`, and is itself a loose paraphrase
   of `codebase-design`'s carefully-defined vocabulary (which explicitly
   lists "boundary" under *Avoid*) — porting it in verbatim, even as an
   edit, would create a *third*, inconsistent definition of the same term.
   The same drift already exists independently in `brainstorming`'s "Design
   for isolation and clarity" section and `writing-plans`' "File Structure"
   section (both say "unit"/"boundaries" instead of "module"/"seam"). Since
   none of these three files may be edited directly (they're inside the
   superpowers plugin's own installed path), all three gaps are closed by
   one global note in `~/.claude/CLAUDE.md` instead: name `codebase-design`
   as the canonical vocabulary source, and state the seams-before-tests
   practice as standing guidance. See §4 step 8 for the exact text.
8. **`improve` vs. `subagent-driven-development`/`writing-plans`/
   `verification-before-completion` — checked in depth twice (once for
   conflict, once retirement-biased), confirmed genuinely distinct on 3
   axes, fix promoted from optional to required.** Surface similarity
   (dispatch-review-verdict-loop) is real, but every load-bearing mechanic
   diverges: (1) dispatch shape — `execute` runs exactly one executor
   subagent for one plan with the verdict rendered by the calling agent
   itself; `subagent-driven-development` dispatches one implementer plus
   two separate reviewer subagents per task, continuously across every task
   in a plan, unattended; (2) plan durability — `improve`'s plans stamp a
   git SHA for drift detection and live in a persistent `plans/README.md`
   backlog with `quick`/`deep`/`branch`/`next`/`--issues`/`reconcile`
   variants meant to survive across sessions; `writing-plans`/
   `subagent-driven-development` plans are meant to execute immediately in
   the same arc, with no drift/backlog concept at all; (3) worktree
   disposition — `improve`'s Hard Rules forbid ever merging, pushing, or
   committing to the user's branch (a disposable review sandbox the human
   decides whether to apply); `subagent-driven-development`'s worktree *is*
   the real feature branch, terminating at `finishing-a-development-branch`
   (i.e., shipping it). The precedence note was previously deferred as
   optional; re-evaluated and promoted to required now that the final
   toolkit adds several more overlapping-sounding names (`interface-design`,
   `threat-modeling`, etc.), which increases the real cost of an agent
   guessing wrong about which tool a request should route through.
9. **`pr-review-toolkit` vs. superpowers' own `code-reviewer.md` template —
   evaluated, no fix needed, both kept running independently.** Superpowers
   bundles its own `code-reviewer.md` agent template inside
   `requesting-code-review` — a direct naming collision with
   `pr-review-toolkit`'s installed `code-reviewer` subagent worth checking.
   5 of `pr-review-toolkit`'s 6 agents (`comment-analyzer`,
   `pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`,
   `code-simplifier`) have no superpowers equivalent at all and are kept
   unconditionally. The 6th, `code-reviewer`, only *partially* overlaps
   superpowers' template: `pr-review-toolkit`'s version is a registered
   subagent Claude can proactively self-invoke, tightly scoped to CLAUDE.md
   compliance + bug detection with a 0-100 confidence gate (only ≥80
   reported); superpowers' template is a manually-filled prompt dispatched
   via a bare `general-purpose` Task, checking plan alignment,
   architecture, test quality, and production-readiness, ending in an
   explicit "Ready to merge: Yes/No/With fixes" verdict — capabilities
   `pr-review-toolkit`'s agent doesn't have and, being a live-updated
   marketplace plugin, cannot be edited to add. **A first draft of this fix
   proposed routing superpowers' dispatch to `pr-review-toolkit:code-reviewer`
   instead of its own template — adversarial verification correctly killed
   this: it drops superpowers' unique review dimensions at exactly its
   "Mandatory" checkpoints (after each task, before merge) rather than
   preserving both, since passing extra prompt text to a subagent whose own
   instructions never ask for those checks doesn't reliably restore them.**
   Correct resolution: no consolidation. Keep both running independently
   when a review checkpoint is hit; some overlap on the bug-finding
   dimension is an acceptable, minor cost next to the alternative of
   silently losing coverage. Separately confirmed: the official (uninstalled)
   Anthropic `code-review` marketplace plugin should **not** be installed
   — not because it duplicates the other two (it doesn't: it's a
   GitHub-PR-native bot that posts inline `gh` comments to a live remote
   PR and includes two genuinely novel review angles, git-blame historical
   context and past-PR-comment precedent, that exist nowhere else in this
   toolkit) but because that bot-oriented, remote-PR-posting mechanism
   doesn't fit this user's current interactive local workflow — installing
   it would add a third overlapping reviewer for no realized value here.
   This is a documented "considered and declined" item (§3.F), not a
   retirement (it was never installed).
10. **`codebase-design` vs. the not-yet-installed `interface-design` — checked
    directly, no fix needed.** Elevating `codebase-design` to canonical
    vocabulary status (item 7 above) creates a real risk if another newly
    adopted skill defines the same terms independently — flagged as an
    open, unverified risk by the retirement audit since no cached copy of
    `interface-design` existed on disk at the time. Resolved directly here
    against `interface-design`'s actual SKILL.md (fetched and read in full
    earlier this session): it uses "Depth" for visual elevation/layering
    (z-axis, shadow/border stacking — "choose ONE and commit: borders-only,
    subtle shadows, layered shadows, surface-color shifts") and "Interface"
    only in its own name, never as a defined term — a genuine word overlap
    with `codebase-design`'s "Depth" (Ousterhout's interface-simplicity
    ratio) and "Interface" (a module's public API), but in a completely
    different domain (visual UI craft vs. software module design), and the
    two skills' trigger surfaces are already cleanly disambiguated
    (dashboard/SaaS UI vs. module/seam design questions) the same way
    `codebase-design`'s "Interface" echo with `interface-design`'s own name
    was independently checked and cleared in §3.E. No CLAUDE.md caveat
    needed beyond this record of having checked it.

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

### E. Gap-filling plugins — five plugins, four bundles, all verified via a
   Check→Verify workflow against primary sources, not taken on the original
   research pass's word

1. **`interface-design` (Dammyjay93) + Anthropic's official `frontend-design`
   — install both, add a CLAUDE.md routing bullet.** Both cover UI
   generation but split unevenly: `interface-design` explicitly excludes
   "landing pages, marketing sites, campaigns, brand-only work" in its own
   frontmatter and owns product/dashboard/SaaS/admin UI, with the only
   standalone review commands in the pair (`/interface-design:design-review`,
   `/interface-design:design-deslop`) and persisted cross-session memory
   (`.interface-design/system.md`). `frontend-design` has no such
   self-limit — its trigger is generic "building new UI or reshaping an
   existing one," and its README usage examples include a dashboard — so a
   bare "build me a dashboard" request could plausibly fire both. The split
   is one-sided (only `interface-design` self-limits), which is exactly why
   a rule is still needed for the dashboard case specifically. Fix: a
   CLAUDE.md routing bullet (exact text in §4 step 12) — any request to
   review/critique/audit/de-slop already-built UI routes to
   `interface-design` (the only one with a review command); for new UI,
   route by the surface's job (a working tool a user operates repeatedly →
   `interface-design`; a one-off promotional/showcase surface →
   `frontend-design`), ask if genuinely ambiguous. **Gate: land this bullet
   in the same change that installs `interface-design` and enables
   `frontend-design`** — a precedence rule for two currently-inactive
   skills is a dead reference. No `codebase-design`/`improve` collision
   (checked directly, zero UI vocabulary in either) and no memoria-vault
   `.agents/` cross-reference needed (confirmed empirically: zero `.tsx`/
   `.jsx`/`.vue` files, no `/components` or `/ui` directory anywhere in the
   repo; the 45 grep hits for "dashboard"/"design system" are Obsidian-note
   homonyms, not application UI).
2. **`threat-modeling` (fr33d3m0n) — install, fix via CLAUDE.md, not a
   direct SKILL.md edit.** A git-clone-based skill (no plugin manifest) with
   its own upstream repo a user might resync — qualifies for this plan's
   "never edit a file with an independent upstream" rule the same as
   `ponytail`/`superpowers`, even though it isn't marketplace-managed. Its
   own frontmatter says it "MUST be invoked instead of analyzing security
   yourself," which over-triggers on a narrow follow-up about one
   already-flagged finding (e.g. "is this actually exploitable?") — a case
   its own "NOT for" list doesn't cover. Fix: a CLAUDE.md precedence note
   (exact text in §4 step 13) routing single-finding follow-ups to a direct
   answer, reserving the full 8-phase run for a deliberate, explicit
   request. Also add a short, optional final section to
   `.agents/playbooks/security-review.md` naming `threat-modeling` as an
   "if installed" whole-system-audit escalation path for when a diff-scoped
   review surfaces something systemic — worded as following **this same
   plan's own step 9 pattern** (which is what first establishes a
   skill-name cross-reference in `code-review.md`), not a pre-existing
   repo precedent, since no such precedent exists anywhere in this
   codebase's history today. Install path assumed as
   `~/.claude/skills/threat-modeling` by analogy with the other loose
   skills — not yet confirmed, flag as an assumption during execution.
3. **`the-elements-of-style` (obra) — install, no fix required.** Closes an
   already-named soft dependency: superpowers' own `brainstorming` skill
   references "elements-of-style:writing-clearly-and-concisely skill if
   available" in its spec-writing step, confirmed to be this exact plugin
   (same author, matching skill id). Lowest trust surface examined in this
   whole plan — plain markdown wrapping the public-domain 1918 Strunk text,
   zero hooks/scripts/bash permissions. No real collision with `caveman`
   (caveman governs live chat-response terseness; this governs durable
   written prose — different artifact class), but add one optional,
   precautionary CLAUDE.md line making that split explicit for the two
   output types caveman's own exemption list doesn't already name (docs/
   UI-text/error-strings, and saved reports) — skip if minimizing CLAUDE.md
   churn is preferred, since no wrong-output case is observed or plausible
   today.
4. **`api-design-principles` — vendor only the one skill, don't install the
   host plugin.** Originally planned as a full-plugin install from
   `wshobson/agents`' `backend-development` plugin; verification found that
   installing at plugin granularity pulls in **9 full skills, not 1**
   (architecture-patterns, cqrs-implementation, event-store-design,
   microservices-patterns, projection-patterns, saga-orchestration,
   temporal-python-testing, workflow-orchestration-patterns alongside
   `api-design-principles`), several with broad triggers
   ("designing new backend services/microservices from scratch") that
   compete directly with `rethink`'s and `brainstorming`'s new-build
   territory, plus a `tdd-orchestrator`/`test-automator` pair and a
   `/feature-development --methodology tdd` command that reintroduce a
   parallel, non-superpowers TDD pipeline this plan is retiring `tdd` in
   favor of avoiding. Fix: vendor **only** `plugins/backend-development/
   skills/api-design-principles/` (SKILL.md + references/ + assets/) into
   `~/.claude/skills/api-design-principles/` (and the Codex mirror) —
   `wshobson/agents` is MIT-licensed, confirmed via `gh api`, the identical
   precedent already used for `codebase-design` itself ("Adapted from
   github.com/mattpocock/skills (MIT License)"). This avoids every
   collision above by construction; no CLAUDE.md precedence note needed.
   No collision with `codebase-design` (confirmed: its glossary explicitly
   says "Interface... Avoid: API, signature" — it deliberately reserves
   "interface" for internal-module vocabulary and steers away from "API,"
   the opposite of a clash). No memoria-vault repo-convention touch (zero
   REST/GraphQL/OpenAPI surface anywhere in the repo, confirmed by grep).

### F. Retirements — evaluated across the entire toolkit with an explicit
   bias toward finding removal candidates, not just conflict patches

1. **`tdd` (loose skill) — retire.** Already covered in §3.B.7/§4 step 4;
   fully superseded by `superpowers:test-driven-development`, its one
   unique idea (seams-before-tests) ported to the CLAUDE.md note, not the
   file.
2. **`grill-me` (loose skill, Claude-only) — retire, do not port to Codex.**
   Re-examined with an explicit bias toward retirement, alongside
   `grilling`/`caveman`/`codebase-design`/`improve` (all four of which
   survive with their fixes above confirmed necessary, not rubber-stamped).
   `grill-me`'s entire body is one line, "Run a `/grilling` session," with
   `disable-model-invocation: true`. Every path it offers — explicit
   `/grilling` invocation, or conversational "grill" trigger phrases — is
   already served by `grilling` directly (its own description already
   covers "any 'grill' trigger phrases"). It adds no independent
   capability; the Simplicity-First case for deleting it ("no abstractions
   for single-use code... no flexibility that wasn't requested") is
   stronger than the case for maintaining and parity-porting a second file
   across two tools forever. Confirmed this is not a disguised technical
   necessity: Codex's `disable-model-invocation` analog
   (`agents/openai.yaml`'s `policy.allow_implicit_invocation: false`)
   could support an equivalent, so the Claude-only asymmetry isn't a
   platform limitation — it just isn't worth replicating. Retiring it is
   itself the cleanest form of parity: absent on both tools, rather than a
   redundant pointer with Codex-specific shim machinery on one side.
   Action: `rm -rf ~/.claude/skills/grill-me` (§4 step 4). No Codex-side
   action — `~/.codex/skills/` already has no `grill-me`.
3. **Official Anthropic `code-review` marketplace plugin — considered,
   declined, never installed.** Covered in §3.B.9: workflow-mismatch with
   this user's local interactive style (it's a GitHub-PR-native bot
   posting inline `gh` comments to a live remote PR), not a clean
   duplicate of anything already here (it has two genuinely novel review
   angles — git-blame historical context, past-PR-comment precedent — that
   exist nowhere else in this toolkit) but not worth adding a third
   overlapping reviewer for value not realized under the current workflow.
4. **`coderabbit@openai-curated` (Codex) — considered for pr-review-toolkit
   parity, declined.** See §3.G.4 — a real external-service dependency
   (separate CLI install, separate CodeRabbit account/auth, data egress),
   and installing it wouldn't even achieve real parity (a different
   mechanism entirely, not a substitute), so it would trade one asymmetry
   for a worse one.
5. **Runtime conditional guard on rethink's brainstorming fix — considered,
   removed.** Covered in §3.B.2/§9 — solved a non-problem (rethink has no
   external "solo installer" base to protect), unnecessary complexity, cut
   in favor of an unconditional trigger narrowing.

### G. Cross-tool parity — closing the gap between what Claude Code and
   Codex end up with, item by item, not accepting asymmetry by default

1. **`codex-security@openai-curated` — install on Codex.** Official OpenAI,
   MCP-backed, 10 explicit-invocation-only skills (security-scan,
   security-diff-scan, deep-security-scan, threat-model, finding-discovery,
   validation, attack-path-analysis, fix-finding, triage-finding,
   track-findings). Not a passive twin of `security-guidance` (nothing on
   Codex fires automatically the way `security-guidance`'s hooks do — that
   asymmetry is accepted, not solved, see item 4 below) but the
   capability-coverage-maximizing move: without it Codex has at most 1
   active security tool (`threat-modeling`, once mirrored) against Claude's
   2 (`security-guidance` + `threat-modeling`); with it, both tools reach 2.
   Command: `codex plugin add codex-security@openai-curated`.
2. **Collision fix: `codex-security`'s internal `threat-model` phase-skill
   vs. a standalone `threat-modeling` request.** `codex-security`'s
   `threat-model` skill triggers on "the user explicitly asks to create,
   update, or persist a repository threat model" — broad enough to also
   catch a request meant for the separately-installed `threat-modeling`
   (fr33d3m0n) skill. Verification found the first-draft fix (a narrow
   routing note anchored only on that one phrase) was too narrow: the real
   `threat-modeling` skill's actual trigger text — confirmed from a draft
   already present in this session's own scratchpad — is far broader
   ("MUST be invoked instead of analyzing security yourself," firing on
   generic "security audit," "find vulnerabilities," "analyze attack
   surface"), so the real collision surface is `codex-security`'s **entire
   scan family** (`security-scan`, `security-diff-scan`,
   `deep-security-scan`, `finding-discovery`), not just its narrow internal
   `threat-model` phase. Fix (broadened; exact text in §4 step 14): append
   to `~/.codex/AGENTS.md` (confirmed present, currently empty — the
   direct Codex structural analog of `~/.claude/CLAUDE.md`, so this is its
   first content) a routing note that `codex-security`'s own `threat-model`
   phase is scan-internal only (per its own hard rule, "do not use as the
   primary trigger for full PR, commit, branch, patch, or repository
   scans"), and that any standalone whole-system audit/STRIDE request goes
   to `threat-modeling` instead — regardless of which of `codex-security`'s
   scan-family skills might also match the phrasing.
3. **Mirror `threat-modeling` onto Codex — the one layer where true file
   identity, not just capability parity, is achievable.** Same loose-skill
   mechanism already used for `caveman`/`grilling`/`codebase-design`/
   `improve`. Install the identical file tree at
   `~/.codex/skills/threat-modeling` once §3.E.2 finalizes it for Claude.
   **Alternative surfaced during the parity audit, to weigh explicitly
   before executing this step:** Codex already carries a pre-existing
   (2026-06-18, predates this whole session) official OpenAI-curated
   `security-threat-model` skill at `~/.codex/vendor_imports/skills/skills/
   .curated/security-threat-model`, installable via Codex's own native
   `$skill-installer` — a lower-friction, higher-trust, officially-curated
   alternative to cloning a third-party GitHub repo onto Codex. Decide at
   execution time: mirror `fr33d3m0n/threat-modeling` for true cross-tool
   file identity, or use Codex's own native equivalent for a
   lower-trust-surface Codex-side install and accept a *capability-parity*
   (not file-identity) outcome instead. Not resolved here — this plan
   surfaces the choice rather than picking silently.
4. **Residual, accepted asymmetry: no Codex equivalent to
   `security-guidance`'s passive hook layer.** Codex supports hooks
   structurally (`[features] hooks = true` already set, `ponytail`/
   `rethink` already fire there every session) but no off-the-shelf plugin
   replicates `security-guidance`'s automatic pattern-warnings + Stop-hook
   diff review + agentic commit reviewer. Building one is new engineering,
   out of scope for a plugin-adoption pass. Document via the same
   `~/.codex/AGENTS.md` note (§4 step 14): Codex does not get the same
   always-on diff-review safety net Claude gets without the user
   explicitly invoking a `codex-security` scan.
5. **Known friction, not a blocker: `codex-security`'s `deep-security-scan`
   will hit a blocked capability gate under this machine's current
   config.** `~/.codex/config.toml` has `max_depth = 1` under
   `[features] multi_agent = true` (v1 mode, no `multi_agent_v2`).
   `codex-security`'s own `deep_security_scan` capability profile marks
   `agent_depth_2`, `delegated_workers`, and `usable_worker_slots_6` as
   **`block`** severity (not warn/suggest, corrected after verification —
   the first-draft finding understated this), which its own
   `config-preflight.md` defines as "the requested workflow cannot be
   claimed honestly when unmet," triggering a mandatory stop-and-ask
   remediation dialogue. `security-scan` and `security-diff-scan` (the
   primary entry points) have only warn/suggest requirements and are
   unaffected — so install and basic use are not blocked, only the deepest
   scan mode. No config change recommended now; treat raising
   `agents.max_depth` as its own deliberate performance decision if the
   full parallel `deep-security-scan` is wanted later.
6. **`coderabbit@openai-curated` — evaluated for pr-review-toolkit parity,
   declined (§3.F.4).** Confirmed via its own SKILL.md: it curl-installs a
   separate `coderabbit` binary, requires `coderabbit auth login --agent`
   against an external CodeRabbit account, and ships diff content off for
   remote analysis ("remote processing" named explicitly in its own
   stay-silent instructions) — a genuine new external-service dependency
   with no counterpart on the Claude side, unlike `pr-review-toolkit`'s
   fully self-contained, zero-egress prompt-template agents. Installing it
   would not produce real parity (a different mechanism, not a
   substitute) — it would trade one asymmetry for a worse one. Accepted
   resolution: once `obra/superpowers` lands identically on both tools,
   `requesting-code-review`'s own bundled `code-reviewer.md` template
   already gives both tools a mechanically equivalent, self-contained
   baseline reviewer with zero new dependency — closing most of the real
   gap without touching `coderabbit` at all. The only genuine residual
   asymmetry is `pr-review-toolkit`'s 5 other specialized personas
   (`comment-analyzer`, `pr-test-analyzer`, `silent-failure-hunter`,
   `type-design-analyzer`, `code-simplifier`), which `coderabbit` — one
   external generalist — could not fill anyway. Accepted, not solved;
   porting those 5 agent prompts as loose Codex skill files is a possible
   future step, deliberately deferred (no Codex-native equivalent exists
   to adopt instead, and manufacturing new Codex-side content is a bigger
   scope change than this plan's own gap-filling mandate covers).
7. **Port `obsidian-skills` (5 sub-skills) to Codex.** Author-blessed:
   upstream `kepano/obsidian-skills`'s own README documents a Codex CLI
   install path verbatim ("Copy the `skills/` directory into your Codex
   skills path, typically `~/.codex/skills`"). All 5 SKILL.md files use
   only portable `name`+`description` frontmatter, no Claude-specific
   mechanics, matching the same flat-loose-skill convention already used
   for `caveman`/`codebase-design`/`grilling`/`improve` on Codex. No
   `.codex-plugin` manifest exists upstream, so a marketplace-plugin
   install isn't an option — a flat `cp -r` per sub-skill is. Commands
   (§4 step 15): `cp -r ~/.claude/skills/obsidian-skills/skills/{obsidian-cli,
   json-canvas,obsidian-bases,defuddle,obsidian-markdown} ~/.codex/skills/`.
   **Justification corrected after verification:** the first-draft
   rationale for accepting the resulting packaging asymmetry (Claude's
   copy stays a git-backed marketplace plugin because "only it can have
   live updates") is false — `claude plugin list` shows `obsidian@skills-dir`
   under the separate "Skills-directory plugins" heading, not real
   marketplace-tracked "Installed plugins"; it has zero entries in
   `known_marketplaces.json`/`installed_plugins.json`. Its only actual
   update path is a manual `git pull` inside the directory (it's a plain
   git clone with an `origin` remote) — a capability that could be
   replicated identically on Codex by cloning instead of copying, if
   symmetric live-updatability is ever wanted. The simpler `cp -r`
   recommendation stands (it matches Codex's existing all-flat-loose-skill
   convention and needs no new git-tracking machinery there), but the
   justification is "matches Codex's existing pattern," not "Claude's copy
   is uniquely updatable." Similarly corrected: the original justification
   ("memoria-vault is itself an Obsidian vault project") overstates the
   primary source — `AGENTS.md`/`README.md` describe Memoria as "a
   standalone local CLI and research engine" with Obsidian listed as one
   of several optional adapters the installer doesn't enable by default;
   this checkout has no `.obsidian/` folder. Real relevance sits one level
   down, in `vault-template/` (what the installer deploys to an end user's
   actual vault, which does contain Obsidian-flavored markdown and a
   `.obsidian/*.json` gitignore entry) — the skills are relevant to
   vault-template work, not because this repo is itself a personal vault.
   Footnote, not a blocker: `defuddle`'s skill depends on an unmet local
   npm package (`npm install -g defuddle`, confirmed not installed) —
   pre-existing on the Claude side today too, so porting adds no new
   dependency, just carries over an already-nonfunctional-until-installed
   skill identically to both tools.

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

4. **Retire the standalone `tdd` skill.** No edit to any superpowers file —
   the "seams" content it would have contributed lands in step 8's global
   CLAUDE.md note instead.

   ```bash
   rm -rf ~/.claude/skills/tdd ~/.codex/skills/tdd
   ```

5. **Fix `grilling`'s routing ambiguity** (`~/.claude/skills/grilling/
   SKILL.md` and the Codex copy — hand-authored loose files, safe to edit
   directly). Change the frontmatter `description` to: `Grill the user
   relentlessly about a plan or design that already exists (their own
   draft, notes, or a prior spec). Use when the user wants to stress-test
   an EXISTING plan before building, or uses any 'grill' trigger phrases.
   Not for building a design from scratch — use brainstorming for that.`
   Add one line to the body: `If no plan or design exists yet — only a
   bare idea — use the brainstorming skill first to produce and get
   approval on one; grilling assumes a plan is already in hand to
   interrogate, not that one needs to be created.`

6. **Fix `caveman`'s persisted-artifact exemption** (both tools —
   hand-authored, safe to edit). Change the Boundaries section's first
   sentence to: `Code/commits/PRs/persisted design docs, specs, and plans
   (files saved to disk as project artifacts, e.g. docs/superpowers/specs/
   *.md, docs/superpowers/plans/*.md): write normal.`

7. **Fix `rethink`'s double-trigger with `brainstorming` — narrow the
   trigger, unconditionally, and update the description**
   (`~/.claude/plugins/marketplaces/rethink/plugins/rethink/` — the user's
   own plugin, released by them, safe to edit directly). No runtime
   conditional guard: rethink is a homebrew, single-user plugin, not a
   published tool with a solo-install base to protect against regression
   — narrowing the trigger unconditionally is the simpler, correct fix.
   In `hooks/directive.md`, change the Persistence section from:

   `ACTIVE EVERY RESPONSE for design and architecture questions. No drift
   back to "here's how to tweak the current code." Still active if
   unsure.`

   to:

   `ACTIVE EVERY RESPONSE for design and architecture questions — except
   creating a new feature, building a new component, or adding new
   functionality from scratch: that territory belongs to
   obra/superpowers' brainstorming skill, which this plugin is designed to
   pair with. Rethink continues to govern narrower/tactical-but-still-
   architectural questions below that threshold (e.g. "should this be
   async or sync," "how should this API be shaped") that brainstorming's
   own trigger doesn't reach and rethink's own "scoped, tactical question"
   exclusion doesn't catch either. No drift back to "here's how to tweak
   the current code" for the territory rethink still owns. Still active if
   unsure. Off only: "stop rethink" / "normal mode".`

   Also update rethink's own description to name the pairing explicitly:
   in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, append
   to the `description` field: `" — designed to pair with obra/superpowers'
   brainstorming skill for new-feature/component design; rethink covers
   standing first-principles reasoning for narrower architectural
   questions."` Same addition to `skills/rethink/SKILL.md`'s frontmatter
   `description`.

   In `skills/rethink-audit/SKILL.md`, under `## Boundaries` (unchanged in
   substance from the prior revision — rethink-audit is self-contained,
   one-shot, and every option weighed in the retirement-scope analysis
   agreed it doesn't compete with brainstorming's always-on territory the
   way the standing directive does), add: `- **Yield to gated design
   flows:** if a loaded skill hard-gates a finished design behind
   interactive requirements-gathering and user approval (e.g. a
   brainstorming-style skill) for a new-build request, do not emit a
   standalone design/recommendation for that request — this audit's
   clean-slate redesign niche (an existing subsystem) is distinct from
   new-build design, so the two rarely collide, but state the distinction
   explicitly when asked to audit something not yet built.` Also add, at
   the end of `## Output`: `migrate: is a sequencing sketch, not an
   implementation plan — it has no file-level structure, task interfaces, or
   test steps. Before any code is written, route the target design plus
   gap: to superpowers:writing-plans (or to brainstorming first if
   requirements are still unclear) to lock in file structure and bite-sized
   TDD tasks; do not execute migrate: steps directly.` Bump
   `plugin.json`/`.codex-plugin/plugin.json` versions (1.1.0 → 1.2.0,
   additive) as done for the earlier rethink revision this session.

   **Residual, deliberately left open rather than solved:** if
   `brainstorming`'s own extremely low invocation bar ("even a 1% chance a
   skill might apply... you ABSOLUTELY MUST invoke it") turns out in
   practice to also absorb the tactical middle-band questions this
   narrowing reserves for rethink, the carve-out is illusory and full
   retirement (donating rethink's method into `brainstorming` via an
   upstream PR) becomes the more honest choice. Watch for this in the §5
   smoke test and revisit if it happens.

8. **Add the global note in `~/.claude/CLAUDE.md`** — durable, update-proof,
   and the mechanism `using-superpowers`'s own text defers to: *"User
   instructions... take precedence over skills."* This is also where the
   `tdd`-seams and `brainstorming`/`writing-plans`-terminology content from
   step 4/§3.B.7 lands, since none of those three files may be edited
   directly (all three are inside the superpowers plugin's installed
   path). Add a new section:

   ```markdown
   ## Skill precedence

   - **Plan Mode:** this harness's native Plan Mode workflow (Explore →
     Design → Review → write plan → ExitPlanMode) governs entering plan
     mode. The `obra/superpowers` plugin's `using-superpowers` skill says to
     invoke `brainstorming` before entering plan mode — that mandate does
     not apply here; a more specific native mechanism already exists.
   - **Design-gate threshold (ponytail vs. brainstorming):** the two mostly
     don't compete — brainstorming governs the design phase, ponytail the
     implementation phase, and `using-superpowers`' own protocol sequences
     design → `writing-plans` → build. The real, narrow collision is
     timing: ponytail's "ship the lazy version now, question it in the same
     response" instinct fires at the exact moment brainstorming's hard gate
     forbids any implementation action before a presented design is
     approved. Resolve it with a two-signal threshold: route to
     brainstorming's gate only when (a) the request needs a new dependency
     that ponytail's own rung 4 would reject ("never add a new one for what
     a few lines can do" failing), or (b) the request spans multiple
     independent subsystems or carries genuine ambiguity about
     purpose/constraints/success criteria. Everything else — single-function
     changes, config tweaks, anything resolved by stdlib/native/an
     already-installed dependency — stays on ponytail's fast path with no
     gate. Known residual risk, accepted rather than solved: this threshold
     is gameable (an agent under pressure could salami-slice a
     multi-subsystem feature into dependency-free single changes to dodge
     the gate) and its two signals are proxies for risk, not risk itself — a
     one-line change to an auth check needs no new dependency but can carry
     real unexamined-assumption danger. If unexamined-assumptions-on-
     trivial-work turns out to be a recurring real problem in practice,
     switch to brainstorming-always-wins instead (accept the ceremony cost)
     rather than patching the threshold further.
   - **Design/architecture reasoning (rethink vs. brainstorming):**
     `rethink`'s own directive is narrowed unconditionally (see `rethink`'s
     `hooks/directive.md`, fixed in step 7 above — rethink now describes
     itself as designed to pair with `obra/superpowers`) to exclude
     new-feature/component-creation work — that territory routes to
     brainstorming's interactive, approved-spec flow instead. Rethink
     continues to govern standing first-principles reasoning for
     narrower/tactical-but-still-architectural questions below that
     threshold (e.g. "should this be async or sync") that neither skill's
     own stated scope otherwise reaches.
   - **Test-first ordering:** when TDD (`superpowers:test-driven-development`)
     is in effect for a change, its test-first ordering wins over
     `ponytail`'s default code-first-then-check sequencing.

   ## Design vocabulary

   - The `codebase-design` skill's module/interface/seam/adapter/leverage/
     locality vocabulary is canonical whenever a skill decomposes work into
     units — including where a skill's own text says "unit" or "boundary"
     instead (e.g. `superpowers:brainstorming`'s "Design for isolation and
     clarity" section, `superpowers:writing-plans`' "File Structure" step):
     read "unit" as module and "boundary" as seam.
   - Before writing a RED test (`superpowers:test-driven-development`), name
     and confirm the test's seam (per `codebase-design`) with the user
     first; test only at pre-agreed seams. This is the one idea from the
     retired local `tdd` skill worth keeping — delivered here, not as an
     edit to the installed skill.
   ```

9. **Repo-side edits on `memoria-vault`.** Isolate first (`AGENTS.md` §1):

   ```bash
   git fetch origin
   git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/adopt-superpowers-docs -b docs/adopt-superpowers-repo-notes origin/main
   cd ~/memoria-vault/worktrees/adopt-superpowers-docs
   ```

   Apply, in this worktree: the two `AGENTS.md` Skills-table rows plus the
   two consolidated paragraphs (§3.C.1); `.agents/playbooks/code-review.md`'s
   two additions (§3.C.2); `.agents/playbooks/exec-plan.md`'s two additions
   (§3.C.4); `.agents/templates/exec-plan.md`'s one-line pointer (§3.C.5);
   `.agents/templates/handoff.md`'s new "Result" section (§3.C.6);
   `.agents/playbooks/security-review.md`'s new "Escalate to a full audit"
   section (§3.E.2/§4 step 13) — land this one in the same PR as
   `code-review.md`'s edit, since its own justification depends on that
   edit landing first (or in the same change) to avoid citing a
   not-yet-real precedent. Exact text for every edit is quoted verbatim in
   §3 above and in the source workflow findings cited in §2.

11. **Install the gap-filling plugins (§3.E).**

    ```bash
    # interface-design + Anthropic's official frontend-design (both tools)
    claude plugin marketplace add Dammyjay93/interface-design
    claude plugin install interface-design@interface-design
    # enable frontend-design (already synced locally, currently disabled)
    claude plugin enable frontend-design@claude-plugins-official

    # threat-modeling (both tools; assumed path, confirm at execution time)
    git clone https://github.com/fr33d3m0n/threat-modeling ~/.claude/skills/threat-modeling
    git clone https://github.com/fr33d3m0n/threat-modeling ~/.codex/skills/threat-modeling

    # the-elements-of-style (both tools)
    claude plugin marketplace add obra/the-elements-of-style
    claude plugin install the-elements-of-style@the-elements-of-style
    codex plugin marketplace add obra/the-elements-of-style
    codex plugin add the-elements-of-style@the-elements-of-style

    # api-design-principles — vendor only the one skill (both tools)
    mkdir -p ~/.claude/skills/api-design-principles
    # copy only plugins/backend-development/skills/api-design-principles/{SKILL.md,references/,assets/}
    # from wshobson/agents (MIT) into ~/.claude/skills/api-design-principles/, then mirror to ~/.codex/skills/
    ```

12. **Add the frontend/UI routing bullet to `~/.claude/CLAUDE.md`** (§3.E.1),
    in the same change as step 11's `interface-design`/`frontend-design`
    install:

    ```markdown
    - **Product/dashboard UI ownership (interface-design vs. frontend-design):**
      any request to review, critique, audit, or de-slop already-built UI
      routes to `interface-design` — only it ships dedicated
      `/interface-design:design-review` and `/interface-design:design-deslop`
      commands for that; `frontend-design` has no standalone equivalent
      (its own "critique, build, critique again" process critiques its own
      in-progress output during generation, not a separately-built
      interface). For new UI, the split is one-sided: `interface-design`'s
      own frontmatter already self-limits away from marketing ("Not for
      marketing pages, landing pages, campaigns, or brand-only work"), so
      on that axis it self-disambiguates. `frontend-design` carries no
      converse carve-out — its trigger is generic "building new UI or
      reshaping an existing one," and its README usage examples include
      "create a dashboard for a music streaming app." Because a dashboard
      is not marketing, interface-design's existing self-limit doesn't
      resolve the overlap, and a bare "build me a dashboard" request would
      otherwise plausibly fire both. `interface-design` also owns
      product/dashboard/SaaS/admin/tool/data UI and is the only one of the
      two with persisted cross-session design-system memory
      (`.interface-design/system.md`). Route by the surface's job, not the
      word "dashboard": a working tool a user will operate repeatedly
      (data views, admin controls, settings, internal tool) goes to
      `interface-design`; a one-off promotional/showcase surface, even one
      styled like a dashboard, goes to `frontend-design`. Genuinely
      ambiguous case → ask. Trade-off: routing product dashboards to
      `interface-design` forgoes `frontend-design`'s distinctive-aesthetic-
      risk angle — invoke `frontend-design` explicitly if that's
      specifically wanted.
    ```

13. **Add the security-tooling notes** — `~/.claude/CLAUDE.md` (threat-modeling
    vs. single-finding questions) and `.agents/playbooks/security-review.md`
    (optional escalation cross-reference):

    ```markdown
    ## Skill precedence: threat-modeling vs. single-finding security questions

    threat-modeling (assumed install path: ~/.claude/skills/threat-modeling
    — git-cloned from fr33d3m0n/threat-modeling, its own upstream repo, no
    plugin-marketplace manifest) runs a heavyweight 8-phase whole-system
    STRIDE audit. Its own frontmatter says it MUST be invoked instead of
    analyzing security yourself, which over-triggers on narrow follow-ups.
    This note overrides that for one case its own "NOT for" list doesn't
    cover:

    Do NOT invoke threat-modeling for a follow-up about one already-
    identified finding (e.g. "is this actually exploitable?", "how bad is
    this one?") — including findings raised by security-guidance's
    Stop-hook diff review or commit reviewer. Answer those directly,
    scoped to that one finding.

    Only invoke threat-modeling when the user deliberately asks for a
    full, standalone audit/threat model of a codebase, app, or project.

    threat-modeling has its own upstream and may be resynced via `git pull`
    inside its skill directory; per this file's editing rule, don't edit
    its SKILL.md directly to narrow triggers — keep precedence rules here.
    ```

    Append to `.agents/playbooks/security-review.md`:

    ```markdown
    ## 5. Escalate to a full audit

    This playbook is scoped to the current diff. If review surfaces
    something beyond one change — systemic exposure, unclear trust
    boundaries, or a request for a standalone security assessment — that
    is out of scope here. If the threat-modeling skill is installed, it
    can run a full 8-phase STRIDE threat model (DFD, risk assessment,
    pentest plan) as a separate, deliberately-requested activity. Do not
    reach for it to answer single-finding follow-up questions raised
    during this review — resolve those in place per section 4.
    ```

    (This addition is consistent with this same plan's own step 9, which
    is what first establishes a skill-name cross-reference inside
    `code-review.md` — not a pre-existing repo precedent; none exists
    anywhere in this codebase's history today.)

14. **Install `codex-security` and add the Codex-side security routing note**
    (§3.G.1–5):

    ```bash
    codex plugin add codex-security@openai-curated
    ```

    Append to `~/.codex/AGENTS.md` (confirmed present, currently empty —
    this becomes its first content):

    ```markdown
    ## Security tooling routing (codex-security vs. threat-modeling)

    Both `codex-security` and `threat-modeling` are installed.
    `codex-security`'s own scan family (`security-scan`,
    `security-diff-scan`, `deep-security-scan`, `finding-discovery`) and
    its internal `threat-model` phase-skill both use broad trigger
    language that can collide with a standalone `threat-modeling` request.
    Treat `codex-security`'s `threat-model` skill as scan-internal only
    (per its own hard rule: "do not use as the primary trigger for full
    PR, commit, branch, patch, or repository scans"). Route any standalone
    request to build, update, or review a threat model (STRIDE analysis,
    trust-boundary mapping, attacker-surface review) that is not part of
    an active codex-security scan to the `threat-modeling` skill instead.

    Known asymmetry: Claude Code's `security-guidance` (passive, hooks-only,
    fires automatically on every Edit/Write, Stop, and git commit/push) has
    no installed Codex equivalent. `codex-security` is the compensating
    capability on Codex but is active/explicit-invocation only — do not
    assume Codex gets the same always-on diff-review safety net Claude
    gets from `security-guidance` without the user explicitly invoking a
    codex-security scan.

    Known friction: `codex-security`'s `deep-security-scan` requires
    `agent_depth_2`/`delegated_workers`/`usable_worker_slots_6` at `block`
    severity; this machine's current `agents.max_depth = 1` (v1 mode) will
    trip a mandatory remediation dialogue for that specific scan mode.
    `security-scan`/`security-diff-scan` are unaffected.
    ```

15. **Port `obsidian-skills` to Codex** (§3.G.7):

    ```bash
    cp -r ~/.claude/skills/obsidian-skills/skills/obsidian-cli ~/.codex/skills/
    cp -r ~/.claude/skills/obsidian-skills/skills/json-canvas ~/.codex/skills/
    cp -r ~/.claude/skills/obsidian-skills/skills/obsidian-bases ~/.codex/skills/
    cp -r ~/.claude/skills/obsidian-skills/skills/defuddle ~/.codex/skills/
    cp -r ~/.claude/skills/obsidian-skills/skills/obsidian-markdown ~/.codex/skills/
    ```

16. **Verify** — see §5 in full; run in a **fresh** Claude Code session and
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
- **Claim (real behavior):** Given a bare "add a small utility function" /
  "tweak this config value" request (single-function, no new dependency, no
  cross-subsystem span), when the two-signal threshold is in effect, then
  the agent proceeds on ponytail's fast path without invoking
  brainstorming's design gate.
  - **Prove with:** transcript of one such request in the fresh session.
- **Claim (real behavior):** Given a "let's build a new payments module
  that needs a new charting library" request (genuinely needs a new
  dependency — trips ponytail's rung 4), when the two-signal threshold is
  in effect, then the agent routes to brainstorming's gate before writing
  implementation code.
  - **Prove with:** transcript of one such request.
- **Claim (real behavior):** Given a tactical-but-architectural question
  ("should this endpoint be async or sync") with both `rethink` and
  `brainstorming` installed, when rethink's narrowed trigger is in effect,
  then rethink still produces its standing first-principles analysis
  (brainstorming's gate does not fire, since this isn't a
  new-feature/component-creation request).
  - **Prove with:** transcript of one such request.
- **Claim (real behavior):** Given a "build a new dashboard widget for X"
  request (squarely brainstorming's new-build territory) with both
  installed, when rethink's narrowed trigger is in effect, then rethink
  stays quiet and brainstorming's interactive design gate runs instead.
  - **Prove with:** transcript of one such request.
- **Claim (real behavior):** Given a request phrased as "grill me on my
  rough idea for X" (bare idea, no existing plan), when `grilling`'s fixed
  description is in effect, then the agent routes to `brainstorming` first
  rather than launching grilling's interview directly.
  - **Prove with:** transcript of one such request.
- **Claim:** Given the repo-side edits (step 9), when a PR is opened, then
  `pr-policy`/`lint`/`cspell`/`markdownlint` all pass (these are pure
  documentation additions, no code paths touched).
  - **Prove with:** `gh pr checks <n> --watch` transcript.
- **Claim (real behavior):** Given a "build me a dashboard for X" request
  with both `interface-design` and `frontend-design` active, when the
  CLAUDE.md routing bullet is in effect, then the agent routes to
  `interface-design` (or explicitly asks, if genuinely ambiguous) rather
  than silently picking one or invoking both.
  - **Prove with:** transcript of one such request in the fresh session.
- **Claim (real behavior):** Given a follow-up question about one
  already-flagged security-guidance finding ("is this actually
  exploitable?"), when the threat-modeling precedence note is in effect,
  then the agent answers directly, scoped to that finding, without
  launching the 8-phase STRIDE workflow.
  - **Prove with:** transcript of one such request.
- **Claim:** Given `api-design-principles` is vendored as a single skill,
  when the skill list is inspected, then no `architecture-patterns`,
  `microservices-patterns`, `cqrs-implementation`, `event-store-design`,
  `projection-patterns`, `saga-orchestration`, `temporal-python-testing`,
  or `workflow-orchestration-patterns` skill is present on either tool, and
  no `tdd-orchestrator`/`test-automator` agent persona exists to compete
  with the retired `tdd`.
  - **Prove with:** `find ~/.claude/skills ~/.codex/skills -iname SKILL.md`
    listing; absence of those 8 names.
- **Claim:** Given `grill-me` is retired, no `grill-me` entry remains on
  Claude Code, and Codex already had none.
  - **Prove with:** `ls ~/.claude/skills/ ~/.codex/skills/` (absent on both).
- **Claim:** Given `codex-security` is installed on Codex, when
  `codex plugin list` is run, then `codex-security@openai-curated` shows
  `installed, enabled`.
  - **Prove with:** `codex plugin list` transcript.
- **Claim (real behavior):** Given a standalone "build a threat model for
  this repo" request on Codex with both `codex-security` and
  `threat-modeling` installed, when the `~/.codex/AGENTS.md` routing note
  is in effect, then the request routes to `threat-modeling`, not
  `codex-security`'s internal `threat-model` phase-skill.
  - **Prove with:** transcript of one such request.
- **Claim:** Given `obsidian-skills` is ported to Codex, when
  `~/.codex/skills/` is inspected, then `obsidian-cli`, `json-canvas`,
  `obsidian-bases`, `defuddle`, and `obsidian-markdown` are all present
  with no naming collisions against existing entries.
  - **Prove with:** `ls ~/.codex/skills/` transcript.
- **Claim:** Given `coderabbit` and the official `code-review` marketplace
  plugin were both evaluated and declined, when `claude plugin list` /
  `codex plugin list` are run, then neither is installed.
  - **Prove with:** both transcripts, absence confirmed.

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
- [ ] improve's precedence sentence added (promoted from deferred to required)
- [ ] `grill-me` retired (Claude only; Codex already absent)
- [ ] `interface-design` installed + `frontend-design` enabled (both), CLAUDE.md routing bullet added in the same change
- [ ] `threat-modeling` installed on both tools (path confirmed at execution time), CLAUDE.md + security-review.md notes added
- [ ] `the-elements-of-style` installed on both tools
- [ ] `api-design-principles` vendored as a single skill on both tools (not the whole backend-development plugin)
- [ ] `codex-security` installed on Codex, `~/.codex/AGENTS.md` routing note added
- [ ] threat-modeling-vs-security-threat-model choice made explicitly (mirror fr33d3m0n, or use Codex's native curated skill)
- [ ] `obsidian-skills` ported to Codex (5 sub-skills)
- [ ] `coderabbit` and the official `code-review` plugin confirmed NOT installed
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
- **Decision #1 resolved — ponytail vs. brainstorming ceremony threshold.**
  Resolved via a Generate→Verify workflow (2 independent option-generation
  agents, then 2 adversarial verification agents re-checking every quoted
  claim against ponytail's and brainstorming's actual SKILL.md text).
  Adopted: the two-signal threshold now in step 8's CLAUDE.md note. Two
  claims in the generating analysis did not survive verification and were
  corrected before landing in step 8: one option's "pro" had misattributed
  brainstorming's own anti-pattern examples ("single-function utility,"
  "config change") as ponytail's worked examples — the reverse of the
  truth — and a claim that the threshold's two signals were "objective, not
  vibes" was overstated (the analysis's own con-list concedes they're
  gameable). Verification also surfaced a framing point neither original
  option named: ponytail and brainstorming mostly govern different
  *phases* (build vs. design), so this was never really a "which skill
  wins" question — the actual collision is only the narrow timing issue
  step 8's bullet now states directly.
- **Decision #2 resolved — rethink's retirement/narrowing scope.** Same
  workflow, same rigor, applied to three options (keep-and-yield / full
  retirement / narrow-the-trigger). Adopted: narrow the trigger
  unconditionally (step 7), plus update rethink's own description to name
  the `obra/superpowers` pairing explicitly. An earlier pass of this
  revision proposed a runtime conditional guard ("only narrow if
  brainstorming is installed this session") to avoid regressing
  hypothetical "solo-rethink" installers — corrected after direct
  pushback: rethink is a homebrew, single-user plugin with no such install
  base to protect, so the conditional was solving a non-problem at the
  cost of real complexity; removed. Verification (run before that
  correction, so scoped to the three-option choice, not the conditional
  question) struck two
  fabricated/miscounted claims from the full-retirement option before they
  could mislead a future reader: a claim that rethink's SKILL.md names
  "three traps (legacy trap, analogy trap, complexity trap)" — grepped the
  whole plugin, zero matches, nothing named "trap" exists in the source —
  and a claim that brainstorming's checklist has 8 steps (it has 9). Two
  more consequential gaps neither option's write-up mentioned, and which
  this plan does not claim to have resolved: (1) `using-superpowers` opens
  with an explicit `<SUBAGENT-STOP>` self-exclusion for subagent-dispatched
  tasks — the "non-negotiable, always-on mandate" premise motivating this
  whole reconciliation doesn't even engage when this harness runs work as a
  subagent; (2) `using-superpowers`' own "Skill Priority" section only
  orders process-skills-before-implementation-skills — it says nothing
  about two competing *process* skills (rethink vs. brainstorming), so even
  if the recommendation's flagged ambiguity ("is a SessionStart directive a
  user instruction or a skill?") resolves toward "skill," a second,
  independent ambiguity remains genuinely open. Neither gap blocks shipping
  the narrowed-trigger fix, but both are real residual unknowns, not
  settled questions — noted here rather than papered over.
- `using-superpowers`'s aggressive mandatory-invocation framing was found by
  directly reading its full body, not by either cross-check workflow —
  neither workflow was scoped to include it, since earlier passes treated it
  as "not independently meaningful." Worth remembering as a process lesson:
  the skill most likely to collide with existing always-on directives was
  the one initially read least carefully (frontmatter + 8 lines, not the
  full ~50-line body).
- **Gap-plugin integration workflow caught a stale-context bug in its own
  task framing:** the workflow was told a "Skill precedence" section
  already existed in `~/.claude/CLAUDE.md` to append to — it doesn't yet
  (that section only exists as unexecuted step 8 of this same plan). The
  workflow caught this itself by reading the live file rather than trusting
  the framing, which is exactly the "verify against the live repo every
  time, never a snapshot baked into a doc" failure mode CLAUDE.md's own
  rule 1 warns about. Both sequencings are handled in §4 step 12's text.
- **A first-draft fix for `api-design-principles` (install the whole
  `backend-development` plugin) was wrong** — verification found it pulls
  in 9 skills, 8 agent personas, and a TDD-orchestration command, not "1
  skill + trivial extras." Caught before it shipped; replaced with
  vendoring only the target skill (§3.E.4).
- **A first-draft fix for `pr-review-toolkit` vs. superpowers' own
  `code-reviewer.md` (route dispatch to `pr-review-toolkit:code-reviewer`
  "instead of" the superpowers template, "keeping both capabilities") was
  self-contradictory** — adversarial verification caught that this would
  drop superpowers' unique review dimensions (plan alignment, architecture,
  production-readiness, the "Ready to merge" verdict) at exactly its
  Mandatory checkpoints, not preserve them. Corrected to: no consolidation,
  run both independently, accept minor overlap on bug-finding as a smaller
  cost than lost coverage (§3.B.9).
- **A first-draft justification for declining the official `code-review`
  marketplace plugin was partly wrong** — it described the two marketplace
  copies as "near-identical" and claimed both post inline `gh` PR comments;
  a direct diff showed materially different mechanics (109 vs. 92 lines,
  different agent counts/models, and the official copy has no inline-
  comment tool at all, posting one top-level `gh pr comment` instead). The
  official copy also has two genuinely novel review angles (git-blame
  historical context, past-PR-comment precedent) nothing else in this
  toolkit replicates. The decline verdict survives on an independent,
  correct rationale (workflow mismatch — GitHub-PR-bot-native vs. this
  user's local interactive style), but the "duplicate, no added value"
  argument was corrected, not the conclusion (§3.B.9/§3.F.3).
- **A first-draft security-tooling collision fix for Codex (`codex-security`
  vs. `threat-modeling`) was too narrow** — anchored only on
  `codex-security`'s own internal `threat-model` phase-skill trigger text,
  because the real `threat-modeling` (fr33d3m0n) trigger text hadn't been
  checked. A draft of that skill was found already sitting in this
  session's own scratchpad; its actual trigger ("MUST be invoked instead of
  analyzing security yourself," firing on generic "security audit," "find
  vulnerabilities") is broad enough to collide with `codex-security`'s
  entire scan family, not just its narrow internal phase-skill. Broadened
  before shipping (§3.G.2/§4 step 14).
- **A first-draft install-friction note for `codex-security` understated
  severity** — it characterized `agent_depth_2`/worker-slot requirements as
  "warn/suggest" (non-blocking); verification found `deep_security_scan`'s
  profile marks these `block` severity specifically, which under this
  machine's current `max_depth = 1` config genuinely triggers a mandatory
  remediation dialogue for that one scan mode (not for the two primary
  entry-point skills). Corrected in §3.G.5.
- **A first-draft justification for the `obsidian-skills`-on-Codex
  packaging asymmetry was wrong** — it claimed Claude's copy is "the only
  side that can have live updates via the plugin marketplace mechanism."
  `claude plugin list` shows it's not marketplace-tracked at all (it's a
  `skills-directory` auto-detected plain git clone); the real (and
  Codex-replicable) update path is just `git pull`. Corrected justification
  in §3.G.7: the flat-copy recommendation stands, but because it matches
  Codex's existing all-loose-skill convention, not because Claude's copy is
  uniquely privileged. A second claim in the same finding — "memoria-vault
  is itself an Obsidian vault project" — was also corrected to the
  narrower, verified truth: the repo itself is a standalone CLI/engine with
  Obsidian as an optional adapter; the real relevance is one level down, in
  `vault-template/` (what the installer deploys to an end user's vault).
- **A newly-discovered Codex-native alternative for the security/threat-
  modeling gap was surfaced only during the parity audit, not the original
  gap-plugin research:** an official OpenAI-curated `security-threat-model`
  skill already sits at `~/.codex/vendor_imports/skills/skills/.curated/
  security-threat-model` (predates this session, installable via Codex's
  own `$skill-installer`) — a lower-trust-surface alternative to cloning
  the third-party `fr33d3m0n/threat-modeling` repo onto Codex. This plan
  does not pick between file-identical mirroring and this native
  alternative — see §3.G.3, a deliberately surfaced, not silently resolved,
  choice.
- **Two citation/counting defects were caught in the retirement-recheck
  audit and corrected before shipping:** a quote supporting the grilling-
  vs-brainstorming argument ("this is a checklist you run yourself — not a
  subagent dispatch") was misattributed to brainstorming's Spec Self-Review
  section; it actually appears in `writing-plans`' Self-Review section — a
  different file. And codebase-design's glossary was described as "the
  formal 11-term glossary," which miscounts the enumerated items (12, by
  direct count) and omits two section headers that actually exist. Neither
  error changed the underlying conclusion (grilling and codebase-design
  both still survive the retirement bias), but both are exactly the kind
  of quoted "evidence" that gets trusted at face value once baked into an
  exec-plan — corrected in §3.B.5 and §3.B.10/§3.E.4's text above rather
  than left as-is.

## 10. Interfaces & dependencies

- **Plugin source:** `github.com/obra/superpowers`, MIT license. Manifests:
  `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` (Claude
  Code), `.codex-plugin/plugin.json` (Codex).
- **Files edited outside `memoria-vault`** (no git history inside this
  repo; recovery is this plan's own quoted exact-edit text): `~/.claude/
  skills/{grilling,caveman,improve}/SKILL.md` + Codex copies; `~/.claude/
  CLAUDE.md`; `~/.claude/plugins/marketplaces/rethink/plugins/rethink/{hooks/
  directive.md, skills/rethink-audit/SKILL.md, .claude-plugin/plugin.json,
  .codex-plugin/plugin.json}`; `~/.codex/AGENTS.md` (new file — currently
  empty, this plan supplies its first content).
- **Never edited, on principle:** any file under `~/.claude/plugins/cache/
  {ponytail,superpowers}/...`, `~/.claude/skills/threat-modeling/` (has its
  own upstream, `fr33d3m0n/threat-modeling`, resyncable via `git pull`),
  `~/.codex/plugins/cache/codex-security/`, or any Codex equivalent — all
  are third-party/upstream-tracked with their own release cadence; a
  direct edit would be silently discarded (or clobbered on the next
  resync) and would block a clean upgrade path. Every fix that would
  otherwise have touched one of these installed files (the `tdd` seams
  idea, the `brainstorming`/`writing-plans` terminology drift, the
  `interface-design`/`frontend-design` routing split, the `threat-modeling`
  trigger narrowing) is instead delivered as standing guidance in
  `~/.claude/CLAUDE.md` or `~/.codex/AGENTS.md`, the same treatment already
  used for the `ponytail`-vs-TDD precedence rule.
- **New installs outside `memoria-vault`, no direct edits, plain
  install/vendor actions:** `~/.claude/skills/{api-design-principles,
  threat-modeling}/` + Codex mirrors (vendored/cloned, not edited);
  `~/.claude/plugins/marketplaces/{interface-design,the-elements-of-style}/`
  + installs; `frontend-design` enabled (already-synced marketplace copy);
  `~/.codex/plugins/cache/codex-security/` (installed via
  `openai-curated`); `~/.codex/skills/{obsidian-cli,json-canvas,
  obsidian-bases,defuddle,obsidian-markdown}/` (ported from
  `~/.claude/skills/obsidian-skills/skills/`).
- **Files edited inside `memoria-vault`** (normal git history, PR-reviewed):
  `AGENTS.md`; `.agents/playbooks/code-review.md`; `.agents/playbooks/
  exec-plan.md`; `.agents/playbooks/security-review.md` (new "Escalate to
  a full audit" section); `.agents/templates/exec-plan.md`; `.agents/
  templates/handoff.md`.
- **Superseded/retired:** `~/.claude/skills/tdd/` and `~/.codex/skills/
  tdd/` (adapted earlier this session from `mattpocock/skills`), retired
  by step 4; `~/.claude/skills/grill-me/` (Claude-only pointer, zero
  independent capability), retired by step 4 — no Codex-side action, it
  was never there.
- **Considered and declined, never installed:** the official Anthropic
  `code-review` marketplace plugin (both `claude-code-plugins` and
  `claude-plugins-official` copies); `coderabbit@openai-curated` on Codex.
- **Checked and left alone, with reasons on file:** `.agents/playbooks/
  {design-history,release,verify-change}.md`, `.agents/
  templates/review-report.md`, `.agents/system/*.md` (three maps), `.agents/
  skills/{policy-change-review,schema-change}/SKILL.md`, `codebase-design`.

## 11. Artifacts & notes

- {{ command transcripts pasted here as the plan runs }}

## 12. Outcomes & retrospective

- **Shipped:** {{ fill at close }}
- **Still open:** {{ fill at close — both process-ceremony decisions (§9)
  are resolved in this plan as of this revision; fill in only genuinely new
  items discovered during execution, e.g. if the §5 smoke tests show either
  threshold needs adjustment }}
- **Routed to:** N/A for decisions/design-history; repo-side doc edits go
  through a normal PR
- **Lessons:** {{ fill at close }}
