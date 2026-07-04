---
topic: decisions
id: 130
title: Read-API-only surfaces and the agent contract
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [125, 127, 128]
supersedes: [31, 51, 70, 72, 81, 102, 109, 112, 114, 115, 116, 118, 121]
superseded_by: []
---

# ADR-130: Read-API-only surfaces and the agent contract

Consolidation ADR (see ADR-125 preamble). Every human and agent surface, on
one boundary. Supersedes the Obsidian-era surface ADRs while carrying their
three load-bearing rules forward.

## Context

The retired surface stack (Obsidian shell, nav rail, spaces, dashboards,
Bases, the enqueue-only control panel — 70, 81, 109, 114, 115, 116, 118, 121;
the native Obsidian MCP — 31; command surfacing — 72; the projection engine —
102; the tutorial arc — 112) assumed Obsidian hosted the product. Under
ADR-125 the engine is the product and every surface is a client.

## Decision

- **The engine's JSON read-API is the sole read path for every implemented
  Memoria-built surface and every agent**. Alpha.15 implements CLI, scoped MCP,
  and loopback HTTP; plugin, TUI, and web adapters are future clients of this
  same contract, not alpha.15 implementation scope. Class split:
  human editors and generic viewers read corpus files directly (the keep-test's
  point — out of contract, never a gate target); Memoria-built surfaces and
  agents are gate-targeted. No surface opens `memoria.sqlite` or reads
  corpus files behind the engine; a UI gap is fixed by adding a read
  command, never a backdoor. Every knowledge/record projection carries its
  `check_status`; clients render the verdict and never present unchecked
  content as verified. Operational rows carry lifecycle state plus refs.
  `--json` is a versioned contract; the schema stays free behind it.
- **All writes go through the request envelope** and land unchecked
  (ADR-127/128). Carried verbatim from 121: a UI **mutates only by
  enqueueing** — it never writes concepts, verdicts, frontmatter, or commits.
- **The agent contract.** An agent is any delegated agent — Memoria's worker or
  the user's own (Claude Code, Cursor, ChatGPT) — that reads and writes only
  through Memoria. Universally quarantined (its writes pass the same checks as
  anyone's), bounded to read-API + envelope, and **never granted
  file/terminal/exec/send tools by Memoria** (the surviving ADR-32/46
  invariant). Untrusted work text is returned as tagged data, never as
  instructions. Per-agent read scoping lands with the MCP transport to bound
  exfiltration (the lethal-trifecta mitigation); the first-rung all-vault CLI
  agent is **trusted-local dogfood only, never a supported safe surface** —
  the supported path is scope-required from its first non-dogfood transport,
  gated by the poisoned-read fixture family — with the threat model stated:
  **read scoping is a policy boundary for tool-limited/cooperating agents; a
  local agent with its own file tools is in the trusted-local class regardless
  of transport** (any local bearer credential, including a future adapter token,
  is readable by it — the cross-channel credential-reuse fixture documents the
  residual). Every agent exchange exposes its
  plan, sources read, assumptions, unknowns, and pending writes before any
  enqueue (the chat transparency contract); chat is additive, never the
  primary path.
- **One engine API, thin transports, in dependency order**: `engine/api`
  typed functions are the single implementation; the CLI (`--json`,
  transport 0), a FastMCP server (transport 1), and a loopback-HTTP server are
  pure marshalling skins — a wrapper holding logic is a gate failure.
  Remote/OAuth transport is deferred (no consumer).
- **PI direct access, carried from 72**: every routine action is reachable by
  the researcher directly without conversing with an agent. In alpha.15 the
  direct-access surface is the CLI plus the read-API transports above. Future
  UI adapters, including an Obsidian adapter, may expose the same read and
  enqueue actions only as thin clients over this contract; adapter-specific UI
  needs its own ADR before it is scheduled. No alpha.15 slice adds, updates,
  packages, or tests Obsidian plugin source, plugin manifests, command-palette
  commands, Inspector panels, or Obsidian-specific adapter UI.
- **Views are declarative and generated** (carrying 102/116's contract:
  one view definition, projections disposable and never a second truth):
  the read-API may attach a **declarative, graph-bound, verdict-carrying
  view-spec** from a fixed component vocabulary; clients render known kinds
  only. Agent-generated components, shared mutable agent↔UI state, and
  rendering untrusted text as active content are rejected. Surface restraint
  carries from the old doctrine: indicators tie to real decisions, empty is
  success, attention converges to zero.
- **The honesty-card obligations carry** (51): attention items present
  argument-for/against, what-tipped-it, and certainty — never a verdict on a
  proposal; high-cardinality decisions become one batch worklist, never N
  items; loudness stays graded (quiet/notice/alert/block). The inbox-as-
  Obsidian-category mechanism is dead; the card discipline is the attention
  surface's contract — extended with **code-review ergonomics** (review
  effectiveness collapses beyond ~60 minutes/bounded batches): sessions are
  bounded, presentation is span-first with source evidence adjacent (the
  Elicit table pattern), and `--apply` is one click. Making each review
  cheaper is the other half of ADR-128's bargain.
- **The tutorial arc principle carries** (112): one destination-first
  deliverable-driven arc, rebuilt against the CLI/read-API surfaces at the 15
  docs pass.

## Consequences

- A daily UI is a clean client of a proven API; read-API completeness gates
  UI work (a completeness checklist over inbox, graph, gaps, provenance,
  journal, requests, records, project state).
- Future UI adapters stay thin clients over the same read/view/enqueue contract;
  everything hard stays in the engine.
- Four concurrent client paths share one SQLite authority; the workspace
  write lock and single-workspace contract (ADR-127) are the concurrency
  answer, and multi-machine sync of the DB remains out of contract.

## Alternatives considered

- **Framework-hosted UX (CopilotKit-class)** — rejected: inverts the boundary
  via shared mutable agent↔UI state; the engine must own state and writes.
- **Direct vault access for agents (obsidian-local-rest-api-class)** —
  rejected: bypasses read scoping and verdict tagging.
- **MCP as the product surface** — rejected: MCP is one transport over
  `engine/api`; the CLI remains the no-daemon recovery surface.

## Related

- ADR-125 (standalone runtime), ADR-128 (attention surface obligations).
- Future adapter implementation, including any Obsidian plugin, requires its
  own adapter ADR before scheduling.
