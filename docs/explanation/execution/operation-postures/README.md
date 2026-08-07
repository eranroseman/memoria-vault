---
title: Operation postures
parent: Execution
grand_parent: Explanation
nav_order: 2
has_children: true
permalink: /explanation/execution/operation-postures/
---

# Operation postures

Operation postures replace the old installed-profile language with drafting and
review stances the CLI and operations adopt. The important change is ownership:
posture describes behavior, while operation manifests and request rows own the
runtime contract.

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

How the five postures relate to each other, to the write boundary, and to the
PI:

```mermaid
flowchart TD
    subgraph postures ["Five postures: posture describes behavior, while operation manifests and request rows own the runtime contract"]
        copi["The Co-PI<br/>authority: read-only<br/>questions, explains, routes"]
        librarian["The Librarian<br/>authority: faithful - include generously,<br/>report state accurately, let the review gate filter<br/>intake, extraction, linking, mapping"]
        writer["The Writer<br/>authority: generative, draft-only<br/>every output is a proposal in draft.md"]
        reviewer["The Peer-reviewer<br/>authority: skeptical, deliberately independent -<br/>flag, don't fix<br/>reads a draft for soundness, not just facts"]
        engineer["The Engineer<br/>authority: no terminal, file, or code execution<br/>scaffolds and records a code handoff;<br/>the external coding agent does the coding"]

        librarian -. "not its own reviewer: the posture that gathers<br/>and proposes must not also grade the result" .-> reviewer
        reviewer -. "not the Co-PI's sparring: a formal pass over a finished<br/>artifact, not continuous in-conversation questioning" .-> copi
        copi -. "the Co-PI is not an author and the Writer is not the Co-PI:<br/>conversation stays read-only, and prose is composed only after<br/>the thinking is represented as checked workspace context<br/>or an explicit request" .-> writer
        engineer -. "not a documenter of research: writing about the<br/>methodology or results is the Writer's domain" .-> writer
    end

    boundary["The worker/trusted-writer boundary<br/>enforces the hard write-wall for runtime operations"]
    pi["The PI<br/>makes every triage, disposition, and promotion decision"]

    copi -- "routes durable work to CLI/engine requests" --> boundary
    librarian -- "suggested links, notes, and hub updates" --> boundary
    writer -- "prose proposals in draft.md" --> boundary
    reviewer -- "findings as attention or draft verification output" --> boundary
    engineer -- "provenance and the commit/revert checkpoint" --> boundary
    boundary -- "the review gate filters" --> pi

    librarian -. "not the owner of synthesis judgment: note acceptance<br/>and hub curation stay with the PI" .-> pi
    writer -. "not a promoter: a draft becoming part of a checked note,<br/>hub, or deliverable is the PI's move" .-> pi
    reviewer -. "not a truth oracle: truth stays the PI's domain" .-> pi
```

## Delegation posture

Delegation is request based in the standalone runtime. A request can narrow scope through input
refs, output intents, and required checks, but it cannot widen the operation
manifest's authority.

## Related

- Current command surface: [CLI](../../../reference/commands-and-transports/cli.md)
- Operation manifests: [Operations](../../../reference/commands-and-transports/operations.md)
