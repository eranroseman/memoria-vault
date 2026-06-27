---
topic: decisions
id: 111
title: "Two-mode tutorial spine, seeded by a half-built corpus"
status: superseded
date_proposed: 2026-06-22
date_resolved: 2026-06-22
assumes: []
supersedes: []
superseded_by: [112]
nav_exclude: true
---

# ADR-111: Two-mode tutorial spine, seeded by a half-built corpus

This ADR records two coupled decisions about the onboarding tutorials: what the
tutorial **spine** is organized around, and how the one-sitting-vs-months problem is
solved with a **seeded completion corpus**. Both were rethought from the question
"what is a real Memoria use case?" rather than "what is the system's data model?"

## Context

The previous tutorials (`01-set-up-from-zero` … `07-find-new-sources`) walked the
note-type dependency graph in order: fleeting note → source → reading → claim → hub →
project → verify → discover. That was Memoria's internal data model, sequenced. The
step *titles* are already task-shaped, but the *spine* is the ontology, and two tells
give it away:

- **It starts on the fleeting note** — the system's cheapest object, not how a
  researcher actually enters. People arrive holding a paper they're reading or a thing
  they have to write; nobody arrives wanting to "create a fleeting note."
- **It is drawn as a line, but the system is a loop.** [The knowledge
  cycle](../explanation/knowledge/knowledge-cycle.md) is explicit that the cycle "is not
  a linear path"; `06` even names the "compounding loop." Real use is not one pass 1→7.

Stripped to user motivation rather than our nouns, Memoria has **one meta-use-case** —
sustain a months-to-years inquiry that *compounds* instead of decaying — which
decomposes into **two modes a researcher alternates between**:

- **Accumulate** (continuous, low-stakes per action) — turn what you read into durable,
  connected, traceable knowledge instead of a pile.
- **Produce** (periodic, high-stakes) — write something defensible from what you know.

Plus three jobs that serve the loop, not entered for their own sake: **stay honest**
(verify), **find the gaps** (discover), **don't rot** (maintenance the agent does). The
two failure modes named in [What Memoria is](../design/what-memoria-is.md)
— "capture without synthesis" and "synthesis without rigor" — are exactly these two
modes *decoupled*. The product is keeping them coupled.

**The methodology problem this raises:** done for real, the loop takes months, so a
one-sitting tutorial cannot reproduce the payoff — writing from a *dense* claim graph —
without pre-existing state. The two modes compress differently: Accumulate is a
**habit** (only a single rep is teachable; the months are its repetition), Produce is an
**event** (naturally sitting-shaped, but it needs accumulated state the day-one vault
does not have).

A [deep-research pass](#related) over four adjacent domains (PKM tools, sample-database
pedagogy, SaaS onboarding, learning science) converged on the resolution and is the
evidentiary basis for the decision below.

## Decision

Restructure the tutorials around the two modes, and resolve the months-vs-sitting
problem by shipping a **small, authored, deliberately half-built sample corpus that the
learner finishes** — completing it *is* the core Accumulate lesson.

### Spine (6 tutorials, was 7)

| # | Tutorial | Mode | What the learner does | Ends with |
| --- | --- | --- | --- | --- |
| 00 | Set up and pick your path | Setup | Install, keys, meet the Co-PI. A **labeled fork**: "start with your own source" **or** "load the sample vault" (half-built, neutral topic, skippable). Write a one-line Produce goal. | A working vault, a goal, optionally a sample to *finish* |
| 01 | Bring in your first source | Accumulate | Capture a real source of your own from scratch (the independent rep). Sample's worked source notes sit alongside as models. Fleeting note demoted to a one-paragraph aside. | Own Catalog entity + source note |
| 02 | Build claims and connect them | Accumulate | The transfer-fragile move, **faded in one tutorial**: *study* a worked claim+links → *finish* the sample's un-distilled claims and un-made links → *then* distill your own source and wire it into the existing cluster. | A cluster, partly completed and partly built — dense enough to write from |
| 03 | Draft a section from your claims | Produce | Open a Project, map the now-dense corpus, draft from your own + completed claims with bound citations. | The 00 goal, in cited prose |
| 04 | Verify it holds | Produce | Verification pass; read finding-first cards; fix or trust. | A draft you'd defend |
| 05 | Close the loop | Capstone | A **planted gap** the map/draft surfaces becomes a discovery that sends you back to Accumulate. Meet the weekly review. Archive the sample if desired — it drops out without breaking links. | A loop you keep turning; a clean handoff to your own vault |

### Seed-corpus rules

1. **Half-built by design** — ~5 of ~8 sources fully worked; ~3 left as completion
   problems (source present, claims/links missing). Finishing them is tutorial `02`.
2. **Authored from real, citable sources — never generated.** Neutral topic.
3. **Subgoals labeled, shapes varied** — each claim/link states what it is *for*;
   include a support, a contradiction, and an open-question across the sources, not
   identical paper→claim pairs.
