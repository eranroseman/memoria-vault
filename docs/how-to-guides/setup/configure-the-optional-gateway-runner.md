---
title: Configure the optional gateway runner
parent: Setup
grand_parent: How-to guides
nav_order: 6
---

# Configure the optional gateway runner

Prepare a workspace to use its seeded `gateway` runner. This task stores a
credential outside the workspace and verifies runner construction; it does not
dispatch a model or change vault content.

The standalone seed has a keyless loopback `local` runner and an optional
OpenAI-compatible `gateway` runner. The gateway names `KILOCODE_API_KEY` as its
credential. Its endpoint and key name live in the workspace provider
configuration; the key itself does not.

## Steps

**1. Inspect the expected credential.**

```bash
memoria secrets list --workspace ~/Memoria --json
```

Find `KILOCODE_API_KEY` in `credentials`. The command reports only its status
and source, never its value.

**2. Store the gateway key.**

```bash
memoria secrets set KILOCODE_API_KEY
```

Paste the value at the hidden prompt. Memoria stores it as a user-scope secret,
not in the workspace. If your shell or service manager already supplies
`KILOCODE_API_KEY`, that process environment takes precedence instead.

**3. Verify construction without a model request.**

```bash
memoria doctor --workspace ~/Memoria --check runner --provider gateway --json
```

Without `--live`, this checks the runner dependency, configured endpoint, and
agent construction without dispatching to the provider. Confirm that
`runner_base_url`, `runner_dependency`, and `runner_agent_constructed` are
`true`. If the key is unavailable, the result names the same `memoria secrets
set KILOCODE_API_KEY` remedy.

Do not add `--live` merely to configure the runner: it intentionally sends a
model request. Use a live operation only when its task guide and run-mode gate
call for it.

## Verify

- `memoria secrets list --workspace ~/Memoria --json` reports
  `KILOCODE_API_KEY` as set from `file` or `env`, without printing its value.
- The non-live runner check reports the selected provider as `gateway` and all
  three runner-construction checks as `true`.

## Related

- Credential classes and provider ownership: [External integrations](../../reference/evidence-and-integrations/integrations.md#credentials-and-keyless-behavior)
- Configuration surfaces and secret boundary: [Memoria configuration](../../reference/system/configuration.md)
- Exact runner and CLI behavior: [CLI](../../reference/commands-and-transports/cli.md)
