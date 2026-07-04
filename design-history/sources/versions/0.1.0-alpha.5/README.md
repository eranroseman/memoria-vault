---
title: v0.1.0-alpha.5
parent: Releasing
has_children: true
---

# v0.1.0-alpha.5 — the Project gate

Internal checkpoint. Headline deliverable: the **Project gate** (the fourth navigation gate, ADR-70's
deferred slot), shipped as the expanded v1 cut. Live state lives in GitHub.

| File | Holds |
|---|---|
| [Release plan — v0.1.0-alpha.5](release-plan-0.1.0-alpha.5.md) | Prose: scope, gate/stage definitions, out-of-scope, cut procedure, roadmap |

- **Scope / readiness:** milestone `0.1.0-alpha.5` (#6) +
  [Release v0.1.0-alpha.5 (#584)](https://github.com/eranroseman/memoria-vault/issues/584).
- **Build workstreams:** #576 (spikes), #577 (ADRs), #578 (schema), #579 (Operation), #580 (gaps),
  #581 (PI surface), #582 (test-env slice), #583 (start-now logs); folds #154 #337 #381 #374 #372 #344 #370 #415.
- The tracked `tmp/` scratch folder was pruned after closeout. Durable decisions live in ADR-76,
  ADR-77, ADR-78, ADR-79, and ADR-80; unresolved packaging/test-env design detail was carried
  forward to `docs/releasing/0.1.0-alpha.8/tmp/`.
