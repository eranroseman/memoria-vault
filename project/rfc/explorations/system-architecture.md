---
topic: proposals
title: Memoria system architecture — the seven-layer stack
status: exploration
created: 2026-06-09
---

# Memoria system architecture — the seven-layer stack

> **Status: exploration.** The *build / runtime* view of Memoria — the layered stack,
> the trust boundaries, and the flow principle. Its companion is
> [memoria-redesign.md](memoria-redesign.md) §2, which is the *cognitive* model (two
> structural layers + three actors). **They describe the same system from two angles and
> map one-to-one** (§3 below); keeping them distinct is what avoids the "which layer
> model is canonical?" confusion. Firm decisions graduate to ADRs (rationale in
> [memoria-redesign-decisions.md](memoria-redesign-decisions.md), D36).

## 1. Guiding principle

**Decisions flow top-down; information flows bottom-up.** A decision originates with the
PI and descends the stack (PI → co-PI → tasks → engines → vault); knowledge ascends it
(vault → engines → tasks → co-PI → PI). Every layer depends only on the one below and
serves only the one above — the classic layered-architecture contract, which is what lets
each layer be reasoned about, swapped, or sandboxed independently.

## 2. The seven layers

| # | Layer | What it is |
|---|---|---|
| **L1** | **PI** | the human in charge — the *Principal Investigator*; the only actor who promotes to canonical. ("human-in-the-loop" is the design concept; "PI" is the role.) |
| **L2** | **Interface** | the Obsidian UI — homepage, dashboards, Inbox, the working surface (Library/Project perspectives), command palette. The PI's whole surface. |
| **L3** | **co-PI** | the permanent agent in the ACP pane the PI converses with. Read-only; runs the PI's read-only skills directly and **delegates every write**. Inherits the old Socratic role + a `memoria` *explain-the-system* skill (so it can teach the PI how to do things). Uses the full Hermes loop — **memory · /goals · skills** — so it grows into a true co-PI. |
| **L4** | **Tasks** | the ephemeral profiles, the kanban board, and task cards. Given work by the PI and the co-PI; each runs under the structured *propose → dispose* process. |
| **L5** | **MCP server(s)** | the **sandbox boundary**. Agents are isolated and reach the vault + enrichment APIs *only* through MCP — a lightweight app that fetches data / executes tools, allow-listing tools and scoping writes (§4). |
| **L6** | **Engines** | the deterministic apps — ingest/cataloging, search, the verification sweeps, the Linter. Invoked by the PI, agents, or cron for **bookkeeping and maintenance**. (Kept the name *engines* — not "apps", which now collides with "MCP apps", §5.) |
| **L7** | **Vault** | the files & folders — the knowledge itself. The Obsidian vault. |

## 3. Mapping to the cognitive model

The stack is the same system as the redesign's *two layers + three actors*, just more
granular — it makes two things explicit that the cognitive model folds away: the **MCP
boundary** and the **co-PI / tasks split**.

| 7-layer stack (build view) | Cognitive model ([redesign §2](memoria-redesign.md)) |
|---|---|
| L1 PI | actor: the PI (the human) |
| L2 Interface | layer: **Workspaces** |
| L3 co-PI · L4 Tasks | actor: **agents** |
| L5 MCP | the agent→{engines, vault, APIs} trust boundary *(new)* |
| L6 Engines | actor: **engines** |
| L7 Vault | layer: **Vault** |

A naming note: L2 is called **Interface** here (not "Workspaces") to deconflict — the
cognitive layer is "Workspaces", and "perspective" is reserved for the Library/Project
layouts *inside* the interface.

## 4. The MCP boundary — a policy gate, not an execution sandbox

MCP is the right place to enforce **policy**: the server validates every request before it
touches the vault or an external API, allow-lists tool types, scopes writes (e.g.
`read_file(path)` rejects paths outside the vault), rate-limits, and logs. This is the
`allowed_paths`/lane-ceiling enforcement the redesign already assumes.

**MCP is *not* an execution sandbox** — a stdio server shares the agent's OS context (no
process/memory/CPU confinement) — so the honest phrasing is **policy-sandboxed via MCP**,
not "completely sandboxed."

**Resolution (the solo, local premise): policy-sandbox-via-MCP is the baseline, and it is
sufficient.** For a single trusted user running their own agents on their own vault, the
threat isn't tenant-escape — it's *wrong writes*, already covered by the MCP policy gate +
propose-not-dispose + the gated zones + the SHA-256 audit log + git history. First-party
Memoria agents get **no process isolation**; it's multi-tenant hygiene that buys nothing
here. **Execution isolation applies only to *untrusted third-party code*** — a community
MCP server, or the Engineer's external coding agent — which warrants a process boundary
(container / separate OS user) or careful vetting, and is **deferred until such code is
actually introduced** (D40).

**Invocation paths — which calls cross MCP:** *the path follows the caller.* **Agents reach
engines only through MCP** (no exceptions — that *is* the sandbox); **trusted callers —
cron, CI, and the PI — invoke engines directly.** So an agent-reachable *processing* engine
(ingest, search) carries an **MCP-tool facade** *and* a direct entry, while a *maintenance*
engine run only by cron/CI (the Linter, the verification sweeps) needs **no MCP facade** —
it runs directly and posts findings to the Inbox (D41). *(Confirmed against the MCP
architecture docs.)*

## 5. MCP apps — a watch item, not a dependency

"MCP **apps**" (2026) are interactive HTML UIs that render *inside the MCP host* (Claude
clients, VS Code) in a sandboxed iframe, served by an MCP server. Crucially they render
**on the agent-client side — the ACP / co-PI pane — not inside Obsidian**. So:

- **Not** a replacement for Obsidian Bases / Canvas, which are the *vault-native,
  plain-text, git-tracked* views (L7) and must stay so.
- **A future option for the co-PI pane's interactive surfaces** (a recommendation-card
  reviewer, a relevance-report screening UI, a graph viewer) — *if/when* the ACP client
  supports them.

Verdict: keep Obsidian-native for vault views now; flag MCP apps for the L3 interaction
layer later. Not a v0.x dependency.

## 6. Resolved / deferred

- **Sandbox model — resolved (D40):** policy-sandbox-via-MCP is the baseline for first-party
  agents (sufficient under the solo/local premise); execution isolation applies only to
  *untrusted third-party code* and is deferred until such code is introduced.
- **Engine invocation — resolved (D41):** agents reach engines only through MCP; cron, CI,
  and the PI invoke them directly. Processing engines (ingest, search) get an MCP facade +
  a direct entry; cron/CI-only maintenance engines (the Linter, the sweeps) need no facade.
- **L6 name — locked (D36):** **engines**, over "apps" (MCP-apps collision), "tools"
  (MCP-tools collision), and services / utilities / scripts / appliances.
- **Still deferred:** add a process boundary *if/when* untrusted third-party MCP servers or
  coding agents are actually run.
