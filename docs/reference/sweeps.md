---
title: Sweeps
parent: Pipelines and I/O
grand_parent: Reference
---

# Sweeps

Deterministic maintenance passes under `vault-template/.memoria/operations`. Re-ingest and retraction sweeps surface review work through the board or Inbox; the inbox archival sweep is a deterministic direct write that only flips eligible resolved cards to `lifecycle: archived`.

## Re-ingest backstops

`reconcile.py` finds ingest work that started but did not land cleanly. Re-ingest must be board-serialized, so each backstop enqueues an idempotent re-ingest card with `hermes kanban create --idempotency-key reingest:<citekey>`; the board provides deduplication, backoff, and the failure circuit-breaker.

| Pass | Detects |
| --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk. |
| `--retry` | A captured note stuck at `ingest_status: tier0`. |

`--dry-run` reports without touching the board. The installer wires these re-ingest passes into the `memoria-sweeps` cron every 15 minutes.

## Inbox archival sweep

`archive_inbox.py` is the direct-write cleanup pass in the same cron wrapper. It archives handled Inbox cards after the freshness window expires:

```bash
python vault-template/.memoria/operations/cleanup/archive_inbox.py --vault <vault>
python vault-template/.memoria/operations/cleanup/archive_inbox.py --vault <vault> --dry-run
```

The retention window comes from `.memoria/schemas/calibration.yaml` at `inbox.archive_after_days`; when the value cannot be read, the operation warns once and uses the default of `30` days. `--days <n>` overrides calibration for a single run.

The sweep scans `inbox/**/*.md` and rewrites only the top-level `lifecycle:` line when all conditions are true: the card is in a resolved-but-visible lifecycle (`current`), it has a parseable `resolved:` date, and that date is older than the cutoff. It never touches `proposed` cards, cards without `resolved:`, already archived cards, or malformed frontmatter. The file stays in place; no body text or other frontmatter fields are rewritten.

Because the operation is idempotent and single-line, it is exempt from board serialization. `--dry-run` returns the same JSON report shape without writing.

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
