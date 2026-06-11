---
title: Query the vault
parent: Compose
nav_order: 5
---

# Query the vault

Ask the vault a research question and get a grounded answer in the co-PI pane. Query is a read operation — nothing is written; the v0.1.0 answer-note inbox is retired, and anything worth keeping you author yourself.

## Which retrieval path?

Several surfaces overlap; pick by what you want *out*:

| You want… | Use | Output |
| --- | --- | --- |
| A synthesized answer grounded in your notes | **Ask the co-PI** (this guide) | conversation in the pane |
| To sharpen your *own* thinking by being questioned | The co-PI's questioning posture — say "push back on this" | conversation in the pane |
| A written, citable synthesis to keep | Delegate a **`draft`** task | a draft in `projects/`, via the Inbox |
| A fast lookup of a known term or field | Obsidian search, or a Dataview/Bases view | results in the UI |

Rule of thumb: converse when *you* should do the synthesizing; delegate a draft when you want prose you'll verify and keep.

## Prerequisites

- At least a handful of classified sources and a few claims — retrieval needs something to retrieve
- The `qmd` search index current (the co-PI's vault search runs on it — [Rebuild the search index](../operate/rebuild-the-search-index.md) if results look stale)

## Steps

**1. Ask in natural language.**

Open the Agent Client pane and ask the question, not keywords:

> "What predicts JITAI receptivity?"
> "Which of my claims would the 2024 papers contradict?"
> "What methods have my sources used to measure EMA compliance?"

The active note auto-attaches; attach others via the paperclip when the question is about a specific cluster.

**2. Interrogate the answer.**

The co-PI reads the vault directly (hybrid keyword + vector search over `qmd`, plus the typed graph). Push on it: "which note says that?", "what disagrees with this?". An assertion it can't ground in a note of yours is its synthesis, not your knowledge — treat it accordingly.

**3. Keep what's worth keeping — yourself.**

- A genuine new synthesis → distill it properly: [Write a claim note](../compile/write-a-claim-note.md).
- Context for a writing project → copy into your `projects/<slug>/` scratch.
- A one-off answer → close the pane. The transcript auto-exports to `notes/fleeting/chats/` and surfaces in fleeting triage, so nothing silently rots.

## Verify

- Every assertion you kept traces to a note or citekey you checked
- Anything durable from the session exists as *your* note, not just a transcript

## Related

- Distilling a kept answer: [Write a claim note](../compile/write-a-claim-note.md)
- The transcript's afterlife: [Triage fleeting notes](../compile/triage-fleeting-notes.md)
- The search engine underneath: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- The agent across the desk: [The co-PI](../../explanation/profiles/co-pi.md)
