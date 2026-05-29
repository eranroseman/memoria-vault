# `open-questions.md` — research agenda view

**Location.** `00-meta/01-dashboards/open-questions.md`

**Decision.** Turn the vault into a research agenda by surfacing all explicit open questions. Use when planning the next research direction. Filter further by project or MOC as needed.

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "30-synthesis/01-claims" OR "20-sources/01-papers"
WHERE contains(file.content, "# Open questions") OR contains(file.content, "Open questions")
SORT file.mtime DESC
```
