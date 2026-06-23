---
title: Navigator
cssclasses: memoria-nav
---

**Now**

[[spaces/inbox|⬤ Needs you]] &nbsp; `$= dv.pages('"inbox"').where(p => p.lifecycle == "proposed").length`

---

**Places**

[[spaces/library|Library]] &nbsp; `$= dv.pages('"notes/sources"').where(p => p.lifecycle == "proposed" && p.sample != true).length` to read

[[spaces/knowledge|Knowledge]] &nbsp; `$= dv.pages('"notes/claims"').where(p => p.lifecycle == "current" && (p.links?.contradicts ?? []).length > 0).length` ⚠

[[spaces/project|Project]] &nbsp; `$= dv.pages('"projects"').where(p => p.type == "project" && p.lifecycle == "current").length` active

<!-- ponytail: badges are Dataview inline-JS, not Bases formulas — Bases can't emit a standalone count. Needs Dataview "Enable inline JavaScript queries" on. -->
