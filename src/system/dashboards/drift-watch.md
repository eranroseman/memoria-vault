# Drift Watch

Active and imminent drift — the Linter's and the sweeps' open findings (`flag` /
`alert` cards still in `proposed`). HIGH findings also push to Home. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch).

```dataview
TABLE file.link AS Card, type, finding, loudness
FROM "inbox"
WHERE (type = "flag" OR type = "alert") AND lifecycle = "proposed"
SORT loudness DESC, file.ctime ASC
```
