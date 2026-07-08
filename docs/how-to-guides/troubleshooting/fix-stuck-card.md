---
title: Fix a stuck card
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 2
---

# Fix a stuck card

Alpha.19 tracks CLI/engine work as operation requests. If old docs or adapters
call this a "card", diagnose the corresponding request.

## Detect

```bash
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
```

Check the request `status`, `operation_id`, `error`, input refs, and output
intents.

## Fix

| State | What to do |
| --- | --- |
| `pending` | Run `memoria workspace run --workspace <workspace>` or resume the specific request. |
| `running` | Run `memoria workspace recover --workspace <workspace>` to replay/reconcile interrupted work. |
| `failed` | Fix the input/provider/file problem, then run `memoria request retry --workspace <workspace> <request-id>`. |
| Human decision needed | Use `memoria attention list` and resolve the attention item after review. |

Cancel obsolete work instead of retrying forever:

```bash
memoria request cancel --workspace <workspace> <request-id>
```

## Verify

- `memoria request show --workspace <workspace> <request-id>` no longer reports a stale `running` or unresolved `failed` state
- Any related attention item has been resolved or deliberately deferred
- `memoria status --workspace <workspace>` reflects the current queue state

## Related

- Safe mode: [Safe mode](safe-mode.md)
- Request commands: [CLI](../../reference/cli.md)
- Failure catalog: [Failure modes](../../reference/failure-modes.md)
