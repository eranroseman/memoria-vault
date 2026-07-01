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
- Windows PowerShell 5.1+ for the current Windows adapter path, or Ubuntu/Debian/WSL for the standalone Linux/WSL path — macOS is not supported.
- Hermes and Obsidian are optional adapter dependencies, not prerequisites for the standalone CLI/runtime.

## Steps

**1. Run the bootstrap.** The one-liner sets up the standalone runtime; inspect the script first if you like.

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows adapter path (PowerShell): native Hermes, native profiles, native vault
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

Prefer to see it first? Clone and run from the **repo root** (the installers live there, not inside `src/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or .\scripts/install.ps1 on Windows
```

**2. What it does.** With your confirmation at each external step, the Linux/WSL installer scaffolds and populates your runtime vault from `vault-template/` (default `~/Memoria`; keep it off OneDrive), stages the golden copy, installs runtime dependencies and the Memoria package into `.memoria/.venv`, registers qmd search, and prints the vault-local CLI commands.

Add `--with-hermes` when you want the Linux/WSL Hermes/Obsidian adapter. That adapter path also:

- Installs Hermes and verifies ACP.
- Stages the profile files from `<vault>/.memoria/profiles/memoria-<name>/`.
- Substitutes `{{VAULT_PATH}}`, `{{PYTHON}}`, `{{QMD}}`, and model values in `config.yaml`.
- Calls `hermes profile install` to register the five profiles.
- Copies `.env.EXAMPLE` to `.env` for each profile on first install.
- Wires the Hermes cron wrappers.

It is idempotent. To re-deploy only the profiles after editing the vault source, run `bash scripts/install.sh --profiles-only` on Linux/WSL2 (`.\scripts\install.ps1 -ProfilesOnly` on Windows) — what that flag re-deploys is in [Redeploy profiles](../operate/redeploy-profiles.md).

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

With the Hermes adapter, also verify:

```bash
hermes profile list
```

All five `memoria-*` profiles should appear. If a profile is missing, the script reported that its required files weren't present — re-run with `--with-hermes` and read its output.

With the Hermes adapter, check that `{{VAULT_PATH}}` was substituted:

```powershell
Get-Content "$env:LOCALAPPDATA\hermes\profiles\memoria-librarian\config.yaml"
```

The `policy` server path should show an absolute vault path, not the `{{VAULT_PATH}}` placeholder. If the placeholder is still there, re-run `.\scripts\install.ps1 -ProfilesOnly` on Windows or `bash scripts/install.sh --profiles-only` on Linux/WSL2.

## Related

- Optional UI adapter: [Set up Obsidian](set-up-obsidian.md)
- Optional profile secrets: [Set up Hermes](set-up-hermes.md)
- Redeploying profile configuration: [Redeploy profiles](../operate/redeploy-profiles.md)
