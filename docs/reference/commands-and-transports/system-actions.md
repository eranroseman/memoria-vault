---
title: System actions
parent: Commands and transports
nav_order: 1
grand_parent: Reference
---

# System actions

Every action the system can perform, with its performer. Three performer kinds:
**operations** (CLI/engine work, deterministic or runner-backed), **optional
adapters** (external surfaces that call the same engine), and the **PI** (CLI
commands and review decisions). Where a topic has its own reference page, that
page is authoritative for the details — this catalog is the map.

This page mirrors the source, not the reverse. Action implementation lives in
the referenced Python modules, capability manifests, and linked reference pages;
keep the operation manifest roster in sync by hand.

## Operation manifest roster

Package-owned operation manifests currently ship these operation IDs:

- `acknowledge-attention`, `analyze-claims`, `analyze-gaps`, `analyze-project-argument`, `answer-query`, `capture-bibtex-source`, `capture-pdf-source`, `capture-source`
- `capture-url-source`, `cascade-rollback`, `check-falsifiability`, `check-source-metadata`, `compare-and-contrast`, `compile-source-digest`, `compose-project-draft`, `create-concept`
- `curate-note-candidate`, `curate-note-link`, `enrich-source`, `empirical-event-record`, `eval-run`, `export-project`, `extract-claim-stubs`, `frame-paper`, `integrity-citation-survival-check`
- `integrity-claim-quote-check`, `integrity-contradiction-check`, `integrity-evidence-check`, `integrity-link-target-check`, `integrity-prompt-injection-check`, `integrity-provenance-checkpoint`, `integrity-quote-anchor-check`, `mark-checked`
- `observe-pi-edits`, `promote-draft-passage`, `propose-note-candidates`, `rebuild-checked-search-index`, `record-copi-interview`, `red-team-argument`, `regenerate-capability-index`, `regenerate-indexes`
- `regenerate-references-bib`, `regenerate-tracked-projections`, `render-project-argument-canvas`, `resolve-attention`, `run-seeded-error-verdict`, `summarize-for-recall`, `surface-tensions`, `trace-integrity-scan`
- `update-work`, `verify-project-draft`, `write-project-slice`

## Detailed action catalogs

| Catalog | What it covers |
| --- | --- |
| [System action operations](system-actions-operations.md) | Deterministic operations, runtime policy helpers, and subsystem helpers. |
| [System action CLI and PI flows](system-actions-cli-and-pi.md) | CLI requests plus PI review and recovery decisions. |
| [System action adapters](system-actions-adapters.md) | Optional external adapters and reusable prompt surfaces. |
| [System action scheduled tasks](system-actions-scheduled.md) | Optional local scheduler wiring around the CLI/runtime package. |
