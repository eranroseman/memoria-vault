---
title: "Tutorial 00: See what you're building"
parent: Tutorials
---

# Tutorial 00: See what you're building

**You will end with:** a project opened over a dense sample corpus, its coverage map read — a tight cluster of connected claims *and* the one gap it doesn't cover — and your goal named. You will have seen the destination before you build toward it.

**Time:** 20–30 minutes.

**You will use:** the Obsidian command palette and the Co-PI pane.

**Prerequisite:** a working vault with the Co-PI answering. If you don't have one yet, run the [Quickstart](../how-to-guides/setup/quickstart.md) first — installing Memoria is a one-time setup, not part of learning it.

---

Memoria is a loop, not a pipeline: you **accumulate** (turn what you read into durable, connected, traceable knowledge) and you **produce** (write something defensible from it). Built for real, a corpus dense enough to write from is weeks of reading — too long to wait before you see the point. So you start at the end: you open a project over a corpus that's *already built* and read its map, so you know the shape of what you're aiming at before you lift a finger to build it.

You do all of this in conversation with **one** agent, the **Co-PI**, in the Agent Client pane (`Cmd/Ctrl-P` → **Agent Client: Open chat view**). It questions your thinking and explains the system, and it delegates durable work to background lanes — but you never address a lane directly. Everything in these tutorials, you do with the Co-PI.

## Step 1 — Load the sample vault

Press `Cmd/Ctrl-P` → **Memoria: load sample vault**. It copies a small, labeled starter corpus on one neutral topic — **whether a Mediterranean diet protects the heart** — into your `catalog/` and `notes/`. Every note it adds is tagged `sample: true`, so it stays visibly separate from your own work, and you can retire it in one command when you're done (Tutorial 05).

The sample is **optional and skippable**: an experienced researcher with a paper already in hand can skip it and start from their own material in Tutorial 01. But it is what lets you reach the writing payoff *today* instead of after weeks of reading, so it is the recommended path — and it's the corpus the rest of this tutorial reads.

> One honest note: a cluster this dense is weeks of reading, compressed. It's a teaching scaffold. You'll finish a few of its deliberately-unfinished pieces to learn the moves, then repeat them on your own sources.

---

## Step 2 — Open a project and name your goal

A project is where producing happens — and opening one is how you name what you're producing *toward*. Run `Cmd/Ctrl-P` → **Memoria: start project** and fill the form: a title, a slug, the scope topic (Mediterranean diet and cardiovascular health), and the deliverable. For the deliverable, write the one concrete, defensible thing you want to be able to stand behind:

> *A verified 200-word section on whether a Mediterranean diet protects the heart.*

(If you skipped the sample to bring your own topic, write the equivalent for it — one writable deliverable, not a vague area like "learn about X.")

The command scaffolds `projects/<slug>/`. Open any file under it and run **Memoria: refresh project gate** — it reads your graph's maturity, saturation, and open gaps into `project-gate-index.md`. Full procedure: [Start a writing project](../how-to-guides/project/start-a-writing-project.md). This goal is the line you'll come back to in Tutorial 03 when you draft.

---

## Step 3 — Read the map

Now see what the corpus can support. Ask the Co-PI in its pane:

> "Map my corpus on Mediterranean diet and cardiovascular health — what does it cover well, and where is it thin?"

That raises a **`map`** task for the Librarian's map lane, which builds the typed graph and topic clusters and returns a coverage read through the **Inbox** ([The Librarian](../explanation/profiles/librarian.md)). Open the **Inbox space** → **Needs me** view and read it with the Co-PI narrating. You don't yet know how every piece was made — that's the next four tutorials — so let it give you the tour:

- **Each dot is a claim** — one defensible sentence that traces to a real paper. Open one (say `meddiet-reduces-major-cv-events`) and see: a single assertion, evidence lines that each cite a paper, typed links to its neighbors. That shape is what you'll learn to make.
- **They cluster** — most of these claims pull the same way: a Mediterranean diet lowers cardiovascular events, carried by two randomized trials and supporting cohort evidence. A dense, mutually linked cluster is the tell that you can *write* from it.
- **The cluster holds a tension on purpose** — one claim (`observational-associations-confounded`) cuts against the others, and a hub names where the evidence is strong versus where it's only suggestive. Disagreement is information, not a defect.
- **And it has a gap.** The map raises a **`gap` card** for what the corpus does *not* cover:

> "Corpus has no evidence on **primary prevention in low-risk people**, and nothing on whether the benefit **transports beyond Mediterranean populations and diets**." — carrying the same honest body a candidate card does.

**Keep that gap card.** It is not a flaw — it is the corpus telling you the truth about its own edges, and in Tutorial 05 it becomes the thing that sends you back out to read. Read coverage by *pattern*, not by counting; the full procedure is [Assess your corpus](../how-to-guides/project/assess-your-corpus.md).

---

## What you have

- A project under `projects/<slug>/`, its deliverable naming your goal
- A coverage map of a dense, writable corpus — and the **gap card** it surfaced, kept for Tutorial 05
- The vocabulary you'll build with — *claim, cluster, gap* — met in context, on a finished example, before you make your own

You have seen the destination. Everything from here builds toward it: you'll bring in a source of your own, distill and connect claims the way the sample models, draft your section, verify it, and close the loop.

---

## What's next

[Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) — capture a real source of your own, judge its candidate card, and write its source note in your own words.

---

[Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) →
