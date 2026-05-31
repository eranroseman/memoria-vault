
# How to set up Obsidian

Open the vault in Obsidian, install the required plugins, and configure the REST API key.

## Prerequisites

- Obsidian installed ([obsidian.md](https://obsidian.md))
- The vault cloned and `install.ps1` run ([set-up-the-vault.md](set-up-the-vault.md))

## Steps

**1. Open the vault.**

In Obsidian: Open vault → Open folder as vault → navigate to the `vault/` subfolder of the cloned repo. The vault name shown is whatever that folder is called on disk.

**2. Enable community plugins.**

The starter vault **ships all eight required plugins pre-installed and configured** in `.obsidian/plugins/` — you do not browse or install them. The only action is to allow Obsidian to load them:

Settings → Community plugins → turn off **Restricted mode**. The bundled plugins activate on the next restart.

The eight bundled plugins:

| Plugin | Purpose |
| --- | --- |
| `obsidian-local-rest-api` | Hermes writes into the vault over this API |
| `agent-client` | Routes human ↔ Hermes conversations through a chat pane |
| `obsidian-citation-plugin` | Reads `library.bib`; creates paper notes from the inline template |
| `callout-manager` | Renders `[!brief]`, `[!suggestions]`, `[!verification]` callout types |
| `dataview` | Powers all dashboards and queue views (dataviewjs enabled) |
| `templater-obsidian` | Runs templates for new notes |
| `quickadd` | Registers `Memoria:` command-palette entries |
| `obsidian-git` | Scheduled, version-controlled vault commits |

All settings ship pre-configured except the per-machine ones below (REST API secrets, agent-client agent paths). See [reference/plugins.md](../../reference/plugins.md) for the load-bearing settings of each.

**3. Configure the REST API plugin.**

The REST API plugin stores its config in a gitignored `data.json`. Copy the example file to bootstrap it:

```powershell
Copy-Item .obsidian\plugins\obsidian-local-rest-api\data.json.example `
          .obsidian\plugins\obsidian-local-rest-api\data.json
```

**4. Restart Obsidian.**

On restart the plugin regenerates a real `apiKey` (64-char hex token) and its TLS material. You should see "Local REST API: started" in the bottom-right status bar.

**5. Copy the API key.**

Settings → Local REST API → copy the `apiKey` value. You'll need it when filling the Librarian's `.env` in [set-up-hermes.md](set-up-hermes.md).

**6. Confirm plugin settings match the shipped defaults.**

The required plugins ship with their settings pre-configured in `.obsidian/plugins/`. Confirm:

- Local REST API: HTTPS on port **27124**, loopback-only, insecure HTTP server **off**
- Obsidian Citation Plugin: bibliography path set to `.memoria/library.bib`

**7. (Only if you add the frontend Obsidian Linter) set its exclusions.**

Memoria does **not** ship the frontend `obsidian-linter` plugin — it is deferred per [ADR-24 / decision 12](../../../project-files/decisions/12-obsidian-linter-reference-only.md) because it writes outside the policy MCP audit trail. Memoria's linting is the `memoria-linter` Hermes profile, not this plugin.

If you choose to install it anyway, it must never run on agent-maintained folders. Settings → Obsidian Linter → Folders to ignore — add:

```text
10-inbox/
20-sources/
30-synthesis/02-reference/
```

This prevents the Linter from stripping the `_proposed_classification` HTML comment blocks the Librarian writes. See [recovery guides](../../how-to-guides/recovery/) for the failure mode if you skip this.

## Verify

- Status bar shows "Local REST API: started"
- Settings → Local REST API shows a 64-char hex `apiKey`
- Opening any template via the command palette (`Cmd-P → Templater`) renders without errors

## Related

- Next step: [Set up Zotero](set-up-zotero.md)
- Plugin reference: [reference/plugins/](../../reference/plugins.md)
- Callout types: [reference/obsidian-callouts](../../reference/obsidian-callouts.md)
- Workspaces reference: [reference/obsidian-workspaces.md](../../reference/obsidian-workspaces.md)
