---
title: Glossary
parent: Vault data model
grand_parent: Reference
---

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses.

For the short version of the core terms, see [Home](../README.md).

---

## System

**ACP** (Agent Client Protocol) — an optional editor-level protocol for external
chat adapters. Alpha.15 does not ship an ACP/Hermes profile setup.

**Co-PI** — the research-partner role exposed in alpha.15 through the
standalone `memoria ask` / `memoria project ask` commands. Older designs mapped
this role to a Hermes profile; alpha.15 does not ship that profile.

**Operation** — a checked capability manifest plus runner behavior invoked by
the CLI/engine. Operations compute and propose; the PI decides. The shipped
operations are listed in [Operations](operations.md).

**Hermes** — an optional external agent runtime that may wrap the CLI/engine in
future adapter work. It is not required by alpha.15.

**Memoria** — the whole system: the OKF knowledge bundles, capability manifests,
standalone CLI/engine, policy/audit layer, workspace DB, and `.memoria/`
runtime state.

**PI** — the human principal investigator who owns and runs the vault. Makes
every triage, disposition, and promotion decision. Single-user by design.
(Older pages say "the human".)

**Agent** — a model-backed process doing work. Alpha.15 exposes agents through
the standalone CLI/engine and optional adapters; it does not ship installed
profile packages or lane assignments.

**Standalone engine architecture** — PI · CLI · Engine · Operations · Storage ·
Vault · Optional adapters ([ADR-125](../adr/125-standalone-cli-engine-architecture.md),
[ADR-130](../adr/130-read-api-surfaces-and-copi.md)): PI intent enters through
the CLI or observed file edits, the engine owns request/write/recovery state,
and adapters are presentation layers over the same contracts. The older
seven-layer architecture is historical context in [ADR-125](../adr/125-standalone-cli-engine-architecture.md).

**Workspace** — the runtime vault root containing `catalog/`, `knowledge/`,
`journal/`, and `.memoria/`. Optional editors open this root. `knowledge/` is
the checked knowledge bundle inside the vault, not the editor vault root.

---

## Surfaces and navigation

**Navigator rail** — the Markdown navigation note for everyday navigation (`_nav.md`, [ADR-130](../adr/130-read-api-surfaces-and-copi.md)): **Now** over **Places**. Replaces the older per-dashboard nav rows.

**Now** — the rail's top band: what is waiting on you right now — **Action
queue** (your Inbox queue) and **Drift** (open integrity flags).

**Places** — the rail's lower band: the three durable **spaces** — Library, Knowledge, Project.

**Space** — a navigation surface that is also a dashboard-as-note
(`projection: space`): Library, Knowledge, Project, each exposing workspace
state through Markdown views and CLI/read-API commands. "Gate" is reserved for
the review gate, never a space.

**Queue** — the **Inbox** (`projection: queue`): the daily attention surface
reached from **Now -> Action queue**. It shows in-process Activity, then
open attention projections such as `candidate`, `gap`, and `work-prompt`.
Clearing it to empty is the goal.

**Maintenance** — the weekly structural-debt surface
(`projection: maintenance`): Drift watch, loose ends, queue state, and
"new this week".

**Rail health band** — the count the rail's **Now** shows for open `flag` /
`alert` attention projections; non-zero means structural debt is waiting in
Maintenance.

**System dashboard** — one of the read-only, Dataview-backed notes in
`system/dashboards/`; the spaces and Maintenance carry the action surfaces.

**Home** — `home.md`, the fresh-vault launch screen — not a navigation front door (the homepage front door was retired in [ADR-130](../adr/130-read-api-surfaces-and-copi.md)).

---

## Board and delegation

**Ceiling** — the maximum write scope an optional adapter policy grants. Request
payloads may narrow that scope, but never widen it.

**Dispatcher** — alpha.15 dispatcher behavior lives in the local worker queue:
CLI commands, scans, and scheduled tasks create request rows, and the worker runs
pending jobs.

**Handoff payload** — the self-contained block that provisions the next worker; its fields are specified in the [Control plane reference](control-plane.md).

**Task/request** — a unit of work represented by a SQLite request row. Attention
projections are PI-facing views over work that needs review.

**Worklist** — the batch surface for high-cardinality decisions: instead of one
attention item per row, like decisions queue into one `system/worklists/` batch
where each `projection: worklist-item` row has a `decision` field the PI can
sweep in Bases.

---

## Notes and lifecycle

**Attention projection** — a generated Inbox row (`candidate`, `gap`, `flag`,
`alert`, `work-prompt`) carrying PI-facing work. It is not a durable Concept;
the owning state is journal/check/queue data.

**Hub** — a checked `hub` Concept in `knowledge/hubs/` aggregating a topic's
members and links. Machine-curated hub changes are suggestions until the PI
adopts them.

**Check status** — the runtime read-state verdict for Concepts:
`unchecked`, `checked`, or `quarantined`. It lives in SQLite/read API surfaces,
not Concept frontmatter.

**Links vs relationships** — the two kinds of connection: authored `links:` edges on notes versus given `relationships` edges on catalog entities. The distinction and its rationale are explained in [Wikilink and link conventions](wikilink-and-link-conventions.md); the field contract is specified in [Frontmatter fields](frontmatter.md).

**Document type** — one of the Concept types defined in
`.memoria/schemas/types/`; the full roster, categories, and folder homes are in
[Document types](document-types.md).

**Pattern** — a package-owned prompt operation
([ADR-125](../adr/125-standalone-cli-engine-architecture.md)) executed through
`memoria operation run`.

**State** — not a field name on its own; use the specific field. A Concept's
read verdict is **`check_status`** in runtime state; request state lives in
SQLite. Prefer the precise field name over a bare "state".

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([ADR-129](../adr/129-layered-machine-judgment.md)): when cross-source identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Policy gate** — optional adapter decision shim: returns `allow` /
`allow_with_log` / `deny` / `dry_run`, appends to the audit log, and fails
closed when adapter policy is missing. See [Policy gate](policy-mcp.md).

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / operations | advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter operation | structural rollup over the detectors — the rollup rule is owned by [Linter: detectors and auto-fix](linter.md) |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection |

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The document types referenced throughout: [Document types](document-types.md)
- Request-control terms: [Control plane reference](control-plane.md)
