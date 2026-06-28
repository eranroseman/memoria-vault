# Board State

The Inbox board — the agent→human action queue (ADR-51). Cards in `proposed` are
waiting on you; the queue converges to empty. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/daily-glance/#board-state-support).

![[inbox.base#Needs me]]

## Everything in flight

![[inbox.base#All cards]]

## Live worker cards

```dataview
TABLE WITHOUT ID file.link AS Card, file.mtime AS Updated
FROM "system/board"
SORT file.mtime DESC
```
