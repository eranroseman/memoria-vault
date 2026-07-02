---
title: Inbox
projection: queue
dashboard: queue
cssclasses: memoria-space
---

# Inbox

> [!brief] Inbox empty? That's the goal. Active work appears first; decisions and
> raw captures follow when they need you.

> [!suggestions] First actions
> - Ask what needs attention: `memoria ask --workspace . --question "What needs my attention?"`
> - List pending requests: `memoria request list --workspace . --json`.

## Activity

Recent background tasks. Only queued or running work appears here.

Runtime request state lives in `.memoria/memoria.sqlite`.

## Needs me

Attention projections are generated from journal, check, and request state.

## Notes to check

Unchecked note Concepts waiting for the worker/check loop or PI review.

![[knowledge.base#Notes]]

Use the CLI for actions; use these Markdown pages as readable workspace views.

## Guides

Step-by-step for working this queue:

- [Work the action queue](https://eranroseman.github.io/memoria-vault/how-to-guides/inbox/work-the-action-queue.html)
- [Run the weekly review](https://eranroseman.github.io/memoria-vault/how-to-guides/inbox/run-the-weekly-review.html)
- [Return to work](https://eranroseman.github.io/memoria-vault/how-to-guides/inbox/return-to-work.html)
