---
title: Operation postures
parent: Explanation
nav_order: 3
has_children: true
permalink: /explanation/operation-postures/
---

# Operation postures

Operation postures are the current replacement for the old installed-profile
language — drafting and review stances the CLI and its operations adopt. The
old profile language maps to them this way:

| Old profile concept | Alpha.18 replacement |
| --- | --- |
| Co-PI profile | `memoria ask` / `memoria project ask` query flow |
| Background lane profile | Checked operation manifest plus request row |
| Profile skill | Capability manifest or operation implementation |
| Lane override | Operation `allowed_paths` / optional adapter policy |
| Kanban card | Operation request and attention item |

The durable source of truth is now
`src/memoria_vault/product/capabilities/operations/` plus the standalone
CLI/engine. Optional adapters may present chat or board
interfaces, but they must call the same engine and may not become the authority
for capabilities, provider config, or write policy.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The Co-PI](co-pi.md) | The conversational, read-only posture behind `memoria ask` — questions, explains, and routes durable work to CLI/engine requests. |
| [The Librarian](librarian.md) | The faithful intake-through-mapping posture — catalog, extract, link, and map operations that surface candidates and gaps. |
| [The Writer](writer.md) | The generative, draft-only posture that turns checked evidence into structured prose proposals. |
| [The Peer-reviewer](peer-reviewer.md) | The skeptical, independent verification posture that flags soundness issues without auto-fixing them. |
| [The Engineer](engineer.md) | The handoff posture that scaffolds and records external coding work without granting Memoria code-execution authority. |

## Delegation posture

Delegation is request based in the standalone runtime. A request can narrow scope through input
refs, output intents, and required checks, but it cannot widen the operation
manifest's authority.

## Related

- Current command surface: [CLI](../../reference/cli.md)
- Operation manifests: [Operations](../../reference/operations.md)
