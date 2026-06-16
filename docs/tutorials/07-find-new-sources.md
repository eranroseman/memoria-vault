---
title: "Tutorial 07: Find new sources"
parent: Tutorials
---

# Tutorial 07: Find new sources

**You will end with:** a discovery run delegated through the Co-PI, a queue of honest candidate cards judged keep-or-skip, and new Catalog entries you didn't know to look for.

**Time:** 25–35 minutes.

**You will use:** the Co-PI pane and the Inbox.

**Prerequisite:** [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) complete — a few Catalog entries and source notes give discovery something to compare against.

Tutorials 03 and 04 brought in papers you already knew about; this is the other direction — the system surfaces papers you haven't met, grounded in what your vault already holds.

---

## Step 1 — Ask the Co-PI

Open the Co-PI pane and name the need in your own words:

> "Find sources on just-in-time interventions for physical activity — what am I missing?"

Phrase it as a research question, not keywords. Seed it however helps: "papers that build on `<citekey>`", "recent work that disagrees with my receptivity claims", "the foundational papers I skipped."

The Co-PI delegates a **`catalog`** task; the Librarian searches, compares hits against your Catalog so nothing you hold is resurfaced, and keeps discovery faithful and generous rather than an echo chamber ([The Librarian](../explanation/profiles/librarian.md)).

---

## Step 2 — Judge the candidates

**`candidate` cards** land in the Inbox (the **Needs me** view of `inbox.base`, in the Desk workspace), one per proposed source. Judge these candidate cards exactly as in [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md) — read `argument_against` and `certainty` first, then keep (set `lifecycle: current`) or skip (set `lifecycle: archived`). A discovery card reads like:

```yaml
action: "Catalog this paper and queue it for reading"
argument_for: "Directly tests the timing mechanism your three receptivity claims assume."
argument_against: "N=23, single lab; may not generalize beyond students."
what_tipped_it: "It's the only experimental test of the assumption in your corpus."
certainty: likely
```

Work the whole discovery queue in one batch sitting, not card by card — the discipline (and why) is in [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md). Kept papers join your reading queue via the ingest engine; skipping generously offered candidates is the system working, not failing.

Run discovery again whenever synthesis stalls — a hub that won't grow, a claim with one lonely source — and from any `gap` card you agree with. For the habit and keeping your research focus current, see [Find new sources](../how-to-guides/compile/find-new-sources.md).

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
