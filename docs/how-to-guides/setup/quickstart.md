---
title: Quickstart
parent: Setup
nav_order: 1
---


# Quickstart

Five steps from zero to a working vault with the Co-PI answering. For the full walkthrough with explanations, see [Tutorial 01: Set up from zero](../../tutorials/01-set-up-from-zero.md), or [Set up the vault](set-up-the-vault.md) through [Set up Hermes](set-up-hermes.md).

## Prerequisites

- Git on your `PATH`; on **Windows**, PowerShell 5.1+ for the native production installer
- A `KILOCODE_API_KEY` (the shipped model provider is `kilocode` — kilo.ai) and an `OPENALEX_API_KEY` ([openalex.org/settings/api](https://openalex.org/settings/api) — required since 2026-02)
- The installer provisions Hermes (+ the ACP extra) and guides the Obsidian install — you don't need them beforehand. Zotero is optional and comes later ([Tutorial 03: Bring in a paper](../../tutorials/03-bring-in-a-paper.md))

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

**4. Make the vault a git repo.** The installer deliberately doesn't `git init` for you; obsidian-git and the pre-commit schema gate need a repo:

```bash
cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"
```

The remote-and-backup details are in [Set up the vault](set-up-the-vault.md).

**5. Bring in your first source.** In Obsidian: `Cmd/Ctrl-P` → **Memoria: capture source from URL** and paste a paper's URL (one with a resolvable DOI) — or open the Agent Client pane and tell the Co-PI "bring in this paper: `<DOI>`". The Librarian's lane does the rest and raises a candidate card in your Inbox.

## Verify

- `hermes profile list` shows the five `memoria-*` profiles
- `<vault>/catalog/papers/<citekey>.md` exists with `type: paper` and a `relationships` block
- `<vault>/system/logs/audit.jsonl` shows at least one `allow_with_log` entry
- A `candidate` card landed in `inbox/` (the **Needs me** view of `inbox.base`, in the Desk workspace)

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Plugin activation details: [Set up Obsidian](set-up-obsidian.md)
- API keys and profile secrets: [Set up Hermes](set-up-hermes.md)
- Optional bibliographic backbone: [Set up Zotero](../zotero/set-up-zotero.md)
