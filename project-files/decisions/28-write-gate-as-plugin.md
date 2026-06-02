---
topic: decisions
id: 28
title: The vault write gate is a Hermes Python plugin, not a shell hook
status: accepted
date_proposed: 2026-06-02
date_resolved: 2026-06-02
supersedes: []
superseded_by: []
---

# ADR-28: The vault write gate is a Hermes Python plugin, not a shell hook

## Context

[ADR-27](27-hermes-native-config-and-gate-enforcement.md) concluded that the
structural review gate ([ADR-03](03-structural-review-gate.md)) enforces via a
`pre_tool_call` **shell hook** (`matcher: "obsidian.*"`, running `policy_hook.py`)
once `mcp_servers` live in `config.yaml` and a toolset allowlist makes obsidian the
only write path. Its validation rows, however, carried hand-set `task_id`s
(`adr27-write-01`) — they came from synthetic hook-test payloads, not a live agent
run.

A real live re-run (Hermes v0.14.0, `hermes -z`, against `Memoria-test`) found the
gate **never fires**: a write to a review-gated zone succeeded, ungated and
unaudited. Three independent investigations plus a first-hand `hermes hooks test`
converged on the cause:

1. **Tool-name / matcher mismatch.** Hermes registers MCP tools as
   `mcp_<server>_<tool>` (`tools/mcp_tool.py`), so the obsidian write is
   `mcp_obsidian_obsidian_append_content` (the `mcp_` prefix + mcp-obsidian's own
   `obsidian_` names, doubled). The shell-hook matcher uses `re.fullmatch`
   (`agent/shell_hooks.py`), and `re.fullmatch("obsidian.*", "mcp_obsidian_…")` is
   `None`. The hook process is never spawned — no block, no audit. (The earlier
   "in-process test passed" used the fabricated name `obsidian_append_content`,
   which *does* fullmatch — hence the false positive.)
2. **Shell hooks are consent-gated.** On non-TTY runs (cron, headless `-z`) they
   register only with `--accept-hooks` / `HERMES_ACCEPT_HOOKS=1` /
   `hooks_auto_accept: true`; otherwise *"not allowlisted — skipped."*
3. **Shell hooks are fail-OPEN by construction.** The hook dispatcher swallows
   callback exceptions; shell hooks return "no block" on error/timeout/bad-JSON
   (`agent/shell_hooks.py`, `hermes_cli/plugins.py`). A gate that proceeds on its
   own failure is not a gate.

Earlier conclusions ("hooks don't fire in oneshot"; "…not in the gateway either")
were partly right about the symptom and wrong about the cause: the firing site
*is* reached in every mode; the matcher silently rejected the tool.

## Decision

**Implement the write gate as a Hermes Python plugin (`memoria-policy-gate`),** not
a shell hook. The plugin registers two lifecycle hooks on the plugin manager:

- `pre_tool_call` → classify the tool, evaluate the lane policy, and return
  `{"action": "block", "message": …}` for `deny`/`dry_run`. **Fail-closed:** any
  error inside the gate returns a block.
- `post_tool_call` → complete the audit record (paired `after_hash`).

It **reuses the tested decision core verbatim** — `policy_hook.evaluate_pre` /
`evaluate_post` and `policy_mcp.PolicyEngine` — so no policy logic is duplicated.
The `hooks:` block is removed from every profile `config.yaml`; the plugin is
turned on per lane via `plugins.enabled` and deployed (with `{{PROFILE}}` /
`{{VAULT_PATH}}` substituted) by the installer's `deploy_policy_plugin`.

The capability layer from ADR-27 (`agent.disabled_toolsets`, obsidian = the only
write path for the five non-terminal lanes) **stands** — it is what makes a single
gated path sufficient. ADR-28 replaces only ADR-27's *enforcement mechanism* (shell
hook → plugin); the config-model decisions in ADR-27 are unchanged.

## Why a plugin (over the alternatives)

| Approach | All modes | task_id | Fail-closed | Notes |
| --- | --- | --- | --- | --- |
| **Python plugin `pre_tool_call`** (chosen) | yes (in-process, no consent) | **yes — passed to the callback** | yes (block on any internal error) | matches in Python, so the real `mcp_obsidian_*` name is caught |
| Fix the shell-hook matcher (`mcp_obsidian.*`) | yes | yes | **no** — fail-open by design | one-line stopgap only |
| Wrapper `obsidian` MCP server | yes | **no — MCP tools get only model args** | yes | new process + replicate REST calls; task_id is the hard part |

The plugin is the only option that is both fail-closed *and* solves `task_id`
provenance for free. Its one residual weakness — if the plugin fails to load there
is no gate — is bounded by `plugins.enabled` (installer-managed) and backstopped by
the capability layer (no other write path exists).

## Consequences

- The gate now enforces live in `-z`/gateway/cron/ACP (all share the same agent
  loop and plugin dispatch). This resolves
  [#58](https://github.com/eranroseman/memoria-vault/issues/58) for real, not by
  artifact.
- `policy_hook.py` stays as the shared decision/audit core (its `--self-test`
  remains valid); only its use as a *shell-hook entrypoint* is retired.
- Defense in depth: the plugin gates both the obsidian MCP writes (all lanes) and
  the `file` toolset writes (`write_file`/`patch`) on Coder/Linter, via the same
  `classify`, so it replaces both former shell-hook matchers.
- New residual risk: "plugin not loaded → ungated." Mitigated by `plugins.enabled`
  per lane and the capability allowlist; a startup assertion is a possible
  follow-up.

## Validation

Live on `Memoria-test` (Hermes v0.14.0, `hermes -z`), against lanes deployed
through the productionized installer (`memoria-librarian` and `memoria-writer`):

- **Allowed-zone write** (`10-inbox/…`) → succeeds; audit logs `allow` +
  `write_complete` with the real session-UUID `task_id`.
- **Review-gated/denied write** (`30-synthesis/…`) → **blocked** (`policy deny`);
  no file on disk; audit reason shows the real `mcp_obsidian_obsidian_append_content`
  name (proving the plugin matched what the shell hook missed).
- **Simulated policy outage** (`policy_mcp.py` moved aside) → an otherwise-allowed
  write is **blocked** (fail-closed), where the shell hook would have failed open.

The gate was then re-validated in the other non-interactive run modes (same agent
loop; the gateway calls `discover_plugins()` at startup, `gateway/run.py`):

- **Gateway** (driven headless via the built-in `api_server` platform,
  `POST /v1/chat/completions`) → denied write blocked (audit `deny`); allowed write
  succeeds (audit `allow` + `write_complete`).
- **Cron** (`hermes -p <lane> cron run … && cron tick`) → denied write blocked
  (audit `deny`), no file on disk.

## Alternatives considered

- **Keep the shell hook, fix the matcher to `mcp_obsidian.*`.** Makes it fire, but
  it stays consent-gated and fail-open — unacceptable for the primary gate. Viable
  only as a transition stopgap; not adopted.
- **Custom wrapper `obsidian` MCP server.** Fail-closed and mode-independent, but an
  MCP tool receives only model-supplied args, so `task_id` provenance is unsolved
  (the model would have to be trusted to pass it). More moving parts than a plugin
  for no enforcement gain. Held as a fallback if the "plugin must load" assumption
  ever proves insufficient.
