# Decisions — adopt-superpowers toolkit rebuild

Rationale record for every retire/adopt/adapt/decline call in
`exec-plan-adopt-superpowers.md`, per `AGENTS.md`'s "ExecPlans" mandate
("architectural and product decisions... go to the release decision ledger
... and are linked, never recorded only in the plan"). This initiative is
not release-scoped, so this file plays that role for it, on the same
`scratch` branch, in the same `scratch/workflow-audit/` location as the
plan it supports. Format follows `.agents/playbooks/design-history.md`'s
dated Y-statement convention.

---

**Y: Adopt `obra/superpowers` as the base of the agent-skill toolkit, for
both Claude Code and Codex.**
Because: an 8-agent adversarial re-verification (`wf_6aecf5d4-a9f`) of an
initial decline-most-skills call found the original analysis had
misread two skills' actual behavior; corrected, all 13 usable skills clear
adoption. Evidence: `wf_6aecf5d4-a9f`, `wf_dbbeb04c-e04` (personal-skill
collision check), `wf_4f8a76cf-7c8` (`.agents/` repo-convention
cross-check).

**Y: Retire the local `tdd` skill.**
Because: fully superseded by `superpowers:test-driven-development`; its one
unique idea (agree the test's seam before writing it) has no equivalent in
the superpowers skill, so it's preserved as a standing note in
`~/.claude/CLAUDE.md` rather than lost. Evidence: `wf_dbbeb04c-e04`.

**Y: Retire `grill-me`; do not port it to Codex.**
Because: re-examined with an explicit retirement bias (workflow
`wedgcpoi3`); its entire body is one line forwarding to `/grilling`, and
every invocation path it offers (explicit slash, conversational trigger) is
already served by `grilling` directly. Confirmed not a disguised technical
necessity: Codex's `agents/openai.yaml` `allow_implicit_invocation: false`
is a real equivalent to Claude's `disable-model-invocation`, so the
Claude-only asymmetry isn't a platform limitation. Retiring is itself the
cleanest parity (absent on both tools). Evidence: `wedgcpoi3` audit +
verify pass; direct read of `~/.claude/skills/grill-me/SKILL.md` and
`~/.claude/skills/grilling/SKILL.md`.

**Y: Narrow `rethink`'s trigger unconditionally, don't add a yield rule or a
runtime conditional guard.**
Because: a Generate→Verify workflow (`wkx7ju7qg`, 4 agents) weighed
keep-and-yield / full-retirement / narrow-the-trigger for the
rethink-vs-brainstorming collision; narrowing preserves rethink's
citation-grounded method undiluted for the tactical-but-architectural band
neither `brainstorming` nor rethink's own "scoped, tactical question"
exclusion reaches, without full retirement's dependency on an unsolicited
upstream PR into `obra/superpowers`. A first pass added a runtime
conditional guard ("only narrow if brainstorming is installed this
session") to protect a hypothetical "solo-rethink installer" — corrected
after direct user pushback: rethink is a homebrew, single-user plugin with
no such install base to protect, so the guard was solving a non-problem.
Evidence: `wkx7ju7qg` (generate+verify), corrected in-session after
2026-07-06 pushback.

**Y: Adopt the two-signal threshold (new-dependency OR multi-subsystem/
ambiguity) for the ponytail-vs-brainstorming ceremony collision.**
Because: same `wkx7ju7qg` workflow; the two skills mostly govern different
phases (build vs. design) — the real, narrow collision is only that
ponytail's "ship the lazy version now" instinct fires at the exact moment
brainstorming's hard gate forbids implementation before an approved design.
Residual risk accepted, not solved: the threshold is gameable
(salami-slicing); if unexamined-assumptions-on-trivial-work turns out to be
a recurring real problem, switch to brainstorming-always-wins instead.
Evidence: `wkx7ju7qg`.

**Y: Elevate `codebase-design` to canonical module-design vocabulary across
the toolkit.**
Because: this isn't hypothetical — the retired `tdd` skill's "Seams"
section already needed exactly this arbitration (its paraphrase would have
created a third, inconsistent definition of "seam" alongside
`brainstorming`'s and `writing-plans`' own looser "unit"/"boundary"
language). Checked directly against the not-yet-installed `interface-design`
plugin for a name collision: real word overlap on "Depth" and "Interface,"
but different domains (visual UI vs. module API) and already-disambiguated
trigger surfaces — no fix needed. Evidence: the `tdd`-seams / canonical-
vocabulary decision above, `wedgcpoi3` retirement audit, direct read of
`interface-design`'s SKILL.md.

**Y: Promote `improve`'s precedence note (vs. `subagent-driven-development`)
from deferred/optional to required.**
Because: `improve` and `subagent-driven-development` are genuinely distinct
on three axes (dispatch cardinality, plan durability/drift-tracking,
worktree disposition — disposable review sandbox vs. real feature branch)
confirmed by direct re-read of both skills' actual text, not the earlier
pass's summary. Promoted because the final toolkit adds several more
overlapping-sounding names (`interface-design`, `threat-modeling`, etc.),
raising the real cost of an agent guessing wrong. Evidence: `wedgcpoi3`.

**Y: Install `interface-design` (Dammyjay93) and enable Anthropic's official
`frontend-design`, with a CLAUDE.md routing rule splitting product/dashboard
UI from marketing/landing UI.**
Because: `interface-design` self-limits away from marketing in its own
frontmatter, but `frontend-design` has no converse carve-out and its own
README examples include a dashboard — a bare "build me a dashboard" request
could otherwise fire both. `interface-design` is also the only one of the
two with a standalone review command (`/interface-design:design-review`)
and persisted cross-session memory. Evidence: workflow `wdlhfiiar`
(check+verify); direct read of both plugins' SKILL.md (`interface-design`
confirmed 320 lines, not the ~600–900 originally guessed).

**Y: Install `threat-modeling` (fr33d3m0n) on Claude Code; route its
trigger-collision with single-finding follow-ups through CLAUDE.md, not a
SKILL.md edit.**
Because: it's a git-clone-based skill with its own upstream repo a user
might resync — qualifies for the "never edit a file with an independent
upstream" rule the same as `ponytail`/`superpowers`, even though it isn't
marketplace-managed. Its own frontmatter over-triggers ("MUST be invoked
instead of analyzing security yourself") on narrow follow-ups its own "NOT
for" list doesn't cover. Evidence: `wdlhfiiar` (check+verify),
`gh api repos/fr33d3m0n/threat-modeling` direct fetch.

**Y: Add `.agents/playbooks/security-review.md`'s "Escalate to a full
audit" section, justified as following this same plan's own precedent
(its `code-review.md` cross-reference edit, in the same repo PR), not a
pre-existing repo pattern.**
Because: the first-draft justification claimed to follow "the precedent
set by `code-review.md`'s cross-reference to `requesting-code-review`" —
verification found no such precedent exists anywhere in this codebase's
history (`git log --all -- .agents/playbooks/code-review.md`, zero hits).
Corrected: the precedent doesn't exist yet, but this same plan creates it
in the same change, so the addition is self-consistent, not
falsely-precedented. Evidence: `wdlhfiiar` verify pass.

**Y: Vendor only `api-design-principles` (from `wshobson/agents`), not the
whole `backend-development` host plugin.**
Because: installing at plugin granularity pulls in 9 full skills (not 1),
several with broad new-service/microservices triggers that compete
directly with `rethink` and `brainstorming`, plus a `tdd-orchestrator`/
`test-automator` pair and a `/feature-development --methodology tdd`
command that reintroduce a parallel, non-superpowers TDD pipeline —
directly working against the `tdd` retirement decision above.
`wshobson/agents` is MIT-licensed, confirmed via `gh api`, same precedent
already used for `codebase-design` itself. Evidence: `wdlhfiiar`
(check+verify), independent recount via fresh `gh api` calls.

**Y: Install `codex-security` on Codex for security-tooling parity; do not
treat it as a passive twin of `security-guidance`.**
Because: without it, Codex has at most 1 active security tool
(`threat-modeling`, once mirrored) against Claude's 2
(`security-guidance` + `threat-modeling`); with it, both reach 2. It's
explicit-invocation-only (10 skills, MCP-backed), never passive — the
absence of a Codex equivalent to `security-guidance`'s automatic hooks is
accepted as a residual, documented asymmetry, not solved. Evidence:
`wedgcpoi3` (audit+verify); direct read of the cached plugin at
`~/.codex/.tmp/plugins/plugins/codex-security`.

**Y: Route `codex-security`'s internal `threat-model` phase-skill away from
standalone `threat-modeling` requests via a `~/.codex/AGENTS.md` note,
scoped to `codex-security`'s entire scan family, not just its narrow
internal phase.**
Because: a first-draft fix anchored only on `codex-security`'s own narrow
trigger phrase; verification found the real `threat-modeling` trigger text
(recovered from a draft already sitting in this session's scratchpad) is
far broader ("MUST be invoked instead of analyzing security yourself"),
colliding with `codex-security`'s whole scan family
(`security-scan`/`security-diff-scan`/`deep-security-scan`/
`finding-discovery`), not just its internal `threat-model` sub-skill.
Evidence: `wedgcpoi3` verify pass.

**Y: Mirror `fr33d3m0n/threat-modeling` onto Codex file-for-file, rather
than use Codex's own native `security-threat-model` skill.**
Because: R3 asks for end states as close to identical as possible — the same
skill on both tools is literally identical; the native `security-threat-model`
is a *different* skill (less parity). The native option (pre-existing at
`~/.codex/vendor_imports/.../security-threat-model`, installable via
`$skill-installer`) has a lower trust surface and stays available as a
fallback if the third-party clone is ever unwanted, but parity is the
governing requirement here. Earlier revisions left this open; decided in
favor of parity after the user flagged that leaving it open contradicted
downstream validation. Evidence: `wedgcpoi3` verify pass (found both
options).

**Y: Do not install `coderabbit@openai-curated` on Codex for
`pr-review-toolkit` parity.**
Because: it curl-installs a separate binary and requires a `coderabbit
auth login` against an external account — ships diff content off for
remote analysis. Installing it would not produce real parity (a different
mechanism, not a substitute) — it would trade one asymmetry for a worse
one. Once superpowers lands on both tools, `requesting-code-review`'s own
`code-reviewer.md` template already gives both a mechanically equivalent,
self-contained baseline reviewer with zero new dependency, closing most of
the real gap. Residual asymmetry (5 specialized `pr-review-toolkit`
personas Codex still lacks) accepted, not solved — no Codex-native
equivalent exists to adopt instead. Evidence: `wedgcpoi3` (audit+verify);
direct read of `coderabbit-review/SKILL.md`.

**Y: Do not install the official Anthropic `code-review` marketplace
plugin.**
Because: it's a GitHub-PR-native bot that posts inline `gh` comments to a
live remote PR — a workflow mismatch with this user's local interactive
style — not because it duplicates anything already here (a first-draft
justification claiming the two marketplace copies were "near-identical"
and that both post inline comments was checked and found wrong: they
differ materially — 109 vs. 92 lines, different agent counts/models — and
the official copy has two genuinely novel review angles, git-blame
historical context and past-PR-comment precedent, that exist nowhere else
in this toolkit; corrected before shipping). Evidence: `wedgcpoi3`
(audit+verify), direct diff of both marketplace copies.

**Y: Evaluated `pr-review-toolkit`'s `code-reviewer` agent against
superpowers' own bundled `code-reviewer.md` template — keep both running
independently, no consolidation.**
Because: a first-draft fix proposed routing superpowers' review dispatch to
`pr-review-toolkit:code-reviewer` "instead of" its own template while
"keeping both capabilities" — verification correctly killed this as
self-contradictory: `pr-review-toolkit`'s agent never checks plan
alignment, architecture, test quality, or production-readiness, and being a
live-updated marketplace plugin, can't be edited to add those checks.
Substituting the dispatch target drops superpowers' unique dimensions at
its own "Mandatory" checkpoints rather than preserving both. Correct
resolution: no consolidation — run both, accept minor overlap on
bug-finding as a smaller cost than losing coverage. Evidence: `wedgcpoi3`
verify pass.

**Y: Port `obsidian-skills` (5 sub-skills) from Claude to Codex via flat
`cp -r`, not a fresh `git clone`.**
Because: upstream `kepano/obsidian-skills`'s own README documents this
exact Codex CLI path; all 5 SKILL.md files use only portable
`name`+`description` frontmatter. A first-draft justification for accepting
the resulting packaging asymmetry ("Claude's copy is the only side that
can have live updates via the marketplace mechanism") was checked and found
false — `claude plugin list` shows it's not marketplace-tracked at all,
just a plain git clone under the skills-directory mechanism; the real
update path (`git pull`) could be replicated on Codex too if ever wanted.
Kept the `cp -r` recommendation anyway since it matches Codex's existing
all-flat-loose-skill convention; corrected only the justification. A
second claim ("memoria-vault is itself an Obsidian vault project") was
also corrected to the narrower truth: the repo itself is a standalone
CLI/engine with Obsidian as an optional adapter; real relevance is one
level down, in `vault-template/`. Evidence: `wedgcpoi3` (audit+verify).

**Y: Add `main/CLAUDE.md` containing only `@AGENTS.md`.**
Because: Anthropic's own Claude Code docs state directly, "Claude Code
reads CLAUDE.md, not AGENTS.md... create a CLAUDE.md that imports it."
`main/CLAUDE.md` does not exist today (confirmed by direct check) — only a
container-root stub one level outside the actual git checkout exists, and
it doesn't import anything. Codex already walks AGENTS.md natively from the
git root down. Without this file, the two tools were not verified to be on
equal footing for the single most important file in the whole toolkit.
Surfaced by prior-art research into the real AGENTS.md convention
(governed since Dec 2025 by the Linux Foundation's Agentic AI Foundation;
natively read by Codex/Cursor/Jules/Devin, not by Claude Code by default).
Evidence: `code.claude.com/docs/en/memory`, `developers.openai.com/codex/
guides/agents-md`, direct filesystem check.

**Y: Fully replace `AGENTS.md`'s Skills table rather than add two rows to
it.**
Because: a full direct read (not the earlier pass's secondhand summary)
found 5 of its 7 rows reference commands that don't exist anywhere in this
environment — no `.claude/commands/` directory exists in this repo at all,
and no installed or planned plugin provides a literal `/docs-review`,
`/security-review`, `/verify`, or `/release` command. Most seriously: the
one plugin that would provide `/code-review` is the exact plugin this same
plan declines to install (above) — meaning that row references something
that will never exist once this plan executes. This is a direct violation
of `AGENTS.md`'s own stated "Zero tolerated contradictions" principle,
inside the file that states the principle. An earlier rethink pass claimed
"this plan already gets the [.agents/] boundary right, empirically" —
that claim was wrong, built on a summary rather than a direct read; this
finding is the correction. Evidence: direct read of `AGENTS.md`; `find
~/memoria-vault/main -iname commands`; `claude plugin list`;
`~/.claude/plugins/cache` search for command-providing plugins.

**Y: Revise `.agents/playbooks/verify-change.md` from "no edit" to "one
optional line appended at the end."**
Because: a full direct read confirmed the file's real portability property
is stronger than "works whether or not superpowers is installed" — it
assumes zero plugin/skill tooling at all (phrased entirely around this
repo's own `scripts/verify` gates), a property worth keeping intact rather
than weaving a reference into the numbered procedure. The fix is one
clearly-separated, optional line at the very end, not a change to the
core steps. Evidence: direct read of `.agents/playbooks/verify-change.md`.

**Y: Add one line to `.agents/playbooks/docs-review.md` pointing to
`the-elements-of-style`; leave `docs-audit.md` untouched since it already
inherits via its own cross-reference.**
Because: these two files were never examined by any earlier pass of this
plan at all — a real gap caught only during a later fact-check. Direct
read confirmed `the-elements-of-style` is in scope (its own SKILL.md names
"docs" explicitly) and complementary, not duplicative, of
`docs-review.md`'s existing terminology/citation checks (different axis:
sentence-level clarity vs. vocabulary/citations). Adding the same line to
`docs-audit.md` too would itself violate the "eliminate redundancy"
principle this whole rewrite applies everywhere else, since it already
says "Apply the Documentation review checks to every page changed by the
audit." Evidence: direct read of both files; `the-elements-of-style`
SKILL.md fetched via `gh api`.

**Y: Apply superpowers' own "reference by name, don't restate mechanics"
convention to `code-review.md` and `exec-plan.md` (playbook), rather than
writing prose descriptions of what the referenced skills already do.**
Because: verified directly against `superpowers:writing-skills`'s own
"Cross-Referencing Other Skills" section — its explicit rule ("Eliminate
redundancy: Don't repeat what's in cross-referenced skills," using
`REQUIRED SUB-SKILL`/`REQUIRED BACKGROUND` markers) is the concrete,
citable answer to how a multi-skill toolkit should avoid duplicated
sources of truth. The same file also states project-specific convention
belongs in CLAUDE.md/AGENTS.md, not in a skill — independently confirming
the Layer 2 (repo policy) / Layer 1 (generic process) boundary this whole
plan already drew empirically. Evidence: direct read of
`~/.codex/.tmp/plugins/plugins/superpowers/skills/writing-skills/SKILL.md`
(also caught, in passing: that same file wrongly claims Codex personal
skills live at `~/.agents/skills/` — confirmed empirically this path does
not exist; `~/.codex/skills/` is the real, working path used all session).

**Y: Confirm no external, named pattern combines memoria-vault's own
`source-of-truth-map` + `change-impact-map` + `test-selection` trio — state
this as a bespoke, original synthesis, not an adopted external
methodology.**
Because: dedicated research (docs-as-code, living documentation, Diátaxis,
golden-path platform engineering, Requirements Traceability Matrices,
Change Impact Analysis literature, Nx/Bazel "affected"-test tooling,
GitLab's handbook-first SSoT culture) found each individual ingredient
well-established, but no source combining all three into one named
pattern. Per the rethink discipline ("cite best practice, don't assert
it"), this should be described in this repo's own docs as an original
design, not attributed to an external framework that doesn't exist.
Evidence: dedicated research workflow (topic: `living-docs-runbook-
architecture`), full citation list retained in that workflow's journal.

**Y: Cover frontend-design on Codex by vendoring `am-will/codex-skills`'
`frontend-design` skill loose, alongside relying on Codex's native GPT-5.5
frontend generation.**
Because: the user surfaced that a "Frontend Design — Codex Plugin
Marketplace" entry exists (verified: `am-will/codex-skills`, 958★). It's the
exact "distinctive, avoid-AI-slop frontend" counterpart to Anthropic's
Claude-only `frontend-design`. Vendoring it (same loose-skill pattern as the
other cherry-picks) closes what was a "Claude-only forced asymmetry."
Caveat, accepted: `am-will/codex-skills` has **no license** — it's a
personal-use copy, not redistributable; recorded in the toolkit doc. Codex's
native frontend generation is the always-current fallback. `openai/plugins`
(official) has no direct `frontend-design` equivalent. Evidence: `gh api`
on both repos; `codex-marketplace.com/skills`.

**Y: Use a capability-parity model, not plugin-identity, for the Claude vs.
Codex end-state.**
Because: the user showed that several capabilities I'd marked "Claude-only"
(PR review via `pr-review-toolkit`; distinctive frontend via
`frontend-design`) are in fact covered on Codex by native features (Codex's
built-in review platform; native GPT-5.5 frontend generation). A capability
is "covered on a tool" if a plugin OR a native feature provides it. Under
this model the only genuine residual asymmetry is passive always-on security
scanning (Claude's `security-guidance` hooks; Codex has no passive
equivalent, only active `codex-security`). Two invocation-surface
differences remain (interface-design's slash-commands; frontend-design being
a plugin on Claude vs. a skill+native on Codex) — not capability gaps.
Evidence: user-provided sources on Codex native review
(openai.com/index/introducing-upgrades-to-codex; developertoolkit.ai) and
native frontend (developers.openai.com/codex/use-cases/frontend-designs).

**Y: The final deliverable is a whole-stack toolkit document at
`.agents/toolkit.md` (exec-plan step 18).**
Because: the user asked for one document covering the entire stack — every
plugin, skill, playbook, template, system map — plus its use and best
practices, stored inside the repo folder. `.agents/toolkit.md` on `main` is
the recommended home: durable, PR-reviewed, and the repo's agent-guidance
directory, so `AGENTS.md` stays the authority and `toolkit.md` is the
"what's available and how to use it" map. It includes the pr-review-toolkit
six-dimension ↔ Codex-native-review mapping, the parity ledger, and the
sourcing caveats (including the `am-will` licensing note). Alternative
considered: `scratch/workflow-audit/` alongside the plan — rejected as less
durable/discoverable for a reference meant to outlive this initiative.

**Y: Resolve the `main/CLAUDE.md` bridge vs. the global "no local CLAUDE.md
files" rule by amending the global rule with a loader carve-out (not by
dropping the bridge).**
Because: `~/.claude/CLAUDE.md` rule 1 forbids local CLAUDE.md files to prevent
instruction fragmentation. The `main/CLAUDE.md` = `@AGENTS.md` bridge carries
zero instructions — it only makes Claude Code read the repo's `AGENTS.md`
(which the same rule already endorses: "checks its own folder for context"),
since Claude Code doesn't read `AGENTS.md` natively (Codex does). So the
bridge serves the rule's intent while tripping its letter. Resolution: a
one-line carve-out to rule 1 permitting a repo-root CLAUDE.md whose entire
content is `@AGENTS.md`. **Decided by the user (2026-07-07): keep the loader
bridge, linking to AGENTS.md only.** The alternative (drop the bridge, accept
a Claude-side Layer-3 gap) was considered and rejected. Surfaced by external
review.

**Y: Pin third-party clone installs to reviewed commit SHAs; take a backup
before any destructive step; make every clone/copy step remove-then-install.**
Because: external review flagged three execution-safety gaps — (1) the plan
cloned live default branches, so a later run could install different code
than was reviewed → pin `fr33d3m0n/threat-modeling` `a0962b73`,
`Dammyjay93/interface-design` `2f9be320`, `obra/the-elements-of-style`
`6099c505`, `wshobson/agents` `5cc2549a`, `am-will/codex-skills` `e3437156`
(reviewed 2026-07-07); Claude marketplace-plugin installs can't be pinned via
the mechanism, so review-after-install is noted instead; (2) idempotence was
falsely claimed (git clone fails into an existing dir; cp merges stale
content) → every clone/copy step now `rm -rf`s its target first; (3) no
backup before `rm -rf` → step 1 writes a full backup tarball. Also corrected:
`rethink` is installed at 1.0.1 on *both* tools (not 1.1.0 on Claude), with
the Claude marketplace clone dirty + 1 commit ahead — step 13 now reconciles
that before editing. `gh auth` preflight added for the PR steps. Evidence:
`gh api` SHA fetches; `claude plugin list`; `git -C ...rethink status`.

**Y: `using-superpowers` is the SessionStart bootstrap/dispatcher, not a
workflow skill you invoke — so the toolkit has 13 usable skills, 14 skill
files on disk.**
Because: the plugin ships 14 SKILL.md files, but `using-superpowers`'s entire
job is to fire at SessionStart and remind the agent to invoke the applicable
*other* skills — it isn't itself invoked for a task. So `claude plugin
details` counts 14; the skill reminder lists 13 invocable `superpowers:`
skills; validation checks 13. Wording aligned across step 1, validation, and
this ledger. (Answers the reviewer's open question.)

**Y: Corrected two invalid CLI commands and one wrong install verb, verified
against the installed CLIs.**
Because: external review caught that (1) `codex plugin` has no `update`
subcommand and its marketplace verb is `upgrade`, not `update` — step 13's
Codex refresh is now `codex plugin marketplace upgrade rethink && codex plugin
remove rethink@rethink && codex plugin add rethink@rethink` (Claude's `plugin
update`/`marketplace update` are valid and unchanged); (2) `frontend-design`
is not installed, and `claude plugin enable` only enables an
already-installed disabled plugin — step 7 now `claude plugin install
frontend-design@claude-code-plugins` (it's in both official marketplaces).
Also: step 13's rethink release is now a concrete preserve→fresh-checkout→
verify→commit→tag→push→update-both procedure (was under-specified), and step
1's backup fails closed (`|| exit 1`) instead of printing false success.
Evidence: `codex plugin --help`, `codex plugin marketplace --help`, `claude
plugin --help`, `claude plugin enable --help`, `claude plugin list`.
