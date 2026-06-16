---
title: Set up the vault
parent: Setup
nav_order: 2
---


# Set up the vault

Run the bootstrap installer to provision the runtime, lay the vault down, and register the profiles. This is the foundation step — all other setup guides build on it.

## Prerequisites

- Git on your `PATH`
- Windows PowerShell 5.1+ for production, or Ubuntu/Debian/WSL for the Linux test path — macOS is not supported
- The installer provisions Hermes itself (+ the ACP extra); you don't need it beforehand

## Steps

**1. Run the bootstrap.** The one-liner does everything; inspect the script first if you like.

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows production (PowerShell): native Hermes, native profiles, native vault
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

Prefer to see it first? Clone and run from the **repo root** (the installers live there, not inside `src/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or .\scripts/install.ps1 on Windows
```

**2. What it does.** With your confirmation at each external step, the installer scaffolds and populates your runtime vault from `src/` (default `~/Memoria`, off OneDrive), installs Hermes + the ACP extra, provisions skills, and for each of the five profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`):

- Stages the profile files from `<vault>/.memoria/profiles/memoria-<name>/`
- Substitutes `{{VAULT_PATH}}` in `config.yaml` with the runtime vault's absolute path
- Calls `hermes profile install` to register the profile
- Copies `.env.EXAMPLE` to `.env` for each profile (only on first install — existing `.env` files are never overwritten)

It is idempotent. To re-deploy only the profiles after editing the vault source, run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows).

**3. Set up your own git in the vault** (recommended).

The installer copies the vault but does **not** initialize git — the runtime vault is your repo, under your identity. From the runtime folder (default `~/Memoria`):

```bash
git init && git add -A && git commit -m "Initial Memoria vault"
git remote add origin git@github.com:<your-handle>/<your-vault-repo>.git   # optional — your own repo
git push -u origin main                                                    # if you added a remote
```

obsidian-git needs a repo to commit into; the remote (your own, not the starter repo) enables backup, multi-machine sync, and the version history the Librarian and Linter depend on.

## Verify

```bash
hermes profile list
```

All five `memoria-*` profiles appear in the output — no retired names ([Installer (bootstrap)](../../reference/installer.md) lists them), none missing. If a profile is missing, the script reported that its required files weren't present — re-run and read its output.

Check that `{{VAULT_PATH}}` was substituted:

```powershell
Get-Content "$env:USERPROFILE\.hermes\profiles\memoria-librarian\config.yaml"
```

The `policy` server path should show an absolute vault path, not the `{{VAULT_PATH}}` placeholder. If the placeholder is still there, re-run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows).

## Related

- Next step: [Set up Obsidian](set-up-obsidian.md)
- Profile secrets: [Set up Hermes](set-up-hermes.md)
- Re-running after a git pull: [Redeploy profiles](../operate/redeploy-profiles.md)
- Build status: [v0.1 release plan](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1.md)
