---
title: How to query the vault
parent: Writing
---


# How to query the vault

Ask the vault a research question and get a cited synthesis — an answer-note with every assertion tagged to a source. Query is a read operation: it doesn't create claim notes; it produces a draft answer for your review.

## Which retrieval path?

Several retrieval surfaces overlap; pick by what you want *out*:

| You want… | Use | Output |
| --- | --- | --- |
| A cited written synthesis you'll verify and maybe keep | **Writer `query`** (this guide) | answer-note in `10-inbox/02-answers/` |
| To sharpen your *own* thinking by being questioned | **Socratic pane** (`Memoria: ask about this note`) | conversation, no file |
| A fast deterministic lookup of a known term or field | **Librarian `query`** | results in chat, no file |
| The notes most similar to one you're looking at | **Mapper `find related notes`** | top matches in chat, no file |

Rule of thumb: reach for **Socratic** when *you* should do the synthesizing; reach for **`query`** when you want the synthesis drafted for your review.

## Prerequisites

- At least a handful of ingested and classified sources in `20-sources/`
- The Writer (or Librarian) profile installed

## Steps

**1. Ask your question via the agent-client pane in Obsidian.**

Cmd-P → Memoria: ask a question (or open the ACP pane and switch to the Writer profile).

Type your question in natural language:

> "What predicts JITAI receptivity?"
> "What methods have been used to measure ecological momentary assessment compliance?"
> "Which papers contradict the claim that cognitive load reduces receptivity?"

**2. Wait for the synthesis.**

The Writer (or Librarian for retrieval-heavy queries) runs a hybrid keyword + dense search across claim notes, reference notes, and paper notes. Superseded claim notes (`superseded_by`) are excluded by default — the synthesis reflects current beliefs.

The result is drafted to `10-inbox/02-answers/` as an answer-note, each assertion tagged with `[@citekey]`.

**3. Open the answer-note and verify.**

Navigate to `10-inbox/02-answers/`. Open the new note. For each assertion:

- Check that the cited citekey actually supports the claim — open the source note and verify
- Edit any overreach (the synthesis may state something more strongly than the source warrants)
- Delete or rewrite anything that doesn't hold up

**4. Decide what to do with the verified answer.**

| Situation | Action |
| --- | --- |
| The answer represents a genuine new synthesis you'll cite later | Promote it: [write a claim note](../sources/write-a-claim-note.md) from it, then delete the answer-note |
| It's useful context for a specific writing project | Move it to `40-workbench/<project>/` |
| It answered a one-off question and you won't return to it | Delete it — answer-notes that aren't promoted surface in the weekly review after 90 days as stale |

## Via the CLI (alternative)

```bash
hermes -p memoria-writer chat -s draft
# then, in the session:
/draft "what predicts JITAI receptivity?" --mode query
```

Same result, different surface.

## Verify

- `10-inbox/02-answers/` contains the answer-note with `[@citekey]` tags
- Every assertion has been manually verified against its cited source
- The note has been promoted, moved, or deleted — not left indefinitely in the answers inbox

## Related

- Promote to claim note: [write-a-claim-note.md](../sources/write-a-claim-note.md)
- Weekly review (step 2 — unreviewed synthesis): [run-the-weekly-review.md](../maintenance/run-the-weekly-review.md)
- The profile running the query: [writer.md](../../explanation/profiles/writer.md)
- Query vs Socratic discussion: [socratic.md](../../explanation/profiles/socratic.md)
