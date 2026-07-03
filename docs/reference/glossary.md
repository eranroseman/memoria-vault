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
chat adapters. Alpha.14 does not ship an ACP/Hermes profile setup.

**Co-PI** — the research-partner role exposed in alpha.14 through the
standalone `memoria ask` / `memoria project ask` commands. Older designs mapped
this role to a Hermes profile; alpha.14 does not ship that profile.

**Operation** — a checked capability manifest plus runner behavior invoked by
the CLI/engine. Operations compute and propose; the PI decides. The shipped
operations are listed in [Operations](operations.md).

**Hermes** — an optional external agent runtime that may wrap the CLI/engine in
future adapter work. It is not required by alpha.14.

**Memoria** — the whole system: the OKF knowledge bundles, capability manifests,
standalone CLI/engine, policy/audit layer, workspace DB, and `.memoria/`
runtime state.

**PI** — the human principal investigator who owns and runs the vault. Makes every approval, triage, and promotion decision. Single-user by design. (Older pages say "the human".)

**Agent** — a model-backed process doing work. Alpha.14 exposes agents through
the standalone CLI/engine and optional adapters; it does not ship installed
profile packages or lane assignments.

**Profile** — historical Hermes role configuration from earlier designs.
Alpha.14 does not ship installed profiles; the current boundary is in
[Installed profiles](profile-capabilities.md).

**Seven-layer architecture** — PI · Interface · Co-PI · Tasks · MCP · Operations · Vault ([ADR-46](../adr/46-seven-layer-architecture.md)): conversation at the top, deterministic code at the bottom, the board and the gate in between.

**Workspace** — the runtime vault root containing `catalog/`, `knowledge/`,
`journal/`, and `.memoria/`. Optional editors open this root. `knowledge/` is
the checked knowledge bundle inside the vault, not the editor vault root.

---

## Surfaces and navigation

**Navigator rail** — the left-pane surface for everyday navigation (`_nav.md`, [ADR-116](../adr/116-obsidian-surface-architecture.md)): **Now** over **Places**. Replaces the older per-dashboard nav rows.

**Now** — the rail's top band: what is waiting on you right now — **Action
queue** (your Inbox queue) and **Drift** (open integrity flags).

**Places** — the rail's lower band: the three durable **spaces** — Library, Knowledge, Project.

**Space** — a navigation surface that is also a dashboard-as-note
(`projection: space`): Library, Knowledge, Project, each embedding Bases views
over the workspace. "Gate" is reserved for the approval gate, never a space.

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

**Home** — `home.md`, the fresh-vault launch screen — not a navigation front door (the homepage front door was retired in [ADR-115](../adr/115-inbox-queue-and-retired-homepage.md)).

---

## Board and delegation

**Card** — historical task-board representation from earlier designs. Alpha.14
uses SQLite request rows and attention projections for product state.

**Ceiling** — the maximum write scope an optional adapter policy grants. Request
payloads may narrow that scope, but never widen it.

**Dispatcher** — alpha.14 dispatcher behavior lives in the local worker queue:
CLI commands, scans, and scheduled tasks create request rows, and the worker runs
pending jobs.

**Handoff payload** — the self-contained block that provisions the next worker; its fields are specified in the [Kanban board reference](kanban-board.md).

**Lane** — historical background-agent execution path from earlier profile
designs. Alpha.14 does not ship installed lanes; operations run through the
standalone CLI/runtime queue.

**Task/request** — a unit of work represented by a SQLite request row. Attention
projections are PI-facing views over work that needs review.

**Worklist** — the batch surface for high-cardinality decisions: instead of one
attention item per row, like decisions queue into one `system/worklists/` batch
where each `projection: worklist-item` row has a `decision` field the PI can
sweep in Bases.

---

## Notes and lifecycle

**Golden copy** — the canonical, hash-manifested copy of every system file at `.memoria/golden/`, staged by the installer ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The Linter checks drift against it and can restore from it (propose-only by default).

**Attention projection** — a generated Inbox row (`candidate`, `gap`, `flag`,
`alert`, `work-prompt`) carrying PI-facing work. It is not a durable Concept;
the owning state is journal/check/queue data.

**Hub** — a checked `hub` Concept in `knowledge/hubs/` aggregating a topic's
members and links. Machine-curated hub changes are suggestions until the PI
adopts them.

**Check status** — the read-state field on every Concept:
`unchecked`, `checked`, or `quarantined`. Values are specified in
[Frontmatter fields](frontmatter.md).

**Links vs relationships** — the two kinds of connection: authored `links:` edges on notes versus given `relationships` edges on catalog entities. The distinction and its rationale are explained in [Wikilink and link conventions](wikilink-and-link-conventions.md); the field contract is specified in [Frontmatter fields](frontmatter.md).

**Document type** — one of the Concept types defined in
`.memoria/schemas/types/`; the full roster, categories, and folder homes are in
[Document types](document-types.md).

**Pattern** — compatibility name for a checked packaged prompt operation
([ADR-53](../adr/53-pattern-library.md)) executed through
`memoria operation run`; `memoria_vault.runtime.patterns`
remains a compatibility prompt composer for tests and optional adapters.

**State** — not a field name on its own; use the specific field. A Concept's
read state is **`check_status`**; request state lives in SQLite; ingest carries
**`ingest_status`**. Prefer the precise field name over a bare "state". Field
contracts are specified in
[Frontmatter fields](frontmatter.md).

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([ADR-56](../adr/56-extraction-uncertainty-flag.md)): when cross-source identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Lane-override file** — optional adapter YAML read by the legacy Policy gate
shim when an external adapter supplies it. Alpha.14 does not ship lane overrides.

**Policy gate** — optional adapter decision shim: returns `allow` /
`allow_with_log` / `deny` / `dry_run`, appends to the audit log, and fails
closed when adapter policy is missing. See [Policy gate](policy-mcp.md).

**Review-gated zone** — an older policy term for folders where agent writes
degrade to proposals. Alpha.11 replaces this with worker-owned staging and
promotion: machine writes enter `.memoria/staging/`, and only checked Concepts
are promoted into `catalog/` or `knowledge/`.

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
- Lane and profile terms: [Installed profiles](profile-capabilities.md)
- Request-control terms: [Kanban board reference](kanban-board.md)
