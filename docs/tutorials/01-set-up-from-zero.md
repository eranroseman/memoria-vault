---
title: "Tutorial 01: Set up from zero"
parent: Tutorials
---

# Tutorial 01: Set up from zero

**You will end with:** a working Memoria vault open in Obsidian, the five profiles installed, the Co-PI answering in the Agent Client pane, and the Library space open.

**Time:** 20–30 minutes.

**You will use:** a terminal (for the installer and your API keys), then Obsidian.

---

## Prerequisites

- Windows PowerShell 5.1+ for production, or Linux/WSL for the test installer
- [Git](https://git-scm.com/) installed (the installer checks and tells you if anything is missing — it provisions the rest itself, including Hermes)
- [Obsidian](https://obsidian.md/) installed, or let the installer guide you through it

You do **not** need Zotero for setup. It is an optional bibliographic backbone, covered where you first use it — [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md).

---

## Step 1 — Run the installer

Download the installer for your platform, read it, then run it.

For Windows production:

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 -OutFile install.ps1
Get-Content .\install.ps1     # read what it will do
.\install.ps1
```

For Linux/WSL testing:

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
less install.sh        # read what it will do
bash install.sh
```

The installer confirms every external step before running it. On screen you'll watch it check prerequisites, then **scaffold → populate → golden-copy** your runtime vault (default `~/Memoria` — pick a folder outside any cloud-synced tree). It deploys the **five profiles** (`memoria-copi` plus the four background lanes) and wires the maintenance crons. When it asks about the optional clustering stack (~2 GB), decline it — graph tools still work, and you can add it later.

When it finishes it prints a **Next steps** checklist. The rest of this tutorial walks that checklist.

Full flag and step reference (the convenience one-liner, `--dry-run`, and adding clustering later): [Installer (bootstrap)](../reference/installer.md).

---

## Step 2 — Add your API keys

Open the shared Hermes env file and fill in your keys — model access, the Obsidian Local REST API key (Step 3 below), the Local REST API HTTPS port and certificate path, and the discovery key. On Windows the file is `%LOCALAPPDATA%\hermes\.env`; on Linux/WSL2 it is `~/.hermes/.env`. The canonical key names and where each comes from are in [Set up Hermes](../how-to-guides/setup/set-up-hermes.md).

Then propagate them into every profile (profile runs read only their own `.env` — there is no global fallback):

```powershell
.\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria"
```

```bash
bash install.sh --profiles-only --vault ~/Memoria
```

Re-run that command any time you add or rotate a key.

---

## Step 3 — Open the vault in Obsidian

1. Open Obsidian → **Open folder as vault** → choose the folder the installer reported (default `~/Memoria`).
2. Turn off Restricted mode when prompted (**Settings → Community plugins**) so the bundled plugins load — they ship pre-installed and pre-configured.
3. Copy the API key from **Settings → Local REST API** into `OBSIDIAN_API_KEY` in the shared Hermes env file. Also set `OBSIDIAN_MCP_PORT` to the plugin's HTTPS port and `OBSIDIAN_MCP_SSL_VERIFY` to the exported certificate path, then re-run the `--profiles-only` command from Step 2.
4. Make the vault a git repo — obsidian-git and the pre-commit hook need one, and the installer deliberately doesn't `git init` for you. The exact init/add/commit commands are in [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).

Obsidian opens the **Inbox** space. The space nav row links Inbox, Library, Knowledge, and Project; `home.md` remains a simple fallback note if the Homepage plugin is disabled.

---

## Step 4 — Open the Co-PI pane

The Co-PI is the one agent you converse with. Open it either way:

- **In Obsidian:** command palette (`Cmd/Ctrl+P`) → **Agent Client: Open chat view**. The pane defaults to the Co-PI.
- **In a terminal:** `hermes -p memoria-copi acp`

Verify the profiles installed first if you like: `hermes profile list` should show all five `memoria-*` profiles.

Say hello and ask it something — "explain how this vault is organized" is a good first question. It questions, explains the system, and delegates tasks to the background lanes; it never writes your vault itself ([The Co-PI](../explanation/profiles/co-pi.md)).

---

## Step 5 — Open the Library space

The vault opens to **Inbox**. Use the dashboard nav row to open **Library** (`spaces/library.md`), then move among Inbox, Library, Knowledge, and Project the same way. See [Obsidian workspaces](../reference/obsidian-workspaces.md).

The Library space opens the reading pipeline, the discuss queue, and the Catalog view — empty for now. They fill as you work through the next tutorials.

---

## What you have

- A runtime vault at `~/Memoria`, scaffolded, populated, and golden-copied
- Five profiles installed and the maintenance crons wired
- API keys in `~/.hermes/.env`, propagated to every profile
- The Co-PI answering in the Agent Client pane
- The Library space open

---

## What's next

[Tutorial 02: Your first note](02-your-first-note.md) — capture a fleeting thought from the palette and learn the distill-or-archive discipline.

**See also:** [Quickstart](../how-to-guides/setup/quickstart.md) for the condensed install path, and [What Memoria is](../explanation/overview/what-memoria-is.md) for what you just installed.

---

[Tutorial 02: Your first note](02-your-first-note.md) →
