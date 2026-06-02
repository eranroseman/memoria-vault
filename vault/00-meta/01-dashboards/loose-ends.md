# Loose Ends

Junk filenames (`TODO`, `tmp`, `untitled`) and unfinished notes. Run after ingest batches or at the weekly review; > 5 is a cleanup signal. Action: rename, finish, archive, or delete. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/loose-ends).

```dataview
TABLE file.link AS Note, file.folder, file.mtime AS Modified
FROM ""
WHERE contains(file.name, "TODO") OR contains(file.name, "tmp") OR contains(file.name, "untitled")
SORT file.mtime DESC
```
