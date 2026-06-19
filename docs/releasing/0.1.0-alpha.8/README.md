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
| `tmp/` | Removed after the carried-forward scratch was routed to ADRs, docs, and GitHub issues. |

## Tmp disposition check

Checked 2026-06-19 after ADR-58/59/61/65 were split into ADR-84 through ADR-100.
All carried-forward `tmp/` files have now been disposed.

Deleted 2026-06-19:

- `tmp/alpha7-docs-audit-report.md` — all findings were already resolved or intentionally deferred in current docs/checks.
- `tmp/deferred-adr-implementability-alpha6.md` — superseded by current ADR statuses plus issues #369, #371, #372, #374, #416, #521, #686, ADR-98/#711 through ADR-100/#713, and the now-closed old ADR-65 umbrella #611.
- `tmp/install-a-real-package-alpha5.md` — folded into [ADR-76](../../adr/76-versioned-vault-release-reconciling-installer.md) and [#521](https://github.com/eranroseman/memoria-vault/issues/521).
- `tmp/test-env-design-alpha5.md` — folded into [ADR-80](../../adr/80-ephemeral-containerized-test-env.md), current testing docs, and Phase 2 tracker [#722](https://github.com/eranroseman/memoria-vault/issues/722).
- `tmp/ui-architecture-design-history-alpha7.md` — verification evidence moved into reference docs and related ADRs.
- `tmp/ui-architecture-future-alpha7.md` — split into [ADR-102](../../adr/102-disposable-projection-engine.md) / [#719](https://github.com/eranroseman/memoria-vault/issues/719) and [ADR-103](../../adr/103-projected-canvas-spatial-axis.md) / [#721](https://github.com/eranroseman/memoria-vault/issues/721).
