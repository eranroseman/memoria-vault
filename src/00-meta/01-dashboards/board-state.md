# Board State

A Dataview view of the Kanban board — reads the markdown export under `99-system/board/` (the live board is Hermes' `kanban.db`). `status` is the Hermes enum (`triage`→`archived`); `lane` is the card's `assignee`; `retry_count`/`last_updated` are exporter-denormalized (`last_updated` as ISO-8601 UTC). [Board states](https://eranroseman.github.io/memoria-vault/explanation/kanban-board/) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/daily-glance/board-state).

## Active cards

```dataview
TABLE status, assignee, reason, retry_count, last_updated
FROM "99-system/board"
WHERE status != "archived"
SORT last_updated ASC
```

## Review queue (who owes what)

```dataview
TABLE file.link AS Card, review_status, assignee AS Lane, last_updated AS "Waiting since"
FROM "99-system/board"
WHERE review_status = "requested"
SORT last_updated ASC
```

## Retry watch

```dataview
TABLE file.link AS Card, retry_count, reason, last_updated
FROM "99-system/board"
WHERE retry_count > 0 AND status != "archived"
SORT retry_count DESC
```

## Claim note maturity histogram

```dataview
TABLE length(rows.file.link) AS Count
FROM "30-synthesis/01-claims"
WHERE type = "claim-note"
GROUP BY maturity
SORT maturity ASC
```

## Enrichment freshness

```dataview
TABLE file.link AS Note, openalex_id, enriched_date
FROM "20-sources/01-papers"
WHERE enriched_date < date(today) - dur(365 days)
SORT enriched_date ASC
```
