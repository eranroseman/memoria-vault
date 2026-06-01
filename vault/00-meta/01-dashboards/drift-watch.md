# `drift-watch.md` — structural drift findings

**Location.** `00-meta/01-dashboards/drift-watch.md`

**Decision.** Surface the Linter's eight structural detector findings as one consolidated view. Each detector catches a specific kind of silent drift the human wouldn't otherwise notice. This is the dashboard you open when something feels off — the lint pass passed but the system still seems wrong.

**When to open.** Weekly review (Friday ritual); after accepting a plugin upgrade; after editing a profile's `SOUL.md` / `config.yaml` or a lane-override file (and re-running `install.ps1`); when an [audit-log](audit-log.md) anomaly suggests a configuration drift.

## The eight detectors

For the full definitions, severities, and remediation paths, see [the Linter's M-detectors reference](../../.memoria/profiles/memoria-linter/M-detectors.md). At a glance:

| ID | Detector | What it catches | Severity |
| --- | --- | --- | --- |
| `profile-install-drift` | Profile install drift | A deployed `~/.hermes/profiles/memoria-<name>/` file differs from its source at `.memoria/profiles/memoria-<name>/` (hand-edit to the install, or `git pull` without re-running `install.ps1`) | LOW |
| `vault-hash-drift` | Vault hash drift | Vault file modified outside the policy MCP (tamper or out-of-band edit) | CRITICAL |
| `skeleton-drift` | Skeleton note drift | Human notes in `00-meta/` lagging the engineering spec | MEDIUM |
| `dashboard-field-drift` | Dashboard field drift | Dataview query references a frontmatter field no template emits | HIGH |
| `command-vocab-drift` | Command vocabulary drift | A command in the design isn't declared in its owner AGENTS file | MEDIUM |
| `plugin-config-drift` | Plugin-config drift | Human's `data.json` files diverge from shipped plugin-config templates | MEDIUM (HIGH on `autoAllowPermissions` escalation) |
| `orphan-working-files` | Orphan working files | `.tmp.*`, `.bak`, editor backups, manual-rename leftovers outside transient zones | LOW |
| `extract-path-broken` | Extract path broken link | Paper-note's `extract_path` frontmatter points to a missing extract file | HIGH |

## Active findings (last lint pass)

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

Empty result is the goal. The Linter writes per-finding entries to `00-meta/02-logs/lint-findings/` (or aggregated into a single JSONL the Linter rotates) when a detector fires; findings are cleared when the human either resolves the drift or marks it as accepted (with a note).

## Verdict band (current period)

The headline rollup. Each lint pass produces one verdict (PASS / REVIEW / FAIL) from its findings — definitions and gating rules in the [Linter SOUL.md](../../.memoria/profiles/memoria-linter/SOUL.md).

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

Time-series view to spot which detectors are recurring offenders. A detector that fires every week with the same finding indicates a systemic issue — either a process the human should change or a configuration that needs revising.

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

## Schema migration progress

Per-template progress against the current canonical `schema_version`. Migration debt isn't a verdict-band concern — it doesn't gate scheduled work, and bumping `schema_version` is expected to lag note authoring. This section tracks the backlog human-side; the Linter's schema-version-mismatch check (data-hygiene tier, not a structural detector) surfaces the same data in the lint report.

**Why this lives here, not as a structural detector.** Per-field "old note missing new field" checks are noisy on day-one — every legacy note flags. The right primitive is `schema_version` on the note plus a single rollup query, not one detector per field. See [[../04-reference/schema-reference|schema-reference]] for the authoritative field list; the design doc covers the "any frontmatter change bumps schema_version" discipline.

### Paper-notes by schema version

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

Read this as a histogram: the current canonical version (e.g., `2`) should accumulate over time; older versions should drain. A version that isn't draining is a migration the human hasn't started; a version that has very few notes left is a long-tail candidate for manual cleanup.

### Paper-notes missing the new reach fields

Per-field progress for the v1 → v2 migration that added `pdf_uri` and `extract_path`. Use this to spot which specific notes need backfill — `schema-migrate --dry-run` proposes the changes, but seeing the actual list helps the human decide between auto-script-backfill and selective re-ingest.

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

Empty result is the goal — every paper-note has both reach fields populated. Oldest-first sort surfaces the longest-stalled notes for prioritization. Cap is 30 to keep the dashboard responsive; if the backlog is larger, work it down in batches.

### Migration approaches

Three ways to pay down what this query surfaces, in increasing effort:

1. **Templater backfill script.** For fields derivable from existing frontmatter (e.g., `pdf_uri` constructed from `zotero_uri` by string-replacing `select` with `open-pdf`), a one-shot Templater run writes the new field across the corpus. Cheap; works for most v1 → v2 cases here because `zotero_uri` already exists.
2. **Re-ingest.** `hermes -p memoria-librarian run ingest --source <citekey>` reruns the full pipeline including Marker extraction. Required when `extract_path` is missing (no extract file exists yet). Expensive — Marker runs are non-trivial — but produces the fully-populated note.
3. **Touch-driven.** Leave the backlog alone; old notes get updated when the human next opens them. Acceptable for cold corpus areas (finished projects, deprecated topics); not acceptable for actively-read areas where the missing fields would block daily workflow.

## What this dashboard does not do

- **Not the same as `audit-log.md`.** The [audit-log dashboard](audit-log.md) shows policy MCP decisions (per write attempt). This dashboard shows structural detector findings (per lint pass). Different cadence, different abstraction layer.
- **Not actionable on its own.** Every finding links back to its detector's documentation; the remediation lives there, not here. This dashboard surfaces *which* drift, not *how to fix*.
- **Not for data-hygiene checks.** Orphan notes, stale enrichment, broken wikilinks are surfaced by the [`weekly-review`](weekly-review.md) and the lint report itself, not here. Structural detectors are reserved for structural drift between the vault source, the deployed Hermes profiles, and the human's working vault state.

## Graceful degradation

- **Until the Linter is implemented end-to-end**, this dashboard is largely empty (or filled with placeholder rows from `lint-findings/` if the human is manually entering test findings). That's expected — see docs/explanation/dashboards/README.md for the discipline.
- **Until `plugin-config-drift` is wired**, the `plugin-config-drift` row in the active findings query won't fire even if `data.json` files drift. Under direct profile management `plugin-config-drift` compares the human's working `.obsidian/plugins/<plugin>/data.json` against the version at the latest git HEAD; the `data.json` suffix conventions are in `docs/reference/plugins.md`.
- **Until `extract-path-broken` is wired**, the `extract-path-broken` row won't fire even if `extract_path` values point at missing files. Until then the "Paper-notes missing the new reach fields" query above gives partial coverage — it surfaces empty `extract_path` values, but doesn't catch the silent-failure case where the path is populated but the file is gone. `extract-path-broken` in the [Linter's M-detectors reference](../../.memoria/profiles/memoria-linter/M-detectors.md) covers that case explicitly.

## Related

- [Linter SOUL.md](../../.memoria/profiles/memoria-linter/SOUL.md) — canonical detector definitions and verdict-band rules.
- [`audit-log.md`](audit-log.md) — per-decision forensics, the layer below this one.
- [`fleet-health.md`](fleet-health.md) — operational health (cost, retries, trust score). Different concern; complementary view.
