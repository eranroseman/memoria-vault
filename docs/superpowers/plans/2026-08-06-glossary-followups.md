# Glossary Follow-ups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the two follow-ups PR #1764 deliberately left out of scope: the request-row field list that contradicts the schema, and the work-package-code citations that diverge from the PI's ruling that only `roadmap.md` cites codes.

**Architecture:** Two independent docs-only sweeps. Task 1 fixes one table row in `why-layered-architecture.md` whose field list names a column (`handoff payload`) that `operation_requests` does not have. Task 2 removes work-package codes (K1, G4/G5, B1, K3, W2, O1/O2, R2, U1/U2, I1/E1, G3, V1) from every published page outside `roadmap.md`, keeping the Planned/Shipped markers, the milestone names (`beta.1`/`beta.2`), and any existing roadmap links.

**Tech Stack:** Markdown (kramdown, Just the Docs on GitHub Pages), pre-commit manual-stage lint (cspell, markdownlint, vale), `python scripts/verify`.

## Global Constraints

- Docs-only; **no `src/` or `tests/` changes**.
- Stage explicit paths only — the repo's `PreToolUse` hook rejects `git add -A`.
- Correctness gate: `python scripts/verify` must pass before the PR.
- American English; if cspell flags a real term, add it to `project-words.txt` (lowercase, sorted) — never inline-suppress.
- **Trust order is schema → tests → code → docs**: the schema (`src/memoria_vault/runtime/schema.sql`) wins over any docs text, including the replacement text in this plan.
- **PI ruling being implemented (Task 2):** "Only roadmap.md cites work packages by code. Other pages use planned or deferred with or without a link to roadmap." Interpretation locked by this plan: work-package codes go; milestone names (`beta.1`, `beta.2`) stay where they convey sequencing; existing roadmap links stay; no new links required.
- Out of scope, do not touch: `docs/roadmap.md` (the one page that owns the codes), `docs/superpowers/` (unpublished working docs), `design-history/` (frozen record), and the L1–L5 autonomy-level vocabulary (`why-not-autonomous.md`, `what-memoria-is.md:104`, `pattern-provenance.md:51` — that is Chen's taxonomy, not work packages), and `vault-eval.md`'s `2026-Q2` quarter strings.
- End commit messages with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

**Lint command used throughout:**

```bash
pre-commit run --hook-stage manual --files <changed files>
```

**Branch note:** execute on a fresh worktree/branch from `origin/main`. PR #1764 (`wip/glossary`) also edits `docs/README.md`, but at line 153 (Co-PI row) — Task 2 touches lines 98–104, so the branches merge cleanly in either order.

---

### Task 1: Request-row field list matches the schema

**Files:**
- Modify: `docs/explanation/rationale/boundaries/why-layered-architecture.md:36`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing later tasks rely on.

Why: the "What happens when they collapse" table says a request row records a "handoff payload". `operation_requests` (`src/memoria_vault/runtime/schema.sql:2-23`) has no such column — its payload column is `job_json`. The glossary (as of PR #1764) defines Handoff payload as the Linter's `hub_handoff` map proposal, a different thing entirely. This stale row is almost certainly where the old, wrong glossary definition came from.

- [ ] **Step 1: Verify the defect is present**

Run: `grep -n "handoff payload" docs/explanation/rationale/boundaries/why-layered-architecture.md`
Expected: 1 hit on line 36.

- [ ] **Step 2: Verify the schema yourself**

Read `src/memoria_vault/runtime/schema.sql` lines 2–23. Confirm `operation_requests` has `status`, `operation_id`, `input_refs_json`, `output_intents_json`, `job_json`, and `error` — and no handoff column. If the schema has changed since this plan was written, the schema wins: pick the field wording from what you find.

- [ ] **Step 3: Fix the row**

In `docs/explanation/rationale/boundaries/why-layered-architecture.md`, replace:

```
| Orchestration + execution | Work state lives in chat or agent memory; retries duplicate work and handoffs lose context. | A request row records status, operation, input refs, output intents, handoff payload, and failure history. |
```

with:

```
| Orchestration + execution | Work state lives in chat or agent memory; retries duplicate work and handoffs lose context. | A request row records status, operation, input refs, output intents, job payload, and failure history. |
```

(Only "handoff payload" → "job payload"; the rest of the row is accurate: `status`, `input_refs_json`, `output_intents_json`, `job_json`, `error`.)

- [ ] **Step 4: Verify the fix**

Run: `grep -n "handoff" docs/explanation/rationale/boundaries/why-layered-architecture.md`
Expected: no "handoff payload" hit remains on line 36. ("handoffs lose context" in the Failure column is ordinary prose and stays.)

Run: `pre-commit run --hook-stage manual --files docs/explanation/rationale/boundaries/why-layered-architecture.md`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add docs/explanation/rationale/boundaries/why-layered-architecture.md
git commit -m "docs: request-row field list matches the schema

operation_requests carries job_json, not a handoff payload column. This
row was the likely origin of the stale glossary definition PR #1764
corrected.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Work-package codes live only in roadmap.md

**Files (14, modify only):**
- `docs/README.md:98-104`
- `docs/explanation/rationale/foundations/intellectual-foundations.md:60-61,71-73`
- `docs/explanation/knowledge/consequence-propagation.md:10`
- `docs/explanation/rationale/foundations/what-memoria-is.md:46,50`
- `docs/explanation/architecture/consistency-model.md:43`
- `docs/explanation/architecture/vault.md:31`
- `docs/explanation/rationale/foundations/design-principles.md:83-85,91-93`
- `docs/explanation/knowledge/knowledge-cycle.md:16-17`
- `docs/explanation/execution/control-plane/states.md:83-86`
- `docs/explanation/architecture/okf-and-portability.md:12,41`
- `docs/reference/analysis-and-surfaces/calibration.md:17`
- `docs/explanation/surfaces/README.md:27,31`
- `docs/reference/data-model/okf-compliance.md:29,44,52-53,55-56`
- `docs/reference/system/on-disk-layout.md:184`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: nothing later tasks rely on.

Transformation rule, applied uniformly: delete the work-package code and any punctuation that carried it; keep the marker word (Planned/Shipped), keep `beta.1`/`beta.2`, keep surrounding prose and links; re-wrap any line the deletion leaves badly wrapped (file convention ~72–80 chars). Every site with its exact before → after:

- [ ] **Step 1: `docs/README.md` — three bullets (lines 98–104)**

```
  — grounded synthesis, workstream R2)*.        →   — grounded synthesis)*.
  — typed blast-radius propagation, workstream G5)*.   →   — typed blast-radius propagation)*.
  the onboarding bar, workstream O1; it ships with the telemetry that measures   →   the onboarding bar; it ships with the telemetry that measures
```

Line 96's `**Planned — beta.1 milestone** ([Roadmap & status](roadmap.md)):` stays — milestone name plus link, no code.

- [ ] **Step 2: `intellectual-foundations.md` — two callouts**

Lines 60–61, replace:

```
> **Planned:** The six-role graph and typed consequence propagation described
> here ship in G4/G5 with the graph substrate in the beta.1 milestone (B1).
```

with:

```
> **Planned:** The six-role graph and typed consequence propagation described
> here ship with the graph substrate in the beta.1 milestone.
```

Lines 71–73, replace:

```
> **Planned:** The beta.1 precursors are I1 event plumbing and E1 frozen
> evaluation; the measured keep-or-discard autoresearch overnight loop ships in
> beta.2.
```

with:

```
> **Planned:** The beta.1 precursors are event plumbing and frozen
> evaluation; the measured keep-or-discard autoresearch overnight loop ships in
> beta.2.
```

- [ ] **Step 3: `consequence-propagation.md:10`**

```
> **Planned (G4/G5, beta.1/B1):** Typed graph propagation and eager write-time marking described below are target-state.
```

becomes

```
> **Planned (beta.1):** Typed graph propagation and eager write-time marking described below are target-state.
```

- [ ] **Step 4: `what-memoria-is.md` — two callouts**

Line 46: `> **Planned beta.1 — K1:** strict OKF conformance…` → `> **Planned beta.1:** strict OKF conformance…`
Line 50: `> **Planned beta.1 — K1/W2:** detachability…` → `> **Planned beta.1:** detachability…`

- [ ] **Step 5: `consistency-model.md:43` and `vault.md:31`**

`> **Planned (beta.1 — K3):**` → `> **Planned (beta.1):**`
`> **Planned (beta.1 — K1/W2):**` → `> **Planned (beta.1):**`

- [ ] **Step 6: `design-principles.md` — two callouts**

Lines 83–85, replace:

```
> **Planned — G4 (beta.1/B1) and V1 (beta.1):** The complete Toulmin
> warrant graph and its checking model are planned across these milestones. Today,
> `checked` covers shipped checks, not the complete Toulmin warrant graph.
```

with:

```
> **Planned (beta.1):** The complete Toulmin warrant graph and its
> checking model are planned for that milestone. Today, `checked` covers
> shipped checks, not the complete Toulmin warrant graph.
```

Lines 91–93, replace:

```
> **Planned — G5 (beta.1/B1):** Origin-blind epistemic consequence and
> blast-radius propagation are planned for this milestone. Today, write and revert
> authority remains origin-gated as stated above.
```

with:

```
> **Planned (beta.1):** Origin-blind epistemic consequence and
> blast-radius propagation are planned for that milestone. Today, write and
> revert authority remains origin-gated as stated above.
```

- [ ] **Step 7: `knowledge-cycle.md:16-17`**

```
> **Planned beta.1 — O2/W2:** Project-pulled admission and the complete
> project-close harvest loop described below are target-state.
```

becomes

```
> **Planned beta.1:** Project-pulled admission and the complete
> project-close harvest loop described below are target-state.
```

- [ ] **Step 8: `states.md:83-86`**

```
> **Planned — G4 (beta.1/B1) and V1 (beta.1):** The complete Toulmin
> warrant graph and its checking model are planned across these milestones.
> Today, `grounds resolve` covers shipped evidence/check resolution (e.g.
> code-grounds references), not the complete Toulmin warrant graph.
```

becomes

```
> **Planned (beta.1):** The complete Toulmin warrant graph and its
> checking model are planned for that milestone. Today, `grounds resolve`
> covers shipped evidence/check resolution (e.g. code-grounds references),
> not the complete Toulmin warrant graph.
```

- [ ] **Step 9: `okf-and-portability.md` — two sites**

Line 12: `**Planned (beta.1 — K1):** standard-Markdown links discipline for` → `**Planned (beta.1):** standard-Markdown links discipline for`
Line 41: `> **Planned (beta.1 — K1/W2):** Detachability enforcement…` → `> **Planned (beta.1):** Detachability enforcement…`

- [ ] **Step 10: `calibration.md:17`**

`> **Planned beta.1 — I1/E1:** A reusable calibration contract does not ship` → `> **Planned beta.1:** A reusable calibration contract does not ship`

- [ ] **Step 11: `surfaces/README.md` — two sites**

Line 27: `**Shipped — U1.** \`memoria help\` presents five jobs…` → `**Shipped.** \`memoria help\` presents five jobs…`
Line 31: `**Planned beta.1 — U2.** Deep work (compose, canvas, drafting)…` → `**Planned beta.1.** Deep work (compose, canvas, drafting)…`

- [ ] **Step 12: `okf-compliance.md` — four sites**

Line 29: `(Planned: G3, beta.1/B1.)` → `(Planned beta.1.)`
Line 44: `**Planned beta.1 — K1.**` → `**Planned beta.1.**`
Lines 52–53: the wrapped `**Planned\n  beta.1 — K1.**` → `**Planned beta.1.**` on one line (re-wrap the sentence it ends).
Lines 55–56: the wrapped `**Planned beta.1 —\n  K1.**` → `**Planned beta.1.**` on one line (re-wrap likewise).

- [ ] **Step 13: `on-disk-layout.md:184`**

In the `.memoria/config/decision-rules.yaml` table row, delete the parenthetical `(I1 spec §5)` — it cites an unpublished working spec by code, a dead pointer for site readers:

`The pre-registered decision rules (I1 spec §5) with their per-vault…` → `The pre-registered decision rules with their per-vault…`

- [ ] **Step 14: Sweep verification**

Run each; expected: no output from all three.

```bash
grep -rnE "\b(Planned|Shipped|Deferred)[^.]{0,60}\b[A-Z][0-9]{1,2}\b" docs/ --include="*.md" | grep -vE "docs/(roadmap\.md|superpowers/)" | grep -vE "\bL[1-5]\b"
grep -rn "workstream" docs/ --include="*.md" | grep -vE "docs/(roadmap\.md|superpowers/)"
grep -rn "I1 spec" docs/ --include="*.md" | grep -v "docs/superpowers/"
```

Then the false-positive control — this one SHOULD still return hits (autonomy levels and quarters, untouched):

```bash
grep -rlE "\bL[1-5]\b|2026-Q2" docs/explanation/rationale/boundaries/why-not-autonomous.md docs/reference/analysis-and-surfaces/vault-eval.md
```

- [ ] **Step 15: Lint and commit**

Run: `pre-commit run --hook-stage manual --files` with all 14 changed files.
Expected: pass.

```bash
git add docs/README.md docs/explanation/rationale/foundations/intellectual-foundations.md docs/explanation/knowledge/consequence-propagation.md docs/explanation/rationale/foundations/what-memoria-is.md docs/explanation/architecture/consistency-model.md docs/explanation/architecture/vault.md docs/explanation/rationale/foundations/design-principles.md docs/explanation/knowledge/knowledge-cycle.md docs/explanation/execution/control-plane/states.md docs/explanation/architecture/okf-and-portability.md docs/reference/analysis-and-surfaces/calibration.md docs/explanation/surfaces/README.md docs/reference/data-model/okf-compliance.md docs/reference/system/on-disk-layout.md
git commit -m "docs: work-package codes live only in roadmap.md

Per PI ruling, pages outside the roadmap say planned or deferred (with
or without a roadmap link); the workstream decoder stays the one home
for codes. Milestone names (beta.1/beta.2) stay where they convey
sequencing.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Close-out — full gate and PR

**Files:**
- Commit: `docs/superpowers/plans/2026-08-06-glossary-followups.md` (this plan, tracked per repo convention)
- Read-only verification otherwise.

- [ ] **Step 1: Commit the plan file**

```bash
git add docs/superpowers/plans/2026-08-06-glossary-followups.md
git commit -m "docs: track the glossary-followups plan this branch executed

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 2: Full correctness gate**

Run: `python scripts/verify`
Expected: `verify: OK`. If a docs gate fails, the gate wins — fix the flagged wording and amend the relevant commit.

- [ ] **Step 3: Full lint on the branch's changed files**

```bash
git diff --name-only origin/main | xargs pre-commit run --hook-stage manual --files
```

Expected: all hooks pass.

- [ ] **Step 4: Push and open the PR**

```bash
git push -u origin HEAD
gh pr create --title "Docs follow-ups: request-row fields match the schema; codes live only in roadmap.md" --body "$(cat <<'EOF'
## Summary

The two follow-ups PR #1764 deliberately left out of scope:

- `why-layered-architecture.md` listed a "handoff payload" request-row field; `operation_requests` carries `job_json`, no handoff column. The row now matches the schema — this line was the likely origin of the stale glossary definition #1764 corrected.
- Work-package codes (K1, G4/G5, B1, K3, W2, O1/O2, R2, U1/U2, I1/E1, G3, V1) removed from 14 published pages, per PI ruling that only `roadmap.md`'s workstream decoder cites codes. Planned/Shipped markers, milestone names (beta.1/beta.2), and existing roadmap links all stay. The L1–L5 autonomy vocabulary and `2026-Q2` quarter strings are untouched (not work packages).

## Test plan

- `python scripts/verify` → `verify: OK`
- Sweep greps: zero code citations remain outside `roadmap.md` and `docs/superpowers/`
- pre-commit manual stage (vale, markdownlint-structural, cspell) passes on all changed files

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-review notes

- Spec coverage: follow-up 1 → Task 1; follow-up 2 → Task 2 (all 22 sites the evidence pass found, enumerated with exact before/after); both greps in Task 2 Step 14 catch any site the enumeration missed.
- Interpretation locked in Global Constraints: codes go, `beta.1`/`beta.2` milestone names stay — the PI's ruling targeted codes; the glossary's stricter bare-"Planned" style is not forced onto explanation pages whose substance is the phasing (e.g. the autoresearch beta.1-precursors-vs-beta.2-loop sentence).
- No placeholder scan hits: every edit shows verbatim before and after text.
- The three README bullets sit inside a `**Planned — beta.1 milestone** ([Roadmap & status](roadmap.md)):` block, so their roadmap link survives at the block level.
- Gates: grep of `scripts/checks/` found no gate pinning any touched line; `python scripts/verify` in Task 3 is the backstop.
