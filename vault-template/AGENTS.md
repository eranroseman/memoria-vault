---
type: system
title: Memoria workspace instructions
---

# How to work in this Memoria workspace

This is the shared instruction layer for any human, local tool, or delegated
agent working in the workspace. The PI is the principal investigator: they
direct and curate, while the Memoria engine owns request state, checks, and
checked promotion.

## The bounded rule

You **propose**; the **PI disposes**. Machine writes and promotions go through the
request envelope and worker check path, PI edits are direct and then
observed/backfilled, and foreign writes are quarantined by the integrity scan.
Do not write Concepts, journal rows, projections, or `check_status` by hand.

## Queued work

If a task should mutate the workspace, queue it through the `memoria` CLI or the
engine request API. Do not emulate the worker by editing files directly. The
worker reads request rows from SQLite, writes staged outputs, and records
check/verdict state before anything becomes readable as checked knowledge.

## Where things live

`notes/` claims/questions · `hubs/` topic hubs · `projects/`
project evidence and gaps · `digests/` generated work digests · `fulltexts/`
generated full-text reproductions · `inbox/` transient attention projections · `system/`
visible manifests, incidents, metrics, templates, and eval fixtures. Product
operation manifests live in the installed `memoria_vault` package, not in a
workspace `capabilities/` tree.
`archived` is a *state*, not a folder.

## State and signals (ADR-126/127)

Concept frontmatter carries meaning fields such as `type`, `id`, `links`, and
`tags`; runtime verdicts and request state live in SQLite/read API surfaces. A
tool's `clean` verdict never substitutes for the worker check or PI direction.

## Talking to the PI (ADR-128/130)

Everything you need the PI to see is an **attention item** projected from journal,
queue, check, and Concept state. Proposals carry the **honesty body**: the argument
for, your strongest argument *against*, what tipped it, and your calibrated
certainty. Verification findings lead with the finding. Never raise N items for one
batch decision.

## Connections (ADR-126)

`relationships` (entities) are **given** facts — the ingest operation builds them; you
never author them. `links:` (notes) are **authored** — you may *propose* a typed link
(`supports` / `contradicts`); the PI confirms it at the link gate.

When querying or writing from claim-bearing notes, exclude claims with non-empty
`superseded_by` by default. Include superseded claims only when the task explicitly
asks for lineage, audit, or supersession history; do not use them as current support.

## Provenance

Every claim-bearing note traces to checked catalog Works. Every machine write
goes through the worker/trusted writer and lands in the journal. If you cannot
cite it, you cannot write it.
