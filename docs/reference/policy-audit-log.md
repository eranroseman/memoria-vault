---
title: Policy audit log
parent: Reference
nav_order: 20
---

# Policy audit log

The audit trail written by the Policy gate. For the request/response protocol and
actor-policy rules, see [Policy gate](policy-mcp.md).

## Format

Every decision is appended to **`system/logs/audit.jsonl`** (append-only JSONL — crash-safe, grep-friendly).

### Fields

| Field | Type | Notes |
| --- | --- | --- |
| `schema_version` | integer | Audit-log schema version. Current value: `2`. |
| `review_mode` | enum | Current review-gate arm. Production value: `blocking`. |
| `timestamp` | ISO datetime | UTC, `…Z`. |
| `actor` | string | Actor named by optional adapter policy. |
| `action` | string | One of the eight actions above (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`). |
| `path` | string | The workspace-relative path targeted. |
| `request_id` | string | The request that triggered the action. |
| `decision` | enum | Exactly one of `allow` · `allow_with_log` · `deny` · `dry_run`. |
| `policy_rule` | string | Which actor-policy rule matched. |
| `reason` | string | Optional prose from the request. |
| `before_hash` / `after_hash` | SHA-256 | The reversibility pair (see below). |

A representative decision entry:

```json
{
  "schema_version": 2,
  "review_mode": "blocking",
  "timestamp": "2026-06-10T14:23:01Z",
  "actor": "adapter",
  "action": "write",
  "path": "inbox/proposal.md",
  "request_id": "REQ-2026-06-10-003",
  "decision": "allow_with_log",
  "policy_rule": "Adapter.write.inbox",
  "before_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
  "after_hash": null
}
```

### Per-write hash pairing

Auditing uses **per-write SHA-256 hash pairing, not a cross-entry chain**: each
mutating write produces a `before_hash` on the decision entry, and a *separate*
`write_complete` record carries the paired `after_hash` once the write lands.
`write_complete` is a **record kind, not a value of the `decision` enum** — the
four `decision` values are exactly `allow`, `allow_with_log`, `deny`, and
`dry_run`. The two records are matched by `request_id` + `path`; the pairing pins
one write's before/after state and nothing more — it does not hash-link
successive entries.

**SHA-256 rules:** the runtime computes hashes; format `"sha256:<64-hex>"`; a
freshly-created file's `before_hash` is the empty-string SHA-256, never null; a
hash read-error denies the request (no hash, no allow).

---

## Related

- Runtime gate: [Policy gate](policy-mcp.md)
- Audit-memory substrate: [Memory substrates](memory-substrates.md)
