---
title: Fix a stuck request
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 2
---

# Fix a stuck request

Memoria tracks CLI and engine work as operation requests.

This guide covers stuck operation **requests** only. Attention items
(`candidate`, `gap`, `work-prompt`, `alert`) are a separate, currently-shipped
concept — see [Work the action queue](../inbox/work-the-action-queue.md).

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
| `cancelled` | Retry only work explicitly cancelled by the PI and not marked as superseded. |
| Human decision needed | Use `memoria attention list` and resolve the attention item after review. |

Cancel obsolete work instead of retrying forever:

```bash
memoria request cancel --workspace <workspace> <request-id>
```

Cancel accepts only a pending request. If its scope is correct but a non-scope
argument is wrong, create a successor instead:

```bash
memoria request amend --workspace <workspace> --idempotency-key <new-key> \
  <request-id> field=value
```

If an ID, reference, path, target, or other scope-bearing field is wrong,
submit a new original operation. `request amend` rejects scope changes.

## Verify

- `memoria request show --workspace <workspace> <request-id>` no longer reports a stale `running` or unresolved `failed` state
- Any related attention item has been resolved or deliberately deferred
- `memoria status --workspace <workspace>` reflects the current queue state

## Related

- Safe mode: [Safe mode](safe-mode.md)
- Request commands: [CLI](../../reference/commands-and-transports/cli.md)
- Failure catalog: [Failure modes](../../reference/system/failure-modes.md)
