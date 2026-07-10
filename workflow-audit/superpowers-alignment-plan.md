# Superpowers full-alignment plan — 2026-07-09

Teardown-and-rebuild sequence from the current harness to full alignment with
`obra/superpowers`. Rationale and evidence: `harness-goal-audit.md` (same
folder). Supersedes `exec-plan-adopt-superpowers.md` (Jul 6–7, recoverable at
scratch commit `06c044e9`), which installed the toolkit this plan simplifies.

**Target end state — four owners, no mirrors:** superpowers owns *how work
happens*; the GitHub ruleset (require-PR + one `verify` check) owns *what gets
in*; `scripts/verify` (pytest + ruff + shellcheck) owns *what correct means*;
a ~15-line facts-only AGENTS.md owns *what's true here*.

**Ordering is load-bearing:** today's required checks would block the PR that
removes them → gate first. Worktree law governs until repealed → repo before
container collapse. Sessions need the harness during migration → harness last.

---

## Phase 0 — Park in-flight state (~30 min)

1. Land or close the `fix/obsidian-plugin-sandbox-load` worktree/PR.
2. Sweep the `scratch` branch for durable content: open decision entries in
   `releases/<version>/decisions.md` → dated records in the repo or closed
   into issues. Everything else dies with the branch. **Irreversible — eyeball
   before deleting.**
3. Tag `main` as `pre-superpowers-alignment` and push the tag.

Verify: `git worktree list` shows only main + scratch; tag on origin.

## Phase 1 — GitHub gate: eight checks → one

4. Settings → Rulesets → "main": required checks = `verify` + `gitleaks`;
   keep require-PR. (UI first — avoids the policy-code deadlock.)
5. One PR: replace the check workflows with `verify.yml` (`pull_request` +
   `push: main`, concurrency group) running `scripts/verify`, which absorbs
   python-selftest, lint (kept gates), lint-installers (shellcheck **and**
   PSScriptAnalyzer — pwsh in CI, graceful skip locally), scoped
   cspell/markdownlint, and lint-config's product half (yamllint + JSON
   syntax over runtime config; actionlint drops — one workflow left to
   lint). **Keep:** `gitleaks.yml` (secrets are the one failure class where
   post-merge detection is too late — it backstops `--no-verify` commits
   and web edits). **Delete `release-please.yml` + its config/manifest** —
   zero releases have ever been published and nothing consumes them (the
   installer clones `main`, no PyPI, no version-pinned readers); it is
   machinery ahead of need whose standing cost is the conventional-PR-title
   constraint. Earn-back: the first real distribution moment — installer
   pinning a tag, a package publish, or users needing per-version
   changelogs. **Also delete:**
   `pr-review-gate.yml` + `pr_policy.py` + tests, `ruleset-audit.yml`
   (dies with ruleset-doctor), `dependabot-auto-merge.yml` (keep
   `dependabot.yml` itself; with one workflow, bump PRs are rare — a manual
   click replaces a `pull_request_target` write-token workflow; earn-back:
   bump volume), and the absorbed standalone check workflows.

Verify: that PR merges under the new single check.

## Phase 2 — Repo teardown (one PR)

6. Delete `.agents/` entirely and `ruleset-contract.yaml` (its only reader
   is the retired ruleset-doctor; the one fact it holds — main requires
   PR + `verify` — becomes a line in the new AGENTS.md). **Keep**
   cspell/markdownlint configs and `project-words.txt`, rescoped: they run
   inside `scripts/verify`, limited to `docs/` **excluding
   `docs/superpowers/`** — published prose stays polished, working
   artifacts stay ungated; their standalone CI checks retire. In
   `scripts/checks/`, split by subject matter, not wholesale:
   - **Delete the governance doctors** (their subject retires with the
     apparatus): `agents_doctor.py`, `ruleset_doctor.py`,
     `status_doctor.py`, `github_doctor.py`, and `docs_doctor.py`
     (convention linting; earn-back for link rot on published Pages is a
     stock markdown link checker, not a bespoke doctor). **Before deleting
     docs_doctor, extract its workspace-seed validation slice** (seed link
     text / seed mirrors) into a product test — the seed is shipped
     product, and `plugin_provenance` guards its file roster but not its
     content links.
   - **Keep the product gates as tests** (they check what ships, not how
     work happens): `plugin_provenance_doctor.py` (seed supply-chain
     integrity), `removed_surface_gate.py` (retired-surface regression),
     `schema_doc_drift.py` (reference docs vs live schemas — the one
     justified mirror, so the one justified drift check),
     `checked_terminology_gate.py` (product-honesty wording gate).
     Rehome under `tests/` or as `scripts/verify` steps; drop the "doctor"
     naming.
