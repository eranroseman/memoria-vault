---
title: "Tutorial 06: Verify and address gaps"
parent: Tutorials
---

# Tutorial 06: Verify and address gaps

**You will end with:** an independent verification pass over your claims, the finding-first cards it raises read and acted on, and your first full turn of the compounding loop — where a gap becomes the next discovery task.

**Time:** 30–45 minutes.

**You will use:** the co-PI pane and the Inbox.

**Prerequisite:** [Tutorial 05: Synthesize toward a writing project](05-synthesize-toward-a-writing-project.md) complete — claims in `notes/claims/`, gap cards from the `map` task in your Inbox.

---

## Step 1 — Delegate a verify task

In the co-PI pane:

> "Verify my claims on `<your-topic>` — check that each one is actually supported by its sources."

The co-PI delegates a **`verify`** task to the **Peer-reviewer** — the adversarial lane ([The Peer-reviewer](../explanation/profiles/peer-reviewer.md)). Its posture is *flag, don't fix*: it traces claims to their cited sources, checks citations, and hunts duplicates — and the only thing it can write is Inbox cards. It never edits your notes, and it is deliberately not the agent that gathered the evidence: the proposer and the checker are independent by construction.

You can point it at anything — one claim, a hub, a draft you wrote elsewhere.

---

## Step 2 — Read the flag cards

Findings land in the Inbox as **`flag` cards**. Unlike a candidate's honesty body, a flag is **finding-first** — here the verdict is the point ([The honesty card](../explanation/kanban-board/card-schema.md)):

- **`finding`** — what the check found, leading the card
- **`agent_recommendation`** — `clean` / `inconclusive` / `issues-found`
- **`target` / `citekey`** — what's being flagged

A `clean` flag closes nothing by itself and an `issues-found` flag changes nothing by itself — you act, the agent flags. Typical actions:

- **A claim's source doesn't say what the claim says:** revise the claim, or soften it and note the weakness in its body.
- **A citation issue:** fix the `sources` entry on the claim.
- **Inconclusive:** decide whether it's worth your own read; archive the flag either way once decided.

Set each handled flag to `lifecycle: archived`. The Inbox converges to empty.

---

> **The check you never run — the retraction sweep:** one verification runs without you asking. The installer wires a cron that refreshes the Retraction Watch dataset monthly and sweeps your Catalog DOIs against it (plus Crossref and Open Retractions); a hit raises a finding-first **`alert`** card in the Inbox ([Ingest routing](../reference/ingest.md)). Flag-don't-fix applies here too — the sweep never flips a note; you decide what a retraction means for the claims that cite it. Nothing to do but know it's running, so you're never the last to learn a source you cite was retracted.

---

## Step 3 — Close the loop: gaps re-trigger discovery

Now return to the **`gap` cards** — from Tutorial 05's map task, or raised by a verify pass that found a claim resting on thin evidence. A gap is a proposal ("your corpus is missing X") with the full honesty body. For each gap you agree with, hand it straight back:

> "That gap on `<sub-topic>` is real — find sources to fill it."

The co-PI delegates a **`catalog`** task, candidates arrive (Tutorial 07), reading produces sources, sources produce claims, the next map or verify pass finds the next gap. This is **the compounding loop**: mapping finds holes → discovery fills them → verification keeps the filling honest. Each turn makes the next one better targeted — the system gets more useful as the corpus grows, not noisier.

Skip the gaps you don't buy — archive them with a clear conscience. The honesty body exists so you can disagree.

---

## What you have

- An independent verify pass over your claims, with each flag read and acted on
- The retraction sweep running on cron behind you
- At least one gap turned back into a discovery task — one full turn of the loop

> **Coming in v0.1.0-alpha.3:** project-level verification — drafts in `projects/` checked claim by claim against your vault before anything ships.

---

## What's next

[Tutorial 07: Find new sources](07-find-new-sources.md) — the discovery side of the loop you just triggered: how candidates are found, argued, and judged.

---

← [Tutorial 05: Synthesize toward a writing project](05-synthesize-toward-a-writing-project.md) · [Tutorial 07: Find new sources](07-find-new-sources.md) →
