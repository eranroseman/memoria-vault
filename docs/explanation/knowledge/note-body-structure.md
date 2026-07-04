---
title: Note body structure
parent: Knowledge
grand_parent: Explanation
nav_order: 3
---

# Note body structure

The main prose-facing knowledge types — works, notes, hubs, and projects — have
distinct body structures because they answer different questions and serve
different epistemic purposes. Understanding why each section exists helps
explain what makes a note function as knowledge rather than as accumulated text.

For the frontmatter fields, templates, and field-by-field reference, see [Document types](../../reference/document-types.md).

---

## Why source work is split between machine and human

A source's record has two authorship layers, and the split between them is intentional, not a convenience.

The mechanical layer is the catalog source row: capture populates bibliographic
facts, identifiers, hashes, source text paths, and source-derived aspects. These
are derivable from the source metadata and existing corpus without PI judgment.

The knowledge layer is checked `work`, `note`, `hub`, and `project` Concepts
under `knowledge/`. Work records hold machine-owned source summaries; notes,
hubs, and project curation carry PI judgment. A useful note captures the thesis,
the key findings that will actually be cited, and the source's relevance to the
research direction.

The Critique section is where source work earns its place in a knowledge system
rather than a bibliography. A source summary without critical engagement — what
is missing, what is methodologically weak, what you would push back on — is
storage, not synthesis. The Open questions section completes the loop by
recording what the source raises but doesn't answer, feeding the synthesis
agenda.

---

## Why claim-bearing notes have a required Links section

The three required sections of a claim-bearing note correspond to three
epistemic commitments.

The `## Claim` section states the single durable idea. Atomicity is the constraint here — one claim per note, not one topic. The discipline matters because wikilinks citing a multi-claim note become ambiguous: does the link support claim A or claim B? And when evidence changes, which part of the note gets superseded?

The `## Evidence and argument` section is what distinguishes a claim from an assertion. A claim with no evidence is an opinion. A claim with citekeys pointing to supporting sources is an argument that can be verified, updated, and superseded as evidence accumulates.

The `## Links` section is the most structurally significant. A claim with no `links:` to other claims has not made it into the knowledge graph — it exists in isolation, where it cannot compound. The `links:` here are *authored* connections (as distinct from the *given* `relationships` on entities — that distinction is explained in [Document types and epistemic roles](document-types.md)), and they are what make the vault a graph rather than a collection. A note that supports, contradicts, or extends another note has been integrated; one without links has not.

This is the **Zettelkasten** principle at the center of the method: a note's value comes from its links, not its contents — an unlinked note is, in Luhmann's terms, lost to the box. The required Links section makes that discipline structural rather than aspirational (see [Intellectual foundations](../../design/intellectual-foundations.md#luhmanns-zettelkasten)).

---

## Why hubs answer three distinct questions

A hub is not an index. The failure mode of a hub-as-index is that it becomes a flat list no one opens because a Base or Dataview query already does it faster. What a hub adds over a query is perspective: a framing of what a cluster is about, a curation of what matters most in it, and a diagnosis of where the cluster needs work.

The three questions a hub body should answer — what is this area about, what belongs here right now, and what needs review or synthesis — correspond to three distinct cognitive operations: framing, curating, and planning. A hub that only does the first two (framing and curating) is a static artifact. One that also does the third (diagnosing open questions and thin branches) is a living planning tool.

---

## Related

- The three epistemic roles explained: [Document types and epistemic roles](document-types.md)
- Why the Links section compounds: [The knowledge cycle](knowledge-cycle.md)
- What goes wrong without this structure: [Common pitfalls](common-pitfalls.md)
- How to use the reading workflow: [Discuss a paper](../../how-to-guides/library/discuss-a-paper.md)
- Document-type reference (templates, fields, lifecycle tables): [Document types](../../reference/document-types.md)
