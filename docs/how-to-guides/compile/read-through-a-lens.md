---
title: Read a paper through a Socratic lens
parent: Compile
nav_order: 7
---


# Read a paper through a Socratic lens

A *lens* is a named theoretical frame the Socratic profile reads through. The same paper questioned through a *receptivity/timing* lens yields different questions than through an *equity/justice* lens — the lens supplies the framing, you supply the answers. This guide covers choosing a lens for a session, what a lens does and doesn't change, and adding your own.

## Prerequisites

- The Socratic profile installed
- A paper note (or a cluster of notes) open to read against
- Socratic is read-only and **interactive-only** — you invoke it synchronously; it is never queue-dispatched

## Steps

**1. Pick a lens that fits the question you're bringing.**

Choose by the question in your head, not by the paper on screen — the point of a lens is to read a familiar text through an unfamiliar frame. The palette commands below are *(deferred — use the Socratic ACP pane / terminal today)*; the lens slug is what you actually pass.

| Palette command | Lens slug | Frame it brings |
| --- | --- | --- |
| `Memoria: read through Mamykina lens` | `mamykina-sensemaking` | Sensemaking — how people interpret and act on information |
| `Memoria: read through Veinot equity lens` | `veinot-informational-justice` | Informational justice — who is served and who is left out |
| `Memoria: read through Design Justice lens` | `design-justice-costanza-chock` | Design justice — power, participation, and harm in design |
| `Memoria: read through JITAI lens` | `jitai-receptivity-timing` | Receptivity and timing — when an intervention can land |

**2. Open the session in that lens.**

Open the agent-client pane (`Agent Client: Open chat view`), switch to **Socratic** (via the pane’s profile picker) — the active paper note auto-attaches — and ask it to read through the lens by slug, e.g. «read this through the `mamykina-sensemaking` lens».

The `Memoria: read through <X> lens` palette command *(deferred — use the ACP pane / terminal today)* is not wired yet. From the terminal (fallback — full syntax in [Hermes CLI](../../reference/hermes-cli.md#socratic)):

```bash
hermes -p memoria-socratic chat -s lens-reading
# then load the lens by slug, e.g. mamykina-sensemaking
```

The `lens-reading` behavior provides the framing; you provide the questions through that frame.

**3. Stay in one frame per session.**

If a session is loaded with one lens, stay in it. Switching lenses mid-session muddies whose questions are being asked. For a different lens, start a new session — the discipline is one frame at a time.

**4. Read actively — the lens shapes questions, not answers.**

Socratic questions the text in front of you through the frame; it will not summarize your thinking back to you, fetch new context, or propose links. Nothing is written to the vault — the entire product is the conversation. The session logs to `99-system/logs/audit.jsonl` (the paper note, the lens, and the duration).

**5. Capture what the lens surfaced — yourself.**

Socratic can't write, by design. When the frame surfaces something worth keeping, author it in your own words in a fleeting or claim note (see [Discuss a paper](discuss-a-paper.md) and [Write a claim note](write-a-claim-note.md)). The lens did its job if you leave with a question or claim you wouldn't have reached unframed.

## Add a custom lens

**6. Define the framing.**

A lens is a named frame the `lens-reading` behavior provides. Add your framing to the Socratic profile's lens behavior with a new slug (kebab-case, e.g. `<author>-<concept>`). Keep it to the theoretical stance and the *kinds of questions* the frame privileges — not a summary of any one paper.

**7. (Optional) Register a palette entry.**

The lens is usable as soon as its slug ships — invoke it from the Socratic ACP pane by slug. If/when the `Memoria: read through <X> lens` palette commands are wired *(deferred today)*, add a single QuickAdd entry mapped to the new slug. See [Use the command palette](../using-obsidian/obsidian-command-palette.md) for the QuickAdd mechanics.

**8. Redeploy and test.**

Redeploy the Socratic profile so the updated skill ships ([Redeploy profiles](../maintain/redeploy-profiles.md)), then open a session in the new lens against a paper you know well to sanity-check that the framing produces the questions you intended.

## Verify

- The Socratic ACP pane accepts the lens slug and reads through that frame (or, once wired, `Cmd-P → read through` lists the lens command).
- A session opened in a lens stays in that frame and questions through it.
- `99-system/logs/audit.jsonl` records the session with the lens name.

## Related

- The workflow it anchors: [Discuss a paper](discuss-a-paper.md)
- Capturing the output: [Write a claim note](write-a-claim-note.md)
- Redeploy after adding a lens: [Redeploy profiles](../maintain/redeploy-profiles.md)
- Command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md); palette setup: [Command palette](../using-obsidian/obsidian-command-palette.md)
- The profile behind it: [The Socratic profile](../../explanation/profiles/socratic.md)
