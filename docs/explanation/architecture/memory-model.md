---
title: The memory model
parent: Architecture
grand_parent: Explanation
nav_order: 2
---

# The memory model

"Memory" in Memoria is not one thing: it is a set of distinct stores -
**substrates** - each with its own scope, owner, and lifespan. Knowing which
substrate a fact lives in is what keeps one operation's request context out of
another's, and durable knowledge out of size-capped session stores. Confusing
the scopes is the source of most "the system forgot" and "the adapter remembered
something it shouldn't" problems.

They're grouped below by how much **you** touch them — the ones you steer and read first, the ones the runtime manages on its own last.

---

## The ones you steer and read

**Program memory** (your standing steering — `steering` discovery priorities +
`screening-protocol` review mode), **project memory** (one sub-project's
cross-operation working state — open questions, decisions, framing), and
**audit memory** (the tamper-evident record of every gated write, append-only
forever per [ADR-127](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

## The ones the runtime manages

**Request memory** (what travels with one queued operation), **session history**
when an optional adapter exists, and **working memory** (the live operation run's
in-context reasoning).

What each substrate holds, its scope and lifespan, and where it is stored is tabulated in [Memory substrates](../../reference/memory-substrates.md); the rest of this page explains *why* each has the scope it does.

**Why the workspace carries durable memory.** Alpha.15 makes the standalone
workspace the authority. Optional adapters can have chat memory, but anything
durable must become checked workspace state, request/journal evidence, or a
project record. Operation runs ground on request input refs and checked
workspace content, not remembered profile context.

---

## Why each substrate has its scope

Store facts at the narrowest scope that can safely own them:

| Substrate | Scope choice | Why it matters |
| --- | --- | --- |
| Program memory | Program-wide, persistent | Holds standing strategy: what to pursue and how to screen. |
| Project memory | One project, archived with it | Keeps a project's working state separate from program strategy. |
| Audit memory | Append-only record | Preserves hash-paired write provenance; see [Policy gate](../../reference/policy-mcp.md). |
| Request memory | One operation request | Carries context across retries and recovery without sharing session state. |
| Adapter memory | Adapter-defined | May help a chat adapter, but never outranks checked workspace state. |
| Session history | Optional searchable recall | Helps answer "did we discuss this?" when an adapter has it, but never outranks the vault. |
| Working memory | One live operation | Keeps active reasoning from leaking across operations or sessions. |

---

## Why the split matters

This is thin-control-over-thick-state applied to memory. Optional adapter memory
stays thin: working memory, chat notes, and searchable history. Durable state
lives in checked workspace files plus request/journal rows.

The split also keeps three vault memories apart: program steering, project working state, and the immutable audit record. Collapsing them hid different scopes and lifespans ([ADR-125](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

---

## Configuration is not memory

A frequent miscategorization is storing a *fact* in a *config* file, or a *rule*
in a memory substrate. The test is: **memory is read back as recall;
configuration is read as rules.** "Use this local model endpoint" is config;
"the PI prefers British spelling" is recall only after it becomes checked
steering or preference state.

For the exact "what lives where" lookup table, use [Memory
substrates](../../reference/memory-substrates.md). This page owns the rationale, not the
field-by-field routing matrix.

---

## Related

**Explanation**

- Request and attention payloads: [The honesty prompt](../control-plane/honesty-card.md)
- Architecture overview: [Architecture](README.md)

**Reference**

- Audit log format: [Policy gate](../../reference/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/memory-substrates.md)

**Background**

- Optional adapter memory is adapter-local context, not Memoria's durable memory
  authority.
