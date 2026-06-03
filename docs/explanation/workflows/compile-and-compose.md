---
title: The Compile and Compose flows
parent: Workflows
nav_order: 1
---

# The Compile and Compose flows

Memoria's knowledge cycle has two flows, each with its own direction:

**The Compile flow** brings new knowledge into the vault. Sources are found, enriched, classified, discussed, and distilled into claim notes. The general shape (simplified — the full stage list adds `link`, `corroborate`, `promote`, and `archive`):

```text
find → ingest → classify → (discuss) → distill
```

Where `find` is the Librarian surfacing candidates; `ingest` is the Librarian creating a paper note; `classify` is the human deciding which topics and projects apply; `discuss` is an optional Socratic session for difficult papers; `distill` is the human writing a claim note based on the source. These stage names match the [Glossary](../../reference/glossary.md#cycle-stages) and the source-workflow how-to guides.

**The Compose flow** turns accumulated knowledge into deliverables. A project starts by assessing the corpus, develops through framing, drafting, verification, and revision, and ends with an exported deliverable.

```text
assess → frame → draft → verify → revise → export
```

Where `assess` is the Mapper charting the corpus (via `scope-project`) and the human deciding whether to proceed; `frame` is the human and Writer developing competing outlines; `draft` is the Writer producing prose; `verify` is the Verifier checking citations; `revise` is the human closing the verification gaps; `export` is a Pandoc export producing the final artifact. These names match the [Glossary](../../reference/glossary.md#cycle-stages) and the writing how-to guides.

The flows are not sequential end-to-end — they're ongoing. The Compile flow runs continuously as new sources are discovered; the Compose flow runs per-project when the human decides to synthesize. A mature vault might have dozens of projects in various stages of the Compose flow while the Compile flow runs nightly.

---

## Related

- The board that coordinates both flows: [The board as a state machine (the control plane)](board-as-state-machine.md)
- The cycle-stage definitions: [Glossary → Cycle stages](../../reference/glossary.md#cycle-stages)
- Why distinct stages with validation points: [Why pattern provenance](../rationale/why-pattern-provenance.md)
