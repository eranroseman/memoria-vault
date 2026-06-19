---
title: v0.1.0-alpha.8
parent: Releasing
has_children: true
---

# v0.1.0-alpha.8

Planning handoff folder for work rolled forward from earlier checkpoint scratch.
No release plan has been cut yet; live scope still belongs in GitHub milestones and
the Memoria Issue Tracker.

| File | Holds |
|---|---|
| `tmp/` | Carried-forward design scratch whose implementation is not complete and whose durable destination is still pending. |

## Tmp disposition check

Checked 2026-06-19 after ADR-58/59/61/65 were split into ADR-84 through ADR-100.
Do not delete the folder wholesale yet; dispose file-by-file:

| File | Safe to delete? | Durable home / blocker |
|---|---:|---|
| `tmp/alpha7-docs-audit-report.md` | Yes | All findings are marked resolved or intentionally deferred in the note itself; current docs and checks carry the resolved state. |
| `tmp/deferred-adr-implementability-alpha6.md` | Yes | Superseded by current ADR statuses plus issues #369, #371, #372, #374, #416, #521, #686, and ADR-98/#711 through ADR-100/#713; old ADR-65 umbrella #611 is closed. |
| `tmp/install-a-real-package-alpha5.md` | Not yet | Long-form rationale behind ADR-76/#521. Keep until ADR-76 absorbs or links the lane-overlay, policy-core import, release-manifest, and host-config details at decision time. |
| `tmp/test-env-design-alpha5.md` | Not yet | Partly superseded by ADR-80 and current testing docs, but still contains discarded/changed clean-sheet assumptions and model/runtime questions. Keep until the useful Phase 2 residue is either folded into ADR-80 or closed as rejected. |
| `tmp/ui-architecture-design-history-alpha7.md` | Not yet | Contains live verification evidence for Bases scale, nested-map backlinks, Portals, Workspaces Plus, CSS snippets, and Obsidian settings. Keep until the evidence is captured in ADRs/reference docs or explicitly rejected as historical scratch. |
| `tmp/ui-architecture-future-alpha7.md` | Not yet | Partly split into ADR-83 and ADR-98 through ADR-100, but still carries the general projector/canvas trigger model and open operator/sync/failure-surfacing questions. Keep until those are folded into proposed ADRs or GitHub issues. |
