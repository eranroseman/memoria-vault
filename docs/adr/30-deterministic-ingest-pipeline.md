---
topic: decisions
id: 30
title: Tiered ingest pipeline (capture → fallback-chained enrichment → gated write)
nav_exclude: true
status: superseded
date_proposed: 2026-06-03
date_resolved: 2026-06-03
assumes: []
supersedes: []
superseded_by: [129]
---

# ADR-30: Tiered ingest pipeline

> **Status note (0.1.0-alpha.15):** superseded by
> [ADR-129](129-layered-machine-judgment.md). Kept for decision history;
> current architecture is carried by the consolidation ADR. Obsidian MCP,
> cron/sweep, and adapter delivery references below are historical and not
> alpha.15 implementation scope.


> *Terminology note (0.1.0-alpha.12): `captured` is now the `ingest_status: tier0`
> floor, **not** a read-state value, and the retry sweep keys on `ingest_status`.
> Concept homes and `check_status` are owned by
> [ADR-119](119-schema-driven-document-creation.md). The pipeline decision below is
> unchanged.*
>
> **Schema note (2026-06-16).** `ingest_status` is a paper-scoped enum, not an
> implicit pipeline scratch field. The schema owns the legal values
> (`tier0`, `enriched`, `complete`, `needs-human`) and Operations must write only those
> values.

> **Alpha.14 standalone note.** [ADR-124](124-standalone-catalog-citation-authority.md)
> supersedes the Zotero-primary intake assumptions below. The deterministic ingest
> spine remains the decision; Zotero is now one optional exported-file input, and
> the standalone catalog/database is the citation authority.

