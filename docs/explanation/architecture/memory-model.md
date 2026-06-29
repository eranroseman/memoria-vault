---
title: The memory model
parent: Architecture
grand_parent: Explanation
nav_order: 2
---

# The memory model

"Memory" in Memoria is not one thing: it's seven distinct stores — **substrates** — each with its own scope, owner, and lifespan. Knowing which substrate a fact lives in is what keeps one lane's reasoning out of another's, and durable knowledge out of size-capped session stores. Confusing the scopes is the source of most "the agent forgot" and "the agent remembered something it shouldn't" problems.

They're grouped below by how much **you** touch them — the ones you steer and read first, the ones the runtime manages on its own last.

---

## The ones you steer and read

**Program memory** (your standing steering — `steering` discovery priorities + `screening-protocol` review mode), **project memory** (one sub-project's cross-lane working state — open questions, decisions, framing), and **audit memory** (the tamper-evident record of every gated write, append-only forever per [ADR-25](../../adr/25-session-logging-two-logs.md)).

## The ones the runtime manages

**Handoff memory** (what travels with a card between lanes), **agent memory** (the Co-PI's `MEMORY.md` + `USER.md`, the **sole memory carrier** — the background lanes are stateless), **session history**, and **working memory** (the live session's reasoning).

What each substrate holds, its scope and lifespan, and where it is stored is tabulated in [Memory substrates](../../reference/memory-substrates.md); the rest of this page explains *why* each has the scope it does.

`SOUL.md` is adjacent but is *not* memory — it's an agent's identity prompt (its posture), stable across sessions by design.

**Why the Co-PI alone carries memory.** Concentrating every conversation in one agent is what lets Hermes' self-improving loop — **memory · /goals · skills** — compound into a genuine Co-PI rather than fragmenting across lanes that never converse ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The background lanes (Librarian, Writer, Peer-reviewer, Engineer) are stateless propose-then-dispose executors: each run grounds on the card's handoff payload and the vault, never on remembered context.

---

## Why each substrate has its scope

Store facts at the narrowest scope that can safely own them:

| Substrate | Scope choice | Why it matters |
| --- | --- | --- |
| Program memory | Program-wide, persistent | Holds standing strategy: what to pursue and how to screen. |
| Project memory | One project, archived with it | Keeps a project's working state separate from program strategy. |
| Audit memory | Append-only record | Preserves hash-paired write provenance; see [Policy MCP](../../reference/policy-mcp.md). |
| Handoff memory | One board card | Carries context across lanes without sharing session state. |
| Agent memory | Co-PI only, loaded at session start | Holds stable recall; token caps make it unsuitable for task state. |
| Session history | Searchable recall | Helps answer "did we discuss this?" but never outranks the vault. |
| Working memory | One live session | Keeps active reasoning from leaking across agents or sessions. |

---

## Why the split matters

This is thin-control-over-thick-state applied to memory. Hermes-native memory stays thin: working memory, capped Co-PI notes, and searchable history. Durable state lives in files: handoff payloads while work is in flight, and the vault after review.

The split also keeps three vault memories apart: program steering, project working state, and the immutable audit record. Collapsing them hid different scopes and lifespans ([ADR-23](../../adr/23-scoped-memory-substrates.md)).

---

## Configuration is not memory

A frequent miscategorization is storing a *fact* in a *config* file, or a *rule*
in a memory substrate. The test is: **memory is read back as recall;
configuration is read as rules.** "Topics `jitai`, `mhealth` belong to the
scoping-review project" is a rule (config → [Configure project
hints](../../how-to-guides/setup/configure-project-hints.md)); "the user prefers
British spelling" is recall (agent memory).

For the exact "what lives where" lookup table, use [Memory
substrates](../../reference/memory-substrates.md). This page owns the rationale, not the
field-by-field routing matrix.

---

## Related

**Explanation**

- Board handoff payload (handoff memory travels here): [The honesty card](../kanban-board/honesty-card.md)
- Architecture overview: [Architecture](README.md)

**How-to**

- Configuring project hints (the config example above): [Configure project hints](../../how-to-guides/setup/configure-project-hints.md)

**Reference**

- Audit log format: [Policy MCP](../../reference/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/memory-substrates.md)

**Background**

- Hermes native memory: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
