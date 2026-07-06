# ExecPlan — Living design history: adopt the two-layer decision record, retire ADRs

## 0. Metadata

- **Task:** Convert the design history into the durable, living decision record
  (frozen per-version chapters + one projected `arcs.md`), retire `docs/adr/` as
  the decision mechanism, and cut every workflow document (`AGENTS.md`,
  `.agents/`) over to the new model.
- **Worktree / branch:** `~/memoria-vault/worktrees/design-history` ·
  `feat/design-history` for main-repo stages; this plan file lives on
  `scratch` at `releases/0.1.0-beta.1/exec-plan-living-design-history.md`.
- **Related ADRs:** — (this plan retires the ADR mechanism; the decision behind
  it is recorded as a dated decision entry, §3 "Bootstrap", not as an ADR).
- **Related issues / milestone:** 0.1.0-beta.1 checkpoint. File a "Release
  beta.1" sub-issue per stage when scheduling (§3 staging).
- **Started:** 2026-07-05 · **Last updated:** 2026-07-05

## 1. Purpose / big picture

Memoria's decision record becomes one system instead of three half-systems
(live ADRs in `docs/adr/`, a 557KB design-history monolith on scratch, and
dated decision sections scattered through release design docs). After this
plan:

- `design-history/` on **main** holds the durable record: frozen per-version
  chapters (`00-origins.md` … `15-alpha.15.md`, then `16-beta.1.md`, …) plus
  one living `arcs.md` that answers "what is the current position on axis X
  and how did we get here" with a `Current (as of <release>)` line per design
  axis.
- New decisions are captured **where they are made** — a dated, Y-statement
  entry in the release workspace — and distilled into a chapter at release
  close. **No new ADRs are ever minted**; `ADR-NN` survives only as a
  historical grep key into the chapters.
- Every workflow document that told an agent "decisions go to ADRs" says the
  new thing instead, so an agent landing cold in the repo cannot follow a
  retired rule.

Observable end state: `ls ~/memoria-vault/main/design-history/` shows 18
files; `rg -c 'Current \(as of' design-history/arcs.md` equals the arc count;
`docs/adr/` contains only a tombstone README; `python scripts/verify l0` is
green; and `rg -n 'go to.*ADR|to an ADR' .agents/ AGENTS.md` returns nothing.

**Why (the decision this implements, dated 2026-07-05):** in the alpha line,
wrong or stale ADR decisions became the justification for new ones — the
owner's rule became "ignore ADRs when making decisions," which means the
artifact failed its purpose. An ADR is authority-shaped (a numbered, citable
unit designed to be referenced); the chapter+arcs form is evidence-shaped (it
records what happened and what failure taught, and cannot be "complied with").
Full rationale and the verified prior art (PEP-0/RFC-style immutable record +
projected index; Nygard on document size; Google SWE ch.10 on doc rot) are in
the session record that produced this plan; the durable summary goes into the
`16-beta.1.md` chapter at release close.

## 2. Context and orientation

Vocabulary, defined once:

- **Design history**: `scratch/design-history/memoria-design-history-alpha.1-to-alpha.15.md`
  — a 557KB, ~2,400-line reconstruction of every design decision alpha.1→15.
  Internal structure: Part I Origins (L17), Part II alpha.1 baseline (L68),
  Part III per-version changelog (L631; one `## alpha.N` section each), Part IV
  synthesis arcs (L2240). It already *contains* the target structure; the gap
  is file boundaries and the living layer.
- **Arc**: one design axis traced across versions (identity, hub, integrity,
  catalog authority, …). Part IV holds these today as prose.
- **Y-statement** (Zdun/Zimmermann, IEEE Software 2013): one-sentence decision
  capture — *"In the context of ⟨use case⟩, facing ⟨concern⟩, we decided
  ⟨option⟩ to achieve ⟨quality⟩, accepting ⟨downside⟩."* The rationale travels
  with the decision so it can be re-derived, not cited.
