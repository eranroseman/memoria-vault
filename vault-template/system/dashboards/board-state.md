---
type: dashboard
title: Board State
---

# Board State

Request and attention state for debugging the local worker. Attention items are
waiting on you; the queue converges to empty. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/daily-glance/#board-state-support).

## Requests

Use `memoria request list --workspace . --json` for queued, running, failed, and
completed operation requests. Runtime request state lives in `.memoria/memoria.sqlite`;
there is no file-backed board projection.

## Attention

Use `memoria attention list --workspace . --json` for PI-facing attention
items projected from journal, check, and request state.
