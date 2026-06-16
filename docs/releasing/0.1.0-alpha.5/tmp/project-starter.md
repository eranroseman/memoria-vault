# Project Starter — the Project gate design

Status: design note (alpha.5 `tmp/`), pre-ADR — **no ADRs changed by this note.** Captures the
converged design for the fourth navigation gate — the **Project gate** deferred by ADR-70 and the
empty `projects/` workflow left by ADR-68. The open decisions are in §13; the ADR/docs build plan
and recommendation are in §18–§19. To be folded into ADRs (§18) once the §13 calls are made.

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
   thesis  (a provisional `thesis`-type note — the project anchor)
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
   (ADR-8 / ADR-52) rooted at the thesis. Source of the *outline*, *impact*, and
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
| **Thesis** | PI authors, project drives its lifecycle | **Provisional `thesis`-type note** (anchor) | Eventually (gated at `current`) | new type, modeled on `source` lifecycle (ADR-50); supersession (ADR-10) |
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

## 4. The thesis is a *provisional note type of its own* — not a claim

**Correction (schema-grounded).** An earlier draft said "the thesis is a claim in
`proposed`/`provisional` state." That cannot work: the claim schema
(`src/.memoria/schemas/types/claim.yaml`) has lifecycle **`[current, retracted, archived]`** —
claims are *born `current`*, because a claim is by definition canonical and gated (ADR-49/50).
A "provisional claim" is a contradiction in this schema. So the thesis must be its **own note
type** (`thesis`), carrying the *full* lifecycle chain `proposed → provisional → current →
retracted → archived`, **gated at the `current` transition** — exactly parallel to how `source`
is ungated until promoted. When a thesis reaches `current` it *is* a defended top-level claim
(whether it then migrates into a `claim` note or stays a `current thesis` is a sub-decision for
the thesis-type ADR).

The motivation is unchanged: a canonical claim asserts something established; the thesis, for
most of a project's life, is a **hypothesis under test**, and forcing it canonical manufactures
the premature-thesis / sunk-cost artifact this design exists to avoid.

> The thesis is a `thesis`-type note whose lifecycle runs `proposed → provisional → current →
> retracted → archived`, gated at `current`. The project's job is to drive it to `current`
> (defended) or `retracted` (killed).

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
   defends a dying thesis to dodge the `retracted` stamp — and "cheap" is made real by the
   mark-don't-invalidate / lazy-re-confirm pivot mechanics in §15 (without which a pivot would
   re-impose the very sunk-cost trap this point removes).
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

### Thesis and question are two distinct artifacts, not lifecycle stages of one thing

They are different parts of speech: the **question is interrogative + scoped** (what you're
asking); the **thesis is declarative** (your tentative answer). They co-exist — early on a
project has a question and **no thesis yet** (the output-mode state above). "The question
becomes the thesis" is wrong: the thesis is the *answer to* the question, 1:1 in v1 (§15). The
question is authored first and is stable (mutation = the expensive cascade of §7); the thesis is
born from the map and moves through its lifecycle.

**Project question — a `project` note** anchoring `projects/<slug>/`:

```yaml
type: project
title: "<inquiry, as a question>"
lifecycle: current          # the container; archived on completion (PARA finishability test)
scope_topics: [...]         # generalizes project-hints primary_topics (ADR-15) = the map boundary
inquiry:                     # PICO → answerability lens (§7); PI-filled, tier-3, not a gate
  population: ...
  intervention: ...
  comparison: ...
  outcome: ...              # a missing/measurable Outcome ⇒ question too broad to answer
finer: { feasible: ..., novel: ..., relevant: ... }   # FINER quality lens (§7)
output_mode: thesis | survey
question_version: 1
question_log: []            # rationale per change — the §7 expensive-mutation guardrail
```

**Thesis — a new `thesis` note** (full lifecycle, gated at `current`):

```yaml
type: thesis
title: "<the position, one declarative sentence>"
lifecycle: provisional      # output_mode AND project status derive from THIS (the active thesis)
project: "[[<slug>]]"
links: { supports: [], contradicts: [], warrant: [] }   # warrant is net-new (§6)
sources: []
superseded_by: ""           # ADR-10 — enables the mid-project pivot (§15 dry run)
created: <date>
```

Both are **new schema + template files** to add under `src/.memoria/schemas/types/` and
`src/system/templates/` (normal maintenance, no ADR) — but the *decision* to add a `thesis`
type (and the claim-born-current resolution above) does need an ADR, because it touches the
ADR-50 lifecycle and claim-gating invariants. See §18.

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
| 2. **Structural impact** | deterministic topology over the argument graph: reachability from the thesis, articulation-point / degree, typed-relation lookup | **Operation** — same trust class as the map (cheap to *compute*; materializing it has a real cost, §12) |
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

