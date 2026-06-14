---
name: policy-change-review
description: Review changes to Memoria profile capabilities, lane write scopes, policy enforcement, task delegation ceilings, or privileged policy workflows for cross-file drift and weakened boundaries.
---

# Policy change review

Use this skill when a diff touches `src/.memoria/tool-registry.yaml`,
`src/.memoria/lane-overrides/`, profile MCP/tool configuration, policy MCP/hook
code, the write-gate plugin, task delegation, or PR policy.

## Authority and maps

Read:

1. [`AGENTS.md`](../../../AGENTS.md)
2. [Source-of-truth map](../../system/source-of-truth-map.md)
3. [Change-impact map](../../system/change-impact-map.md)
4. [Test selection](../../system/test-selection.md)

## Review procedure

1. Resolve the exact diff and list every changed policy surface.
2. Build a per-profile matrix containing:
   - Tool capabilities from `tool-registry.yaml`
   - MCP servers and disabled toolsets from `config.yaml`
   - Allowed and denied paths from the lane override
   - Invocation and external API policy
   - Plugin enforcement
3. Confirm capability and scope remain separate:
   - Tool registry answers what a profile can call.
   - Lane override answers where a permitted tool can write.
   - Task payloads may narrow but never widen the lane ceiling.
4. Trace every changed mutating path through:

   ```text
   tool call -> policy hook/plugin -> policy decision -> filesystem side effect
   -> complete_write/audit
   ```

5. Verify the structural invariants:
   - The Co-PI remains hard read-only and delegates writes.
   - No profile gains direct-world `file`, `terminal`, `code_execution`,
     `browser`, `web`, or `computer_use`.
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
identify the profile or workflow, the widened or inconsistent authority, the
reachable operation, and the missing control. If no issue survives, include the
matrix surfaces reviewed and tests run.
