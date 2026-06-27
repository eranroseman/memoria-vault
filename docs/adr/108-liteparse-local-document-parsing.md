---
topic: decisions
id: 108
title: LiteParse as the local document-parsing engine
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30, 32]
supersedes: []
superseded_by: []
---

# ADR-108: LiteParse as the local document-parsing engine

## Context

The tiered ingest pipeline ([ADR-30](30-deterministic-ingest-pipeline.md)) prefers
pre-extracted full text (PMC, S2ORC, CORE, arXiv) and falls back to parsing a local
Zotero PDF, with OCR as the last resort. The local-parse tier uses `pymupdf4llm`,
which wraps PyMuPDF. Two properties of that choice are worth revisiting:

- **License.** PyMuPDF is **AGPL-3.0** (dual-licensed commercial). Memoria ships it
  in the deterministic ingest stack, which is the strictest license obligation in
  the dependency set.
- **Parse surface.** ADR-30 already isolates the parser in a subprocess with
  `rlimit` caps because MuPDF has a CVE history; the C parsing surface is the
  reason the sandbox exists.

[LiteParse](https://github.com/run-llama/liteparse) (LlamaIndex, released March 2026)
is a **Rust**, **Apache-2.0** document parser that runs entirely local — no cloud,
no LLM, no API key — and emits Markdown with spatial layout, bounding boxes, and
built-in Tesseract OCR. It parses PDF plus DOCX/XLSX/PPTX and PNG/JPG, and ships a
Python binding. Its design statement is nearly a restatement of
[ADR-30](30-deterministic-ingest-pipeline.md) / [ADR-32](32-external-access-over-mcp.md):
offline, deterministic, no model in the loop. This is the opposite of GROBID/Marker,
which ADR-30 rejected as too heavy.

Because LiteParse would live in the self-hosted ingest tier (a library dependency of
`extract.py`, run as an MCP tool), not as an agent capability, it does not touch the
MCP-only sandbox boundary.

## Proposal

Memoria may replace the `pymupdf4llm` + OCR fallback in the ingest
full-text extractor (`extract.py`) with
LiteParse, keeping the existing subprocess `rlimit` sandbox, lazy import, and
extraction-coherence checks (≥200 chars/page, ≤2% replacement chars). LiteParse's
DOCX/XLSX/PPTX support would also be the parsing substrate if Memoria later admits
office-document source types.

This is **deferred, not adopted**. The local-parse tier is a last-resort fallback
(most full text arrives pre-extracted), so the upside is bounded and does not justify
betting the deterministic spine on a library with no track record.

## Consequences

- Drops the only AGPL dependency in the ingest stack for an Apache-2.0 one.
- Replaces a C parse surface (MuPDF CVE history) with a memory-safe Rust core; the
  subprocess sandbox stays regardless, since Tesseract and the format parsers remain
  untrusted input.
- Adds office-document and real OCR capability the current tier lacks.
- Spatial-layout and bounding-box output is unused by today's text→markdown pipeline;
  it is latent value, not a current need.
- Takes a dependency on a young library (released March 2026) in a reliability-
  sensitive path.

## When this matters

Adopt when any of these trips, not before:

- LiteParse reaches a stable Python API with roughly 6–12 months of track record.
- The PyMuPDF AGPL obligation becomes a real constraint (relicensing, distribution).
- OCR / scanned-PDF quality becomes an actual ingest pain point.
- Memoria commits to office-document ingestion.

The trial gate is a head-to-head against `pymupdf4llm` on the real Zotero corpus,
scored by the existing coherence checks, before any switch.

## Alternatives considered

**Adopt now.** Rejected: the library is ~3 months old and the local-parse tier is a
narrow fallback, so the reliability risk outweighs the bounded gain.

**Keep `pymupdf4llm` indefinitely.** The default if no trigger trips, but it leaves
the AGPL obligation and the MuPDF parse surface in place.

**LlamaParse or other cloud parsers.** Rejected: cloud, API-key, and (for LlamaParse)
LLM-in-the-loop dependencies are incompatible with the offline-first stance of
[ADR-30](30-deterministic-ingest-pipeline.md) and [ADR-32](32-external-access-over-mcp.md).

## Related

- **Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md),
  [ADR-32](32-external-access-over-mcp.md).
