---
topic: decisions
id: 31
title: Vault access via the Local REST API plugin's native MCP (HTTPS), not uvx mcp-obsidian
status: accepted
date_proposed: 2026-06-04
date_resolved: 2026-06-04
assumes: []
supersedes: []
superseded_by: []
---

# ADR-31: Native obsidian MCP over HTTPS

## Context

Every lane's vault-write path is the `obsidian` MCP ([ADR-27](27-hermes-native-config-and-gate-enforcement.md)/[ADR-28](28-write-gate-as-plugin.md)). v0.1 used the **uvx `mcp-obsidian`** package (stdio), which **hardwires port 27124** and reads only `OBSIDIAN_API_KEY` — `OBSIDIAN_HOST`/`OBSIDIAN_PORT` are ignored. Because only one Obsidian vault can serve a given port, a sandbox and a production vault couldn't both expose the REST API at once, forcing a "keep production closed during runs" rule and manual port juggling.

The **Local REST API plugin (v4.1.2, "with MCP")** now ships its **own native MCP server** at `/<host>/mcp` (Streamable HTTP) — a viable replacement whose port lives in the URL.

## Decision

Point every profile's `obsidian` `mcp_servers` entry at the plugin's **native MCP over verified HTTPS on loopback**, dropping uvx `mcp-obsidian`:

```yaml
obsidian:
  url: "https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp"
  ssl_verify: "${OBSIDIAN_MCP_SSL_VERIFY}"
  headers:
    Authorization: "Bearer ${OBSIDIAN_API_KEY}"
```

- **Verified HTTPS, not plain HTTP** — Hermes supports `mcp_servers.<name>.ssl_verify` as either a bool or a path to a PEM CA bundle for HTTP/SSE MCP servers. `OBSIDIAN_MCP_SSL_VERIFY` points at the Local REST API plugin's exported certificate/CA bundle, so the bearer key no longer travels over unencrypted loopback and verification remains on.
- **Port via `OBSIDIAN_MCP_PORT`** (`~/.hermes/.env`) so sandbox + production coexist on different ports — no more "keep production closed."
- **Explicit `Authorization: Bearer`** header — `hermes mcp add --auth header` sent a form the plugin 401'd; the exact bearer header works.

## Security — the gate still holds

The native server exposes 16 tools with **different names** (`vault_write`/`append`/`patch`/`delete`/`move`, `command_execute`, …). The write gate matches on `obsidian` + a write keyword, and `WRITE_KEYWORDS` already covers `write`/`append`/`patch`/`delete`/`move` — so the native write tools are gated **with no matcher change** (verified: `mcp_obsidian_vault_write` to a denied zone is blocked). The path arg is `path` (first `PATH_KEYS` match), so the gate evaluates the right file.

`policy_hook` adds a **hard-deny** (`DENY_OBSIDIAN`) for `command_execute` (arbitrary Obsidian command — no path to gate), `vault_delete`, and `vault_move` (destructive, unused by the workflows; the old uvx tools were read/write/append/patch only). These are blocked for every lane even inside an allowed zone — least privilege, defense-in-depth beyond tool-selection.

## Consequences

- **Sandbox + production coexist** on different ports; the uvx dependency is gone.
- **Validated live:** read + a full ingest end-to-end through the native MCP (note written via `vault_write`/`append`, gated); `policy_hook --self-test` covers native tool names + the hard-denies.
- **Setup cost:** enable the plugin's HTTPS endpoint on `OBSIDIAN_MCP_PORT` and set `OBSIDIAN_MCP_SSL_VERIFY` to the exported PEM certificate/CA bundle path. **All profiles** *(v0.1.0-alpha.2: the fleet is the five profiles of [ADR-48](48-copi-and-agent-consolidation.md); originally seven)* are switched — leaving any lane on uvx (27124) would re-introduce the port collision the moment it ran, so the coexistence benefit only holds with every lane native. The shared `policy_hook` (with `DENY_OBSIDIAN`) gates them all identically.
- **Residual:** the certificate file is per-machine plugin state, so it stays in `.env` / gitignored plugin state rather than repository source.

- **Related:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md) (the write gate this preserves).
