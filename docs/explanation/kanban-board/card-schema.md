---
title: Why the card schema is split
parent: Kanban board
---


# Why the card schema is split

The card schema divides into two layers: Hermes' fixed built-in fields and a Memoria-specific `metadata` overlay. This page explains why the split exists and why the handoff payload is designed to be self-contained. For the field-by-field tables — each field's name, type, allowed values, and who writes it — see the [card-schema reference](../../reference/kanban-board.md).

---

## Fixed fields vs. the Memoria overlay

The Hermes Kanban schema is fixed and not user-customizable. Memoria cannot add columns, rename fields, or extend the `status` enum. Everything Memoria-specific — the review gate, provenance, handoff payloads — has to live inside the `metadata` JSON field that Hermes treats as opaque.

**Why not fork Hermes to add real columns?** Forking would couple Memoria to a specific Hermes build and break compatibility with stock `hermes kanban` tooling. Storing the overlay in `metadata` means Memoria cards work with any standard Hermes installation while still carrying all the review and provenance semantics Memoria requires.

The cost is that the overlay is *convention*, not *schema*: nothing in Hermes validates it. Workers and the policy MCP are responsible for reading and writing the keys correctly. This is an acceptable trade — the alternative (forking) would be worse.

---

## Why `review_status` is separate from `status`

A card can be `status: running` while `review_status` is still `unreviewed`. This is the normal mid-flight state — a worker making progress does not imply anything about whether the human will eventually accept the output. Keeping the two dimensions orthogonal is what lets dashboards and dispatch logic query review state independently of execution state without any special-casing.

Board fields and note fields are also kept deliberately disjoint. A board card uses `status` and `review_status`. A vault note uses `lifecycle` and `maturity`. The two vocabularies do not overlap, so a query for `lifecycle: current` cannot accidentally match a card, and a card carrying `status: done` says nothing about whether any note is done.

---

## Why the handoff payload must be self-contained

The `metadata` JSON payload that travels with a completed card is not a pointer to shared state — it *is* the context the next worker needs. Hermes delegated children return summaries rather than sharing live parent state, so every handoff must be fully self-contained: the receiving worker should need nothing beyond the payload to begin its work.

This design constraint is why the payload carries an explicit `goal`, structured `context` key-value pairs, an `allowed_paths` write scope, `expected_outputs`, and `review_checks`. Each is something the receiver would otherwise have to reconstruct from a shared context that does not exist between sessions.

Two consequences follow from self-containment:

**`allowed_paths` can narrow but never widen the lane override.** The policy MCP cross-checks the payload against the lane's permissions. A handoff can restrict write scope for a specific card, but it cannot grant the worker more reach than its lane allows. The lane override is the ceiling; the payload sets the floor for that task.

**The exit state is not a payload field.** Workers call `kanban_complete` → `done` or `kanban_block` → `blocked` as lifecycle operations, not by writing JSON. A worker cannot declare its own exit state through the payload — the state machine controls transitions, not the worker's self-assessment.

---

## Why dependencies use `parents`, not scheduling

Cards can depend on other cards through the built-in `parents` array. Hermes uses these edges for execution ordering — a child becomes dispatchable once all its parents complete. Memoria expresses "do B after A" as a dependency edge rather than as a scheduled time.

Scheduling would encode a guess about *when* A finishes. The dependency edge encodes the actual constraint, so the board remains correct even when A runs longer than expected. Use parent-edges only for genuine ordering constraints. Routing (which lane claims a card) and review (whether the human accepts the output) are not dependencies — they live in `assignee` and `review_status` respectively.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- State machine: [Board states and the review gate](states.md)
- Card-schema field tables: [Kanban board reference](../../reference/kanban-board.md)
- How policy gates the payload: [Policy MCP](../../reference/policy-mcp.md)
