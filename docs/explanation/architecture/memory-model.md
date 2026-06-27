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

**Program memory** (your standing steering — `research-focus` discovery priorities + `screening-protocol` review mode), **project memory** (one sub-project's cross-lane working state — open questions, decisions, framing), and **audit memory** (the tamper-evident record of every gated write, append-only forever per [ADR-25](../../adr/25-session-logging-two-logs.md)).

## The ones the runtime manages

**Handoff memory** (what travels with a card between lanes), **agent memory** (the Co-PI's `MEMORY.md` + `USER.md`, the **sole memory carrier** — the background lanes are stateless), **session history**, and **working memory** (the live session's reasoning).

What each substrate holds, its scope and lifespan, and where it is stored is tabulated in [Memory substrates](../../reference/memory.md); the rest of this page explains *why* each has the scope it does.

`SOUL.md` is adjacent but is *not* memory — it's an agent's identity prompt (its posture), stable across sessions by design.

**Why the Co-PI alone carries memory.** Concentrating every conversation in one agent is what lets Hermes' self-improving loop — **memory · /goals · skills** — compound into a genuine Co-PI rather than fragmenting across lanes that never converse ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The background lanes (Librarian, Writer, Peer-reviewer, Engineer) are stateless propose-then-dispose executors: each run grounds on the card's handoff payload and the vault, never on remembered context.

---

## Why each substrate has its scope

The scoping isn't arbitrary — it follows from what each substrate holds, and the cost of getting it wrong.

**Program memory** is program-wide and persistent because it's the standing strategy you set for the whole research effort — what to pursue (`research-focus`) and how to screen (`screening-protocol`). Every agent that touches the program reads it; you refresh it on your own cadence. It never archives, because the program outlives any one sub-project.

**Project memory** is scoped to a single sub-project and archives with it. A project in `projects/<project>/` is a bounded, transient effort; its open questions and decisions are working state that matters while the project is live and becomes provenance once it ships. Keeping it separate from program memory holds "what I want pursued overall" apart from "where this one project's thinking is" — different scope, different lifespan.

**Audit memory** is append-only because its value is the complete, unmodified record. Agents read it; the Policy MCP writes an entry at every gated write. The constraint is enforced, not advisory — every gated write is hash-paired so it can be reversed and tamper is detectable; that mechanism is owned by [Policy MCP](../../reference/policy-mcp.md), and audit memory is the immutable substrate it writes to. Capture must start from day one, because the cost and human-loop trends it tracks can't be reconstructed retroactively.

**Handoff memory** is per-card rather than per-agent because the handoff is the unit of cross-lane communication. When a card moves from the Librarian lane to the Writer lane, the payload travels with it; the Writer inherits the structured handoff, never the Librarian's session context. That's what makes cross-lane handoffs reliable without agents sharing session state.

**Agent memory** belongs to the Co-PI and is frozen at session start because it's injected as a snapshot into the system prompt. The token caps on `MEMORY.md` (~800) and `USER.md` (~500) are load-bearing: anything larger gets truncated. So it holds stable facts only — in-flight task state belongs in handoff memory, cross-project state in program or project memory.

**Session history** is the cross-session recall channel but carries no authority. It's searchable history — useful for "did we discuss X before?" — but it never gates promotion and is never authoritative over the vault. A session-history result that contradicts a vault note loses; the vault is ground truth.

**Working memory** is correctly session-scoped because it's the agent's active reasoning state. Sharing it across agents would bleed one lane's in-flight reasoning into another's. Discarding it on `/clear` costs nothing — anything worth keeping must be written to a durable substrate.

---

## Why the split matters

This is thin-control-over-thick-state applied to memory. The Hermes-native substrates are deliberately thin — bounded working memory, capped agent notes, on-demand session history — so an agent carries minimal persistent state. The durable, compounding knowledge lives in thick files: the board's handoff payloads while work is in flight, and the vault while it's settled.

The vault side then splits by *purpose and lifespan*: **program memory** is your standing steering (persistent, program-wide); **project memory** is one effort's working state (bounded, archives with the project); **audit memory** is the immutable record of what happened. Collapsing program and project into one bucket — as the model originally did — hid that a program-wide steering file and per-project scratch are different kinds of memory, on different scopes and lifespans ([ADR-23](../../adr/23-scoped-memory-substrates.md)).

Without the split, every cross-session question collapses into "store it and hope," and agents either share too much (leaking context between lanes) or too little (re-deriving the goal every session). The substrates make "where does X live?" answerable by scope and lifespan.

---

## Configuration is not memory

A frequent miscategorization is storing a *fact* in a *config* file, or a *rule* in a memory substrate. The seven substrates hold state the system produces and reads back as **recall**; configuration is input you author that the agent reads as **rules**. Keep them distinct:

| If the thing is… | It belongs in… | Not in… |
| --- | --- | --- |
| A durable fact or convention the agent should recall | Agent `MEMORY.md` | `project-hints.yaml` (that's config, not recall) |
| Your working style or preferences | Agent `USER.md` | `MEMORY.md` (keep identity vs. preference separate) |
| What you want the system to pursue | Program memory (`research-focus`) | `project-hints.yaml` |
| Which topics map to which project | `.memoria/project-hints.yaml` (config) | a memory substrate |
| A synthesized claim or finding | Vault notes (`notes/claims/`) | any memory substrate |

The test: **memory is read back as recall; configuration is read as rules.** "Topics `jitai`, `mhealth` belong to the scoping-review project" is a rule (config → [Configure project hints](../../how-to-guides/setup/configure-project-hints.md)); "the user prefers British spelling" is recall (agent memory).

---

## Related

**Explanation**

- Board handoff payload (handoff memory travels here): [The honesty card](../kanban-board/card-schema.md)
- Architecture overview: [Architecture](README.md)

**How-to**

- Configuring project hints (the config example above): [Configure project hints](../../how-to-guides/setup/configure-project-hints.md)

**Reference**

- Audit log format: [Policy MCP](../../reference/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/memory.md)

**Background**

- Hermes native memory: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