7. Rewrite `AGENTS.md` as the facts file (~20 lines). What Memoria is,
   distilled from the canonical product statement
   (`product-statement.md`, same folder): *an opinionated, phase-gated,
   personal knowledge-production tool — a durable research vault for one
   researcher who owns all judgment; sources enter the catalog, become
   connected claims in Knowledge Bundles (a Toulmin argument graph parallel
   to the catalog graph), and drive to output in Projects; built on
   Karpathy's LLM-Wiki and Luhmann's Zettelkasten, expanded with agentic
   capabilities; it should feel like a co-PI, not a knowledge base.* Plus:
   `scripts/verify` as the correctness command, test only against `sandbox/`
   (which has its own nested `.git`), Obsidian seeded-not-required. Plus the
   facts that are load-bearing but stated nowhere else after teardown:
   - **Squash-merge stays** (decided) — superpowers delegates merge method
     to the repo (its finish flow only specifies plain `git merge` for the
     local option); squash keeps `main` linear with one-commit revert per
     feature while the spine's granular TDD/SDD commits stay visible on the
     PR. With release-please deleted (step 5), PR titles and commits carry
     **no required format** — descriptive is enough; Conventional Commits
     earns back together with release tooling.
   - **Concurrent sessions each work in their own `.worktrees/` checkout** —
     the git index is shared per checkout, so two simultaneous sessions
     (Claude planning + Codex executing) in the clone root can capture each
     other's staged files. One line of fact, not a process override.
   - The two justified parity asymmetries (step 18), with the Codex
     security line naming its own trigger ("installer or runtime-policy
     changes") since the pr-policy sensitive-path list is deleted.
   - The layer-disagreement heuristic (from `insights.md`): **when layers
     disagree, trust order is schema → tests → code → docs.**
   Plus five lines that are the conscious exception to "facts only" — each
   preserves a function with no other home in the end state:
   - Code shape (4 lines): smallest change that solves the problem; no
     speculative abstractions or unrequested flexibility; match existing
     style; tests attach to agreed interfaces/seams, not incidental
     internals. (With ponytail audit-only and the global CLAUDE.md gone,
     this is the only standing counterweight to over-building — and the
     seam line patches the one gap superpowers' TDD has: it says test
     first, never where. Origin: preserved from the retired local tdd
     skill, kept on merit, not provenance.)
   - Options are presented with pros/cons and a recommendation, never a
     bare list.
   - The admission rule: an addition must name the expensive, occurring
     failure it prevents; prefer deletion > mechanism > rule > checker.
   No other process content. `CLAUDE.md` stays the `@AGENTS.md` loader.
   **Decided:** (a) retire the "Release <version>" parent-issue/readiness
   ceremony — the milestone alone is the readiness view for one person
   (with release-please also deleted, "releasing" is currently just closing
   the milestone; tagging returns with release tooling when distribution
   needs it); earn-back: a release that slips from invisible scope. (b) drop the Memoria Issue Tracker Project's custom
   Status/Readiness fields — superpowers tracks per-feature state inside
   the plan document (task checkboxes), and issues + milestone own the
   cross-feature backlog; the fields were a third state layer with no
   enforcing mechanism. The board itself is optional glass over the same
   issues — keep or drop per taste.
8. Rewrite `scripts/verify` as a flat single gate — run the command list,
   exit nonzero on failure, and still **print skipped checks** (e.g. no
   pwsh) rather than passing silently: pytest (full suite; the `-m static`
   tier markers retire with the test-selection policy) + compileall +
   `bash -n` on the installer + ruff + shellcheck +
   PSScriptAnalyzer (when pwsh) + yamllint/JSON syntax over runtime config +
   the four kept product gates from step 6 + cspell/markdownlint scoped to
   `docs/` minus `docs/superpowers/`. Mechanism for the lint tools: keep
   ruff/cspell/markdownlint in `.pre-commit-config.yaml` as
   **manual-stage hooks** (never fire on commit; `verify` invokes them via
   `pre-commit run --hook-stage manual`) — version pinning, env caching,
   dependabot's pre-commit ecosystem, and the stub `package.json` host all
   survive unchanged. Delete its evidence-bundle machinery
   (hashes/timestamps served the retired RC-readiness process; nothing
   reads it) and the `l0`/`pr`/`check` tiers (`check`'s only consumer was
   the pre-commit pytest-collect hook, which goes). Same PR, the test
   cascade: **delete** the orphaned doctor tests (`test_docs_doctor`,
   `test_agents_doctor`, `test_github_doctor`, `test_ruleset_doctor`,
   `test_status_doctor`; `test_pr_policy` per step 5); **update**
   `test_verify_script.py` (pins the new roster — the one legitimate
   roster mirror, as a test), `test_cspell_scope.py` (one consumer now),
   `test_node_tooling.py` (required-check coupling). **Do not touch the
   false friends:** `test_precommit_schema.py` tests Memoria's own vault
   pre-commit hook (product), and `scripts/sandbox/*` +
   `test_test_env_harness`/`test_refresh_test_vault` are test-environment
   infrastructure. Update `scripts/dev/setup.sh` for the slimmed
   pre-commit config. Slim `.pre-commit-config.yaml` to the
   two hooks CI cannot replace: `gitleaks` (block secrets *before* they
   enter history — post-push detection on a public repo is rotation, not
   prevention) and `no-commit-to-branch main`; every other hook duplicates
   `verify`'s roster and goes. Delete `.github/CODEOWNERS` (solo repo — every
   rule assigns the owner `*` already assigns; earn-back: a second
   maintainer). Sweep `.github/` prose for retired references (dependabot.yml
   header comment, issue/PR templates), plus root-file rot: CHANGELOG.md's
   header cites the deleted release-please workflow (the changelog itself
   stays — hand-curated dated record); the pre-commit comment references a
   nonexistent `.markdownlintignore`. (A prior draft flagged CITATION.cff's
   "phase-gated" as stale — retracted: it is the canonical product term per
   `product-statement.md`; CITATION.cff is correct as-is.) Update
   `.vscode/settings.json`
   excludes for the Phase 3 layout: drop `_papers/**`, rename `_notes/**` →
   `.notes/**`, and add `.worktrees/**` + `sandbox/**` to search and watcher
   excludes (otherwise searches double-hit sibling worktrees and the watcher
   churns on test-vault runs). Gitignore `sandbox/` and
   `.worktrees/`. Trim CONTRIBUTING.md references to retired machinery.
   `docs/` and `design-history/` content untouched (dated history cannot
   drift; only its enforcement machinery leaves).
