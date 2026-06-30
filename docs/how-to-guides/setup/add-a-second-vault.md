---
title: Add a second vault
parent: Setup
grand_parent: How-to guides
nav_order: 7
---

# Add a second vault

Fork the starter vault for a separate project or research area, keeping it independent from your primary vault while sharing the same Hermes profiles.

## Prerequisites

- Your primary vault is working ([Quickstart](quickstart.md))
- Hermes is installed and on your `PATH`
- A separate GitHub repo for the second vault (or plan to create one)

## Steps

**1. Choose a folder for the second vault.**

You already have the repo from your primary setup — no need to re-clone. Pick a distinct folder, e.g. `~/my-second-vault`; step 2 lays the vault down there.

**2. Register the second vault's profiles under unique aliases.**

The default aliases (`memoria-librarian`, etc.) belong to your primary vault, and the installer does not yet support an alias prefix. Lay down the second vault (this temporarily re-points the shared `memoria-*` profiles at it), then duplicate the deployed profiles under a `project2-*` alias:

```bash
# from your repo clone — copy the vault out + deploy (memoria-* now point at it):
bash scripts/install.sh --vault ~/my-second-vault

# duplicate each deployed profile under a project2-* alias (its config.yaml already
# has the substituted second-vault path):
for role in copi librarian writer peer-reviewer engineer; do
  hermes profile install ~/.hermes/profiles/memoria-$role --alias project2-$role --force --yes
done

# restore the memoria-* profiles to your primary vault:
bash scripts/install.sh --profiles-only --vault ~/your-primary-vault
```

This leaves `project2-copi`, `project2-librarian`, etc. pointing at the second vault while `memoria-*` keep pointing at your primary.

> **Note.** A built-in `--alias-prefix` flag is a future enhancement; until then this manual duplication is the supported route.

**3. Open the second vault in Obsidian.**

Obsidian supports multiple vaults. File → Open Another Vault → Open folder as vault → select `~/my-second-vault` (the folder the installer copied the vault to).

**4. Install the same set of required plugins** in this vault (same as step 2 of [Set up Obsidian](set-up-obsidian.md)). Each vault has its own `.obsidian/` config.

**5. Give the second vault its own MCP port and copy its key.**

Each vault's Obsidian instance runs its own Local REST API plugin, and two instances can't share the same HTTPS port ([Set up Obsidian](set-up-obsidian.md) covers the port itself). In the second vault's Local REST API settings, set a distinct HTTPS port (for example, `27125`), export that instance's PEM certificate/CA bundle, and restart Obsidian. Then, in each second-vault profile's `.env`:

- `OBSIDIAN_MCP_PORT` = that port (e.g. `27125`), so the native MCP targets the right instance.
- `OBSIDIAN_API_KEY` = the second instance's `apiKey` (Settings → Local REST API).
- `OBSIDIAN_MCP_SSL_VERIFY` = the second instance's exported PEM certificate/CA bundle path.

> **Tip — full isolation.** To keep the two vaults' profiles, skills, and `.env`s completely separate, install the second vault under its own Hermes home: `HERMES_HOME=~/.hermes-project2 bash scripts/install.sh --vault ~/my-second-vault`. Each `HERMES_HOME` then owns an independent set of `memoria-*` profiles, sidestepping the alias dance above.

**6. Set up Zotero for the second vault.**

No per-vault Better BibTeX auto-export is needed. Keep citekeys stable in
Zotero; each vault regenerates its own `references.bib` from checked SQLite
catalog rows.

## Verify

```bash
hermes profile list
```

Both the primary (`memoria-*`) and second vault (`project2-*`) profiles appear.

Test ingest on the second vault:

```bash
hermes -p project2-librarian chat
# in session: ask it to dry-run an ingest of a known citekey
```

The dry-run output should show paths inside `my-second-vault/`, not your primary vault.

## What collides when two vaults run at once

The steps above isolate the three resources two vaults would otherwise contend for — the Obsidian REST API port (step 5), the Hermes profiles (step 2 aliases or a separate `HERMES_HOME`), and the Kanban queue (a separate `HERMES_HOME`). For what each fix protects against and why coexistence works this way, see [Distribution model → Running more than one vault](../../design/distribution-model.md#running-more-than-one-vault).

## Related

- First vault setup: [Set up the vault](set-up-the-vault.md)
- Redeploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- Distribution model explanation: [Distribution model](../../design/distribution-model.md)
