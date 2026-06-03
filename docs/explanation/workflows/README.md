---
title: Workflows
parent: Explanation
nav_order: 7
has_children: true
permalink: /explanation/workflows/
---

# The workflow model

Memoria's workflows are **state-machine paths on the board**, not scripted procedures. Understanding this distinction is the key to understanding why the system behaves the way it does — and why it's more resilient than a procedural approach.

---

## Workflows as state-machine paths

A scripted procedure says: "do step 1, then step 2, then step 3." If step 2 fails, the script fails. The state of the work lives implicitly in how far along the script got.

A state-machine path says: "a card in state A, assigned to profile P, moves to state B when condition C is met." The state of the work is **explicit, persistent, and queryable**. If something fails, the card stays in its current state, the failure is recorded, and dispatch retries or escalates.

The difference matters most in long-horizon work. A research task doesn't complete in one session. Sources are found over days, synthesis develops over weeks, verification happens in parallel with drafting. A scripted procedure can't represent "this task is in progress across three sessions" — a state machine can.

---

## The two pipelines

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

## What coordinates work: the board

The board is the shared state machine. Every long-lived piece of work lives on the board as a card until a human approves it. The board coordinates work across sessions, profiles, and pipelines by making state explicit and persistent.

See [The board as a state machine (the control plane)](board-as-state-machine.md) for why Kanban — not chat, not a custom orchestration system — is the right coordination layer.

---

## What makes synthesis human-owned

At every synthesis boundary — when an `answer-note` might become a `claim-note`, when a draft might become a deliverable, when a candidate might enter the canonical vault — the workflow pauses. A `done` card waits for `review_status: approved` before anything downstream proceeds.

This pause is not a workflow bottleneck in the negative sense — it is the mechanism that keeps the human in contact with what the system is producing. See [Review as a first-class state](review-as-state.md) for how review is implemented as a structured state rather than a convention.

---

## Documents in this section

- **[The board as a state machine (the control plane)](board-as-state-machine.md)** — why Kanban is the coordination layer: cards, states, and the persistence properties that make long-horizon work reliable.
- **[Review as a first-class state](review-as-state.md)** — why review is a first-class state in the card schema, what makes it structural rather than advisory, and how it coordinates the human with the agents.

For step-by-step workflow recipes, see [how-to guides](../../how-to-guides/).
