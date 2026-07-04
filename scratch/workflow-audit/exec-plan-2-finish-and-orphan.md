# ExecPlan 2 — Finish the workflow-audit recommendations, then orphan the scratch branch

Waves A and B of the workflow audit already shipped to `main` as PR #1256 and
#1257 (durably recorded in those merged PRs); their originating plan is retired.
This plan is the single, standalone source for the remaining work: it finishes
the paused Wave C on a re-grounded footing, then removes the structural cause of
the stale-analysis problem. **Beta.1 is explicitly out of scope** — the beta.1
design doc is left untouched.

## 0. Metadata

- **Task:** Finish the workflow-audit recommendations (the paused Wave C),
  verified against `main` rather than the stale scratch tree; then make the
  `scratch` branch a standalone orphan (nothing but `scratch/`) and add the
  "analysis runs from main" rule so no future audit is contaminated.
- **Worktree / branch:** `~/mv/wf-audit-c` · `fix/workflow-audit-c` off
  `origin/main` for the repo edits; this plan lives on the `scratch` branch
  under `scratch/workflow-audit/`.
- **Related:** workflow-audit Waves A/B already merged (#1256, #1257;
  originating plan retired); live `scratch` ruleset id **18508798**
  (`deletion` + `non_fast_forward`, created by Wave B). Background: AGENTS.md
  scratch-branch flow.
- **Related issues / milestone:** — (open per wave; milestone 0.1.0-alpha.16).
- **Started:** 2026-07-04 · **Last updated:** 2026-07-04

## 1. Purpose / big picture

The original workflow audit was run from the **scratch worktree** — a tree 226
commits behind `main` and 180 ahead on unmerged cleanup, differing from `main`
in 15 of the 16 files it examined. Plan 1's *implementation* branched off
`origin/main` and re-verified every finding at HEAD, so no wrong fix shipped
(Wave A's log shows it correctly dropped already-fixed targets). But Wave C was
paused before executing, and the structural cause — a scratch branch carrying a
full, divergent repo tree that agents can analyze — is still live.

When this plan is done: Wave C's four live backstops (secret scanning, a CI
backstop for `--doc-refs`, yamllint consolidation, a scheduled live-link audit,
and failure notification) are in place, each re-verified against `main`; the
`scratch` branch contains **nothing but `scratch/`**; and a
repo audit can no longer be run from the scratch worktree because there is no
repo tree there to read — the stale-analysis failure mode becomes structurally
impossible, not merely discouraged.

## 2. Context and orientation

**Re-grounding result (2026-07-04, against `origin/main` f26596b8, which
already includes the merged Waves A/B).** Four Wave C findings still held and
shipped in #1258. The `render_profile_configs` test finding was struck after
checking current `main`: installed-profile rendering is intentionally retired,
`scripts/render_profile_configs.py` is absent, and `tests/test_profiles.py` pins
that absence.

| Wave C item | State on `main` |
|---|---|
| Secret scanner | none (no gitleaks/detect-secrets/trufflehog) — real |
| `docs_doctor --doc-refs` in `test.sh l0` | absent — real |
| yamllint in `test.sh l0` | absent — real |
| `lint-config.yml` yamllint/json-validate jobs | still present (the dead `src/.obsidian` excludes were cleaned, but the duplication vs `test.sh l0` stands) — real |
| `check_live_docs_links.py` invoked anywhere | no; `ruleset-audit.yml` has no failure notification — real |
| `tests/test_render_profile_configs.py` | missing by design — struck |

**The live scratch ruleset is the sharp hazard for the orphan step.** Wave B
created ruleset **18508179** with `non_fast_forward`; Wave 2 recreated it as
**18508798** after the orphan reset. Orphaning is a
force-push, which that rule **blocks** — so the orphan step must delete the
ruleset, do the reset, then recreate it. `ruleset-contract.yaml` still declares
`scratch`, so `ruleset_doctor --live` will flag the gap during the window; keep
the window tight.

**The orphan-branch decision (user-chosen, this session):** `scratch` is a
standalone folder with its own branch and its own rule — it includes nothing
but itself, and has no pre-commit, no CI, no PR requirement. An **orphan
branch** (`git checkout --orphan`, no shared history with `main`) is how that is
expressed in git: its tree is just `scratch/`.

**Coordination hazard (unchanged):** concurrent sessions commit to shared
branches. Re-verify each step at your HEAD before acting.

