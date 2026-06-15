---
created: 2026-06-02
updated: 2026-06-12
cssclasses:
  - dashboard
---

# Memoria

> [!info] Status line
> ```dataviewjs
> async function loadJsonl(path) {
>   const text = await dv.io.load(path);
>   return (!text || !text.trim()) ? [] : text.trim().split("\n").filter(Boolean).map(line => JSON.parse(line));
> }
> function linterFallback(rows) {
>   const sev = rows.map(row => row.severity).filter(Boolean);
>   if (sev.includes("CRITICAL")) return "FAIL";
>   if (sev.includes("HIGH") || sev.includes("MEDIUM")) return "REVIEW";
>   return rows.length ? "PASS" : "--";
> }
> const boardRows = await loadJsonl("system/logs/board-state.jsonl");
> const lintRows = await loadJsonl("system/logs/lint-findings.jsonl");
> const verdicts = dv.pages('"system/metrics"')
>   .where(page => page.type === "lint-verdict")
>   .sort(page => page.period ?? page.file.name, "desc");
> const latest = boardRows.length ? boardRows[boardRows.length - 1] : null;
> const totals = latest?.totals ?? {};
> const verdict = verdicts.length ? verdicts[0].verdict : linterFallback(lintRows);
> const icon = verdict === "FAIL" ? "✕" : verdict === "REVIEW" ? "!" : verdict === "PASS" ? "✓" : "…";
> const active = totals.running ?? 0;
> const waiting = totals.blocked ?? 0;
> const review = totals.review_queue ?? 0;
> const retries = totals.retrying ?? 0;
> const urgentCards = dv.pages('"inbox"').where(page => page.lifecycle === "proposed" && ["alert", "block"].includes(page.loudness));
> const alerts = urgentCards.where(page => page.loudness === "alert").length;
> const blocks = urgentCards.where(page => page.loudness === "block").length;
> dv.paragraph(`${icon} ${verdict} · Active: ${active} · Waiting: ${waiting} · Review: ${review} · Retries: ${retries} · Alerts: ${alerts} · Blocks: ${blocks} — [[board-state|board]] · [[drift-watch|findings]]`);
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
action QuickAdd: Memoria: delegate task
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
action QuickAdd: Memoria: open Desk workspace
```

```button
name Library
type command
action QuickAdd: Memoria: open Library workspace
```

```button
name Studio
type command
action QuickAdd: Memoria: open Studio workspace
```

## Dashboards

> [!example]- Library — reading & synthesis
> - [[library|Library]] — source, Catalog, and claim objects in one gate
> - [[reading-pipeline|Reading Pipeline]] — sources to read & distill; claims by maturity
> - [[discuss-queue|Discuss Queue]] — read-but-not-distilled, worth a Co-PI pass
> - [[open-questions|Open Questions]] — unconnected claims (the synthesis backlog)
> - [[contradictions|Contradictions]] — open tensions to resolve

> [!example]- Desk — action queue
> - [[desk|Desk]] — next PI actions, capture, delegation, and worker state
> - [[board-state|Board State]] — the full Inbox board and worker cards

> [!example]- Maintenance — structural health
> - [[drift-watch|Drift Watch]] — open `flag`/`alert` findings
> - [[loose-ends|Loose Ends]] — Notice-level debt for the weekly pass
> - [[weekly-review|Weekly Review]] — the Friday aggregator

> [!example]- Agent ops
> - [[studio|Studio]] — focus, claim corpus, and pattern library for synthesis
> - [[audit-log|Audit Log]] — the provenance trail
> - [[fleet-health|Fleet Health]] — agent operational rollup
> - [[eval-trend|Eval Trend]] — quarterly vault-eval capability scores
> - [[skill-lifecycle|Skill Lifecycle]] — which skills are active in which lane

[[research-focus|Research focus]] — your current priorities · [[troubleshooting|Troubleshooting]] — verify, fall back, recover