9. **Migrate the scratch branch's keepers into the repo** (same PR):
   copy via `git show scratch:<path>` — accepted-and-implemented decisions
   from `releases/<version>/decisions.md` fold into `design-history/` (one
   final close-out); open questions become GitHub issues; live design docs
   (e.g. `releases/0.1.0-beta.1/0.1.0-beta.1-design.md`) land as dated
   records in `docs/superpowers/specs/`; `workflow-audit/` (this plan and
   its audit) lands in `docs/superpowers/plans/` — except
   `product-statement.md`, which is product doctrine, not a working
   record: it becomes a `docs/` explanation page (published). Exclude
   `docs/superpowers/` from the GitHub Pages build (one config line) —
   working records are tracked, not published. `design-history/` itself
   stays frozen at the repo root as the pre-alignment museum — do not move
   it under `docs/superpowers/`; new design history accrues as dated specs.

Verify: `scripts/verify` green locally + CI;
`rg -l 'agents_doctor|pr_policy|ruleset-contract'` → nothing.

## Phase 3 — Container collapse (local, after Phase 2 merges)

10. **Tag the scratch tip first** (`scratch-final` — scratch is an orphan
    branch, so deletion without a tag is irreversible), then delete the
    `scratch` branch + worktree; remove remaining worktrees; prune.
11. Collapse to a single ordinary clone at `~/memoria-vault`: clone fresh to a
    temp path, verify, swap in. Remove the decoy empty `.git`, the
    `AGENTS.md`/`CLAUDE.md` symlinks, and container `.codex`/`.venv`/`.cache`
    residue. `.kilo/` survives in minimal form (see step 18).
