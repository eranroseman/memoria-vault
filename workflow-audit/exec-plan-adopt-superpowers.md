# ExecPlan — Build the complete agent skill workflow, with `obra/superpowers` as the base

## 0. Metadata

- **Task:** Install `obra/superpowers` (13 skills + `using-superpowers`) for
  both Claude Code and Codex as the base of the agent-skill toolkit; retire
  `tdd` and `grill-me`; install five gap-filling plugins/skills across four
  bundles (§3.E); close two cross-tool parity gaps (`codex-security` on
  Codex, `obsidian-skills` ported to Codex, §3.G); apply every fix this
  collides with in the personal-skill layer (§3.B) and this repo's own
  `.agents/`/`AGENTS.md` conventions (§3.C); decline three candidates that
  would not improve anything (§3.F). **Rationale for every individual
  retire/adopt/adapt/decline call lives in
  [`decisions-adopt-superpowers.md`](decisions-adopt-superpowers.md), not
  here** — this file states what to do and how to verify it worked.
- **Worktree / branch:** None on `memoria-vault` for the *implementation* —
  the skill/plugin files live under `~/.claude/` and `~/.codex/` (per-user
  tool config, not repo content), so `AGENTS.md` §1's git-worktree setup does
  not apply there. It does apply to the `memoria-vault`-tracked edits this
  plan makes (a new `CLAUDE.md`, `AGENTS.md`, and eight files under
  `.agents/`) — those go through the normal worktree → branch → PR flow, not
  a direct edit on `main`. This plan file itself lives on the **`scratch`**
  branch under `scratch/workflow-audit/` (this repo's holding area for
  cross-cutting, non-release-scoped plans).
- **Related decisions:** All in
  [`decisions-adopt-superpowers.md`](decisions-adopt-superpowers.md), per
  `AGENTS.md`'s own ExecPlan mandate 5 ("architectural and product
  decisions... go to the release decision ledger... and are linked, never
  recorded only in the plan"). This initiative isn't release-scoped, so
  that file plays the decision-ledger role for it.
- **Related issues / milestone:** — (personal tooling + repo-doc
  consistency, not release-scoped; milestone `0.1.0` is unaffected)
- **Started:** 2026-07-06 · **Last updated:** 2026-07-06

## 1. Purpose / big picture

Install `obra/superpowers` as the base of the full agent-skill toolkit for
both Claude Code and Codex, then reconcile everything it touches: the
already-installed personal-skill layer, this repo's own `.agents/`
conventions, and a set of gap-filling plugins that close capability holes
superpowers itself doesn't cover. See
[`decisions-adopt-superpowers.md`](decisions-adopt-superpowers.md) for why
each individual call was made.

What becomes observable when this plan is complete: the 13 superpowers
skills work in both tools *and* nothing already installed gives
contradictory guidance when they fire together *and* this repo's own
`.agents/` conventions either absorb the new capability with an explicit
cross-reference or explicitly document why they don't need to *and*
`AGENTS.md`'s own Skills table names only things that actually exist.

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
- **Hook coexistence is already empirically proven**: this session's own
  SessionStart output showed ponytail's and rethink's hooks fire as two
  independent, additive `<system-reminder>` blocks; superpowers' own
  `hooks/session-start` (read in full: pure read-and-inject, no network
  calls) will coexist the same way.
- **`using-superpowers`** (the bundle's onboarding meta-skill, installed
  automatically) is a standing mandate to invoke any applicable skill,
  including before entering plan mode — this collides with this harness's
  native Plan Mode workflow and with `rethink`'s own always-on directive.
  Its own text supplies the resolution mechanism ("user instructions...
  take precedence over skills"), which this plan uses via a
  `~/.claude/CLAUDE.md` note (§4 step 8) rather than editing the vendored
  file. **Editing rule, load-bearing throughout this plan:** never edit a
  file under a third-party plugin's own installed/cached path (`ponytail`,
  `superpowers`, and anything else with an independent upstream, e.g.
  `threat-modeling`) — route any needed cross-reference through
  `~/.claude/CLAUDE.md`/`~/.codex/AGENTS.md` instead. `rethink` (the user's
  own plugin) and the cherry-picked loose skills (`grilling`, `caveman`,
  `codebase-design`, `improve`) have no such live-update mechanism and are
  safe to edit directly. Full rationale: `decisions-adopt-superpowers.md`.

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

