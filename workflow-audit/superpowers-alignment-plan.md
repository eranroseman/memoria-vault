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

6. Delete `.agents/` entirely, `scripts/checks/` doctors,
   `ruleset-contract.yaml`, cspell/markdownlint configs, `project-words.txt`.
7. Rewrite `AGENTS.md` as the facts file (~15 lines): what Memoria is,
   `scripts/verify` as the correctness command, test only against `sandbox/`,
   Obsidian seeded-not-required. No process content. `CLAUDE.md` stays the
   `@AGENTS.md` loader.
8. Slim `scripts/verify` to the single gate. Gitignore `sandbox/` and
   `.worktrees/`. Trim CONTRIBUTING.md references to retired machinery.
   `docs/` and `design-history/` content untouched (dated history cannot
   drift; only its enforcement machinery leaves).

Verify: `scripts/verify` green locally + CI;
`rg -l 'agents_doctor|pr_policy|ruleset-contract'` → nothing.

## Phase 3 — Container collapse (local, after Phase 2 merges)

9. Delete the `scratch` branch + worktree; remove remaining worktrees; prune.
10. Collapse to a single ordinary clone at `~/memoria-vault`: clone fresh to a
    temp path, verify, swap in. Remove the decoy empty `.git`, the
    `AGENTS.md`/`CLAUDE.md` symlinks, `.kilo/` (unowned firebase MCP;
    recreate when actually test-driving), container `.codex`/`.venv`/`.cache`
    residue.
11. Move `papers/` out of the repo tree (personal research, not product);
    `sandbox/` lives inside the clone, gitignored.

Verify: `git -C ~/memoria-vault status` clean on `main`; `scripts/verify`
passes from the new root.

## Phase 4 — Harness teardown (global layer)

12. **Pin superpowers to a tagged release** instead of the `superpowers-dev`
    channel: reinstall from the stable marketplace/tag if obra publishes one,
    otherwise pin by commit SHA; record version + SHA here on execution.
    Upgrades become deliberate acts, aligned with filing issues upstream.
13. `~/.claude/settings.json`: disable pr-review-toolkit and interface-design.
    Keep **superpowers**, **security-guidance**, and **frontend-design**
    (invoke-scoped; the only design-craft source — superpowers has none;
    interface-design earns back at real product-UI work). Delete the dead
    `plansDirectory` line.
14. **Ponytail and rethink become audit-only** (standing modes retired,
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
15. `~/.claude/skills/`: delete `api-design-principles` and `threat-modeling`
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
16. `~/.claude/CLAUDE.md`: delete the precedence table and the six behavioral
    sections — superpowers hosts on AGENTS.md. Keep at most a simplified
    write-perimeter hook (outside-project *ask* only; drop the
    CLAUDE.md-police logic).
17. `~/.codex/AGENTS.md`: delete the precedence copy; prune mirrored
    `~/.codex/skills` to the kept set (audit tools, caveman, grilling,
    obsidian-skills); `config.toml`: remove stale `writable_roots`
    (`~/Memoria-test`, `~/mv`), delete the `~/mv` skeleton. Codex otherwise
    runs on repo AGENTS.md alone.
18. Delete the ponytail 4.7.0 cache, and — after a skim (**second
    irreversible eyeball**) — the ten orphaned plans in `~/.claude/plans`.

Verify: fresh session in the collapsed repo; only injected mode is
superpowers' using-superpowers.

## Phase 5 — Acceptance test + upstream debts

19. Run one real feature end-to-end through the spine: brainstorm → spec in
    `docs/superpowers/specs/` → plan → SDD → PR → `verify` → squash-merge →
    finish flow (answer "PR"). This exercises every adopted convention.
20. File upstream superpowers issues instead of patching locally: (a) SDD
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
  (step 14) but cannot return as standing modes while brainstorming's gate
  is law (structural conflict); ponytail's `/ponytail-review` additionally
  waits on the upstream sticky-mode fix.
- interface-design — earns back at real product-UI work (Obsidian plugin
  interface); frontend-design covers design craft until then.
