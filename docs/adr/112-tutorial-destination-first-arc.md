---
topic: decisions
id: 112
title: "Onboarding is one destination-first project arc"
nav_exclude: true
status: accepted
date_proposed: 2026-06-22
date_resolved: 2026-06-22
assumes: []
supersedes: []
superseded_by: []
---

# ADR-112: Onboarding is one destination-first project arc

This ADR redesigns the onboarding tutorials from first principles: learner
requirements, Diátaxis, and learning-science evidence for worked examples, guidance
fading, expertise reversal, and sample-corpus pedagogy.

## Context

The shipped tutorials were organized around the two modes a researcher alternates
between (Accumulate / Produce) and solved the one-sitting-vs-months problem with a
seeded half-built corpus. That shipped: tutorials `00`–`05`, the `sample-vault`
bundle, and the `Memoria: load/remove sample vault` commands are live on `main`.

Re-derived from scratch, two parts of the shipped tutorial design are **forced by real
constraints and kept**, and the rest is **challenged**:

- **Forced, kept:** the beat *order* capture → distill → draft → verify → loop is fixed
  by knowledge-cycle dependencies (no claim without a source, no draft without claims).
  The **seeded half-built corpus** is forced by the one-sitting-vs-months problem —
  without pre-existing state the payoff (writing from a dense graph) cannot land in a
  sitting.
- **Challenged:**
  1. **Setup lives inside the tutorial.** Install / keys / Obsidian / git has one right
     way and teaches no Memoria *idea* by doing — it is how-to, and Diátaxis says keep it
     out. Embedding it also duplicated the [Quickstart](../how-to-guides/setup/quickstart.md),
     and the two copies drifted (e.g. restart-Obsidian and git-init present in one, absent
     in the other).
  2. **Feature-tour framing.** "Learn six moves" is weaker motivation than "produce one
     real thing you wanted."
  3. **The two-mode concept as the *spine*.** Diátaxis is explicit that tutorials should
     not be organized around concepts; the concept is the *why* (explanation), the *doing*
     is the structure.
  4. **Bottom-up entry.** Starting on capture buries the motivation until the payoff three
     beats later.
  5. **A vague "close the loop" ending** instead of a concrete graduation into real use.

## Decision

Onboarding is **one deliverable-driven, destination-first project arc**: *from a working
vault to a verified, cited paragraph you'd defend, in one sitting.* Every beat is a
sub-task of that single artifact.

- **Setup is excluded** — the tutorial assumes a working vault with the Co-PI answering
  and links to the [Quickstart](../how-to-guides/setup/quickstart.md). (This dissolves the
  Quickstart ↔ tutorial duplication and its drift.)
- **The two modes are narrative, not spine** — their canonical home stays
  [What Memoria is](../design/what-memoria-is.md); the tutorial references
  the *why* but is structured by the *doing*.
- **The seeded half-built sample vault is retained** — and now earns a third job: it
  **enables the destination-first opening** (you cannot map an empty vault).

The seed has authored, real sources (target: about eight sources and fifteen claims),
prebuilt examples, half-built completion problems, a planted gap, and required
provenance. It is optional and removable, but when loaded it is not toy filler: it is
the worked example and faded practice surface that makes the one-sitting tutorial
possible.

### The arc

1. **Orient** — load the sample, open a project over it, and *read* the Co-PI's narrated
   coverage map: a dense corpus and its planted gap. Destination-first.
2. **Capture** — bring in one source of your own (provenance: catalog + source note in
   your words).
3. **Distill & connect** — the transfer-fragile move, faded: *study* a worked claim →
   *finish* the sample's half-built claim/link → *distill your own source, cold* (the link
   gate).
4. **Draft** — your paragraph from the now-denser corpus, citations bound. **The payoff
   lands here.**
5. **Verify** — trace it, read the argument (not a verdict), fix or trust.
6. **Close the loop** — the gap from beat 1 re-triggers discovery; it is a cycle, not a
   finish line. *(A tight beat — the *why* of graduation.)*
7. **Graduate** — `Memoria: remove sample vault`, import your own library, open your real
   project.

### Two design rules that make the arc work

- **Beat 1 is *read* the map, not *perform* mapping.** A novice cannot map concepts they
  have not met, but can be *shown* one — a narrated worked-example tour that introduces
  *claim / cluster / gap* in context at low load.
- **Beat 3 includes one rep of distilling the learner's *own* source.** Otherwise
  graduation (beat 7) is the first contact with their own material, and learning-science
  transfer requires the fade-to-own-data to happen *inside* the lesson. Graduation then
  *scales* (one source → a library), it does not introduce.

The months-long rhythm stays out of the tutorial; it belongs in a separate "Your first
month" practice guide.

## Consequences

- **The Quickstart/tutorial duplication disappears** — setup has a single home (how-to),
  and the drift it caused cannot recur.
- The arc is **shorter and deliverable-driven**: ~6–7 short beats (four *doing*, three
  *framing*) versus the old six feature-tutorials including setup.
- The seed now carries **three** jobs, not two: density for Produce, the planted gap for
  the loop, and the built corpus that makes destination-first possible on day one.
- The **graduation beat** gives `Memoria: remove sample vault` and the library import a
  natural home and ends the learner standing in their own project — the strongest point
  for activation and retention.
- This redesigns the **narrative arc and packaging only**: the sample vault, the
  load/remove commands, and the provenance discipline are reused unchanged.
- **Implementation (pending):** rewrite `docs/tutorials/` to the arc — setup leaves,
  orient/map opens, graduation closes; the existing `00`–`05` collapse and reframe.

## Alternatives considered

**Bottom-up order (capture first) — the shipped spine and the first cut of this redesign.**
Rejected: it buries motivation until the payoff. Opening with the map sells Accumulate via
the *visible gap* — something a from-scratch vault cannot do but the seed can.

**Bundle map + draft as one "Produce" beat.** Rejected: *map* is a survey move that belongs
early (orient), *draft* is a synthesis move that belongs after the learner has contributed;
conflating them mis-sequences the arc.

**Keep setup inside the tutorial.** Rejected: setup is how-to; embedding it
duplicates the Quickstart, and the duplicates drift in practice.

**Co-PI-guided onboarding instead of doc pages.** Deferred, not rejected — see
[ADR-113](113-copi-guided-onboarding.md). The doc arc is the script the agent layer would
later dramatize, so it must exist and stabilize first.

## Related

- **Deferred alternative:** [ADR-113: Co-PI-guided onboarding](113-copi-guided-onboarding.md).
- **Builds on:** [What Memoria is](../design/what-memoria-is.md),
  [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md), and the
  [Quickstart](../how-to-guides/setup/quickstart.md) (which now owns setup).
- **Research basis:** worked-example, guidance-fading, expertise-reversal, and
  sample-corpus pedagogy findings from the onboarding research pass.
- **Source discussion:** first-principles design session, 2026-06-22.
