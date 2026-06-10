---
title: "Tutorial 04: Build a reading batch"
parent: Tutorials
---

# Tutorial 04: Build a reading batch

**You will end with:** a reading queue of around five sources on one topic, built by delegation, and the habit of working it as **one worklist** — not card by card.

**Time:** 30 minutes to build the queue; reading time is yours, spread across sessions.

**You will use:** the co-PI pane, the Inbox, `sources.base`, and the reading-pipeline dashboard.

**Prerequisite:** [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md) complete.

---

## Step 1 — Ask the co-PI for a batch

Open the co-PI pane and name a topic — the same area as your Tutorial 03 paper. For example:

> "Build me a reading batch on notification receptivity — find the key papers and bring in the ones I should read. Mix foundational and recent; include something that might disagree with the rest."

The co-PI delegates one or more **`catalog`** tasks to the Librarian. You'll never see the Librarian directly — its work comes back as cards and Catalog entries.

You can also seed the batch yourself: capture papers you already know via **Memoria: capture from Zotero selection** or **Memoria: capture source from URL**, exactly as in Tutorial 03. Both routes feed the same queue.

---

## Step 2 — Judge the candidates as a batch

Candidate cards accumulate in the Inbox (`home.md` → **What needs me**), each with the honesty body from Tutorial 03. Sit down once and judge them together:

- Read each card's `argument_against` and `certainty` first.
- **Keep** the ones worth your reading time; **skip** (archive) the rest. Skipping is cheap — the cost of an over-inclusive candidate is exactly this one decision.

This is the batch discipline ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)): high-cardinality decisions belong in **one worklist worked in one sitting**, never N cards trickling at you. A queue you clear in a pass keeps your judgment sharp; a drip-feed trains you to wave things through.

For each kept paper, the Catalog entity already exists. Create its source note stub in `notes/source/` (frontmatter + empty sections, `lifecycle: proposed`) — or ask the co-PI to have stubs prepared for the keeps.

---

## Step 3 — Open your reading queue

Your queue is **not** the Inbox — candidates were a keep/skip decision; reading is a different kind of work, on a different surface:

- **`system/dashboards/sources.base`**, view **"To read & distill"** — every source note still at `lifecycle: proposed`, i.e. awaiting your reading.
- **`system/dashboards/reading-pipeline.md`** — the same queue plus your claims by maturity: the whole Library side at a glance.

The Library workspace (Tutorial 01) opens the reading pipeline in its left tabs — switch to it for reading sessions.

---

## Step 4 — Work the queue

For each source, the Tutorial 03 loop: read (the extract lives at `.memoria/data/extracts/<citekey>.md`), then fill the source note — **In my words**, **Worth distilling**, **Tensions**.

Batch habits that pay off:

- **Read in one topic, not round-robin.** By the third paper you'll notice agreements and tensions the first two hid — note them in each source's **Tensions** section.
- **Keep vocabulary consistent.** If you tag one source `research-area: receptivity-detection`, don't tag the next `opportune-moments` for the same concept ([Vocabulary discipline](../explanation/knowledge/vocabulary-discipline.md)).
- **Advance the lifecycle as you go.** A source you've read and distilled from moves off `proposed` — and off the "To read & distill" view. The queue converging to empty is the success signal.

Don't try to finish the batch in one session. The queue is durable; that's what it's for.

---

## What you have

- ~5 Catalog entities and kept candidates, judged in one sitting
- Source notes in `notes/source/`, filling in your own words as you read
- A reading queue in `sources.base` / the reading-pipeline dashboard that you work down as a batch
- A growing sense of where your sources agree and where they fight — fuel for the next tutorial

---

## What's next

[Tutorial 05: Synthesize toward a writing project](05-start-a-writing-project.md) — distill what you read into claims, gather them under a hub, and map your corpus.

---

← [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md) · [Tutorial 05: Synthesize toward a writing project](05-start-a-writing-project.md) →
