---
title: "Tutorial 05: Synthesize toward a writing project"
parent: Tutorials
---

# Tutorial 05: Synthesize toward a writing project

**You will end with:** two or three claim notes distilled from your reading batch, a hub gathering them, and a corpus map from a delegated `map` task — the synthesis surface a writing project will stand on.

**Time:** 45–60 minutes.

**You will use:** Obsidian, your source notes from Tutorial 04, and the co-PI pane.

**Prerequisite:** [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) complete — several read sources with filled **Worth distilling** sections.

> **Honest scoping:** the full project workflow — `projects/` folders, the Project workspace, briefs and outlines — ships with **v0.1.2**. The `projects/` folder in your vault is empty until then. What exists *today*, and what this tutorial teaches, is the part that matters most anyway: claims and hubs, your durable synthesis layer, plus the `map` lane that tells you whether the corpus is ready to write from.

---

## Step 1 — Distill claims from your sources

Open the source notes from Tutorial 04 and re-read each **Worth distilling** section. Pick two or three assertions that are durable, surprising, or in tension with each other.

For each, create a claim note in `notes/claims/` from `system/templates/claim.md`:

```yaml
type: claim
lifecycle: current
maturity: seedling
sources: ["<citekey>"]
topics: [<your-topic>]
links:
  supports: []
  contradicts: []
```

- **Title:** the claim itself, one falsifiable sentence, in your words — not a paper's title.
- **Body:** the claim, the evidence (every line traces to a citekey in `sources` — the provenance guardrail), and connections in prose.
- **`maturity: seedling`** — maturity (`seedling → budding → evergreen`) tracks *development*, never trust. A seedling isn't a doubted claim; it's a young one ([Note types](../reference/note-types.md)).

If two of your claims relate, say so in `links:` — `supports` or `contradicts`. The contradictions are the valuable ones.

`notes/claims/` is a **review-gated zone**: agents can only *propose* writes there ([Why promotion is gated](../explanation/knowledge/promotion-model.md)). You write claims directly — they're yours.

---

## Step 2 — Gather them under a hub

When a topic has a few claims, give it a navigational home. Create a hub in `notes/hubs/` from `system/templates/hub.md`:

```yaml
type: hub
lifecycle: current
topic: <your-topic>
members: []
```

List your claim notes (and key sources) as `members`, and write a few lines of orientation in the body: what this cluster is about, what's settled, what's still fighting. A hub is the renamed MOC — the synthesis surface a future draft starts from. Like claims, hubs are review-gated and PI-authored.

---

## Step 3 — Delegate a map task

Now ask the system what your corpus actually covers. In the co-PI pane:

> "Map my corpus on `<your-topic>` — what do I have good coverage on, and where is it thin?"

The co-PI delegates a **`map`** task to the Librarian, whose map lane produces corpus and coverage views: how your sources and claims cluster, which sub-topics are dense, which are thin ([The Librarian](../explanation/profiles/librarian.md)). Results come back through the Inbox — a coverage read to act on, plus **`gap` cards** for the thin areas, each carrying the same honesty body as a candidate card.

Read the coverage view and decide: is any cluster dense enough to write from (a hub with several mutually linked claims is the tell)? Keep the gap cards — Tutorial 06 closes the loop on them.

---

## Step 4 — A preview of v0.1.2

When the Project release lands, the path from here continues inside `projects/`:

1. **Brief** — you state what you're writing and for whom.
2. **Relevance scan** — the map lane scopes your corpus against the brief.
3. **Canvas** — argument mapping on the claims you just wrote.
4. **Outline** — competing framings to choose between, drafted by the Writer.

Nothing you did in this tutorial is throwaway — claims and hubs are exactly the inputs that workflow consumes. Until then, draft in any editor you like, from your hub.

---

## What you have

- 2–3 claim notes in `notes/claims/` — falsifiable, sourced, `maturity: seedling`
- A hub in `notes/hubs/` gathering the cluster
- A corpus/coverage read from the `map` lane, and gap cards marking the thin spots

---

## What's next

[Tutorial 06: Verify and address gaps](06-verify-and-address-gaps.md) — put your claims in front of the adversarial lane, and watch gaps feed discovery.

---

← [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) · [Tutorial 06: Verify and address gaps](06-verify-and-address-gaps.md) →
