---
title: Sample vault
parent: System and infrastructure
grand_parent: Reference
---

# Sample vault

The bundled Mediterranean-diet sample vault was alpha.10 tutorial scaffolding.
It is retired in alpha.15: the starter vault ships no sample corpus and no
`Memoria: load sample vault` or `Memoria: remove sample vault` commands.

## Current state

| Surface | Alpha.15 state |
| --- | --- |
| Hidden shipped bundle | Not shipped |
| Runtime sample notes | Not created by install |
| Sample commands | Not registered |
| Tutorial dependency | Retired with the alpha.10 tutorial arc |

Alpha.15 starts from an empty working vault. Capture source work through the
`memoria work` CLI or write PI-owned notes directly, then let the worker/check
loop backfill checked Concepts.

## Historical context

The retired tutorial rationale lives in
[ADR-112](../adr/112-tutorial-destination-first-arc.md). It is historical
context only, not current product behavior.
