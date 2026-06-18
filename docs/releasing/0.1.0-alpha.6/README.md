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

- **Scope / readiness:** milestone `0.1.0-alpha.6` (#7) +
  [Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635)
  (gate sub-issues #636–#639, stage sub-issues #640–#645).
- **Build workstreams (Track A — conformance, "re-implement approved goals"):**
  WS-1 correctness/security (#620, #621, #624) — implementation landed in
  [PR #651](https://github.com/eranroseman/memoria-vault/pull/651), with the S4 live
  sandbox HTTPS smoke still tracked in the release issues; WS-2 Project-gate surface
  inside Studio (#622) — implementation landed in
  [PR #653](https://github.com/eranroseman/memoria-vault/pull/653), with the S5 live
  Obsidian drive-through still tracked in the release issues; WS-3
  docs/template/supply-chain (#627, #626, #585; #625 documented) — landed in
  [PR #649](https://github.com/eranroseman/memoria-vault/pull/649).
- **Build workstream (Track B — net-new):** WS-4 test-env harness Phase 1 (#586) —
  model-free implementation landed in
  [PR #655](https://github.com/eranroseman/memoria-vault/pull/655), with the optional
  live Gemma/`llama.cpp` tool-call smoke still tracked in the release issues.
- The tracked `tmp/` scratch folder was pruned after closeout. Durable conformance and
  harness decisions live in the accepted ADRs and current docs; unresolved deferred-ADR
  implementability detail was carried forward to `docs/releasing/0.1.0-alpha.8/tmp/`.
