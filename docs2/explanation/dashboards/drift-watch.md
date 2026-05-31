# `drift-watch` dashboard

Surfaces the Linter's eight structural-detector findings as one consolidated view. Open it when something feels wrong but the system looks clean — a lint pass came back clear yet things still seem off. The verdict band at the top (PASS / REVIEW / FAIL) is the headline; the per-detector findings below are the diagnosis.

## What it shows

The dashboard reads from `00-meta/02-logs/lint-findings.jsonl`, written by the Linter on each scheduled pass. Each of the eight M-detectors produces findings; the dashboard groups them by detector and shows the verdict band rollup.

**Verdict band:**
- `PASS` — no HIGH or CRITICAL findings
- `REVIEW` — MEDIUM findings present, no HIGH
- `FAIL` — any HIGH or CRITICAL finding; scheduled work pauses until resolved

Schema migration progress also appears here — per-template `schema_version` rollups (e.g., "127 notes still on schema v1") share the dashboard because they represent related drift surfaces.

## What it is not

**Not audit-log.** The audit log records per-write policy MCP decisions. Drift-watch records per-lint-pass structural findings. Different cadence, different layer.

**Not fleet-health.** Fleet-health is operational (cost, latency, success rate). Drift-watch is structural (source-vs-deployed-profile-vs-working-vault alignment). They are complementary: verdict band is the structural headline; trust score is the operational headline.

**Not for data hygiene.** Orphan notes, stale enrichment, and broken wikilinks surface in weekly-review and the lint report, not here. The M-detectors are reserved for structural drift between vault source, deployed Hermes profiles, and working vault state — the "silent" failures the human wouldn't notice by reading content.

## When to open it

- During the weekly Friday review
- After accepting a plugin upgrade
- After editing a profile's SOUL.md or a lane-override file and re-running the installer
- When an audit-log anomaly suggests a configuration problem

## Before it has real data

Until the Linter is running end-to-end and writing to `00-meta/02-logs/lint-findings.jsonl`, this dashboard shows a placeholder. Daily-health shows the last-24h HIGH and CRITICAL findings (a filtered subset) once the Linter is active.

## Related

- [explanation/profiles/linter.md](../profiles/linter.md) — the eight M-detectors and what each catches
- [reference/profiles.md](../../reference/profiles.md#linter-eight-m-detectors) — M-detector severity table
- [explanation/dashboards/audit-log.md](audit-log.md) — per-decision forensics layer below structural drift
