---
title: Query the vault
parent: Knowledge
grand_parent: How-to guides
nav_order: 7
---

# Query the vault

Ask the vault a research question and get a grounded answer in the Agent Client pane. Query is a deliberate Co-PI-only case because the product is synchronous, read-only dialogue: nothing is written, and anything worth keeping you author yourself. When you want a durable artifact instead of a conversation, use a direct command or delegated lane task.

## Which retrieval path?

Several surfaces overlap; pick by what you want *out*:

| You want… | Use | Output |
| --- | --- | --- |
| A synthesized answer grounded in your notes | **Ask the Co-PI** (this guide) | conversation in the pane |
| To sharpen your *own* thinking by being questioned | The Co-PI's questioning posture — say "push back on this" | conversation in the pane |
| A written, citable synthesis to keep | Delegate a **`draft`** task | a draft in `projects/`, via the Inbox |
| A fast lookup of a known term or field | Obsidian search, or a Dataview/Bases view | results in the UI |

Rule of thumb: converse when *you* should do the synthesizing; use a command or delegated lane task when you want a card, report, draft, or other durable output you'll verify and keep.

## Prerequisites

- At least a handful of classified sources and a few claims — retrieval needs something to retrieve
- The `qmd` search index current (the Co-PI's vault search runs on it — [Rebuild the search index](../operate/rebuild-the-search-index.md) if results look stale)

## Steps

**1. Ask in natural language.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) and ask the question, not keywords:

> "What predicts JITAI receptivity?"
> "Which of my claims would the 2024 papers contradict?"
> "What methods have my sources used to measure EMA compliance?"

The active note is passed as a readable reference; attach others when the question is about a specific cluster ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**2. Interrogate the answer.**

The Co-PI reads the vault directly and never writes (hybrid keyword + vector
search over Memoria's filtered `qmd` MCP, plus the typed graph — [The
Co-PI]({{ site.baseurl }}/explanation/profiles/co-pi.html)). Current retrieval excludes claim
notes that carry `superseded_by`; ask explicitly for historical/superseded claims
when you are reconstructing what changed. Push on it: "which note says that?",
"what disagrees with this?". An assertion it can't ground in a note of yours is
its synthesis, not your knowledge — treat it accordingly.

**3. Keep what's worth keeping — yourself.**

- A genuine new synthesis → distill it properly: [Write a claim note](../knowledge/write-a-claim-note.md).
- Context for a writing project → copy into your `projects/<slug>/` scratch.
- A one-off answer → close the pane. The transcript auto-exports for review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)); promote anything durable yourself instead of letting the raw transcript become a canonical note.

## Verify

- Every assertion you kept traces to a note or citekey you checked
- Anything durable from the session exists as *your* note, not just a transcript

## Related

- Distilling a kept answer: [Write a claim note](../knowledge/write-a-claim-note.md)
- The transcript's afterlife: [Triage fleeting notes](../inbox/triage-fleeting-notes.md)
- The search engine underneath: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- The agent in the Agent Client pane: [The Co-PI]({{ site.baseurl }}/explanation/profiles/co-pi.html)
