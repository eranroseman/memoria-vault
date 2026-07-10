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
   consequences.** Origin is provenance, not authorization. The central
   operation this axiom serves: when the PI decides a claim is wrong, the
   system's job is to propagate the grounding consequences across the
   entire knowledge graph — and that blast radius is the same whoever
   authored the claim. (Rollback/quarantine of machine derivations is a
   cleanup utility, not the epistemic core.)

**The graph basis:** the Toulmin model's six components — Claim, Grounds,
Warrant, Backing, Qualifier, Rebuttal — are the basis of the project's
knowledge graph. The roles are what make consequence propagation typed:
losing grounds, losing a warrant, a qualifier bounding regression, and a
rebuttal strengthening when its target falls are different graph events.

Consequences for the roadmap: (a) the shipped 3-relation link graph
(supports/contradicts/extends, with warrant/backing excluded by
LINK_RELATIONS and qualifier/certainty unread) can propagate only support
counts — closing the gap to the six-role basis is the core substrate work,
the largest design-to-implementation gap in the product; (b)
structural_impact (impact-by-lost-reachability, articulation points,
fragility — built, orphaned, awaiting fields nothing writes) is the
"decided wrong → blast radius" engine and should be wired first; today
only source-level falls propagate (retraction sweep, fama-exposure); (c)
the co-PI's conversational half is grounding interrogation ("what grounds
this? where does this quote anchor? is this warrant stated?"), never truth
adjudication.
