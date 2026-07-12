---
topic: explorations
title: Ingest pipeline — one pipeline, three tiers, two model holes
status: historical
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 9
---

# Ingest pipeline — one pipeline, three tiers, two model holes

> **Historical (v0.1.0).** This note describes the pre-v0.1.1 ingest pipeline and is
> kept for design rationale only. The current sources are
> [ADR-30](../adr/30-deterministic-ingest-pipeline.md) and
> [Ingest reference](../reference/ingest.md).

A design capture of how a source becomes a vault note: the tiered deterministic
pipeline, the capture-first durability anchor, ID-keyed entity dedup, and the two
points where the Librarian (an LLM) makes a judgment. Reconstructed from the
ingest engine ([`vault/.memoria/engines/ingest/`](../../src/.memoria/engines/ingest)),
its MCP facade ([`vault/.memoria/mcp/ingest_mcp.py`](../../src/.memoria/mcp/ingest_mcp.py)),
and the [`catalog:enrich-record`](../../src/.memoria/profiles/memoria-librarian/skills/catalog-enrich-record)
skill. Implements [ADR-30](../adr/30-deterministic-ingest-pipeline.md),
[ADR-05](../adr/05-zotero-as-bibliographic-backbone.md), and
[ADR-06](../adr/06-citekey-naming-convention.md).

> **Why capture this.** Ingest is the deepest deterministic subsystem in the vault —
> five scripted stages plus an MCP wrapper — and the design that makes it durable and
> idempotent deserves a standalone view.

## What it is

One pipeline, three tiers, two ordering invariants — **capture commits first** and
**scriptable-before-LLM** — with **gated writes only**. The deterministic spine is
five stages (`pipeline.py` chaining `ingest_paper` → `resolve_merge` → `classify` →
`extract` → `link`), reached by the Librarian as an MCP tool (`ingest_pipeline`)
because the lane disables `code_execution`. The agent makes only two judgments;
every write goes through the gated obsidian MCP.

## How it works

### The three tiers

```
Tier 0  ingest_paper  → identity + route + captured frontmatter   (local, must succeed)
Tier 1  resolve_merge → S2 + OpenAlex + Crossref merged metadata + ref union
        classify      → research_area / methodology from the OpenAlex topics
                        (automated, audited, flag-on-ambiguity — D21/ADR-54)
        extract       → full text (PMC / local PDF), coherence-gated
        link          → entity find-or-create plan + cites edges   (network, fallback-chained)
Tier 2  [!brief] · NLI contradiction signal · arXiv→code-repo       (best-effort, absent-able)
```

- **Tier 0** is the floor: no network, no PDF, no ML. It resolves identity from the
  local `.bib`, builds frontmatter from the type template, and gated-writes the note
  at `lifecycle: captured` (`ingest_status: tier0`). It always succeeds when the
  citekey is in `memoria.bib`.
- **Tier 1** is *reliable*, not best-effort: each subsystem is a fallback chain, so the
  note gets a field if *any* source has it, degrading to Tier 0 only when all miss. The
  merge is per-field, best-source-wins, with provenance — authors+ORCID from OpenAlex,
  intents/tldr/embedding from S2, scalar metadata from Crossref/OpenAlex.
- **Tier 2** is optional and may be absent without affecting correctness.

### Capture-first durability

Before ingest runs, QuickAdd appends the raw selection to an append-only anchor log,
`system/logs/capture-intake.jsonl` (de-duped by citekey — the one un-gated write
the server makes). If the Tier-0 stub never lands, a log-reconciliation sweep re-drives
the entry. Re-ingest is **idempotent in writes** (ID-keyed find-or-create makes no
duplicates) but **not stable in output** (refreshed APIs change enrichment) — so all
re-ingest is enqueued as a board card, never run ad-hoc.

### Entity dedup by stable ID

`link.py` keys each entity path on its stable identifier, not its name:
`venue-note` ← ISSN, `person-note` ← ORCID, `organization-note` ← ROR. The same
ORCID/ROR/ISSN always resolves to the same file — find-or-create is idempotent.
No-ID entities are recorded by name in the paper-note and never node-created (never
name-merged). References are the union across sources, deduped by DOI (the keyspace
the vault stores).

### The two model holes

The pipeline declares exactly two gaps for the Librarian to fill
(`"holes": ["_proposed_classification", "brief"]`):

