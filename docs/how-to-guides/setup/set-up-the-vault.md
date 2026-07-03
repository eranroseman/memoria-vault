---
title: Set up the vault
parent: Setup
grand_parent: How-to guides
nav_order: 2
---


# Set up the vault

Run the bootstrap installer to provision the standalone CLI/runtime workspace and lay the vault down. This is the foundation step — optional adapter setup builds on it.

## Prerequisites

- Git and Python 3 with venv support on your `PATH`; sandbox images must include Git too.
- Windows PowerShell 5.1+ on Windows, or Ubuntu/Debian/WSL for the Linux path — macOS is not supported.
- Hermes and Obsidian are optional adapter dependencies, not prerequisites for the standalone CLI/runtime.

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

**2. What it does.** With your confirmation at each external step, the installer scaffolds and populates your runtime vault from `vault-template/` (default `~/Memoria` on Linux/WSL, `%USERPROFILE%\Memoria` on Windows; keep it off OneDrive), installs runtime dependencies and the Memoria package into `.memoria/.venv`, registers qmd search, wires local hooks, and prints the vault-local CLI commands.

The installer is standalone-only. It does not install Hermes, profiles, lane
overrides, profile skills, Hermes crons, Obsidian setup, or Zotero integration.

**3. Make your first git checkpoint** (recommended).

The installer initializes Git so hooks work immediately, but the runtime vault is your repo, under your identity. From the runtime folder:

```bash
git add -A && git commit -m "Initial Memoria vault"
git remote add origin git@github.com:<your-handle>/<your-vault-repo>.git   # optional — your own repo
git push -u origin main                                                    # if you added a remote
```

The remote (your own, not the starter repo) enables backup, multi-machine sync, and the version history the runtime and Linter depend on. A sandbox without a real `git` binary is an unsupported degraded runtime, because the commit hooks and rollback/history assumptions cannot run.

## Verify

```bash
~/Memoria/.memoria/.venv/bin/memoria doctor bundle --workspace ~/Memoria
~/Memoria/.memoria/.venv/bin/memoria status --workspace ~/Memoria
```

## Related

- Optional UI adapter: [Set up Obsidian](set-up-obsidian.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
