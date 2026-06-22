---
title: The sample vault
parent: Reference
---

# The sample vault

A small, labeled starter corpus the tutorials load so you can reach the *Produce* payoff in one sitting instead of after weeks of reading. Its topic is neutral and broadly legible: **adherence to a Mediterranean diet and cardiovascular health**.

It ships inside the installed vault as a hidden bundle at `.memoria/samples/mediterranean-diet/` and becomes live `catalog/` and `notes/` only when you load it. To **load or remove** it, see [Load and remove the sample vault](../how-to-guides/setup/sample-vault.md); **why** it is shaped this way — seeded, half-built, provenance-bound — is recorded in [ADR-112](../adr/112-tutorial-destination-first-arc.md).

## What is in it

| Layer | Worked (study these) | Half-built (left for you to finish) |
| --- | --- | --- |
| Sources | 6 source notes, written "in my words" with claims distilled | 2 sources captured but not yet distilled |
| Claims | 11 connected claims with typed `supports` / `contradicts` links | 2 claim stubs (evidence blank) and 1 deliberately unmade link |
| Catalog | 8 catalog entities, one per cited paper | — |
| Hub | 1 hub organizing the cluster and naming an open gap | — |

Every note is labeled `sample: true`, which keeps it visibly separate from your own work and lets a single command archive the whole sample later.

Everything traces to a **real, citable paper** (PREDIMED, the Lyon Diet Heart Study, the Seven Countries Study, a Greek cohort, and two reviews). Nothing is fabricated or model-generated: the whole point of Memoria is that every claim traces to a source, so a sample that faked its provenance would teach the exact habit the system exists to prevent.

## The shape to notice

The cluster is not all agreement. It deliberately holds a **tension** — the strong causal reading of the trial evidence sits against the observational caution that diet effects may be confounded by overall healthy lifestyle — and the hub names a **gap** the corpus does not yet cover: primary prevention in low-risk people, and whether the benefit transports beyond Mediterranean populations. The tutorials have you read that tension and gap on the coverage map, and later turn the gap back into discovery — one full turn of the loop.

The **half-built pieces** — the un-distilled sources, the claim stubs, the unmade link — are deliberate. Finishing them is how the tutorials teach the distill-and-connect move on a worked example before you do it on your own material; the completions stay `sample: true`, so they archive with the sample when you remove it, while the claims you distill from your own sources do not.
