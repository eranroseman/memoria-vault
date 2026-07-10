# Memoria — product statement (canonical, 2026-07-09)

Authored by Eran in the superpowers-alignment review. This is the
authoritative "what Memoria is" statement. Migration destination: a docs/
explanation page (step 9 routes it to `docs/`, not `docs/superpowers/`);
the facts AGENTS.md carries the distilled version (plan step 7).

---

Memoria is an opinionated, phase-gated, personal knowledge-production tool
for thinking and writing — a durable research vault that compounds over
months and years.

**Personal** — thinking is private and separate from communication; notes
stay unfiltered, preserving raw reasoning before audience-aware editing
sanitizes it. The design assumes one human who owns judgment: review
decisions, synthesis choices, and scope priorities all belong to that
researcher. This is not a team tool.

**Opinionated** — it enforces specific workflows and eliminates setup
paralysis. The vault structure, the document types, and the review gates
are not configurable surfaces to tune; they are the design.

**Phase-gated** — work passes through defined phases with explicit
outputs. A source doesn't become synthesis until it has been captured,
enriched, read, and compiled; a draft doesn't become a deliverable until
it has been verified and accepted.

It is knowledge production, not just storage: the vault grows more useful
over time as new sources connect to existing claims, synthesis sharpens as
evidence accumulates, and structural maintenance keeps the graph coherent.
That is the difference between a research vault and a notes pile.

Day-to-day, that work happens in three spaces: you bring sources into the
catalog, build them into connected claims in a Knowledge Bundle, and drive
an inquiry to output in a Project.

## Lineage

Memoria builds on Karpathy's LLM-Wiki pattern and Luhmann's Zettelkasten,
and expands them with agentic AI capabilities:

- The ZK bibliography box is augmented into the catalog knowledge graph.
- Every new source follows the LLM-Wiki pattern: extracted (raw sources),
  digested, and indexed.
- ZK and LLM-Wiki align in a few places: they share the index, and some
  digest products are ZK notes.
- The ZK project-notes concept becomes the nested Knowledge Bundle.
- The Toulmin Model is overlaid on claim notes to create an argument
  knowledge graph, connected to and parallel with the catalog knowledge
  graph.
- The LLM-Wiki lint concept is expanded to cover all housekeeping and
  bookkeeping aspects of the system.

The end result should feel like a co-PI, not a knowledge base.

## Design axioms (added 2026-07-09, same review)

**The kernel:** we never read a claim and ask whether we think it is true.
We read a claim and ask how it is grounded in the evidence. Truth-assessment
is replaced by grounding-assessment — and grounding is a property of the
artifact, inspectable and author-independent, which is why axiom 2 follows
from axiom 1.

1. **No single node is judged true or false.** The system only asserts how
   a change affects knowledge-graph integrity. "Checked" means integrity
   checks passed, never a truth verdict; dispositions record judgment
   events, they do not adjudicate content.
2. **The origin of a change — human, machine, LLM — does not affect its
   consequences.** Origin is provenance, not authorization; the same edit
   produces the same integrity effects whoever made it. Apparent
   origin-asymmetries (cascade rollback quarantines machine-derived content,
   routes PI-authored content to "ask") track derivation-chain topology,
   not authorship: journal-derived content's grounding breaks mechanically
   when its source is poisoned; authored content merely cites, so "ask" is
   the only honest verdict.

Consequences for the roadmap: the co-PI's conversational half is grounding
interrogation ("what grounds this? where does this quote anchor? what
contradicts it?"), never truth adjudication; and the deferred warrant field
is the most axiom-central unbuilt piece — the warrant is the grounding
relation made explicit, and without it grounding is assessed only by edge
existence and lexical overlap, never by stated justification.
