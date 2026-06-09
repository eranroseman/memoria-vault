---
title: Why promotion is gated
parent: Knowledge
nav_order: 5
---

# Why promotion is gated

Promotion is the act of moving a note from one lifecycle stage to a more canonical one — from inbox to sources, from draft to synthesis, from synthesis to deliverable. In Memoria, promotion at the synthesis boundary requires explicit human approval. This is not a safeguard bolted onto the system; it is the mechanism that keeps the vault trustworthy.

---

## What "canonical" means

A note in the vault's canonical zones (`30-synthesis/`, `50-deliverables/`) is trusted content. When a Verifier checks a draft, it checks whether the draft's claims trace back to sources in `20-sources/`. When a human builds on a claim note, they assume the claim represents something they've actually concluded — not something an agent drafted and left in the vault. When an export runs, it pulls from `50-deliverables/` as finished work.

The trust assumption in canonical zones is not just a convention; it's what makes downstream work reliable. If canonical zones can be written to without review, the trust assumption fails, and every downstream use of canonical content becomes suspect.

---

## The promotion map

Promotion follows a one-way path through lifecycle stages. The legal moves:

```text
fleeting-note  ──► paper-note / item-note  (Librarian enriches, human classifies)
fleeting-note  ──► claim-note              (human writes directly)
fleeting-note  ──► (discarded)

answer-note    ──► claim-note              (human distills)
answer-note    ──► (discarded)

candidate-note ──► paper-note / item-note  (Librarian ingests after human accepts)
candidate-note ──► (discarded)

claim-note     ──► reference-note          (when evergreen and cross-linked)
claim-note     ──► moc membership          (via frontmatter moc:)

draft          ──► deliverable             (on export)
```

Two clarifications on the map. **Source notes are not only papers**: a captured repository, package, product, dataset, or standard promotes along the same path but lands as an `item-note` in `20-sources/02-items/` — the destination keys on whether the source carries a stable publication ID, not on any difference in how the note is handled (see [Note types and epistemic roles](note-types.md)). **Entity notes** (`person-note`, `organization-note`, `venue-note`) are created as cross-link side-effects during ingestion rather than promoted from an earlier stage, so they don't appear above. And `candidate-note` is the 16th type (adopted in v0.1 — [ADR-17](../../adr/17-shared-candidate-frontmatter.md); see [Note types and epistemic roles](note-types.md)); its two rows are live for the discovery and gap-card paths.

Several moves are explicitly disallowed:

- A `paper-note` never becomes a `claim-note`. A source note describes what the source says; a claim note says what the human thinks. These are different epistemic acts, and conflating them loses provenance. The path is: paper-note → human discusses with Socratic → human writes claim-note → claim-note links to paper-note.
- Agents never write `claim-note` directly. Agents can draft proposals (in `answer-note`), but the canonical claim requires human authorship.
- Notes move to `95-archive/` only by human action. Agents never archive.

---

## Why the human gate is at synthesis, not at sources

Sources (`20-sources/`) have a different trust profile than synthesis (`30-synthesis/`). A paper note records what a paper says — this can be verified against the paper. If the Librarian makes a mistake (wrong summary, missed nuance), the paper is still there; a reader can check. Source notes are recoverable.

Synthesis notes are not recoverable in the same way. A claim note says what the human thinks. There is no external document to check against. If a claim note is wrong, there is nothing to verify it against except other notes and the human's own judgment. The compounding risk is higher: a wrong claim note gets cited, built on, and referenced in deliverables. Finding the error later requires tracing through the citation graph.

This is why the gate is at the synthesis boundary, not the source boundary. Sources are controlled enough (enrichment protocols, schema enforcement) that agent-write with human-review is appropriate. Synthesis requires human authorship.

---

## Maturity as a signal, not a gate

Claim notes carry a `maturity` field with values `seedling`, `budding`, `evergreen`. Maturity is not a promotion gate — a `seedling` claim is still a canonical claim. It is a signal to the human about how much confidence to place in the claim for downstream use.

The progression from seedling to evergreen is organic: a claim becomes more evergreen as it accumulates corroborating links, as it survives the addition of contradictory evidence, and as the human revisits and refines it. There is no automated promotion from `seedling` to `evergreen`; the human sets the maturity in judgment.

The `seedling → budding → evergreen` vocabulary is borrowed from the **evergreen-notes** tradition that grew out of Zettelkasten (Andy Matuschak's framing of notes that are developed over time rather than written once). Memoria adopts the maturity ladder but, per its bookkeeping-not-intelligence stance, keeps the maturity judgment human-set — see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten).

A common pitfall is using `maturity` as a reason to defer promotion: "I'll make it canonical when it's evergreen." This misunderstands the model. Make a claim canonical when the human has decided it represents their position. Maturity tracks confidence in the claim; promotion tracks whether the human has claimed it as theirs.

---

## The role of the review gate in promotion

The formal promotion mechanism is the review gate on the board card. When an agent produces a `paper-note` or an `answer-note`, it completes the card to `done` with `review_status: requested`. The human reviews the work, then sets `review_status` to `approved` (the output stays) or `rejected` (the output is revised or discarded).

Promotion to canonical is a separate step from the card's approval. The card's approval says "this agent did good work." Promotion to synthesis says "I, the human, am making this my position." The two can happen at different times.

In practice: the human approves a `paper-note` (good summary, correct fields) and later writes a `claim-note` based on it. The card's approval and the promotion are both human actions; they're just different actions.

---

## Why this feels slow

The human gate at the synthesis boundary is the single biggest bottleneck in the system. Agents can discover, classify, and draft faster than a human can review. The queue of done-awaiting-review cards grows unless the human keeps pace.

This is the design. The bottleneck at synthesis is not a performance problem to optimize away — it is the proof that the human is in contact with what the system is producing. A system that can autonomously populate `30-synthesis/` without human attention is a system where the human no longer owns their own knowledge base.

The right response to a full review queue is not to automate review. It is to maintain the WIP cap (a limit on how many done-awaiting-review cards can exist, enforced by the board), which creates back-pressure: when the queue is full, new cards stop being created. This prevents agents from racing ahead of human attention.

---

## Related

**Explanation**

- The three epistemic roles: [Note types and epistemic roles](note-types.md)
- Why lifecycle folders enable this: [Why folders encode lifecycle, not topic](lifecycle-over-topic.md)
- Why the review gate is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- How the board's review state works: [Review as a first-class state](../workflows/review-as-state.md)
- The folders promotion moves between: [The vault](../architecture/vault.md)

**Reference**

- The reference promotion map: [Note types](../../reference/note-types.md)
