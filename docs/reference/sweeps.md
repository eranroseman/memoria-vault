---
title: Sweeps
parent: Reference
---

# Sweeps

Deterministic maintenance passes under `src/.memoria/operations`. Sweeps are read-only against notes: they detect drift, missing work, and external status changes, then surface review items through the board or Inbox.

## Re-ingest backstops

`reconcile.py` finds ingest work that started but did not land cleanly. Re-ingest must be board-serialized, so each backstop enqueues an idempotent re-ingest card with `hermes kanban create --idempotency-key reingest:<citekey>`; the board provides deduplication, backoff, and the failure circuit-breaker.

| Pass | Detects |
| --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk. |
| `--retry` | A captured note stuck at `ingest_status: tier0`. |

`--dry-run` reports without touching the board. The installer wires both passes as the `memoria-sweeps` cron, every 15 minutes.

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
- The alert-card fields: [Inbox card fields](inbox-card-fields.md)
