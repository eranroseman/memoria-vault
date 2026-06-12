---
created: 2026-06-02
updated: 2026-06-10
cssclasses:
  - dashboard
---

# Memoria

The front door — opened on launch by the [obsidian-homepage](https://eranroseman.github.io/memoria-vault/reference/obsidian-plugins) plugin. Consumer-only: it embeds views and owns no logic, so it can't drift or error. Above the fold: **what needs me?** Below: the detail dashboards, on demand.

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
>   const stamp    = latest?.timestamp ? ` · as of ${latest.timestamp.slice(11, 16)} UTC` : "";
>   dv.paragraph(`${clear ? "✅ All clear — " : "⚠ "}${reviews} review(s) pending · ${blocked} blocked · ${findings} HIGH/CRITICAL finding(s)${stamp}`);
> }
> ```

## What needs me

The Inbox — cards in `proposed` are waiting on your decision; the queue converges to
empty. Full board: [[board-state|Board State]].

![[inbox.base#Needs me]]

## Start here

- [[research-focus|Research focus]] — your current priorities; read and refresh at
  session start (the Librarian reads it too).
- **Talk to the co-PI** — open the ACP pane (`Agent Client: Open chat view`). One
  conversation partner: it questions, explains the system, and delegates tasks to the
  background lanes for you.
- **Capture / create** — `Cmd/Ctrl-P → Memoria:` `capture fleeting`

## Dashboards

> [!example]- Library — reading & synthesis
> - [[reading-pipeline|Reading Pipeline]] — sources to read & distill; claims by maturity
> - [[discuss-queue|Discuss Queue]] — read-but-not-distilled, worth a co-PI pass
> - [[open-questions|Open Questions]] — unconnected claims (the synthesis backlog)
> - [[contradictions|Contradictions]] — open tensions to resolve

> [!example]- Maintenance — structural health
> - [[drift-watch|Drift Watch]] — open `flag`/`alert` findings
> - [[loose-ends|Loose Ends]] — Notice-level debt for the weekly pass
> - [[weekly-review|Weekly Review]] — the Friday aggregator

> [!example]- Agent ops
> - [[board-state|Board State]] — the Inbox board + live worker cards
> - [[audit-log|Audit Log]] — the provenance trail
> - [[fleet-health|Fleet Health]] — agent operational rollup
> - [[eval-trend|Eval Trend]] — quarterly vault-eval capability scores

## Reference

- [[troubleshooting|Troubleshooting]] — verify the system, fall back, recover (the one
  help note kept in-vault, for when you're offline/broken)
- Everything else is on the website: [schema / frontmatter](https://eranroseman.github.io/memoria-vault/reference/frontmatter) · [profiles & roles](https://eranroseman.github.io/memoria-vault/explanation/profiles/) · [who-writes-where](https://eranroseman.github.io/memoria-vault/reference/policy-mcp) · [Architecture](https://eranroseman.github.io/memoria-vault/explanation/architecture/) · [Setup](https://eranroseman.github.io/memoria-vault/how-to-guides/setup/)

## Full documentation

→ <https://eranroseman.github.io/memoria-vault/> — tutorials, how-to guides, reference, and architecture explanation.