**Argument structure sharpens the impact proxy — but it *is* a heuristic, honestly.** Toulmin's
distinction between *linked* and *convergent* support makes the "redundant support" intuition
precise:

- A **linked co-premise** — one of several premises that must work *together*, where dropping
  any one collapses the inference — behaves like an **articulation point** = **high structural
  impact**. A gap here is load-bearing.
- A **convergent** support — an independent reason that supports the thesis on its own — is
  **redundancy-tolerant** = **lower impact**. A gap here closes a nice-to-have.

Two honesty caveats (correcting an earlier overclaim that this "isn't inventing a heuristic"):
1. **Linked-vs-convergent is not something topology *yields*.** Whether premises are linked or
   convergent is an authored co-premise annotation; articulation-point analysis only
   *approximates* it. So the within-on-path *ranking* is a (defensible) heuristic, and if the
   distinction is authored rather than approximated, that is additional PI labor (§14).
2. **The off-path/on-path *cut* is the part that stays sound** — reachability from the thesis is
   real topology, so off-path gaps genuinely cannot move the thesis and can be pruned with
   confidence. The heuristic lives only in ordering *within* the on-path set.

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

1. the argument graph is **mature enough** (density threshold — see §13.1), and
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
  proposal. It does **not** become a computed fact. (For the v1 cut, §19 makes this a single
  PI-asserted "refutation sufficiency" stamp rather than a standing honesty-card nag.)

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

**The missing-vs-contested split is this design's own synthesis** — informed by the
research-gap-taxonomy literature (D. Anthony Miles's seven-gaps workshop handout, 2017;
Müller-Bloch & Kranz, 2015), but **not** claimable as either author's canonical scheme, and Miles
does not "supersede" Müller-Bloch (they are different artifact types, and a workshop handout is
not a peer-reviewed source). With that caveat: additive/fragility/unstated-warrant fall in the
*missing* family (knowledge / evidence / empirical), and conflict/refutation in the *contested*
family — the additive-only model is blind to the entire contested family, which is where most live
research fails. The literature also names gap kinds Memoria does **not** yet model (methodological,
theoretical, population) — candidates for a system-wide `gap_type` field on the `gap` Inbox card,
beyond the project gate (§16). Pin the exact citations before any enter `bibliography.md` (§18, §D2).

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

The map mutates **freely** (derived — cheap to recompute, though materializing it has a real cost,
§12). The question mutates **rarely**
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
   provisional-type; two graphs; structural impact / triage / saturation as derived
   Operations; output-mode = thesis lifecycle state; project status derived, not stored.
2. **Question split** (scope / inquiry, versioned, rationale-logged) + **thesis as provisional
   anchor type**; project status read off the thesis lifecycle.
3. **The two graphs + their structural views**: descriptive map (knowledge graph); argument
   subgraph with structural-impact and structural-saturation (thesis mode); coverage-saturation
   (survey mode); maturity gate + scope-overlap cold-start floor; displayed confidence below
   the threshold.
4. **Gap taxonomy** (additive / conflict / fragility — the three free, deterministic kinds, §13.5;
   structural / unstated-warrant / refutation deferred as *advisory* tier-2 checks, §6) ranked by
   the structural-impact view; honesty cards on every *quality* judgment and on the *recommendation
   to act*, not on the tier-2 signals.
5. **Writing-as-gap-generator** loop + **sources-gap reliability gate** via the Peer-reviewer
   lane (relevance is discovery's job; CEBM-level/source-type are tier-2 enum fields feeding
   impact, CRAAP is the tier-3 rubric — §11). Gap-pull ships as **on-demand find** via the
   existing Librarian (ADR-48); ADR-61's nightly cron is *not* a prerequisite (§11). Triage
   reliability by the impact view so it doesn't become its own treadmill.
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

This is a real shift, and the earlier draft framed it as a fork between "adopt ADR-61" and "ship
manual." **That fork is now resolved — toward neither extreme.** The key realization: the gate's
gap-pull needs *gap-triggered find* (on-demand, PI-initiated), which **already exists** via the
unified Librarian (the `find` capability is documented not in ADR-48's body but in ADR-37's
supersession note, where the Retriever/Scout split folded into the unified Librarian; it runs
under the L3 ceiling, ADR-21). It does **not** need ADR-61's autonomous *nightly cron*. So:

