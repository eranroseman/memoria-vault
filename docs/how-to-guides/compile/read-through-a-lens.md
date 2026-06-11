---
title: Read a paper through a lens
parent: Compile
nav_order: 7
---

# Read a paper through a lens

A *lens* is a named theoretical frame the co-PI reads through. The same paper questioned through a *receptivity/timing* lens yields different questions than through an *equity/justice* lens — the lens supplies the framing, you supply the answers. Lens reading is the co-PI's `ask:read-lens` skill ([Hermes CLI](../../reference/hermes-cli.md#skill-names-the-taskverb-object-convention)); like everything at the desk, it is read-only and synchronous — never queue-dispatched.

## Prerequisites

- A source note (or a cluster of notes) open to read against
- The Agent Client pane connected ([Agent-client pane](../using-obsidian/use-the-acp-pane.md))

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

Open the Agent Client pane — the active note auto-attaches — and ask the co-PI to read through the frame by name:

> "Read this through a sensemaking lens."

The lens provides the framing; you provide the answers through that frame.

**3. Stay in one frame per session.**

Switching lenses mid-session muddies whose questions are being asked. For a different lens, clear the pane and start a new session — one frame at a time.

**4. Read actively — the lens shapes questions, not answers.**

The co-PI questions the text through the frame; it will not summarize your thinking back to you or write anything to the vault — its write scope is empty. The entire product is the conversation (which exports to `notes/fleeting/chats/` on close).

**5. Capture what the lens surfaced — yourself.**

When the frame surfaces something worth keeping, author it in your own words: a fleeting note (`Cmd/Ctrl-P` → **Memoria: capture fleeting**) or a claim note ([Write a claim note](write-a-claim-note.md)). The lens did its job if you leave with a question or claim you wouldn't have reached unframed.

## Add a standing lens of your own

A lens you reach for repeatedly is worth curating as a **pattern** — a typed prompt-transformation stored in `system/patterns/` ([ADR-53](../../adr/53-pattern-library.md)). Author the framing as a pattern note (the stance and the *kinds of questions* the frame privileges — not a summary of any one paper), set `lifecycle: current` when it's ready, and the co-PI can run it through the patterns MCP — typed, audited, and provenance-logged to `system/logs/patterns.jsonl`.

## Verify

- The session stays in the named frame and questions through it
- Nothing in the vault was edited by the agent (the co-PI is write-denied)
- Anything durable from the session exists as *your* note — fleeting or claim

## Related

- The workflow it anchors: [Discuss a paper](discuss-a-paper.md)
- Capturing the output: [Write a claim note](write-a-claim-note.md)
- Curated frames as data: [Note types](../../reference/note-types.md)
- The profile behind it: [The co-PI](../../explanation/profiles/co-pi.md)
