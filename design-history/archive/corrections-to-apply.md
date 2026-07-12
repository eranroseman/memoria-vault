# Corrections to apply to memoria-design-history-alpha.1-to-alpha.15.md

Confirmed by adversarial recheck (wf_03487b83-235). Apply each as a MINIMAL edit:
locate the anchor text at/near the cited line (line numbers may drift as edits are
made — locate by content), verify the corrected value against ground truth in
`/home/eranr/memoria-vault/main` before writing, then edit. Report old→new per item.

## APPLY (confirmed)

1. **L603 accepted count** — "48 accepted" → "46 accepted". (README ADR index at 0e9ed9dd: 46 accepted rows; 46+15+7=68 numbered ADRs.)
2. **L603 deferred count** — "13 deferred (ADRs 34, 35, 38, 39, 40, 41, 58, 59, 60, 61, 62, 63, 64, 65, 66" → change only the count "13" to "15" (the enumerated 15 numbers are already correct).
3. **L50 profile roster** — the clause asserting a seven-profile alpha.1 roster incl. "retriever-scout and one more" is wrong. alpha.1 (0e9ed9dd) ships FIVE: co-pi, engineer, librarian, peer-reviewer, writer. Reword to: the five shipped profiles, and if naming the earlier pre-consolidation *seven*-profile fleet, use ADR-02's set (librarian/mapper/socratic/writer/verifier/coder/linter). Drop "retriever-scout" (ADR-37, superseded by ADR-48, never shipped) and "and one more".
4. **L62 blockquote** — presented as a verbatim origin-notes quote but sentence 2 ("This approach prevented us from selecting optimal solutions for specific problems") is unattested in any source. Downgrade to paraphrase: remove the quotation marks / italic-quote framing and present it as a paraphrase (e.g. change the L60 lead-in and drop the `> *"..."*` quote styling), OR keep only the attested sentence 1 as a quote.
5. **L41 three "quotes"** — the three strings dressed as verbatim origin-notes quotes are paraphrases of the distillation. Remove the quotation marks (present as paraphrase). Substance is accurate; only the verbatim framing is loose. (Fidelity fix.)
6. **L478** — "A missing `task_id` is itself denied and audited (`request.no-task-id`)." → drop "and audited": a missing task_id is denied (rule `request.no-task-id`) but NOT audited (it returns before any append_audit; unlike a path-traversal deny, which is audited).
7. **L482** — the FAMA-exposure detector Borrow is attributed to why-pattern-provenance.md's ledger, but that file has no FAMA/obsolete-memory entry. Re-attribute the borrow to **ADR-10** (Memora/FAMA). Keep the detector claim; fix the source.
8. **L1344 (alpha.9)** — claim.md is described as a "new first-class template" with schema_version:2 / links.supports/contradicts / superseded_by introduced this version. Those fields PRE-EXISTED (present at alpha.7/alpha.8). Only change in the alpha.9 window: +30 lines adding the `[!suggestions]` callout + 4 QuickAdd buttons. Reword to "claim.md gains an action-oriented `[!suggestions]` callout + QuickAdd buttons"; drop schema_version:2/links/superseded_by as new (or note they are pre-existing fields the new write path now populates). Button names are correct.
9. **L1259 (alpha.8)** — "Retired/disposed all carried-forward tmp/ scratch across alpha.4-7 release folders (deletions under docs/releasing/0.1.0-alpha.{4,5,6,7}/tmp/; commits be840217, aa02089f, 2593076e)". Fix: the disposed scratch lived under **docs/releasing/0.1.0-alpha.8/tmp/** (files named for alpha 5/6/7 but in the alpha.8 tmp dir). Drop **2593076e** (not a deletion). Cite only **be840217** (#723) and **aa02089f**.
10. **L1288 (alpha.8)** — "ADR-74 ... accepted ... (commit 0bbfe1cf; ADR-74 diff)". 0bbfe1cf touches only ADR-100/76/84/README. ADR-74's deferred→accepted transition is commit **ffed6dab** (#687). Also note plugin-provenance-lock.json predates this cycle (created c79f659c, alpha.6). Fix the SHA; keep the design facts.
11. **L1308 (alpha.8)** — "ADR-83 Direct PI relate control accepted ... (commit 0bbfe1cf)". Correct SHA is **4f524fce** (#696) — NOT 0bbfe1cf and NOT 89588b3d. (Verify: `git show -s 4f524fce`.)
12. **L1444 (alpha.10)** — index type removal "index.yaml deleted, `24540227`/ADR-119". 24540227 is not a real revision. Correct SHA: **cb81a255** (#924, "implement updated ADR-119 schema contract"). The described deletions (index.yaml, index.md, folders.yaml index + notes/indexes skeleton) are correct.
13. **L1475 (alpha.10)** — superseded-claim filter "landed in `bafa92e2`/#851". bafa92e2 doesn't exist. Correct SHA: **baa92e61** ("fix(alpha9): filter superseded claims from qmd", #851). Subject/PR are right; only the SHA is wrong.
14. **L1540 (alpha.10)** — "seven old tutorials … replaced by **six** (01-orient … 07-make-it-your-own)". At 383034b0 there are SEVEN numbered tutorials (01-orient … 07-make-it-your-own). Change "six" → "seven".
15. **L1629 (alpha.11)** — "The type vocabulary collapsed from **27 types to 13**". The cited yaml glob yields 25→12 (src/.memoria/schemas/types/ at 383034b0 = 25 files; vault-template/.memoria/schemas/types/ at 1b24453b = 12). Change to "collapsed from **25 types to 12**" (19 removed + 6 kept → 6 added + 6 kept).
16. **L1768 (alpha.12)** — "driven by ... **four** disposable pre-implementation spikes whose **three FAIL** verdicts...". Internally contradictory: run_spikes.py has FOUR spikes, all PASS; the THREE FAILs come from alpha12-test-results.md which has SEVEN results (4 PASS / 3 FAIL). Reword to "seven disposable spike results (4 PASS / 3 FAIL, per alpha12-test-results.md)" OR clearly separate the four all-PASS run_spikes.py spikes from the seven-result test harness.
17. **L1770 & L1784 (alpha.12)** — the alpha.12 "design specifies … field-provenance … enrichment runs/tables" list. The design has NO 'enrichment' and NO 'field-provenance' (grep = 0). Drop those two items from the design-only list; keep the verified ones: entities, catalog_links, recursive-CTE cascade-rollback (+ journal-heads.jsonl anchor, Turso adapter).
18. **L1982 & table row L2056 (alpha.14)** — Zotero import surface removed in #1123 (7ad88a84) is listed as including `regenerate-ai-catalog.md`. #1123 deletes only capture-zotero-source.md. Drop `regenerate-ai-catalog.md` from both spots (it was RENAMED to regenerate-capability-index.md in #1066, unrelated to Zotero).
19. **L2012 & table row L2058 (alpha.14)** — skill-state.md "removed with the Obsidian payload #1124". It was removed in **#1119** (a3794fb6, "Remove installed profile runtime surface"), not #1124. Fix both spots. (136-line figure is correct.)
20. **L2082 (alpha.15)** — "work.yaml has `work_id` required, `citations`/`evidence_set` optional". work.yaml optional fields are only {aliases, archived, description, x}. Drop the "`citations`/`evidence_set` optional" clause (those were on the deleted digest.yaml). work_id-required is correct.
21. **L2138 (alpha.15)** — enrichment merge "PR-F #1173, `ingest_paper.py` +114". The enrichment code landed in **runtime/enrichment.py (~+133)**, not ingest_paper.py (+1). Fix filename + line count (PR #1173 / commit 82d0a6a9 is correct).
22. **L2172 & table row L2226 (alpha.15)** — "`calibration.yaml` **deleted**" / floors retired. The file SURVIVES at 5b1ea8bc with entity_resolution/classify/hybrid_scores intact; only the CLUSTERING section was removed (PR #1204). Change to "the clustering-config surface was removed from calibration.yaml (#1204)".

## DO NOT TOUCH (adversarial recheck overturned the flag — doc is correct)

- **L1466** — the `PROFILE_SCOPED_DIRECT_TOOLS = {"memory": {"memoria-copi"}}` constant IS real at the doc's cited commit 450f659d (policy_hook.py line 142). Leave as-is.
- **L1784 "SCHEMA_VERSION not yet externalized / schema.sql arrives later"** — recheck ruled ACTUALLY-CORRECT (schema inlined via executescript, no .sql file). Leave as-is.
- **§11/§2/§6 PR numbers #1158–#1162** — recheck ruled ACTUALLY-CORRECT; the SHAs are real and correctly attributed. Leave as-is.

## LEAVE (recheck overturned the verifier's proposed correction — needs no change / manual look)

- **L847 (both findings)** — the "fabricated #559–562" and "2026-06-16/ssl_verify" charges were themselves overturned (#559–562 DO appear in the finalized ExecPlan; the ssl_verify charge checked the wrong artifact). Do not remove #559–562. A residual imprecision may exist but is not pinned — leave unedited.
- **L869/L929 "16 command-palette commands"** — recheck overturned "no source says 16" (test-env.md does state 16). Leave "16" as-is.
