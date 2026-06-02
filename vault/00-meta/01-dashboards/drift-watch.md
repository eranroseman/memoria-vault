# Drift watch

The Linter's eight structural-detector findings in one view — silent drift between the vault source, the deployed Hermes profiles, and your working vault. Open at the [[weekly-review|weekly review]], after a plugin upgrade, or after editing a `SOUL.md` / `config.yaml` / lane-override (and redeploying). Detector definitions, severities, and remediation: [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter/) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch/).

## Active findings (last lint pass)

Empty is the goal. Each finding links to its detector — remediation lives in the [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter/).

```dataview
TABLE WITHOUT ID
  detector AS Detector,
  severity AS Severity,
  finding AS Finding,
  path AS Path,
  reported_at AS "Reported"
FROM "00-meta/02-logs/lint-findings"
WHERE active = true
SORT severity ASC, reported_at ASC
LIMIT 30
```

## Verdict band (current period)

The headline rollup — one `PASS` / `REVIEW` / `FAIL` per lint pass.

```dataview
TABLE WITHOUT ID
  period AS Period,
  verdict AS Verdict,
  finding_count AS "Findings",
  critical_count AS Critical,
  high_count AS High,
  medium_count AS Medium
FROM "00-meta/08-metrics"
WHERE type = "lint-verdict"
SORT period DESC
LIMIT 8
```

## Findings by detector (last 4 weeks)

Recurring offenders: a detector firing weekly with the same finding is a systemic issue to fix, not re-clear.

```dataview
TABLE WITHOUT ID
  detector AS Detector,
  count(rows) AS "Fired (4 wks)",
  last(rows.reported_at) AS "Last fired"
FROM "00-meta/02-logs/lint-findings"
WHERE date(reported_at) > date(today) - dur(28 days)
GROUP BY detector
SORT count(rows) DESC
```

## Schema-migration backlog

Per-template `schema_version` debt. Not a verdict-band concern (it doesn't gate work, and bumping lags authoring). Field list and the "any frontmatter change bumps `schema_version`" discipline: [schema reference](https://eranroseman.github.io/memoria-vault/reference/frontmatter/).

### Paper-notes by schema version

Current canonical is `1`. After a future bump, a version that won't drain is an unstarted migration.

```dataview
TABLE WITHOUT ID
  schema_version AS "Schema version",
  length(rows) AS "Note count",
  rows.file.link AS "Notes (oldest 5)"
FROM "20-sources/01-papers"
WHERE type = "paper-note"
GROUP BY schema_version
SORT schema_version DESC
LIMIT 8
```

### Paper-notes missing the reach fields

`pdf_uri` / `extract_path` shipped as additive v1 fields, so pre-existing notes can lack them. Empty is the goal; backfill via a Templater script, re-ingest (`hermes -p memoria-librarian run ingest --source <citekey>`), or on next touch.

```dataview
TABLE WITHOUT ID
  file.link AS Source,
  citekey AS Citekey,
  created AS Created,
  schema_version AS Version
FROM "20-sources/01-papers"
WHERE type = "paper-note" AND (pdf_uri = "" OR !pdf_uri OR extract_path = "" OR !extract_path)
SORT created ASC
LIMIT 30
```

## Related

- [[audit-log]] — per-write policy decisions, the layer below this one.
- [[fleet-health]] — operational health (cost, retries, trust score).
- Empty until the Linter runs end-to-end — see the [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch/).
