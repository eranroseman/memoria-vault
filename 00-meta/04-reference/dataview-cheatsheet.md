# Dataview cheatsheet

Reference patterns for dashboard authors. Companion to [surfaces/persistent.md](../../../memoria-docs/surfaces/persistent.md).

## TABLE — the most common

````dataview
TABLE
  file.mtime AS "Modified",
  lifecycle AS "Status"
FROM "20-sources/01-papers"
WHERE lifecycle = "proposed"
SORT file.mtime DESC
LIMIT 20
````

## LIST — when you just want links

````dataview
LIST
FROM "30-synthesis/01-claims"
WHERE maturity = "seedling"
SORT file.ctime DESC
````

## TASK — for inline TODO surfacing

````dataview
TASK
FROM "10-inbox"
WHERE !completed
````

## FLATTEN — one row per array item

````dataview
TABLE flat-source AS Source, file.link AS Note
FROM "30-synthesis"
FLATTEN sources AS flat-source
````

## Multi-field SORT

```
SORT verdict ASC, severity DESC, file.mtime DESC
```

## Folder-scoped FROM (mandatory for performance)

Always: `FROM "10-inbox"` (narrow). Never: `FROM ""` (vault-wide) unless truly required.

## FILTER by field presence

- `WHERE topic` — only notes that have a `topic` field
- `WHERE !topic` — only notes that don't
- `WHERE contains(topic, "hci")` — notes whose `topic` includes "hci"

## dataviewjs — for external file reads

````dataviewjs
const data = await dv.io.load("00-meta/02-logs/audit.jsonl");
const events = data.trim().split("\n").map(l => JSON.parse(l));
const recent = events.filter(e => new Date(e.timestamp) > moment().subtract(24, "hours"));
dv.table(["Time", "Action", "Decision"], recent.map(e => [e.timestamp, e.action, e.decision]));
````

Use sparingly — only when TABLE / LIST can't handle the query. dataviewjs is harder to read and slower to render.

## Common patterns

### Pending review

```
WHERE review_status = "requested"
SORT file.mtime ASC
```

### Stale enrichment

```
WHERE _enrichment AND enriched_date < date(today) - dur(30 days)
```

### Orphan claims

```
FROM "30-synthesis/01-claims"
WHERE length(file.inlinks) = 0
```

---

**For depth:** [Dataview docs](https://blacksmithgu.github.io/obsidian-dataview/). [surfaces/persistent.md#performance-discipline](../../../memoria-docs/surfaces/persistent.md#performance-discipline) for query-shape rules.

**Promotion bar.** When a new query pattern proves useful across two or more dashboards, add it here. The cheatsheet is the operational complement to the dashboard discipline doc.