4. **~8 sources / ~15 claims** — the "semi-realistic" band: not toy (understates the
   real effort), not large (a steep curve that blocks the payoff). Paired with an honest
   in-line line: *"this sample is weeks of reading compressed; you finish a few reps to
   learn the moves."*
5. **One planted gap** — a known hole the map/draft will surface, to fuel `05`.

### The months-long rhythm is not a tutorial

The tutorials teach the **moves** (compressed, one sitting). The real-time loop —
capture as you read, distill once ~10 sources accumulate, map/draft/verify when a
deadline appears, let gaps pull the next reading — lives in a separate **"Your first
month" practice guide** (how-to/explanation genre). Cramming the real timeline into a
by-doing tutorial is a genre mismatch.

## Consequences

- A shipped seed corpus becomes a **maintained artifact**: it drifts as the note schema
  / frontmatter / space layout change, and must be kept valid. It pays for itself by
  doubling as an end-to-end **test fixture** and a **demo**.
- Authoring ~8 real-sourced sources + ~15 claims is real one-time work; the half-built
  rule trims ~3 sources to completion stubs.
- Structural shape changes: entry flips fleeting→source · "your first note" folds to an
  aside · "build a reading batch" folds into `02` as technique · `06`/`07` become the
  Produce-rigor + loop-close capstone · **7 → 6**.
- The **provenance risk is mitigated structurally** by rule 2: because novices imitate
  the surface form they are shown, a faked/LLM-generated seed would model the exact
  anti-pattern the product exists to prevent (claims that don't trace). Authoring from
  real sources is non-negotiable, not a quality nicety.
- The **sample → own-vault handoff stops being a cliff**: the learner builds part of the
  seed, so the "is this fake or mine?" boundary dissolves.
- The seed does **double duty** — density for Produce *and* the planted gap for the
  loop-close — so one artifact carries two pedagogical jobs.
- Bounded by the **expertise-reversal effect**: heavy guidance helps novices but harms
  experienced learners, so the sample must stay **optional and skippable**, and the
  fade-to-own-data step is load-bearing, not decorative.

## When this matters

*(Proposed.)* Finalize when the alpha10 docs pass reaches the tutorials. The spine rests
on the current note-type model and four-space navigation staying stable — a change to
either reshapes it, which is why this is `proposed` rather than silently implemented.
The one open lever is the **seed topic**: it must be broadly legible (no domain jargon),
built from real open sources, and mildly contested (so the contradiction and the planted
gap are natural, not forced). Picking the topic is the long pole, because seed authoring
gates the `02`/`03` rewrites.

## Alternatives considered

**Keep the pipeline spine.** Rejected: it is the ontology sequenced — it starts on the
wrong object and draws a loop as a line, so it reads as a tour of five note types rather
than one researcher's work.

**No seed, or a toy seed (2–3 claims).** Rejected: the Produce payoff and the
"feel the density" lesson cannot land at one-session scale without pre-existing state;
toy data both understates the real effort and exercises nothing — the same gap the
Sakila/Northwind/Chinook teaching corpora exist to close (Dyer & Rogers, JISE 2015).

**A generated / LLM-authored seed.** Rejected: provenance *is* the product; because
learners imitate the form they are shown (Catrambone 1994; Robertson 2000), a faked seed
teaches fabrication of the exact thing the system prevents.

**A finished showcase seed the learner synthesizes beside.** Rejected: passive finished
examples do not secure transfer (the strong "just show a complete worked example" claim
was refuted 0–3 in the research pass); fading a worked example into a **completion
problem finished on the learner's own data** is what bridges to their messy reality
(Renkl & Atkinson guidance-fading; Paas 1992 completion problems).

**Make the months-long loop a tutorial directly.** Rejected: a habit cannot be taught
by-doing in a sitting — genre mismatch. It belongs in a practice guide.

## Related

- **Builds on:** [What Memoria is](../design/what-memoria-is.md) (the two
  failure modes), [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)
  (the loop, the six delegable tasks), and the current
  [Tutorials](../tutorials/README.md).
- **Implementation (follows acceptance + topic choice):** rewrite `docs/tutorials/`
  `00`–`05`, author the seed corpus, add the "Your first month" practice guide.
- **Research basis (deep-research pass, 2026-06-22):** worked-example & cognitive-load —
  [ACM ToCE 2025](https://dl.acm.org/doi/full/10.1145/3732791); subgoal/transfer-failure
  — [Catrambone 1994](https://link.springer.com/article/10.3758/BF03198399); fading &
  completion —
  [Renkl/Chen 2023](https://www.tandfonline.com/doi/full/10.1080/01443410.2023.2273762);
  expertise-reversal —
  [Kalyuga et al.](https://www.researchgate.net/publication/226748784_The_expertise_reversal_effect_and_worked_examples_in_tutored_problem_solving);
  sample-corpus pedagogy — [MySQL Sakila](https://dev.mysql.com/doc/sakila/en/),
  [Dyer & Rogers, JISE 2015](https://jise.org/Volume26/n2/JISEv26n2p85.pdf); empty-state
  vs sample-data UX —
  [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/).
- **Source discussion:** design session, 2026-06-22.
