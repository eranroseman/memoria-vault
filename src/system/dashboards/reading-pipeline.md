# Reading Pipeline

Sources awaiting your reading and distillation, and claims by maturity — what's in
flight on the Library side. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/reading-pipeline).

## To read & distill

```dataview
TABLE file.link AS Note, entity, source_type
FROM "notes/source"
WHERE lifecycle = "proposed"
SORT file.mtime DESC
```

## Claims by maturity

```dataview
TABLE file.link AS Note, maturity, sources
FROM "notes/claims"
WHERE lifecycle = "current"
SORT maturity DESC, file.mtime DESC
```

![[claims.base#By maturity]]
