---
title: Note body structure
parent: Knowledge
nav_order: 3
---

# Note body structure

The three most important prose types — source notes, claim notes, and hubs — have distinct body structures because they answer different questions and serve different epistemic purposes. Understanding why each section exists helps explain what makes a note function as knowledge rather than as accumulated text.

For the frontmatter fields, templates, and field-by-field reference, see [Note types](../../reference/note-types.md).

---

## Why source notes are split between machine and human

A source's record has two authorship layers, and the split between them is intentional, not a convenience.

The mechanical layer is the **paper entity** in `catalog/`: the ingest engine populates the bibliographic facts and the `relationships` (cites, cited-by, authored-by, published-in) at intake. These are derivable from the source's metadata and the existing corpus without reading comprehension — structural facts about the source's place in the graph, produced deterministically and cheaply. The Librarian adds the two LLM pieces — a comparative brief and a draft classification — as proposals.

The human layer is the **source note** in `notes/sources/`: the Summary, the Critique, and the Open questions. These require reading comprehension and judgment. The Summary in particular is load-bearing — it is what the PI reads six months later to cite the paper without re-reading it. A Summary that merely paraphrases the abstract has failed this purpose; it needs to capture the thesis, the key findings that will actually be cited, and the paper's relevance to the specific research direction.

The Critique section is where a source note earns its place in a knowledge system rather than a bibliography. A source note without critical engagement — what is missing, what is methodologically weak, what you would push back on — is storage, not synthesis. The Open questions section completes the loop by recording what the source raises but doesn't answer, feeding the synthesis agenda.

---

## Why claim notes have a required Links section

The three required sections of a claim note correspond to three epistemic commitments.

The `## Claim` section states the single durable idea. Atomicity is the constraint here — one claim per note, not one topic. The discipline matters because wikilinks citing a multi-claim note become ambiguous: does the link support claim A or claim B? And when evidence changes, which part of the note gets superseded?

The `## Evidence and argument` section is what distinguishes a claim from an assertion. A claim with no evidence is an opinion. A claim with citekeys pointing to supporting sources is an argument that can be verified, updated, and superseded as evidence accumulates.

The `## Links` section is the most structurally significant. A claim with no `links:` to other claims has not made it into the knowledge graph — it exists in isolation, where it cannot compound. The `links:` here are *authored* connections (as distinct from the *given* `relationships` on entities — that distinction is explained in [Note types and epistemic roles](note-types.md)), and they are what make the vault a graph rather than a collection. A note that supports, contradicts, or extends another note has been integrated; one without links has not.

This is the **Zettelkasten** principle at the center of the method: a note's value comes from its links, not its contents — an unlinked note is, in Luhmann's terms, lost to the box. The required Links section makes that discipline structural rather than aspirational (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

---

## Why hubs answer three distinct questions

A hub is not an index. The failure mode of a hub-as-index is that it becomes a flat list no one opens because a Base or Dataview query already does it faster. What a hub adds over a query is perspective: a framing of what a cluster is about, a curation of what matters most in it, and a diagnosis of where the cluster needs work.

The three questions a hub body should answer — what is this area about, what belongs here right now, and what needs review or synthesis — correspond to three distinct cognitive operations: framing, curating, and planning. A hub that only does the first two (framing and curating) is a static artifact. One that also does the third (diagnosing open questions and thin branches) is a living planning tool.

---

## The epistemic separation between note types

The note types enforce a separation that is easy to violate under time pressure:

A source note records what a source says, from an external perspective. A claim note records what the PI thinks, in their own words. A hub is a navigational and planning surface, not a synthesis destination.

Mixing these produces notes that serve neither purpose well. A source note that contains the PI's claims makes citation tracing ambiguous — did the citekey in a draft point to what the source says, or to what the PI concluded? A claim that summarizes a paper rather than asserting the PI's own position is not a claim; it is a misplaced source note.

The separation is what allows agent permissions to be cleanly scoped — recording what a source says is delegable bookkeeping, while asserting the PI's synthesis is not, which is why `notes/claims/` and `notes/hubs/` are gated. That bookkeeping-vs-synthesis boundary is developed in [Note types and epistemic roles](note-types.md).

---

## Related

- The three epistemic roles explained: [Note types and epistemic roles](note-types.md)
- Why the Links section compounds: [The knowledge cycle](knowledge-cycle.md)
- What goes wrong without this structure: [Common pitfalls](common-pitfalls.md)
- How to use the reading workflow: [Discuss a paper](../../how-to-guides/compile/discuss-a-paper.md)
- Note-type reference (templates, fields, lifecycle tables): [Note types](../../reference/note-types.md)
