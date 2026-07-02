---
title: Sweeps
parent: Pipelines and I/O
grand_parent: Reference
---

# Sweeps

Deterministic maintenance passes under `memoria_vault.runtime.subsystems`.
Re-ingest and retraction sweeps surface review work through worker-owned
projections; they do not directly promote Concept files.

## Re-ingest backstops

`reconcile.py` finds ingest work that started but did not land cleanly.
Re-ingest must be request-serialized, so each backstop creates an idempotent
local request such as `reingest:<citekey>`; the SQLite request queue provides
deduplication, backoff, and the failure circuit-breaker.

| Pass | Detects |
| --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk. |
| `--retry` | A captured note stuck at `ingest_status: tier0`. |

`--dry-run` reports without creating requests. Alpha.14 does not install a host
scheduler; an operator-managed scheduled task can invoke the sweep through the
CLI when the re-ingest path is enabled.

## Retraction sweep

`retraction.py` performs deterministic, read-only retraction-by-DOI checks from three sources, most authoritative first:

| Source | Role |
| --- | --- |
| Local Retraction Watch CSV | Primary source; `--refresh` downloads it to `.memoria/data/retraction_watch.csv`, refreshed monthly by cron. |
| Crossref `update-to` delta | Live DOI status check. |
| Open Retractions | Cross-check source. |

`retraction.py --sweep --vault V` scans the Catalog DOIs and raises Inbox `alert` cards on hits. It never flips a note lifecycle.

## Related

- The ingest stage that creates the source records these sweeps monitor: [Ingest routing](ingest.md)
- The cron wiring for installed vaults: [Installer (bootstrap)](installer.md)
- The retired Inbox card contract: [Inbox card fields](inbox-card-fields.md)
