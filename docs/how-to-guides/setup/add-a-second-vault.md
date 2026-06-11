---
title: Add a second vault
parent: Setup
nav_order: 9
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

Each vault's Obsidian instance runs its own Local REST API plugin, and two instances can't share the insecure HTTP port. In the second vault's `data.json`, set a distinct `insecurePort` (e.g. `27125`), keep `enableInsecureServer: true`, and restart Obsidian. Then, in each second-vault profile's `.env`:

- `OBSIDIAN_MCP_PORT` = that port (e.g. `27125`), so the native MCP url targets the right instance ([ADR-31](../../adr/31-native-obsidian-mcp.md)).
- `OBSIDIAN_API_KEY` = the second instance's `apiKey` (Settings → Local REST API).

> **Tip — full isolation.** To keep the two vaults' profiles, skills, and `.env`s completely separate, install the second vault under its own Hermes home: `HERMES_HOME=~/.hermes-project2 bash scripts/install.sh --vault ~/my-second-vault`. Each `HERMES_HOME` then owns an independent set of `memoria-*` profiles, sidestepping the alias dance above. (The HTTPS port 27124 is still single-instance — run the two Obsidian windows on distinct `insecurePort`s as above.)

**6. Set up Zotero for the second vault.**

Add a second auto-export in Better BibTeX pointing at `my-second-vault/.memoria/memoria.bib`. You can share the same Zotero library or create a separate collection.

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

Two vaults run fully in parallel — *if* you isolate the three things they'd otherwise contend for. The steps above already apply each fix; this is what they protect against.

| Resource | What collides if shared | Isolation |
|---|---|---|
| **Obsidian REST API port** | Both Local REST API plugins bind the same insecure HTTP port; the second to start can't bind, so its `OBSIDIAN_MCP_PORT` serves nothing (or points Hermes at the wrong vault). | A distinct `insecurePort` per vault (step 5), with each vault's profiles' `OBSIDIAN_MCP_PORT` matching. |
| **Hermes profiles** | Profiles substitute one `VAULT_PATH` at install; a shared `HERMES_HOME` points `memoria-*` at whichever vault was installed last, so the other vault's agents read and write the wrong tree. | Unique aliases (`project2-*`, step 2) **or** a separate `HERMES_HOME` per vault (the isolation tip in step 5). |
| **Kanban queue** | The board/queue (`hermes kanban`) is Hermes runtime state under `HERMES_HOME`, **not** a file in the vault — so a shared `HERMES_HOME` is one shared queue: cards from both vaults intermix and cron fires against the wrong vault. | A separate `HERMES_HOME` per vault gives each its own independent queue. |

**Safe configuration:** a distinct REST port **and** a separate `HERMES_HOME` per vault → no cross-talk. Sharing the port collides the REST bridge; sharing `HERMES_HOME` collides both the profiles and the kanban queue. This is the sandbox-beside-production coexistence ADR-31 was designed for — the production vault stays untouched while a test vault runs.

## Related

- First vault setup: [Set up the vault](set-up-the-vault.md)
- Redeploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- Distribution model explanation: [Distribution model](../../explanation/deployment/distribution-model.md)
