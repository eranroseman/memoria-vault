---
title: Draft with the Writer
parent: Compose
nav_order: 6
---

# Draft with the Writer

Delegate prose and outline work to the Writer's **`draft`** lane. Drafting is human-led — the Writer turns your chosen framing and claims into candidate prose; the argument assembly, and every edit that matters, is yours. The Writer is a background lane: you never chat with it — the co-PI delegates, the board dispatches, and the result resurfaces through the Inbox.

## Prerequisites

- A chosen framing and the claims it stands on ([Frame a project](frame-a-project.md))
- A `projects/<slug>/` scratch folder — the Writer's write scope is `projects/`

## Steps

**1. Delegate a section.**

In the co-PI pane, name the section, the framing, and the working set:

> "Draft the introduction for `<deliverable>` from `projects/<slug>/chosen-framing.md`, using my claims on `<topic>`. Cite citekeys in-text."

The co-PI delegates via `delegate_route_task` ([Hermes CLI](../../reference/hermes-cli.md)); the handoff is validated against the Writer's lane ceiling and the card lands on the board. (Palette twin: **Memoria: draft a section** — prompts for the goal or outline ref; see [Command palette](../../reference/obsidian-command-palette.md).)

**2. Know what the lane can and can't do.**

The Writer writes **only** under `projects/` — claims, hubs, catalog, and inbox are denied. Its external-API policy is `blocked`: it composes from the vault, never researches, so it can't cite a source you don't hold. One `running` card at a time keeps drafts in flight bounded ([Kanban board reference](../../reference/kanban-board.md)).

**3. Pick up the result.**

The done card surfaces in the Inbox with the draft's location in `projects/<slug>/`. Open the draft and edit freely — the Writer's output is a starting point, never the deliverable.

**4. Don't draft past unsupported claims.**

If the prose asserts something with no claim note behind it, stop: find the source, write the claim, or cut the assertion. The verify lane will flag it anyway ([Verify and revise a draft](verify-and-revise.md)) — it's faster to address now.

**5. Cite citekeys in-text.**

Keep citations in Pandoc form (`[@mamykina2010sense]`) so the export route renders the bibliography ([Export a draft](export-a-draft.md)).

**6. Iterate by new delegation, not by nagging.**

A rejected draft is not "redo it better" on the same card — delegate a corrected spec (the board archives the old card as superseded). Small fixes you just make yourself in the file.

## Verify

- The draft exists under `projects/<slug>/` and the done card is resolved
- Every substantive claim in the prose corresponds to a claim note; every citation is a citekey in your `.bib`
- `system/logs/audit.jsonl` shows the Writer's writes confined to `projects/`

## Related

- Previous step: [Frame a project](frame-a-project.md)
- Next step: [Verify and revise a draft](verify-and-revise.md)
- The spatial sketch behind the outline: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- The lane's posture and scope: [The Writer](../../explanation/profiles/writer.md)
