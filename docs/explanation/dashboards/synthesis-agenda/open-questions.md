---
title: open-questions dashboard
parent: Synthesis agenda
nav_order: 3
grand_parent: Dashboards
---

# `open-questions` dashboard

Turns the vault into a research agenda by surfacing the **unconnected claims** — `current` claim notes that no hub holds and nothing links to yet. Open it when planning the next reading direction — which claims has past synthesis raised that still haven't been woven into the rest of the corpus?

## What it shows

Every `current` claim note in `notes/claims/` with zero inbound links (`length(file.inlinks) = 0`), sorted oldest-first. These are the synthesis backlog: claims that stand alone, waiting to be connected to a hub or to other claims. The dashboard doesn't propose the connections — it shows which claims are stranded, so you navigate to each and decide where it belongs.

## One source folder

The dashboard reads from `notes/claims/` only. A claim with no inbound links is unconnected by definition; the sources that fed it are tracked separately by the reading-pipeline dashboard.

## What it is not

**Not a synthesizer.** It surfaces unconnected claims; it doesn't propose the links, cluster the claims, or rank them by importance.

**Not a tracker.** There's no `resolved:` state. When a claim gains an inbound link — a hub picks it up, or another claim references it — it simply drops off the list. The dashboard reflects current link state; it doesn't remember history.

**Not auto-resolving.** Nothing in the system links these claims for you. The Librarian reads `research-focus.md` to guide discovery; the unconnected claims surfaced here can inform what you write there.

## Why inbound-link count, not a prose section

An unconnected claim is one nothing points to — a fact the corpus has captured but not yet integrated. Measuring it by inbound-link count (`file.inlinks`) catches that structurally, without depending on the PI to hand-author a "## Open questions" section. The cost is that it surfaces *which* claims are stranded, not a prose statement of what's unknown.

## Works on day one

Any `current` claim with no inbound links appears immediately. No plugin, no log file, no schema required.

## Related

- [contradictions dashboard](contradictions.md) — closest sibling; both build the synthesis agenda (questions vs. tensions)
- Where the cycle is stuck: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- [Write a claim note](../../../how-to-guides/compile/write-a-claim-note.md) — where to put open questions in claim notes
- Where questions are generated: [Discuss a paper](../../../how-to-guides/compile/discuss-a-paper.md)
