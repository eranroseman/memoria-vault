---
created: 2026-06-02
updated: 2026-06-02
---

# Memoria

The vault front door — opened on launch by the [obsidian-homepage](https://eranroseman.github.io/memoria-vault/reference/obsidian-plugins/) plugin. A launchpad: it surfaces one status glance and routes you everywhere else.

> [!info] Status — full view in [[daily-health|Daily Health]]
> ```dataviewjs
> async function load(path) {
>   const t = await dv.io.load(path);
>   return (!t || !t.trim()) ? null : t.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
> }
> const board = await load("99-system/logs/board-state.jsonl");
> const lint  = await load("99-system/logs/lint-findings.jsonl");
> if (board === null && lint === null) {
>   dv.paragraph("_Status feeds not wired yet — see [[daily-health|Daily Health]]._");
> } else {
>   const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
>   const reviews  = (board ?? []).filter(e => e.review_status === "requested").length;
>   const blocked  = (board ?? []).filter(e => e.state === "blocked").length;
>   const findings = (lint ?? []).filter(e => e.reported_at >= cutoff && (e.severity === "HIGH" || e.severity === "CRITICAL")).length;
>   const clear = reviews === 0 && blocked === 0 && findings === 0;
>   dv.paragraph(`${clear ? "✅ All clear — " : "⚠ "}${reviews} review(s) pending · ${blocked} blocked · ${findings} HIGH/CRITICAL finding(s) (24h)`);
> }
> ```

## Do

- `Cmd/Ctrl-P → Memoria:` — `capture fleeting` · `ask about this note` (Socratic) · `new project` · `lint this note` · `find related notes` · `similarity-check this claim`
- Mode-switch in the ACP pane: `Ctrl+Shift+1` Ask · `2` Map · `3` Draft · `4` Check

## Monitor

→ [[daily-health|Daily Health]] (start of session) · all dashboards below

- [[discuss-queue|Reading queue]] — classified papers not yet processed
- [[board-state|Board state]] — full Kanban
- [[weekly-review|Weekly review]] — the Friday ritual
- [[open-questions|Open questions]] · [[contradictions|Contradictions]] · [[reading-pipeline|Reading pipeline]]
- [[drift-watch|Drift watch]] · [[fleet-health|Fleet health]] · [[audit-log|Audit log]] · [[loose-ends|Loose ends]]

## Reference

- [[troubleshooting|Troubleshooting]] — verify the system, fall back, recover (the one help note kept in-vault, for when you're offline/broken)
- Everything else is on the website: [schema / frontmatter](https://eranroseman.github.io/memoria-vault/reference/frontmatter/) · [profiles & roles](https://eranroseman.github.io/memoria-vault/explanation/profiles/) · [who-writes-where](https://eranroseman.github.io/memoria-vault/reference/policy-mcp/) · [architecture](https://eranroseman.github.io/memoria-vault/explanation/architecture/) · [setup](https://eranroseman.github.io/memoria-vault/how-to-guides/setup/)

## Inputs

- [[research-directions|Research directions]] — your current priorities (read by the Librarian at session start)

## Full documentation

→ <https://eranroseman.github.io/memoria-vault/> — tutorials, how-to guides, reference, and architecture explanation.
