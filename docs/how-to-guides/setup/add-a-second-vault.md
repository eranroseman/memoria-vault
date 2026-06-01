
# How to add a second vault

Fork the starter vault for a separate project or research area, keeping it independent from your primary vault while sharing the same Hermes profiles.

## Prerequisites

- Your primary vault is working ([quickstart.md](quickstart.md))
- Hermes is installed and on your `PATH`
- A separate GitHub repo for the second vault (or plan to create one)

## Steps

**1. Clone or fork the starter vault into a new folder.**

```bash
git clone https://github.com/<your-handle>/memoria-vault.git my-second-vault
cd my-second-vault/vault
```

Choose a different folder name from your primary vault — the Hermes profile aliases will include this vault's path, so names must not collide.

**2. Run the installer with unique profile aliases.**

The default aliases (`memoria-librarian`, etc.) are already used by your primary vault. Install the second vault's profiles under different names:

```powershell
./install.ps1 -AliasPrefix "project2-"
```

This registers `project2-librarian`, `project2-linter`, etc. — separate Hermes profiles pointing at the second vault's `.memoria/` directory.

> **Note.** If `install.ps1` doesn't yet support `-AliasPrefix`, run it normally and manually rename the profiles in `~/.hermes/profiles/` after install, then update `mcp.json` in each to point at this vault's path.

**3. Open the second vault in Obsidian.**

Obsidian supports multiple vaults. File → Open Another Vault → Open folder as vault → select `my-second-vault/vault/`.

**4. Install the same set of required plugins** in this vault (same as step 2 of [set-up-obsidian.md](set-up-obsidian.md)). Each vault has its own `.obsidian/` config.

**5. Copy the REST API key.**

The second vault's Obsidian instance generates a different `apiKey`. Copy it from Settings → Local REST API and update the `OBSIDIAN_API_KEY` in each second-vault profile's `.env`.

**6. Set up Zotero for the second vault.**

Add a second auto-export in Better BibTeX pointing at `my-second-vault/vault/.memoria/library.bib`. You can share the same Zotero library or create a separate collection.

## Verify

```bash
hermes profile list
```

Both the primary (`memoria-*`) and second vault (`project2-*`) profiles appear.

Test ingest on the second vault:

```bash
hermes -p project2-librarian chat -s obsidian-paper-note
/obsidian-paper-note --source <citekey> --dry-run
```

The dry-run output should show paths inside `my-second-vault/vault/`, not your primary vault.

## Related

- First vault setup: [set-up-the-vault.md](set-up-the-vault.md)
- Redeploying after profile edits: [redeploy-profiles.md](../maintenance/redeploy-profiles.md)
- Distribution model explanation: [distribution-model.md](../../explanation/architecture/distribution-model.md)