## 3. Plan of work

Three waves. Wave 1 is the priority — it *is* "finish the recommendations" —
and is independent of the rest. Waves 2–3 remove the cause and can follow (or
wait for a quiet window).

**Wave 1 — Finish Wave C (re-grounded, stale item struck).** On a
fresh branch off `origin/main`: (1) add the gitleaks pre-commit hook + an
advisory non-required CI step (no ruleset-contract churn); (2) add
`docs_doctor.py --doc-refs` over tracked `md/py/yaml` to `test.sh l0`;
(3) move yamllint into `test.sh l0` and drop the yamllint + json-validate jobs
from `lint-config.yml` (keep actionlint — it needs the container binary;
pre-commit `check-json` already covers JSON locally); (4) add a weekly
`docs-link-audit` workflow cloned from `ruleset-audit.yml` running
`check_live_docs_links.py`, plus an open-issue-on-failure step on both it and
`ruleset-audit.yml` (the `hermes-version-check.yml` issue pattern; needs
`issues: write`). This shipped in #1258, touching `scripts/`+`.github/`
(sensitive → `needs_human`).

**Wave 2 — Orphan the `scratch` branch (removes the stale-analysis cause).**
Prerequisites, in order: (a) confirm the recovered work is provably on `main` —
review `git diff --stat origin/main origin/scratch -- ':!scratch/'` and account
for every non-`scratch/` delta as already-landed or intentionally-discarded
(the orphan reset abandons scratch's 180 ahead-commits); (b) a quiet window
with no active scratch worktrees. Then: delete ruleset 18508179 → orphan-reset
scratch to contain only `scratch/` → recreate the ruleset → recreate scratch
worktrees. The plan docs and the beta.1 design live under `scratch/`, so they
are the content that survives the reset. (Reversible alternative, if you want
history kept: a normal commit that `git rm -r`s everything except `scratch/` —
same end-state tree, force-push-free, misfiled history still recoverable. Noted
so the destructive orphan is a choice, not the only path.)

**Wave 3 — "Analysis runs from main" rule, enforced by structure.** In
AGENTS.md, rewrite the scratch-flow section to describe the orphan branch, and
add the rule: *repo audits and analysis run from a worktree of the code branch
under review (main by default); never from the scratch worktree.* Tag it
`enforced-by-structure: orphan scratch branch — no repo tree present to
analyze`. This needs one small extension to Wave B's `enforced:`-tag doctor: a
third tag class `enforced-by-structure:` that the doctor recognizes and
format-checks but does **not** try to resolve to a hook/script/check (those are
runnable mechanisms; this one is a layout invariant). Without that, the new tag
would false-fail the tag doctor. Extend `tests/test_agents_doctor.py`
accordingly.

## 4. Concrete steps

1. **Isolate** (`AGENTS.md` §1):

   ```bash
   git fetch origin
   git worktree add ~/mv/wf-audit-c -b fix/workflow-audit-c origin/main
   cd ~/mv/wf-audit-c
   ```

2. **Re-confirm the five Wave C findings at this HEAD** (they were real at
   f26596b8; main moves):

   ```bash
   git grep -liE 'gitleaks|detect-secrets|trufflehog' -- .pre-commit-config.yaml .github/ || echo "no scanner — real"
   grep -nE 'doc-refs|yamllint' scripts/test.sh || echo "absent in test.sh — real"
   git grep -l check_live_docs_links -- .github/ scripts/ || echo "invoked nowhere — real"
   ls tests/test_render_profile_configs.py 2>&1
   ```

   Any that resolved → strike from Wave 1 and log in §8.

3. **Wave 1 edits**, then prove each backstop bites:

   ```bash
   # gitleaks blocks a secret:
   printf 'AKIAIOSFODNN7EXAMPLE\n' > probe.txt && git add probe.txt && git commit -m probe   # expect: blocked
   git restore --staged probe.txt && rm probe.txt
   # --doc-refs now fails in the lint gate on a dangling ref:
   bash scripts/test.sh l0        # expect: runs --doc-refs + yamllint, exits 0 clean
   # render_profile_configs was struck: current main intentionally has no
   # installed-profile renderer, pinned by tests/test_profiles.py.
   ```

4. **Full gate + PR:**

   ```bash
   pre-commit run --all-files && bash scripts/test.sh all      # expect exit 0
   gh pr create --base main --fill && gh pr checks <n> --watch
   ```

5. **Wave 2 — orphan reset (quiet window only).** Pre-flight the rescue check
   first; do **not** proceed if it lists un-rescued non-`scratch/` work:

   ```bash
   git fetch origin
   git diff --stat origin/main origin/scratch -- ':!scratch/'   # must be all already-on-main / intentional
   git worktree list                                            # no active scratch worktrees
   env -u GITHUB_TOKEN gh api -X DELETE repos/eranroseman/memoria-vault/rulesets/18508179
   # in a throwaway checkout of origin/scratch:
   git switch --orphan scratch-orphan
   git checkout origin/scratch -- scratch/          # bring only scratch/ forward
   git add scratch/ && git commit -m "scratch: reset to standalone orphan (scratch/ only)"
   git push -f origin scratch-orphan:scratch
   # recreate the ruleset (same body as plan 1 step 6):
   env -u GITHUB_TOKEN gh api -X POST repos/eranroseman/memoria-vault/rulesets --input - <<'EOF'
   {"name":"scratch","target":"branch","enforcement":"active",
    "conditions":{"ref_name":{"include":["refs/heads/scratch"],"exclude":[]}},
    "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
   EOF
   ```

   Expected: `git ls-tree --name-only origin/scratch` prints only `scratch`;
   the plan docs are still present; `ruleset_doctor.py --live` green.

6. **Wave 3 — the rule** (own PR into `main`): edit AGENTS.md scratch-flow +
   add the rule with the `enforced-by-structure:` tag; extend the tag doctor
   and its test; `bash scripts/test.sh all` green; PR.

## 5. Validation and acceptance

- **Claim:** a key-shaped secret is blocked at commit. **Prove:** step 3
  gitleaks probe.
- **Claim:** `test.sh l0` runs `--doc-refs` and yamllint, and a dangling
  docs-ref fails the `lint` gate even with `--no-verify`. **Prove:** seed a
  dangling ref in a `scripts/` file, `bash scripts/test.sh l0` → nonzero.
- **Claim:** no `render_profile_configs` regression test is required. **Prove:**
  current `main` has no `scripts/render_profile_configs.py`, and
  `tests/test_profiles.py` pins installed-profile absence.
- **Claim (orphan):** `origin/scratch` tree is exactly `scratch/`; the plan
  docs survive; the ruleset is back and `ruleset_doctor --live` is green.
  **Prove:** step 5 `ls-tree` + doctor transcript.
- **Claim (structural rule):** the new `enforced-by-structure:` tag passes the
  tag doctor, and a repo audit cannot be sourced from the scratch worktree
  (there is no `scripts/`/`.agents/` there). **Prove:** `agents_doctor` exit 0
  on the tag; `ls ~/mv/scratch` shows only `scratch/`.
- **Claim:** nothing regressed — `pre-commit run --all-files` and
  `bash scripts/test.sh all` exit 0 on each PR's final commit.

## 6. Idempotence and recovery

- **Wave 1 & 3** are ordinary PRs — `git revert <merge-sha>` undoes either; the
  gitleaks/CI additions are advisory-or-local first, so a revert can't block
  unrelated PRs.
- **Wave 2 is the one destructive, hard-to-undo step.** Mitigations: the
  rescue-verify pre-flight gates it; the reversible `git rm -r` alternative
  keeps history if you prefer; and tagging the pre-reset tip
  (`git tag scratch-preorphan origin/scratch` before the force-push) leaves a
  recovery point until you're satisfied. Deleting the ruleset is momentary and
  immediately recreated.

## 7. Progress

- [x] 2026-07-04 — Wave C re-grounded against `origin/main` f26596b8: four
      findings confirmed real; stale profile-render item struck.
- [x] 2026-07-04 — Wave 1: finish Wave C live backstops — #1258 merged.
- [x] 2026-07-04 — Wave 2: scratch branch orphaned at `e93783b7`; ruleset
      18508798 recreated; `ruleset_doctor --live` green.
- [ ] Wave 3: "analysis runs from main" rule + `enforced-by-structure:` tag
      class + doctor extension — PR merged.
- [x] 2026-07-04 — Retired `exec-plan.md`; this file is the sole standalone
      plan an agent executes.
- [ ] Close-out: this plan deleted per ExecPlan lifecycle.

## 8. Execution log

- 2026-07-04 — Scope set by the user: finish the workflow-audit recommendations
  (Wave C) and fold in the orphan-branch + analysis-from-main rule; **beta.1
  left untouched** (its stale-analysis exposure is acknowledged but not
  remediated here). Re-grounded Wave C against `main` before authoring rather
  than trusting the scratch-tree findings — four live findings held, so no
  phantom risk.
- 2026-07-04 — Chose an orphan branch over a paths-only pre-commit hook + CI
  guard (proposed earlier, then dropped): with scratch holding nothing but
  `scratch/`, there is no repo tree to mis-edit or mis-audit, so the structural
  fix subsumes the hooks and honors "no pre-commit/CI on scratch." Added the
  `enforced-by-structure:` tag class so the new rule doesn't false-fail Wave B's
  tag doctor (structural invariants aren't runnable checks).
- 2026-07-04 — Retired the first plan (`exec-plan.md`) and made this file
  standalone. Safe because its Waves A/B are already merged (#1256/#1257) — the
  durable record is those PRs, not the plan — and its only pending work, Wave C,
  is carried here verbatim as Wave 1 (re-grounded against `main`). An executing
  agent runs this one file; there is no longer a second plan to confuse it.
- 2026-07-04 — Wave 1 shipped as #1258 (`a5dac378` on `main`). Local evidence:
  gitleaks blocked a seeded AWS-shaped key at commit time; a seeded dangling
  docs ref failed `bash scripts/test.sh l0`; clean `pre-commit run --all-files`
  and `bash scripts/test.sh all` passed; PR checks passed. The
  `render_profile_configs` test item was struck because current `main`
  intentionally retired installed-profile rendering and already pins that
  absence in `tests/test_profiles.py`.
- 2026-07-04 — Wave 2 completed. Pre-reset scratch tip was `125a4c0e`; the
  orphan root is `e93783b7` and contains exactly one top-level tracked entry,
  `scratch`. The ruleset was temporarily deleted for the force-push and
  recreated as id `18508798` with `deletion` + `non_fast_forward`; live
  `ruleset_doctor.py --live --repository eranroseman/memoria-vault` returned
  `ruleset-doctor: ok`. The local scratch checkout has empty untracked
  `.agents`/`.codex` helper directories from the agent environment, but
  `git ls-files` and `git ls-tree origin/scratch` prove the branch content is
  scratch-only.

## 9. Surprises & discoveries

- 2026-07-04 — Quantified the contamination: of 16 audit-target files, 15
  differ between `scratch` and `main` (AGENTS.md by 235 lines, `agents_doctor.py`
  by 244, `test.sh` by 99); the audited tree was 226 commits behind main / 180
  ahead. The implication drives Wave 2: an audit sourced from scratch is
  unreliable *as a statement about main*, which is why the fix is structural.
- 2026-07-04 — Residual not addressed here (by scope): false negatives — real
  `main` defects the scratch audit never surfaced because scratch had fixed
  them. Wave C's five findings are re-grounded, but a full main-sourced re-audit
  (to catch what the stale audit missed) is deliberately out of this plan.

## 10. Interfaces & dependencies

- `scripts/test.sh` `l0` — gains `docs_doctor.py --doc-refs` and yamllint;
  `.github/workflows/lint-config.yml` loses its yamllint/json-validate jobs.
- `scripts/agents_doctor.py` — Wave B's `enforced:`-tag check gains a third tag
  class `enforced-by-structure:` (format-checked, not resolved to a file).
- `.github/ruleset-contract.yaml` / ruleset **18508798** — deleted and
  recreated across the orphan reset; contract declaration unchanged.
- gitleaks — local pre-commit wrapper plus advisory CI image.
- Orphan mechanics — `git switch --orphan` + `git checkout origin/scratch --
  scratch/`; `non_fast_forward` on the live ruleset forces the delete/recreate
  ordering.

## 11. Artifacts & notes

- Re-grounding transcript (Wave C vs `origin/main` f26596b8) captured in §2.
- Prior plan retired: Waves A/B shipped as #1256/#1257 (their durable record is
  the merged PRs); their Wave C is carried here as Wave 1. `exec-plan.md` was
  deleted — this file is the sole standalone plan.
- Beta.1 design is intentionally **not** modified by this plan.

## 12. Outcomes & retrospective

- **Shipped:** — (fill at close)
- **Still open:** — (note the deferred main-sourced re-audit if it's wanted)
- **Routed to:** AGENTS.md scratch-flow (orphan model + analysis-from-main rule)
- **Lessons:** —
