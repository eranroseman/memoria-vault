---
title: Discuss a paper
parent: Compile
nav_order: 6
---

# Discuss a paper

Think a source through with the co-PI before writing a claim. The co-PI is the one conversational agent — a reflective thinking-partner that questions and pushes back; it is **hard read-only**, so the thinking and the eventual claim note are yours.

## Prerequisites

- A source you've read, with a source note in `notes/source/` ([Capture and ingest a source](capture-and-ingest.md))
- The `agent-client` Obsidian plugin connected ([Agent-client pane](../using-obsidian/use-the-acp-pane.md))

## Steps

**1. Pick a source from the discuss queue.**

Open `system/dashboards/discuss-queue.md` — source notes at `lifecycle: provisional` (read, not yet distilled). The Library workspace opens it in its left tabs. Or just open the source note you want to think through.

**2. Orient yourself first.**

Re-read your **In my words** and **Worth distilling** sections, and skim the extract at `.memoria/data/extracts/<citekey>.md` if you need the full text. Bring a position, not a blank page.

**3. Open the co-PI pane.**

`Cmd/Ctrl-P` → **Agent Client: Open chat view** (or the ribbon icon). The active note auto-attaches as context. Ask it to discuss the source.

**4. Work the standard questions.**

Good opening moves, whoever asks them first:

- What is the strongest single claim this paper makes?
- What does it connect to in your existing notes?
- What would falsify it?
- What is the smallest version of this idea that stands alone?

Answer in your own words, not the paper's.

**5. Follow where the dialogue leads.**

Don't treat the questions as a checklist. When a question feels too abstract, ask the co-PI to ground it in a specific passage. When you disagree with the paper's framing, say so directly — the dialogue exists to surface *your* position, not to defend the author's. The conversation is done when you can state the paper's core claim in your own words and name where you stand on it.

**6. Decide the outcome.**

- **The paper yields one or more claims** → proceed to [write a claim note](write-a-claim-note.md), then advance the source note to `lifecycle: current`.
- **No standalone claim right now** → add one line to the source note's **Worth distilling** section saying why ("confirms existing claims, adds no new argument"), and advance the lifecycle anyway — the discuss queue reads `provisional`, and the decision is the work.

Closing the pane exports the transcript to `notes/fleeting/chats/`, where the sweep stamps it as a fleeting note — triage it later like any other ([Triage fleeting notes](triage-fleeting-notes.md)).

## Verify

- The source note has moved off `lifecycle: provisional` and out of the discuss queue
- Nothing in the vault was edited by the agent — the co-PI's write scope is empty; if you see an unexpected edit, treat it as a configuration error and check `system/logs/audit.jsonl`

## Related

**How-to**

- Previous step: [Classify a source](classify-a-source.md)
- Next step: [Write a claim note](write-a-claim-note.md)
- A named theoretical frame for the session: [Read a paper through a lens](read-through-a-lens.md)

**Reference**

- The full permission matrix: [Profile capabilities](../../reference/profiles.md)

**Explanation**

- The agent across the desk: [The co-PI](../../explanation/profiles/co-pi.md)
- The queue this works down: [The discuss-queue dashboard](../../explanation/dashboards/synthesis-agenda/discuss-queue.md)
