# Weekly Review

The Friday aggregator — everything at Notice loudness plus the week's movement, in one
sitting. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/weekly-review).

## Notice-level findings

```dataview
TABLE file.link AS Card, type, finding
FROM "inbox"
WHERE loudness = "notice" AND lifecycle = "proposed"
SORT type ASC
```

## New this week — catalog

```dataview
TABLE file.link AS Entity, type
FROM "catalog"
WHERE file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```

## New this week — notes

```dataview
TABLE file.link AS Note, type, lifecycle
FROM "notes"
WHERE file.ctime >= date(today) - dur(7 days) AND type != "fleeting"
SORT file.ctime DESC
```

## Fleeting backlog

This is the same proposed fleeting queue embedded in the Inbox space. Distill, attach, or archive each note; do not review these again in **New this week — notes**.

![[fleeting.base#To process]]
