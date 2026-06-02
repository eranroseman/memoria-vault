---
title: How to triage fleeting notes
parent: Sources
---


# How to triage fleeting notes

Clear the fleeting inbox: promote each note to something durable, attach it to an existing note, or discard it. Fleeting notes are raw captures — they have a short shelf life by design.

## Prerequisites

- At least one note in `10-inbox/01-fleeting/`
- Obsidian open (all steps are in the vault UI)

## Steps

**1. Open the Reading Pipeline dashboard.**

Cmd-P → Memoria: open reading pipeline (or navigate to `00-meta/01-dashboards/reading-pipeline.md`).

The dashboard surfaces fleeting notes older than a few days. Any note sitting in `01-fleeting/` beyond that threshold is stale capture.

**2. Open each fleeting note and decide its fate.**

For each note in the queue, choose one of three actions:

**Promote — it's a real idea worth keeping.**

If the note contains a distinct observation or argument:

- If it connects cleanly to an existing claim note: open the claim note and add the idea as a supporting point. Delete the fleeting note.
- If it could become a standalone claim: use it as a seed to [write a claim note](write-a-claim-note.md). Delete the fleeting note after the claim is written.
- If it's a question that deserves an answer: move it to `10-inbox/02-answers/` with `type: question-note`.

**Attach — it's context for something else.**

If the note is a reaction to a specific paper or project:

- Open the relevant source note or workbench note
- Add the content as a bullet or paragraph in the appropriate section
- Delete the fleeting note

**Discard — the capture served its purpose.**

If the note is a passing thought you no longer need, a duplicate of something you already have, or a reference you've already added to Zotero:

- Delete the file directly in Obsidian (right-click → Delete) or move to trash

**3. Confirm `01-fleeting/` is empty** (or contains only notes from the current session).

## Verify

- `10-inbox/01-fleeting/` has no notes older than a few days
- The reading pipeline dashboard shows zero stale fleeting notes

## Notes

The Linter flags stale fleeting notes but never promotes or deletes them — that decision is always yours. A rising count of stale fleeting notes in the weekly review is a signal to run this triage before the next session.

## Related

**How-to**

- Write a claim note: [How to write a claim note](write-a-claim-note.md)
- Weekly review (step 2 — unreviewed synthesis): [How to run the weekly review](../maintenance/run-the-weekly-review.md)
- Messaging gateway (how fleeting notes arrive): [How to set up the messaging gateway](../setup/set-up-messaging.md)

**Reference**

- Note types: [Note types](../../reference/note-types.md)

**Explanation**

- The fleeting note's role: [Note types and epistemic roles](../../explanation/knowledge/note-types.md)
- Triage as the first promotion decision: [Why promotion is gated](../../explanation/knowledge/promotion-model.md)
