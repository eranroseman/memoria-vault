---
title: Triage fleeting notes
parent: Inbox
nav_order: 1
---

# Triage fleeting notes

Clear `notes/fleeting/`: promote each note to something durable, attach it to an existing note, or archive it. Fleeting notes are raw captures — they have a short shelf life by design, and the Linter's `stale-fleeting` detector flags anything older than 7 days.

## Prerequisites

- At least one note in `notes/fleeting/`
- Obsidian open (all steps are in the vault UI)

## Steps

**1. Open the fleeting queue.**

Open the Inbox queue (`spaces/inbox.md`) and use the **Fleeting notes** section. It embeds the **To process** view of `system/dashboards/fleeting.base`, which is the single queue for every fleeting note still at `lifecycle: proposed`.

**2. Open each fleeting note and decide its fate.**

**Promote — it's a real idea worth keeping.**

- If it connects cleanly to an existing claim: open the claim note and work the idea into its Evidence or Connections section. Archive the fleeting note.
- If it could stand alone as a claim: use it as the seed for [Write a claim note](../knowledge/write-a-claim-note.md), then archive the fleeting note.
- If it's a paper or source to chase: capture it (`Cmd/Ctrl-P` → **Memoria: capture source from URL**), delegate discovery (**Memoria: delegate task** → `catalog`), or ask the Co-PI to shape the search, then archive the fleeting note.

**Attach — it's context for something else.**

Open the relevant source note or hub, add the content where it belongs, archive the fleeting note.

**Discard — the capture served its purpose.**

Set `lifecycle: archived` (or delete outright — a fleeting note has no provenance value once judged).

**3. Confirm the queue is empty** (or contains only notes from the current session).

## Verify

- `notes/fleeting/` has no `proposed` notes older than 7 days
- The **Fleeting notes** queue in the Inbox is empty

## Notes

**Chat exports are adjacent, not automatic fleeting notes.** Closed pane sessions are auto-exported to `system/exports/` for PI review. They do not enter the fleeting queue automatically; when a transcript contains a durable thought, create the fleeting note yourself and link back to the export if the context matters. See [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md).

The Linter flags stale fleeting notes but never promotes or deletes them — that decision is always yours. A rising fleeting backlog in the Inbox is a signal to run this triage before the next session.

## Related

**How-to**

- Write a claim note: [Write a claim note](../knowledge/write-a-claim-note.md)
- Weekly review rhythm: [Run the weekly review](../inbox/run-the-weekly-review.md)
- Command-palette capture: [Obsidian command palette](../../reference/obsidian-command-palette.md)

**Reference**

- The fleeting type and its lifecycle subset: [Document types](../../reference/document-types.md)

**Explanation**

- The fleeting note's role: [Document types and epistemic roles](../../explanation/knowledge/document-types.md)
- Triage as the first promotion decision: [Why promotion is gated](../../explanation/knowledge/promotion-model.md)
