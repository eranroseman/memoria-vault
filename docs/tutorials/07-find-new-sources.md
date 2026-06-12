---
title: "Tutorial 07: Find new sources"
parent: Tutorials
---

# Tutorial 07: Find new sources

**You will end with:** a discovery run delegated through the co-PI, a queue of honest candidate cards judged keep-or-skip, and new Catalog entries you didn't know to look for.

**Time:** 25–35 minutes.

**You will use:** the co-PI pane and the Inbox.

**Prerequisite:** [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) complete — a few Catalog entries and source notes give discovery something to compare against.

---

## Why this tutorial

Tutorials 03 and 04 brought in papers *you already knew about*. This is the other direction: the system surfaces papers you haven't met, grounded in what your vault already holds. You ran one targeted form of this in Tutorial 06 when a gap card became a discovery task; here you drive it directly.

---

## Step 1 — Ask the co-PI

Open the co-PI pane and name the need in your own words:

> "Find sources on just-in-time interventions for physical activity — what am I missing?"

Phrase it as a research question, not keywords. Seed it however helps: "papers that build on `<citekey>`", "recent work that disagrees with my receptivity claims", "the foundational papers I skipped."

---

> **Behind the pane:** the co-PI delegates a **`catalog`** task; the Librarian searches across 20+ databases, compares hits against your Catalog so nothing you hold is resurfaced, and reserves at least 20% of intake for serendipitous sources so discovery stays *faithful and generous* rather than an echo chamber ([The Librarian](../explanation/profiles/librarian.md)).

---

## Step 2 — Judge the candidates

**`candidate` cards** land in the Inbox (`home.md` → **What needs me**), one per proposed source, each carrying the honesty body — an argument, not a verdict. A real one reads like:

```yaml
action: "Catalog this paper and queue it for reading"
argument_for: "Directly tests the timing mechanism your three receptivity claims assume."
argument_against: "N=23, single lab; may not generalize beyond students."
what_tipped_it: "It's the only experimental test of the assumption in your corpus."
certainty: likely
```

Why a card argues instead of ruling: [The honesty card](../explanation/kanban-board/card-schema.md); the exact field set: [Frontmatter fields](../reference/frontmatter.md). There is no verdict field — the card existing *is* the recommendation, so the verdict would be noise. Read `argument_against` and `certainty` first; they're what make this a real decision instead of a rubber stamp. Then, as one batch sitting (Tutorial 04's discipline):

- **Keep:** the ingest engine builds the Catalog entity and the paper joins your reading queue — the Tutorial 03 flow from here.
- **Skip:** set the card to `lifecycle: archived`. Skipping generously offered candidates is the system working, not failing.

---

---

## Making it a habit

Discovery isn't a one-off run; it's the intake side of the loop you closed in Tutorial 06. Run it **when synthesis stalls** — a hub that won't grow, a claim with one lonely source — and **from gaps**, since every `gap` card you agree with is a pre-written discovery prompt. Keep your **research focus** current (`research-focus.md` at the vault root); the Librarian reads it to aim discovery.

As the corpus grows, comparison gets sharper: discovery surfaces less of what you have and more of what you lack.

---

## What you have

- A discovery run from a plain-language question — no search syntax, no terminal
- A judged candidate queue: kept papers in the Catalog and reading queue, skips archived with a clear conscience
- The complete v0.1.0-alpha.2 loop in hand: capture → catalog → read → distill → map → verify → discover → repeat

---

## Where to go from here

You've completed the tutorial sequence. The [How-to guides](../how-to-guides/README.md) cover each recurring task in more depth — and [Run the weekly review](../how-to-guides/curate/run-the-weekly-review.md) is the Friday ritual that keeps the queues honest. The [Reference](../reference/README.md) section is where you look up the exact field, command, or schema.

---

← [Tutorial 06: Verify and address gaps](06-verify-and-address-gaps.md)
