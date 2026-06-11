---
title: Quickstart
parent: Setup
nav_order: 1
---


# Quickstart

Five steps from zero to a working vault with the co-PI answering. For the full walkthrough with explanations, see [Tutorial 01: Set up from zero](../../tutorials/01-set-up-from-zero.md), or [Set up the vault](set-up-the-vault.md) through [Set up Hermes](set-up-hermes.md).

## Prerequisites

- Git on your `PATH`; on **Windows**, WSL2 enabled ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install))
- A `KILOCODE_API_KEY` (the shipped model provider is `kilocode` — kilo.ai) and an `OPENALEX_API_KEY` ([openalex.org/settings/api](https://openalex.org/settings/api) — required since 2026-02)
- The installer provisions Hermes (+ the ACP extra) and guides the Obsidian install — you don't need them beforehand. Zotero is optional and comes later ([Tutorial 03: Bring in a paper](../../tutorials/03-bring-in-a-paper.md))

## Steps

**1. Install.** One line (inspect the script first if you like — see the raw URL):

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows (PowerShell): gates WSL2, then runs the Linux installer
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

The installer provisions Hermes, scaffolds and populates your runtime vault (default `~/Memoria`, off OneDrive), deploys the **five profiles** (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`), and wires the maintenance crons.

**2. Open the vault in Obsidian.** Open the folder the installer reported (default `~/Memoria`) → Open folder as vault. The required plugins ship pre-installed in `.obsidian/plugins/` — turn off **Restricted mode** (Settings → Community plugins) to activate them, then restart Obsidian. You do not browse or install plugins.

**3. Fill the secrets.** Copy the `apiKey` from Settings → Local REST API, then put your keys in the **global** `~/.hermes/.env`:

```bash
KILOCODE_API_KEY=...      # model access
OBSIDIAN_API_KEY=...      # 64-char hex from the Local REST API plugin
OPENALEX_API_KEY=...      # enrichment + discovery
```

Propagate them into every profile (profile runs read only their own `.env`):

```bash
bash scripts/install.sh --profiles-only --vault ~/Memoria
```

**4. Make the vault a git repo.** obsidian-git and the pre-commit schema gate need one, and the installer deliberately doesn't `git init` for you:

```bash
cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"
```

**5. Bring in your first source.** In Obsidian: `Cmd/Ctrl-P` → **Memoria: capture source from URL** and paste a paper's URL (one with a resolvable DOI) — or open the Agent Client pane and tell the co-PI "bring in this paper: `<DOI>`". The Librarian's lane does the rest and raises a candidate card in your Inbox.

## Verify

- `hermes profile list` shows the five `memoria-*` profiles
- `<vault>/catalog/papers/<citekey>.md` exists with `type: paper` and a `relationships` block
- `<vault>/system/logs/audit.jsonl` shows at least one `allow_with_log` entry
- A `candidate` card landed in `inbox/` (the **What needs me** view on `home.md`)

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Plugin activation details: [Set up Obsidian](set-up-obsidian.md)
- API keys and profile secrets: [Set up Hermes](set-up-hermes.md)
- Optional bibliographic backbone: [Set up Zotero](../zotero/set-up-zotero.md)