- **Typed pointers**: `Reverses: <chapter>#<anchor>` (successor stands alone) /
  `Amends: <chapter>#<anchor>` (supplement) — the IETF Obsoletes/Updates
  distinction, which is what lets `arcs.md` be maintained semi-mechanically.
- **The rule the whole design serves**: **history is evidence, never
  authority.** No decision may cite a chapter, arc, or ADR as justification.
  Justification = requirements + current evidence; history is cited only for
  *what failure was observed*.

Current state of the pieces this plan touches:

- `main/docs/adr/` — 28 live ADR files + `README.md` + `_template.md`.
  AGENTS.md calls it "the single home for every live decision"; superseded
  ADRs are already *deleted* (recoverable in git history) — precedent this
  plan extends to the whole tree. 41 pages under `docs/` link into `adr/`.
  `docs/adr/` is a pr-policy **sensitive path**.
- `main/docs/design/` — 18 Diátaxis-explanation pages ("why is it designed
  this way"). **Out of scope**: they explain the current system, they are not
  decision records. Only their `adr/` links get rewritten in Stage 3.
- `main/AGENTS.md` — carries the ADR workflow in: the ExecPlans section
  ("decisions to ADRs"), the "ADR template (`docs/adr/`)" section, the
  docs-writing ADR-links bullet, the Work-routing table (two rows), the
  pr-policy mirror table, and Merge discipline ("same ADR").
- `main/.agents/` — ADR-workflow instructions in:
  `templates/exec-plan.md` (mandate 5, §0 field, §8, §12),
  `playbooks/exec-plan.md` (L30, L47, L49, L65-67, L110),
  `templates/handoff.md` (L40), `templates/release-plan.md` (L31, L42, L44),
  `playbooks/release.md` (L15, L56-58 "retire-sweep ADRs", L64),
  `playbooks/docs-review.md` (L57, ADR-index drift check),
  `skills/schema-change/SKILL.md` (L47, L50),
  `system/source-of-truth-map.md` (L26, L33-34, L39, L72).
- CI relevant here: `lint` runs `python scripts/verify l0` (docs-doctor link
  checks, agents-doctor AGENTS.md-mirror checks); `cspell` gates tracked prose
  markdown (`cspell.json` scope); `markdownlint` covers `docs/` only;
  `tests/test_pr_policy.py` covers `.github/scripts/pr_policy.py`.
- The beta.1 release workspace (`scratch/releases/0.1.0-beta.1/`) holds the
  sources the first new chapter will distill: the design doc (§11–§18 dated
  decisions), the gap adjudication, and the owner rulings file — the
  contemporaneous decision record this plan formalizes.

## 3. Plan of work

Four stages, additive before destructive, one PR each on main (Stage 0 and 4
are scratch-side). Each stage is independently shippable and revertible.

**Stage 0 — Bootstrap decision entry (scratch, no PR).** Record the decision
this plan implements as the *first instance of the new mechanism*: a dated
Y-statement entry appended to the beta.1 release workspace (a new
`releases/0.1.0-beta.1/decisions.md` ledger seeded with it). This is
deliberately self-hosting: the decision to retire ADRs is not an ADR.

**Stage 1 — Create `design-history/` on main (additive PR).** Split the
monolith at its existing header boundaries into `main/design-history/`:
Part I → `00-origins.md`, Part II → `01-alpha.1-baseline.md`, each Part III
`## alpha.N` → `02-alpha.2.md` … `15-alpha.15.md`, Part IV → `arcs.md`. Zero
prose rewriting in chapters. Then: (a) rework `arcs.md` — per arc, lineage
bullets pointing at chapters, ending in `**Current (as of alpha.15):** …` and
`**Pending (unreleased):** …` seeded from the beta.1 owner rulings and the
settled adjudication outcomes; add a "Decision-record mechanism" arc whose
lineage is Old-Skeleton → ADR model → alpha.4 ExecPlan/ADR-only split →
docs-tree deletion → this decision; (b) write `design-history/README.md` — the
map plus the four rules (chapters freeze, dated corrections only; history is
evidence never authority; decision-time capture as Y-statement entries in the
release workspace with typed pointers; release-close procedure) and the check
command; (c) add `design-history/**` to `cspell.json` ignorePaths (historical
record, alpha-era vocabulary — not prose to gate; markdownlint doesn't apply,
its scope is `docs/`). Root placement, not `docs/`: unpublished working record
like `.agents/`, keeps the published site describing only the current system,
and pr-policy classifies root-unknown paths `needs_human`, which is the right
review posture for the decision record without touching policy code. The
scratch monolith stays untouched until Stage 4 verification.

**Stage 2 — Workflow cutover in AGENTS.md + `.agents/` (sensitive-path PR).**
Replace every "decisions go to ADRs" instruction with the new model. AGENTS.md:
swap the "ADR template" section for a "Decision records (`design-history/`)"
section carrying the four rules, the no-new-ADRs statement, and the
decision-entry format; update the ExecPlans section, both Work-routing rows
(decisions → dated entry in the release workspace, distilled to a chapter at
close; durable analysis → the release workspace doc that carries the entry),
the docs-writing links bullet (history references only in explanation prose,
title-text links), the Where-things-live table (add `design-history/`), the
Skills table (add the new playbook), and Merge discipline ("same decision", not
"same ADR"). `.agents/`: edit the eight files listed in §2 accordingly; add
`playbooks/design-history.md` (the release-close procedure: draft chapter from
the release workspace → promote every `Pending` line → rewrite `Current` lines
→ one commit; plus mid-cycle procedure: decision entry + arc `Pending` line);
register it in `.agents/README.md`. Open proposals stop being
`status: proposed` ADRs — they live as GitHub issues (already the scheduling
home) until decided, then get a dated decision entry. agents-doctor guards the
AGENTS.md mirrors; run `python scripts/verify l0` before the PR.

**Stage 3 — Absorb and retire `docs/adr/` (destructive PR — owner checkpoint
before starting).** For each of the 28 live ADRs: verify its decision is
represented in a chapter + the relevant arc's `Current` line (most are — the
history was reconstructed from them; the alpha.15-era ADRs 122–130 are
extensively covered); add any missing arc line. Rewrite the 41 inbound
`docs/` links to point at the design-history chapter/arc anchor (or drop the
link where the prose stands alone — per the docs rule, title-text links in
explanation prose only). Delete the ADR files and `_template.md`; leave
`docs/adr/README.md` as a tombstone ("Retired 2026-07: decisions live in
`design-history/`; ADR-NN are historical keys — full texts in git history at
tag/commit …"). Update `.github/scripts/pr_policy.py`: remove the dead
`docs/adr/` carve-outs (sensitive list, and the docs-safe-path exception) and
update `tests/test_pr_policy.py` to match; retire the ADR-index drift check
referenced by `playbooks/docs-review.md`. docs-doctor (in `verify l0`) proves
the link sweep is complete.


## 4. Concrete steps

1. **Isolate the session** (`AGENTS.md` §1):

   ```bash
   git -C ~/memoria-vault/main fetch origin
   git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/design-history -b feat/design-history origin/main
   cd ~/memoria-vault/worktrees/design-history
   ```

2. **Stage 0 — bootstrap decision entry** (scratch worktree, direct push per
   scratch flow):

   ```bash
   cd ~/memoria-vault/scratch && git pull --ff-only origin scratch
   # create releases/0.1.0-beta.1/decisions.md with the dated Y-statement entry:
   # "2026-07-05 — In the context of Memoria's decision record, facing ADR
   #  justification-chains (stale decisions justifying new ones) and the
   #  deleted-docs rot history, we decided on a living design history (frozen
   #  chapters + projected arcs.md) with decision-time capture as dated
   #  Y-statement entries, to achieve a record that is evidence rather than
   #  authority, accepting release-close distillation discipline as the new
   #  maintenance duty. Reverses: docs/adr mechanism (AGENTS.md 'ADR template')."
   git add releases/0.1.0-beta.1/decisions.md
   git commit -m "scratch: bootstrap decision entry — living design history" && git push origin HEAD:scratch
   ```

3. **Stage 1 — split the monolith** (in the feat worktree; the split script is
   ~20 lines of awk keyed on the header lines listed in §2):

   ```bash
   mkdir design-history
   python3 - <<'EOF'
   # read scratch/design-history monolith; emit 00-origins.md (L17-67),
   # 01-alpha.1-baseline.md (L68-630), 02..15 per '## alpha.N' boundary in
   # Part III (L631-2239), arcs.md (L2240-end). Assert: sum of emitted lines
   # + section-header adjustments == wc -l of source.
   EOF
   wc -l design-history/*.md   # expected: 18 files, total ≈ source total
   ```

   Then author `arcs.md` Current/Pending lines and `README.md` (manual,
   content per §3), and:

   ```bash
   # cspell.json: "ignorePaths" += "design-history/**"
   python scripts/verify l0    # expected: PASS
   git add design-history cspell.json && git commit -m "feat: design-history — frozen chapters + living arcs"
   git push -u origin feat/design-history && gh pr create --base main --fill
   ```

4. **Stage 2 — workflow cutover** (new worktree/branch `feat/decision-workflow`
   after Stage 1 merges): apply the AGENTS.md + `.agents/` edits enumerated in
   §2/§3, add `playbooks/design-history.md`, then:

   ```bash
   rg -n 'go to.*ADR|to an ADR|ADR in `docs/adr/`' AGENTS.md .agents/   # expected: no matches
   python scripts/verify l0                                            # expected: PASS (agents-doctor green)
   ```

5. **Stage 3 — retire docs/adr** (new branch `feat/retire-adr`, only after the
   owner confirms): absorption audit (28 ADRs → arc lines), link sweep (41
   files), delete + tombstone, `pr_policy.py` + `tests/test_pr_policy.py`:

   ```bash
   rg -l 'adr/' docs --glob '!docs/adr/**'      # expected: no matches after sweep
   python -m pytest tests/test_pr_policy.py     # expected: PASS
   python scripts/verify l0                     # expected: PASS (docs-doctor green)
   ```



## 5. Validation and acceptance

- **Claim:** Given the merged Stage 1, when a reader opens
  `design-history/arcs.md`, then every arc section ends with a
  `Current (as of alpha.15)` line and chapters are byte-faithful to the
  monolith. **Prove with:** the split script's line-accounting assertion +
  `rg -c 'Current \(as of' design-history/arcs.md`.
- **Claim:** Given the merged Stage 2, when an agent greps the workflow docs
  for where decisions go, then only the design-history mechanism appears.
  **Prove with:** `rg -n 'go to.*ADR|to an ADR' AGENTS.md .agents/` → empty;
  `python scripts/verify l0` → PASS.
- **Claim:** Given the merged Stage 3, when CI runs on any docs PR, then no
  link into `docs/adr/` remains and pr-policy has no dead ADR carve-outs.
  **Prove with:** `verify l0` docs-doctor PASS; `pytest tests/test_pr_policy.py` PASS.
- **Failure behavior:** if the split's line accounting fails, nothing is
  committed (script asserts before writing); if the Stage 3 link sweep misses
  a file, docs-doctor fails the `lint` check and the PR cannot merge.

## 6. Idempotence and recovery

- **Safe to re-run:** the split script regenerates all 18 files from the
  unchanged scratch monolith (deterministic, asserts coverage first); each
  grep/lint check is read-only; Stage 2/3 edits are plain-text and re-applied
  edits converge.
- **Rollback:** each stage is one squash-merged PR — `git revert <merge-sha>`
  restores the prior state; the scratch monolith is not deleted until Stage 4
  re-verifies coverage, so Stage 1–3 rollback loses nothing; deleted ADRs
  remain in git history (the tombstone names the last tag containing them).

## 7. Progress

- [x] Stage 0: bootstrap decision entry on scratch
- [x] Stage 1: design-history/ split PR merged, verify l0 green
- [x] Stage 2: AGENTS.md + .agents/ cutover PR merged, agents-doctor green
- [x] OWNER CHECKPOINT: confirm Stage 3 (delete docs/adr/) before branching
- [x] Stage 3: absorb + retire docs/adr PR merged, docs-doctor green

## 8. Execution log

<!-- Tactical/sequencing choices made while running. The governing decision is
     the Stage 0 dated entry — not an ADR, by design. -->

- 2026-07-05 — Plan authored. Sequencing choice: additive (Stage 1) before
  cutover (Stage 2) before destructive (Stage 3) so every PR is independently
  revertible and the owner checkpoint sits before the only irreversible-ish
  step.
- 2026-07-06 — Implementation audit found the staged work landed, with one
  small remaining cutover gap: root README/CONTRIBUTING and docs-doctor fixtures
  still referenced `docs/adr/` as live decision material. Patched those in
  `agent/design-history-implementation-audit`; `python scripts/verify l0`
  passed.

## 9. Surprises & discoveries

- The repo already half-adopted the target model: superseded ADRs are deleted
  (not statused), decision history is explicitly delegated to git history, and
  beta.1 decisions accreted as dated design-doc sections (§17/§18) — the new
  workflow formalizes existing drift rather than fighting it.
- `docs/adr/` is a pr-policy sensitive path and appears in the auto-approve
  carve-out ("docs/ except docs/adr/") — retiring it requires a policy-code
  edit + test update (Stage 3), not just file deletion.
- The 557KB monolith exceeds agent read limits (measured this session) — the
  split is a functional requirement for agent consumers, not aesthetics.

## 10. Interfaces & dependencies

- `python scripts/verify l0` — the lint aggregate (docs-doctor, agents-doctor,
  ruleset-doctor…): the acceptance gate for Stages 1–3.
- `.github/scripts/pr_policy.py` + `tests/test_pr_policy.py` — the only code
  touched (Stage 3).
- `cspell.json` `ignorePaths` — Stage 1 addition.
- Source of the split: `scratch/design-history/memoria-design-history-alpha.1-to-alpha.15.md`
  (header-line map in §2 — recompute with `grep -n '^# \|^## ' <file>` before
  splitting; do not trust cached line numbers).
- Beta.1 chapter sources (Stage 4): `scratch/releases/0.1.0-beta.1/`
  {design.md §11–§18, gap adjudication, owner rulings, decisions.md}.

## 11. Artifacts & notes

- `design-history/` has 18 Markdown files: 16 frozen chapters, `README.md`, and
  `arcs.md`.
- `design-history/arcs.md`: 10 `Current (as of alpha.15)` lines and 10
  `Pending (unreleased)` lines.
- Frozen chapter audit: 16 chapter files match the source monolith section
  content with source separator blanks accounted outside stored EOF whitespace.
- `docs/adr/` contains only `README.md`.
- ``rg -n 'go to.*ADR|to an ADR|ADR in `docs/adr/`' AGENTS.md .agents/``:
  no matches.
- `rg -n 'adr/' docs --glob '!docs/adr/**'`: no matches.
- `python -m pytest tests/test_docs_doctor.py tests/test_pr_policy.py`: 33
  passed.
- `python scripts/checks/docs_doctor.py docs`: clean.
- `python scripts/verify l0`: PASS; evidence
  `/tmp/memoria-verify/20260706T013511Z-l0/summary.json`.

## 12. Outcomes & retrospective

<!-- Filled at close. -->

- **Shipped:** `design-history/` replaced live ADRs as the decision record,
  workflow guidance points at the release-ledger + design-history model, and
  `docs/adr/` is retired to a tombstone.
- **Still open:** none for this plan's implementation audit.
- **Routed to:** the Stage 0 decision entry → `16-beta.1.md` chapter;
  state/scheduling → "Release beta.1" sub-issues.
- **Lessons:** root README/CONTRIBUTING and checker fixtures are consumer docs
  too; include them in future cutover greps, not only `docs/`, `AGENTS.md`, and
  `.agents/`.