**Evidence trail** (workflow run IDs referenced by the decisions ledger):
`wf_6aecf5d4-a9f`, `wf_dbbeb04c-e04`, `wf_4f8a76cf-7c8`, plus the
Generate→Verify and Check→Verify workflows named per-decision in
`decisions-adopt-superpowers.md`. Full reasoning for every finding is in
each run's `journal.jsonl` under
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

### B. Personal-skill-layer fixes

Rationale for each item below: `decisions-adopt-superpowers.md`. Exact text
for each fix: §4 as cross-referenced.

1. `ponytail` vs. `test-driven-development` (genuine contradiction on test
   timing) → CLAUDE.md note: TDD's ordering wins when in effect; ponytail
   governs size/shape after (§4 step 8).
2. `rethink`'s standing directive vs. `brainstorming` → narrow rethink's
   trigger unconditionally in `hooks/directive.md`; update its description
   to name the pairing (§4 step 7).
3. `rethink-audit` vs. `brainstorming`, separately (self-contained, doesn't
   inherit fix #2) → own boundary clause (§4 step 7).
4. `rethink-audit`'s `migrate:` step vs. `writing-plans` (a sequencing
   sketch could be mistaken for an executable plan) → one-line boundary in
   `rethink-audit`'s own `SKILL.md` (§4 step 7).
5. `grilling` vs. `brainstorming` (routing ambiguity — neither skill's
   description says whether a plan must already exist) → sharpen
   `grilling`'s description + one routing line (§4 step 5).
6. `caveman` vs. `brainstorming`/`writing-plans` (persisted-artifact
   exemption doesn't cover spec/plan files) → extend the exemption (§4
   step 6).
7. `tdd`'s retired "seams" idea + a terminology drift in `brainstorming`/
   `writing-plans` (both say "unit"/"boundaries" instead of
   "module"/"seam") → one `~/.claude/CLAUDE.md` note naming
   `codebase-design` canonical (§4 step 8; none of the three superpowers
   files touched directly).
8. `improve` vs. `subagent-driven-development`/`writing-plans`/
   `verification-before-completion` (genuinely distinct on 3 axes: dispatch
   cardinality, plan durability, worktree disposition) → precedence
   sentence in `improve`'s own `SKILL.md`, promoted from deferred to
   required.
9. `pr-review-toolkit` vs. superpowers' own `code-reviewer.md` template →
   no fix, both kept running independently (5 of 6 `pr-review-toolkit`
   agents have no superpowers equivalent at all; the 6th only partially
   overlaps). The separate, uninstalled official `code-review` marketplace
   plugin is declined (§3.F.3) for workflow-mismatch reasons, not
   duplication.
10. `codebase-design` vs. the not-yet-installed `interface-design` → checked
    directly against `interface-design`'s actual SKILL.md; a genuine word
    overlap on "Depth"/"Interface" exists but in unrelated domains with
    already-disambiguated trigger surfaces. No fix needed.

### C. Repo-convention fixes in `memoria-vault` itself

Rationale for each item: `decisions-adopt-superpowers.md`. This section
carries the exact text to apply (needed to execute); the "why" behind each
is not repeated here.

0. **NEW file: `main/CLAUDE.md`** — does not exist today; add it containing
   exactly:

   ```markdown
   @AGENTS.md
   ```

   New tracked file in `main/`, added in the same PR as the other repo-side
   edits (§4 step 9).

