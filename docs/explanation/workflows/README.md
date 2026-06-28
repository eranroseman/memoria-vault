---
title: Workflows
parent: Explanation
nav_order: 6
permalink: /explanation/workflows/
---

# Workflows

Memoria's workflows are board-backed, not scripted procedures: work lives as a
card whose state is explicit, persistent, and queryable. The board model itself
is explained in [Kanban board](../kanban-board/README.md); this section keeps the
workflow-specific triggers that sit on top of it.

## Verify-on-commit

Committing a draft to `projects/<project>/` automatically creates a verification
card in the Peer-reviewer's verify lane. The trigger is automatic because
verification is important enough to be non-negotiable but easy to defer under
deadline pressure.

The trigger fires on `post-commit` to `projects/*/`, not on a schedule. A commit
is the natural unit of change in the writing workflow; a cron job would verify
based on time, rechecking unchanged drafts and delaying changed ones. The hook
creates a board card and returns. The Peer-reviewer claims that card through the
normal dispatcher, so verification stays audited, retryable, and visible.

This does not make verification completion automatic. The card enters the
Peer-reviewer's queue; the result is an `agent_recommendation`, never an approval
gate. The human still reads the report and decides whether to revise.

For step-by-step workflow recipes, see [how-to guides](../../how-to-guides).

## Related

- [The Peer-reviewer](../profiles/peer-reviewer.md) — what the Peer-reviewer checks
- [Verify and revise a draft](../../how-to-guides/project/verify-and-revise.md) — how to read the report and address gaps
