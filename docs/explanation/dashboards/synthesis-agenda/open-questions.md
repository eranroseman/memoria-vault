---
title: open-questions dashboard
parent: Synthesis agenda
nav_order: 3
grand_parent: Dashboards
---

# `open-questions` dashboard

Turns the vault into a research agenda by collecting every note that contains an explicit `## Open questions` section. Open it when planning the next reading direction — what questions has past synthesis raised that still haven't been answered?

## What it shows

All claim notes and paper notes that contain a `## Open questions` heading section, sorted by most-recently-modified. The dashboard doesn't extract the questions into a list — it shows which notes have them, so you navigate to the note and read the questions in context.

## Two source folders

The dashboard reads from `30-synthesis/01-claims/` and `20-sources/01-papers/`. These are where durable questions accumulate naturally. Project pages might also have open-questions sections, but those tend to be operational ("what should we do next?") rather than research-direction questions ("what's still unknown in the field?").

## What it is not

**Not a synthesizer.** It collects existing sections; it doesn't propose new questions, cluster them, or rank them by importance.

**Not a tracker.** There's no `resolved:` state. When a question gets answered, you manually remove or update the section. The dashboard reflects what's currently in the notes; it doesn't remember history.

**Not auto-resolving.** Nothing in the system reads these questions and attempts to answer them. The Librarian reads `research-focus.md` to guide discovery; open questions from the dashboard can inform what you write there.

## Why free-form section, not frontmatter

Questions are prose — often a paragraph with context and stakes. Constraining them to a flat `open_questions: []` YAML list would lose the framing that makes them worth revisiting. The cost is that the dashboard can't filter by question topic; it shows which notes have questions, not what the questions say.

## Works on day one

Any note with a `## Open questions` section appears immediately. No plugin, no log file, no schema required.

## Related

- [contradictions dashboard](contradictions.md) — closest sibling; both build the synthesis agenda (questions vs. tensions)
- Where the cycle is stuck: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- [Write a claim note](../../../how-to-guides/sources/write-a-claim-note.md) — where to put open questions in claim notes
- Where questions are generated: [Discuss a paper](../../../how-to-guides/sources/discuss-a-paper.md)
