---
title: Inbox
dashboard: gate
gate: inbox
---

# Inbox — what needs me

Gates: **Inbox** · [[library|Library]] · [[knowledge|Knowledge]] · [[project|Project]]

> [!note] Draft gate dashboard. Ships into the golden copy (`src/`) as the **Inbox**
> gate. Embed + per-view targeting verified live (`![[name.base#View Name]]`,
> `workspaces-design.md` §8). Opened on launch by Homepage (ADR-13).

> [!tip] Inbox empty? That's the goal — "Needs me" converges to empty. New agent
> proposals and integrity flags land here for your decision.

## Needs me

![[inbox.base#Needs me]]

## At a glance

```dataview
%% Status strip — single cross-collection line (§6). Exact queries pending (#664):
   reviews pending · blocked · HIGH/CRITICAL findings. Placeholder below. %%
TABLE WITHOUT ID
  length(filter(file.tasks, (t) => !t.completed)) AS "—"
WHERE file.name = this.file.name
```

> *Status-strip queries are the one Dataview surface (§6) and are not yet pinned —
> finalize before merge.*

## Board (mechanic's view)

<!-- secondary; blank until the dispatcher runs -->
![[board.base#By lane]]

---
*Capture (`fleeting` · `source`) and actions (delegate · resolve) are in the ribbon —
available in every gate. Gate switcher is the nav row above.*
