# Memoria — vault index

The pinned landing page. Open it in the morning; close it when the system looks healthy.

## Daily / weekly dashboards

- [[01-dashboards/index|Daily Health]] — daily 30-second glance (board queues, drift signals, lane health, cron status)
- [[01-dashboards/discuss-queue|Reading queue]] — papers classified but not yet processed
- [[01-dashboards/weekly-review|Weekly ritual]] — Friday vault audit (orphans, stale enrichment, promotion queue)
- [[01-dashboards/board-state|Board state]] — full Kanban
- [[01-dashboards/audit-log|Audit log]] — forensic view of policy MCP decisions
- [[01-dashboards/drift-watch|Drift watch]] — Linter findings + verdict band
- [[01-dashboards/open-questions|Open questions]] — research agenda view

## Reference

- [[04-reference/getting-started|Getting started]] — first-time setup
- [[04-reference/safe-mode|Safe mode]] — what to do when Hermes or the ACP connection is down
- [[04-reference/agent-roles|Agent roles]] — what each Hermes profile does
- [[04-reference/profile-policies|Profile policies]] — who can write where
- [[04-reference/schema-reference|Schema reference]] — frontmatter field catalog
- [[04-reference/system-map|System map]] — plain-language architecture summary

## Inputs

- [[research-directions|Research directions]] — your current priorities (read by Librarian at session start)
- [[system-status|System status]] — runtime health snapshot

## Common operations (via Cmd-P → "Memoria:")

- `Memoria: capture fleeting` — instant capture to `10-inbox/01-fleeting/`
- `Memoria: ask about this note` — open Socratic ACP pane on the active note
- `Memoria: new project` — scaffold a new project folder
- `Memoria: lint this note` — manual dry-run lint on the active note
- `Memoria: find related notes` — Mapper transient query
- `Memoria: similarity-check this claim` — Verifier transient query

## Mode-switching hotkeys (in ACP chat)

- `Ctrl+Shift+1` → Ask (Socratic)
- `Ctrl+Shift+2` → Map (Mapper)
- `Ctrl+Shift+3` → Draft (Writer)
- `Ctrl+Shift+4` → Check (Verifier)
