# Open Questions

Every claim/paper note carrying an explicit `Open questions` section — the vault as a research agenda. Open when planning the next direction; filter by project or MOC as needed. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/open-questions).

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "30-synthesis/01-claims" OR "20-sources/01-papers"
WHERE contains(file.content, "# Open questions") OR contains(file.content, "Open questions")
SORT file.mtime DESC
```
