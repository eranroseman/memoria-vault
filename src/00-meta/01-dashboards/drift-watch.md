# Drift watch

The Linter's eight structural-detector findings in one view — silent drift between the vault source, the deployed Hermes profiles, and your working vault. Open at the [[weekly-review|weekly review]], after a plugin upgrade, or after editing a `SOUL.md` / `config.yaml` / lane-override (and redeploying). Detector definitions, severities, and remediation: [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch).

## Active findings (last lint pass)

Empty is the goal. Each finding links to its detector — remediation lives in the [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter).

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
if (!text || !text.trim()) { dv.paragraph("✅ No findings."); return; }
const rank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const rows = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l))
  .sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9)
                  || (b.timestamp ?? "").localeCompare(a.timestamp ?? "")).slice(0, 30);
if (!rows.length) { dv.paragraph("✅ No findings."); return; }
dv.table(["Detector", "Severity", "Finding", "Path", "Reported"],
  rows.map(e => [e.detector, e.severity, e.message, e.path, (e.timestamp ?? "").slice(0, 10)]));
```

## Verdict band (by period)

The headline rollup — one `PASS` / `REVIEW` / `FAIL` per lint period, written by `metrics_aggregate.py` from the period's findings (any `CRITICAL` → FAIL; any `HIGH`/`MEDIUM` → REVIEW; else PASS). Most recent first.

```dataview
TABLE WITHOUT ID
  period AS Period,
  verdict AS Verdict,
  finding_count AS "Findings",
  critical_count AS Critical,
  high_count AS High,
  medium_count AS Medium
FROM "99-system/metrics"
WHERE type = "lint-verdict"
SORT period DESC
LIMIT 8
```

## Findings by detector (last 4 weeks)

Recurring offenders: a detector firing repeatedly with the same finding is a systemic issue to fix at the source, not re-clear one by one.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
if (!text || !text.trim()) { dv.paragraph("✅ No findings."); return; }
const cutoff = new Date(Date.now() - 28 * 864e5).toISOString();
const ev = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l))
  .filter(e => (e.timestamp ?? "") >= cutoff);
const by = {};
for (const e of ev) { (by[e.detector] ??= { n: 0, last: "" }); by[e.detector].n++;
  if ((e.timestamp ?? "") > by[e.detector].last) by[e.detector].last = e.timestamp; }
const rows = Object.entries(by).sort((a, b) => b[1].n - a[1].n);
if (!rows.length) { dv.paragraph("✅ No findings in the last 4 weeks."); return; }
dv.table(["Detector", "Fired (4 wks)", "Last fired"],
  rows.map(([d, v]) => [d, v.n, (v.last ?? "").slice(0, 10)]));
```

## Schema-migration backlog

Per-template `schema_version` debt. Not a verdict-band concern (it doesn't gate work, and bumping lags authoring). Field list and the "any frontmatter change bumps `schema_version`" discipline: [schema reference](https://eranroseman.github.io/memoria-vault/reference/frontmatter).

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

- [[audit-log|Audit log]] — per-write policy decisions, the layer below this one.
- [[fleet-health|Fleet Health]] — operational health (cost, retries, trust score).
- Empty until the Linter runs end-to-end — see the [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch).
