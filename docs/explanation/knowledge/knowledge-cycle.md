---
title: The knowledge cycle
parent: Knowledge
grand_parent: Explanation
nav_order: 2
---

# The knowledge cycle

Every note in the vault is somewhere in a long-term progression from catalogued source to written output. Understanding the cycle as a whole — what it is for, where it gets stuck, and what makes it compound — is the conceptual foundation for understanding why the vault is structured the way it is.

## Delegable tasks are not a pipeline

The PI works at the three spaces — **Library**, **Knowledge**, and **Project** —
plus the **Inbox** queue. Beneath them, capability-backed operations can capture,
enrich, extract, link, map, digest, and verify; the concrete operation surface
lives in [Operations](../../reference/operations.md).

These tasks are **individually triggered, not a set**. A human gate — often a
long gap — sits between each: a source is catalogued; much later, if ever,
extracted; only after a claim exists does linking fire.

A new source typically arrives as a catalog row plus a `candidate` attention
item, is kept or rejected by the PI, and becomes checked source state only after
the required enrichment and review checks pass. The PI reads it, distills claims
in their own words, and confirms the links that connect them into the graph.
Those claims mature and cross-link; once enough accumulate, a project maps the
corpus, drafts, verifies, and ships.

**The loop that compounds:** gaps found in mapping and verification raise Inbox
attention that can trigger new capture/catalog work. The output end of the cycle
feeds the intake end - what you write exposes what you're missing, and what you
catalog next is shaped by what you tried to write.

## Why the cycle is not a linear path

The cycle describes the intended direction of flow, not a timeline or a required
sequence. A note can remain underdeveloped for months — that is normal, not
broken. A checked source work can sit for a year before there is enough
surrounding context to extract claims from it. A new paper may arrive and
retroactively change what an older claim was arguing.

What the cycle prevents is the two failure modes at opposite ends: notes that are captured but never synthesized (the vault grows but never compounds), and claims that are synthesized but never written from (the knowledge accumulates but never produces output). The cycle's shape names these as distinct failure modes because they look identical from the outside — both appear as an active vault — but indicate different structural problems.

## Why the vault compounds rather than accumulates

The distinction between a vault that compounds and one that merely accumulates
is in the density of the claim layer. A vault with 500 catalog entities and 10
claims is a sophisticated reading list — useful for finding sources but not for
writing from. A vault with 50 checked source works and 40 claims that link to
each other and to hubs is a structure the PI can write from directly, navigating
the graph of connected ideas rather than remembering what they read.

A new source's value is not the text it contains but what it contributes to existing claims — the connections it makes explicit, the contradictions it names, the open questions it opens or closes. Compounding-through-connection is the **Zettelkasten** wager — that a densely linked note collection becomes a thinking partner rather than a filing cabinet. The claim density that separates a compounding vault from an accumulating one is the same density Luhmann's slip-box depended on (see [Intellectual foundations](../../design/intellectual-foundations.md#luhmanns-zettelkasten)).

## Where the cycle gets stuck

The Inbox and space dashboards surface exactly where work has stopped. Sources awaiting reading and distillation surface in the Library reading pipeline. Unconnected claims surface in Knowledge's Open questions view; low-stakes structural debt surfaces in Maintenance's Loose ends view. Open verification findings surface as Inbox `flag`/`alert` attention items in Maintenance. The correspondence between stuck points and views is not accidental — they were designed to make the cycle's failure modes visible before they compound.

The one transition the dashboards cannot surface is when developed claims are
never assembled into a draft - that gap is a judgment call, not a structural
signal. It is also the hardest gap to notice, because a vault full of
well-developed claims looks healthy even when nothing is being written. Today
mapping operations surface coverage, clusters, graph/canvas views, and gap
attention; writability/readiness scoring is deferred future work.

## Why archiving preserves the cycle's integrity

Notes that are no longer useful do not become invisible by deletion — they
become gaps in the provenance graph. A deleted source work breaks every claim
that cited it; a deleted claim leaves later notes without their grounding.

Archiving preserves the chain, and since the archive marker is frontmatter rather
than a folder move ([ADR-119](../../adr/119-schema-driven-document-creation.md)),
it costs nothing structurally: the note stays in its type-home, remains readable
and in Git history, drops out of active views and the agents' working scope, and
can still be traced from any note that linked to it. No file moves, so no links
break. The cycle's integrity depends on every step being traceable backward, not
just forward. Archiving itself is propose-only for every actor but the PI.

## Related

**Explanation**

- The ritual that keeps the cycle from stalling: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The daily practice surface: [Knowledge how-to guides](../../how-to-guides/knowledge/README.md)
- The epistemic roles of document types: [Document types and epistemic roles](document-types.md)
- Why promotion is gated: [Why promotion is gated](promotion-and-gated-zones.md)
- The folder structure the cycle flows through: [The vault](../architecture/vault.md)

**How-to**

- The weekly maintenance pass: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The cycle's key linking step: [Link checked notes](../../how-to-guides/knowledge/link-related-claims.md)
