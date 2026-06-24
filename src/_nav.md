---
title: Navigator
cssclasses: memoria-nav
---

**Now**

[[spaces/inbox|⬤ Needs you]] &nbsp; `$= dv.pages('"inbox"').where(p => p.lifecycle == "proposed" && p.type != "flag" && p.type != "alert").length`

[[spaces/maintenance|Drift]] &nbsp; `$= (() => { const n = dv.pages('"inbox"').where(p => p.lifecycle == "proposed" && (p.type == "flag" || p.type == "alert")).length; return n > 0 ? "◆ " + n : n })()` &nbsp; [[system/dashboards/fleet-health|Fleet]] &nbsp; `$= (() => { const n = dv.pages('"system/metrics"').where(p => p.type == "lane-metric" && (p.band == "act" || p.band == "watch")).length; return n > 0 ? "◆ " + n : n })()`

---

**Places**

[[spaces/library|Library]] &nbsp; `$= dv.pages('"notes/sources"').where(p => p.lifecycle == "proposed" && p.sample != true).length` to read

[[spaces/knowledge|Knowledge]] &nbsp; `$= (() => { const n = dv.pages('"notes/claims"').where(p => p.lifecycle == "current" && (p.links?.contradicts ?? []).length > 0).length; return n > 0 ? n + " ⚠" : n })()`

[[spaces/project|Project]] &nbsp; `$= dv.pages('"projects"').where(p => p.type == "project" && p.lifecycle == "current").length` active

---

**Actions**

> [!note]- Inbox actions
> ```button
> name Capture source
> type command
> action QuickAdd: Memoria: capture source from URL
> ```
>
> ```button
> name Capture fleeting
> type command
> action QuickAdd: Memoria: capture fleeting
> ```
>
> ```button
> name Load sample
> type command
> action QuickAdd: Memoria: load sample vault
> ```

> [!note]- Library actions
> ```button
> name Capture source
> type command
> action QuickAdd: Memoria: structured source capture
> ```
>
> ```button
> name Capture from Zotero
> type command
> action QuickAdd: Memoria: capture from Zotero selection
> ```

> [!note]- Knowledge actions
> ```button
> name Write claim
> type command
> action QuickAdd: Memoria: write claim note
> ```
>
> ```button
> name Link claim
> type command
> action QuickAdd: Memoria: link claim
> ```

> [!note]- Project actions
> ```button
> name Start project
> type command
> action QuickAdd: Memoria: start project
> ```
>
> ```button
> name Refresh gate
> type command
> action QuickAdd: Memoria: refresh project gate
> ```

<!-- ponytail: badges are Dataview inline-JS, not Bases formulas — Bases can't emit a standalone count. Needs Dataview "Enable inline JavaScript queries" on. Fleet reads runtime-only lane-metric notes; absent in a fresh vault renders 0. Period precision is best-effort, not week-scoped. -->
