---
title: The knowledge cycle
parent: Knowledge
grand_parent: Explanation
nav_order: 2
---

# The knowledge cycle

Every note in the vault is somewhere in a long-term progression from catalogued source to written output. Understanding the cycle as a whole — what it is for, where it gets stuck, and what makes it compound — is the conceptual foundation for understanding why the vault is structured the way it is.

## The six delegable tasks

The PI works at the three spaces — **Library**, **Knowledge**, and **Project** — not along a pipeline, plus the **Inbox** queue. Library, Knowledge, and Project are where knowledge is taken in, built into claims, and turned into output; the Inbox queue is where the agents' proposals surface for a decision. Beneath the spaces, six tasks can be delegated to a background agent lane; each task's name is at once the action, the lane, and the Inbox signal it raises:

| Task        | What it does                                            | Inbox signal    |
| ----------- | ------------------------------------------------------- | --------------- |
| **catalog** | find and record a source (entity record + candidate)    | `candidate`     |
| **extract** | distill a kept source toward claim stubs                | (work prompt)   |
| **link**    | propose connections between claims                      | (link proposal) |
| **map**     | scope a corpus — coverage, clusters, writability        | `gap`           |
| **draft**   | generate proposed prose with bound citations            | —               |
| **verify**  | check citations, trace claims, red-team the argument    | `flag`          |

The tasks are **individually triggered, not a set**. A human gate — often a long gap — sits between each: a source is catalogued; much later, if ever, extracted; only after a claim exists does linking fire. The four Librarian tasks (catalog, extract, link, map) belong to the Librarian posture, draft to the Writer, and verify to the Peer-reviewer; the authoritative task-lane → profile map lives in [Profile capabilities](../../reference/profiles.md). All six are reachable from the spaces via the command palette.

A new source typically arrives as a `candidate` card, is kept at triage, and becomes a Catalog entity plus a `proposed` source note. The PI reads it, distills claims in their own words, and confirms the links that connect them into the graph. Those claims mature and cross-link; once enough accumulate, a project maps the corpus, drafts, verifies, and ships.

**The loop that compounds:** gaps found in _map_ and _verify_ raise Inbox `gap` cards that re-trigger _catalog_. The output end of the cycle feeds the intake end — what you write exposes what you're missing, and what you catalog next is shaped by what you tried to write.

## Why the cycle is not a linear path

The cycle describes the intended direction of flow, not a timeline or a required sequence. A claim can remain at `maturity: seedling` for months — that is normal, not broken. A source note can sit `current` for a year before there is enough surrounding context to extract claims from it. A new paper may arrive and retroactively change what an older claim was arguing.

What the cycle prevents is the two failure modes at opposite ends: notes that are captured but never synthesized (the vault grows but never compounds), and claims that are synthesized but never written from (the knowledge accumulates but never produces output). The cycle's shape names these as distinct failure modes because they look identical from the outside — both appear as an active vault — but indicate different structural problems.

## Why the vault compounds rather than accumulates

The distinction between a vault that compounds and one that merely accumulates is in the density of the claim layer. A vault with 500 catalog entities and 10 claims is a sophisticated reading list — useful for finding sources but not for writing from. A vault with 50 source notes and 40 claims that link to each other and to hubs is a structure the PI can write from directly, navigating the graph of connected ideas rather than remembering what they read.

A new source's value is not the text it contains but what it contributes to existing claims — the connections it makes explicit, the contradictions it names, the open questions it opens or closes. Compounding-through-connection is the **Zettelkasten** wager — that a densely linked note collection becomes a thinking partner rather than a filing cabinet. The claim density that separates a compounding vault from an accumulating one is the same density Luhmann's slip-box depended on (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

## Where the cycle gets stuck

The Inbox and the dashboards surface exactly where work has stopped. Sources awaiting reading and distillation surface in the reading-pipeline dashboard. Unconnected claims surface in open-questions and loose-ends. Open verification findings surface as `flag`/`alert` cards on the board. The correspondence between stuck points and views is not accidental — they were designed to make the cycle's failure modes visible before they compound.

The one transition the dashboards cannot surface is when developed claims are never assembled into a draft — that gap is a judgment call, not a structural signal. It is also the hardest gap to notice, because a vault full of well-developed claims looks healthy even when nothing is being written. (The _map_ task's writability and readiness reports exist to prompt exactly this.)

## Why archiving preserves the cycle's integrity

Notes that are no longer useful do not become invisible by deletion — they become gaps in the provenance graph. A deleted source note breaks every claim that cited it; a deleted claim leaves later notes without their grounding.

Archiving preserves the chain, and since `archived` became a **state rather than a folder** ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)), it costs nothing structurally: the note stays in its type-home, remains readable and in Git history, drops out of active views and the agents' working scope, and can still be traced from any note that linked to it. No file moves, so no links break. The cycle's integrity depends on every step being traceable backward, not just forward. Archiving itself is propose-only for every actor but the PI.

## Related

**Explanation**

- The ritual that keeps the cycle from stalling: [The weekly-review dashboard](../dashboards/structural-health/weekly-review.md)
- The cycle's tempo over your first weeks of real use: [Your first month](your-first-month.md)
- The epistemic roles of document types: [Document types and epistemic roles](document-types.md)
- Why promotion is gated: [Why promotion is gated](promotion-model.md)
- The folder structure the cycle flows through: [The vault](../architecture/vault.md)

**How-to**

- The weekly maintenance pass: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The cycle's key transition: [Write a claim note](../../how-to-guides/knowledge/write-a-claim-note.md)
