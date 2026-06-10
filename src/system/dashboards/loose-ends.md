# Loose Ends

Structural debt at Notice loudness — cosmetic and low-stakes findings batched for the
weekly review, never pushed. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/loose-ends).

```dataview
TABLE file.link AS Card, type, finding, raised_by
FROM "inbox"
WHERE type = "flag" AND loudness = "notice" AND lifecycle = "proposed"
SORT file.ctime ASC
```