> **Implemented and validated live (#100–#116).** The deterministic spine ships as
> six scripts (`ingest_paper` / `resolve_merge` / `extract` / `link` / `pipeline` /
> `sweeps`) plus the seeded `00-meta/vocabulary.md`, the `captured` + `ingest_status`
> schema, and the two re-ingest sweeps on cron. One correction to the design below:
> the Librarian's capability allowlist ([ADR-120](120-profile-config-materialization.md))
> disables `code_execution`, so the
> pipeline is reached as an **MCP tool** (`ingest_pipeline`, `mcp/ingest_mcp.py`), not
> a script the worker runs — the agent still makes only the two judgments and writes
> through the gated obsidian MCP. A real paper ingested end-to-end on installer-deployed
> lanes (vocabulary-constrained classify + `[!brief]` + ID-keyed entity links + gated
> writes → `review_status: requested`); the Tier-1 merge is grounded by the 867-paper
> spike. Tracked in the 0.1.0 release plan as G10.

> **Verified on-box 2026-06-21 (partial — the tag-suggestion layer is absent).** The
> deterministic spine above is real, but the embedding/zero-shot **tag-suggestion layer**
> that this ADR frames as Tier-1's value is **not built**: `classify` intentionally runs a
> deterministic OpenAlex-topic mapping, and the full-text chain ships only Unpaywall → PMC →
> local PDF. The "Implemented and validated live" callout applies to the spine, not to the
> full Tier-1 value layer. Treat tag suggestion, S2ORC/CORE/arXiv/OCR extraction, and Tier-2
> NLI/code-repo enrichment as deferred follow-up work unless a later ADR or issue implements
> them.

## Context

Capture → ingest is the system's primary source intake path. Earlier designs
started from Zotero selection capture, but alpha.14 starts from the standalone
CLI/runtime: portable BibTeX, CSL JSON, exported Zotero item files, DOI/ISBN/URL
captures, and PDF/file captures all enter the same catalog path. The existing
`obsidian-paper-note` skill is **fully LLM-orchestrated** — costly,
non-reproducible, and fragile (its PDF dependency `ocr-and-documents` currently
fails to install) for work that is overwhelmingly mechanical.

Two things make a redesign tractable: a **free, programmatic scholarly-API layer** (Semantic Scholar, OpenAlex, Crossref, PubMed/PMC, arXiv, Unpaywall, CORE) lets enrichment be built as **fallback chains** rather than a single dependency; and **lightweight tooling** (`pymupdf4llm`, embedding retrieval over the user's own tag list) covers the rest without heavy local ML. The hard requirements: every write **gated and audited**; **nothing captured is ever lost**; robustness **by redundancy**.

This ADR was hardened across **two adversarial red-team rounds** and grounded by an **empirical spike on the user's 867-entry library**. The corpus is genuinely heterogeneous — 436 articles, 166 conference papers, 111 preprints, 53 chapters, 49 software, 48 books; 737 DOIs (641 Crossref-registered, 96 arXiv), 283 arXiv/eprint, 117 PMCID, 228 ISBN; mostly CS/ML/HCI with a real biomedical slice. That heterogeneity, and what the spike found about multi-source disagreement, drive the design below. The result is **one pipeline in three tiers** — a guaranteed local floor, a reliable fallback-chained standard layer, and optional extras — so a failing extra cannot break the core, because the core never depends on it.

## Decision

Memoria ingests a source through **one pipeline, three tiers**, with two ordering
invariants — **capture commits first** and **scriptable-before-LLM** — and gated
writes only. Zotero export import is an input adapter, not a separate pipeline or
required fast path. The deterministic spine is a standalone runtime operation;
adapters call it rather than owning ingest semantics. Machine writes go through
the trusted runtime writer and policy checks — no raw filesystem writes.

> The "scriptable" tiers are **stable-ish, not bit-deterministic** — API, embedding, and OCR outputs drift across versions and over time; pin model/API versions.

### Tier 0 — Guaranteed (local, must succeed → `lifecycle: captured`)

The floor: no network, no PDF, no ML; succeeds when the input payload contains
enough identity metadata to create a catalog row.

1. **Durability anchor first.** The runtime records the raw input payload and
   source-content blob before enrichment or markdown materialization. This is
   the true "nothing lost" anchor and does not depend on Zotero, Obsidian, or
   Hermes.
2. **Resolve identity + route by type** from the catalog/import payload: citekey
   alias, title, all author names, year, DOI/arXiv/PMCID/ISBN, venue, abstract,
   and the **entry type** → paper source, software/source item, or book/chapter
   handling. ~17% of the corpus is non-paper; the pipeline never forces a repo
   or a book into the paper-note shape.
3. **Build frontmatter** from the type's template — stable IDs, all authors recorded, classification fields empty.
4. **Gated write** to the catalog and derived Concept path, `lifecycle: captured`.

### Tier 1 — Standard (network, fallback-chained → *reliable*, not best-effort)

Each subsystem is a chain; the note gets the data if *any* source has it, degrading to Tier 0 only when all miss. **All sources are open access / free** — no subscription publisher APIs. Tier 1 carries the system's *value* (a Tier-0-only note is a near-empty stub); it is not safety-critical but it **is** correctness-critical, and the merge below is its hard problem — validate it on a real sample before relying on it (see Consequences).

**Resolve + merge — `S2 + OpenAlex` co-primary, `Crossref` for non-arXiv DOIs.** The spike showed these sources **disagree and are each incomplete** (reference counts for the same paper: 151/129/146, 107/32/95, 68/82/68 across S2/OpenAlex/Crossref; ORCID present in OpenAlex up to 14/paper but ~0 in S2). Therefore the merge is **per-field, best-source-wins, with provenance**, not whole-record precedence:

- authors + **ORCID** + affiliations ← **OpenAlex**; `intents` / `isInfluential` / `contexts` / `tldr` / `embedding` ← **S2**; canonical scalar metadata ← Crossref/OpenAlex.
- **references = the union across sources, deduped by DOI** (the keyspace the vault stores), since no single source is complete. The graph requires the **paginated `/paper/{id}/references` and `/citations`** endpoints — the **batch endpoint does not reliably return nested references** (empirically 7/21 papers), so this costs extra calls against the ~1 req/s budget; cache by DOI/CorpusId.
- Do **not** pair author sub-fields by index across sources (name forms and ordering differ); merge within a source, then reconcile by name+position+ORCID.
- These are **model/aggregator outputs, not ground truth** — only the ID matching is exact; intent/influence/contradiction signals are advisory.

**Conditional-by-ID enrichment** (each well-populated in the corpus): **PMCID** → PMC open-access full text (pre-extracted) + MeSH (PMCID→PMID via the NCBI ID converter); **arXiv ID** → arXiv full text + categories; **non-arXiv DOI** → Crossref references/metadata.

**Full text — pre-extracted first, parse last:** `S2ORC → CORE (by DOI) → PMC (PMCID) → arXiv (arXiv ID) → Unpaywall→OA-PDF → caller-supplied local PDF → pymupdf4llm → OCR`. Sources returning text already-extracted (S2ORC/CORE/PMC) are preferred — no local parsing, no untrusted-PDF surface. A supplied local PDF is the local floor when present. The OCR decision is the script's (a deterministic text-layer + coherence check; the coherence heuristic is **English-biased** — non-English papers must not be auto-misrouted). Empty/garbled extract is **flagged degraded**, not silently dropped; it does not abort the ingest.

**Tag suggestion — the kept NLP, domain-agnostic, over the user's tag set.** Tags are a **setup input**: the user seeds an initial vocabulary (tied to `steering`) that the system develops over time. Each tag should carry a **short definition/description** — a 1–3-word label embeds weakly; the definition is what makes similarity meaningful. Produce a ranked shortlist per dimension (**topic / methodology / research-type**) by combining: (a) **embedding similarity** between the paper text and each tag's *definition* (domain-agnostic — works across the biomedical + CS corpus; reuses the `qmd` stack); (b) optional **zero-shot classification** (one inference *per tag* — a real cost); (c) the API taxonomies (OpenAlex topics, MeSH for the PMCID slice, arXiv categories) as *additional* signal. The model ranks existing tags; it never invents one.

**Classification proposal (LLM call #1) — promotes `captured → proposed`.** Map the shortlist to `_proposed_classification`, **hard-schema-constrained** to the vocabulary. Extracted document text is **untrusted input** (delimited, instructions stripped, schema-constrained) — see Security.

**Linking (ID-keyed, idempotent).** Find-or-create `venue-note` (ISSN), `person-note` (ORCID), `organization-note` (ROR), keyed on stable IDs. **No-ID entities are recorded by name in the paper-note, never node-created, never name-merged** (venues/orgs as well as authors). Cites/cited-by via local **DOI-match** of the merged reference union against the vault; annotate edges with `isInfluential` / `intents` / `contexts` where S2 supplied them.

### Tier 2 — Optional (best-effort; absent-able)

- **`[!brief]` comparative narrative** (LLM call #2) over deterministically-selected neighbors.
- **NLI contradiction signal** — *advisory, low-precision only*; a hint for the brief, never a fact.
- **arXiv → code-repo** (Papers-with-Code / confidence-thresholded) → `item-note` + cross-link; proposed when uncertain.

### Lifecycle

Adds one value, **`captured`** (today `lifecycle` is `proposed · current · dormant · archived`). The classification proposal is the only thing separating `captured` from `proposed`; everything else is enrichment present in either state.

- **paper-note:** `captured` (Tier 0) → `proposed` (classification proposal) → `current` (human).
- **entity notes:** created at `proposed` during Tier-1 linking → `current` (human, lazily) — the existing entity lifecycle, no new track.
- **terminal floor:** after bounded failed re-ingest attempts, `captured` + `ingest_status: needs-human` so the retry-sweep stops and the human is surfaced.

### Reliability, re-ingest, serialization

The capture-intake log + the `captured` stub mean a failure anywhere in Tiers 1–2 **leaves the note at `captured`** — recoverable, nothing lost. This supersedes the old "materialize a `capture-timeout` candidate" idea for the *deliberate-capture* path. There are **two distinct backstops, with distinct owners**:

- **(a) log-reconciliation** — a pass that reconciles `capture-intake.jsonl` against created notes and re-drives any entry whose **Tier-0 stub never landed** (the durability anchor for a failed first write).
- **(b) captured retry-sweep** — re-runs **Tier 1** on `captured` notes whose enrichment failed, with backoff and the `needs-human` floor.

Re-ingest is **idempotent in writes** (ID-keyed find-or-create makes no
duplicates) but **not stable in output** (refreshed APIs/vault → refreshed
enrichment). Find-or-create safety requires **serialized writes**. Therefore
**all re-ingest (manual command included) is enqueued through the runtime task
queue**, never run as an ad-hoc adapter session, so a manual re-ingest cannot
run concurrently with sweep (b) and race find-or-create. (Equivalently, a
per-citekey/per-entity lock; routing through the queue is the chosen mechanism.)

### Security (untrusted ingest surface)

The gate bounds *where* writes land, not their *content*. So: local PDF/OCR parsing runs in a **subprocess with CPU/memory/time `rlimit`s and a temp working dir** — not in the worker's main process (MuPDF has a CVE history); pre-extracted API text (S2ORC/CORE/PMC) is preferred precisely because it avoids local parsing, leaving only the local-PDF floor as the residual untrusted-parse surface. For prompt injection: **classify (LLM #1) is hard-schema-constrained**, so a crafted PDF/abstract cannot steer the typed field. The **`[!brief]` (LLM #2) is free-text and *not* schema-constrained** — instruction-stripping is unreliable, so a crafted abstract/neighbor can steer its prose; this is a **lower-stakes, human-reviewed, acknowledged residual** injection surface, not one the schema defense covers.

### Cost / latency (per ingest)

Tier 0 is effectively free (local). Tier 1 is a handful of HTTP calls — the merge chain **plus** the paginated `/references` fetch (the graph is not free in the batch) — one local embedding pass, an optional **per-tag** zero-shot pass, and **one** schema-constrained classify call. Tier 2 adds at most **one** larger `[!brief]` call. The cost moves off the old 8-step LLM loop into cheap HTTP + a reused embedding model; the additions the first estimate omitted are the `/references` calls and per-tag zero-shot.

### Future options

Subscription publisher APIs are deliberately out of scope (open-access full text via S2ORC/CORE/PMC/arXiv/Unpaywall covers the OA slice). Deferred: heavier domain NLP (scispaCy, an RCT/PICO classifier) only if the embedding/zero-shot tag layer proves insufficient; the S2 Recommendations API and `/snippet/search` for discovery; additional adapter transports once the standalone CLI/runtime path is complete.

## Consequences

- **Robust by redundancy.** No single API is load-bearing for *safety*; the Tier-0 floor guarantees a valid note offline / for an unindexed paper / with no PDF.
- **But Tier-1 correctness is owed.** The fallback chains traded a single-API risk for a **multi-source merge** risk — the spike confirmed the sources disagree, so the merge (per-field best-source; reference union deduped by DOI) is the now-load-bearing piece and **must be validated on a real sample** of the vault's papers before the system is trusted to enrich correctly. The merge is grounded by an n≈22 spike here; a fuller pass is a build-time gate.
- **The "no extra call" linking claim is retracted** — the citation graph requires the paginated `/references` endpoint, costed above.
- **Heterogeneity handled.** Type-routing (paper/item/software/book) + by-ID conditionals (PMCID/arXiv/Crossref) match the real corpus; books/software degrade to metadata-only rather than breaking.
- **Domain-agnostic tagging.** Embedding/zero-shot over the user's defined tag set works across biomedical + CS, where a MeSH-only crosswalk would be empty for most papers.
- **Nothing lost, everything gated** (un-gated capture-intake log as the anchor; every note write audited); honest determinism (idempotent writes + board-serialized re-ingest, not identical output).
- **Cost — a real rewrite.** `obsidian-paper-note` slims to "run the script, judge, write"; `ingest_paper.py` must be built and tested, with the merge logic, structured-output contracts, and explicit edge-case branches (type routing, no-DOI/PDF, OCR fallback, no-ID entities, non-English text).
- **Constraint — lifecycle.** Adds `captured` (+ `ingest_status: needs-human`) and changes the deliberate-capture dead-letter to "stays `captured`"; docs describing the LLM-orchestrated ingest must be updated.

## Alternatives considered

- **Single-source (S2-only) enrichment.** Rejected: rests on one API's coverage and ML outputs; the spike showed each source is incomplete, so fallback chains + a union graph are required.
- **Split into two ADRs (spine + spike-gated enrichment).** Rejected for **three tiers in one ADR**: defining enrichment as reliable-but-non-load-bearing-for-safety makes approving the whole safe without a multi-step project — but the Tier-1 *validation* the split would have forced is preserved as a build-time gate.
- **A separate Zotero capture+ingest pipeline.** Rejected: Zotero export import is just one input adapter; a Zotero-specific pipeline duplicates the standalone ingest path and drifts.
- **Deterministic work at capture (in adapter glue).** Rejected: thickens glue the control plane keeps thin, bypasses the gate, and blocks the capture UX on slow PDF tooling. The spine runs in the runtime operation.
- **`candidate-note` as the universal capture record.** Rejected: "awaiting decision" mismatches a deliberate capture, plus happy-path churn. The capture-intake log + card commit the capture; the candidate stays for leads/dead-letters.
- **A `derived` lifecycle track for entities.** Rejected: entity notes already use `proposed → current`.
- **GROBID / Marker as the default extractor.** Rejected: heavy and (Marker) currently failing to install; pre-extracted API text + `pymupdf4llm` cover the common case, OCR/Marker only for scanned/equation-heavy PDFs.
- **Keep the LLM-orchestrated ingest.** Rejected: non-reproducible, costly, fragile for mechanical work.

## Related

- **Workflows affected:** [Capture and ingest a source](../how-to-guides/library/capture-and-ingest.md), Obsidian command palette.
- **Files affected:** ingest runtime operation (source of truth for API field lists, chain order, and merge rules — kept out of the ADR so it can change without re-deciding), [Ingest routing](../reference/ingest.md) (type routing, fallback chains, extraction tiers, S2-not-GROBID), [Frontmatter fields](../reference/frontmatter.md) / [Document types](../reference/document-types.md) (`captured` + `ingest_status`), optional adapter importers, the seed-tag vocabulary format (tags carry definitions).
- **Correction (delivery mechanism):** the worker **cannot run the pipeline as a script** — the Librarian's capability allowlist ([ADR-120](120-profile-config-materialization.md)) disables `code_execution`/`terminal`/`file`. The deterministic spine is therefore delivered as an **MCP tool** (`ingest_pipeline` on the `memoria-ingest` server, `mcp/ingest_mcp.py`, wrapping `runner.run()`), reached the same way vault access and the policy gate are. The tool reads + computes only; the agent still fills the two holes and writes through the gated obsidian MCP. (The CLI entry points remain for cron/sweeps and offline use.)
- **Related decisions / Depends on:** [ADR-120](120-profile-config-materialization.md), [ADR-28](28-write-gate-as-plugin.md) (the write gate), [ADR-16](16-systematic-review-adopt-on-demand.md).
- **Supersession note:** deliberate-capture dead-letters stay `captured` rather than materializing a `capture-timeout` candidate.
- **Source discussion:** design conversation + two red-team rounds + an 867-paper API merge spike, 2026-06-03.
