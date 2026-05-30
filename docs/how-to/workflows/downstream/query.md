---
topic: workflows
---

# Query

**Group.** Downstream
**Goal.** Ask the vault a question and get a cited synthesis.

## Steps

1. Human asks a question in Obsidian or terminal.
2. The Writer or Librarian searches literature, claim notes, and reference notes — with **query rewrite/decomposition** before retrieval over a **hybrid keyword + dense** retriever (reasoning-relevant questions defeat plain embeddings). **Superseded claim notes (`superseded_by`) are excluded by default**, so the synthesis reflects current belief.
3. Synthesizes an answer with citekeys and links.
4. Proposes filing as an answer note in `10-inbox/`.
5. Human verifies, edits, and either promotes or discards.

## Owners

The **Librarian** runs retrieval-heavy lookups; the **Writer** drafts the synthesis (the dispatcher routes by card type — retrieval-only cards to Librarian, synthesis cards to Writer). The human verifies and files.

## Example

The human asks "what predicts JITAI receptivity?" in the ACP pane → the Writer searches claim notes, reference notes, and paper notes → drafts a cited synthesis as an `answer-note` in `10-inbox/02-answers/`, each assertion tagged with a `[@citekey]` → the human checks the citekeys actually support the claims, edits, and either promotes the answer toward a `claim-note` or discards it.

## Related

- **Answer-draft retention:** [ADR-3 answer-draft retention](../../../project/decisions/03-answer-draft-retention.md) — 90-day surfacing.
- **Profile:** [profiles/librarian.md](../../../explanation/profiles/librarian.md), [profiles/writer.md](../../../explanation/profiles/writer.md)
- **Reasoning-augmented retrieval + superseded-claim exclusion:** [roadmap/evaluation.md](../../../project/roadmap/evaluation.md) (Refinement 3) and [ADR-22](../../../project/decisions/22-claim-supersession.md).
