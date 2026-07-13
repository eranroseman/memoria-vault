---
title: The knowledge cycle
parent: Knowledge
grand_parent: Explanation
nav_order: 2
---

# The knowledge cycle

Every note in the vault sits somewhere between catalogued source and written
output. The cycle explains what that progression is for, where it stalls, and
why the vault compounds instead of merely accumulating files.

## Pull, not push

> **Planned beta.1 — O2/W2:** Project-pulled admission and the complete
> project-close harvest loop described below are target-state.

The cycle is inquiry-first: a project opens with a question or thesis, gap
analysis runs over what the vault already holds *before* new reading, and
capture is pulled by identified gaps rather than pushed by whatever arrives.
Sources are admitted to the catalog freely, but nothing enters knowledge
until a project pulls it through digestion and judgment. At project close,
durable claims harvest back into the vault — each project leaves the
permanent knowledge richer than it found it.

## Delegable tasks are not a pipeline

The PI works in **Library**, **Knowledge**, and **Project**, with **Inbox** as
the queue. Beneath those surfaces, operations capture, enrich, extract, link,
map, digest, and verify; the concrete roster lives in
[Operations](../../reference/commands-and-transports/operations.md).

These tasks are **individually triggered, not a set**. A human gate — often a
long gap — sits between each: a source is catalogued; much later, if ever,
extracted; only after a claim-bearing note exists does linking fire.

A source arrives as an unchecked SQLite catalog row with its source text in the
blob store. Enrichment records provider evidence; passing rows become checked,
while failed or contested rows raise Inbox attention. The PI then reads checked
Works, distills claims, and confirms links into the graph. Once enough claims
accumulate, a project maps them into
`outline.md`, composes `draft.md`, verifies evidence markers, exports clean
drafts, and promotes selected passages back into unchecked notes for review.

**The loop compounds** because mapping and verification expose gaps. Those gaps
raise Inbox attention, which can trigger new capture work. What you write shows
what is missing; what you catalog next is shaped by what you tried to write.

## Why the cycle is not a linear path

The cycle describes direction, not a required timeline. A note can remain
underdeveloped for months. A checked source can sit for a year before there is
enough context to extract claim-bearing notes from it. A new paper can also
change what an older claim means.

The cycle distinguishes two failures that look alike from the outside: capture
without synthesis, and synthesis without output. Both look like an active vault.
Only the first means the vault is not compounding; the second means the
knowledge is not reaching drafts.

## Why the vault compounds rather than accumulates

Claim density separates a compounding vault from an accumulating one. A vault
with 500 catalog entities and 10 claim-bearing notes is a reading list. A vault
with 50 checked source works and 40 linked claims is a writing structure: the PI
navigates connected ideas instead of remembering what they read.

A source's value is what it contributes to existing claims: connections,
contradictions, and open questions. This is the **Zettelkasten** wager: a dense
claim graph becomes a thinking partner instead of a filing cabinet. Luhmann's
slip-box depended on the same density (see [Intellectual foundations](../rationale/foundations/intellectual-foundations.md#luhmanns-zettelkasten)).

## Where the cycle gets stuck

The shipped CLI and read API show where work stopped. Sources awaiting work are
visible through `memoria list --type work`, `memoria work export`, request
state, and file-backed Inbox attention; no separate named pipeline ships.
Unconnected claims remain visible in the checked note graph, and open
verification findings appear as Inbox `flag`/`alert` attention items. These
surfaces expose stalled work before it hardens.

The project transition is now explicit: `memoria project slice` proposes a
checked outline, `compose` writes a draft, `verify` gates the evidence markers,
and `promote` turns selected passages into unchecked notes. Broad writability
scoring remains out of scope; the shipped signal is concrete file state and
verification findings, not a synthetic score.

## Project slices

A project slice is the bridge between checked knowledge and draft prose. It
names the notes the draft may use, and it puts them in the order the PI wants
the draft to follow.

The slice matters because project writing should not pull from the whole vault
opportunistically. Search can propose relevant notes, but the PI chooses which
checked notes belong in the argument. That choice keeps the draft traceable:
when the prose is wrong, review starts from a small, explicit evidence set
instead of an opaque chat transcript.

The slice is narrower than an argument map. It records membership and sequence;
it does not restate every relationship among the notes. Memoria can recompute
in-slice links from checked notes, so the project outline stays editable by a
human while the graph remains grounded in authored note links.

## Exploration channel

The exploration channel is separate from relevance-ranked search because the PI
needs two different questions answered. Search asks, "what checked material
already matches this question?" Exploration asks, "what should I inspect next
because the graph suggests a gap, contrary item, or nearby candidate?"

That distinction keeps exploration from polluting answers. A ranked answer stays
grounded in checked material; exploration may point outside the current argument
so the PI can decide whether the candidate belongs.

Every surfaced item carries a `why` string so the PI can decide whether it is
worth action. The command contract belongs in [CLI](../../reference/commands-and-transports/cli.md) and
[Operations](../../reference/commands-and-transports/operations.md).

## Why archiving preserves the cycle's integrity

Notes that are no longer useful do not become invisible by deletion — they
become gaps in the provenance graph. A deleted source work breaks every claim
that cited it; a deleted claim leaves later notes without their grounding.

Archiving preserves the chain, and since the archive marker is frontmatter rather
than a folder move, it costs nothing structurally: the note stays in its
type-home, remains readable and in Git history, drops out of active views and the
agents' working scope, and can still be traced from any note that linked to it.
No file moves, so no links break. The cycle's integrity depends on every step
being traceable backward, not just forward. Archiving itself is propose-only for
every actor but the PI.

## Related

**Explanation**

- The ritual that keeps the cycle from stalling: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The daily practice surface: [Knowledge how-to guides](../../how-to-guides/knowledge/README.md)
- The epistemic roles of document types: [Document types and epistemic roles](document-types.md)
- Why promotion is gated: [Why promotion is gated](promotion-and-gated-zones.md)
- The folder structure the cycle flows through: [The vault](../architecture/vault.md)
- The project drafting task flow: [Compose a draft](../../how-to-guides/project/compose-a-draft.md)
- The read contract behind project slices: [Engine read API](../../reference/commands-and-transports/read-api.md)

**How-to**

- The weekly maintenance pass: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The cycle's key linking step: [Link checked notes](../../how-to-guides/knowledge/link-checked-notes.md)
