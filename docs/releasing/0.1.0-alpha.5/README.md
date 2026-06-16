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
| `tmp/exec-plan-0.1.0-alpha.5.md` | The living build doc (workstreams, validation) — deleted at checkpoint close |
| `tmp/project-starter.md` | Design of record for the gate (expanded v1 cut) |
| `tmp/adr-update.md` | ADR audit — the WS-A housekeeping/retirement source |
| `tmp/test-env.md` | Test-env design (ADR-77/78) — only the deny-assertion slice rides alpha.5 |
| `tmp/install-a-real-package.md` | Packaging design (ADR-76, deferred) — not alpha.5 |

- **Scope / readiness:** milestone `0.1.0-alpha.5` (#6) +
  [Release v0.1.0-alpha.5 (#584)](https://github.com/eranroseman/memoria-vault/issues/584).
- **Build workstreams:** #576 (spikes), #577 (ADRs), #578 (schema), #579 (Operation), #580 (gaps),
  #581 (PI surface), #582 (test-env slice), #583 (start-now logs); folds #154 #337 #381 #374 #372 #344 #370 #415.
- `tmp/` is tracked scratch — promote durable decisions into ADRs, then delete `tmp/` before the checkpoint closes.