12. Relocate the non-repo content: `papers/` → `~/papers` (personal research
    corpus; its eventual home is a Memoria workspace once the product can
    dogfood it); `scratch/.notes/` → `.notes/` inside the clone, gitignored
    (add `.notes/` to `.gitignore` in step 8); `sandbox/` stays inside the
    clone, gitignored — noting it is an installed Memoria vault with **its
    own nested `.git`** (vault versioning is product behavior). Gitignored
    nesting is safe: the outer repo skips it, and the inner `.git`
    self-isolates git commands run inside it. Record one line in the facts
    AGENTS.md: "`sandbox/` is a disposable installed vault with its own
    `.git`; `git clean -fdx` destroys it — it must always be
    reconstructible." Tests keep the repo-relative default; Codex
    workspace-write covers it with no extra roots.

Verify: `git -C ~/memoria-vault status` clean on `main`; `scripts/verify`
passes from the new root.

## Phase 4 — Harness teardown (global layer)

13. **Pinning policy — pin what stands or enforces; track what you're
    waiting on or own.** Pin superpowers (the spine; drop the
    `superpowers-dev` channel for a tagged release, else a commit SHA),
    security-guidance (always-on enforcement — silent upstream change
    alters security behavior without a decision), and interface-design
    while it's active (step 18's cross-harness "same version" is only
    stable if pinned). Leave ponytail deliberately tracking (waiting on
    the upstream sticky-mode fix); rethink needs no pin (own upstream —
    every update is already a decision). Disabled plugins (frontend-design,
    pr-review-toolkit) need no pin; any that earns back re-enters this
    policy on re-enable (frontend-design: pinned while active, same version
    across harnesses, like interface-design). Record versions + SHAs here
    on execution. Mechanics to verify at execution: a pin must actually stop
    marketplace auto-refresh (observed live — ponytail auto-updated the
    night before this audit), via version-pinned install path or per-
    marketplace auto-update off.
14. `~/.claude/settings.json`: disable pr-review-toolkit and frontend-design
    (earn-back: marketing/landing work, which has no near-term surface).
    Keep **superpowers**, **security-guidance**, and **interface-design** —
    the Obsidian plugin's interface is the next task, so the product-UI
    design skill stays; superpowers itself has no design-craft content.
    Keeping exactly one design skill also avoids resurrecting the
    interface-vs-frontend routing rule. Known interface-design caveats to
    manage in use: treat `.interface-design/system.md` as the *authored
    design-decision source that code follows* (one direction of authority —
    then it is a record, not a mirror); ignore its bundled `reference/`
    examples (they contradict the skill's own typography rules). Delete the
    dead `plansDirectory` line.
15. **Ponytail and rethink become audit-only** (standing modes retired,
    one-shot audit commands kept):
    - ponytail: keep installed; set the default mode off
      (`~/.config/ponytail/config.json` or `PONYTAIL_DEFAULT_MODE` — verify
      the exact knob at execution); delete `~/.claude/.ponytail-active`.
      `/ponytail-audit` stays available. **Caveat:** until the upstream
      sticky-mode bug is fixed, `/ponytail-review` re-arms subagent injection
      for the rest of the session — run ponytail reviews in throwaway
      sessions, or check/reset the flag file afterward.
    - rethink: remove the SessionStart injection upstream (own repo — gate or
      drop the hook, ship as next release); `/rethink` and `/rethink-audit`
      stay as explicit lenses.
16. `~/.claude/skills/`: delete `api-design-principles` and `threat-modeling`
    (earn-back: reinstall on demonstrated need). Keep `caveman`, `grilling`.
    Keep **`improve` as an audit-only tool**: retarget its hard-coded output
    path from repo-root `plans/` to `docs/superpowers/plans/` (local one-line
    edit; the spine has exactly one plan home). Keep **`obsidian-skills`** —
    but fix the installation so it actually loads: the current clone nests
    `skills/*/SKILL.md` one level too deep and is never discovered; flatten
    to `~/.claude/skills/<name>/SKILL.md`, and dedupe against the
    environment-provided `obsidian:*` plugin skills so both don't trigger
    (the properly-nested copies also serve Codex, which has no environment
    plugin).
17. `~/.claude/CLAUDE.md`: delete the precedence table and the six behavioral
    sections — superpowers hosts on AGENTS.md. Delete the PreToolUse
    write-perimeter hook entirely: half enforces the retired
    no-local-CLAUDE.md policy; the other half failed the empirical test
    (silently allowed main/scratch/other-worktree writes, denied a legal
    loader edit), never covered shell writes, and duplicates native
    permission prompts + bash sandboxing (Claude) and sandbox
    `writable_roots` (Codex). Earn-back: a real incident of a harmful
    durable write outside the repo that native permissions missed.
18. **Cross-harness parity — Codex and Kilo (parity by default; asymmetry
    only with justification):**
    - Kilo: reads repo AGENTS.md natively — the facts file covers it for
      free. Symlink the canonical skills dir if Kilo supports one (verify
      at execution). Superpowers ships no Kilo packaging today —
      **justified asymmetry:** Kilo runs plan-driven execution only, so the
      spine's process reaches it through the plan artifact itself (plans
      written so execution degrades to transcription). Keep `.kilo/` as a
      minimal config; drop the firebase MCP (no justified consumer) and its
      node_modules scaffolding.
    - `~/.codex/AGENTS.md`: delete the precedence copy (nothing left to
      arbitrate).
    - Skills: replace the hand-copied `~/.codex/skills/*` with symlinks to
      the canonical `~/.claude/skills/*` — one source, zero drift, full
      parity (verify Codex resolves symlinks at execution; fallback: a
      one-line rsync in a shell alias, never hand-copies).
    - Plugins: install the same pinned superpowers release on Codex (it
      ships `.codex-plugin` packaging) and the same interface-design version
      (ships `openai.yaml`); delete the stale Codex copies (old maximalist
      frontend-design, hand-neutralized improve).
    - `config.toml`: remove stale `writable_roots` (`~/Memoria-test`,
      `~/mv`), delete the `~/mv` skeleton.
    - **Justified asymmetries (the only tolerated ones), recorded as two
      lines in the new AGENTS.md:** (a) always-on security review — Claude
      via security-guidance hooks, Codex has no passive-hook equivalent, so
      Codex runs explicit `codex-security` scans on sensitive diffs;
      (b) write perimeter — Claude via PreToolUse hook, Codex via sandbox
      `writable_roots`. Same outcome, platform-appropriate mechanism.
      Anything else non-parallel is a defect.
