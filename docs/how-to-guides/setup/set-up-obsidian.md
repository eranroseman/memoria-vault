
# How to set up Obsidian

Open the vault in Obsidian, install the required plugins, and configure the REST API key.

## Prerequisites

- Obsidian installed ([obsidian.md](https://obsidian.md))
- The vault cloned and `install.ps1` run ([set-up-the-vault.md](set-up-the-vault.md))

## Steps

**1. Open the vault.**

In Obsidian: Open vault → Open folder as vault → navigate to the `vault/` subfolder of the cloned repo. The vault name shown is whatever that folder is called on disk.

**2. Install required community plugins.**

Settings → Community plugins → turn off Restricted mode → Browse. Install each of the following:

| Plugin | Purpose |
| --- | --- |
| `obsidian-local-rest-api` | Hermes writes into the vault over this API |
| `agent-client` | Connects command palette actions to Hermes profiles |
| `obsidian-citation-plugin` | Reads `library.bib` for in-note citations |
| `callout-manager` | Renders `[!brief]` and other Memoria callout types |
| `dataview` | Powers all dashboards and queue views |
| `templater-obsidian` | Runs templates for new notes |

Enable each plugin after install.

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

**7. Set up the Obsidian Linter exclusions** (critical).

The Obsidian Linter plugin must never run on agent-maintained folders. Settings → Obsidian Linter → Folders to ignore — add:

```text
10-inbox/
20-sources/
30-synthesis/02-reference/
```

This prevents the Linter from stripping `_proposed_classification` HTML comment blocks the Librarian writes. See [failure-modes](../../how-to-guides/recovery/) for the failure mode if you skip this.

## Verify

- Status bar shows "Local REST API: started"
- Settings → Local REST API shows a 64-char hex `apiKey`
- Opening any template via the command palette (`Cmd-P → Templater`) renders without errors

## Related

- Next step: [Set up Zotero](set-up-zotero.md)
- Plugin reference: [reference/plugins/](../../reference/plugins.md)
- Callout types: [reference/obsidian-callouts](../../reference/obsidian-callouts.md)
- Workspaces reference: [reference/obsidian-workspaces.md](../../reference/obsidian-workspaces.md)
