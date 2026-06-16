---
title: Set up Obsidian
parent: Setup
nav_order: 3
---


# Set up Obsidian

Open the vault in Obsidian, activate the bundled plugins, and copy the REST API key.

## Prerequisites

- Obsidian installed ([obsidian.md](https://obsidian.md)) — or let the bootstrap guide you through it
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))

## Steps

**1. Open the vault.**

In Obsidian: Open vault → Open folder as vault → navigate to the runtime vault the installer created (default `~/Memoria`, off OneDrive). The vault name shown is whatever that folder is called on disk. `home.md` opens as the front door.

**2. Enable community plugins.**

The vault **ships its plugins pre-installed and configured** in `.obsidian/plugins/` — you do not browse or install them. The only action is to allow Obsidian to load them:

Settings → Community plugins → turn off **Restricted mode**. The bundled plugins activate on the next restart.

The required plugins:

| Plugin | Purpose |
| --- | --- |
| `obsidian-local-rest-api` | Hermes reaches the vault over this plugin's native MCP |
| `agent-client` | The Co-PI chat pane (ACP) inside Obsidian |
| `obsidian-citation-plugin` | Reads `.memoria/memoria.bib`; inserts citations |
| `callout-manager` | Renders `[!brief]`, `[!suggestions]`, `[!verification]` callout types |
| `dataview` | Powers the dashboards and queue views |
| `templater-obsidian` | Runs the templates in `system/templates/` for new notes |
| `quickadd` | Registers the `Memoria:` command-palette entries |
| `cmdr` | Places frequent `Memoria:` commands in the ribbon and page header |
| `modalforms` | Provides structured capture forms with controlled vocabulary fields |
| `obsidian-git` | Scheduled, version-controlled vault commits |
| `homepage` | Opens `home.md` on launch |
| `buttons` | Renders the command buttons on `home.md` |

All settings ship pre-configured except the per-machine ones below (REST API secrets, agent-client command paths). See [Obsidian plugins](../../reference/obsidian-plugins.md) for the load-bearing settings of each.

**3. Configure the REST API plugin.**

The REST API plugin stores its config in a gitignored `data.json`. Copy the example file to bootstrap it:

```bash
cp .obsidian/plugins/obsidian-local-rest-api/data.json.example \
   .obsidian/plugins/obsidian-local-rest-api/data.json
```

**4. Restart Obsidian.**

On restart the plugin regenerates a real `apiKey` (64-char hex token) and its TLS material. You should see "Local REST API: started" in the bottom-right status bar.

**5. Copy the API key and HTTPS certificate path.**

Settings → Local REST API → copy the `apiKey` value. It goes into `OBSIDIAN_API_KEY` in the shared Hermes env file (`%LOCALAPPDATA%\hermes\.env` on Windows, `~/.hermes/.env` on Linux/WSL2) in [Set up Hermes](set-up-hermes.md).

Export or copy the plugin's HTTPS certificate/CA bundle as a PEM file and keep
that path for `OBSIDIAN_MCP_SSL_VERIFY`. The path is machine-local; do not commit
the certificate or a real plugin `data.json`.

**6. Confirm plugin settings match the shipped defaults.**

- Local REST API: **HTTPS server ON, port 27124** (loopback-only) — Hermes reaches the vault over the plugin's native MCP at `https://127.0.0.1:27124/mcp` and verifies the plugin cert through `OBSIDIAN_MCP_SSL_VERIFY` ([ADR-31](../../adr/31-native-obsidian-mcp.md)). Keep `OBSIDIAN_MCP_PORT` in the shared Hermes env file equal to this port.
- Obsidian Citation Plugin: bibliography path set to `.memoria/memoria.bib`

**7. Do not install the frontend Obsidian Linter.**

Memoria is **incompatible** with the frontend `obsidian-linter` plugin — do not install it. It is a second frontmatter authority that collides with the agent-owned namespaces and bypasses the policy-MCP audit trail; the full rationale is in [ADR-12](../../adr/12-obsidian-linter-reference-only.md).

Memoria's linting is the Linter **engine** — deterministic Python with a daily cron and a pre-commit gate ([Linter: detectors and auto-fix](../../reference/linter.md)); `markdownlint` covers Markdown hygiene. Neither needs this plugin.

## Verify

- Status bar shows "Local REST API: started"
- Settings → Local REST API shows a 64-char hex `apiKey`
- `Cmd/Ctrl-P` → `Mem` lists the `Memoria:` commands ([Obsidian command palette](../../reference/obsidian-command-palette.md))
- The left ribbon includes Memoria capture, delegate, resolve, and workspace-switch buttons
- Modal Forms lists the `memoria-source-capture` form
- `Cmd/Ctrl-P` → `Memoria: workspace` lists **Desk**, **Library**, and **Studio**

Once Hermes is set up, the working loop is: open the Co-PI pane (the Agent Client pane, or `hermes -p memoria-copi acp`), then load the **Library** workspace (`Memoria: open Library workspace`) to work the reading pipeline.

## Related

- Next step: [Set up Hermes](set-up-hermes.md)
- Plugin reference: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Callout types: [Obsidian callouts](../../reference/obsidian-callouts.md)
- Workspaces reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
