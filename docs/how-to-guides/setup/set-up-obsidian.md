---
title: Set up Obsidian
parent: Setup
nav_order: 3
---


# Set up Obsidian

Open the vault in Obsidian, install the required plugins, and configure the REST API key.

## Prerequisites

- Obsidian installed ([obsidian.md](https://obsidian.md))
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))

## Steps

**1. Open the vault.**

In Obsidian: Open vault → Open folder as vault → navigate to the folder the installer copied the vault to (default `~/Memoria`, off OneDrive). The vault name shown is whatever that folder is called on disk.

**2. Enable community plugins.**

The starter vault **ships all eight required plugins pre-installed and configured** in `.obsidian/plugins/` — you do not browse or install them. The only action is to allow Obsidian to load them:

Settings → Community plugins → turn off **Restricted mode**. The bundled plugins activate on the next restart.

The eight bundled plugins:

| Plugin | Purpose |
| --- | --- |
| `obsidian-local-rest-api` | Hermes writes into the vault over this API |
| `agent-client` | Routes human ↔ Hermes conversations through a chat pane |
| `obsidian-citation-plugin` | Reads `memoria.bib`; creates paper notes from the inline template |
| `callout-manager` | Renders `[!brief]`, `[!suggestions]`, `[!verification]` callout types |
| `dataview` | Powers all dashboards and queue views (dataviewjs enabled) |
| `templater-obsidian` | Runs templates for new notes |
| `quickadd` | Registers `Memoria:` command-palette entries |
| `obsidian-git` | Scheduled, version-controlled vault commits |

All settings ship pre-configured except the per-machine ones below (REST API secrets, agent-client agent paths). See [Obsidian plugins](../../reference/obsidian-plugins.md) for the load-bearing settings of each.

**3. Configure the REST API plugin.**

The REST API plugin stores its config in a gitignored `data.json`. Copy the example file to bootstrap it:

```powershell
Copy-Item .obsidian\plugins\obsidian-local-rest-api\data.json.example `
          .obsidian\plugins\obsidian-local-rest-api\data.json
```

**4. Restart Obsidian.**

On restart the plugin regenerates a real `apiKey` (64-char hex token) and its TLS material. You should see "Local REST API: started" in the bottom-right status bar.

**5. Copy the API key.**

Settings → Local REST API → copy the `apiKey` value. You'll need it when filling the Librarian's `.env` in [Set up Hermes](set-up-hermes.md).

**6. Confirm plugin settings match the shipped defaults.**

The required plugins ship with their settings pre-configured in `.obsidian/plugins/`. Confirm:

- Local REST API: **insecure HTTP server ON, port 27123** (loopback-only) — Hermes reaches the vault over the plugin's native MCP at `http://127.0.0.1:27123/mcp`, because it can't verify the self-signed HTTPS cert on 27124 ([ADR-31](../../../project/adr/31-native-obsidian-mcp.md)). The shipped `data.json.example` enables it; confirm it stayed on. Keep `OBSIDIAN_MCP_PORT` in your `.env` equal to this port.
- Obsidian Citation Plugin: bibliography path set to `.memoria/memoria.bib`

**7. Do not install the frontend Obsidian Linter.**

Memoria is **incompatible** with the frontend `obsidian-linter` plugin — do not install it (see [ADR-12](../../../project/adr/12-obsidian-linter-reference-only.md)). It is a second frontmatter authority: it reformats and reorders frontmatter on save, which collides continuously with the agent-owned `_proposed_classification` / `_enrichment` namespaces the Librarian writes on every ingest, and its writes bypass the policy MCP audit trail. Folder exclusions don't rescue it — `40-workbench/` drafts are both human-edited and agent-written, so no exclusion list is safe.

Memoria's linting is the `memoria-linter` Hermes profile (structural validation under the policy MCP); `markdownlint` covers Markdown hygiene. Neither needs this plugin.

## Verify

- Status bar shows "Local REST API: started"
- Settings → Local REST API shows a 64-char hex `apiKey`
- Opening any template via the command palette (`Cmd-P → Templater`) renders without errors

## Related

- Next step: [Set up Zotero](set-up-zotero.md)
- Plugin reference: [reference/obsidian-plugins/](../../reference/obsidian-plugins.md)
- Callout types: [reference/obsidian-callouts](../../reference/obsidian-callouts.md)
- Workspaces reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
