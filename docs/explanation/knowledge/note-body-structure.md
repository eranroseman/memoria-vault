---
title: Note body structure
parent: Knowledge
---

# Note body structure

The three most important note types — paper-notes, claim-notes, and MOCs — have distinct body structures because they answer different questions and serve different epistemic purposes. Understanding why each section exists helps explain what makes a note function as knowledge rather than as accumulated text.

For the frontmatter fields, templates, and field-by-field reference, see [reference/note-types.md](../../reference/note-types.md).

---

## Why paper-notes are split between Librarian and human

A paper-note has two authorship layers, and the split between them is intentional, not a convenience.

The Librarian populates the bibliographic and relational sections at ingest: citation connections (`## Cites (in vault)`, `## Cited by (in vault)`) and discovery candidates. These are derivable from the paper's metadata and the existing corpus without reading comprehension — they are structural facts about the source's relationship to the graph. The Librarian produces them deterministically and cheaply.

The human fills the interpretive sections: the Summary, the Critique, and the Open questions. These require reading comprehension and judgment. The Summary in particular is load-bearing — it is what the human will read six months later when they need to cite the paper without re-reading it. A Summary that merely paraphrases the abstract has failed this purpose; it needs to capture the thesis, the key findings that will actually be cited, and the paper's relevance to the specific research direction.

The Critique section is where a paper-note earns its place in a knowledge system rather than a bibliography. A paper note without critical engagement — what is missing, what is methodologically weak, what you would push back on — is storage, not synthesis. The Open questions section completes the loop by recording what the paper raises but doesn't answer, feeding the synthesis agenda.

---

## Why claim-notes have a required Connections section

The three required sections of a claim-note correspond to three epistemic commitments.

The `## Claim` section states the single durable idea. Atomicity is the constraint here — one claim per note, not one topic. The discipline matters because wikilinks citing a multi-claim note become ambiguous: does the link support claim A or claim B? And when evidence changes, which part of the note gets superseded?

The `## Evidence and argument` section is what distinguishes a claim from an assertion. A claim note with no evidence is an opinion. A claim note with citekeys pointing to supporting sources is an argument that can be verified, updated, and superseded as evidence accumulates.

The `## Connections` section is the most structurally significant. A claim note with no connections to other claim notes has not made it into the knowledge graph — it exists in isolation, where it cannot compound. Connections are what make the vault a graph rather than a collection. A note that supports, contradicts, or extends another note has been integrated; one without connections has not.

This is the **Zettelkasten** principle at the center of the method: a note's value comes from its links, not its contents — an unlinked note is, in Luhmann's terms, lost to the box. The required Connections section makes that discipline structural rather than aspirational (see [intellectual-foundations.md](../intellectual-foundations.md#luhmanns-zettelkasten)).

---

## Why MOCs answer three distinct questions

A MOC is not an index. The failure mode of a MOC-as-index is that it becomes a flat list no one opens because the Dataview query already does it faster. What a MOC adds over a Dataview query is perspective: a framing of what a cluster is about, a curation of what matters most in it, and a diagnosis of where the cluster needs work.

The three questions a MOC body should answer — what is this area about, what belongs here right now, and what needs review or synthesis — correspond to three distinct cognitive operations: framing, curating, and planning. A MOC that only does the first two (framing and curating) is a static artifact. One that also does the third (diagnosing open questions and thin branches) is a living planning tool.

---

## The epistemic separation between note types

The note types enforce a separation that is easy to violate under time pressure:

A `paper-note` records what a source says, from an external perspective. A `claim-note` records what the human thinks, in their own words. A `moc` is a navigational and planning hub, not a synthesis destination.

Mixing these produces notes that serve neither purpose well. A paper-note that contains the human's claims makes citation tracing ambiguous — did the citekey in a draft point to what the paper says, or to what the human concluded? A claim-note that summarizes a paper rather than asserting the human's own position is not a claim note; it is a misplaced source note.

The separation is what allows agent permissions to be cleanly scoped: the Librarian can write paper-notes because recording what a source says is mechanical. It cannot write claim-notes because asserting the human's synthesis is not.

---

## Related

- The three epistemic roles explained: [note-types.md](note-types.md)
- Why the Connections section compounds: [knowledge-cycle.md](knowledge-cycle.md)
- What goes wrong without this structure: [common-pitfalls.md](common-pitfalls.md)
- How to use the paper-note workflow: [how-to-guides/sources/discuss-a-paper.md](../../how-to-guides/sources/discuss-a-paper.md)
- Note-type reference (templates, fields, lifecycle tables): [reference/note-types.md](../../reference/note-types.md)