1. **`AGENTS.md`'s Skills table — full replacement**, not an addition. New
   table:

   ```markdown
   | Stage | Skill | Use when |
   |---|---|---|
   | Whole-docs audit | [`docs-audit`](.agents/playbooks/docs-audit.md) | Fresh Diátaxis, consistency, generated-reference, terminology, coverage, and live-link audit across `docs/` |
   | Any docs PR | [`docs-review`](.agents/playbooks/docs-review.md), plus `the-elements-of-style:writing-clearly-and-concisely` for prose clarity | Before opening — checks quadrant fit, links, indexing, terminology, and sentence-level clarity |
   | Any PR | [`code-review`](.agents/playbooks/code-review.md), which dispatches `superpowers:requesting-code-review` → `pr-review-toolkit:code-reviewer` | Before opening — catches bugs, CLAUDE.md-style compliance, plan alignment, and production-readiness |
   | Deeper review on a dimension | `pr-review-toolkit` agents: `silent-failure-hunter` (error handling), `pr-test-analyzer` (coverage/edge cases), `code-simplifier`, `comment-analyzer`, `type-design-analyzer` | After the above — probe one lens. Conversational — ask for the lens you want |
   | Sensitive-path changes | [`security-review`](.agents/playbooks/security-review.md), plus `security-guidance` (passive, automatic) and `threat-modeling` (deliberate full audit, only if escalation is warranted — see the playbook's own "Escalate to a full audit" section) | PRs touching `scripts/`, `.github/`, `vault-template/.memoria/`, `design-history/`, `AGENTS.md`, or agent guidance directories |
   | Confirming a fix | [`verify-change`](.agents/playbooks/verify-change.md), plus `superpowers:verification-before-completion` as a complementary claim-honesty check | After a change — runs the app to confirm actual behavior |
   | New or cut release | [`release`](.agents/playbooks/release.md) | Scaffolds the release folder/plan, milestone (scope), and "Release <version>" parent issue with readiness/stage sub-issues; release-please owns version/notes |
   ```

   Also add, directly under the table: *"This repo's own Critical/High/
   Medium/Low severity vocabulary (used in review reports and this table)
   is lighter than `requesting-code-review`'s Critical/Important/Minor
   scale — never mix the two inside one persisted report, issue, or PR
   comment; a report written for this repo uses this repo's four-tier
   scale throughout."* Also update the "Passive, when installed" paragraph
   directly below the table to add `threat-modeling` and `codex-security`
   alongside the existing `security-guidance` mention.

2. **`.agents/playbooks/code-review.md`** — two additions, exact text:

   After "## 1. Establish scope" (new final paragraph in that section):

   > **Dispatching this as an isolated review.** When reviewing your own
   > recent work rather than an external diff, follow
   > `superpowers:requesting-code-review`'s context-isolation mechanic:
   > dispatch a reviewer subagent given only the base/head SHAs and
   > requirements, never your own session history, so the review judges the
   > work product, not your reasoning trail. Route the dispatch to the
   > installed `pr-review-toolkit:code-reviewer` subagent for the bug/
   > compliance pass in section 2 below — its confidence-gated output is
   > not a substitute for the plan-alignment and production-readiness
   > checks this playbook's own report format still owns.

   At the end of "## 4. Report" (new final bullet):

   > - After presenting findings, apply `superpowers:receiving-code-review`'s
   >   discipline: fix Critical issues immediately, fix Important before
   >   proceeding, note Minor for later, and push back explicitly (with
   >   reasoning) on a finding that looks wrong — don't apply it uncritically.

   The playbook's own review criteria/checks/report-format sections stay
   authoritative — the two superpowers skills supply mechanics, not the
   domain-specific policy.

3. **`.agents/playbooks/verify-change.md`** — one optional line appended at
   the very end (its own numbered procedure, §1–§5, stays untouched):

   > *(If `superpowers:verification-before-completion` is installed, its
   > claim-honesty discipline complements this playbook's own evidence-first
   > procedure. This file's own steps remain authoritative regardless.)*

4. **`.agents/playbooks/exec-plan.md`** — two additions, exact text:

   New 5th item appended to "## Authoring":

   > 5. Size tasks using `superpowers:writing-plans`' right-sizing rule (a
   >    task should be independently testable and revertable) — but the
   >    deliverable still lands in this file's own template under
   >    `releases/<version>/` or `scratch/workflow-audit/`, never a new
   >    `docs/superpowers/plans/` file.

   New section, inserted after "## Running" and before "## Validating":

   > ## Reusing superpowers execution techniques
   >
   > An ExecPlan's own Concrete steps may be carried out using superpowers'
   > execution mechanisms as optional engines, not replacements for this
   > file's own record:
   >
   > - `superpowers:subagent-driven-development` — per-task implementer +
   >   two-stage reviewer subagent pattern, with its own model-tiering, for
   >   independently-testable task lists.
   > - `superpowers:executing-plans` — separate-session handoff mechanics,
   >   if the plan must be picked up by a different session or agent.
   >
   > Either technique may drive execution of the Concrete steps, but this
   > file's own Validation, Progress, Execution log, and Surprises sections
   > remain authoritative — neither technique's own plan-file default or
   > recovery ledger substitutes for this file's record.

