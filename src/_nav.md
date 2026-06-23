---
title: Navigator
cssclasses: memoria-nav
---

**Now**

[[spaces/inbox|⬤ Needs you]] &nbsp; `$= dv.pages('"inbox"').where(p => p.lifecycle == "proposed" && p.type != "flag" && p.type != "alert").length`

[[spaces/maintenance|◆ Drift]] &nbsp; `$= dv.pages('"inbox"').where(p => p.lifecycle == "proposed" && (p.type == "flag" || p.type == "alert")).length` &nbsp; [[system/dashboards/fleet-health|◆ Fleet]] &nbsp; `$= dv.pages('"system/metrics"').where(p => p.type == "lane-metric" && (p.band == "act" || p.band == "watch")).length`

---

**Places**

[[spaces/library|Library]] &nbsp; `$= dv.pages('"notes/sources"').where(p => p.lifecycle == "proposed" && p.sample != true).length` to read

[[spaces/knowledge|Knowledge]] &nbsp; `$= dv.pages('"notes/claims"').where(p => p.lifecycle == "current" && (p.links?.contradicts ?? []).length > 0).length` ⚠

[[spaces/project|Project]] &nbsp; `$= dv.pages('"projects"').where(p => p.type == "project" && p.lifecycle == "current").length` active

<!-- ponytail: badges are Dataview inline-JS, not Bases formulas — Bases can't emit a standalone count. Needs Dataview "Enable inline JavaScript queries" on. Fleet reads runtime-only lane-metric notes; absent in a fresh vault renders 0. Period precision is best-effort, not week-scoped. -->
