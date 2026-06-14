---
created: 2026-06-02
updated: 2026-06-12
cssclasses:
  - dashboard
---

# Memoria

> [!info] Status glance
> ```dataviewjs
> async function load(path) {
>   const t = await dv.io.load(path);
>   return (!t || !t.trim()) ? null : t.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
> }
> const board = await load("system/logs/board-state.jsonl");   // per-run snapshots
> const lint  = await load("system/logs/lint-findings.jsonl"); // one row per finding
> if (board === null && lint === null) {
>   dv.paragraph("_Status feeds not wired yet — they appear after the first agent run._");
> } else {
>   const latest   = (board ?? []).length ? board[board.length - 1] : null;  // newest snapshot
>   const reviews  = latest?.totals?.review_queue ?? 0;
>   const blocked  = latest?.totals?.blocked ?? 0;
>   const findings = (lint ?? []).filter(e => e.severity === "HIGH" || e.severity === "CRITICAL").length;
>   const clear    = reviews === 0 && blocked === 0 && findings === 0;
>   dv.paragraph(`${clear ? "✅ " : "⚠ "}${reviews} review(s) pending · ${blocked} blocked · ${findings} HIGH/CRITICAL finding(s) — [[board-state|board]] · [[drift-watch|findings]]`);
> }
> ```

## Act

```button
name Capture fleeting
type command
action QuickAdd: Memoria: capture fleeting
```

```button
name Capture from Zotero
type command
action QuickAdd: Memoria: capture from Zotero selection
```

```button
name Capture URL
type command
action QuickAdd: Memoria: capture source from URL
```

```button
name Delegate a task
type command
action QuickAdd: Memoria: delegate a task
```

```button
name Resolve card
type command
action QuickAdd: Memoria: resolve inbox card
```

```button
name Talk to Co-PI
type command
action Agent Client: Open chat view
```

## Workspaces

```button
name Desk
type command
action QuickAdd: Memoria: workspace Desk
```

```button
name Library
type command
action QuickAdd: Memoria: workspace Library
```

```button
name Studio
type command
action QuickAdd: Memoria: workspace Studio
```

## Dashboards

> [!example]- Library — reading & synthesis
> - [[reading-pipeline|Reading Pipeline]] — sources to read & distill; claims by maturity
> - [[discuss-queue|Discuss Queue]] — read-but-not-distilled, worth a Co-PI pass
> - [[open-questions|Open Questions]] — unconnected claims (the synthesis backlog)
> - [[contradictions|Contradictions]] — open tensions to resolve

> [!example]- Maintenance — structural health
> - [[drift-watch|Drift Watch]] — open `flag`/`alert` findings
> - [[loose-ends|Loose Ends]] — Notice-level debt for the weekly pass
> - [[weekly-review|Weekly Review]] — the Friday aggregator

> [!example]- Agent ops
> - [[audit-log|Audit Log]] — the provenance trail
> - [[fleet-health|Fleet Health]] — agent operational rollup
> - [[eval-trend|Eval Trend]] — quarterly vault-eval capability scores
> - [[skill-lifecycle|Skill Lifecycle]] — which skills are active in which lane

[[research-focus|Research focus]] — your current priorities · [[troubleshooting|Troubleshooting]] — verify, fall back, recover
