# The knowledge model

The vault stores durable knowledge organized by lifecycle stage. Understanding the knowledge model means understanding what makes knowledge *durable*, how the vault's organization serves that goal, and why certain moves are allowed and others aren't.

---

## Knowledge vs work

The most important distinction in the system is between **work** and **knowledge**:

- **Work** is transient. It lives on the board as a card, has a lifecycle that ends at `archived`, and exists only as long as the task does. A Librarian card that ingests a paper is work. It finishes and disappears from the active board.
- **Knowledge** is durable. It lives in the vault, has a lifecycle that moves toward `evergreen`, and persists indefinitely. The paper note that the Librarian created — that's knowledge.

This distinction is load-bearing because it determines *where* something lives and *who* controls its fate. The board tracks work; only the vault accumulates knowledge. An agent can write to the vault's working zones (inbox, sources, workbench); it can only *propose* in the vault's synthesis zones, and only a human can approve promotion.

---

## The vault as compiled memory

The vault is not a document store — it is **compiled memory**. The difference:

A document store holds files. Retrieval fetches files. Nothing compounds.

Compiled memory is integrated. A new source connects to existing claims through typed wikilinks. A new claim note traces back to the papers that support it. A MOC (Map of Content) surfaces the structure of a topic as knowledge accumulates. Over time, the vault grows more useful — not just larger — because each new piece is integrated with what's already there.

This is Karpathy's LLM-Wiki insight applied to personal research: the agent is a compiler, not just a retriever. The value of the vault is in its structure, not just its contents.

---

## Lifecycle stage as the organizing principle

Folders in the vault encode **lifecycle stage**, not subject area. A paper about behavioral economics lives in `20-sources/01-papers/`, not in `economics/`. A claim about loss aversion lives in `30-synthesis/01-claims/`, not in `psychology/` or `finance/`.

This sounds counterintuitive. The explanation is in [lifecycle-over-topic.md](lifecycle-over-topic.md). The short version: topics are many-to-many — a paper belongs to multiple topics and a topic spans many papers — so topic folders either duplicate notes (wrong) or become meaningless catch-alls (useless). Lifecycle stage is one-to-one: a note is at exactly one stage in its lifecycle. The stage belongs in the folder; the topics belong in frontmatter and links.

---

## The three epistemic roles

Notes in Memoria have one of three fundamental epistemic roles:

**Source notes** (`20-sources/`) describe the world. They record what something says, does, or is. A paper note records what a paper argues. An item note records what a tool does. An entity note records who a person is. Source notes are written from an external perspective.

**Synthesis notes** (`30-synthesis/`) express the human's thinking. A claim note is the human's own durable statement, grounded in sources but in the human's own words. A reference note is a stable synthesis page the human curates. A MOC is a navigational hub. Synthesis notes are written from an internal perspective — they represent the human's knowledge, not the world's.

**Working notes** (`10-inbox/`, `40-workbench/`) are in transit or in progress. They are neither source nor synthesis; they are becoming. An inbox note is a candidate for one of the two permanent zones. A workbench draft is synthesis in progress.

Understanding these roles matters because **the agent's permissions follow the roles**. Source notes can be agent-written; the Librarian creates paper notes directly. Synthesis notes are human-owned; the agent can only draft and propose, never canonize. Working notes are shared territory. See [note-types.md](note-types.md) for the full picture.

---

## The promotion map

Knowledge moves left-to-right through the folder numbers. A fleeting note might become a paper note after review; a paper note might become a claim note after discussion and synthesis. The promotion map is intentionally restrictive:

- Promotion requires human review at each stage gate.
- A source note never becomes a claim note directly — the human writes the claim in their own words, then links to the source.
- Promotion is irreversible downward; a claim-note doesn't become an inbox note again (it would be archived or superseded instead).

The restriction is not bureaucratic — it is the mechanism that maintains the epistemic integrity of the synthesis zone. See [promotion-model.md](promotion-model.md).

---

## Documents in this section

- **[lifecycle-over-topic.md](lifecycle-over-topic.md)** — why folders encode stage, not subject, and what would break if they didn't.
- **[note-types.md](note-types.md)** — the three epistemic roles of notes, and what it means for a note to have an epistemic role.
- **[promotion-model.md](promotion-model.md)** — what promotion means, why it's gated, and the rules that constrain the promotion map.

For the complete note-type reference (fields, templates, lifecycle tables), see [reference/note-types.md](../../reference/note-types.md).
