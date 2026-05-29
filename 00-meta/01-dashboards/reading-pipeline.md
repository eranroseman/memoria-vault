# `reading-pipeline.md` — what to read next

**Location.** `00-meta/01-dashboards/reading-pipeline.md`

**Decision.** Keep papers flowing through the pipeline; surface what's stuck. Use when the inbox feels full and you need to decide what to process next.

## Papers in active processing

```dataview
TABLE file.link AS Note, lifecycle, study_design, topic
FROM "20-sources/01-papers"
WHERE lifecycle = "proposed"
SORT file.mtime DESC
```

## Claim notes by maturity

```dataview
TABLE file.link AS Note, maturity, sources
FROM "30-synthesis/01-claims"
SORT maturity DESC, file.mtime DESC
```
