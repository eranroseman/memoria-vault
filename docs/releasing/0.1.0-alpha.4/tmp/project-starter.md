# Project Starter — the Project gate design

Status: design note (alpha.4), pre-ADR. Captures the converged design for the fourth
navigation gate — the **Project gate** deferred by ADR-70 and the empty `projects/`
workflow left by ADR-68. To be folded into an ADR; the open tuning parameter is flagged
at the end.

---

## 1. What this is

A project in Memoria is a bounded research inquiry that drives catalog/library/source
work and feeds writing. This note designs the artifacts a project holds, how they relate,
who produces them, and — critically — when a project is *done*.

The headline result of the design: **the gate's *logic* is auditable and bias-free — its
*inputs* are not.** Every load-bearing mechanism (the map, impact, triage, saturation,
termination) is a deterministic Operation — a derived view in the same trust class as the
existing knowledge-map and contradictions dashboards. Agents still discover sources (Librarian)
and draft prose (Writer), but the gate's *logic* never asks an LLM to judge. This keeps the
gate inside the architecture's deepest invariant — agents propose, the PI promotes, nothing
auto-infers (ADR-10, ADR-48, ADR-51).

**But determinism buys auditability of the computation, not correctness of the conclusion.**
Every Operation here runs over the argument graph, whose *content* is PI-authored or
agent-proposed. Structural impact computed over a sparse or mis-typed graph is precise nonsense.
The durable risk is not the empty graph (a transient cold-start problem, §8) but the **wrong**
one — a mis-typed `supports`, a missing `contradicts`. So the honest claim is narrow: the gate's
logic is bias-free and replayable; whether its output is *true* depends entirely on inputs the
gate does not and cannot verify.

### Where determinism stops: the two-tier rule

This boundary recurs in four mechanisms below (warrant gaps §6, saturation condition 3 §5,
PICO/FINER §7, source appraisal §11), and it is the same rule each time. A structural Operation
can check that a thing is **present / articulated** — that is tier 2, auditable, cheap, and
**gameable** (fill the field with garbage and the check passes). It *cannot* check that the
thing is **good** — whether the inference holds, the rebuttal is the strongest available, the
source is authoritative. That is tier-3 judgment, and it belongs on an honesty card, not in an
Operation. The design's rule: **tier 2 detects absence-of-articulation (a real, weaker defect);
tier 3 judges quality (the PI, or a gated agent proposal).** Wherever this note earlier implied
a presence check was a quality check, it was wrong; the corrected mechanisms below state which
tier they live in.

---

## 2. The artifact lattice

The original five-artifact sketch (question → map → outline) was descriptive-to-rhetorical
with a missing middle: a map is *what exists*, an outline is *how you argue*, and an outline
that falls out of the map's topology is a **survey, not a contribution**. The corrected
pipeline inserts the thesis and splits the question:

```
        ┌── scope ───────> map boundary (which subgraph is "the project")
question┤
        └── inquiry ─────> thesis target (what we're trying to answer)
                                 │
   map (descriptive view over the knowledge graph)
                                 │
                                 ▼
   thesis  (a CLAIM in provisional/hypothesis state — the project anchor)
                                 │
   argument graph  (the supports/contradicts subgraph rooted at the thesis)
                                 │
        ┌────────────────────────┼─────────────────────────┐
        ▼                         ▼                          ▼
   gaps (thesis-relative,    outline (rhetorical order   structural impact +
   impact-ranked)            of the DEFENSE, not the     saturation
        │                    graph topology)             (derived views over
        │                         │                       the argument graph)
        │                         ▼
        │                    writing / drafting ──> EMITS gaps (loop back)
        ▼
   sources-gap (when a knowledge-gap can't be closed from existing catalog)
```

Two feedback edges matter and were under-weighted in the original sketch:

- **Closing any gap regenerates the map** (derived — the *traversal* is cheap; *materializing*
  it to frontmatter for Bases is not free, see §12).
- **Writing emits gaps** (the highest-value loop — see §6). The draft is where you discover
  the gaps the map structurally cannot show you.

And one edge is *expensive*, not casual: **revising the question** triggers a project-wide
staleness cascade (§7).

### There are two graphs, not one

This is the central structural insight. The system holds:

1. The **descriptive knowledge map** — topology of what exists in the project's subgraph.
   Source of the *scope* picture and the "open issues" panel. This is the **bottom-up**,
   emergent structure of the Zettelkasten / Maps-of-Content tradition (Memoria's
   fleeting → source → claim → hub pipeline is exactly Ahrens's fleeting → literature →
   permanent → structure-note pipeline).
2. The **argument graph** — the `supports` / `contradicts` / **`warrant`** subgraph
   (ADR-8 / ADR-52) rooted at the thesis claim. Source of the *outline*, *impact*, and
   *saturation*. This is the **top-down** logical scaffold of the Toulmin argument-mapping
   tradition (claim ← grounds ← warrant, with backing, qualifier, and rebuttal).

