---
title: Set up MCP
parent: Setup
grand_parent: How-to guides
nav_order: 5
---

# Set up MCP

Connect one Memoria vault to an MCP host over a least-privilege stdio server.
The normal bootstrap creates the vault-local environment and seeds `.mcp.json`,
but it does not install the optional MCP SDK.

## Prerequisites

- A bootstrapped vault ([Set up the vault](set-up-the-vault.md))
- An MCP host that can start a local stdio command
- The absolute path to the vault
- The folders or files the agent needs to read

## Steps

**1. Install MCP support into the vault-local environment.**

Use the Python executable that owns the installed `memoria` command. The
installed package metadata supplies the declared MCP dependency; do not use a
global Python.

```bash
# Linux / WSL2, for the default vault path:
~/Memoria/.memoria/.venv/bin/python -m pip install "memoria-vault[mcp]"
```

```powershell
# Windows, for the default vault path:
& "$env:USERPROFILE\Memoria\.memoria\.venv\Scripts\python.exe" -m pip install "memoria-vault[mcp]"
```

If your vault is elsewhere, replace `~/Memoria` or
`$env:USERPROFILE\Memoria` with its path. These commands add the optional SDK
to the existing vault environment; they do not create another Memoria install.

**2. Open the seeded `.mcp.json`.**

`memoria init`, including `--no-obsidian`, writes this host-facing template
only when it is absent. An existing `.mcp.json` is PI-owned and preserved, but
a later `memoria init` recreates the seed if the file was deleted. `memoria
doctor --repair` neither recreates nor overwrites it.

Replace the template's `command: "memoria"` and `--workspace .` values with
absolute paths. A host may start outside the vault or with a different `PATH`,
so relative values are unreliable.

For Linux or WSL2, a server entry can use this shape:

```json
{
  "mcpServers": {
    "memoria": {
      "command": "/home/alex/Memoria/.memoria/.venv/bin/memoria",
      "args": [
        "mcp",
        "--workspace",
        "/home/alex/Memoria",
        "--read-scope",
        "notes",
        "--read-scope",
        "projects",
        "--actor",
        "literature-review-agent"
      ]
    }
  }
}
```

On Windows, use escaped absolute paths in JSON:

```json
{
  "mcpServers": {
    "memoria": {
      "command": "C:\\Users\\Alex\\Memoria\\.memoria\\.venv\\Scripts\\memoria.exe",
      "args": [
        "mcp",
        "--workspace",
        "C:\\Users\\Alex\\Memoria",
        "--read-scope",
        "notes",
        "--read-scope",
        "projects",
        "--actor",
        "literature-review-agent"
      ]
    }
  }
}
```

Use the configuration location your host assigns to local stdio servers. The
JSON above describes the command and arguments only; it does not depend on a
particular host's settings screen.

**3. Narrow the read scopes.**

Keep only the named folders or files required for this connection. Each
`--read-scope` adds one boundary, so repeat the flag when the agent needs more
than one. Memoria rejects root scopes (`/` or `.`) and paths that escape the
workspace. An internal path such as `notes/../projects` can normalize to a
valid non-root scope, but configure the normalized name directly (`projects`)
so the boundary is easy to inspect.

The scope set belongs to one server instance and is fixed when that process
starts. A tool call cannot widen it. Create a separate server entry when
another agent needs a different scope instead of broadening every connection.

**4. Set a stable agent identity.**

Set `--actor` to the concrete agent identity you want in provenance, such as
`literature-review-agent`. The value identifies the agent; it grants no
authority. Every built-in MCP `operation_run` remains an `agent`-actor,
machine-authored request. PI- and integrity-reserved operations are refused,
and machine-authored bodies remain neutralized.

**5. Restart the host.**

Save `.mcp.json`, then fully restart the host so it starts a new stdio process
with the new executable, workspace, scopes, and identity.

## Verify the connection without writing

In the host, invoke the connected Memoria tools in this order:

1. Call `status`. Confirm the result has `ok: true`.
2. Call `operations`. Confirm it returns the packaged operation list.
3. Call `concept` with the path of an existing Concept inside a configured
   scope. Confirm the returned `path` matches the target.
4. Call `concept` with the path of an existing Concept outside every configured
   scope. Confirm the tool returns `target not found`, the same result used for
   a missing target.

The last two calls test the boundary without revealing the hidden target. Do
not create or change personal-vault content merely to test setup. If you need a
controlled manual smoke, use a disposable workspace under `test-vault/` and
choose one existing in-scope target and one existing out-of-scope target there.

## Understand the write boundary

`--read-scope` limits read tools only. It does not make the server read-only or
restrict `operation_run` writes to those scopes. Built-in writes remain bounded
by actor authority, engine and operation validation, and the allowed paths in
the operation manifest.

The built-in `operation_run` tool enters Memoria's engine request envelope.
The engine validates the operation, stages output, runs checks, materializes
trusted output, and records journal rows. The agent identity does not bypass
that path or the actor guard.

The optional adapter policy hook is a different boundary. It governs additional
external adapter tools that a host may expose; the built-in Memoria MCP server
does not route `operation_run` through that hook.

## Related

- Tool roster, stdio contract, and scope behavior: [MCP transport](../../reference/commands-and-transports/mcp-transport.md)
- Agent and reserved-operation authority: [Actor Authority Guard](../../reference/control-and-policy/control-plane.md#actor-authority-guard)
- Optional external-adapter boundary: [Policy gate](../../reference/control-and-policy/policy-mcp.md)
- First-init configuration ownership: [Memoria configuration](../../reference/system/configuration.md)
