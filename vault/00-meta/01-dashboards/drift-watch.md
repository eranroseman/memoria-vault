# Drift watch

The Linter's eight structural-detector findings in one view — silent drift between the vault source, the deployed Hermes profiles, and your working vault. Open at the [[weekly-review|weekly review]], after a plugin upgrade, or after editing a `SOUL.md` / `config.yaml` / lane-override (and redeploying). Detector definitions, severities, and remediation: [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter/) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch/).

## Active findings (last lint pass)

Empty is the goal. Each finding links to its detector — remediation lives in the [Linter reference](https://eranroseman.github.io/memoria-vault/reference/linter/).

```dataviewjs
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
if (!text || !text.trim()) { dv.paragraph("✅ No findings."); return; }
const rank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const rows = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l))
  .sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9)).slice(0, 30);
if (!rows.length) { dv.paragraph("✅ No findings."); return; }
dv.table(["Detector", "Severity", "Finding", "Path"],
  rows.map(e => [e.detector, e.severity, e.message, e.path]));
```

## Verdict (current lint pass)

The headline rollup, computed live from the findings above: any `CRITICAL` → **FAIL**; any `HIGH`/`MEDIUM` → **REVIEW**; otherwise **PASS**. (Per-period history would need a periodized `lint-verdict` note from the metrics aggregator — not yet wired.)

```dataviewjs
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
const ev = (text && text.trim()) ? text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l)) : [];
const n = s => ev.filter(e => e.severity === s).length;
const crit = n("CRITICAL"), high = n("HIGH"), med = n("MEDIUM");
const verdict = crit ? "🔴 FAIL" : (high || med) ? "🟡 REVIEW" : "🟢 PASS";
dv.paragraph(`**${verdict}** — ${ev.length} finding(s): ${crit} critical · ${high} high · ${med} medium`);
```

## Findings by detector (current pass)

Which detectors are firing now — a detector with many findings is a systemic issue to fix at the source, not re-clear one by one. (Cross-pass recurrence needs timestamped findings, which the lean `Finding` schema doesn't carry.)

```dataviewjs
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
if (!text || !text.trim()) { dv.paragraph("✅ No findings."); return; }
const ev = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const by = {};
for (const e of ev) by[e.detector] = (by[e.detector] ?? 0) + 1;
const rows = Object.entries(by).sort((a, b) => b[1] - a[1]);
if (!rows.length) { dv.paragraph("✅ No findings."); return; }
dv.table(["Detector", "Count"], rows.map(([d, c]) => [d, c]));
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

- [[audit-log|Audit log]] — per-write policy decisions, the layer below this one.
- [[fleet-health|Fleet Health]] — operational health (cost, retries, trust score).
- Empty until the Linter runs end-to-end — see the [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/structural-health/drift-watch/).
