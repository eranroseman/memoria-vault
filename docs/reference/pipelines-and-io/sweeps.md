---
title: Sweeps
parent: Pipelines and I/O
nav_order: 2
grand_parent: Reference
---

# Sweeps

Deterministic maintenance passes under `memoria_vault.runtime.subsystems`.
Retraction sweeps surface review work through Inbox alert projections; they do
not directly promote Concept files.

## Retraction sweep

`retraction.py --doi <doi>` performs deterministic, read-only retraction-by-DOI
checks from three sources, most authoritative first:

| Source | Role |
| --- | --- |
| Local Retraction Watch CSV | Primary source; `--refresh` downloads it to `.memoria/data/retraction_watch.csv`, refreshed by manual or operator-managed scheduled runs. |
| Crossref `update-to` delta | Live DOI status check. |
| Open Retractions | Cross-check source. |

`retraction.py --sweep --vault V` scans checked SQLite Catalog Works (not
legacy source files) and raises an Inbox `alert` attention item for each
retracted DOI. It never changes a Work's state.

## Related

- The capture stage that creates the Work records these sweeps monitor: [Ingest routing](ingest.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../system/installer.md)
- Request and attention state: [Control plane](../control-and-policy/control-plane.md)
