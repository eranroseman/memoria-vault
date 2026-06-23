---
title: Supersede a thesis
parent: Project
nav_order: 3.5
---

# Supersede a thesis

Pivot a project thesis without erasing the old argument trail. Supersession marks the old thesis as replaced, creates a proposed successor, and asks you to re-check the project gate instead of pretending the graph stayed valid.

## Prerequisites

- A project already exists under `projects/<slug>/`
- The current thesis note is open in Obsidian
- You have the replacement thesis as one sentence

## Steps

**1. Open the active thesis.**

Open the project from the Project space, then open the thesis named by
`active_thesis`. The command only runs from a thesis note in the project.

**2. Run the command.**

Use `Cmd/Ctrl-P` -> `Memoria: supersede thesis` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). Enter the replacement thesis as one sentence.

The command creates a new `projects/<slug>/thesis-<replacement>.md` note at `lifecycle: proposed`, sets `supersedes:` to the old thesis, sets `superseded_by:` on the old thesis, updates `project.md` so `active_thesis` points at the replacement, and raises an Inbox alert to re-confirm the argument graph.

**3. Refresh the project gate.**

Open the project from the Project space and run `Memoria: refresh project gate`. The refreshed `project-gate-index.md` recalculates impact, saturation, open risks, and on-path relations from the new active thesis.

**4. Triage the alert.**

Open the Inbox alert named for the thesis pivot. Treat it as a reminder to re-check high-impact links lazily as you keep working. Archive it only after the gate has been refreshed and any obviously stale on-path relations are corrected or captured as gaps.

## Verify

- The old thesis has `superseded_by:` pointing at the replacement
- The new thesis has `lifecycle: proposed` and `supersedes:` pointing at the old thesis
- `projects/<slug>/project.md` names the replacement in `active_thesis`
- `project-gate-index.md` was refreshed after the pivot
- The Inbox alert is resolved only after you have checked the gate

## Related

- Start point: [Start a writing project](start-a-writing-project.md)
- Gate refresh context: [Assess your corpus](assess-your-corpus.md)
- Draft verification after a pivot: [Verify and revise a draft](verify-and-revise.md)
- Thesis schema: [Note types](../../reference/note-types.md)
