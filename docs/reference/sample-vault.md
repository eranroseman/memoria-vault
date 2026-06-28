---
title: Sample vault
parent: System and infrastructure
grand_parent: Reference
---

# Sample vault

Reference for the bundled Mediterranean-diet tutorial corpus. To load or remove
it, see [Load and remove the sample vault](../how-to-guides/setup/load-sample-vault.md).
The tutorial rationale is [ADR-112](../adr/112-tutorial-destination-first-arc.md).

## Bundle location

| Surface | Path |
| --- | --- |
| Hidden shipped bundle | `.memoria/samples/mediterranean-diet/` |
| Catalog destination | `catalog/papers/` |
| Source-note destination | `notes/sources/` |
| Claim destination | `notes/claims/` |
| Hub destination | `notes/hubs/` |

## Current bundle counts

| Type | Count |
| --- | ---: |
| Catalog paper entities | 10 |
| Source notes | 10 |
| Claim notes | 13 |
| Hub notes | 1 |
| Total Markdown notes | 34 |

Every bundled note carries `sample: true`. Removal archives live notes with that
label; it does not delete the hidden bundle.

## Commands

| Command | Effect |
| --- | --- |
| `Memoria: load sample vault` | Copies bundled `catalog/` and `notes/` files into the live vault, skipping existing files. |
| `Memoria: remove sample vault` | Archives live `sample: true` notes. |

## Map floor

The bundle includes 10 non-empty source notes, matching the calibrated full-map
floor used by corpus mapping. That lets Tutorial 01 exercise Map corpus without
immediately blocking on corpus size.

## Source of truth

The source files live under
[`src/.memoria/samples/mediterranean-diet/`](https://github.com/eranroseman/memoria-vault/tree/main/src/.memoria/samples/mediterranean-diet).
If this page disagrees with the bundle, the bundle wins.