- **Ship now (no new ADR needed):** gap-pull as **on-demand find** — a high-impact sources-gap
  emits a `gap` card (ADR-51); the PI (or the Librarian on PI request) runs find against it.
  This is *theoretical sampling* (sampling driven toward the under-developed categories), and it
  works today.
- **Leave deferred:** ADR-61's nightly autonomous loop. **Do not accept it to unblock this gate**
  — its own adoption conditions are unmet (always-on deployment, `research-focus.md` maintained
  ≥4 weeks, a written `screening-plan.md`), and its `assumes: [34, 37, 21]` is **stale** (ADR-37
  was superseded by ADR-48). When ADR-61's conditions are met, the nightly loop becomes the
  *automated* feeder for the same `gap` cards — an upgrade, not a prerequisite. (Recommended
  side-fix, tracked separately: amend ADR-61's `assumes` 37→48. **Not in this change** — no ADRs
  touched here.)

Either way: **gap-pull and ambient discovery are complementary, not a replacement** — gap-pull
prioritizes the queue; ambient discovery is the serendipity channel (you don't want to only ever
find what you already knew you were missing).

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
  traversal (reachability, articulation points, linked-vs-convergent, degree). They require a
  deterministic **Operation** that traverses the relation graph and materializes derived values
  (`impact`, `on_path`, `saturation_state`, `graph_maturity`, `thesis_lifecycle`) for Bases to
  display and filter. Do not wait for native Bases relations.

  **This is net-new infrastructure, not "the same pattern as existing derived views" (correcting
  an earlier overclaim).** Nothing in Memoria today writes derived properties back onto
  existing-note frontmatter — the contradictions, drift, MOC-threshold, and knowledge-map views
  all render **read-only** or **emit a card**, and the standing discipline is "write notes once."
  Stamping computed props onto notes fits none of ADR-69's four operation categories and inverts
  that discipline. So this must be owned as a **first-class design decision**, with two rules:
  - **Write-only-on-change.** Re-stamp a note only when its value actually changes — never the
    whole component per gap-close. (ADR-25's append-only, hash-paired audit means a naïve
    re-stamp of a 20–40-note component per gap-close is real write amplification, §D4.)
  - **`computed_at` + visible staleness.** The Operation runs on-demand (on gap-close, a
    debounce, or PI request) and stamps `computed_at`; Bases has **no auto-refresh**, so the
    dashboard shows the timestamp and stale values read as stale. "Cheap to compute" is true; the
    persisted values are a **materialized cache with a real write cost** — not free, not silently
    current.

  **Open decision — per-note stamps vs. a single generated index-note (see §13.4).** The two
  materialization shapes trade off against each other; this is a genuine fork, not a settled call.

  **Can the Operation tell the PI to refresh? Yes — ambient, escalating to alert only on
  invalidation.** Three tiers, matching ADR-70's "ambient maintenance, not forced gates":
  1. **Dashboard `computed_at` + a refresh Button** (Buttons plugin is bundled, ADR-68) —
     PI-triggered recompute, fully within the L3 ceiling (ADR-21: on-demand is allowed; only
     *scheduled* ops are inbox-only). Recompute eagerly on gap-close where the traversal is cheap.
  2. **Ambient status-bar staleness badge** (the ADR-70 ambient-health pattern) — e.g. "map
     stale: 12 gap-closes since compute." The default; non-intrusive.
  3. **An `alert` card (ADR-51)** *only* when cached values are not merely stale but **wrong** —
     a structural invalidation like thesis supersession (§15) or a question-revision cascade (§7).
     Staleness ≠ urgency; reserve the loud channel for invalidation.

  The Operation never "pushes" — it writes a `stale: true` / `computed_at` derived property and
  the ambient UI reads it. Notification stays deterministic and inside the gate model.

**Where to build the surfaces:**

- Ship the map / argument-graph / impact dashboards as a **custom Bases view via the Bases API**
  (`registerBasesView`). Native, composable, and aligned with kepano's framing of Bases as "a
  visualization layer in service of editing Markdown" — Memoria's files-first philosophy exactly.
  **Verify before committing (§D3):** the dates and the API's existence/stability here are from
  web research, not the repo or first-hand knowledge, and the whole surface plan depends on
  `registerBasesView` being real and stable. Treat it like ADR-70's version-pinned pilot — pin and
  test the API before building on it. (The *data model* survives even if the view tech differs;
  only the rendering layer is at risk.)
- Use a **base-board–style Kanban** (Kanban-on-Bases) for **gap triage** (non-canonical cards by
  `impact` / status) — *not* for the thesis lifecycle (see the gating caveat).
