# Discuss Queue

Sources you've read but not yet distilled — worth a pass with the Co-PI (Ask) before
the claims firm up. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/discuss-queue).

```dataview
TABLE file.link AS Source, entity, research_area
FROM "notes/sources"
WHERE lifecycle = "provisional"
SORT file.mtime ASC
```
