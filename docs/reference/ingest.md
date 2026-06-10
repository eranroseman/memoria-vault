---
title: Ingest routing
parent: Reference
---

# Ingest routing

The ingest engine ([src/.memoria/engines/ingest/](../../src/.memoria/engines/ingest)): the deterministic spine that turns a citekey into a draft paper-note bundle, the Catalog outputs it plans, the uncertainty floor, and the recovery sweeps. The Librarian reaches it over the ingest MCP ([src/.memoria/mcp/ingest_mcp.py](../../src/.memoria/mcp/ingest_mcp.py)) — its lane has no terminal — fills the two LLM holes, and performs the gated writes; the engine itself writes no vault notes.

---

## The pipeline

[src/.memoria/engines/ingest/pipeline.py](../../src/.memoria/engines/ingest/pipeline.py) chains four deterministic stages into a single **draft bundle**:

| Stage | Module | Does |
| --- | --- | --- |
| Tier-0 capture | `ingest_paper.py` | Identity + route + captured frontmatter from the local `.bib` alone — the offline, nothing-lost floor. |
| Tier-1 resolve/merge | `resolve_merge.py` | Semantic Scholar + OpenAlex (co-primary) + Crossref, merged per-field best-source-wins **with provenance**; references = the union across sources, deduped by DOI. |
| Tier-1 extract | `extract.py` | Full text, pre-extracted-first: PMC JATS → local Zotero PDF via pymupdf4llm. A deterministic coherence check (chars/page, replacement-char ratio, word ratio) gatekeeps so only good text reaches the model; non-English text is flagged, never auto-failed. |
| Tier-1 link | `link.py` | The knowledge-graph plan: entity find-or-create keyed on stable IDs (ISSN / ORCID / ROR — never name-merged) + cites edges by local DOI/arXiv match. |

The bundle arrives **with two holes** the Librarian fills: `_proposed_classification` (LLM #1) and the `[!brief]` comparative read (LLM #2). `ingest_pipeline(citekey, enrich=True, pdf_path="")` is the MCP tool; without `enrich` only Tier-0 runs.

### Catalog outputs

The link plan is what populates the Catalog ([ADR-52](../adr/52-links-vs-relationships.md)):

- **Entities** — find-or-create records in `catalog/` (`paper`, `person`, `organization`, `venue`, `dataset`, `repository`), keyed on the stable ID so same-named entities never merge. Entities without a stable ID are recorded by name only, never node-created.
- **Relationships** — the **given** edges on those entities (`cited_by`, `authored_by`, `published_in`, …), applied bidirectionally by the worker. Authored `links:` on notes are the PI's, never the engine's.

---

## The uncertainty floor (D51 / ADR-56)

The engine never merges identities silently ([ADR-56](../adr/56-extraction-uncertainty-flag.md)). `resolve_merge.py` scores **cross-source identity agreement** (title + year across the sources that resolved) in `[0,1]`; the floor comes from [src/.memoria/schemas/calibration.yaml](../../src/.memoria/schemas/calibration.yaml) (`entity_resolution.confidence_floor: 0.85`, drift-bound — recalibrate on model/source-version change).

Below the floor, the bundle carries a `flag_needed` block instead of a silent best-source-wins merge: the Librarian raises a **near-tie `flag` card** in the Inbox ("Identity disagreement on `<citekey>`", with the agreement score and the disagreements), and the PI decides. One source found = trusted (1.0) — the floor measures _disagreement_, not coverage.

---

## Derived artifacts

The ingest MCP persists the un-gated derived artifacts the agent can't:

| Artifact | Path | Notes |
| --- | --- | --- |
| Full-text extract | `.memoria/data/extracts/<citekey>.md` | Outside the Librarian's write lane; the paper note's `extract_path` points here (the `extract-path-broken` detector checks it). |
| Capture-intake anchor | `system/logs/capture-intake.jsonl` | One append-only line per capture, written **before** the gated note write — the durability anchor. |

---

## The sweeps

Two engines under [src/.memoria/engines/sweeps/](../../src/.memoria/engines/sweeps); neither writes the vault.

### Re-ingest backstops — `reconcile.py`

Re-ingest must be board-serialized, so each backstop is a detector that enqueues an **idempotent** re-ingest card (`hermes kanban create --idempotency-key reingest:<citekey>`); the board provides dedup, backoff, and the failure circuit-breaker (the `needs-human` floor).

| Pass | Detects |
| --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk (the Tier-0 stub never landed). |
| `--retry` | A `captured` note stuck at `ingest_status: tier0` (Tier-1 never completed). |

`--dry-run` reports without touching the board. The installer wires both as the `memoria-sweeps` cron, every 15 minutes.

### Retraction sweep — `retraction.py`

Deterministic, read-only retraction-by-DOI from three sources, most authoritative first: the local Retraction Watch CSV (`--refresh` downloads it to `.memoria/data/retraction_watch.csv`; monthly cron), the live Crossref `update-to` delta, and Open Retractions as a cross-check. `retraction.py --sweep --vault V` scans the Catalog DOIs and raises Inbox **alerts** on hits — flag-don't-fix; the engine never flips a note.

---

## Frontmatter written at ingest

| Field | Value |
| --- | --- |
| `type` / `lifecycle` | `paper` / per the universal chain — `proposed` until the PI classifies. |
| `citekey`, `title`, `doi`, `authors`, `year`, `venue`, `url` | From the merged record, with per-field provenance. |
| `relationships` | The given edges from the link plan. |
| `extract_path`, `pdf_uri` | The extract store path and the Zotero PDF URI. |
| `_proposed_classification` | The Librarian's proposal (LLM hole #1), promoted by the PI at classify. |

---

## Related

- The schemas and field kinds these notes must satisfy: [Frontmatter fields](frontmatter.md)
- The lane that runs the pipeline: [Profile capabilities](profiles.md)
- The crons that wire the sweeps: [Installer (bootstrap)](installer.md)
- The cards the sweeps and flags land in: [Kanban board reference](kanban-board.md)
