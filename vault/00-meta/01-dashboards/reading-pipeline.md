# Reading Pipeline

Papers still being classified (`lifecycle: proposed`) and claim notes by maturity — what's in flight. Open when the inbox feels full and you need to pick what to process next. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/reading-pipeline/).

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
