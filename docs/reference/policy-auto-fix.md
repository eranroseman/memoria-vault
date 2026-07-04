---
title: Policy auto-fix
parent: Agents and control
grand_parent: Reference
---

# Policy auto-fix

The class gate for automated repairs that pass through the Policy gate. For the
request/response protocol and actor policy rules, see [Policy gate](policy-mcp.md).

## Classes

| Class | Disposition | Examples |
| --- | --- | --- |
| `safe-and-unambiguous` | `allow_with_log` within the actor's write scope | Trailing whitespace, missing `created` with one obvious value |
| `authorized-targeted` | `allow_with_log`, `request_id`-bound | Findings-file truncation |
| `schema-content` | `dry_run` always | Field rename, enum change — needs manual schema/content repair |
| `review-gated-edit` | `deny` always | Any write to a gated zone |

---

## Related

- Runtime gate: [Policy gate](policy-mcp.md)
- Linter repair surfaces: [Linter: detectors and auto-fix](linter.md)
