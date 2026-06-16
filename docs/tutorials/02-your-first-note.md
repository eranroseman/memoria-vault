---
title: "Tutorial 02: Your first note"
parent: Tutorials
---

# Tutorial 02: Your first note

**You will end with:** one fleeting note captured from the palette, understood field by field, and processed — distilled or archived, not left to rot.

**Time:** 10–15 minutes.

**You will use:** the Obsidian command palette (`Cmd+P` on Mac, `Ctrl+P` on Windows/Linux) and, optionally, the Co-PI pane.

**Prerequisite:** [Tutorial 01: Set up from zero](01-set-up-from-zero.md) complete.

---

## Step 1 — Capture a fleeting note

Think of something you noticed, read, or wondered about recently. One sentence is enough. ("Most interventions assume users are unmotivated, but they're actually just distracted.")

Press `Cmd/Ctrl+P` → type `capture fleeting` → select **Memoria: capture fleeting** → type your thought → Enter.

A new note opens in `notes/fleeting/`, timestamped, with your thought as the title. That's the whole capture — the point is zero friction between having a thought and having it on disk.

---

## Step 2 — Read the frontmatter

Your note's frontmatter looks like this:

```yaml
type: fleeting
lifecycle: proposed
origin: human
created: 2026-06-10
```

Three fields carry the meaning:

- **`type: fleeting`** — the lightest of the note types: a raw capture, one item per note, no quality bar. The full catalog: [Note types](../reference/note-types.md).
- **`lifecycle: proposed`** — every note in Memoria sits on the universal lifecycle chain. `proposed` means *awaiting your decision*. A fleeting note's chain is short: `proposed → archived`.
- **`origin: human`** — you wrote this. Agent-captured fleeting notes carry `origin: agent`, so you always know whose thought you're reading.

---

## Step 3 — Decide: distill or archive

A fleeting note is a queue item, not a home for an idea. It has exactly two futures:

- **Distill** — the thought is worth keeping. Restate it in durable form: usually a claim note later (Tutorial 05), or fold it into an existing note. The fleeting note then gets archived.
- **Archive** — the thought served its moment. Change `lifecycle: proposed` to `lifecycle: archived` and move on. Archiving is success, not failure; most captures should end here.

Not sure which? Open the Co-PI pane with the note active (it auto-attaches) and ask: *"Is there a durable claim in this, or should I archive it?"* It will question you — that sparring is its job — but the decision and the writing are yours.

For this tutorial, make the call now. If you distill, write the durable version somewhere real first; either way, set the fleeting note to `lifecycle: archived` when you're done.

---

## Step 4 — See where fleeting notes surface

You won't re-find fleeting notes by browsing. They surface on two tracking surfaces — `system/dashboards/fleeting.base` and the Friday weekly review — so unprocessed captures can't silently pile up; how the two work together as a triage queue is covered in [Triage fleeting notes](../how-to-guides/compile/triage-fleeting-notes.md).

Open `fleeting.base` now (its "To process" view). If you archived your note in Step 3, the view is empty — and *empty is the goal state*. A fleeting queue that converges to zero means the discipline is working.

---

## What you have

- One fleeting note in `notes/fleeting/`, captured in seconds
- Read literacy for the three fields that matter: `type`, `lifecycle`, `origin`
- The distill-or-archive habit, and the two surfaces that enforce it

---

## What's next

[Tutorial 03: Bring in a paper](03-bring-in-a-paper.md) — capture a real source, watch the ingest engine build its Catalog entry, and write your first source note.

---

← [Tutorial 01: Set up from zero](01-set-up-from-zero.md) · [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md) →
