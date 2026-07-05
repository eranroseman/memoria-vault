# Security review

Use this playbook for changes touching `scripts/`, `.github/`, `vault-template/.memoria/`,
secrets, external integrations, or another trust boundary. It complements
available security tools; it does not depend on a particular plugin.

## 1. Define the boundary

1. Read [`AGENTS.md`](../../AGENTS.md), especially secrets, sensitive paths, and
   runtime facts.
2. Resolve the exact diff and identify changed privileged surfaces.
3. List relevant assets: vault contents, canonical notes, API keys, audit logs,
   GitHub permissions, profile capabilities, and runtime configuration.
4. Identify attacker- or model-controlled inputs and the operations they reach.

## 2. Trace changed paths

For each changed entry point, follow data to its control and side effect:

```text
source -> normalization/validation -> authorization/policy -> sink -> audit/recovery
```

Check for:

- Secret exposure in files, logs, commands, errors, fixtures, or documentation
- Path traversal, unsafe archive/file handling, and writes outside intended scopes
- Shell, template, query, YAML, or command injection
- SSRF or unrestricted external destinations
- Missing authentication or authorization
- Fail-open behavior in policy gates, hooks, CI, and plugin loading
- Untrusted code execution in privileged GitHub Actions events
- Lane/tool permissions that widen instead of narrow authority
- Destructive operations without explicit authorization or recovery
- Audit gaps, incomplete before/after records, or mutable evidence

Treat MCP as a policy boundary, not an operating-system sandbox.

## 3. Verify controls

- Read the closest tests and add or request regression cases for each changed
  security invariant.
- For `.github/`, verify event type, token permissions, checkout target,
  expression handling, dependency pinning, and concurrency behavior.
- For `vault-template/.memoria/`, verify tool capability and path scope separately.
- For installer changes, use dry-run and a disposable vault, never `~/Memoria`.
- Run the narrow tests and `python scripts/verify pr` when practical.

## 4. Report

Only report a vulnerability when there is a plausible source-to-impact path.
For each finding include:

- Severity and confidence
- Source, broken control, sink, and impact
- Exact affected file and line
- Preconditions and counterevidence
- Minimal remediation and regression test

If no finding survives, record reviewed surfaces, tests run, and any unresolved
environmental limitation.
