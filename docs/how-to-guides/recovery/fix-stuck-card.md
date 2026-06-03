---
title: How to fix a stuck card
parent: Recovery
nav_order: 2
---


# How to fix a stuck card

Resolve a Kanban card that won't advance — sitting in `running`, `ready`, or `blocked` without progressing.

## Detect

```bash
hermes kanban show <card-id>     # full state: status, retry count, blocker reason
hermes kanban list               # see if a queue is backing up behind one card
```

A stuck card shows one of three states:

| State | What it means |
| --- | --- |
| `running` long past expected completion | Worker crashed or hung mid-claim |
| `ready` never dispatched | Unresolvable `assignee` field |
| `blocked` | Hit `max_retries` — needs human decision before it can continue |

## Fix

**Card stuck in `running` (worker crashed).**

The dispatcher reclaims stale `running` claims automatically on its next tick and returns the card to `ready`. No manual intervention is needed for a first occurrence. Wait for the next tick (usually within 60 seconds).

If the card re-enters `running` and immediately stalls again, the problem is the prompt or tool, not the crash. Treat it as the `blocked` case.

**Card stuck in `ready` and never dispatched.**

Check the `assignee` field:

```bash
hermes kanban show <card-id> | grep assignee
```

The assignee must match a real lane name. If it doesn't, edit the card:

```bash
hermes kanban edit <card-id> --assignee memoria-librarian
```

If the card was created with an invalid lane, it will never be picked up — the dispatcher logs `skipped_nonspawnable` and leaves it in `ready`. Fix the assignee and the dispatcher will claim it on the next tick.

**Card stuck in `blocked` (hit max_retries).**

A blocked card needs a fix before re-queuing, not just a retry. Diagnose first:

```bash
hermes kanban show <card-id>
```

Read the `blocker_reason` and the `handoff_summary`. Then:

1. Fix the underlying problem (broken tool, malformed input, missing file)
2. Update the card's metadata if the payload was wrong:
   ```bash
   hermes kanban edit <card-id> --metadata '{"source": "corrected-citekey"}'
   ```
3. Unblock the card:
   ```bash
   hermes kanban unblock <card-id>
   ```

The unblock resets the retry count and returns the card to `ready`. If the same failure recurs, the prompt or tool is broken — archive rather than retry indefinitely.

**Archive an infeasible card.**

If the card represents work that genuinely can't be done (source no longer available, citekey doesn't exist, task was superseded):

```bash
hermes kanban archive <card-id> --reason "infeasible: source PDF no longer accessible"
```

## Verify

```bash
hermes kanban show <card-id>
```

Status has changed from the stuck state, or the card is archived with an explicit reason. No card should be silently sitting.

## Related

- Kanban board states reference: [Kanban board reference](../../reference/kanban-board.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- Retry pattern explanation: [Kanban board](../../explanation/kanban-board/README.md)
- The state machine explained: [Board states and the review gate](../../explanation/kanban-board/states.md)
