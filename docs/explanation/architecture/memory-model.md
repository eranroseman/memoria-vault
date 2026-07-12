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
forever per [quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

## The ones the runtime manages

**Request memory** (what travels with one queued operation), **session history**
when an optional adapter exists, and **working memory** (the live operation run's
in-context reasoning).

What each substrate holds, its scope and lifespan, and where it is stored is tabulated in [Memory substrates](../../reference/pipelines-and-io/memory-substrates.md); the rest of this page explains *why* each has the scope it does.

**Why the workspace carries durable memory.** The current standalone baseline
makes the workspace the authority. Optional adapters can have chat memory, but
anything durable must become checked workspace state, request/journal evidence,
or a project record. Operation runs ground on request input refs and checked
workspace content, not remembered profile context.

## The placement rule

Every datum has one home, chosen by who authored it: **authored** content
(notes, frontmatter, steering) lives in files — part of the bundle, portable;
**judged** state (verdicts, dispositions, provenance) lives in the database —
engine-space, re-derivable trust; **derived** values (counts, health,
saturation) are computed on read or projected one-way, never stored as if
authored. Files may never self-assert judgment (no verdict fields in
frontmatter), and any "both places" data must be a declared one-direction
projection — `bibliography.bib` from the catalog, `concept_edges` from
frontmatter links **(planned: G2, alpha.22/B1)** — so drift is detectable and
one side is always authority.

### Provenance actors

`observe_pi_edit` attributes unmediated file edits to `pi` by design: an edit that arrives outside the operation envelope is, by definition, the human working in their own editor. Every mediated write carries the envelope's true actor (`pi`, `agent`, `operation`, `integrity`); the engine never defaults a missing actor.

---

## Why each substrate has its scope

Store facts at the narrowest scope that can safely own them. Program steering
can guide the whole workspace; project memory should not leak into other
projects; request memory should not become standing strategy; working memory
should disappear with the run. Audit memory is the exception: it is append-only
because write provenance must survive every session.

The exact substrate table belongs in [Memory substrates](../../reference/pipelines-and-io/memory-substrates.md).

---

## Why the split matters

This is thin-control-over-thick-state applied to memory. Optional adapter memory
stays thin: working memory, chat notes, and searchable history. Durable state
lives in checked workspace files plus request/journal rows.

The split also keeps three vault memories apart: program steering, project working state, and the immutable audit record. Collapsing them hid different scopes and lifespans ([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

---

## Configuration is not memory

A frequent miscategorization is storing a *fact* in a *config* file, or a *rule*
in a memory substrate. The test is: **memory is read back as recall;
configuration is read as rules.** "Use this local model endpoint" is config;
"the PI prefers British spelling" is recall only after it becomes checked
steering or preference state.

For the exact "what lives where" lookup table, use [Memory
substrates](../../reference/pipelines-and-io/memory-substrates.md). This page owns the rationale, not the
field-by-field routing matrix.

---

## Related

**Explanation**

- Request and attention payloads: [The honesty prompt](../execution/control-plane/honesty-card.md)
- Architecture overview: [Architecture](README.md)

**Reference**

- Audit log format: [Policy gate](../../reference/control-and-policy/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/pipelines-and-io/memory-substrates.md)

**Background**

- Optional adapter memory is adapter-local context, not Memoria's durable memory
  authority.
