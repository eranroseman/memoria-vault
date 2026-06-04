---
title: The Compile and Compose flows
parent: Workflows
nav_order: 1
---

# The Compile and Compose flows

Memoria's knowledge cycle has two flows, each a sequence of **phases**:

```text
  Compile   sources → claims
    find → capture → enrich → [classify] → discuss* → [distill] → connect

  Compose   claims → deliverable
    assess → frame → sketch* → draft → verify → «review» → export

  [ ] human gate      * reflective phase (engaged by judgment)      «» review gate
```

The two flows form one cycle: Compile's claims are Compose's raw material, and gaps surfaced during Compose — plus new claims written while drafting — feed back into Compile. Neither is a one-shot script; both run continuously.

**The Compile flow** brings new knowledge into the vault — sources become your own integrated claims. `find` is the Librarian surfacing candidate sources; `capture` lands a chosen source as a paper-note from the local `.bib` alone — the guaranteed, offline *nothing-lost* floor (`lifecycle: captured`); `enrich` adds network metadata, full text, and ID-keyed entity/citation links and proposes a classification (`captured → proposed`); `classify` is the human accepting the classification and making the note canonical (`→ current`); `discuss` is the reflective phase — questioning the source through the Socratic profile before any claim is written; `distill` is the human writing a claim note from the source; `connect` is the human relating that claim into the existing graph (typed `supports` / `contradicts`). The two human gates are **classify** and **distill** — agents find, capture, and propose; the human canonizes. (`promote`-to-reference and `archive` are knowledge-maintenance, not intake phases; a formal systematic review prepends an opt-in `screen` phase.)

**The Compose flow** turns accumulated knowledge into deliverables. `assess` is the Mapper charting the corpus (via `scope-project`) and the human deciding whether to proceed — gaps route back to Compile; `frame` is the human and Writer committing to one outline from competing options; `sketch` is the reflective phase — laying the chosen claims out spatially (a JSON Canvas in `40-workbench/<project>/03-canvas/`) to find the argument's structure before prose; `draft` is the Writer producing prose; `verify` is the Verifier tracing every claim to a source while the human closes the gaps it flags — a check ↔ fix loop, not a single pass; `export` is a Pandoc render to the final artifact. The human **review gate** (`review_status: approved`) sits on the transition into export, not as a phase of its own; `query` is a cited-synthesis lookup used across phases, and a `code` artifact is a parallel deliverable type.

**`discuss` and `sketch` are the cycle's two reflective phases** — the deliberate "think before you commit" beats where the human does the intellectual work the rest of the cycle exists to set up and capture. They're engaged by judgment (a difficult source, a tangled argument), not run on every item — a matter of cadence, not importance.

The flows are not sequential end-to-end — they're ongoing. The Compile flow runs continuously as new sources are discovered; the Compose flow runs per-project when the human decides to synthesize. A mature vault might have dozens of projects in various phases of the Compose flow while the Compile flow runs nightly. For per-phase definitions see the [Glossary → Cycle phases](../../reference/glossary.md#cycle-phases); for which profile owns each phase, see [Profiles](../profiles/README.md); the source and writing how-to guides walk through each.

---

## Related

- The board that coordinates both flows: [The board as a state machine (the control plane)](board-as-state-machine.md)
- Which profile owns each phase: [Profiles](../profiles/README.md)
- The cycle-phase definitions: [Glossary → Cycle phases](../../reference/glossary.md#cycle-phases)
- Why distinct phases with validation points: [Why pattern provenance](../rationale/why-pattern-provenance.md)
