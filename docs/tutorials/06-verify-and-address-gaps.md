---
title: "Tutorial 06: Verify and address gaps"
parent: Tutorials
---

# Tutorial 06: Verify and address gaps

**You will end with:** an independent verification pass over your claims, the finding-first cards it raises read and acted on, and your first full turn of the compounding loop — where a gap becomes the next discovery task.

**Time:** 30–45 minutes.

**You will use:** the Co-PI pane and the Inbox.

**Prerequisite:** [Tutorial 05: Synthesize toward a writing project](05-synthesize-toward-a-writing-project.md) complete — claims in `notes/claims/`, gap cards from the coverage pass in your Inbox.

---

## Step 1 — Ask for a verification pass

In the Co-PI pane:

> "Verify my claims on `<your-topic>` — check that each one is actually supported by its sources."

The Co-PI delegates the pass to the **Peer-reviewer** — the adversarial verify lane ([The Peer-reviewer](../explanation/profiles/peer-reviewer.md)). Its posture is *flag, don't fix*: it traces claims to their cited sources, checks citations, and hunts duplicates — and the only thing it can write is Inbox cards. It never edits your notes, and it is deliberately not the agent that gathered the evidence: the proposer and the checker are independent by construction.

You can point it at anything — one claim, a hub, a draft you wrote elsewhere.

---

## Step 2 — Read the flag cards

Open the **Inbox space** (the **Needs me** view). Findings land there as **`flag` cards**. Unlike a candidate's honesty body, a flag is **finding-first** — the `finding` leads, carries an `agent_recommendation`, and names its `target`; here the verdict is the point. Why a verification card leads with the finding: [The honesty card](../explanation/kanban-board/card-schema.md); the exact fields: [Frontmatter fields](../reference/frontmatter.md).

A `clean` flag closes nothing by itself and an `issues-found` flag changes nothing by itself — you act, the agent flags. Typical actions:

- **A claim's source doesn't say what the claim says:** revise the claim, or soften it and note the weakness in its body.
- **A citation issue:** fix the `sources` entry on the claim.
- **Inconclusive:** decide whether it's worth your own read; archive the flag either way once decided.

Resolve each handled flag from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. The Inbox converges to empty.

One verification runs without you asking: the retraction sweep checks Catalog DOIs and raises an `alert` card on a hit — [Run a retraction sweep](../how-to-guides/operate/run-a-retraction-sweep.md).

---

## Step 3 — Close the loop: gaps re-trigger discovery

Now return to the **`gap` cards** — from Tutorial 05's coverage pass, or raised by a verify pass that found a claim resting on thin evidence. A gap is a proposal ("your corpus is missing X") with the full honesty body. For each gap you agree with, hand it straight back:

> "That gap on `<sub-topic>` is real — find sources to fill it."

The Co-PI delegates discovery to the Librarian's catalog lane, candidates arrive (Tutorial 07), reading produces sources, sources produce claims, and the next coverage or verification pass finds the next gap. That's one full turn of the loop — why it compounds rather than just repeats: [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md).

Skip the gaps you don't buy — archive them with a clear conscience. The honesty body exists so you can disagree.

---

## What you have

- An independent verify pass over your claims, with each flag read and acted on
- The retraction sweep running on cron behind you
- At least one gap turned back into a discovery task — one full turn of the loop

> **Project-level verification:** once a cluster becomes a project, keep drafts in `projects/<slug>/` and verify them claim by claim against your vault before anything ships.

---

## What's next

[Tutorial 07: Find new sources](07-find-new-sources.md) — the discovery side of the loop you just triggered: how candidates are found, argued, and judged.

---

← [Tutorial 05: Synthesize toward a writing project](05-synthesize-toward-a-writing-project.md) · [Tutorial 07: Find new sources](07-find-new-sources.md) →
