---
name: policy-change-review
description: Review changes to Memoria operation capabilities, write policy enforcement, task delegation ceilings, optional adapter policy, or privileged policy workflows for cross-file drift and weakened boundaries.
---

# Policy change review

Use this skill when a diff touches `vault-template/capabilities/operations/`,
runtime policy code, policy gate/hook code, the write-gate plugin, task delegation,
provider ceilings, or PR policy.

## Authority and maps

Read:

1. [`AGENTS.md`](../../../AGENTS.md)
2. [Source-of-truth map](../../system/source-of-truth-map.md)
3. [Change-impact map](../../system/change-impact-map.md)
4. [Test selection](../../system/test-selection.md)

## Review procedure

1. Resolve the exact diff and list every changed policy surface.
2. Build an operation/policy matrix containing:
   - Operation id and manifest home
   - Allowed tools, paths, and network/provider ceilings
   - Request input/output intents and mutation targets
   - Required checks and promotion gates
   - Optional adapter enforcement, if present
3. Confirm capability and scope remain separate:
   - Operation manifests answer what an operation may call and touch.
   - Request payloads may narrow but never widen the operation ceiling.
   - Optional adapter policy may only add fail-closed checks.
4. Trace every changed mutating path through:

   ```text
   request -> operation manifest -> policy decision -> filesystem side effect
   -> complete_write/audit
   ```

5. Verify the structural invariants:
   - No removed installed-profile package, lane override, or tool registry reappears.
   - No operation gains direct-world `file`, `terminal`, `code_execution`,
     `browser`, `web`, or `computer_use` outside an explicit checked manifest.
   - Review-gated prefixes cannot be automatically written.
   - Deny rules and invalid configuration fail closed.
   - Delete and auto-fix retain explicit authorization/class controls.
   - Every allowed mutation is audited with before/after evidence.
   - `.github/` policy changes do not execute untrusted PR code with privileged
     credentials.
6. Inspect all consumers named in the change-impact map. Do not assume matching
   prose proves matching enforcement.
7. Run the focused tests from `test-selection.md`, then the full gate before PR
   handoff.

## Output

Use the [review report template](../../templates/review-report.md). Findings must
identify the operation or workflow, the widened or inconsistent authority, the
reachable operation, and the missing control. If no issue survives, include the
matrix surfaces reviewed and tests run.