5. **`.agents/templates/exec-plan.md`** — one-sentence pointer added to the
   "Concrete steps" guidance comment: *"See `.agents/playbooks/exec-plan.md`
   → 'Authoring' item 5 and 'Reusing superpowers execution techniques' for
   optional sizing/execution engines — this skeleton's own section shapes
   don't change."* Keeps the template in sync without duplicating guidance
   text into the skeleton itself.

6. **`.agents/templates/handoff.md`** — new section, exact text, appended
   at the end:

   > ## Result
   >
   > <!-- Filled by the RECEIVER after completing the handoff, not the dispatcher. -->
   >
   > **Status:** DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
   >
   > <!-- DONE: acceptance checks pass, nothing else to report.
   >      DONE_WITH_CONCERNS: acceptance checks pass, but note a risk/caveat below.
   >      NEEDS_CONTEXT: could not proceed without information only the dispatcher has — ask below.
   >      BLOCKED: a hard blocker outside the receiver's control — name it below. -->
   >
   > <!-- What was actually done, any deviation from Expected outputs, and why. -->

   Adopts `subagent-driven-development`'s four-way status vocabulary; its
   compaction-recovery ledger is not adopted.

7. **`.agents/playbooks/docs-review.md`** — one line appended to the end of
   "## 4. Check terminology and claims" (`docs-audit.md` needs no separate
   edit — it inherits via its own existing cross-reference to
   `docs-review.md`):

   > If the `the-elements-of-style` skill is installed, apply its
   > `writing-clearly-and-concisely` rules (active voice, omit needless
   > words) as a prose-clarity pass over any page that changed —
   > complementary to, not a substitute for, this section's terminology and
   > citation checks.

