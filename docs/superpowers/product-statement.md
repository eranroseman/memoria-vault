> **Superseded (2026-07-11).** This working record's canonical doctrine now lives
> in the published foundations pages — [What Memoria is](../explanation/rationale/foundations/what-memoria-is.md),
> [Intellectual foundations](../explanation/rationale/foundations/intellectual-foundations.md),
> and [Design principles](../explanation/rationale/foundations/design-principles.md).
> Kept as the dated 2026-07-09 composition. The one open item, warrant ontology,
> is tracked in [issue #1353](https://github.com/eranroseman/memoria-vault/issues/1353).

# Memoria — product statement (canonical, v2 — composed 2026-07-09)

Authored by Eran; composed from the day's ratified understandings
(v1's accretion history is in git). This is the authoritative "what
Memoria is." Migration destination: a docs/ explanation page. Companions:
`okf-note.md` (storage constitution), `roadmap.md` (the change program),
`user-workflow.md` (the lived experience).

---

Memoria is an opinionated, phase-gated, personal knowledge-production tool
for thinking and writing — a durable research vault that compounds over
months and years.

The unifying idea: **all trust is placed in inspectable grounding
structure, never in any author — human or machine.** That is what frees
machines to do every non-judgment task, and what reserves judgment, by
construction, to the one human.

**Personal** — thinking is private and separate from communication; notes
stay unfiltered, preserving raw reasoning before audience-aware editing
sanitizes it. The design assumes one human who owns judgment: review
decisions, synthesis choices, and scope priorities all belong to that
researcher. This is not a team tool. Thinking itself is ungated; the
knowledge graph is gated; promotion is the boundary between them — so
"unfiltered" and "gated" never apply to the same act. The zones are
**states, not places**: promotion is a record update, never a file move —
a note is born in its type home and dies there, so state changes cannot
break links or sever history.

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

## The bundle and the three spaces

The vault — excluding `.memoria/` — is **one self-contained Knowledge
Bundle** in the Open Knowledge Format's sense: the unit of distribution,
holding all the researcher's knowledge and thoughts, readable by anything
(`cat` works) with no Memoria present. Memoria is an opinionated OKF
producer profile; `.memoria/` is engine-space — verdicts, provenance,
queues, blobs: trust state *about* the knowledge, never the knowledge
itself. `bibliography.bib` is the catalog's bundle-resident projection,
each entry carrying `memoria_work_id` as the join key back to
engine-space. Full texts are external material and live in engine-space;
the bundle carries the researcher's *engagement* with them — digests,
claims, links — plus the pointers that resolve anywhere.

Day-to-day, work happens in three spaces — regions of the one bundle, not
separate containers: sources enter the **catalog**, become connected
claims in the **knowledge** region, and drive an inquiry to output in a
**Project**. Each project is its own **nested, detachable bundle** per the
Zettelkasten project-notes concept: projects reference vault knowledge
freely, permanent knowledge never links into `projects/`, and project
close harvests durable claims into the vault before the working bundle
archives. The vault must live without its projects' bundles.

## Four pillars

Memoria stands on four pillars, each owning one layer with no overlap:

- **LLM-Wiki** (Karpathy) owns the **inflow** — every source is extracted
  (raw kept), digested, and indexed; the lint concept is expanded to all
  housekeeping and bookkeeping.
- **Zettelkasten** (Luhmann) owns the **topology** — atomic notes, typed
  links, hubs (the bibliography box augmented into the catalog knowledge
  graph), and disposable project bundles.
- **Toulmin** owns the **logic** — the six components (Claim, Grounds,
  Warrant, Backing, Qualifier, Rebuttal) are the basis of the knowledge
  graph, the gates' criteria, and the co-PI's question taxonomy.
- **autoresearch** (Karpathy) owns the **self-improvement** — fixed
  harness, one metric, keep/discard, overnight; applied to Memoria's own
  instruments, never to the knowledge they assess.

Knowledge gets its shape from ZK, its supply from LLM-Wiki, its meaning
from Toulmin, its sharpening from autoresearch. ZK and LLM-Wiki align in
places: they share the index, and some digest products are ZK notes.

## The co-PI

The end result should feel like a co-PI, not a knowledge base. The co-PI's
expertise is **method, never belief**: it interrogates grounding, sets
agendas, and surfaces contradictions, but by the axioms below it can never
tell the researcher what to believe. The engine owns LLM calls as **fenced
one-shot operations** — sealed inputs, manifest fencing, prompt and model
provenance, validated outputs; what it deliberately does not own is an
**agent loop** (multi-turn, tool-using, initiating). The conversation loop
belongs to the researcher's agent of choice, speaking from engine-authored
method.

## Design axioms

**The kernel:** we never read a claim and ask whether we think it is true.
We read a claim and ask how it is grounded in the evidence.
Truth-assessment is replaced by grounding-assessment — and grounding is a
property of the artifact, inspectable and author-independent, which is why
axiom 2 follows from axiom 1.

1. **No single node is judged true or false.** The system only asserts how
   a change affects knowledge-graph integrity. "Checked" means integrity
   checks passed, never a truth verdict; dispositions record judgment
   events, they do not adjudicate content.
2. **The origin of a change — human, machine, LLM — does not affect its
   consequences.** Origin is provenance, not authorization. Scope
   (formalized after reconciling with the decision record): the axiom
   governs **epistemic consequences** — flags, demotions, gap findings,
   blast radius are origin-blind; write and revert **authority** remains
   origin-gated (human-authored spans are never auto-destroyed; machine
   material auto-reverts). The central operation this axiom serves: when
   the researcher decides a claim is wrong, the system propagates the
   grounding consequences across the entire knowledge graph — and that
   blast radius is the same whoever authored the claim. Propagation is
   lazy and impact-ranked (stale-marking, on-path re-confirmation) —
   eager re-confirmation of every downstream edge is the sunk-cost trap
   inverted.

**The past is a teacher, not a prison.** History is preserved completely
and binds nothing: the journal is append-only forever, superseded claims
archive in place, design-history freezes how the system got here — and
none of it is authority. Verdicts speak only for the present; reopening
anything is always allowed, as a decision. This governs the vault's
treatment of the researcher's own record and the project's treatment of
its own design history alike.

**The master pattern** (it resolved every design fork it was tested on):
*the fluent, judging half of any capability stays with the human — or the
human's chosen agent; the structural, inspectable half goes into the
engine.* Truth/grounding, judgment/method, brain/protocol,
agent-loop/fenced-operation, knowledge/trust-state, bundle/engine are all
this one cut. A fork that resists resolution has usually not been cut
along this line yet.

## The graph basis

The Toulmin six are the knowledge graph's basis because the roles make
consequence propagation **typed**: losing grounds, losing a warrant, a
qualifier bounding regression, and a rebuttal strengthening when its
target falls are different graph events. The argument graph is authored in
note frontmatter (files-first), indexed for traversal, and connected to
the catalog graph through the work-identity namespace.

## Open design question — warrant ontology (decide before extending the graph)

When a warrant becomes explicit, is it a link property or a node? Warrants
are general inference licenses that recur across arguments and normally
stay implicit until challenged. Edge-properties are simple but make the
central operation unimplementable for warrants (no node to dispose, no
backing target, invisible to lint) and evaporate at bundle export.
Warrant-as-node makes one disposition propagate to every argument it
licenses, gives backing and rebuttal their true targets, and — over
years — turns the warrant inventory into the researcher's explicit,
versioned methodology; its cost is reifying a three-way relation and
authoring friction. **Standing recommendation — hybrid:** warrants are
nodes when explicit, absent when implicit, and *demandable on challenge*;
the under-warranted pressure and gates promote implicit → explicit at the
points that matter, and lint proposes shared nodes when the same inference
recurs — machine proposes, researcher disposes. Four independent weights
now favor nodes (typed propagation, methodology inventory, OKF
exportability, frontmatter evolvability); the choice sets whether the
graph is about claims with annotated justifications or equally about
inferences as research objects, and migrating after years of accumulation
is expensive. The decision is evidence-gated: the empirical-use plan's
warrant touch-budget observation (one real project loop) carries the
pre-registered decision rule.
