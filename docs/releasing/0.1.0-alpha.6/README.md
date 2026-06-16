---
title: v0.1.0-alpha.6
parent: Releasing
has_children: true
---

# v0.1.0-alpha.6 — Conformance & the test-env harness

Internal checkpoint. Two pillars: **make the accepted-ADR audit's findings true**
(close the conformance gaps the alpha.6 audit found) and ship the roadmap's
committed-next **ephemeral test-env harness (ADR-80, Phase 1)**. Live state lives in
GitHub.

| File | Holds |
|---|---|
| [Release plan — v0.1.0-alpha.6](release-plan-0.1.0-alpha.6.md) | Prose: scope, gate/stage definitions, out-of-scope, cut procedure, roadmap |
| `tmp/exec-plan-0.1.0-alpha.6.md` | Living build doc — workstreams, sequencing, per-issue steps (retained for closeout audit) |
| `tmp/adr-implementation-gap-analysis.md` | Audit scratch — accepted ADRs vs. built state (source of the G1–G3 issues) |
| `tmp/deferred-adr-cadence-review.md` | Audit scratch — which deferred ADRs are buildable now (source of B1 + the alpha.7 harvest) |
| `tmp/deferred-adr-implementability-verification.md` | Independent re-verification of the cadence review |

- **Scope / readiness:** milestone `0.1.0-alpha.6` (#7) +
  [Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635)
  (gate sub-issues #636–#639, stage sub-issues #640–#645).
- **Build workstreams (Track A — conformance, "re-implement approved goals"):**
  WS-1 correctness/security (#620, #621, #624), WS-2 Project-gate surface (#622),
  WS-3 docs/template/supply-chain (#627, #626, #585; #625 documented).
- **Build workstream (Track B — net-new):** WS-4 test-env harness Phase 1 (#586).
- The tracked `tmp/` scratch folder is retained while alpha.6 is being designed;
  promote durable decisions into ADRs and delete `tmp/` at cut.