8. **`.agents/playbooks/design-history.md`, `release.md`,
   `.agents/templates/review-report.md`, `.agents/system/*.md` (three maps
   plus `change-impact.yaml`), `.agents/skills/policy-change-review/
   SKILL.md`, `.agents/skills/schema-change/SKILL.md`** — all read in full
   this session. All confirmed **leave-alone**: irreducibly repo-specific
   knowledge (exact file paths, test files, GitHub milestone/issue
   conventions, schema/policy invariants) no generic plugin could supply.
   `change-impact-map.md` carries its own instruction ("Generated by
   scripts/checks/agents_doctor.py; edit the source YAML instead") — any
   future change goes through `change-impact.yaml` and regeneration, never
   a direct hand-edit. No edits from this plan. (`security-review.md` was
   originally in this leave-alone set too — superseded by §3.E.2, which
   gives it one new section for the `threat-modeling` gap-fill.)

### D. Verification, not just presence-checking

Checking that 13 new names appear in a skill list proves the files parsed,
not that the skills behave correctly or that the fixes in B/C actually
resolved the conflicts they target. §5 adds an actual smoke-test: trigger at
least one skill from each of the three fixed conflict pairs (TDD vs.
ponytail; a design request, to confirm rethink now yields to brainstorming's
gate when appropriate; grilling vs. brainstorming routing) and read the
transcript, not just the skill-list membership.

### E. Gap-filling plugins — five plugins, four bundles

Rationale: `decisions-adopt-superpowers.md`.

1. **`interface-design` (Dammyjay93) + Anthropic's official `frontend-design`**
   — install both, add a CLAUDE.md routing bullet (exact text §4 step 12).
   **Gate: land the bullet in the same change that installs/enables both**
   — a precedence rule for two currently-inactive skills is a dead
   reference. No `codebase-design`/`improve` collision, no memoria-vault
   `.agents/` cross-reference needed (confirmed empirically: zero repo UI
   surface).
2. **`threat-modeling` (fr33d3m0n)** — install, fix via CLAUDE.md (exact
   text §4 step 13) and one new section in
   `.agents/playbooks/security-review.md`. Install path assumed as
   `~/.claude/skills/threat-modeling` by analogy with the other loose
   skills — not yet confirmed, flag as an assumption during execution.
3. **`the-elements-of-style` (obra)** — install, no fix required. One
   optional, precautionary CLAUDE.md line distinguishing it from `caveman`
   — skip if minimizing CLAUDE.md churn is preferred.
4. **`api-design-principles`** — vendor only
   `plugins/backend-development/skills/api-design-principles/` (SKILL.md +
   references/ + assets/) from `wshobson/agents` (MIT) into
   `~/.claude/skills/api-design-principles/` and the Codex mirror. **Do
   not** install the whole `backend-development` host plugin. No CLAUDE.md
   precedence note needed; no memoria-vault repo-convention touch.

### F. Retirements

Rationale: `decisions-adopt-superpowers.md`.

1. `tdd` — retire (§3.B.7/§4 step 4).
2. `grill-me` — retire, do not port to Codex. `rm -rf
   ~/.claude/skills/grill-me` (§4 step 4). No Codex-side action needed.
3. Official Anthropic `code-review` marketplace plugin — considered,
   declined, never installed.
4. `coderabbit@openai-curated` (Codex) — considered, declined (§3.G.6).
5. Runtime conditional guard on rethink's brainstorming fix — considered,
   removed (§3.B.2).

### G. Cross-tool parity

Rationale: `decisions-adopt-superpowers.md`.

1. **`codex-security@openai-curated`** — install on Codex:
   `codex plugin add codex-security@openai-curated`.
2. **Collision fix:** append to `~/.codex/AGENTS.md` (exact text §4 step
   14) — routes standalone whole-system audit/STRIDE requests to
   `threat-modeling`, keeps `codex-security`'s own `threat-model` phase
   scan-internal only.
3. **Mirror `threat-modeling` onto Codex** at `~/.codex/skills/
   threat-modeling` once §3.E.2 finalizes it for Claude — **or** use
   Codex's own pre-existing native `security-threat-model` skill instead
   (`~/.codex/vendor_imports/skills/skills/.curated/security-threat-model`,
   installable via `$skill-installer`). **Not resolved here — decide at
   execution time.**
4. **Residual, accepted asymmetry:** no Codex equivalent to
   `security-guidance`'s passive hook layer. Documented via the same
   `~/.codex/AGENTS.md` note (§4 step 14).
5. **Known friction, not a blocker:** `codex-security`'s `deep-security-scan`
   will hit a blocked capability gate under this machine's current config
   (`agents.max_depth = 1`). `security-scan`/`security-diff-scan` are
   unaffected. No config change recommended now.
6. **`coderabbit@openai-curated`** — evaluated, declined (§3.F.4).
7. **Port `obsidian-skills`** (5 sub-skills) to Codex via `cp -r` (exact
   commands §4 step 15). Footnote: `defuddle`'s skill depends on an unmet
   local npm package (`npm install -g defuddle`) on both tools equally —
   not a new dependency introduced by porting.

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

   Apply, in this worktree, using the exact text quoted in §3.C above for
   each:

   - **NEW FILE** `CLAUDE.md` at the repo root, containing exactly `@AGENTS.md`
     (§3.C.0) — closes the Claude-Code-native-loading gap.
   - `AGENTS.md`'s Skills table — **full replacement**, not an addition (§3.C.1):
     every hedged "(plugin/project, when available)" row is replaced with a
     row naming a real file, skill, or plugin capability; the
     severity-vocabulary reconciliation note and the passive-tools paragraph
     are both updated in the same change.
   - `.agents/playbooks/code-review.md` — two additions (§3.C.2): the
     "Dispatching this as an isolated review" paragraph after "Establish
     scope," and the `receiving-code-review` bullet at the end of "Report."
   - `.agents/playbooks/verify-change.md` — one optional line appended at
     the very end (§3.C.3; revised from the earlier "no edit" call after a
     full direct read — see §9).
   - `.agents/playbooks/exec-plan.md` — two additions (§3.C.4): the 5th
     "Authoring" item, and the new "Reusing superpowers execution
     techniques" section between "Running" and "Validating."
   - `.agents/templates/exec-plan.md` — one-sentence pointer (§3.C.5).
   - `.agents/templates/handoff.md` — new "Result" section (§3.C.6).
   - `.agents/playbooks/docs-review.md` — one line appended to "## 4. Check
     terminology and claims" (§3.C.7). `docs-audit.md` needs no separate
     edit — it inherits via its existing cross-reference.
   - `.agents/playbooks/security-review.md` — new "Escalate to a full
     audit" section (§3.E.2/§4 step 13) — land this one in the same PR as
     `code-review.md`'s edit, since its own justification depends on that
     edit landing first (or in the same change) to avoid citing a
     not-yet-real precedent.

   `.agents/playbooks/design-history.md`, `release.md`,
   `.agents/templates/review-report.md`, `.agents/system/*.md`,
   `.agents/skills/{policy-change-review,schema-change}/SKILL.md` get **no
   edits** (§3.C.8) — confirmed via full direct read this revision, not
   secondhand.

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

- **Claim:** Given `main/CLAUDE.md` containing `@AGENTS.md` exists, when a
  fresh Claude Code session starts in `~/memoria-vault/main` (or a worktree
  of it), then AGENTS.md's content is present in context without the agent
  needing to read the file itself first.
  - **Prove with:** transcript of a fresh session where an early response
    correctly cites an AGENTS.md-only fact (e.g. the worktree-first rule)
    before any tool call reads AGENTS.md.
- **Claim:** Given the AGENTS.md Skills-table rewrite, when the table is
  read, then every row names a file, skill, or plugin that actually exists
  under this plan's final state — zero rows reference a command that isn't
  real.
  - **Prove with:** for each row, `find`/`ls` or `grep` confirming the named
    file/skill exists, or the named plugin is in `claude plugin list`.
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
- [ ] `main/CLAUDE.md` created (`@AGENTS.md` import) — new file, closes Layer-3 gap
- [ ] `AGENTS.md` Skills table fully replaced (zero dangling "(plugin/project, when available)" rows)
- [ ] repo-side worktree opened, `CLAUDE.md` (new) + `AGENTS.md` + 8 `.agents/` files edited (code-review.md, verify-change.md, exec-plan.md playbook, templates/exec-plan.md, templates/handoff.md, docs-review.md, security-review.md — plus AGENTS.md itself), PR opened and merged
- [ ] all §5 claims proven, transcripts pasted into §11
- [ ] release/checkpoint close only — N/A (no `design-history/` update needed)

## 8. Execution log

- {{ to be filled while running }}

## 9. Surprises & discoveries

Full history of what was found, corrected, and why (including two
structural misreadings, two fabricated/miscounted claims, five corrected
first-draft fixes, and the `AGENTS.md` Skills-table defect) lives in
`decisions-adopt-superpowers.md` — kept out of this file per its own
mandate that decisions/corrections are recorded in the ledger, linked, not
duplicated here. This section holds only what's genuinely still open or
worth watching **during execution**, not yet resolved:

- **Watch during validation:** if `brainstorming`'s own low invocation bar
  turns out in practice to absorb the tactical middle-band questions
  rethink's narrowed trigger reserves for it (e.g. "should this be async or
  sync" actually triggers `brainstorming`), the narrowing is illusory —
  reconsider full retirement of rethink's standing directive at that point.
- **Genuinely open, not resolved by this plan:** `using-superpowers`'s
  `<SUBAGENT-STOP>` self-exclusion means its mandate doesn't engage when
  this harness runs work as a subagent; separately, its "Skill Priority"
  section never resolves ordering between two competing *process* skills
  (only process-vs-implementation). Neither blocks shipping, both are
  residual unknowns.
- **Decided at execution time, not here:** §3.G.3 — mirror
  `fr33d3m0n/threat-modeling` onto Codex file-for-file, or use Codex's own
  native `security-threat-model` skill instead.

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
- **New file inside `memoria-vault`:** `CLAUDE.md` at the repo root of
  `main/` — did not exist before this plan; contains only `@AGENTS.md`,
  closing the Layer-3 discovery gap (§3.C.0/§9).
- **Files edited inside `memoria-vault`** (normal git history, PR-reviewed):
  `AGENTS.md` (Skills table fully replaced, not just added to);
  `.agents/playbooks/code-review.md`; `.agents/playbooks/verify-change.md`
  (one line, appended — revised from "no edit," see §9);
  `.agents/playbooks/exec-plan.md`; `.agents/playbooks/security-review.md`
  (new "Escalate to a full audit" section); `.agents/playbooks/docs-review.md`
  (one line, appended); `.agents/templates/exec-plan.md`; `.agents/
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
  {design-history,release}.md`, `.agents/
  templates/review-report.md`, `.agents/system/*.md` (three maps), `.agents/
  skills/{policy-change-review,schema-change}/SKILL.md`, `codebase-design`.
  (`verify-change.md` moved out of this list — it now gets one appended line,
  §3.C.3.)

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
