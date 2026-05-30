---
topic: workflows
---

# Fleeting triage

**Group.** Upstream
**Goal.** Keep `10-inbox/01-fleeting/` from silting up — every fleeting note is promoted or discarded, never left to rot.

Fleeting notes are raw captures (a Telegram `/fleeting` message, a quick idea typed in Obsidian). They are the one inbox folder with no agent owner, so triage is a human habit surfaced by a dashboard.

## Steps

1. The [`reading-pipeline`](../../../explanation/dashboards/reading-pipeline.md) / weekly review surfaces fleeting notes older than a few days.
2. Human reads each one and decides:
   - **Promote** to an `answer-note` or `claim-note` (it's a real idea worth keeping), or
   - **Attach** it to an existing note as context, or
   - **Discard** (capture served its purpose).
3. Promoted notes leave `01-fleeting/`; discarded ones are deleted.

## Owners

The **human** owns every decision here — fleeting triage is judgment, not automation. The Linter only *surfaces* stale fleeting notes (a data-hygiene check); it never promotes or deletes them.

## Related

- Note type: [vault/note-types.md](../../../reference/note-types.md) — `fleeting-note`.
- Dashboard: [reading-pipeline.md](../../../explanation/dashboards/reading-pipeline.md).
- Next stages: [classify](classify.md), [distill](distill.md).
