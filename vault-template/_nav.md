---
title: Navigator
cssclasses: memoria-nav
---

**Now**

[[spaces/inbox|⬤ Action queue]] &nbsp; `$= dv.pages('"inbox"').where(p => p.projection == "attention" && p.attention_status == "open" && ["candidate", "gap", "work-prompt"].includes(p.attention_kind)).length`

[[spaces/maintenance|Drift]] &nbsp; `$= (() => { const n = dv.pages('"inbox"').where(p => p.projection == "attention" && p.attention_status == "open" && ["flag", "alert"].includes(p.attention_kind)).length; return n > 0 ? "◆ " + n : n })()` &nbsp; [[system/dashboards/fleet-health|Fleet]] &nbsp; `$= (() => { const n = dv.pages('"system/metrics"').where(p => p.type == "lane-metric" && (p.band == "act" || p.band == "watch")).length; return n > 0 ? "◆ " + n : n })()`

---

**Places**

[[spaces/library|Library]] &nbsp; `$= dv.pages('"catalog/sources"').where(p => p.check_status == "checked" && p.sample != true).length` sources

[[spaces/knowledge|Knowledge]] &nbsp; `$= (() => { const n = dv.pages('"knowledge/notes"').where(p => p.check_status == "checked").length; return n > 0 ? n : n })()`

[[spaces/project|Project]] &nbsp; `$= dv.pages('"knowledge/projects"').where(p => p.type == "project" && p.check_status == "checked").length` active

---

**Actions**

> [!note]- Inbox actions
> ```button
> name Capture note
> type command
> action QuickAdd: Memoria: capture note
> ```
>
> ```button
> name Open Inbox
> type command
> action QuickAdd: Memoria: open Inbox
> ```
>
> ```button
> name Resolve active
> type command
> action QuickAdd: Memoria: resolve inbox card
> ```

> [!note]- Project actions
> ```button
> name Record exploration trace
> type command
> action QuickAdd: Memoria: record exploration trace
> ```

<!-- ponytail: badges are Dataview inline-JS, not Bases formulas — Bases can't emit a standalone count. Needs Dataview "Enable inline JavaScript queries" on. Fleet reads runtime-only lane-metric notes; absent in a fresh vault renders 0. Period precision is best-effort, not week-scoped. -->