1. **Classification.** From the abstract / tldr / extract, propose
   `_proposed_classification` (`study_design`, `methods`, `topic`) using terms from
   [`system/vocabulary.md`](../../src/system/vocabulary.md) — prefer a defined
   term; only propose a new one (`provisional: true`) when nothing fits. The
   deterministic `classify` stage has already applied the mechanical part —
   `research_area` (and a `methodology` facet when derivable from the S2
   publication types) from the OpenAlex topics — so this hole is the judgment
   residue, not the bookkeeping. On landing, the note advances to
   `lifecycle: proposed`, `ingest_status: complete`.
2. **Comparative brief.** Using the shared `qmd` vector index (the similarity
   primitive the verify and map lanes also lean on — wired as the `qmd` MCP
   server in four profiles), select the top-5 most-similar sources and
   compose an "overlaps with / may contradict / new construct" `[!brief]` callout
   leading the note body. Bootstrapping the qmd index at install time is deferred
   ([#385](https://github.com/eranroseman/memoria-vault/issues/385)); the qmd
   pre-file similarity *ratchet* for claims stays a deferred decision
   ([ADR-38](../adr/38-pre-file-similarity-gate.md),
   [#370](https://github.com/eranroseman/memoria-vault/issues/370)).

### Calibrated thresholds (ADR-56)

Every numeric gate the pipeline applies lives in one drift-bound file,
[`vault/.memoria/schemas/calibration.yaml`](../../src/.memoria/schemas/calibration.yaml):

- `entity_resolution.confidence_floor` (`0.85`) — below it, cross-source identity
  disagreement raises an Inbox **near-tie flag** instead of a silent
  best-source-wins merge ([ADR-56](../adr/56-extraction-uncertainty-flag.md)).
- `classify.confidence_floor` (`0.6`) + `classify.near_tie_margin` (`0.15`) — a
  research area applies silently only when the best OpenAlex topic score clears the
  floor *and* beats the runner-up by the margin; otherwise the field stays unset and
  ingest raises one flag ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)).
  Every applied/flagged decision appends one audit line to
  `system/logs/classify.jsonl`, so the automation stays correctable.

A fuller calibration spec — grounding, error budgets, recalibration cadence for the
hybrid scores — is deferred:
[#379](https://github.com/eranroseman/memoria-vault/issues/379).

### External sources

Metadata: Semantic Scholar + OpenAlex (co-primary), Crossref (non-arXiv DOIs).
Full text, pre-extracted first, parse last:
`S2ORC → CORE → PMC → arXiv → Unpaywall/OA-PDF → local Zotero PDF → pymupdf4llm → OCR`.
Conditional by ID: PMCID → PMC full text + MeSH; arXiv ID → arXiv full text + categories.

### Bibliographic backbone

Zotero + Better BibTeX is the source of truth (ADR-05): every citable source has a
pinned BBT citekey before its note exists; `memoria.bib` is auto-exported and
read-only to the Librarian. Citekeys follow `authoryearword` —
`[auth.lower][year][shorttitle1_0]`, e.g. `mamykina2010sense` (ADR-06).

## Design rationale

- **Capture before enrich.** A network failure must never lose the source. Writing the
  Tier-0 stub (and the intake anchor) first guarantees the source is in the vault even
  if every enrichment API is down.
- **Scriptable before LLM.** Determinism is cheaper, faster, and reproducible. The LLM
  is contracted to the two judgments that genuinely need it; everything else is code.
- **Fallback chains, not single sources.** Bibliographic APIs disagree and are each
  incomplete; per-field best-source-wins with provenance beats whole-record precedence.
- **ID-keyed idempotence.** Keying entity files on ORCID/ROR/ISSN (not names) is what
  makes re-ingest safe — the same entity can't fork into two files, and there is no
  fragile name-matching.
- **Re-ingest is serialized.** Because output isn't stable across runs, re-ingest goes
  through the board, never an ad-hoc session — so two runs can't race the same note.

## Related

- [ADR-30](../adr/30-deterministic-ingest-pipeline.md), [ADR-05](../adr/05-zotero-as-bibliographic-backbone.md), [ADR-06](../adr/06-citekey-naming-convention.md), [ADR-17](../adr/17-shared-candidate-frontmatter.md), [ADR-54](../adr/54-two-decision-kinds-batch-worklists.md), [ADR-56](../adr/56-extraction-uncertainty-flag.md)
- [Classical method displacements](classical-methods-over-llm.md) — the classifier / NLI methods behind the holes
- [Schema and retrieval extensions](retrieval-and-schema-extensions.md) — the `_aspects` / paper-note schema the pipeline populates
- [Profiles and the SOUL model — one co-PI, four lanes, no orchestrator](profiles-and-soul-model.md) — the Librarian lane that drives it
- Reference: [`docs/reference/ingest.md`](../reference/ingest.md), [`zotero-plugins.md`](../reference/zotero-plugins.md)