- A **generated JSON Canvas** is a good *read-only* human-facing render of the argument map
  (claim → grounds → rebuttal), but Canvas is JSON and invisible to Operations — it is output,
  never source of truth.

**Gating caveat (load-bearing — corrected).** The earlier draft said drag-to-promote would "bypass
the policy MCP." That is the wrong protection: `policy_hook.py` gates **agent/Hermes** writes; a
**human** dragging a base-board card writes through Obsidian directly, and ADR-49's Linter monitor
catches it only **post-hoc** — it does not block. And for the PI specifically, promotion is not a
*security* bypass at all: the PI **is** the gate's authority (ADR-03 — canonical zones receive
human-approved content, and the human is the approver). The real risk is **ritual erosion** — a
one-gesture drag canonizes without the honesty-card review the gate exists to force. So the
constraint is precise: **a gated transition must route through the review step, never a column
drag.** A board over canonical zones may *display* lifecycle, but the move to `current` is a
reviewed action — which is exactly why the thesis lifecycle is **not** a draggable Kanban here.

**What to deliberately avoid:** the **task/deadline PM paradigm** (Tasks, Day Planner, the
Gantt-style Project Manager plugin; GTD next-action/context semantics) reintroduces the very
treadmill §5 was built to escape — it models work as deadline-driven task completion that never
knows it's *done*. Likewise **Johnny Decimal / rigid top-down address grids** are antithetical
to an emergent knowledge graph. Memoria should be **Zettelkasten-for-the-map, Toulmin-for-the-
argument** — never a to-do list.

---

## 13. Open decisions (the earlier "one knob" claim was wrong)

An earlier draft claimed "no architecture decision left open" with the maturity threshold as a
minor tuning knob. That was wrong on both counts. There are now **five** open decisions; the first
is **safety-critical**, and 13.4/13.5 are the two the reviewers left explicitly open.

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

**13.2 — Is `warrant` worth its cost? Recommendation: NOT in v1.** Net-new vocabulary against
ADR-8/52's deliberate minimalism, with real authoring burden (§6), and its tier-2 detector is a
gameable presence check. It is the single biggest labor sink in the design for the least
deterministic payoff, so the v1-cut (§19) drops it; revisit once a real project has proven the
cheaper pieces earn their PI labor.

