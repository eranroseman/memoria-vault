---
title: Sweeps
parent: Pipelines and I/O
grand_parent: Reference
nav_order: 2
---

# Sweeps

Deterministic maintenance passes under `memoria_vault.runtime.subsystems`.
Retraction sweeps surface review work through worker-owned projections; they do
not directly promote Concept files.

## Retraction sweep

`retraction.py` performs deterministic, read-only retraction-by-DOI checks from three sources, most authoritative first:

| Source | Role |
| --- | --- |
| Local Retraction Watch CSV | Primary source; `--refresh` downloads it to `.memoria/data/retraction_watch.csv`, refreshed by manual or operator-managed scheduled runs. |
| Crossref `update-to` delta | Live DOI status check. |
| Open Retractions | Cross-check source. |

`retraction.py --sweep --vault V` scans the Catalog DOIs and raises Inbox
`alert` attention items on hits. It never flips a note lifecycle.

## Related

- The capture stage that creates the source records these sweeps monitor: [Ingest routing](ingest.md)
- Scheduler wiring boundary: [Installer (bootstrap)](installer.md)
- The retired Inbox card contract: [Inbox card fields](inbox-card-fields.md)
