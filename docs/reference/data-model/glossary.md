---
title: Glossary
parent: Reference data model
nav_order: 5
grand_parent: Reference
---

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses.

For the short version of the core terms, see [Home](../../README.md).

---

## System

**Co-PI** — the research-partner role exposed through the standalone
`memoria ask` / `memoria project ask` commands.

**Operation** — a checked capability manifest plus runner behavior invoked by
the CLI/engine. Operations compute and propose; the PI decides. The shipped
operations are listed in [Operations](../commands-and-transports/operations.md).

**Memoria** — the whole system: the OKF knowledge bundles, capability manifests,
standalone CLI/engine, policy/audit layer, workspace DB, and `.memoria/`
runtime state.

**PI** — the human principal investigator who owns and runs the vault. Makes
every triage, disposition, and promotion decision. Single-user by design.

**Agent** — a model-backed process doing work. Memoria exposes agents through
the standalone CLI/engine and optional adapters; it does not ship installed
profile packages or lane assignments.

**Standalone engine architecture** — PI · CLI · Engine · Operations · Storage ·
Vault · Optional adapters. PI intent enters through the CLI or observed file
edits, the engine owns request/write/recovery state, and adapters are
presentation layers over the same contracts.

**Workspace** — the runtime vault root containing `notes/`, `hubs/`,
`projects/`, `digests/`, `fulltexts/`, `inbox/`, `system/`, and `.memoria/`.
Optional editors open this root; the top-level bundle roots are the checked
corpus homes.

---

## Surfaces and navigation

**Navigator rail** — the read-API navigation model for everyday navigation
([thin read-API surfaces over one engine, PI direct access preserved](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)):
**Now** over **Places**. It replaces the older per-dashboard nav rows without
requiring a shipped navigation note.

**Now** — the rail's top band: what is waiting on you right now — **Action
queue** (your Inbox queue) and **Drift** (open integrity flags).

**Places** — the rail's lower band over durable corpus homes: Library
(`digests/`, `fulltexts/`, `bibliography.bib`), Knowledge (`notes/`, `hubs/`), and
Project (`projects/`).

**Queue** — the **Inbox** (`projection: attention`): the daily attention surface
reached from **Now -> Action queue**. It shows in-process Activity, then
open attention projections such as `candidate`, `gap`, and `work-prompt`.
Clearing it to empty is the goal.

**Maintenance** — the weekly structural-debt surface: Drift watch, loose ends,
queue state, and "new this week". It is a read-API/CLI/editor view over request,
attention, linter, and log state, not a persisted projection type.

**Rail health band** — the count the rail's **Now** shows for open `flag` /
`alert` attention projections; non-zero means structural debt is waiting in
Maintenance.

**System dashboard** — a read-only view over metrics, request state, attention
state, or linter findings. The standalone baseline does not ship `system/dashboards/*.md`;
`inbox/` and CLI request/attention views carry the action surfaces.

---

## Board and delegation

**Ceiling** — the maximum write scope an optional adapter policy grants. Request
payloads may narrow that scope, but never widen it.

**Dispatcher** — dispatcher behavior lives in the local worker queue:
CLI commands, scans, and scheduled tasks create request rows, and the worker runs
pending jobs.

**Handoff payload** — the self-contained block that provisions the next worker; its fields are specified in the [Control plane reference](../control-and-policy/control-plane.md).

**Task/request** — a unit of work represented by a SQLite request row. Attention
projections are PI-facing views over work that needs review.

**Worklist** — the batch surface for high-cardinality decisions: instead of one
attention item per row, like decisions queue into one `system/worklists/` batch
where each `projection: worklist-item` row has a `decision` field the PI can
sweep in any editor or adapter view.

---

## Notes and lifecycle

**Attention projection** — a generated Inbox row (`candidate`, `gap`, `flag`,
`alert`, `work-prompt`) carrying PI-facing work. It is not a durable Concept;
the owning state is `.memoria/journal/`, check, and queue data.

**Hub** — a checked `hub` Concept in `hubs/` aggregating a topic's
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
([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) executed through
`memoria operation run`.

**State** — not a field name on its own; use the specific field. A Concept's
read verdict is **`check_status`** in runtime state; request state lives in
SQLite. Prefer the precise field name over a bare "state".

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([machine judgments are layered proposals, never authorities](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)): when cross-Work identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Policy gate** — optional adapter decision shim: returns `allow` /
`allow_with_log` / `deny` / `dry_run`, appends to the audit log, and fails
closed when adapter policy is missing. See [Policy gate](../control-and-policy/policy-mcp.md).

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / operations | advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter operation | structural rollup over the detectors — the rollup rule is owned by [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md) |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection |

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The document types referenced throughout: [Document types](document-types.md)
- Request-control terms: [Control plane reference](../control-and-policy/control-plane.md)
