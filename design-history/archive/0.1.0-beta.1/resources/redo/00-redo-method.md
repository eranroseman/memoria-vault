# The alpha.16 design — governing method

> ## North star — every agent reads this first
> **Memoria is an opinionated, single-person knowledge-production tool. It is
> an AI-enhanced Zettelkasten utilizing the LLM-wiki framework.**
>
> This sentence is the identity of the system. It leads every redo agent's
> prompt, verbatim. A design decision that does not serve *opinionated,
> single-person, knowledge-**production**, ZK-native, LLM-wiki* is off-target,
> however technically elegant. beta.1's failure was elegance detached from this
> identity.

> ## Epistemic status — read this second (owner correction, 2026-07-05)
> **Nothing here is sacred. Not the owner's notes, not the ADRs, not even the
> mission statement.** Only **facts and solid reasoning** are authoritative.
> Every owner statement, alpha position, and beta.1 choice is a **prior to
> validate against facts**, never an axiom. Where this document attributes a
> position to the owner or a version, read it as "a claim to test," not "a
> truth to apply." (This corrects an earlier framing that called owner
> statements "design truths"; there are none.)
>
> **Mission (the one declared position — and even this, with a grain of salt):**
> Memoria is a tool that helps the user **read** (accumulate / compile / curate
> knowledge) and **write** (compose / create new knowledge), with **code and
> text as the main outputs.** Note the direct bearing on MVP scope: writing and
> coding are the *output half of the mission*, not peripheral.

Date: 2026-07-05. This note governs the beta.1 redo. It exists because the
original beta.1 design and everything built on it rest on a broken base.

## Why the redo

- `0.1.0-beta.1-design.md` is dated **2026-07-03**. The design-history
  reconstruction was **Assembled 2026-07-04** and states it "does not cover
  beta.1." **beta.1 was authored the day before the accumulated knowledge
  existed** — it was written blind, from the requirements charter plus ~380
  external papers, with the real accumulated learning demoted to §11
  "back-pressure."
- The dependency tower is therefore rotten at the base:
  `gap-adjudication.md → gap-analysis.md → beta.1-design.md → partial info`.
  The adjudication was rigorous but adjudicated a blind design against
  ADR-summaries.

## The target: design THE MVP (the complete beta.1), then sequence the alphas to it

**The design object is the MVP — the complete beta.1, defined by NO deferred
items** — the destination the whole alpha line aspires to. We **design the
destination first** (the owner's method: clean-slate from requirements + best
practice), then **sequence the increments** (alpha.16, .17 …) that reach it.
beta.1's error was the reverse: it shipped an increment full of deferrals while
calling it the destination. A design that defers is, by the owner's definition,
an alpha — so the flawed "beta.1" is really alpha.16-grade work, and the real
beta.1 is the no-deferrals MVP we now design.

The MVP design is built alpha.15-forward, using beta.1's knowledge (the three
pillars). Once it exists, **alpha.16 is scoped as the first increment toward
it** — and anything alpha.16 cannot yet deliver is a **tracked debt against the
MVP with a path to closure, never a silent deferral.**

**What "done" means for the MVP** (owner, 2026-07-05): the point where system
functionality is complete enough that **a real researcher can actually use it
on a real corpus, and the build-measure-learn feedback loop begins.** The MVP
is the *first usable product*, not a demo — "no deferred items" follows from
this, because core functionality stubbed cannot carry a real user or produce
honest feedback. This is the acceptance bar: every design decision is tested
against "does this get a real researcher to real, feedback-producing use."

**MVP scope is set by user NEED, not by deferral convenience** (owner,
2026-07-05). The failure mode — beta.1's, and agents' generally — is reading
MVP as "the least I can build; anything I can find an excuse to defer is out of
scope." **That is backwards. Everything the user needs for viable use is IN the
MVP; you minimize only by cutting what the user does NOT need.** To defer an
item you must *prove the user does not need it* for viable, feedback-producing
use — "it's a future consumer," "post-beta scope," "hard to build" are excuses,
not proofs. This is precisely why beta.1's deferrals were illegitimate: a
knowledge-**production** tool's user needs the argument graph, hubs, and claims
to produce knowledge, so they are MVP, not deferrable.

**What the no-deferrals beta.1 MVP contains** (owner's Round 2 definition): the
**basic knowledge cycle + the plugin, working end-to-end** — open a project
(question/thesis) → seed → **gap analysis over BOTH graphs** (sources and
notes, and the gap between them) → source to fill gaps → capture any digital
source (immutable raw + content + metadata) → extract atomic annotations →
**develop notes/claims toward the thesis** → re-run gap analysis. Therefore the
**argument/claims/notes graph and hubs are INSIDE the MVP** — the flawed beta.1
wrongly deferred them. **Writing and coding are the legitimately post-MVP
items** (owner: "their own agents," ~v0.3). The redo must tell these apart:
pull the core-cycle items (claims, hubs, gap-over-both-graphs) INTO alpha.16;
leave writing/coding as tracked, path-to-closure deferrals. *(Scope confirm:
this reading puts the knowledge cycle in the MVP and writing/coding after —
grounded in the owner's Round 2 note; owner to confirm.)*

## beta.1's actual failure mode (owner, 2026-07-05)

- **alpha.15 was an important RESET based on lessons learned. beta.1 was
  supposed to build on top of it — learn from it and improve it — not produce
  a technically brilliant clean-slate design.** beta.1 optimized for
  engineering elegance and lost the accumulated learning. That is the shape of
  the whole problem: real technical improvements, wrapped around misguided
  functionality that a from-scratch design reinvented instead of inheriting.
- **The accumulated knowledge WAS available to the beta.1 agents — and was
  dismissed as "historical artifacts."** (The design.md header says it
  outright: "Deliberately *not* extrapolated from the alpha implementation.")
  The assumed justification was that the new research had shown the old
  positions wrong. **After reading the research, the owner is not sure that
  justification holds.** So the redo does not take "the research superseded it"
  on faith: for **every** beta.1 divergence from the accumulated learning, the
  redo must show the *specific* new-research finding that justifies it — or the
  divergence was clean-slate dismissal, and alpha.15's position stands (this is
  the inverted burden, principle 1, made operational). This is exactly what
  Pillar 2's research agents are testing right now (applied-correctly vs
  misread vs not-applied).

