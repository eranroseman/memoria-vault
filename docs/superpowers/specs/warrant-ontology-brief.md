# Warrant ontology — decision brief

Date: 2026-07-12. Status: **brief for the scheduled brainstorm** — the first
design session after Foundation (F1–F4) lands, per the owner's recorded
schedule. Derived from `product-statement.md` §Open design question, the
blind-spots owner rulings (§A.4/A.5, folded via the consolidation), the
roadmap's item-7 terminology finding, and the empirical plan's touch-budget
row. Interim posture already ruled (2026-07-12, consolidation §6): **Option B —
roles carried by typed relations with promotion-ready edges**; this brief
frames the *remaining* decision, which is evidence-gated and deferred to
beta.2 (`0.1.0-beta.2-scope.md` §4).

## The question

When a warrant (the inference license connecting grounds to a claim) becomes
explicit, is it an **edge property** or a **first-class node**? Warrants are
general inference licenses that recur across arguments and normally stay
implicit until challenged.

## What is already decided (do not relitigate; revisable only on merit)

- **Interim graph shape:** the six Toulmin roles ride typed relations;
  `concept_edges` gains `edge_id` + attribute columns (G2) so a warrant
  reference can hang on an edge — the *promotion-ready* property that keeps
  later node reification cheap.
- **Reify-on-explicit:** a warrant becomes a node only when explicitly
  authored or shared; implicit warrants are absent, and **demandable on
  challenge** — under-warranted pressure and gates promote implicit → explicit
  at the points that matter; lint proposes shared nodes when the same
  inference recurs (machine proposes, researcher disposes).
- **No warrant-node schema work before the touch-budget observation**
  (empirical plan, What-Not-To-Build-Yet).
- **Earn-each-type:** relation vocabulary is earned one relation at a time as
  each is actually used — a half-populated typed field returns incomplete
  answers.

## The evidence gate (pre-registered — the brainstorm's decision rule)

Collect over **one full project loop**: under-warranted findings raised,
"state the warrant" demands, PI minutes per warrant made explicit.

> If explicit warrants stay under budget **and** get demanded → ratify
> hybrid-with-nodes. If never demanded → keep demandable-only and defer nodes.

## The trade frame (from the product statement)

**Edge-property costs:** makes the central operation unimplementable for
warrants (no node to dispose, no backing target, invisible to lint) and
evaporates at bundle export.

**Node benefits (four independent weights):** one disposition propagates to
every argument the warrant licenses (typed propagation); over years the
warrant inventory becomes the researcher's explicit, versioned methodology;
OKF exportability; frontmatter evolvability.

**Node costs:** reifying a three-way relation; authoring friction; migrating
after years of accumulation is expensive — which is exactly why the interim
posture keeps edges promotion-ready rather than committing early.

## Must-resolve in the same session: the terminology collision

The beta.1 design (§1.4) calls a typed evidence-set a "warrant." Under the
Toulmin pillar that is **grounds**; the warrant is the inference license.
One of the two must be renamed **before the six-role vocabulary ships**, or
the graph vocabulary launches pre-confused. (Roadmap item 7 finding; touches
the evidence-set contract wording in `0.1.0-beta.1-design.md` §1.4 and the
verification labels in V2/V3.)

## Session outputs expected

1. A ratified ontology ruling (hybrid-with-nodes vs demandable-only-longer),
   grounded in the touch-budget data — or an explicit extension of the
   observation window if the data is thin.
2. The grounds/warrant rename decision and its sweep list.
3. If nodes are ratified: the reification mechanics (node type, backing/
   rebuttal targeting, lint-proposal flow) as an alpha-scoped spec feeding
   the beta.2 register's unit 4.
