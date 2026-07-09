# Security review

Use this playbook for changes touching `scripts/`, `.github/`,
`src/memoria_vault/product/workspace_seed/`,
secrets, external integrations, or another trust boundary. Use installed
security skills for generic vulnerability discovery; this playbook names the
Memoria boundaries and evidence to check in a diff.

## 1. Scope the boundary

1. Read [`AGENTS.md`](../../AGENTS.md), especially secrets, sensitive paths, and
   runtime facts.
2. Resolve the exact diff and identify changed privileged surfaces.
3. List the repo assets the diff can affect: vault contents, canonical notes,
   API keys, audit logs, GitHub permissions, optional-adapter capabilities, and
   runtime configuration.
4. Identify attacker-, contributor-, model-, or adapter-controlled inputs and
   the operations they reach.

## 2. Check Memoria controls

For each changed entry point, prove the enforcing line still gates the side
effect:

```text
source -> normalization/validation -> authorization/policy -> sink -> audit/recovery
```

- For `.github/`, verify event type, token permissions, checkout target,
  expression handling, dependency pinning, and concurrency behavior.
- For `src/memoria_vault/product/workspace_seed/`, verify package-data scope and
  baseline-vault payload boundaries separately.
- For installer changes, use dry-run and a disposable vault, never `~/Memoria`.
- For policy or hook changes, test the allowed, denied, and fail-closed paths.
- For MCP or optional-adapter changes, treat MCP as a policy boundary, not an
  operating-system sandbox.
- For secret-bearing paths, verify secrets stay in gitignored config or
  environment files and are not printed in logs, errors, fixtures, or docs.
- Use [Test selection](../system/test-selection.md) for focused checks and
  `scripts/verify` gate promotion.

## 3. Report

Only report a vulnerability when there is a plausible source-to-impact path.
For each finding include:

- Severity and confidence
- Source, broken control, sink, and impact
- Exact affected file and line
- Preconditions and counterevidence
- Minimal remediation and regression test

If no finding survives, record reviewed surfaces, tests run, and any unresolved
environmental limitation.

## 4. Escalate to a full audit

This playbook is scoped to the current diff. If review surfaces something beyond
one change — systemic exposure, unclear trust boundaries, or a request for a
standalone assessment — and the `threat-modeling` skill is installed, it runs a
full 8-phase STRIDE model as a separate, deliberately-requested activity. Do not
reach for it to answer single-finding follow-ups here — resolve those per
section 4.