19. Delete the ponytail 4.7.0 cache, and — after a skim (**second
    irreversible eyeball**) — the ten orphaned plans in `~/.claude/plans`.
20. **Remove the account-level claude.ai connector pile from coding
    sessions** (Clinical Trials, PubMed, Canva, Gmail, Calendar, Drive,
    Notion, Figma, Hugging Face, Microsoft Learn, plus the pending-auth
    set) — their tool rosters and instructions tax every session's context.
    Two paths: full disconnect in claude.ai → Settings → Connectors
    (removes them from claude.ai chats too — fine only for connectors
    unused everywhere), or exclude account connectors from Claude Code
    sessions via its MCP settings, keeping them for chat (exact setting:
    verify at execution). GitKraken is a local VSCode MCP, not part of
    this — disposition separately if wanted.

Verify: fresh session in the collapsed repo; only injected mode is
superpowers' using-superpowers.

## Phase 5 — Acceptance test + upstream debts

21. Run one real feature end-to-end through the spine: brainstorm → spec in
    `docs/superpowers/specs/` → plan → SDD → PR → `verify` → squash-merge →
    finish flow (answer "PR"). This exercises every adopted convention.
22. File upstream superpowers issues instead of patching locally: (a) SDD
    task-reviewer "do not re-run the suite" vs verification-before-completion;
    (b) orphaned spec/plan reviewer prompt templates.

---

## Earn-back triggers (what stays out, and what would justify re-adding it)

- Doctors / drift checks — a doc must restate machine-readable data for real
  outside readers; first response to drift is deleting the duplicate.
- pr-policy tiers / auto-approve — untrusted contributors actually opening PRs.
- Source-of-truth / change-impact maps — codebase exceeds one-session grep.
- Scratch branch / ExecPlan playbook / Project fields — a real multi-session
  handoff fails for lack of them.
- Second standing behavioral plugin — never two at once; everything beyond
  superpowers is invoke-only. Ponytail and rethink stay as audit lenses
  (step 15) but cannot return as standing modes while brainstorming's gate
  is law (structural conflict); ponytail's `/ponytail-review` additionally
  waits on the upstream sticky-mode fix.
- frontend-design — earns back at marketing/landing/brand work;
  interface-design (kept — the Obsidian plugin UI is the next task) covers
  product-UI craft.
- Hand-copied cross-harness mirrors — never; parity is by symlink or same
  pinned install, and any asymmetry must carry a written justification.
