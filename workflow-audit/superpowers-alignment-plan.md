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

4. Settings → Rulesets → "main": required checks = `verify` only; keep
   require-PR. (UI first — avoids the policy-code deadlock.)
5. One PR: replace all workflows with `verify.yml` (`pull_request` +
   `push: main`, concurrency group) running `scripts/verify`; fold shellcheck
   into that script. Delete `pr-review-gate.yml` and `pr_policy.py` + tests.
   **Keep release-please** (ships the product; not governance).

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
     stock markdown link checker, not a bespoke doctor).
   - **Keep the product gates as tests** (they check what ships, not how
     work happens): `plugin_provenance_doctor.py` (seed supply-chain
     integrity), `removed_surface_gate.py` (retired-surface regression),
     `schema_doc_drift.py` (reference docs vs live schemas — the one
     justified mirror, so the one justified drift check),
     `checked_terminology_gate.py` (product-honesty wording gate).
     Rehome under `tests/` or as `scripts/verify` steps; drop the "doctor"
     naming.
7. Rewrite `AGENTS.md` as the facts file (~15 lines): what Memoria is,
   `scripts/verify` as the correctness command, test only against `sandbox/`,
   Obsidian seeded-not-required. No process content. `CLAUDE.md` stays the
   `@AGENTS.md` loader.
8. Slim `scripts/verify` to the single gate: pytest + ruff + shellcheck +
   the four kept product gates from step 6 + cspell/markdownlint scoped to
   `docs/` minus `docs/superpowers/`. Gitignore `sandbox/` and
   `.worktrees/`. Trim CONTRIBUTING.md references to retired machinery.
   `docs/` and `design-history/` content untouched (dated history cannot
   drift; only its enforcement machinery leaves).
9. **Migrate the scratch branch's keepers into the repo** (same PR):
   copy via `git show scratch:<path>` — accepted-and-implemented decisions
   from `releases/<version>/decisions.md` fold into `design-history/` (one
   final close-out); open questions become GitHub issues; live design docs
   (e.g. `releases/0.1.0-beta.1/0.1.0-beta.1-design.md`) land as dated
   records in `docs/superpowers/specs/`; `workflow-audit/` (this plan and
   its audit) lands in `docs/superpowers/plans/`. Exclude
   `docs/superpowers/` from the GitHub Pages build (one config line) —
   working records are tracked, not published. `design-history/` itself
   stays frozen at the repo root as the pre-alignment museum — do not move
   it under `docs/superpowers/`; new design history accrues as dated specs.

Verify: `scripts/verify` green locally + CI;
`rg -l 'agents_doctor|pr_policy|ruleset-contract'` → nothing.

## Phase 3 — Container collapse (local, after Phase 2 merges)

10. Delete the `scratch` branch + worktree; remove remaining worktrees; prune.
11. Collapse to a single ordinary clone at `~/memoria-vault`: clone fresh to a
    temp path, verify, swap in. Remove the decoy empty `.git`, the
    `AGENTS.md`/`CLAUDE.md` symlinks, and container `.codex`/`.venv`/`.cache`
    residue. `.kilo/` survives in minimal form (see step 18).
12. Relocate the non-repo content: `papers/` → `~/papers` (personal research
    corpus; its eventual home is a Memoria workspace once the product can
    dogfood it); `scratch/.notes/` → `.notes/` inside the clone, gitignored
    (add `.notes/` to `.gitignore` in step 8); `sandbox/` stays inside the
    clone, gitignored (tests default to a repo-relative path; Codex
    workspace-write covers it with no extra roots).

Verify: `git -C ~/memoria-vault status` clean on `main`; `scripts/verify`
passes from the new root.

## Phase 4 — Harness teardown (global layer)

13. **Pin superpowers to a tagged release** instead of the `superpowers-dev`
    channel: reinstall from the stable marketplace/tag if obra publishes one,
    otherwise pin by commit SHA; record version + SHA here on execution.
    Upgrades become deliberate acts, aligned with filing issues upstream.
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

Verify: fresh session in the collapsed repo; only injected mode is
superpowers' using-superpowers.

## Phase 5 — Acceptance test + upstream debts

20. Run one real feature end-to-end through the spine: brainstorm → spec in
    `docs/superpowers/specs/` → plan → SDD → PR → `verify` → squash-merge →
    finish flow (answer "PR"). This exercises every adopted convention.
21. File upstream superpowers issues instead of patching locally: (a) SDD
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
