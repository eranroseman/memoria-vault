---
topic: decisions
id: 46
title: Seven-layer architecture — PI · Interface · Co-PI · Tasks · MCP · Engines · Vault
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [22]
supersedes: [1]
superseded_by: []
---

# ADR-46: Seven-layer architecture — PI · Interface · Co-PI · Tasks · MCP · Engines · Vault

> **Vocabulary amended (2026-06-14, [ADR-69: Operations — name the deterministic
> layer and its four categories](69-operations-layer-naming.md)).** The layer this ADR
> calls **Engines** is now named **Operations** (the synonym "app" is retired too).
> ADR-69 governs the vocabulary; this ADR keeps the architecture.

> **Verified on-box 2026-06-21 (mechanism note).** "agents reach engines and the Vault
> only through [MCP]" (Decision, below) is bound by the **gate's deny rules** —
> `policy_hook.DENY_DIRECT_TOOLS` hard-denies `file`/`terminal`/`code_execution` and the
> decision core default-denies unknown tools at dispatch (the [ADR-28](28-write-gate-as-plugin.md)
> mechanism; on v0.14.0 `disabled_toolsets` alone is schema-hiding only). The strict
> layer-dependency contract *describes* the agent write-path; the gate is what stops a
> direct write. Per AGENTS.md "Enforcement is a mechanism, not a label."

## Context

ADR-01's three layers (board, workers, vault) described the v0.1.0-alpha.1 infrastructure but
conflated two distinctions the design update pulled apart: *where* things live
(structure) and *who* acts (actor-kind). The design work
converged on a single model that serves as both the cognitive and the build view, with
the MCP trust boundary made explicit. An adversarial review then scoped its layering claim
honestly.

## Decision

Memoria is **seven layers** — **PI** (the human; the only actor who promotes to
canonical) · **Interface** (the Obsidian UI: Home, dashboards, Inbox, the
Library/Project Workspaces, command palette) · **Co-PI** (the permanent conversational
agent in the ACP pane) · **Tasks** (ephemeral profiles + the kanban board + cards) ·
**MCP** (the policy/sandbox boundary) · **Engines** (the deterministic apps: ingest,
search, clustering, verification sweeps, Linter) · **Vault** (the files and folders).

Three **actor-kinds** act across the structural layers: the PI (human judgment),
**agents** (posture + LLM — the Co-PI and the Task lanes), and **engines**
(deterministic, no posture). One flow rule: **decisions flow down, information flows
up.** The strict each-layer-depends-only-on-the-one-below contract binds the **agent
write-path** (Co-PI → Tasks → MCP → Engines/Vault); the PI and trusted automation
(cron, CI) are *direct edges* — the PI edits the Vault in Obsidian, and cron/CI/the PI
invoke engines directly. **MCP is a policy gate, not an execution sandbox**: agents
reach engines and the Vault only through it; first-party agents get no process
isolation (sufficient under the solo/local premise).

## Consequences

- The "is it an agent or an engine?" question is decided by posture + LLM judgment,
  not by invocation style; deterministic work never occupies a board lane.
- The MCP boundary is where allow-listing, write-scoping, and audit live; adding an
  engine means deciding whether it needs an MCP facade (agent-reachable) or not
  (cron/CI-only).
- "Completely sandboxed" is over-claiming: the honest phrase is *policy-sandboxed via
  MCP*; execution isolation is deferred until untrusted third-party code is run.
- Docs and diagrams describe one model at two zoom levels (three actors over the
  substrate; seven layers in the build view), never two competing models.

## Alternatives considered

**Keep the three-layer model.** It hid the Co-PI/Tasks split and the MCP boundary —
the two things v0.1.0-alpha.2 builds against. **Two separate models (cognitive + build) with a
mapping table.** A 1:1 mapping was the smell that they were redundant; one
good-enough model beats two perfect ones (D42). **Strict layering for every actor.**
False in practice — the PI edits the Vault directly; claiming otherwise misleads
(red-team contradiction 3).

## Related

- **Resolves / supersedes:** [ADR-01](01-three-layer-architecture.md)
- **Related decisions / Depends on:** [ADR-22](22-build-on-hermes-runtime.md),
  [ADR-48](48-copi-and-agent-consolidation.md)
