---
title: How to add a second vault
parent: Setup
---


# How to add a second vault

Fork the starter vault for a separate project or research area, keeping it independent from your primary vault while sharing the same Hermes profiles.

## Prerequisites

- Your primary vault is working ([quickstart.md](quickstart.md))
- Hermes is installed and on your `PATH`
- A separate GitHub repo for the second vault (or plan to create one)

## Steps

**1. Choose a folder for the second vault.**

You already have the repo from your primary setup — no need to re-clone. Pick a distinct folder, e.g. `~/my-second-vault`; step 2 lays the vault down there.

**2. Register the second vault's profiles under unique aliases.**

The default aliases (`memoria-librarian`, etc.) belong to your primary vault, and the installer does not yet support an alias prefix. Lay down the second vault (this temporarily re-points the shared `memoria-*` profiles at it), then duplicate the deployed profiles under a `project2-*` alias:

```bash
# from your repo clone — copy the vault out + deploy (memoria-* now point at it):
bash install.sh --vault ~/my-second-vault

# duplicate each deployed profile under a project2-* alias (its mcp.json already
# has the substituted second-vault path):
for role in librarian mapper socratic writer verifier coder linter; do
  hermes profile install ~/.hermes/profiles/memoria-$role --alias project2-$role --force --yes
done

# restore the memoria-* profiles to your primary vault:
bash install.sh --profiles-only --vault ~/your-primary-vault
```

This leaves `project2-librarian`, `project2-linter`, etc. pointing at the second vault while `memoria-*` keep pointing at your primary.

> **Note.** A built-in `--alias-prefix` flag is a future enhancement; until then this manual duplication is the supported route.

**3. Open the second vault in Obsidian.**

Obsidian supports multiple vaults. File → Open Another Vault → Open folder as vault → select `~/my-second-vault` (the folder the installer copied the vault to).

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
