
# Explanation

This section is for **understanding** Memoria — what it is, how it thinks, and why it was built the way it was. These documents answer "why" and "what is" questions. They are for reading and reflection, not for following step-by-step.

If you need to *do* something, see [how-to guides](../how-to-guides/). If you need exact values, field names, or configuration formats, see [reference](../reference/). If you want a guided first experience, see [tutorials](../tutorials/).

---

## What explanation documents do (and don't do)

Explanation documents build a mental model. They:

- Answer "why is it this way?" and "what does this mean?"
- Compare alternatives and explain trade-offs
- Provide context and intellectual background
- Make connections between concepts

They don't include step-by-step instructions, lookup tables, or precise configuration values. When an explanation references exact schemas or commands, it points to the reference section.

---

## Conceptual map

Read from the inside out: start with what the system is, then how it's structured, then how each design area works.

### Start here

1. **[what-memoria-is.md](what-memoria-is.md)** — the system's identity: what it is, what it's not, and why it exists. Everything else builds on this.
2. **[intellectual-foundations.md](intellectual-foundations.md)** — the three ideas Memoria is built on (Karpathy, Zettelkasten, Memex) and how the AI-research systems survey shaped the design.

### The architecture

3. **[architecture/README.md](architecture/README.md)** — the three-layer model: board, workers, vault.
4. **[architecture/why-three-layers.md](architecture/why-three-layers.md)** — why these three concerns are kept separate.
5. **[architecture/why-specialist-profiles.md](architecture/why-specialist-profiles.md)** — why seven specialists instead of one generalist agent.
6. **[architecture/why-human-gate.md](architecture/why-human-gate.md)** — why the review gate is structural, not advisory.
7. **[architecture/why-not-autonomous.md](architecture/why-not-autonomous.md)** — the autonomy ceiling and why Memoria doesn't cross it.

### The knowledge model

8. **[knowledge/README.md](knowledge/README.md)** — how the vault organizes durable knowledge.
9. **[knowledge/lifecycle-over-topic.md](knowledge/lifecycle-over-topic.md)** — why folders encode lifecycle stage, not subject area.
10. **[knowledge/note-types.md](knowledge/note-types.md)** — the three epistemic roles of notes: source, claim, reference.
11. **[knowledge/promotion-model.md](knowledge/promotion-model.md)** — why moving knowledge forward is gated, not automatic.

### The workflow model

12. **[workflows/README.md](workflows/README.md)** — how work moves through the system.
13. **[workflows/board-as-state-machine.md](workflows/board-as-state-machine.md)** — why Kanban, not chat, is the coordination layer.
14. **[workflows/review-as-state.md](workflows/review-as-state.md)** — why review is a first-class state, not a comment or convention.

---

## Entry points by background

**New to Memoria:** The identity documents (1–2), the three-layer architecture overview (3), the knowledge model overview (8), and the workflow overview (12) together provide a working mental model of the system. The architecture and workflow subsections fill in the detail from there.

**Coming from another agent system (LangChain, CrewAI, autogen, etc.):** The key differences from those systems — specialist lanes, structural human gate, no reasoning orchestrator — are concentrated in the specialist-profiles rationale (5), the human-gate rationale (6–7), and the board-as-state-machine explanation (13).

---

## For decisions and direction

The *why* behind a specific choice lives in an ADR. The forward plan lives in the roadmap. Both are in [project/](../../project-files/): [decisions/](../../project-files/decisions/) for the ADRs, [roadmap/](../../project-files/operations/) for direction. *(Stubs — content coming.)*
