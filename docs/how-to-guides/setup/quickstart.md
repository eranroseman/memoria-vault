---
title: Quickstart
parent: Setup
nav_order: 1
---


# Quickstart

Four steps from zero to an installed vault. For the full walkthrough with explanations, see [Set up the vault](set-up-the-vault.md) through [Set up Hermes](set-up-hermes.md). Once you're installed, learn Memoria itself with [Tutorial 01: See what you're building](../../tutorials/01-orient.md).

## Prerequisites

- Git on your `PATH`; on **Windows**, PowerShell 5.1+ for the native production installer. Sandbox images must include Git too.
- A `KILOCODE_API_KEY` (the shipped model provider is `kilocode` — kilo.ai) and an `OPENALEX_API_KEY` ([openalex.org/settings/api](https://openalex.org/settings/api) — required since 2026-02)
- The installer provisions Hermes (+ the ACP extra) and guides the Obsidian install — you don't need them beforehand. Zotero is optional and comes later ([Tutorial 02](../../tutorials/02-bring-in-your-first-source.md)).

## Steps

**1. Install.** One line (inspect the script first if you like — see the raw URL):

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows production (PowerShell): native Hermes + native vault
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

The installer provisions Hermes, scaffolds your runtime vault (default `~/Memoria`), deploys the **five profiles** (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`), and wires the maintenance crons — full walkthrough in [Set up the vault](set-up-the-vault.md).

**2. Open the vault in Obsidian.** Open the folder the installer reported (default `~/Memoria`) → Open folder as vault. The required plugins ship pre-installed in `.obsidian/plugins/` — turn off **Restricted mode** (Settings → Community plugins) to activate them, then restart Obsidian. You do not browse or install plugins.

**3. Fill the secrets.** Copy the `apiKey` from Settings → Local REST API, then put your keys in the shared Hermes env file (`%LOCALAPPDATA%\hermes\.env` on Windows, `~/.hermes/.env` on Linux/WSL2). At minimum you need `KILOCODE_API_KEY` (model access), the `OBSIDIAN_*` keys (the REST API key, port, and cert path), and `OPENALEX_API_KEY` — the full annotated list is in [Set up Hermes](set-up-hermes.md).

Propagate them into every profile (profile runs read only their own `.env`):

```powershell
.\scripts\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria"
```

```bash
bash scripts/install.sh --profiles-only --vault ~/Memoria
```

**4. Make the vault a git repo.** The installer deliberately doesn't `git init` for you; obsidian-git, rollback/history, the pre-commit schema check, and verify-on-commit need a repo:

```bash
cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"
```

The remote-and-backup details are in [Set up the vault](set-up-the-vault.md).

On a fresh vault, empty tables are normal. The Inbox, Library, Knowledge, and
Project spaces each show a **First actions** callout above their Bases views; use
those commands as the day-1 path for the space you are in.

## Verify

- `hermes profile list` shows the five `memoria-*` profiles
- `Cmd/Ctrl-P` → `Mem` lists the `Memoria:` commands
- The runtime vault has a `.git/` directory after the initial commit

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Plugin activation details: [Set up Obsidian](set-up-obsidian.md)
- API keys and profile secrets: [Set up Hermes](set-up-hermes.md)
- First source walkthrough: [Tutorial 02](../../tutorials/02-bring-in-your-first-source.md)
- Optional bibliographic backbone: [Set up Zotero](../zotero/set-up-zotero.md)
