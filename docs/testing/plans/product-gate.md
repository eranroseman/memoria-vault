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
- Throwaway workspace has a real source available through Zotero Local API,
  BibTeX, URL capture, or another release-scoped capture adapter.
- Manual GUI checks are ready if the gate includes Obsidian-rendered evidence.

## Checks

| Check | Pass criteria |
| --- | --- |
| Worker spine | A shipped operation completes enqueue -> run -> checked Concept write -> journal/audit evidence -> `done`. |
| Capture value loop | One real source reaches a checked catalog `source` with stable `source_id`, raw/content paths, metadata provenance where available, and traced writes. |
| Knowledge value loop | The source produces digest/hub synthesis, an accepted anchored `note`, Ask/gap evidence, and a changed project argument view. |
| Review handoff | Attention rows surface the needed PI action and can be acknowledged or resolved through the worker-owned path. |
| Review close | Human review leaves a traced PI edit, acceptance, rejection, or rollback disposition; machine consumers only see checked content. |
| Telemetry | Board state, transitions, audit, lint findings, cost, attention, and triage logs gain expected rows from the live activity. |
| GUI product surfaces | Manual GUI checks pass for dashboards, Bases, spaces, Zotero, and Agent Client. |
| Quality evidence | Eval/gold-task evidence exists when the release claims output-quality readiness. |

## Tier-1 Correctness

For capture reliance, spot-check 5-10 real sources:

- multi-source merge identity and author/reference alignment;
- tag/classification relevance;
- extract degradation behavior for missing or bad source files.

If the check is not acceptable, scope the release to the reliable subset instead
of treating the product gate as green.

## Evidence Home

Record the run in the release readiness/stage issue. Store a curated
`validation-log.md` only when the issue trail is not enough.
