---
title: Policy auto-fix
parent: Agents and control
grand_parent: Reference
---

# Policy auto-fix

The class gate for automated repairs that pass through the Policy gate. For the request/response protocol and lane enforcement rules, see [Policy gate](policy-mcp.md).

## Classes

| Class | Disposition | Examples |
| --- | --- | --- |
| `safe-and-unambiguous` | `allow_with_log` within the lane's write scope | Trailing whitespace, missing `created` with one obvious value |
| `authorized-targeted` | `allow_with_log`, `task_id`-bound | Findings-file truncation, golden-copy restore |
| `schema-content` | `dry_run` always | Field rename, enum change — needs `lint:migrate-schema` |
| `review-gated-edit` | `deny` always | Any write to a gated zone |

---

## Related

- Runtime gate: [Policy gate](policy-mcp.md)
- Linter repair surfaces: [Linter: detectors and auto-fix](linter.md)
