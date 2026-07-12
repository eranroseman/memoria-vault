# alpha.15 → BORROW / ADAPT / REJECT

*Memoria alpha.16 redo. alpha.15 is NOT sacred either. Facts-only: borrow only
what a documented failure, research, or a verifiable fact earns AND the mission
serves; adapt where the form is wrong or refuted; reject what is carried on
ADR-authority with no surfaced failure, is refuted, or is an owner-endorsed
drop. Mission (grain of salt): help the user READ (accumulate/compile/curate)
and WRITE (compose/create), code+text as outputs. Sources as in the companion
file. 2026-07-05.*

## BORROW — earned by a documented failure or research, and mission-serving

1. **Meaning-only frontmatter; files own meaning, DB owns verdicts.** Earned by a documented failure: `check_status` in frontmatter meant "checking a note rewrote it, hand-edits forged status, and every consumer had to distrust the file it was reading" (DH 2086). Corollary: any in-file marker is display-only, never authority.
2. **No-write-time-oracle (`checked` ≠ approved).** Research SUPPORTS strongly — Jacobs 2021: human+ML (0.356) ≈ human-alone (0.357) ≪ ML-alone (0.667), and a wrong recommendation dragged the human *below* baseline (RR #1, L27, L105). Both lines converge here.
3. **Argument-topology gap analysis: two graphs (sources + notes) + saturation (a claim needs ≥1 support AND ≥1 counterpoint, ADR-79).** Research SUPPORTS: RR promotes contradiction/supersession tracking from feature to **precondition** for durable state (Memora, RR L33); Popper corroboration. Central to the mission's WRITE side and the owner's basic knowledge cycle. **beta.1's removal is not research-justified.**
4. **`note` claim/question mode + claim-context fields (temporal_scope, tense, qualifier).** Research **explicitly requires** it — TEMPO: a claim's truth is determinate only relative to temporal scope + tense; "require ISO temporal scope, tense, certainty/hedging, and originating section as first-class typed fields" (RR L21). beta.1 dropped it *against* the evidence.
5. **Hub as tag-membership (mechanical) + human salience (prose).** Research SUPPORTS the tabular/faceted form (Hearst: faceted beats spatial at scale, RR L23); checked-tag membership *is* that form. Descends from Memex/Luhmann/Karpathy (intellectual foundation, not ADR-authority). beta.1's total drop has no research basis.
6. **Per-field best-source-wins enrichment merge with provenance; references = DOI-deduped union.** Earned by a documented failure: an 867-entry spike + two red-team rounds proved each of S2/OpenAlex/Crossref incomplete (reference counts 151/129/146; ORCID present in OpenAlex, ~0 in S2) and rejected single-source (DH 2138). beta.1's single-source empty-field-fill departed from this with no new evidence.
7. **Catalog authority in SQLite (relational); compact citation-survival copy mirrored to `bibliography.bib`.** The catalog graph is relational by nature and derives from the bibliography; the keep-test is served by the `.bib` projection. beta.1's markdown-authority reverts the spike-grounded ADR-124 (owner R-4/R-9).
8. **Shadow-first calibration DISCIPLINE** — no score changes routing/promotion/visibility until grounded on recorded dispositions; every tunable ships behind `production_enabled:false`. This *is* the owner's "the biggest pitfall is a synthetic index with a threshold" guardrail, and research SUPPORTS it (every threshold in the corpus was un-validated; RR throughout). Borrow the *discipline*, not alpha.15's specific un-validated constants.
9. **Read-API as the sole read path + enqueue-only writes + per-agent read scoping.** Safety architecture; research-supported (lethal-trifecta / exfiltration; RR §5). 
10. **Quarantine-and-verify: any change (human/agent/machine) is non-consumable until verified.** The owner's structural-integrity model (integrity = graph integrity; verification triggered by any change). Safety-serving. *Adapt the verification target — ADAPT-4.*
11. **Untrusted-input sealing** — raw source text never interpolates into an instruction template; a manifest violating this fails to load (DH 2144). Research SUPPORTS (injection; sealing narrows the channel).
12. **Deterministic edge extraction** — explicit typed body links → unchecked candidate edges; argument edges (`supports`/`contradicts`/`extends`) never auto-promoted (DH 2146). Research SUPPORTS: auto-typing bare links corrupts the argument graph, and NLI/contradiction auto-writes are refuted (RR §2).
13. **Seeded-error operation test + eval harness (diagnostic, never gates).** Engineering discipline serving testability and the feedback bar (DH 2194).
14. **Semantic Scholar as a conditional, default-on-when-keyed provider** (reference union, citation intents) — enrichment value; research-neutral; owner R-17. Gate on key feasibility.

## ADAPT — keep the mechanic, change the form (the form was wrong or refuted)

1. **Two-tier demotion propagation over the derivation graph** — keep the *stale-vs-invalid cascade* (earned build-system lesson: one demoted node must not flood a whole subgraph; DH 2126) — it **is** the structural-integrity propagation the owner's model wants — and **add** beta.1's snapshot/revert for reversibility. They are complementary, not substitutes. *(Corrects beta.1's regression of dropping the cascade.)*
2. **Gap severity {0,1,2} ordinals + saturation band** → keep the argument-topology, but express saturation as **honest coverage reasoning** (which claims lack a counterpoint, which lack support), not a synthetic score/band. Grounded in the owner's anti-synthetic-index guardrail + the charter's aggregate-score exclusion + "saturation cannot be pre-registered as a number."
3. **Hub / argument-graph rendering** → tag-membership + prose is the **default** (Hearst: faceted beats spatial; ADR-103 rejected spatial-at-scale, RR L23); a **JSON-Canvas / spatial map is an analyst-only, small-graph option that must beat a tabular baseline** (owner R-11's canvas, scoped by the evidence).
4. **Verification of a change** → from alpha.15's semantic check-suite toward the owner's **graph-integrity** verification (links/anchors/references resolve; structural, not per-node semantic validity). Reinforced by research: single-node semantic checks are unreliable (NLI recall .38, κ=0.68; RR §2, §5).
5. **Typed authored links {supports, contradicts, extends}** → keep as the **argument substrate** (human-authored edges for the project argument graph), but retrieval/synthesis runs on **BM25+dense, never graph traversal** (MemoryAgentBench: graph underperforms BM25 for synthesis; RR L51). Typed edges are the argument layer, not the retrieval representation.
6. **Controlled-vocabulary / faceting** → borrow the topics/faceting substrate (owner R-13 needs topics for discovery; faceted navigation is the validated form) but **machine classification is enrichment-only + human-certified** — no machine-materialized frontmatter facets.

## REJECT — carried on authority, refuted, or an owner-endorsed drop

1. **`spaces/` + `_nav` Navigator + three-places model + Maintenance cadence** — carried on ADR-101/114/116 authority with **no surfaced failure** (inventory flag). The workspace/navigation design is an **open task** the owner's notes richly re-open (gates, deep-vs-task-oriented work, left-pane nav / right-pane Co-PI). Reject the carried model; redesign the workspace from job-to-be-done requirements. *(beta.1's 5-surface model is also not adoptable on authority — both are inputs to a fresh workspace design.)*
2. **Closed reject-undeclared frontmatter validation + `x.*` namespace** — not earned by any documented failure; OKF-permissive tolerance judged "more idiomatic" (RR R6). Stay permissive/tolerant. This is the one place beta.1's looser stance is the better-grounded call.
3. **ULID as an identity scheme "because ADR-126's principle"** → reject the *authority* justification, but **adopt a stable `work_id` (ULID-class)** grounded in the **fact** that citekeys mutate (Zotero re-export; owner R-1). Same mechanism, fact-based reason.
4. **`work interview` elicitation step** — owner-endorsed drop (R-16: a wiki-LLM concept the ZK layer covers); no research either way. Reject, pending the read/write-flow design.
5. **`steering.md` + "The Librarian" persona + separate priority-weighting file** — owner-endorsed drop (R-14: redundant with the project research-question); the priority function lives inside the project question, not a standing file.
6. **Tier-2 LLM tension judge** — research is skeptical of LLM-judge-on-this-path (CiteGuard recall 16–17%; ConCoRD ~28% wrong belief-flips; RR §2, L67); alpha.15 already constrained it to proposer-never-authority, and beta.1 dropped it. Keep contradiction surfacing on the **local NLI proposer** only.

## Cross-cutting note

The BORROW list is dominated by the **WRITE / knowledge-production side** — argument graph, claims-with-context, hubs, gap-over-both-graphs, faceting. These are exactly what beta.1 deferred and what the mission ("write: compose/create new knowledge, code+text as outputs") centers. The research does **not** justify their removal; in several cases (TEMPO claim-context, Memora supersession-as-precondition, the 867-spike enrichment) it **requires** keeping them. This is the concrete answer to "was the dismissal research-justified": **no** for the production core; **yes** only for the retrieval-unit (verbatim span over atomic) and the no-graph-retrieval calls, which beta.1 got right.
