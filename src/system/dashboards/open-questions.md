# Open Questions

Unconnected claims — your synthesis backlog: claims no hub holds and nothing links to
yet. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/open-questions).

```dataview
TABLE file.link AS Claim, maturity, topics
FROM "notes/claims"
WHERE lifecycle = "current" AND length(file.inlinks) = 0
SORT file.mtime ASC
```
