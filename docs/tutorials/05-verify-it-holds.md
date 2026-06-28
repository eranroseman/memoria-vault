---
title: "Tutorial 05: Verify it holds"
parent: Tutorials
---

# Tutorial 05: Verify it holds

*Session 2 of 3 · Produce a cited section.*

**You'll finish with:** an independent verification pass over your draft, the findings it raises read and acted on, and a short section you would defend in front of someone who disagrees with you.

**Time:** 30–45 minutes.

**You'll use:** the Agent Client pane and the Inbox.

**Prerequisite:** [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) complete — a ~200-word draft under `projects/<slug>/` with in-text citekeys, and the gap card from the map kept in your Inbox.

Drafting got the words down; verifying asks whether they hold up. The point isn't to bless the draft — it's to put a deliberate skeptic between you and publishing, so the weak spots surface here instead of in front of a reviewer.

---

## Step 1 — Ask for a verification pass

Run `Cmd/Ctrl-P` → **Memoria: verify draft** with the draft as the active note, or ask in the Agent Client pane if you want help shaping the scope:

> "Verify `projects/<slug>/<section>.md` — check that every claim it makes is actually supported by its cited sources."

Either way, this hands a **verify** task to the **Peer-reviewer** — the background worker whose whole job is to challenge your draft ([The Peer-reviewer](../explanation/profiles/peer-reviewer.md)). Three things define it:

- **It flags, it doesn't fix.** The only thing it can write is Inbox cards. It never edits your draft — every change stays yours.
- **It's independent by design.** It is deliberately *not* the worker that gathered the evidence or wrote the prose. Whoever proposes and whoever checks are kept separate on purpose.
- **It traces, checks, and attacks.** It follows each claim back to its cited source, checks that the citations resolve, and hunts the argument for gaps and overreach.

If your runtime vault is a git repo, committing a changed project draft queues a verify pass automatically, so verification keeps up with your actual edits ([Verify and revise a draft](../how-to-guides/project/verify-and-revise.md)).

---

## Step 2 — Read the findings

Open **Maintenance** → **Drift watch**. Findings arrive as **flag cards**. A flag card leads with the finding itself: the `finding` comes first, the recommendation rides along in a separate `agent_recommendation` field, and the card names its `target`. Why a verification card is built this way: [The honesty card](../explanation/kanban-board/card-schema.md); the exact fields: [Inbox card fields](../reference/inbox-card-fields.md).

A `clean` flag closes nothing on its own, and an `issues-found` flag changes nothing on its own — **you act, the agent only flags.** Read each finding as a question about your draft, not a verdict on it.

---

## Step 3 — This is where the built-in tension shows up

The cluster you finished was never all agreement, and verification is what brings that out. Expect the Peer-reviewer to put its finger on the tension you wrote across:

| Finding | Why it matters | What to do |
| --- | --- | --- |
| Causal claim leans too hard | `observational-associations-confounded` warns that cohort signals may reflect a generally healthy lifestyle. | Make clear that the *trials* carry the causal reading, not the cohort data. |
| PREDIMED treated as clean | The 2013 report was retracted over randomization problems; the 2018 re-analysis is what left the result standing. | Name the caveat instead of hoping no reviewer knows it. |
| Claim rests on thin evidence | `meddiet-and-stroke-risk` or your own claim may rest on one source. | Say so, or add more support before leaning on it. |

This is the system working as intended: the tension was planted so verification has something real to catch. A draft that survives it is stronger than one that was never challenged.

---

## Step 4 — Fix or trust

Work each flag and resolve it. Typical actions:

- **A cited source doesn't say what the draft says:** revise the sentence, or soften it and acknowledge the weakness in the text.
- **An unsupported assertion:** add the citation, write the missing claim from a source you hold, or rewrite the line as explicitly your own view.
- **A real open question (the gap):** that's a *limitation, not a failure*. Name it in the draft's own words — "the evidence here is about high-risk Mediterranean populations" — archive the flag, and move on. The honest card exists precisely so you can disagree with the agent.

Resolve each handled flag from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. After revising, commit the draft again or send another pass over the same file — verify and fix is a loop, not a one-shot gate. The Inbox settles back to empty.

One check you never have to run yourself: a retraction sweep runs on a schedule in the background and raises an `alert` card if any of your DOIs has been retracted ([Run a retraction sweep](../how-to-guides/operate/run-a-retraction-sweep.md)) — fitting, since the PREDIMED retraction is part of this very corpus.

---

## What you have

- An independent verify pass over your draft, with each flag read and acted on
- A section that names its own seams — the confounding caution, the PREDIMED caveat, and the limit of who the evidence is about — instead of hiding them
- A draft you would defend: not because nothing could be said against it, but because the strongest things that *could* be said are already in the text

> **The gap is still open.** Verification confirmed the section holds for high-risk Mediterranean populations — and, with the map, that it says nothing beyond them. That open edge isn't a loose end; it's the start of the next turn. Keep the gap card.

---

## What's next

[Tutorial 06: Close the loop](06-close-the-loop.md) — let the gap your draft exposed become a discovery that sends you back to read again: one full turn of the loop.

---

← [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) · [Tutorial 06: Close the loop](06-close-the-loop.md) →
