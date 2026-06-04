---
topic: decisions
id: 31
title: "Vault access via the Local REST API plugin's native MCP (HTTP), not uvx mcp-obsidian"
status: accepted
date_proposed: 2026-06-04
date_resolved: 2026-06-04
supersedes: []
superseded_by: []
---

# ADR-31: Native obsidian MCP over HTTP

## Context

Every lane's vault-write path is the `obsidian` MCP ([ADR-27](27-hermes-native-config-and-gate-enforcement.md)/[ADR-28](28-write-gate-as-plugin.md)). v0.1 used the **uvx `mcp-obsidian`** package (stdio), which **hardwires port 27124** and reads only `OBSIDIAN_API_KEY` — `OBSIDIAN_HOST`/`OBSIDIAN_PORT` are ignored. Because only one Obsidian vault can serve a given port, a sandbox and a production vault couldn't both expose the REST API at once, forcing a "keep production closed during runs" rule and manual port juggling.

The **Local REST API plugin (v4.1.2, "with MCP")** now ships its **own native MCP server** at `/<host>/mcp` (Streamable HTTP) — a viable replacement whose port lives in the URL.

## Decision

Point every profile's `obsidian` `mcp_servers` entry at the plugin's **native MCP over plain HTTP on loopback**, dropping uvx `mcp-obsidian`:

```yaml
obsidian:
  url: "http://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp"
  headers:
    Authorization: "Bearer ${OBSIDIAN_API_KEY}"
```

- **HTTP, not HTTPS** — Hermes has no flag to skip TLS verification or trust a CA for URL MCP servers, and the plugin's HTTPS uses a self-signed cert (Hermes errored `CERTIFICATE_VERIFY_FAILED`). The plugin's HTTP server (loopback only) is the transport Hermes accepts. The bearer key travels over **unencrypted 127.0.0.1** — acceptable for a single-user local box; revisit if Hermes adds CA/insecure support.
- **Port via `OBSIDIAN_MCP_PORT`** (`~/.hermes/.env`) so sandbox + production coexist on different ports — no more "keep production closed."
- **Explicit `Authorization: Bearer`** header — `hermes mcp add --auth header` sent a form the plugin 401'd; the exact bearer header works.

## Security — the gate still holds

The native server exposes 16 tools with **different names** (`vault_write`/`append`/`patch`/`delete`/`move`, `command_execute`, …). The write gate matches on `obsidian` + a write keyword, and `WRITE_KEYWORDS` already covers `write`/`append`/`patch`/`delete`/`move` — so the native write tools are gated **with no matcher change** (verified: `mcp_obsidian_vault_write` to a denied zone is blocked). The path arg is `path` (first `PATH_KEYS` match), so the gate evaluates the right file.

`policy_hook` adds a **hard-deny** (`DENY_OBSIDIAN`) for `command_execute` (arbitrary Obsidian command — no path to gate), `vault_delete`, and `vault_move` (destructive, unused by the workflows; the old uvx tools were read/write/append/patch only). These are blocked for every lane even inside an allowed zone — least privilege, defense-in-depth beyond tool-selection.

## Consequences

- **Sandbox + production coexist** on different ports; the uvx dependency is gone.
- **Validated live:** read + a full ingest end-to-end through the native MCP (note written via `vault_write`/`append`, gated); `policy_hook --self-test` covers native tool names + the hard-denies.
- **Setup cost:** enable the plugin's HTTP server on `OBSIDIAN_MCP_PORT` (a documented step). **All seven profiles** are switched — leaving any lane on uvx (27124) would re-introduce the port collision the moment it ran, so the coexistence benefit only holds with every lane native. The shared `policy_hook` (with `DENY_OBSIDIAN`) gates them all identically.
- **Residual:** loopback HTTP is unencrypted; the self-signed-HTTPS path reopens once Hermes supports CA/insecure URL MCP.

- **Related:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md) (the write gate this preserves).
