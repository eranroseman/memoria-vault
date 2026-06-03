---
title: The two pipelines
parent: Workflows
nav_order: 1
---

# The two pipelines

Memoria distinguishes two pipelines, each with its own direction:

**The upstream pipeline** brings new knowledge into the vault. Sources are found, enriched, classified, discussed, and distilled into claim notes. The general shape (simplified — the full stage list adds `link`, `corroborate`, `promote`, and `archive`):

```text
find → ingest → classify → (discuss) → distill
```

Where `find` is the Librarian surfacing candidates; `ingest` is the Librarian creating a paper note; `classify` is the human deciding which topics and projects apply; `discuss` is an optional Socratic session for difficult papers; `distill` is the human writing a claim note based on the source. These stage names match the [Glossary](../../reference/glossary.md#pipeline-stages) and the source-workflow how-to guides.

**The downstream pipeline** turns accumulated knowledge into deliverables. A project starts by assessing the corpus, develops through framing, drafting, verification, and revision, and ends with an exported deliverable.

```text
assess → frame → draft → verify → revise → export
```

Where `assess` is the Mapper charting the corpus (via `scope-project`) and the human deciding whether to proceed; `frame` is the human and Writer developing competing outlines; `draft` is the Writer producing prose; `verify` is the Verifier checking citations; `revise` is the human closing the verification gaps; `export` is a Pandoc pipeline producing the final artifact. These names match the [Glossary](../../reference/glossary.md#pipeline-stages) and the writing how-to guides.

The pipelines are not sequential end-to-end — they're ongoing. The upstream pipeline runs continuously as new sources are discovered; the downstream pipeline runs per-project when the human decides to synthesize. A mature vault might have dozens of projects in various stages of the downstream pipeline while the upstream pipeline runs nightly.

---

## Related

- The board that coordinates both pipelines: [The board as a state machine (the control plane)](board-as-state-machine.md)
- The pipeline-stage definitions: [Glossary → Pipeline stages](../../reference/glossary.md#pipeline-stages)
- Why distinct stages with validation points: [Why pattern provenance](../rationale/why-pattern-provenance.md)
