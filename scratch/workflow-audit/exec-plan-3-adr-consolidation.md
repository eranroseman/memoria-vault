# ExecPlan 3 — ADR consolidation and inflation prevention

Shrink the ADR log from ~90 files to ~27 by the owner's rule — *an ADR is kept
only if it carries unique, still-needed decision information found nowhere
else* — then remove the structural cause of the inflation so it cannot
re-accrue. **No renumbering** (recorded reason below). **Beta.1 is out of
scope.** The 4 `rejected` ADRs are kept untouched.

## 0. Metadata

- **Task:** Execute the ADR-absorption audit (90 → ~27) and land the one
  mechanism that prevents re-inflation. Waves are small PRs off `main`.
- **Worktree / branch:** `~/mv/adr-consolidate` · `fix/adr-consolidation` off
  `origin/main` for the repo edits; this plan lives on the `scratch` branch
  under `scratch/workflow-audit/`.
- **Related:** the absorption audit (per-ADR verdicts, run 2026-07-04;
  full report kept in the run's scratchpad, not the repo); the ADR-only
  decision model (AGENTS.md "ADR template" / "Work routing"); the six
  consolidation ADRs 125–130 as the absorption anchors.
- **Related issues / milestone:** — (open one per wave when work starts;
  milestone 0.1.0-alpha.16).
- **Started:** 2026-07-04 · **Last updated:** 2026-07-04

## 1. Purpose / big picture

The ADR log holds ~90 files; 52 are `superseded` full-body tombstones — ~290 KB
of agent-greppable stale decision prose that shadows the live SSOT (an agent
greps a topic and lands in a retired decision's body, which `nav_exclude` hides
from humans but not from `grep`). The cause is structural, not a discipline
lapse: AGENTS.md currently makes the ADR log "the single home for every
decision, at any lifecycle status" — accumulate-by-default, plus supersession
that mints a new ADR without removing the old one. Given design churn, that
guarantees the pile.

This plan does two things: (1) delete what carries no unique value (the audit's
62 removals), moving any un-absorbed content into its successor first; (2)
change the default from *accumulate* to *self-prune* with **one mechanism**, so
the pile cannot rebuild.

The deeper option — replacing numbered immutable ADRs with living
decision-area docs — is a **pending decision, deferred from this plan**. The
shrink here is a prerequisite either way (you delete the tombstones regardless),
so nothing here forecloses it.

## 2. Context and orientation

- **Corpus (origin/main):** 26 accepted, 8 proposed, 4 rejected, 52 superseded.
- **Audit result:** ~27 survivors — the six anchors (125–130), 11 genuinely
  distinct accepted (11, 20, 24, 62, 64, 99, 101, 105, 122, 123, 124), 6
  forward-looking proposed (16, 88, 91, 92, 96, 107, 108 — one of these spans
  two reasons; count is 23 from the audit + the 4 rejected = 27), plus the 4
  rejected kept as-is.
- **Removals (62):** 50 clean deletes, 2 conditional move-then-delete, 5
  fold-into-anchor, 5 relocate-to-AGENTS.md.
- **Guardrail from the audit (do not violate):** never dissolve 125–130 (they
  are the absorption targets); 129 is the highest mega-ADR risk (multiple folds
  route into it — land each as a single bullet, not a feature catalogue); do
  not fold 123 into 129 (its capture-vs-promote gate is unique).
- **Reference reality:** ~1,200 `ADR-NN` references across 169 files. Most live
  in `docs/adr/` frontmatter (deleted *with* the tombstones) or in survivors'
  cross-refs (which stay valid — we are **not** renumbering). Only refs from
  `src/`, `tests/`, AGENTS.md, and docs prose that point at a **deleted** ADR
  need repointing to its successor; that is a per-wave step.

## 3. Plan of work (waves)

Each wave is one PR; each is independently revertible; each leaves `main` green.

- **Wave A — clean deletes + machinery cleanup.** Delete the 50 fully-absorbed
  superseded ADRs. Remove the referential machinery that pointed at them (the
  `supersedes:`/`superseded_by:` frontmatter on survivors, the index arrows).
  Repoint any `src/`/`tests/`/AGENTS/docs reference to a deleted ADR to its
  successor. Regenerate `docs/adr/README.md`.
- **Wave B — conditional move-then-delete (2).** Requires a human confirm of
  where the content lands before deleting; see §4.
- **Wave C — fold feature-ADRs into anchors (5), then delete.**
- **Wave D — relocate dev-process ADRs to AGENTS.md (5), then delete.**
- **Wave E — prevention (the point).** Retire `superseded` as a status and add
  the CI mechanism that makes supersession *delete-not-archive*; remove the
  harmful "at any status" doctrine clause.

## 4. Concrete steps

### Wave A — clean deletes (50)

Delete these files; their load-bearing content already lives in the named
successor (git retains the originals):

```
03→128  05→124  07→125  09→129  10→129  15→126  19→126  21→128  22→125  23→125
25→127  26→125  28→125  30→129  31→130  32→125  33→125  35→125  38→129  41→128
43→125  46→125  48→125  49→122  52→126  53→125  54→128  55→125  56→129  57→128
66→129  69→125  72→130  74→125  77→126  79→126  80→125  83→126  100→126 102→130
104→127 109→130 112→130 114→130 115→130 116→130 118→130 119→126 120→125 121→130
```

Then, in the same PR:
1. Remove `supersedes:`/`superseded_by:` frontmatter lines that reference any
   deleted id from the survivors (mostly 122–130). The lineage note, if wanted,
   is one prose line in the successor ("consolidates the earlier decisions on
   X; see git history") — not a live file-pointer.
2. `git grep -nE 'ADR-(03|05|07|…|121)\b'` across `src/ tests/ AGENTS.md
   docs/` (excluding `docs/adr/` frontmatter being deleted) → repoint each to
   the successor id, or delete the reference if it was pure lineage.
3. Update `scripts/gen_adr_index.py` (and `tests/test_gen_adr_index.py`) so it
   no longer expects superseded rows/arrows; regenerate `docs/adr/README.md`.

### Wave B — move-then-delete (2, conditional)

| ADR | Confirm before deleting | If confirmed |
| --- | --- | --- |
| 06 (citekey convention) | Is the concrete citekey *shape* (`authoryearword`, the BBT `shorttitle(1,0)` trap, pin-key-before-export) already in the ingest reference or ADR-124? 124 carries alias-vs-key semantics but **not the format**. | If missing, move the format spec into 124 (or the ingest reference), then delete 06. If already present, clean-delete. |
| 14 (advisor live-citation export) | Did the live-citation Word round die with Zotero+BBT authority (which 125 drops)? | If moot, clean-delete. If still in scope, move the distinct-artifact + failure-modes (lpeg-on-Windows, first-open .docx corruption, pick-editor-first) into 126 or a live export-routes reference, then delete 14. |

### Wave C — fold feature-ADRs into anchors (5), then delete

Land each as a **single bullet** under the target anchor's existing section,
then delete the source ADR:

| Fold | Into | One-line decision that lands |
| --- | --- | --- |
| 12 | 130 | single-frontmatter-authority / no second formatter in audited zones |
| 93 | 129 | tag candidates via deterministic phrase pass, cards-not-tags, KeyBERT/YAKE deferred (shadow-first, #706) |
| 98 | 126 | expand authored `links:` vocabulary one value at a time, validated-not-inferred |
| 90 | 129 | claim-sentence pre-classifier narrows candidates before LLM proposal, never decides (shadow-first, #703) |
| 94 | 129 | deterministic ID/name-collision dedup routes to attention, never auto-merges |

Guardrail: 129 must not become a feature catalogue — one bullet each under its
existing proposer/shadow-first section.

### Wave D — relocate dev-process to AGENTS.md (5), then delete

These record contributor tooling, not product invariants — they belong in the
lifecycle-free AGENTS.md, not the decision log:

| ADR | Relocate to (AGENTS.md section) |
| --- | --- |
| 29 + 44 (testing tiers, L1-in-repo-tree) | Test-before-PR / testing conventions (move as a pair) |
| 73 (doc source-link + ADR-link conventions) | Writing docs |
| 75 (GitHub Project + release-please usage) | Work routing / Release process (durable homes already in `.agents/playbooks/release.md` + CONTRIBUTING.md — reference, don't duplicate) |
| 110 (ruff format owns layout, curated lint set) | Python style (preserve the rejected-alternatives rationale) |

125 already records 29/44/64 as "not superseded"; relocating 29/44 keeps that
survival fact in 125 while the how-to moves. 64 stays an ADR (platform decision).

### Wave E — prevention (one mechanism, minimal prose)

The real prevention is structural, not a rule:
1. **Drop `superseded` from the ADR status enum** (`gen_adr_index.py`
   `ADR_STATUSES`), leaving `proposed | accepted | rejected`.
2. **Add a required doctor check: no ADR file may have `status: superseded`.**
   This forces every future supersession to *delete the old file and carry its
   content into the new decision* — the corpus can only grow by net-new
   distinct decisions, so it is self-limiting.
3. **Remove** the AGENTS.md clause "ADRs are the single home for every
   decision, at any lifecycle status" — the rule that manufactured the pile.
   The owner's stated principle replaces it in one line: *an ADR is kept only
   while it carries a unique, still-needed decision; supersession deletes, git
   holds the original.*

Deliberately **not** added: a "don't put dev-process in ADRs" scope rule or any
other behavioral prose — Wave D just does the relocation; the mechanism plus
the removed clause carry the prevention. (If dev-process ADRs recur, that is a
judgment call, not a missing rule.)

## 5. Validation and acceptance

Per wave, before merge:
- `python scripts/docs_doctor.py docs` green (README membership + links).
- `python scripts/gen_adr_index.py` regenerates `docs/adr/README.md` with no
  diff after commit; `tests/test_gen_adr_index.py` passes.
- `git grep -nE 'ADR-0*(<deleted ids>)\b' -- src tests AGENTS.md docs ':!docs/adr'`
  returns nothing (every inbound ref to a deleted ADR was repointed).
- `scripts/verify pr` (source checks + evidence bundle) passes.
- Wave E: a deliberately-added `status: superseded` ADR makes the new doctor
  **fail** (negative assertion — the mechanism fires on the installed build).

Acceptance: ADR count ~90 → ~27; zero `status: superseded` files; no dangling
`ADR-NN` reference to a deleted ADR; the four `rejected` ADRs unchanged.

## 6. Idempotence and recovery

- Each wave is one squash PR, independently revertible; deletions are recoverable
  from git in full.
- Re-running a wave is a no-op (files already gone; frontmatter already clean;
  index regenerates identically).
- If a "clean delete" turns out to have un-absorbed content mid-wave, pull it
  into Wave B treatment (move-then-delete) rather than dropping it.

## 7. Deferred / out of scope (recorded so they are not re-litigated)

- **Renumbering survivors from 1** — rejected. Blast radius: ~1,200 references
  across 169 files (a large silent-error surface), plus **unfixable** desync
  from every git commit/PR/issue and external link that names an ADR number.
  An ADR number is a permanent identifier like a DOI; gaps are honest (they
  say "decisions were retired"), and contiguity is cosmetic. Not worth the
  damage.
- **Living decision-area docs** (replace numbered immutable ADRs with a small
  set of current-state area docs + a rejected-directions log + proposals-as-
  issues) — a pending design decision, deferred. This plan is a prerequisite
  either way.
- **The 4 rejected ADRs** (95, 97, 103, 106) — kept, untouched; a rejected
  ADR's body is unique current-true "we killed this, here's why" guidance.

## 8. Progress

- [ ] Wave A — clean deletes + machinery + ref repoint + index regen
- [ ] Wave B — 06, 14 move-then-delete (after confirm)
- [ ] Wave C — fold 12/90/93/94/98, delete
- [ ] Wave D — relocate 29/44/73/75/110 to AGENTS.md, delete
- [ ] Wave E — retire `superseded`, add doctor, remove the "at any status" clause

## 9. Execution log

_(filled during execution — PR numbers, surprises, deviations)_
