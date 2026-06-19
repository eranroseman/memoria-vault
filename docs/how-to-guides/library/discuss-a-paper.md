---
title: Discuss a paper
parent: Library
nav_order: 5
---

# Discuss a paper

Think a source through with the Co-PI before writing a claim. The Co-PI is the one conversational agent — a reflective thinking-partner that questions and pushes back; it is read-only ([The Co-PI](../../explanation/profiles/co-pi.md)), so the thinking and the eventual claim note are yours.

## Prerequisites

- A source you've read, with a source note in `notes/sources/` ([Capture and ingest a source](capture-and-ingest.md))
- The `agent-client` Obsidian plugin connected ([Agent-client pane](../using-obsidian/use-the-acp-pane.md))

## Steps

**1. Pick a source from the discuss queue.**

Open `system/dashboards/discuss-queue.md` — source notes at `lifecycle: provisional`, the read-not-yet-distilled stage where the discuss queue picks a note up ([Frontmatter fields](../../reference/frontmatter.md)). The Library gate surfaces this queue. Or just open the source note you want to think through.

**2. Orient yourself first.**

Re-read your **In my words** and **Worth distilling** sections, and keep `catalog/papers/<citekey>.md` open for the source metadata while you consult the paper/PDF if you need the full text. Bring a position, not a blank page.

**3. Open the Co-PI pane.**

Open the Co-PI pane (see [Agent-client pane](../using-obsidian/use-the-acp-pane.md)) with the source note active so it auto-attaches, then ask it to discuss the source.

**4. Work the standard questions.**

Good opening moves, whoever asks them first:

- What is the strongest single claim this paper makes?
- What does it connect to in your existing notes?
- What would falsify it?
- What is the smallest version of this idea that stands alone?

Answer in your own words, not the paper's.

**5. Follow where the dialogue leads.**

Don't treat the questions as a checklist. When a question feels too abstract, ask the Co-PI to ground it in a specific passage. When you disagree with the paper's framing, say so directly — the dialogue exists to surface *your* position, not to defend the author's. The conversation is done when you can state the paper's core claim in your own words and name where you stand on it.

**6. Decide the outcome.**

- **The paper yields one or more claims** → proceed to [write a claim note](../knowledge/write-a-claim-note.md), then advance the source note to `lifecycle: current`.
- **No standalone claim right now** → add one line to the source note's **Worth distilling** section saying why ("confirms existing claims, adds no new argument"), and advance the lifecycle anyway — the discuss queue reads `provisional`, and the decision is the work.

Closing the pane exports the transcript for later review ([Agent-client pane](../using-obsidian/use-the-acp-pane.md)). If the dialogue surfaced a durable insight, promote that insight yourself as a fleeting note, claim note, or source-note update.

## Verify

- The source note has moved off `lifecycle: provisional` and out of the discuss queue
- Nothing in the vault was edited by the agent — the Co-PI's write scope is empty; if you see an unexpected edit, treat it as a configuration error and check `system/logs/audit.jsonl`

## Related

**How-to**

- Previous step: [Classify a source](classify-a-source.md)
- Next step: [Write a claim note](../knowledge/write-a-claim-note.md)
- A named theoretical frame for the session: [Read a paper through a lens](read-through-a-lens.md)

**Reference**

- The full permission matrix: [Profile capabilities](../../reference/profiles.md)

**Explanation**

- The agent in the Co-PI pane: [The Co-PI](../../explanation/profiles/co-pi.md)
- The queue this works down: [The discuss-queue dashboard](../../explanation/dashboards/synthesis-agenda/discuss-queue.md)