The outline derives from the **second** graph — the argument, not the topology. That single
distinction is what moves the gate from "organizes knowledge" to "produces an argument," and
it is grounded in the PKM/research literature: pure bottom-up emergence (naïve Zettelkasten —
"the outline is discovered in the links") *structurally* yields a survey, because the structure
follows topology; the Toulmin layer is the third structuring mode that turns a cluster of
claims into a *defended* argument, and its hierarchy linearizes into an outline mechanically
(top node → thesis, first-level reasons → section topic sentences, grounds + warrant →
supporting sentences, rebuttal nodes → counterargument section).

**Warrant is a first-class attribute, not decoration.** Toulmin's load-bearing observation is
that the *warrant* — the inferential rule licensing grounds → claim — is "frequently left
unstated." Making it an explicit attribute on `supports` edges is what surfaces the
unstated-warrant gap (§6): a thesis can be well-*supported* while the reasoning connecting its
evidence to the claim is merely assumed.

---

## 3. The artifacts, classified

The load-bearing axes are the architecture's own: **derived vs. authored** (regenerable view
vs. lifecycle-tracked note) and **operation vs. agent vs. human** (deterministic vs. posture
vs. PI). Get the classification right and canonical-ness, gating, and staleness all fall out.

| Artifact | Owner / producer | Kind | Canonical? | Reuses |
|---|---|---|---|---|
| **Question** (scope + inquiry) | PI authors, Co-PI refines | Authored note, versioned | Yes | `research-focus.md`, `project-hints.yaml` topics (ADR-15) |
| **Map** | Operation (deterministic scan) | **Derived** view / Base | No — never hand-edited | Bases (ADR-49), contradictions (ADR-9), MOC-threshold (ADR-19), drift (ADR-67) |
| **Thesis** | PI authors, project drives its lifecycle | **Provisional claim** (anchor) | Eventually (gated) | Claim note type (ADR-10 / ADR-50) |
| **Argument graph** | Human-set relations; agents propose | Derived view over relations | Relations yes | Typed relations (ADR-8 / ADR-52) |
| **Knowledge gap** | Librarian *map/link* lanes propose | Proposals → approved hubs/indexes/claims | Results yes (review-gated) | Inbox cards (ADR-51), pre-file similarity (ADR-38), pattern library (ADR-53) |
| **Sources gap** | Librarian discovers → Peer-reviewer gates | Proposals → approved catalog entries | Results yes | **Existing `gap` card** (ADR-51), ingest (ADR-30); discovery engine = ADR-61 (**deferred**) |
| **Structural impact / saturation** | Operation (graph query) | **Derived** view | No | new — twin of the map |
| **Outline** | Writer lane (generative, drafts only) | **Derived / draft** note | No | Studio (ADR-68), Writer lane (ADR-48) |

Note how much already exists. The **sources-gap is the existing `gap` Inbox card** (ADR-51
defines it as "missing-source need"), whose discovery engine is the nightly loop of ADR-61 —
**which is `deferred`, not accepted**. So sources-gap cannot treat ADR-61 as existing machinery
(see §11 and build-order step 5 for the consequence). The **map**
is the same recompute pattern as the contradictions dashboard, scoped to a project. The
genuinely new artifacts are: the **versioned question**, the **thesis as project anchor**,
the **knowledge-gap card type** (distinct from the sources `gap`), the **structural-impact
view**, and the **outline**.

---

## 4. The thesis is a *provisional* claim — and that one state does four jobs

The thesis is **not** a claim "promoted" to anchor. A canonical claim asserts something
established and defended; the thesis, for most of a project's life, is a **hypothesis under
test**. Promoting it to canonical manufactures exactly the premature-thesis / sunk-cost
artifact the design is trying to avoid. So:

> The thesis is a claim in `proposed` / `provisional` lifecycle state (ADR-50). The project's
> job is to drive it to `current` (defended) or `retracted` (killed).

That single lifecycle field absorbs four things, in keeping with the ADR-10 precedent of
*deriving state from structure rather than adding a parallel status field*:

1. **Output-mode visibility** — "no thesis yet" / "provisional" / "canonical" is just the
   thesis's state, not a separate flag.
2. **Project status, derived not stored** — *exploring* while the thesis is `proposed`,
   *defending* as it climbs, *done* at `current`, *killed* at `retracted`. The project needs
   no status field of its own.
3. **Falsification as a clean result** — a `retracted` thesis plus the argument subgraph that
   refuted it *is* an answer to the inquiry (no). The system treats this as a finished project,
   not a dead end. The architecture must make falsification **cheap to reach**, or the PI
   defends a dying thesis to dodge the `retracted` stamp.
4. **Mode transition** — a project whose thesis is `retracted` but whose map is rich can
   **convert to survey output**, the map as salvage value. Thesis-death is a natural
   mode-conversion trigger, not only a terminal state.

