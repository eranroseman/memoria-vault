---
title: The Compile and Compose flows
parent: Workflows
nav_order: 1
---

# The Compile and Compose flows

Memoria's knowledge cycle has two flows, each with its own direction.

**The Compile flow** brings new knowledge into the vault — sources become your own integrated claims:

```text
find → capture → enrich → classify → (discuss) → distill → link
```

Where `find` is the Librarian surfacing candidate sources; `capture` lands a chosen source as a paper-note from the local `.bib` alone — the guaranteed, offline *nothing-lost* floor (`lifecycle: captured`); `enrich` adds network metadata, full text, and ID-keyed entity/citation links and proposes a classification (`captured → proposed`); `classify` is the human accepting the classification and making the note canonical (`→ current`); `discuss` is an optional Socratic session before claims are written; `distill` is the human writing a claim note from the source; `link` is the human relating that claim into the existing graph (`supports` / `contradicts`). The two human gates are **classify** and **distill** — agents find, capture, and propose; the human canonizes. (`promote`-to-reference and `archive` are knowledge-maintenance, not intake stages; a formal systematic review prepends an opt-in `screen` step.)

**The Compose flow** turns accumulated knowledge into deliverables:

```text
assess → frame → (canvas) → draft → verify ⇄ revise → export
```

Where `assess` is the Mapper charting the corpus (via `scope-project`) and the human deciding whether to proceed — gaps route back to Compile; `frame` is the human and Writer committing to one outline from competing options; `canvas` *(optional)* is laying the chosen claims out spatially to find the argument's structure before prose (a JSON Canvas in `40-workbench/<project>/03-canvas/`); `draft` is the Writer producing prose; `verify ⇄ revise` is the Verifier tracing every claim to a source while the human closes the gaps it flags — a loop, not two passes; `export` is a Pandoc render to the final artifact. The human **review gate** (`review_status: approved`) sits on the transition into export, not as a stage of its own; `query` is a cited-synthesis lookup used across stages, and a `code` artifact is a parallel deliverable type.

The flows are not sequential end-to-end — they're ongoing. The Compile flow runs continuously as new sources are discovered; the Compose flow runs per-project when the human decides to synthesize. A mature vault might have dozens of projects in various stages of the Compose flow while the Compile flow runs nightly. For per-stage definitions see the [Glossary → Cycle stages](../../reference/glossary.md#cycle-stages); the source and writing how-to guides walk through each step.

---

## Related

- The board that coordinates both flows: [The board as a state machine (the control plane)](board-as-state-machine.md)
- The cycle-stage definitions: [Glossary → Cycle stages](../../reference/glossary.md#cycle-stages)
- Why distinct stages with validation points: [Why pattern provenance](../rationale/why-pattern-provenance.md)
