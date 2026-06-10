# Contradictions

Open tensions — claims carrying a typed `contradicts` link, unresolved until one side
is retracted or superseded (ADR-09/ADR-52). [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/contradictions).

```dataview
TABLE file.link AS Claim, links.contradicts AS Contradicts, maturity
FROM "notes/claims"
WHERE lifecycle = "current" AND links.contradicts
SORT file.mtime DESC
```
