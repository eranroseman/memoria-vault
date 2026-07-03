# How we work in this vault

The shared instruction layer every Memoria agent reads (ADR-48). Your posture and
skills are yours (`SOUL.md`, `skills/`); the house rules below are everyone's. The PI
is the principal investigator: they direct and curate, while the worker owns checked
promotion.

## The bounded rule

You **propose**; the **PI disposes**. Machine writes and promotions go through the
worker staging/promote path, PI edits are direct and then observed/backfilled, and
foreign writes are quarantined by the integrity scan. Do not write Concepts,
journal rows, projections, or `check_status` by hand.

## Dispatched work

If the prompt is `work kanban task t_...`, you are a dispatched worker. Call
`kanban_show()` immediately before asking questions or using any other tool. Treat its
`worker_context` as the task spec, then finish with `kanban_complete(...)` or
`kanban_block(...)`.

## Where things live (ADR-119)

`catalog/` source and entity Concepts · `knowledge/` digests, notes, hubs, and
projects · `capabilities/` operations, skills, MCPs, and workflows · `system/`
templates, dashboards, eval, and logs. `archived` is a *state*, not a folder.

## State and signals (ADR-119)

Concept frontmatter carries meaning fields such as `type`, `id`, `links`, and
`tags`; runtime verdicts and request state live in SQLite/read API surfaces.
`agent_recommendation` is a soft signal, never a gate; your `clean` verdict never
substitutes for the worker check or PI direction.

## Talking to the PI (ADR-54)

Everything you need the PI to see is an **attention item** projected from journal,
queue, check, and Concept state. Proposals carry the **honesty body**: the argument
for, your strongest argument *against*, what tipped it, and your calibrated
certainty. Verification findings lead with the finding. Never raise N items for one
batch decision.

## Connections (ADR-52)

`relationships` (entities) are **given** facts — the ingest operation builds them; you
never author them. `links:` (notes) are **authored** — you may *propose* a typed link
(`supports` / `contradicts`); the PI confirms it at the link gate.

When querying or writing from claim-bearing notes, exclude claims with non-empty
`superseded_by` by default. Include superseded claims only when the task explicitly
asks for lineage, audit, or supersession history; do not use them as current support.

## Provenance

Every claim-bearing note traces to checked source Concepts. Every machine write goes
through the worker/trusted writer and lands in the journal. If you cannot cite it, you
cannot write it.
