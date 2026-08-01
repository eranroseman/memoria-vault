---
title: Set up the vault
parent: Setup
grand_parent: How-to guides
nav_order: 2
---


# Set up the vault

Run the bootstrap installer to provision the standalone CLI/runtime workspace and lay the vault down. This is the foundation step; the package seed includes the default Memoria Obsidian adapter/config and first-init agent/MCP host configuration.

## Prerequisites

- Git and Python 3.12+ with venv support on your `PATH`; sandbox images must include Git too.
- Windows PowerShell 5.1+ on Windows, or Ubuntu/Debian/WSL for the Linux path — macOS is not supported.
- Obsidian is optional as an app, but the workspace seed includes Memoria's
  Obsidian adapter files and core settings.
- The initial workspace also receives agent/MCP host configuration. It configures
  hosts but does not install any external agent runtime.

## Steps

**1. Run the bootstrap.** The one-liner sets up the standalone runtime; inspect the script first if you like.

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows:
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

Prefer to see it first? Clone and run from the **repo root** (the installers live there, not inside `src/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or .\scripts/install.ps1 on Windows
```

**2. Confirm each step.** The installer asks before each external step and
creates the runtime vault folder (default `~/Memoria` on Linux/WSL,
`%USERPROFILE%\Memoria` on Windows; keep it off OneDrive or any cloud-synced
tree), then prints the vault-local CLI commands when it finishes. For exactly
what it installs, seeds, skips, and refuses — including the `memoria init
--no-obsidian` opt-out — see the
[Installer reference](../../reference/system/installer.md).

**3. Add a remote** (optional).

The installer already committed the seeded workspace (`initialize memoria workspace`); the runtime vault is your repo, under your identity. If you want a remote, add one and push:

```bash
git remote add origin git@github.com:<your-handle>/<your-vault-repo>.git   # optional — your own repo
git push -u origin main                                                    # replace `main` if your default branch differs
```

The remote is your own vault repository, not the starter repo.

## Verify

```bash
~/Memoria/.memoria/.venv/bin/memoria doctor bundle --workspace ~/Memoria
~/Memoria/.memoria/.venv/bin/memoria status --workspace ~/Memoria
```

## Related

- Obsidian adapter setup: [Set up Obsidian](set-up-obsidian.md)
- Back up the vault outside Git: [Back up and restore the workspace](../operate/back-up-and-restore-the-workspace.md)
- Installer reference: [Installer (bootstrap)](../../reference/system/installer.md)
