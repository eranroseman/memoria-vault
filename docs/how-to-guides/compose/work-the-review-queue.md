---
title: Work the review queue
parent: Compose
nav_order: 8
---


# Work the review queue

When an agent finishes a task that writes to a review-gated zone (`30-synthesis/01-claims/`, `02-reference/`, `03-moc/`, or `50-deliverables/`), its card lands in `done` with `review_status: requested` and **blocks** — the write is held in `dry_run` until you decide. This guide is how you, the human, clear that queue: inspect each card, then approve (let the write land) or reject (nothing lands, and you choose what happens next).

## Prerequisites

- The board exporter (`board_export.py`) running, so the dashboards reflect the live board
- At least one card in `done` with `review_status: requested`
- A working grasp of the review-state model — see [Review as a first-class state](../../explanation/workflows/review-as-state.md)

## Steps

**1. Open the review queue.**

From `home.md` — the front-door note that opens on startup — go to the **board-state dashboard** (`00-meta/01-dashboards/board-state.md`). The review queue is every card in `done` whose `review_status` is `requested`; the dashboard surfaces them under the review-queue count. For dashboard navigation see [Navigate the dashboards](../using-obsidian/navigate-the-dashboards.md).

**2. Inspect one card.**

Each card shows the **assignee** (which lane produced it), the **`agent_recommendation`** (`clean` / `issues-found` / `inconclusive`), and a summary of the proposed write. For a synthesis or deliverable write, open the target zone and read the proposed change — the policy MCP keeps the write in `dry_run` until you approve, so nothing has landed yet and there is no risk in reading first.

**3. Weigh the agent verdict — but decide for yourself.**

`agent_recommendation` is a *recommendation*, not the decision. You can reject a card the Verifier marked `clean`, or approve one it flagged after reading the flag and judging it minor. Approval means "good enough to move forward" — not "every claim in this output is verified."

**4. Approve.**

Set the card's `review_status` to `approved`. The dispatcher then lets the gated write proceed and the policy MCP stops applying `dry_run` to that card's target. For link-suggestion cards specifically, `Cmd-P → Memoria: approve all link suggestions` bulk-approves every `requested` card at once.

**5. Reject — then choose a path.**

Set `review_status` to `rejected`. A rejected card is **not** handed back to the worker — there is no "do the same thing but better." Pick one path (see [Post-rejection paths](../../explanation/workflows/review-as-state.md#post-rejection-paths)):

- **Supersede** — create a new card on the same lane with a corrected specification; the old card is archived with `archive_reason: superseded`. Use this when the *spec* was wrong, not just the execution.
- **Discard** — archive the card with `archive_reason: discarded`. Use this when the task itself should never have existed.

Don't confuse rejection with a **retry** — a retry is automatic re-dispatch of the *same* card after a transient failure (rate limit, timeout). Retries address execution failures; rejections address quality failures.

**6. Mind the WIP cap.**

The `done-awaiting-review` queue has a cap. When it fills, the dispatcher slows new work on that lane — this is back-pressure that keeps the board from racing ahead of your review capacity, not a malfunction. If a lane stalls, clear its review queue rather than raising the cap.

## Verify

- The board-state dashboard's review-queue count drops as you approve or reject.
- Approved synthesis/deliverable writes now appear in their target zone (no longer held in `dry_run`); rejected cards left nothing behind.
- No card sits in `done` + `review_status: requested` longer than your review cadence.

## Related

- Where the queue is surfaced: [Navigate the dashboards](../using-obsidian/navigate-the-dashboards.md), [board-state dashboard](../../explanation/dashboards/daily-glance/board-state.md)
- The write-gate that enforces it: [Policy MCP reference](../../reference/policy-mcp.md)
- Why review is a state, not a convention: [Review as a first-class state](../../explanation/workflows/review-as-state.md)
- Why the gate is structural: [Why a human gate](../../explanation/rationale/why-human-gate.md)
- Decisions: [ADR-03 structural review gate](../../adr/03-structural-review-gate.md), [ADR-14 advisor review](../../adr/14-advisor-review-vs-frozen-deliverable.md), [ADR-16 adopt-on-demand](../../adr/16-adopt-on-demand-for-reviews.md)
