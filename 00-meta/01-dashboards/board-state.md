# `board-state.md` — Kanban board summary (optional)

**Location.** `00-meta/01-dashboards/board-state.md`

**Decision.** A Dataview view of cards on the Kanban board. Only useful if the board is markdown-backed (or if there's a markdown export).

## Active cards

```dataview
TABLE status, assignee, lane, blocked_reason, retry_count, last_updated
FROM "00-meta/board"
WHERE status != "done"
SORT last_updated ASC
```

## Review queue (who owes what)

```dataview
TABLE file.link AS Card, review_status, review_owner, review_requested_at
FROM "00-meta/board"
WHERE review_status = "requested" OR review_status = "in-review"
SORT review_requested_at ASC
```

## Retry watch

```dataview
TABLE file.link AS Card, retry_count, blocked_reason, last_updated
FROM "00-meta/board"
WHERE retry_count > 0 AND status != "done"
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
