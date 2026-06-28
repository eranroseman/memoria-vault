# How we work in this vault

The shared instruction layer every Memoria agent reads (ADR-48). Your posture and
skills are yours (`SOUL.md`, `skills/`); the house rules below are everyone's. The PI
is the principal investigator — the only actor who promotes anything to canonical.

## The bounded rule

You **propose**; the **PI disposes**. Every write you make lands in staging or your
lane's scratch — never in a review-gated zone (`notes/claims/`, `notes/hubs/`), never a
promotion, never a `retracted` decision. The policy MCP enforces this at the
filesystem; do not try to route around it.

## Dispatched work

If the prompt is `work kanban task t_...`, you are a dispatched worker. Call
`kanban_show()` immediately before asking questions or using any other tool. Treat its
`worker_context` as the task spec, then finish with `kanban_complete(...)` or
`kanban_block(...)`.

## Where things live (ADR-47)

`catalog/` entity records (Bases-backed; built by the ingest operation) · `notes/` prose —
fleeting / source / claims 🔒 / hubs 🔒 · `projects/` project work · `inbox/`
your messages to the PI · `system/` templates, dashboards, patterns, logs. One folder
never mixes two categories. `archived` is a *state*, not a folder — never move a note
to archive it.

## State and signals (ADR-50)

One lifecycle chain: `proposed → provisional → current → retracted → archived` (each
type uses its schema's subset — `.memoria/schemas/types/`). `maturity` and
`agent_recommendation` are soft signals, never gates: a `seedling` claim is fully
current, and your `clean` verdict never substitutes for the PI's approval.

## Talking to the PI (ADR-51)

Everything you need the PI to see is an **Inbox card** — candidate, gap, flag,
alert, or work-prompt — in `inbox/`, conforming to its type schema. Proposals carry the **honesty
body**: the argument for, your strongest argument *against*, what tipped it, and your
calibrated certainty. No verdict line — the recommendation is implied by the card
existing. Verification findings lead with the finding. Never raise N cards for one
batch decision — write the worklist, raise one work-prompt.

## Connections (ADR-52)

`relationships` (entities) are **given** facts — the ingest operation builds them; you
never author them. `links:` (notes) are **authored** — you may *propose* a typed link
(`supports` / `contradicts`); the PI confirms it at the link gate.

When querying or writing from claim notes, exclude claims with non-empty
`superseded_by` by default. Include superseded claims only when the task explicitly
asks for lineage, audit, or supersession history; do not use them as current support.

## Provenance

Every claim traces to a citekey in `sources`. Every gated write goes through the
policy MCP and lands in the audit log. If you cannot cite it, you cannot write it.
