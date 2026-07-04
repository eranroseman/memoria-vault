---
title: v0.1.0-alpha.7
parent: Releasing
has_children: true
---

# v0.1.0-alpha.7 — Clean-slate Obsidian UI & navigation

Complete internal checkpoint. Landed the buildable, sandbox-verified subset of the UI redesign:
the **Bases view layer**, **capture forms**, the **persistent-shell gate model**
(Inbox/Library/Knowledge/Project, switched by a nav row — retiring the ADR-68
workspace-swap), **Portals** folder navigation with the core file explorer retained as
fallback, and the **Memoria-tuned Obsidian config + CSS**. The general projector engine, projected telemetry, the
Canvas/argument-graph spatial axis, and the edge-authoring "relate" control are
**deferred** in [ADR-81](../../adr/81-persistent-gate-dashboards.md). Live state lives
in GitHub.

| File | Holds |
|---|---|
| [Release plan — v0.1.0-alpha.7](release-plan-0.1.0-alpha.7.md) | Prose: scope, gate/stage definitions, out-of-scope, cut procedure, roadmap |
| [Validation log](validation-log.md) | Curated closeout evidence for PR #677, CI, local validation, and issue closure |

- **Scope / readiness:** milestone `0.1.0-alpha.7`, PR #677, and the validation log.
- **Closed shipped-UI issues:** #659 (one title), #665 (de-duplicated Inbox), #666
  (workspace switching — by elimination), #667 (navigation), #663 (`system/` hidden),
  #668 (CSS snippets).
- **Scope-reconcile:** the alpha.6 roadmap's shadow/instrument harvest
  (#370/#611/#416/#371) is **not** absorbed here and rolls to alpha.8 / the next
  telemetry checkpoint.
- The tracked `tmp/` scratch was pruned after closeout. Durable decisions live in ADR-81;
  unresolved future UI design detail was carried forward to `docs/releasing/0.1.0-alpha.8/tmp/`.