### Output mode: thesis-driven (default) vs. survey (explicit)

The gate must default to thesis-driven output but allow **survey/landscape mode** as an
explicit, chosen state. A system that *cannot* produce a survey has merely inverted the
literature-review bias instead of removing it; forcing a thesis onto a project that has none
yet produces the worst artifact — a premature thesis defended out of sunk cost. "This project
has no thesis yet" is a visible state (= the thesis lifecycle), not a hidden assumption.

Survey mode swaps the *done* metric (§5).

---

## 5. Termination — the artifact the original model lacked entirely

The original loop ("closing a gap changes the map, the map informs new gaps") is a **treadmill**:
gaps are unbounded, and nothing said when the map is sufficient to write from. The dashboard's
implicit job was to keep generating reasons to keep working. Termination needs a **saturation
signal**, and it is *derivable* once gaps are thesis-relative.

### Structural impact is an Operation, not an inference (the three-tier correction)

There are three tiers of "how much does closing this gap change the thesis's defensibility,"
and only the third is the inference the architecture distrusts:

| Tier | What it is | Trust class |
|---|---|---|
| 1. Manual PI prioritization | no signal | — (strictly dominated) |
| 2. **Structural impact** | deterministic topology over the argument graph: reachability from the thesis, articulation-point / degree, typed-relation lookup | **Operation** — twin of the map, recomputes for free |
| 3. Semantic impact | an agent judging "how persuasive-to-the-argument is this gap" | inference — gated behind honesty cards, **not now** |

Tier 2 carries **none** of the automation-bias risk, because there is nothing to promote —
it is a computation. Manual-first is *strictly worse* than a deterministic view and no more
honest. So: **tier 2 is the launch mechanism**; tier 3 is evidence-gated and may be
permanently deferrable.

**The tier-2/tier-3 boundary bounds what tier 3 would ever buy.** Topology tells you a gap
is *positioned* to matter (on-path, load-bearing) — not that closing it *would* matter (the
new support might be redundant). So tier 2 delivers a **sound cut**: off-path gaps genuinely
cannot move the thesis; prune them with confidence. Among on-path gaps it orders by cheap
structural proxies (degree, fragility, recency). Tier 3's only job would be **ranking within
the on-path set** — ships only if those proxies demonstrably underserve.

**Argument structure *is* the impact proxy.** Toulmin's distinction between *linked* and
*convergent* support is exactly the topological signal tier 2 needs, and it makes the
"redundant support" intuition above precise:

- A **linked co-premise** — one of several premises that must work *together*, where dropping
  any one collapses the inference — is an **articulation point** in the argument graph =
  **high structural impact**. A gap here is load-bearing.
- A **convergent** support — an independent reason that supports the thesis on its own — is
  **redundancy-tolerant** = **lower impact**. A gap here closes a nice-to-have.

So the impact Operation isn't inventing a heuristic; it's computing linked-vs-convergent
structure (articulation points / co-premise sets) over the argument graph.

### Saturation gates on three conditions

This is **theoretical saturation** in the grounded-theory sense (Glaser & Strauss; Corbin &
Strauss) — the *categories are dense and their relationships validated* — **not** *data*
saturation (mere informational repetition). The distinction matters: you can stop finding new
material long before the argument is actually defensible. We adopt Dey's softer **theoretical
sufficiency** — stop at *sufficient* depth to defend the thesis, not at a provable absence of
anything new.

Naïvely, "all open gaps below an impact threshold" is **true on an empty project** — nothing
is wired, so everything is low-impact, so a newborn project reads as saturated and termination
fires at birth. And it is **true on an unchallenged thesis** — a thesis that has only ever
accumulated `supports` and never faced a serious `contradicts` looks complete but is
intellectually untested (Popper: a hypothesis is *corroborated by surviving refutation*, never
proven by confirmation). So saturation gates on **three** conditions:

