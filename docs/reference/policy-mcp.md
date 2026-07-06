---
title: Policy gate
parent: Agents and control
grand_parent: Reference
nav_order: 8
---

# Policy gate

The alpha.15 write boundary is the standalone CLI/engine: operation manifests,
request rows, staging, checks, promotion, and journal entries control machine
mutations. Optional adapters may call
`memoria_vault.runtime.policy.hook` before and after tool calls so external writes
reuse the same fail-closed policy and audit behavior.

The baseline workspace does not ship adapter servers, lane override packages, or
installed profiles. If an optional adapter supplies
`.memoria/config/policy.yaml`,
missing or invalid policy still fails closed.

## Request Flow

```text
optional adapter tool call
  -> memoria_vault.runtime.policy.hook
     -> normalize action and path
     -> load operator-supplied policy, if present
     -> allow | allow_with_log | deny | dry_run
     -> adapter executes or blocks
     -> post-tool hook records before/after hashes
```

Every request carries complete identity metadata. `request_id` is required for
mutating adapter calls. A missing `request_id`, a path-traversal attempt, direct
file/terminal/code/browser/egress tool use, or an invalid policy configuration is
denied and audited. Audit rows identify the policy subject with `actor`, never
with an installed profile.

## Actor Policy

Optional adapters provide one config file:

```yaml
version: 1
actors:
  adapter:
    allow:
      tools: [obsidian.get_file_contents, search.query]
      write: ["inbox/**"]
    deny:
      tools: [web_search, execute_code]
      write: ["knowledge/**", "catalog/**", "system/**"]
    require: [audit_log]
    write_scope: ["inbox/"]
```

`allow.tools` is the hard ceiling for non-direct adapter tools. Direct file,
terminal, code, browser, web, message, and delegation tools are hard-denied
before actor policy is evaluated.

## Action Vocabulary

| Action | Default disposition |
| --- | --- |
| `read` | Default-allow unless explicitly denied. |
| `write` / `append` | Deny rules win; allowed writes are audited. |
| `move` | As write, and always audit-paired when allowed. |
| `delete` | Deny unless explicit authorization and the path is inside scope. |
| `mkdir` | Allow within declared write scope, else deny. |
| `auto_fix` | Class-gated by `flags.class`. |
| `report` | Non-mutating report action. |

## Audit Contract

Allowed mutating adapter writes record the pre-write hash before the tool runs
and append the paired before/after record after the tool completes. Denied,
dry-run, and policy-load failures append a decision row immediately. Runtime
worker mutations use the request/journal path directly and do not need an adapter
hook.

## Current Checks

| Check | Purpose |
| --- | --- |
| `tests/test_runtime_policy.py` | Policy decision and audit core behavior. |
| `tests/test_policy_hook.py` | Hook protocol and fail-closed tool/path behavior. |
| `tests/test_policy_gate_plugin.py` | Optional plugin import/failure behavior. |
| `tests/test_policy_gate_completeness.py` | Direct-tool deny coverage. |
