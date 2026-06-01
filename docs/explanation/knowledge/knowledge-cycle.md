# The knowledge cycle

Every note in the vault is somewhere in a long-term progression from ingested source to written output. Understanding the cycle as a whole — what it is for, where it gets stuck, and what makes it compound — is the conceptual foundation for understanding why the vault is structured the way it is.

## The progression

The cycle moves through seven broad stages: ingest, classify, synthesize, develop, promote, write, export. A new source arrives as a candidate, becomes a paper-note after the Librarian processes it, gets classified by the human, generates claim notes through Socratic discussion and synthesis, those claims mature and cross-link into the existing graph, stable claims get promoted to reference notes, and eventually assembled into a deliverable.

This cycle runs in parallel across many sources simultaneously. A healthy vault at any given time has paper-notes in active classification, claim notes in early stages of development, a growing MOC for a cluster, and an active draft being assembled. The stages coexist; the cycle is not one pipeline but many running concurrently.

## Why the cycle is not a linear path

The cycle describes the intended direction of flow, not a timeline or a required sequence. A claim note can remain at `maturity: seedling` for months — that is normal, not broken. A paper note can sit classified for a year before there is enough surrounding context to synthesize claim notes from it. A new paper may arrive and retroactively change what an older claim note was arguing.

What the cycle prevents is the two common failure modes at opposite ends: notes that are captured but never synthesized (the vault grows but never compounds), and claims that are synthesized but never written from (the knowledge accumulates but never produces output). The cycle's shape names these as distinct failure modes because they look identical from the outside — both appear as an active vault — but indicate different structural problems.

## Why the vault compounds rather than accumulates

The distinction between a vault that compounds and one that merely accumulates is in the density of the claim-note layer. A vault with 500 paper-notes and 10 claim notes is a sophisticated reading list — useful for finding sources but not for writing from. A vault with 50 paper-notes and 40 claim notes that link to each other and to MOCs is a structure the human can write from directly, navigating the graph of connected ideas rather than remembering what they read.

This is Karpathy's compiler insight applied to personal research: the vault's value is not in its size but in its integration. A new source's value is not the text it contains but what it contributes to existing claims — the connections it makes explicit, the contradictions it names, the open questions it opens or closes.

Compounding-through-connection is the **Zettelkasten** wager — that a densely linked note collection becomes a thinking partner rather than a filing cabinet. The claim-note density that separates a compounding vault from an accumulating one is the same density Luhmann's slip-box depended on (see [intellectual-foundations.md](../intellectual-foundations.md#luhmanns-zettelkasten)).

## Where the cycle gets stuck

The dashboards exist to surface exactly where in the cycle work has stopped. Classification backlog surfaces in `reading-pipeline.md`. Orphan claim notes with no connections surface in `open-questions.md` and `loose-ends.md`. Verification gaps surface in `board-state.md`. The correspondence between stuck points and dashboard views is not accidental — the dashboards were designed to make the cycle's failure modes visible before they compound.

The one transition the dashboards cannot surface is when developed claims are never assembled into a draft — that gap is a judgment call, not a structural signal. This is also the hardest gap to notice because a vault full of well-developed claim notes looks healthy even when nothing is being written.

## Why archiving preserves the cycle's integrity

Notes that are no longer useful do not become invisible by deletion — they become gaps in the provenance graph. A deleted source note breaks every claim note that cited it. A deleted claim note leaves claims in later notes without their grounding.

Archiving preserves the chain: the note moves to `95-archive/`, remains readable and in Git history, disappears from active Dataview queries and from the agent's search scope, but can still be traced from any note that linked to it. The cycle's integrity depends on every step being traceable backward, not just forward.

For the archive procedure, see [how-to-guides/maintenance/run-the-weekly-review.md](../../how-to-guides/maintenance/run-the-weekly-review.md).

## Related

- Why the cycle needs weekly attention: [../dashboards/weekly-review.md](../dashboards/weekly-review.md)
- The epistemic roles of note types: [note-types.md](note-types.md)
- Why promotion is gated: [promotion-model.md](promotion-model.md)
- The folder structure the cycle flows through: [vault.md](../architecture/vault.md)
- The ritual that keeps the cycle from stalling: [run-the-weekly-review.md](../../how-to-guides/maintenance/run-the-weekly-review.md)
- The cycle's key transition: [write-a-claim-note.md](../../how-to-guides/sources/write-a-claim-note.md)