1. the argument graph is **mature enough** (density threshold — see §13), and
2. remaining open gaps are **below the impact threshold**, and
3. the thesis has **faced its strongest available rebuttals and survived** (Corbin & Strauss's
   "relationships validated" + Popper's refutation).

**Conditions 1 and 2 are fully structural; condition 3 is not — and the note earlier
overclaimed that it was.** "Strongest *available*" and "*sought*" are not topological
properties: a lazy project with one strawman `contradicts` marked `addressed` passes a purely
structural check while remaining intellectually untested. Condition 3 therefore splits along
the two-tier rule (§1):

- **Tier-2 floor (structural, auditable):** at least one `contradicts` edge on the thesis
  exists and is marked `addressed`. Necessary, gameable, *not* sufficient.
- **Tier-3 ceiling (honesty card):** is it the *strongest available* rebuttal, and was it
  *genuinely* addressed? This is an irreducible judgment — the PI's, or a gated Peer-reviewer
  proposal. It does **not** become a computed fact.

So saturation is a **computed fact on conditions 1–2 plus an honesty-card judgment on
condition 3** — "no open gap is on-path-and-load-bearing in a mature graph; a tier-2 refutation
floor is met; the PI confirms the thesis has truly survived challenge." Honesty cards also carry
the *recommendation to act* and the PI's right to override from off-graph knowledge. This still
**inverts the treadmill**: the dashboard's job flips from generating reasons to keep working to
*arguing for stopping when warranted*.

**What the structural formulation actually buys (corrected).** The standard critique of
saturation (Saunders et al.) is that it rests on "an uncertain predictive claim about… data yet
to be collected… testable only by overturning the decision to halt" — i.e. it is *unprovable*.
The structural formulation sidesteps this **for conditions 1 and 2** — it replaces an unprovable
prediction with a checkable fact about topology. It does **not** escape the critique for
condition 3, which is precisely the part (refutation sufficiency) that resists structural
formulation. The honest headline is: *two of three saturation conditions are auditable; the
third is the irreducible judgment, and it lives on an honesty card by design* — not "we fully
escaped the critique."

### Survey mode terminates too

Survey mode has no thesis, so it can't borrow thesis-relative saturation. It uses
**coverage-relative saturation**: the map's high-degree entities are addressed. That is also
deterministic topology — just over the **knowledge map** instead of the argument graph. Both
done-metrics unify: **thesis mode terminates on the argument graph, survey mode on the
knowledge map, both via structural Operations.**

---

## 6. Gaps — absences are only one kind

"Knowledge gap = things that can be added" is the **additive** gap only. The gaps that sink
research are quality gaps the additive model is blind to. A project can have zero missing
notes and still be intellectually bankrupt. The taxonomy:

| Gap kind | What it detects | Detection |
|---|---|---|
| **Additive** | missing hub / index / claim / source | Librarian map/link lanes; pre-file similarity (ADR-38) |
| **Fragility** | a claim resting on a single source | degree query on the support graph |
| **Conflict** | two notes in the relevant subgraph contradict | ADR-9 dashboard (accepted) — but it reads only *human-set* `contradicts`; project-driving is future intent, not existing wiring |
| **Structural** | over-concentration / circular support (everything cites one hub) | articulation-point / centrality query |
| **Unstated-warrant** | an on-path `supports` edge whose warrant (grounds→claim inference) is not *articulated* | warrant attribute absent/empty — **tier-2 presence check only** |
| **Refutation** | the thesis has accumulated support but never faced a serious challenge | no `addressed` `contradicts` edge past the maturity gate — **tier-2 floor; §5 condition 3** |

The last two are the methodologically-grounded additions, and both are honestly **tier-2
presence checks, not quality checks** (§1):

- **Unstated-warrant** (Toulmin: the warrant is "frequently left unstated"). What the Operation
  detects is *absence of articulation* — the inference isn't even written down. It **cannot**
  detect a *bad* warrant: fill the field with garbage and the gap closes. Judging whether the
  inference holds is tier-3. This is still worth flagging — an unarticulated inference is a real,
  if weaker, defect, and forcing articulation is exactly what argument-mapping research shows
  improves reasoning — but the note must not pretend the check validates the inference.
- **Refutation** (Popper) feeds saturation condition 3 and inherits its tier-2/tier-3 split (§5).

**`warrant` is a net-new decision, not reuse.** It is **not** in ADR-8 or ADR-52, which keep a
deliberately small `supports` / `contradicts` vocabulary. This design *introduces* it; the ADR
must own that as a new decision (and weigh it against ADR-8/52's minimalism), not present it as
existing machinery.

**Authoring cost (named, not hidden).** Requiring a warrant on every on-path `supports` edge is
real PI labor (or agent-proposed-then-PI-confirmed — see §14). A design that mandates
hand-authored warrants on a dense argument graph can fail on adoption alone; the warrant gap
should likely be *advisory* (a surfaced weakness), not a hard blocker, until that cost is
measured.

Mapped onto the research-gap taxonomy (Müller-Bloch & Kranz), additive/fragility/unstated-warrant
are *missing*-family gaps and conflict/refutation are *contested*-family gaps — the additive-only
model is blind to the entire contested family, which is where most live research fails.

All are evaluated **thesis-relative**: a single-source claim *on the thesis's support
path* is high-impact; the same fragility off-path is noise. A contradiction *inside the
argument subgraph* is top priority. Thesis-relativity is what makes the map's "open issues"
panel substantive rather than cosmetic — and it's the intended path to making ADR-9's dashboard
(today a surface over human-set `contradicts`) actually *drive* project work, which it does not
do yet.

### Knowledge-gap → sources-gap is the one crossing edge

A `knowledge-gap` card that **cannot be closed from the existing catalog** emits a
`sources-gap` card. That is the single edge in the lattice that crosses from "use what we
have" to "go get more," and the natural seam between the two gap types.

### Writing is a gap-generator, not a terminal sink

The original DAG ended `outline → writing`. But the **draft is the best gap-detector**: you
sit down to write the paragraph and find you don't actually have the evidence. So writing
produces back into the system. Implementable directly: run the Writer's draft against the
argument graph; **every assertion not grounded in a `current` claim emits a knowledge-gap**
(or a citation flag, tying into FAMA). The outline stops being terminal and becomes a *probe*
— part of its job is to fail and reveal what the map couldn't.

---

## 7. The question is the inverse of the map

The map mutates **freely** (derived, recomputes for free). The question mutates **rarely**
and cascades **widely**. Question-creep is the #1 real-world failure mode of research
projects, and the original model treated "gaps may inform changes to the question" as a casual
edge equal to closing a gap. It is the most expensive move available: changing the question
potentially invalidates the gaps, the outline, the thesis, and the scope of the map.

Guardrails:

- **Version the question**, record the **rationale** for each change.
- Mutation triggers a **staleness cascade**: downstream artifacts are *marked* needing
  re-validation (`provisional` / alert), **not auto-invalidated** — consistent with
  propose-don't-promote. Fight creep by making the cost *visible* ("this edit puts 14
  artifacts in doubt"), not by making the edit destructive.

### Split scope from inquiry

The question conflates two jobs:

- **Scope** — what's in the project subgraph (the map's boundary). Generalizes the existing
  `project-hints` topics (ADR-15).
- **Inquiry** — what you're trying to answer (the thesis target).

Splitting them lets the map **diagnose which problem you have**: well-scoped but unanswerable
from the catalog (→ sources-gap), or answerable but trivially narrow (→ inquiry too thin).

The split has direct methodological backing, and the two frameworks give the question artifact
its template and its quality check:

- **Answerability = PICO completeness.** Structuring the inquiry as Population/Problem,
  Intervention/Exposure, Comparison, Outcome (PICO) makes un-answerability visible — a question
  missing a *measurable Outcome* is too broad to answer, and each element becomes a search-concept
  block the map can check coverage against.
- **Scope = FINER-Feasible; quality = FINER-Novel.** FINER (Feasible, Interesting, Novel,
  Ethical, Relevant) judges whether the question is *good*: too-broad fails **Feasible**
  (remedy: narrow scope), too-narrow fails **Novel/Relevant**. **Novel** ties question quality
  directly to gap analysis (§6) — a good question is one whose answer fills a real gap.

So the map's diagnostic becomes concrete: a project that fails PICO has an *answerability*
problem; one that fails FINER-Feasible has a *scope* problem; one that fails FINER-Novel has
an *inquiry-worth* problem.

**Honesty about the mechanism (don't oversell it).** PICO/FINER here are **PI-applied quality
lenses and a structured question template**, not deterministic checks. "The map checks PICO
coverage" can only mean one of two things: a tier-2 presence check over structured fields the PI
fills (gameable — an empty `outcome:` is detectable, a vacuous one is not), or tier-3 NLP
judgment of whether the question is *genuinely* answerable. The first is a useful prompt; the
second is inference and out of the deterministic spine. FINER-Novel "ties to gap analysis" is
likewise a lens, not an automatic computation. Treat these as checklist scaffolding for the
question artifact, not as Operations.

---

## 8. Cold start — be honest about when the signal turns on

Structural impact's quality scales with the argument graph's density — and the graph is
emptiest exactly when the project is youngest. At birth the thesis has two or three wired
relations; nothing is "on a path" because there's barely a path. Impact ranking is weakest
precisely when orientation is most needed. The fix is not to defer; it's to be honest about
the **regime the project is in**:

- **Two triage regimes with an observable transition.** Early regime: **scope-overlap**
  (does this gap touch the inquiry's topics? — deterministic via `project-hints`, still tier 2,
  no semantic judgment needed). Later regime: **argument-structure** (the impact view above).
  The transition is the argument graph crossing the maturity threshold — a milestone worth
  surfacing ("triage has switched from scope-relevance to argument-structure").
- **Maturity gates trust in *every* structural signal, not just termination.** Below the
  threshold the impact ranking is advisory and the dashboard **displays low confidence**
  rather than presenting a confident-looking but meaningless ranking. Above it, load-bearing.

The cold-start fallback never forces a tier-3 jump: scope-overlap is deterministic.

---

## 9. Build order

1. **ADR for the Project gate** — anchored in the deferred ADR-70 slot. Spine: thesis-as-
   provisional-claim; two graphs; structural impact / triage / saturation as derived
   Operations; output-mode = thesis lifecycle state; project status derived, not stored.
2. **Question split** (scope / inquiry, versioned, rationale-logged) + **thesis as provisional
   anchor claim**; project status read off the thesis lifecycle.
3. **The two graphs + their structural views**: descriptive map (knowledge graph); argument
   subgraph with structural-impact and structural-saturation (thesis mode); coverage-saturation
   (survey mode); maturity gate + scope-overlap cold-start floor; displayed confidence below
   the threshold.
4. **Gap taxonomy** (additive / fragility / conflict / structural; unstated-warrant and
   refutation as *advisory* tier-2 presence checks, §6) ranked by the structural-impact view;
   honesty cards on every *quality* judgment and on the *recommendation to act*, not on the
   tier-2 signals.
5. **Writing-as-gap-generator** loop + **sources-gap reliability gate** via the Peer-reviewer
   lane (relevance is discovery's job; CEBM-level/source-type are tier-2 enum fields feeding
   impact, CRAAP is the tier-3 rubric — §11). **Depends on the ADR-61 fork**: either adopt the
   deferred discovery engine or ship sources-gap as a manual `gap`-card queue. Triage reliability
   by the impact view so it doesn't become its own treadmill.
6. **Tier-3 semantic impact** — explicitly *not now*. Ships only if tier 2 underserves the
   on-path ordering, behind honesty cards.

---

## 10. Out of scope

**Coding.** "The basis for the writing and coding" implied a generality this five-artifact
model doesn't have. Code output has a different artifact lattice (spec / interface / test) and
a different lane (Engineer, ADR-34 / ADR-07). This gate is scoped to **argumentative output**;
the thesis/outline can *feed* code work downstream, but this model does not cover it.

---

## 11. Sources-gap closes on reliability, not just relevance

Discovery finds *relevant* sources; relevance ≠ trustworthiness. A gap-pull loop that fills
holes with whatever discovery surfaces fills them with the most *findable* material, which
correlates with popularity, not authority — laundering low-quality sources into canonical
claims. Closing a sources-gap therefore routes through the **Peer-reviewer** lane (skeptical
posture, separation of duties from the Librarian who discovers) for source evaluation. Triage
this too: only hard-evaluate sources that would close **high-impact** gaps.

**The reliability gate has concrete criteria** — but only one of them is deterministic; the
two-tier rule (§1) applies here too:

- **Source type** (primary / secondary / tertiary) and **levels of evidence** (CEBM: systematic
  review › RCT › cohort › case series › expert opinion) are **tier-2 structured enum fields**.
  CEBM-level is *rankable*, so it **feeds impact triage (§5)** — closing a fragility gap with a
  Level-1 source is worth more than with a blog post. This is the one genuinely mechanical bridge
  between reliability and impact, and the most concrete enhancement here. (Caveat: assigning the
  level is itself a judgment; the *field* is tier-2, *populating it correctly* is tier-3.)
- **CRAAP** (Currency, Relevance, Authority, Accuracy, Purpose) is a **tier-3 appraisal lens** —
  a Peer-reviewer judgment surfaced on an honesty card, not a computed gate. A weakness in
  Authority or Purpose disqualifies even a current, relevant source, but no Operation can decide
  that. Treat CRAAP as the Peer-reviewer's rubric, not a deterministic filter.

### On "the gate drives all catalog/library/source work"

This is a real shift, **but it depends on a deferred ADR.** The ambient/topic-pull discovery
engine (nightly loop by `primary_topics`) lives in ADR-61, which is `deferred`. So the project
model has a fork it must state explicitly:

- **Either** this gate's gap-pull becomes a *reason to adopt ADR-61* — in which case the ADR
  must say so and satisfy ADR-61's own gate conditions (it `assumes: [34, 37, 21]`), **or**
- **sources-gap ships as a manual queue** in v1: the gate emits `gap` cards (ADR-51) and the PI
  pursues them by hand, with no automated discovery engine behind them.

Do not cite ADR-61 as a given. With the engine present, gap-pull is **theoretical sampling** in
the grounded-theory sense — sampling driven *toward the under-developed categories* (the
high-impact gaps), collection and analysis interleaved. Recommendation either way: **gap-pull
and ambient are complementary, not a replacement** — gap-pull prioritizes the queue; ambient
discovery is the serendipity channel (you don't want to only ever find what you already knew you
were missing).

---

## 12. Obsidian / Bases integration

The 2025–2026 Obsidian ecosystem has converged on **exactly Memoria's architecture**:
*frontmatter is the canonical store → Bases (+ Dataview) are views → Templater / QuickAdd /
Modal Forms are the input layer.* That is ADR-47 / ADR-49 verbatim. Bases went core (v1.9.0,
May 2025; GA Aug 2025); Projects-by-Olsson is discontinued; the mgmeyers Kanban is stalled —
the whole ecosystem is collapsing onto properties-as-truth, which Memoria bet on early. The
integration plan rides this, with one hard constraint.

**The constraint: Bases reads only frontmatter, never note bodies, and cannot traverse graphs.**
It has no relations/rollups and no aggregation (the v1.9.7 `file()` lookup has neither
auto-refresh nor aggregation; Gantt/relations aren't on the roadmap). Consequences for the two
graphs:

- The **argument graph is Bases-visible** only because typed relations live in frontmatter
  (ADR-8 / ADR-52). Keep them there.
- **Structural impact, saturation, and maturity are NOT Bases formulas** — they are graph
  traversal (reachability, articulation points, linked-vs-convergent, degree). They must be a
  deterministic **Operation** that traverses the relation graph and **writes derived properties
  back to frontmatter** (`impact`, `on_path`, `saturation_state`, `graph_maturity`,
  `thesis_lifecycle`). Bases then displays and filters on those computed properties. This is the
  concrete shape of the §5 Operation, and it confirms: do not wait for native Bases relations.

  **This contradicts the "recomputes for free" language used earlier — reconcile it.** The
  *traversal* is cheap, but *materializing* it to frontmatter is not: every gap-close triggers a
  frontmatter write across the affected component (git churn, ADR-25 logging), and because Bases
  has **no auto-refresh**, the displayed values go **stale between Operation runs**. So the model
  is explicitly: the Operation runs **on-demand** (on gap-close, on a debounce, or on PI request),
  it stamps a **`computed_at`** on each derived property, and the dashboard shows that timestamp
  so stale values are visible as stale. "Cheap derived view" is true of the computation; the
  persisted properties are a materialized cache with a real write cost and an explicit freshness
  marker — not free, and not silently current.

**Where to build the surfaces:**

- Ship the map / argument-graph / impact dashboards as a **custom Bases view via the Bases API**
  (`registerBasesView`, shipped Oct 2025). Native, composable, and aligned with kepano's framing
  of Bases as "a visualization layer in service of editing Markdown" — which is Memoria's
  files-first philosophy exactly.
- Use a **base-board–style Kanban** (Kanban-on-Bases) for gap triage (cards by `impact` /
  status) and for the thesis lifecycle (`proposed → provisional → current → retracted`).
- A **generated JSON Canvas** is a good *read-only* human-facing render of the argument map
  (claim → grounds → rebuttal), but Canvas is JSON and invisible to Operations — it is output,
  never source of truth.

**Gating caveat (load-bearing):** base-board's drag-to-change-frontmatter writes directly to the
note. That is fine for **non-canonical** artifacts (gap cards, outline drafts) but must **never**
be the write path for the thesis or claims in gated zones — those route through the policy MCP
(ADR-03 / ADR-28). Drag-to-promote would silently bypass the review gate.

**What to deliberately avoid:** the **task/deadline PM paradigm** (Tasks, Day Planner, the
Gantt-style Project Manager plugin; GTD next-action/context semantics) reintroduces the very
treadmill §5 was built to escape — it models work as deadline-driven task completion that never
knows it's *done*. Likewise **Johnny Decimal / rigid top-down address grids** are antithetical
to an emergent knowledge graph. Memoria should be **Zettelkasten-for-the-map, Toulmin-for-the-
argument** — never a to-do list.

---

## 13. Open decisions (the earlier "one knob" claim was wrong)

An earlier draft claimed "no architecture decision left open" with the maturity threshold as a
minor tuning knob. That was wrong on both counts. There are three open decisions, and the first
is **safety-critical, not cosmetic**.

**13.1 — The maturity threshold is the gate's trust switch.** It governs the transition from
"advisory, low-confidence" to "load-bearing" for *every* structural signal (§8 says so
explicitly). Set it too low and the gate asserts confidence on a sparse graph — *the
automation-bias failure the whole design exists to prevent*. Set it too high and the gate is
permanently advisory and never terminates. This is the parameter the gate's safety rests on, not
a knob to tune after launch. Candidates for the measure:

- count of `addressed` `supports` / `contradicts` relations on the thesis's component, or
- the component reaching connectedness (every claim reachable from the thesis).

Propose a *conservative* default (err toward advisory) and treat raising it as a safety change,
not a preference.

**13.2 — Is `warrant` worth its cost?** Net-new vocabulary against ADR-8/52's deliberate
minimalism, with real authoring burden (§6). Decide whether it ships at all in v1, and if so as
advisory-only.

**13.3 — The ADR-61 fork (§11).** Adopt the deferred discovery engine (and satisfy its gate
conditions) or ship sources-gap as a manual queue. This is a scoping decision the ADR must make,
not inherit.

---

## 14. The PI labor budget — "inference-free" is "PI-labor-full"

The gate is inference-free partly by *relocating* cost onto the PI. Every input the deterministic
spine runs over is human-authored or human-confirmed: the PICO/FINER question, the thesis, every
typed relation, every warrant, every gap-card adjudication, every source gate. For a **solo
researcher** (ADR-24, single-researcher scope) this is the make-or-break adoption question, and
the earlier draft hid it entirely.

This is partly *intentional* — the architecture maximizes human contact with what gets produced
by design (ADR-48/51); approval is the structural guarantee. But "intentional" is not "free," and
the design must budget it:

- **Author vs. review.** The cost is far lower if agents **propose** (relations, warrants,
  gap closures, source appraisals) and the PI **confirms**, rather than the PI authoring from
  scratch. This is already the architecture's posture (agents propose, PI promotes) — the gate
  must lean on it everywhere, so PI labor is *review* labor, not *authoring* labor.
- **Advisory by default.** Tier-2 presence checks (warrant, refutation, PICO coverage) should
  *surface* weaknesses, not *block* progress, until their cost is measured against real use.
- **Measure it.** The vault-eval / measurement harness (ADR-62) should track per-project PI touch
  count (cards adjudicated, relations confirmed) as a first-class adoption metric. If a project
  costs hundreds of clicks before it terminates, the leverage the gate promises has evaporated —
  exactly the §7/#7 failure, now visible.

This does not change the architecture; it names the tradeoff the architecture makes, so the ADR
can decide it deliberately rather than discover it at adoption.

---

## 15. Scope: one thesis per project (and what breaks otherwise)

The elegant "project status = thesis lifecycle" (§4) assumes **one thesis per project**. Two
cases break it, and the ADR must address them explicitly:

- **Competing theses.** If a project carries two rival theses, "project status" is undefined when
  one is `current` and the other `retracted`, and the argument graph has two roots (so on-path /
  impact is ambiguous). **v1 recommendation: one thesis per project.** Rival hypotheses are
  separate projects, or sub-theses under one parent thesis with a defined precedence — deferred.
- **Thesis supersession mid-project.** ADR-10 supersession applies to the thesis claim itself
  (ironically, since the thesis *is* a claim): the PI may replace the anchor mid-inquiry. This is
  not a failure — it's a legitimate pivot — but it **re-roots the argument graph**, which
  invalidates `on_path` / `impact` / `saturation` for the whole component and triggers the §7
  staleness cascade. This is the one case where project status is *not* a clean read off a single
  lifecycle field, because two thesis claims (old `retracted`, new `provisional`) coexist during
  the handover. The ADR should define re-rooting on thesis supersession as a first-class
  operation, even if v1 just forces a full recompute.

---

## Appendix — ADRs this gate reuses

- **ADR-70** navigation gates — the deferred Project-gate slot this fills
- **ADR-68** workspaces — Studio drafting surface, `research-focus.md` anchor
- **ADR-51** Inbox category & honesty cards — `gap` card (= sources-gap), arguments-for/against
- **ADR-61** nightly discovery loop (**deferred**) — the engine sources-gap *would* drive; this gate either forces its adoption or ships sources-gap as a manual queue
- **ADR-15** project membership from topic hint — scope / `project-hints` topics
- **ADR-10** claim supersession — derive state from structure; provisional → current/retracted
- **ADR-50** universal lifecycle & maturity — the thesis's lifecycle states
- **ADR-8 / ADR-52** typed relations / links-vs-relationships — the argument graph
- **ADR-9** contradictions dashboard — conflict gaps, now wired into project work
- **ADR-19** MOC-threshold alert, **ADR-67** drift — the map's "open issues" panel
- **ADR-49** catalog in Bases — the map as a Base view layer
- **ADR-48** Co-PI & agent consolidation — Librarian / Writer / Peer-reviewer lanes
- **ADR-38** pre-file similarity, **ADR-53** pattern library — additive-gap detection
- **ADR-34 / ADR-07** code artifacts — the out-of-scope coding consumer
- **ADR-16** systematic review (adopt-on-demand) — the PRISMA screening funnel behind sources-gap
- **ADR-31 / ADR-49** native Obsidian MCP / catalog in Bases — the §12 integration substrate

## Appendix — external methodological grounding

- **Toulmin** (*The Uses of Argument*) — claim / grounds / **warrant** / backing / qualifier /
  rebuttal; the argument graph (§2), the warrant attribute, the unstated-warrant gap (§6).
- **Argument mapping** (van Gelder) — *linked* (co-premise / articulation point) vs *convergent*
  (independent) support; the structural-impact proxy (§5).
- **Ahrens, *How to Take Smart Notes* / Zettelkasten / LYT (Milo)** — fleeting → literature →
  permanent → structure-note pipeline = Memoria's fleeting/source/claim/hub; bottom-up emergence
  and why it alone yields a survey (§2).
- **Glaser & Strauss / Corbin & Strauss; Dey; Saunders et al.** — theoretical saturation vs data
  saturation, theoretical sufficiency, theoretical sampling, the unprovability critique (§5, §11).
- **Popper** (falsifiability) — thesis corroborated by surviving refutation; saturation
  condition 3 and the refutation gap (§5, §6).
- **PICO / FINER** — answerability vs scope vs novelty for the question artifact (§7).
- **Müller-Bloch & Kranz** — missing-vs-contested research-gap taxonomy (§6).
- **CRAAP; primary/secondary/tertiary; CEBM levels of evidence** — the reliability gate and its
  feed into impact triage (§11).
- **PARA (Forte) / GTD (Allen)** — the *finishability* test (a project must be able to end) and
  the task/deadline paradigm deliberately **not** adopted (§12).
