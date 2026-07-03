---
title: Board export
parent: Pipelines and I/O
grand_parent: Reference
---

# Board export

Alpha.15 does not ship a Hermes board exporter. The standalone product state is
the SQLite request/journal database plus checked workspace projections generated
by `memoria workspace rebuild`, `memoria journal tail`, and the runtime worker.

## Current Replacement

| Need | Alpha.15 surface |
| --- | --- |
| Queue/request state | `memoria status`, `memoria request list`, and `.memoria/memoria.sqlite` |
| Human attention | `memoria attention list/show/resolve` over `inbox/` projections |
| Operation history | `memoria journal tail/show` and `system/logs/audit.jsonl` |
| Project/export evidence | `memoria project export` and checked generated projections |
| Runtime diagnostics | `memoria doctor bundle` |

Historical board exports may still appear in old ADRs or release scratch, but
they are not a current runtime command, scheduled job, package dependency, or
release gate.