**13.3 — The ADR-61 fork — RESOLVED (§11).** No longer open. Gap-pull ships as **on-demand find**
via the existing Librarian (ADR-48); ADR-61's nightly cron stays deferred and is *not* a
prerequisite. So this gate does not depend on accepting ADR-61. (The remaining ADR-61 item — a
maintenance fix to its stale `assumes` 37→48 — is tracked separately and is *not* part of this
design's critical path.)

**13.4 — Materialization: per-note stamps vs. a single generated index-note (§12).** How the
Operation persists `impact`/`on_path`/`saturation_state` for Bases to read. A real fork:

| | **Per-note stamps** (props on each claim/thesis note) | **Single index-note** (one generated file: claim → values) |
|---|---|---|
| **Pro** | Bases filters/sorts claims *natively* by `impact`/`on_path` — the whole reason §12 wanted write-back. | Honors "write notes once"; one file to write and stamp; near-zero write amplification; clean audit (§D4). |
| **Con** | Violates write-once; write amplification across the component per recompute (mitigated, not removed, by write-only-on-change); churns the ADR-25 audit. | Bases **cannot join** index→notes (no relations/rollups), so native per-claim filtering is **lost** — you must build a custom `registerBasesView` that reads the index. |

The catch: the index-note's con (needs a custom view) is **already paid** if you build the custom
Bases view §12 proposes for the map/argument-graph dashboards anyway. **Recommendation: index-note
*if* the custom view is being built regardless** (likely true) — you get clean writes for free;
fall back to per-note stamps only if you decide to lean entirely on stock Bases tables with no
custom view. Either way, **write-only-on-change** is mandatory.

**13.5 — How many gap kinds in v1? Recommendation: three, not two and not six.** The reviewers
proposed stripping to two (additive, conflict); §6 defined six (additive, fragility, conflict,
structural, unstated-warrant, refutation). The discriminator is **authoring cost**, not concept
count:

| Gap kind | v1? | Why |
|---|---|---|
| **Additive** | ✅ | free; missing-source/claim, already via ADR-51 `gap` cards |
| **Conflict** | ✅ | free; reads human-set `contradicts`, already via ADR-9 |
| **Fragility** | ✅ | **free — a degree query, zero PI authoring**; high diagnostic value. The reviewers' "two" drops this for nothing; keep it. |
| **Structural** | ⛔ | deterministic but niche (over-concentration); defer until a project shows the need |
| **Unstated-warrant** | ⛔ | needs `warrant` (13.2 = not in v1); gameable presence check |
| **Refutation** | ⛔ | folds into saturation condition 3 as a one-click stamp (§19), not a standing gap card |

So: **three free, deterministic, no-authoring gap kinds in v1**; the three authored/niche ones
unlock only after the §14 labor budget is met (§19).

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
- **Thesis supersession mid-project.** ADR-10 supersession applies to the `thesis` note itself:
  the PI may replace the anchor mid-inquiry. This is not a failure — it's a legitimate pivot — but
  it **re-roots the argument graph**, invalidating `on_path` / `impact` / `saturation` for the
  whole component and triggering the §7 cascade. Because old (`retracted`) and new (`provisional`)
  theses coexist during the handover, project status is *not* a clean read off a single field.

**Status rule (refinement).** Resolve the handover ambiguity with one rule:
**project status = the lifecycle of the *active, non-superseded* thesis.** The `retracted` old
thesis is provenance, not the anchor. The ADR should define re-rooting on supersession as a
first-class operation, even if v1 just forces a full recompute.

### Dry run: thesis supersession (worked example)

No `thesis` notes exist yet, so this is constructed — but it exercises the re-rooting and surfaces
the cost. Project `mhealth-adherence`; question stable; thesis **T1** "Reminder notifications
improve adherence" at `provisional`; argument graph G1 = 4 `supports` + 1 `contradicts`, all wired
to T1; impact/saturation computed, `computed_at` stamped, `graph_maturity` above threshold.

1. **Trigger.** A high-impact *refutation* gap closes: a CEBM Level-1 systematic review strongly
   contradicts T1. The PI judges T1 wrong as framed.
2. **Author T2** "Reminders improve adherence *only when paired with clinician follow-up*" — a new
   `thesis` note, `lifecycle: proposed → provisional`, `project: [[mhealth-adherence]]`.
3. **Supersede (ADR-10).** Set `T1.superseded_by: [[T2]]`, `T1.lifecycle: retracted`. T1 is **not**
   deleted — it's provenance, and its survived-then-refuted history is a real result (§4/§5).
4. **Invalidate.** The Operation detects the anchor changed → marks `on_path` / `impact` /
   `saturation_state` **stale** across the component and emits an **`alert` card** ("thesis
   superseded — argument-graph re-root required", §12 tier 3). It does **not** silently recompute
   correctness.
5. **Re-root with mark-don't-invalidate (the contradiction fix).** An earlier draft said edges
   "do not auto-carry — re-confirm each by hand," which **reimposed the exact sunk-cost trap §4
   exists to remove** (a pivot becoming a punishing re-wire). Resolve it with the doc's own §7
   pattern, applied to edges: **carry the former T1 edges forward as `stale`, and re-confirm only
   the on-path / high-impact ones, lazily, as the PI works.** Crucially, **stale edges are
   excluded from load-bearing math** (maturity, saturation, impact) until re-confirmed —
   otherwise T2 would falsely inherit T1's maturity and read as "done." With that rule the fresh
   T2 component sits **below the maturity threshold** until enough edges are re-confirmed → triage
   reverts to the **scope-overlap regime** (§8) and **saturation cannot fire** (§5). Correct: a
   just-pivoted thesis is not done, but the pivot is *cheap* — you re-confirm a handful of
   load-bearing edges, not the whole graph.
6. **Cascade (§7).** The T1-derived outline is marked stale/archived; a new outline derives from
   T2's graph as it re-wires.
7. **Status.** During handover both T1 (`retracted`) and T2 (`provisional`) exist → status reads
   the *active non-superseded* thesis = T2 `provisional` → "exploring/defending."

**What the dry run reveals (now folded in above):** (a) the explicit status rule; (b) re-rooting's
cost is bounded by **mark-don't-invalidate + lazy re-confirmation** — only on-path/high-impact
edges are re-checked, which is what keeps §4's "make falsification cheap" *true* rather than
contradicted by §15; (c) supersession is the mechanism that lets §4's "kill the thesis" be a
*pivot*, not a dead end.

---

## 16. Toulmin and the gap taxonomy are system-wide, not gate-only

Both borrowed models earn their keep beyond this gate — which is itself the argument for
documenting them as standalone concepts (§18), not burying them in a project-gate page.

**Toulmin / `warrant`:**
- **Every claim, not just theses.** The claim template's "Evidence" section *is* implicit
  grounds+warrant. An optional `warrant` field on the claim schema raises the whole knowledge
  base's defensibility.
- **Peer-reviewer lane (ADR-48).** Toulmin is a ready-made skeptic's checklist — warrant stated?
  backing? qualifier? an *addressed* rebuttal? — that operationalizes the "skeptical" posture.
- **Contradictions dashboard (ADR-9).** With warrants it can distinguish *grounds* conflicts from
  *warrant* conflicts (shared evidence, opposite inference) — a sharper synthesis prompt.
- **Writer lane.** Claim/grounds/warrant/qualifier/rebuttal is a prose scaffold; FAMA
  citation-checking is grounds-checking.

**The gap taxonomy (our synthesis, informed by the gap-taxonomy literature — §6):**
- **The `gap` Inbox card (ADR-51)** is today only "missing-source need." A `gap_type` field
  (knowledge / evidence / empirical / methodological / theoretical / population / contradictory)
  enriches gap triage *everywhere*, and surfaces gap kinds beyond this gate's set (methodological,
  theoretical, population).
- **`research-focus.md`'s "Synthesis gaps"** section and a future gaps dashboard become typed
  rather than freeform.

These are opportunities, not part of this gate's v1 — flagged so the gate's design choices are
reused deliberately elsewhere rather than reinvented.

---

## 17. `research-focus.md` stays — re-scoped, not replaced

`research-focus.md` (`src/research-focus.md`) is **program-level** steering across *all* projects:
the Librarian reads it at session start to weight discovery (ADR-23: program memory vs. project
working state). The project question is **one inquiry's** anchor. They are different layers — the
question does **not** replace `research-focus.md`; collapsing them would erase the portfolio layer.

Once projects are first-class, divide cleanly:
- **`research-focus.md` → the portfolio/priority layer** — which projects are active,
  cross-cutting priorities, what discovery weights globally.
- Its current **"Open questions"** and **"Synthesis gaps"** sections hold per-project content
  today; that **migrates into the project artifacts** (the question note and gap cards), leaving
  `research-focus.md` to either roll them up as an index or keep only genuinely cross-project items.

That re-scoping is an **ADR-23 amendment** (not made here — no ADRs touched).

---

## 18. Documentation & ADR plan (for implementation)

*Recorded here so the build has a map; none of this is executed in this change.*

**ADRs needed (Q3):**

| ADR | Action |
|---|---|
| **New — The Project gate** | Fills ADR-70's deferred alpha.4 slot; umbrella for the five artifacts. |
| **New — Argument graph + `warrant`** | `warrant` is net-new vs ADR-52's deliberate minimalism; keep it a separate, testable decision extending ADR-52. |
| **New — Thesis as a distinct note type** | Resolves the claim-born-current conflict (§4); touches ADR-50 / claim-gating invariants. |
| **Amend ADR-61** | Fix stale `assumes` 37→48. **Not** accept (§11). |
| **Amend ADR-68 / ADR-70** | They defer/replace the Project workspace; the new gate ADR supersedes that language. |
| **Amend ADR-23** | Re-scope `research-focus.md` vs the project question (§17). |
| **Amend ADR-62** | Add a deferred "Project-gate health" harness (PI-touch-count, saturation rate) — ties to §14. |

**Docs pages to add (Q5)** — house pattern: prose, 60–95 lines, `title`/`parent`/`nav_order`
frontmatter, markdown links whose text = page title (docs-doctor), citations via
`reference/bibliography.md` anchors:

- *Explanation* (new `explanation/projects/` domain): `README.md`, `the-project-gate.md`,
  `thesis-and-question.md`, `impact-and-saturation.md`.
- *Explanation* (`knowledge/` domain — turning the grounding appendix into real pages, Q9):
  `argument-graph.md` (Toulmin, two graphs, `warrant`, outline-from-argument),
  `research-gaps.md` (the gap taxonomy + Memoria's gap kinds), `saturation.md` (theoretical
  sufficiency, the three conditions, why structural is auditable).
- *Explanation* — **amend** `overview/intellectual-foundations.md`: add Toulmin as a foundational
  source **when the gate lands** (it documents what *is*); the gap taxonomy stays operational, not
  on this page (Q1).
- *Reference* — **amend** `bibliography.md` (Toulmin 1958, Glaser & Strauss 1967, Corbin & Strauss,
  Dey, Saunders 2018, Popper, PICO, FINER, CRAAP, CEBM; gap-taxonomy sources per §D2); note-type
  reference for `thesis` / `project`; new frontmatter fields (`warrant`; derived props
  `impact`/`on_path`/`saturation_state`/`graph_maturity`/`computed_at`; `gap_type`).
- *How-to*: `start-a-project.md`, `work-the-project-gate.md`, `supersede-a-thesis.md`; **amend**
  `run-the-weekly-review.md`, `find-new-sources.md`, `build-a-moc.md` to be project-aware.
- *Tutorial*: "a project from question to outline" (extends the existing series).

**Schemas/templates (src, not docs — normal maintenance):**
`.memoria/schemas/types/thesis.yaml` + `system/templates/thesis.md`; `…/project.yaml` + template +
`projects/<slug>/` scaffold; claim schema optional `warrant`; `gap` card `gap_type`; the derived
property fields.

**Verification preconditions (reviewer lower-priority flags — do before the relevant build/ADR step):**
- **§D1 — `find` lineage.** Cite ADR-37's supersession note (where Retriever/Scout folded into the
  unified Librarian) as the basis for on-demand find; ADR-48's body omits it (§11).
