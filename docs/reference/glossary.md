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

**ACP** (Agent Client Protocol) — the editor-level protocol that exposes Hermes profiles to editor chat panes. Obsidian's Agent Client pane uses ACP to talk to Hermes. Distinct from the Obsidian Local REST API (which gives Hermes vault-level read/write access).

**Co-PI** — the one conversational agent (`memoria-copi`, [ADR-48](../adr/48-copi-and-agent-consolidation.md)): a reflective thinking-partner, system explainer, and delegation front. Hard read-only across the vault (empty write scope); every write it wants goes out as a board card; the sole carrier of the Hermes memory loop.

**Operation** — deterministic, no-LLM (or LLM-free-by-default) code that runs on cron/CI or behind an MCP facade, never as a board lane. Operations compute and propose; agents judge; the PI decides. The shipped operations are listed in [Operations — the deterministic layer](../explanation/operations.md).

**Hermes** — the Nous Research agent runtime Memoria runs on: Kanban, profile management, MCP server connections, skills, cron, and the gateway process.

**Memoria** — the whole system: the vault, the Co-PI + four background agents, the Operations layer, the policy gate, the board, and the tooling layer (`.memoria/`).

**PI** — the human principal investigator who owns and runs the vault. Makes every approval, triage, and promotion decision. Single-user by design. (Older pages say "the human".)

**Agent** — a running instance of the model doing work, operating under exactly one **profile**. Two kinds: the **Co-PI**, the interactive agent the PI talks to (it runs off the board), and **background agents**, which execute operations in **lanes**. An agent is a *process*; its permissions come from its profile, and its place on the board is its lane. Contrast *profile* (the configured posture) and *lane* (the board slot).

**Profile** — a Hermes role with bounded permissions, skills, and tools. Memoria defines five: Co-PI, Librarian, Writer, Peer-reviewer, Engineer. A profile is *configuration* — a posture — not a running process; the process that runs under it is an **agent** and its board slot is a **lane**. Permissions live on the profile, so "agent permissions" and "a lane's permissions" are shorthand for the permissions of the profile that agent or lane runs. See [Profile capabilities](profile-capabilities.md).

**Seven-layer architecture** — PI · Interface · Co-PI · Tasks · MCP · Operations · Vault ([ADR-46](../adr/46-seven-layer-architecture.md)): conversation at the top, deterministic code at the bottom, the board and the gate in between.

**Workspace** — the alpha.11 runtime vault root containing `catalog/`,
`knowledge/`, `capabilities/`, `journal/`, and `.memoria/`. Obsidian opens this
root. `knowledge/` is the checked knowledge bundle inside the vault, not the
Obsidian vault root.

---

## Surfaces and navigation

**Navigator rail** — the left-pane surface for everyday navigation (`_nav.md`, [ADR-116](../adr/116-obsidian-surface-architecture.md)): **Now** over **Places**. Replaces the older per-dashboard nav rows.

**Now** — the rail's top band: what is waiting on you right now — **Action queue** (your Inbox queue), **Drift** (open integrity flags), and **Fleet** (background-worker health).

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

**System dashboard** — one of the read-only, Dataview-backed notes in `system/dashboards/` (consolidated to five in [ADR-118](../adr/118-dashboard-consolidation.md)); the spaces and Maintenance carry the action surfaces.

**Home** — `home.md`, the fresh-vault launch screen — not a navigation front door (the homepage front door was retired in [ADR-115](../adr/115-inbox-queue-and-retired-homepage.md)).

---

## Board and delegation

**Card** — a task on the Hermes Kanban board. Carries `status`, `assignee`, retry count, and a handoff summary. Lives in `kanban.db`, projected into `system/board/`.

**Ceiling** — a lane's `routing.write_scope` in its lane-override: the outer bound on where its writes may land. A card's `allowed_paths` may _narrow_ but never _widen_ it (lane = ceiling, payload = floor); the tasks MCP refuses widening delegations and the policy MCP re-checks per write.

**Dispatcher** — the Hermes component that polls the board every 60 seconds and claims `ready` cards for matching-lane profiles. Makes no quality or approval decisions.

**Handoff payload** — the self-contained block that provisions the next worker; its fields are specified in the [Kanban board reference](kanban-board.md).

**Lane** — a background agent's execution path on the board; a lane _is_ an `assignee` value. Four lanes: Librarian, Writer, Peer-reviewer, Engineer. Each lane runs one fixed **profile** and so inherits that profile's permissions; the thing that actually runs in the lane is an **agent**. The Co-PI has no lane; operations run off the board.

**Card vs task** — a *task* is a unit of delegated work; a card is its runtime
board representation. Alpha.11 surfaces board state as projections, not Concept
types.

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

**Check status** — the read-state field on every alpha.11 Concept:
`unchecked`, `checked`, or `quarantined`. Values are specified in
[Frontmatter fields](frontmatter.md).

**Links vs relationships** — the two kinds of connection: authored `links:` edges on notes versus given `relationships` edges on catalog entities. The distinction and its rationale are explained in [Wikilink and link conventions](wikilink-and-link-conventions.md); the field contract is specified in [Frontmatter fields](frontmatter.md).

**Document type** — one of the Concept types defined in
`.memoria/schemas/types/`; the full roster, categories, and folder homes are in
[Document types](document-types.md).

**Pattern** — compatibility name for a checked prompt operation stored as data
in `capabilities/operations/` ([ADR-53](../adr/53-pattern-library.md)) and
executed only through the patterns MCP runner.

**State** — not a field name on its own; use the specific field. A Concept's
read state is **`check_status`**; a board card's execution state is **`status`**;
review carries **`review_status`**, ingest **`ingest_status`**, and the
operational-health dashboard tracks **skill state**. Prefer the precise field
name over a bare "state". Field contracts are specified in
[Frontmatter fields](frontmatter.md).

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([ADR-56](../adr/56-extraction-uncertainty-flag.md)): when cross-source identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Lane-override file** — per-lane YAML at `.memoria/lane-overrides/<lane>.yaml` declaring `policy.allow`/`deny`/`require` and `routing` (invocation, external-API policy, write scope). Read by the policy MCP.

**Policy MCP** — the runtime write-gate: intercepts every vault action, returns `allow` / `allow_with_log` / `deny` / `dry_run`, and appends to the audit log. Enforced in-process by the fail-closed `memoria-policy-gate` plugin. See [Policy MCP](policy-mcp.md).

**Review-gated zone** — an older policy term for folders where agent writes
degrade to proposals. Alpha.11 replaces this with worker-owned staging and
promotion: machine writes enter `.memoria/staging/`, and only checked Concepts
are promoted into `catalog/`, `knowledge/`, or `capabilities/`.

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / operations | advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter operation | structural rollup over the detectors — the rollup rule is owned by [Linter: detectors and auto-fix](linter.md) |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection |

**Trust score** — a 0–100 per-lane operational-health aggregate on the fleet-health dashboard; its inputs and bands are specified in [Dashboards](dashboards.md).

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The document types referenced throughout: [Document types](document-types.md)
- Lane and profile terms: [Profile capabilities](profile-capabilities.md)
- Board and delegation terms: [Kanban board reference](kanban-board.md)
