---
title: v0.1.0-alpha.7
parent: Releasing
has_children: true
---

# v0.1.0-alpha.7 — Clean-slate Obsidian UI & navigation

Internal checkpoint. Lands the buildable, sandbox-verified subset of the UI redesign:
the **Bases view layer**, **capture forms**, the **persistent-shell gate model**
(Inbox/Library/Knowledge/Project, switched by a nav row — retiring the ADR-68
workspace-swap), **Portals** folder navigation, and the **Memoria-tuned Obsidian
config + CSS**. The general projector engine, projected telemetry, the
Canvas/argument-graph spatial axis, and the edge-authoring "relate" control are
**deferred**. Live state lives in GitHub.

| File | Holds |
|---|---|
| [Release plan — v0.1.0-alpha.7](release-plan-0.1.0-alpha.7.md) | Prose: scope, gate/stage definitions, out-of-scope, cut procedure, roadmap |
| `tmp/exec-plan-0.1.0-alpha.7.md` | Living build doc — workstreams, sequencing, per-WS steps, verification mapping |
| `tmp/ui-architecture-alpha7.md` | The alpha.7 UI scope cut (Bases / forms / gates / config) |
| `tmp/workspaces-design.md` | Gate model — dashboard notes in a persistent shell (amends ADR-68) |
| `tmp/portals-design.md` | Folder-navigation chrome — Portals, gated |
| `tmp/ui-architecture-future.md` | The deferred set (projector engine, Canvas, telemetry, relate-control) |
| `tmp/dashboards/` | Draft gate dashboards (`inbox`/`library`/`knowledge`/`project`) |

- **Scope / readiness:** milestone `0.1.0-alpha.7` + `Release v0.1.0-alpha.7` parent
  issue (gate sub-issues G1–G6, stage sub-issues S0–S5) — **to create** (see the exec
  plan's GitHub-setup section).
- **Closes shipped-UI issues:** #659 (one title), #665 (de-duplicated Inbox), #666
  (workspace switching — by elimination), #667 (navigation), #663 (`system/` hidden),
  #668 (CSS snippets).
- **Day-1 checks that can move scope:** the `newLinkFormat: absolute` backlink
  re-verification (G1) and the `gen-forms.py`-exists check (G2); plus the **PI release
  decision** on day-1 empty-state (G6).
- **Scope-reconcile:** the alpha.6 roadmap's shadow/instrument harvest
  (#370/#611/#416/#371) is **not** absorbed here — fold-in vs roll-to-alpha.8 is open.
- The tracked `tmp/` scratch is retained while alpha.7 is being designed; promote durable
  decisions into the UI ADR and delete `tmp/` at cut.
