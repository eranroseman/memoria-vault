---
topic: explorations
title: Memoria system architecture — the seven-layer stack
status: exploration
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 25
nav_exclude: true
---

# Memoria system architecture — the seven-layer stack

> **Status: exploration.** The Memoria architecture — the layered stack, the trust
> boundaries, and the flow principle. This is the **one model** — it serves as both the
> cognitive model and the build view (an earlier draft kept two and mapped them; one good
> model beats two perfect ones). The redesign's
> [§2](memoria-redesign.md) is the summary; this is the full treatment. Firm decisions
> graduate to ADRs (rationale in
> [Memoria redesign — decisions & rationale](memoria-redesign-decisions.md), D36/D40/D41/D42).

## 1. Guiding principle

**Decisions flow top-down; information flows bottom-up.** A decision originates with the
PI and descends the stack (PI → co-PI → tasks → engines → vault); knowledge ascends it
(vault → engines → tasks → co-PI → PI). Along the **agent write-path** (co-PI → Tasks →
MCP → Engines/Vault) each layer depends only on the one below — the classic layered
contract that lets each be reasoned about, swapped, or sandboxed independently. But the
**PI and trusted automation are direct edges, not rungs**: the PI edits the Vault directly
in Obsidian, and cron/CI/the PI invoke engines directly (§3). The strict layering binds
*agents*, not every actor.

## 2. The seven layers

| # | Layer | Actor-kind | What it is |
|---|---|---|---|
| **L1** | **PI** | human | the human in charge — the *Principal Investigator*; the only actor who promotes to canonical. ("human-in-the-loop" is the design concept; "PI" is the role.) |
| **L2** | **Interface** | — | the Obsidian UI — Home, dashboards, Inbox, the Library/Project Workspaces, command palette, panes/sidebars. The PI's whole surface. |
| **L3** | **co-PI** | agent | the permanent agent in the ACP pane the PI converses with. Read-only; runs the PI's read-only skills directly and **delegates every write**. Inherits the old Socratic role + a `memoria` *explain-the-system* skill. Uses the full Hermes loop — **memory · /goals · skills** — so it grows into a true co-PI. |
| **L4** | **Tasks** | agents | the ephemeral profiles, the kanban board, and task cards. Given work by the PI and the co-PI; each runs under the structured *propose → dispose* process. |
| **L5** | **MCP server(s)** | — | the **sandbox boundary**. Agents are isolated and reach the Vault + external APIs *only* through MCP — a lightweight app that fetches data / executes tools, allow-listing tools and scoping writes (§3). |
| **L6** | **Engines** | engines | the deterministic apps — **ingest · search · clustering · verification sweeps · Linter**. Invoked by the PI, agents, or cron for bookkeeping and maintenance. (Name *engines*, not "apps" — that now collides with "MCP apps", §4.) |
| **L7** | **Vault** | — | the files & folders — the knowledge itself. The Obsidian vault. |

L2 is the **Interface** (the whole Obsidian UI); *Library* and *Project* are two saved
Obsidian **Workspaces** (saved pane layouts) within it. Three **actor-kinds** act on the
structural layers (L2, L7): the **PI** (L1), **agents** (L3 co-PI + L4 Tasks), and
**engines** (L6). **L5 MCP is a *trust boundary*, not a stratum everyone crosses** — only
the *agent* path passes through it; the PI and cron/CI reach engines/Vault directly (§3).
Read the table as a dependency *order*, not a claim that every actor traverses all seven.

## 3. The MCP boundary — a policy gate, not an execution sandbox

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
(ingest, search, clustering) carries an **MCP-tool facade** *and* a direct entry, while a
*maintenance* engine run only by cron/CI (the Linter, the verification sweeps) needs **no
MCP facade** — it runs directly and posts findings to the Inbox (D41). *(Confirmed against
the MCP architecture docs.)*

## 4. MCP apps — a watch item, not a dependency

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

## 5. Resolved / deferred

- **One model — resolved (D42):** this seven-layer stack *is* the model (cognitive +
  build); the earlier separate "two layers + three actors" framing and its mapping table
  are dropped.
- **Sandbox model — resolved (D40):** policy-sandbox-via-MCP is the baseline for first-party
  agents (sufficient under the solo/local premise); execution isolation applies only to
  *untrusted third-party code* and is deferred until such code is introduced.
- **Engine invocation — resolved (D41):** agents reach engines only through MCP; cron, CI,
  and the PI invoke them directly. Processing engines (ingest, search, clustering) get an
  MCP facade + a direct entry; cron/CI-only maintenance engines (the Linter, the sweeps)
  need no facade.
- **L6 name — locked (D36):** **engines**, over "apps" (MCP-apps collision), "tools"
  (MCP-tools collision), and services / utilities / scripts / appliances.
- **Still deferred:** add a process boundary *if/when* untrusted third-party MCP servers or
  coding agents are actually run.
