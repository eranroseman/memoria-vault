# `schema-hygiene.md` — catch leftover junk

**Location.** `00-meta/05-dashboards/schema-hygiene.md`

**Decision.** Catch junk filenames and notes the agent or human forgot to finish. Run after ingest batches or whenever something feels off. The action: rename, finish, archive, or delete.

```dataview
TABLE file.link AS Note, file.folder, file.mtime AS Modified
FROM ""
WHERE contains(file.name, "TODO") OR contains(file.name, "tmp") OR contains(file.name, "draft") OR contains(file.name, "untitled")
SORT file.mtime DESC
```
