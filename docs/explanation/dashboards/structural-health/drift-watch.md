---
title: drift-watch dashboard
parent: Structural health
nav_order: 1
grand_parent: Dashboards
---

# `drift-watch` dashboard

Surfaces the Linter's eight structural-detector findings as one consolidated view. Open it when something feels wrong but the system looks clean — a lint pass came back clear yet things still seem off. The verdict band at the top (PASS / REVIEW / FAIL) is the headline; the per-detector findings below are the diagnosis.

## What it shows

The dashboard reads from `99-system/logs/lint-findings.jsonl`, written by the Linter on each scheduled pass. Each of the eight structural detectors produces findings; the dashboard groups them by detector and shows the verdict band rollup.

**Verdict band:**

- `PASS` — no HIGH or CRITICAL findings
- `REVIEW` — MEDIUM findings present, no HIGH
- `FAIL` — any HIGH or CRITICAL finding; scheduled work pauses until resolved

Schema migration progress also appears here — per-template `schema_version` rollups (e.g., "127 notes still on schema v1") share the dashboard because they represent related drift surfaces.

## What it is not

**Not audit-log.** The audit log records per-write policy MCP decisions. Drift-watch records per-lint-pass structural findings. Different cadence, different layer.

**Not fleet-health.** Fleet-health is operational (cost, latency, success rate). Drift-watch is structural (source-vs-deployed-profile-vs-working-vault alignment). They are complementary: verdict band is the structural headline; trust score is the operational headline.

**Not for data hygiene.** Orphan notes, stale enrichment, and broken wikilinks surface in weekly-review and the lint report, not here. The structural detectors are reserved for structural drift between vault source, deployed Hermes profiles, and working vault state — the "silent" failures the human wouldn't notice by reading content.

## When drift-watch becomes relevant

Drift-watch is most useful after changes that could desynchronize the working vault from the deployed configuration: plugin upgrades, edits to profile `SOUL.md` files or lane-override files, or any event that appears in the audit log as an anomaly. The structural detectors exist precisely because these desynchronizations are invisible at the content level — the vault looks clean because the content is unchanged, but the structural alignment between source, deployed profiles, and working vault has shifted.

The Friday weekly review includes a drift-watch pass because a week of ordinary operation also accumulates small drift signals that are not individually urgent but benefit from regular review.

## Before it has real data

Until the Linter is running end-to-end and writing to `99-system/logs/lint-findings.jsonl`, this dashboard shows a placeholder. Daily-health shows the last-24h HIGH and CRITICAL findings (a filtered subset) once the Linter is active.

## Related

- [The Linter](../../profiles/linter.md) — the eight structural detectors and what each catches
- [audit-log dashboard](../operational-health/audit-log.md) — per-decision forensics layer below structural drift
- [Linter: detectors and auto-fix](../../../reference/linter.md#the-eight-structural-detectors) — structural-detector severity table
