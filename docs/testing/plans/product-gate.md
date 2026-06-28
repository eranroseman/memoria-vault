---
topic: tests
title: Product Gate
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 40
---

# Product Gate

The Product Gate proves Memoria produces research value, not just green wiring.

## Preconditions

- Source, Package, and Runtime gates are green.
- Throwaway vault has a real Zotero/BBT source with a DOI or other resolvable ID.
- Manual GUI checks are ready if the gate includes Obsidian-rendered evidence.

## Checks

| Check | Pass criteria |
| --- | --- |
| Dispatched-card spine | A shipped lane completes dispatch -> claim -> run -> gated write -> audit -> `done`. |
| Ingest value loop | One real source reaches a `current` paper note with `ingest_status: complete`, `_proposed_classification`, `[!brief]`, stable IDs, extract/provenance where available, and audited writes. |
| Review handoff | The card reaches `done` with review requested and surfaces for human action. |
| Review close | Human review promotes `_proposed_classification` into canonical fields and removes the proposal block. |
| Telemetry | Board state, transitions, audit, lint findings, cost, attention, and triage logs gain expected rows from the live activity. |
| GUI product surfaces | Manual GUI checks pass for dashboards, Bases, spaces, Zotero, and Agent Client. |
| Quality evidence | Eval/gold-task evidence exists when the release claims output-quality readiness. |

## Tier-1 Correctness

For ingest reliance, spot-check 5-10 real papers:

- multi-source merge identity and author/reference alignment;
- tag/classification relevance;
- extract degradation behavior for missing or bad PDFs.

If the check is not acceptable, scope the release to the reliable subset instead
of treating the product gate as green.

## Evidence Home

Record the run in the release readiness/stage issue. Store a curated
`validation-log.md` only when the issue trail is not enough.
