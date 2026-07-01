---
title: Maintenance
projection: maintenance
cssclasses: memoria-space
---

# Maintenance

> [!brief] Weekly structural debt lives here: drift, loose ends, and worker-board state.

## Drift watch

Trace and quarantine findings are recorded in `journal/` and `.memoria/quarantine/`.

## Loose ends

Unchecked Concepts are visible in the bundle Bases until promoted.

## Board

Worker request state lives in `.memoria/memoria.sqlite`.

## New this week — catalog

```dataview
TABLE file.link AS Entity, type
FROM "catalog"
WHERE sample != true AND file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```

## New this week — notes

```dataview
TABLE file.link AS Note, type, check_status
FROM "knowledge"
WHERE sample != true AND file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```
