---
title: "Tutorial 05: Verify it holds"
parent: Tutorials
---

# Tutorial 05: Verify it holds

**You will end with:** an independent verification pass over your draft, the finding-first cards it raises read and acted on, and a short section you would defend in front of someone who disagrees with you.

**Time:** 30–45 minutes.

**You will use:** the Co-PI pane and the Inbox.

**Prerequisite:** [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) complete — a ~200-word draft under `projects/<slug>/` with in-text citekeys, and the gap card from the map kept in your Inbox.

This is the second **Produce** tutorial. Drafting got the words down; verification asks whether they hold. The point is not to bless the draft — it is to put an *adversary* between you and shipping, so the weaknesses surface here instead of in review.

---

## Step 1 — Ask for a verification pass

Run `Cmd/Ctrl-P` → **Memoria: verify draft** with the draft as the active note, or ask in the Co-PI pane if you want help shaping the scope:

> "Verify `projects/<slug>/<section>.md` — check that every claim it makes is actually supported by its cited sources."

Either route creates a **`verify`** task for the **Peer-reviewer** — the adversarial verify lane ([The Peer-reviewer](../explanation/profiles/peer-reviewer.md)). Three things define it:

- **Posture: flag, don't fix.** The only thing it can write is Inbox cards. It never edits your draft — every change stays yours.
- **Independent by construction.** It is deliberately *not* the agent that gathered the evidence or wrote the prose. The proposer and the checker are different lanes on purpose.
- **It traces, checks, and red-teams.** It traces each claim to its cited source, checks the citations resolve, and hunts the argument for gaps and overreach.

For project drafts, committing the draft also enqueues a verify card automatically through the vault's `post-commit` hook — so verification tracks your actual edits ([Verify and revise a draft](../how-to-guides/project/verify-and-revise.md)).

---

## Step 2 — Read the finding-first cards

Open the **Inbox space** → **Needs me** view. Findings land as **`flag` cards**. Unlike a candidate card's honesty body, a flag is **finding-first**: the `finding` leads, the verdict rides in a separate `agent_recommendation` field, and the card names its `target`. Here the verdict is the point — why a verification card leads with the finding is in [The honesty card](../explanation/kanban-board/card-schema.md); the exact fields are in [Inbox card fields](../reference/inbox-card-fields.md).

A `clean` flag closes nothing by itself and an `issues-found` flag changes nothing by itself — **you act, the agent flags.** Read each finding as a question about your draft, not a verdict on it.

---

## Step 3 — This is where the built-in tension shows up

The cluster you finished was never all agreement, and verification is exactly what surfaces that. Expect the Peer-reviewer to put its finger on the seam you drafted across:

- **The causal claim leans harder than the evidence.** Your section says a Mediterranean diet *reduces* cardiovascular events. The standing counter-claim — `observational-associations-confounded` — cautions that cohort signals may be confounded by overall healthy lifestyle. A good flag asks: does your prose acknowledge that the *trials* are what let the causal reading survive the caution, or does it quietly borrow confidence from the cohort data the caution targets?
- **The trial evidence has a seam too.** If the draft cites PREDIMED (`[@estruch2018]`) as clean, a flag may surface `predimed-randomization-caveat`: the 2013 report was retracted over randomization deviations, and the 2018 re-analysis is what left the result standing. A section you would defend names that, rather than hoping no reviewer knows it.
- **A claim resting on thin evidence.** If your grounded `meddiet-and-stroke-risk` claim or your own claim carries a single source, the flag says so — that is the verify lane finding the same thinness the map did.

This is the product working: the tension was planted so that verification has something real to catch. A draft that survives it is stronger than one that was never challenged.

---

## Step 4 — Fix or trust

Work each flag and resolve it. Typical actions:

- **A cited source doesn't say what the draft says:** revise the sentence, or soften it and acknowledge the weakness in the text.
- **An unsupported assertion:** add the citation, write the missing claim from a source you hold, or rewrite the line as explicitly your own view.
- **A genuine open question (the gap):** that is a *limitation, not a failure*. Name it in the draft's own text — "the evidence here is about high-risk Mediterranean populations" — archive the flag, and move on. The honesty body exists so you can disagree with the agent.

Resolve each handled flag from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. After revising, commit the draft again or delegate another pass over the same file — verify ↔ fix is a loop, not a single gate. The Inbox converges to empty.

One check you never run: the retraction sweep runs on cron behind you and raises an `alert` card on a DOI hit ([Run a retraction sweep](../how-to-guides/operate/run-a-retraction-sweep.md)) — fitting, given the PREDIMED retraction is part of this very corpus.

---

## What you have

- An independent verify pass over your draft, with each flag read and acted on
- A section that names its own seams — the confounding caution, the PREDIMED caveat, and the limit of who the evidence is about — instead of hiding them
- A draft you would defend: not because nothing could be said against it, but because the strongest things that *could* be said are already in the text

> **The gap is still open.** Verification confirmed the section holds for high-risk Mediterranean populations — and, with the map, that it says nothing beyond them. That open edge is not a loose end; it is the start of the next turn. Keep the gap card.

---

## What's next

[Tutorial 06: Close the loop and make it your own](06-close-the-loop.md) — let the gap your draft exposed become a discovery that sends you back to Accumulate, and meet the weekly review that keeps the whole loop turning.

---

← [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) · [Tutorial 06: Close the loop and make it your own](06-close-the-loop.md) →