- **§D2 — citations.** Pin author/year/venue before anything enters `bibliography.md`:
  linked/convergent = Beardsley/Freeman (not van Gelder); confirm the Miles handout and
  Müller-Bloch; Toulmin / Dey / Saunders / Popper / PICO / FINER check out (§6, appendix).
- **§D3 — Bases facts.** `registerBasesView`, the core/GA dates, and plugin states are from web
  research, unverifiable from the repo and near the knowledge boundary. Verify the API exists and
  is stable before building the surface layer (mirror ADR-70's version-pinned pilot); the data
  model survives even if the view tech differs (§12).
- **§D4 — git churn.** ADR-25's append-only, hash-paired audit makes naïve per-component re-stamps
  real write amplification — the reason write-only-on-change (or the index-note, §13.4) is
  mandatory (§12).

---

## 19. Recommendation

**Verdict: the full design as specified is a NO-GO; a stripped core is a CONDITIONAL-GO.** The
adoption analysis (§14) is decisive: cost is **front-loaded** (warrants, gap cards, source gates
run from day one) while value is **back-loaded** (impact/saturation stay dark below the maturity
threshold — most of a small project's life), and MCP-only makes "agents propose, PI confirms" a
**serial promotion queue**, not a near-free mitigation. Driving one thesis to `current` is
realistically ~100–250 deliberate confirmations. For a solo PI who is also the sole reviewer,
shipping the full surface front-loads guilt-ledger labor before the deterministic payoff arrives.

### The v1 cut (smaller than the staged path below)

Ship the genuinely-novel deterministic value and nothing whose cost is unproven:

- **Spine + three concepts:** the `project` note, the `thesis` note + lifecycle, and the two-graph
  model with the **structural-impact view**.
- **Three gap kinds only** — additive, conflict, fragility (all free, zero PI authoring; §13.5).
  *Not* structural / unstated-warrant / refutation.
- **`warrant`: do not ship** (§13.2). Biggest labor sink, net-new, gameable.
- **Saturation: conditions 1–2 only.** Condition 3 becomes a **one-click PI-asserted "refutation
  sufficiency" stamp**, not a standing honesty-card nag. (Honest caveat: the stamp is itself
  gameable — it mitigates, doesn't solve, the unchallenged-thesis problem; an acceptable
  "trust the solo PI" choice for v1.)
- **Advisory items collapsed, uncounted, on-demand, and *hidden* (not greyed) below the maturity
  threshold** — so the dashboard never becomes a guilt ledger.
- **Instrument-as-gate:** commit a **PI-touch budget before launch** (§14 / ADR-62 harness).
  Gap-kind and `warrant` expansion **unlock only after one real project comes in under budget.**

### The staged path (for the core above)

1. **Correct, then decide.** This doc is corrected (thesis ≠ claim §4; status rule §15;
   mark-don't-invalidate pivot §15). Make the five §13 calls — note 13.2 (`warrant` = **not v1**),
   13.4 (materialization — **index-note if building the custom view anyway**), 13.5 (**three** gap
   kinds), 13.3 (resolved), and 13.1 (conservative maturity default, the safety switch).
2. **Write three ADRs, accept none of ADR-61.** Project gate; argument-graph (`warrant` documented
   but flagged post-v1); thesis-type. Amend ADR-61's `assumes` 37→48 as housekeeping only.
3. **Ship the deterministic spine** with write-only-on-change materialization and `computed_at`
   staleness; on-demand gap-pull via the existing Librarian. **Verify `registerBasesView` first**
   (§D3) — the data model survives even if the view tech differs.
4. **Keep the deferred pieces advisory/hidden** until the §14 budget is met: structural / warrant /
   refutation gaps, tier-3 semantic impact, PICO/FINER and CRAAP lenses.
5. **Defer automation entirely:** ADR-61's nightly loop, multi-thesis projects, and the system-wide
   Toulmin/gap-taxonomy reuse (§16) all wait for evidence the core earns its labor.

The throughline: **the gate's job is to know when to stop** — both per-project (saturation) and
per-feature (ship the auditable core, prove it earns its PI labor under an explicit budget, and
only then expand).

---

## Appendix — ADRs this gate reuses

- **ADR-70** navigation gates — the deferred Project-gate slot this fills
- **ADR-68** workspaces — Studio drafting surface, `research-focus.md` anchor
- **ADR-51** Inbox category & honesty cards — `gap` card (= sources-gap), arguments-for/against
- **ADR-61** nightly discovery loop (**deferred**) — *not* a dependency; gap-pull ships as on-demand find via ADR-48, ADR-61 is the later automation upgrade (§11)
- **ADR-48** unified Librarian — provides the on-demand find that gap-pull actually needs
- **ADR-23** scoped memory — `research-focus.md` (program layer) vs the project question (§17)
- **ADR-21** L3 autonomy ceiling — why on-demand find is allowed but autonomous loops are inbox-only
- **ADR-15** project membership from topic hint — scope / `project-hints` topics
- **ADR-10** claim supersession — derive state from structure; provisional → current/retracted
- **ADR-50** universal lifecycle & maturity — the thesis's lifecycle states
- **ADR-8 / ADR-52** typed relations / links-vs-relationships — the argument graph
- **ADR-9** contradictions dashboard (accepted; reads only human-set `contradicts`) — conflict gaps; project-driving is future intent, not existing wiring
- **ADR-19** MOC-threshold alert, **ADR-67** drift — the map's "open issues" panel
- **ADR-49** catalog in Bases — the map as a Base view layer
- **ADR-38** pre-file similarity, **ADR-53** pattern library — additive-gap detection
- **ADR-34 / ADR-07** code artifacts — the out-of-scope coding consumer
- **ADR-16** systematic review (adopt-on-demand) — the PRISMA screening funnel behind sources-gap
- **ADR-31 / ADR-49** native Obsidian MCP / catalog in Bases — the §12 integration substrate

## Appendix — external methodological grounding

- **Toulmin** (*The Uses of Argument*) — claim / grounds / **warrant** / backing / qualifier /
  rebuttal; the argument graph (§2), the warrant attribute, the unstated-warrant gap (§6).
- **Argument structure** — *linked* (co-premise / articulation point) vs *convergent* (independent)
  support; the structural-impact proxy (§5). Attribution: the linked/convergent taxonomy is
  **Beardsley (1950) / Freeman**, *not* van Gelder (who built argument-mapping pedagogy/software).
  Pin before citing.
- **Ahrens, *How to Take Smart Notes* / Zettelkasten / LYT (Milo)** — fleeting → literature →
  permanent → structure-note pipeline = Memoria's fleeting/source/claim/hub; bottom-up emergence
  and why it alone yields a survey (§2).
- **Glaser & Strauss / Corbin & Strauss; Dey; Saunders et al.** — theoretical saturation vs data
  saturation, theoretical sufficiency, theoretical sampling, the unprovability critique (§5, §11).
- **Popper** (falsifiability) — thesis corroborated by surviving refutation; saturation
  condition 3 and the refutation gap (§5, §6).
- **PICO / FINER** — answerability vs scope vs novelty for the question artifact (§7).
- **Research-gap taxonomy** — informs the gap kinds and the missing-vs-contested framing (§6, §16).
  Sources: D. Anthony Miles, *A Taxonomy of Research Gaps* (2017) — a **workshop handout, not
  peer-reviewed**; and Müller-Bloch & Kranz (2015). Neither is canonical and Miles does **not**
  supersede Müller-Bloch (different artifact types); **the missing-vs-contested split is this
  design's own synthesis.** Confirm author/year/venue before either enters `bibliography.md`.
- **CRAAP; primary/secondary/tertiary; CEBM levels of evidence** — the reliability gate and its
  feed into impact triage (§11).
- **PARA (Forte) / GTD (Allen)** — the *finishability* test (a project must be able to end) and
  the task/deadline paradigm deliberately **not** adopted (§12).
