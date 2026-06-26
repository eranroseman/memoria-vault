---
title: Draft with the Writer
parent: Project
nav_order: 5
---

# Draft with the Writer

Delegate prose and outline work to the Writer's **`draft`** lane. Drafting is human-led — the Writer turns your chosen framing and claims into candidate prose; the argument assembly, and every edit that matters, is yours. The Writer is a background lane: you never chat with it — use the direct palette command when the request is clear, or use the Co-PI to shape an unclear handoff before it becomes a board card.

## Prerequisites

- A chosen framing and the claims it stands on ([Frame a project](frame-a-project.md))
- A `projects/<slug>/` scratch folder — the Writer's write scope is `projects/`

## Steps

**1. Delegate a section.**

Use `Cmd/Ctrl-P` → **Memoria: draft section**, or ask in the Agent Client pane if you want help shaping the handoff. Name the section, the framing, and the working set:

> "Draft the introduction for `<deliverable>` from `projects/<slug>/chosen-framing.md`, using my claims on `<topic>`. Cite citekeys in-text."

The palette command prompts for the goal or outline ref; the Co-PI route delegates via `delegate_route_task` ([Hermes CLI](../../reference/hermes-cli.md)). Both paths validate the handoff against the Writer's lane ceiling and land a card on the board (see [Command palette](../../reference/obsidian-command-palette.md)).

**2. Know what the lane can and can't do.**

The Writer writes **only** under `projects/` — claims, hubs, catalog, and inbox are denied. Its external-API policy is `blocked`: it composes from the vault, never researches, so it can't cite a source you don't hold. One `running` card at a time keeps drafts in flight bounded ([Kanban board reference](../../reference/kanban-board.md)).

**3. Pick up the result.**

The task state appears in Inbox Activity. If the Writer requests review, a Needs me prompt links the draft location in `projects/<slug>/`. Open the draft and edit freely — the Writer's output is a starting point, never the deliverable.

**4. Don't draft past unsupported claims.**

If the prose asserts something with no current claim note behind it, stop: find
the source, write the claim, or cut the assertion. The Writer's search path hides
superseded claims by default; use them only when the task explicitly asks for
historical contrast. The verify lane will flag unsupported or stale claim reuse
anyway ([Verify and revise a draft](verify-and-revise.md)) — it's faster to
address now.

**5. Cite citekeys in-text.**

Keep citations in Pandoc form (`[@mamykina2010sense]`) so the export route renders the bibliography ([Export a draft](export-a-draft.md)).

**6. Iterate by new delegation, not by nagging.**

A rejected draft is not "redo it better" on the same card — delegate a corrected spec (the board archives the old card as superseded). Small fixes you just make yourself in the file.

## Verify

- The draft exists under `projects/<slug>/`, Activity no longer shows the task, and any review prompt is resolved
- Every substantive claim in the prose corresponds to a claim note; every citation is a citekey in your `.bib`
- `system/logs/audit.jsonl` shows the Writer's writes confined to `projects/`

## Related

- Previous step: [Frame a project](frame-a-project.md)
- Next step: [Verify and revise a draft](verify-and-revise.md)
- The spatial sketch behind the outline: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- The lane's posture and scope: [The Writer](../../explanation/profiles/writer.md)
