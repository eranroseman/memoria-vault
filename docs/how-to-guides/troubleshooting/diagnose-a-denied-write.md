---
title: Diagnose a denied or blocked write
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 4
---

# Diagnose a denied or blocked write

**Symptom:** a CLI command or optional adapter reports a write, but the expected
workspace file or projection is missing.

**Diagnosis:** separate policy denial from runtime failure:

1. The runtime policy gate denied or dry-ran an optional adapter write.
2. The CLI worker request failed before materialization.
3. A direct editor/file change was quarantined until `workspace scan` checks it.

## Steps

**1. Check request state.**

```bash
memoria status --workspace <workspace> --json
memoria request list --workspace <workspace> --json
```

If the request is failed or pending, inspect the request payload and retry or
resume it with the `request` command surface.

**2. Check the audit log.**

```bash
memoria journal list --workspace <workspace> --json
```

For optional adapter writes, also inspect `system/logs/audit.jsonl`. A matching
`deny` or `dry_run` means the gate worked; read `policy_rule` and `reason`.

**3. Check quarantine.**

```bash
memoria workspace scan --workspace <workspace> --json
```

Observed external edits are not machine-consumable until checked. The scanner
journals them as external edits, marks them unchecked, and promotes only after
the relevant checks pass.

**4. Check generated projections.**

```bash
memoria workspace rebuild --workspace <workspace> --json
```

Generated files such as indexes, bibliography, and qmd input mirrors are rebuilt
from SQLite and checked Concepts. A direct edit to a generated target is not
authoritative.

## Common Outcomes

| Outcome | What to do |
| --- | --- |
| `deny` | Use the correct CLI operation or narrow adapter policy; do not bypass the gate. |
| `dry_run` | The target is gated or missing an approved promotion path; inspect the staged output. |
| failed request | Fix the payload/provider/runner error, then retry or resume the request. |
| quarantined external edit | Review the scan result, then accept/promote through the checked workflow. |