**Reframing this forces: the redo is alpha.15-FORWARD, not another clean
slate.** beta.1's root error was making the charter + external literature the
base and alpha.15 the "back-pressure." The redo inverts that — **alpha.15's
reset (the encoded lessons) is the base; the new research refines it where it
genuinely earns a change; the charter scopes it; the owner's design philosophy
sets the intent.** "Redo from scratch" means rebuild the design correctly
grounded — NOT repeat beta.1's mistake of designing away from the history.

## The governing principles (owner, 2026-07-05)

1. **Inverted burden of proof.** The accumulated historic learning is
   authoritative *by default*. Where beta.1 diverges from it, **history wins
   unless the divergence is justified by new evidence.** This reverses the
   adjudication's implicit default ("beta.1 is right unless disproven"), which
   is exactly backwards. Every divergence must earn its keep against the
   record; silence defaults to the historic position, not to beta.1.

2. **beta.1 is not all regression — it has real value that must survive.**
   Two genuine contributions postdate the history and must be folded in, not
   discarded with the flawed base:
   - **New research** the project did not have before: the system-design
     research (`research-evidence.md`), the 210-finding information-flow
     research (`information-flow-research.md`), and the 380-paper adversarial
     review. Where this research is sound and correctly applied, it is new
     evidence that *can* justify a divergence from history (principle 1).
   - **Technical improvements**: concrete engineering advances beta.1
     introduced (single VaultWriter, the snapshot/apply/verify/commit batch
     protocol + revert, the local FTS5+sqlite-vec+ONNX stack, cost/breaker
     machinery, the exfiltration linter, the derived-store two-class split,
     staged writes). These are real and largely independent of the misguided
     functionality around them.

3. **Every beta.1 element sorts into exactly one of three buckets:**
   - **Technical improvement / correctly-applied new research → KEEP.**
   - **Misguided functionality → DROP** (no evidence supports it, or it
     contradicts historic learning with no new evidence to justify it).
   - **Misread research implication → FIX** (beta.1 had the research but drew
     the wrong design conclusion — keep the finding, correct the design).

4. **ADRs are reference, never justification.** An ADR number is a search key
   into the underlying failure/spike/incident; only that underlying evidence
   justifies a decision. Every design claim carries a citation into the
   historic records or the new research; unbacked reconstruction rationale is
   flagged, not trusted.

## The three-pillar evidence base (built before any redesign)

- **Pillar 1 — historic learning** (`redo/evidence-base/`): per subsystem, the
  trajectory, the earned lessons (what failed and why), the invariants that
  survived every reset, and what was genuinely open at alpha.15. Grounded in
  design-history + `sources/`, cited, verified. This is the base the redo
  builds forward from.
- **Pillar 2 — beta.1's genuine contributions** (`redo/beta1-contributions/`):
  the new-research findings with their *correct* design implications (flagging
  where beta.1 misread them), and the technical improvements sorted from the
  misguided functionality. This pillar carries the burden of justifying every
  beta.1 divergence from Pillar 1.
- **Pillar 3 — owner design philosophy + open questions** — the intent layer:
  what Memoria is *for* and the decision agenda. The authoritative record of
  design *intent* (not settled fact): where it states philosophy it governs
  direction; where it asks a question the redesign must answer or explicitly
  defer. **Canonical home: `design-history/sources/researcher-notes.md`** — the
  owner's round-by-round notes, already in `sources/` and cited by the history
  report. This is decisive for the diagnosis: **the philosophy was not missing
  from beta.1 — it was available in `sources/` and dismissed as a historical
  artifact.** (`redo/sources/owner-design-notes.md` is a 2026-07-05 re-emphasis
  the owner pasted, carrying the north-star sentence; it points back to the
  canonical file. **⚠ That paste was truncated inside the alpha.15 section;
  owner to re-paste the remainder.**) Core intent already captured:
  opinionated/personal/phase-gated durable research vault that *compounds*;
  knowledge *production* not storage; the catalog graph (objective) vs the
  ZK+Toulmin knowledge graph (subjective) with the source-note as the bridge;
  the entity-vs-note distinction as a named source of tension; the basic
  knowledge cycle as the definition of beta.1; gap analysis over *both* graphs
  and the gap between them; structural graph integrity over single-node
  semantic validity; propose-not-dispose + reasoning-shown guardrails;
  local-first as a constraint not a goal; ADRs written to enable retirement.

## Sequence

Pillar 1 (extracting) ∥ Pillar 2 (extracting) ∥ Pillar 3 (captured; awaiting
the rest) → **owner review of the consolidated three-pillar evidence base** →
the sort/adjudication under principle 1 (inverted burden), building forward
from alpha.15 → the corrected constraint set + the owner's decision agenda →
redesign on that base + charter scope + Pillar-3 intent → verify the new design
against all three pillars.

No redesign drafting happens until the evidence base is reviewed. The point is
to never again build on partial information, and never again to design *away*
from the accumulated learning.
