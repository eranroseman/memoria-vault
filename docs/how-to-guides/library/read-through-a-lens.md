---
title: Read a paper through a lens
parent: Library
nav_order: 6
---

# Read a paper through a lens

Read a paper through a named theoretical frame so the Co-PI questions it from an angle you choose. This is one of the deliberate Co-PI-only cases: the synchronous, read-only dialogue is the product, so the `ask-read-lens` skill ([Hermes CLI](../../reference/hermes-cli.md#skill-names)) is never queue-dispatched. If the lens session should create a durable artifact, capture that artifact separately with the palette or a normal delegated card.

## Prerequisites

- A source note (or a cluster of notes) open to read against
- The [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) connected; this guide is intentionally conversational rather than a queued action

## Steps

**1. Pick a lens that fits the question you're bringing.**

Choose by the question in your head, not by the paper on screen — the point of a lens is to read a familiar text through an unfamiliar frame. Examples of frames worth naming:

| Lens | Frame it brings |
| --- | --- |
| sensemaking | How people interpret and act on information |
| informational justice | Who is served and who is left out |
| design justice | Power, participation, and harm in design |
| receptivity and timing | When an intervention can land |

**2. Open the session in that lens.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) with the source note active, and ask the Co-PI to read through the frame by name:

> "Read this through a sensemaking lens."

The lens provides the framing; you provide the answers through that frame.

**3. Stay in one frame per session.**

Switching lenses mid-session muddies whose questions are being asked. For a different lens, clear the pane and start a new session — one frame at a time.

**4. Read actively — the lens shapes questions, not answers.**

The Co-PI questions the text through the frame; it will not summarize your thinking back to you or write anything to the vault ([The Co-PI](../../explanation/profiles/co-pi.md)). The entire product is the conversation, which exports on close for review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**5. Capture what the lens surfaced — yourself.**

When the frame surfaces something worth keeping, author it in your own words: a fleeting note (`Cmd/Ctrl-P` → **Memoria: capture fleeting**) or a claim note ([Write a claim note](../knowledge/write-a-claim-note.md)). The lens did its job if you leave with a question or claim you wouldn't have reached unframed.

## Add a standing lens of your own

Curate a lens you reach for repeatedly as a **pattern** in `system/patterns/` ([ADR-53](../../adr/53-pattern-library.md)). Author the framing as a pattern note (the stance and the *kinds of questions* the frame privileges — not a summary of any one paper), then set `lifecycle: current` when ready. The Co-PI can then run it through the patterns MCP — typed, audited, and provenance-logged.

## Verify

- The session stays in the named frame and questions through it
- Nothing in the vault was edited by the agent (the Co-PI is write-denied)
- Anything durable from the session exists as *your* note — fleeting or claim

## Related

- The workflow it anchors: [Discuss a paper](discuss-a-paper.md)
- Capturing the output: [Write a claim note](../knowledge/write-a-claim-note.md)
- Curated frames as data: [Document types](../../reference/document-types.md)
- The profile behind it: [The Co-PI](../../explanation/profiles/co-pi.md)
