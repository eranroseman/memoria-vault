---
title: Maintenance
type: maintenance
lifecycle: current
cssclasses: memoria-space
---

# Maintenance

> [!brief] Weekly structural debt lives here: drift, loose ends, and worker-board state.

## Drift watch

![[inbox.base#Drift watch]]

## Loose ends

![[inbox.base#Loose ends]]

## Board

![[board.base#By lane]]

## New this week — catalog

```dataview
TABLE file.link AS Entity, type
FROM "catalog"
WHERE sample != true AND file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```

## New this week — notes

```dataview
TABLE file.link AS Note, type, lifecycle
FROM "notes"
WHERE sample != true AND file.ctime >= date(today) - dur(7 days) AND type != "fleeting"
SORT file.ctime DESC
```
