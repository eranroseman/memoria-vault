---
topic: tests
title: Manual GUI Checks
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 50
---

# Manual GUI Checks

These attended checks cover what CI cannot prove: Obsidian rendering, Zotero,
Bases, dashboards, and the Agent Client pane.

## Preconditions

- Runtime Gate is green.
- Obsidian opens the throwaway runtime vault, not the development repo.
- Dataview JavaScript queries are enabled.
- Local REST API HTTPS is configured for the test vault.

## Checks

| Area | Pass criteria |
| --- | --- |
| Plugins | All bundled plugins are installed and enabled without load errors. |
| Local REST API | Authenticated HTTPS request succeeds; Hermes writes through the Obsidian bridge. |
| Dashboards | `board-state.md`, `fleet-health.md`, `audit-log.md`, `eval-trend.md`, and `skill-state.md` render without Dataview errors. |
| Spaces | `spaces/inbox.md`, `spaces/library.md`, `spaces/knowledge.md`, `spaces/project.md`, and `spaces/maintenance.md` render their embedded views. |
| Bases | Every shipped `.base` opens without YAML or missing-view errors. |
| Zotero/BBT | `.memoria/memoria.bib` updates and citation lookup resolves a test item. |
| Agent Client | A session with a Memoria profile returns a model response. |
| Deny visibility | A forced denied write creates no file and appears in the audit dashboard. |
| Board visibility | A card plus board-export cron appears in the board dashboard. |

## Evidence Home

Complete the checklist in the relevant release readiness/stage issue. Screenshots
are useful only for failures or ambiguous rendering problems.
