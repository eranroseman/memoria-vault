
# How to set up the vault

Clone the starter vault and run the install script to get the folder structure, profiles, and templates in place. This is the foundation step — all other setup guides build on it.

## Prerequisites

- Git on your `PATH`
- PowerShell (Windows) or bash (macOS/Linux)
- Hermes installed and on your `PATH`

## Steps

**1. Clone the starter vault.**

```bash
git clone https://github.com/<your-handle>/memoria-vault.git
```

Choose the folder name freely — the installer detects its own location at runtime.

**2. Navigate into the vault subfolder.**

```powershell
cd memoria-vault\vault
```

The `vault/` subfolder is the Obsidian vault. It contains `.obsidian/`, `.memoria/`, `install.ps1`, and the full folder skeleton (`00-meta/` through `95-archive/`).

**3. Run the install script.**

```powershell
./install.ps1
```

The script is idempotent — safe to re-run. For each of the seven profiles it:

- Stages the profile files from `.memoria/profiles/memoria-<name>/`
- Substitutes `{{VAULT_PATH}}` in `mcp.json` with this vault's absolute path
- Calls `hermes profile install` to register the profile
- Copies `.env.EXAMPLE` to `.env` for each profile (only on first install — existing `.env` files are never overwritten)

**4. Set up a Git remote** (recommended).

```bash
git remote add origin git@github.com:<your-handle>/memoria-vault.git
git push -u origin main
```

This enables the `.bib` distribution and version history that the Librarian and Linter depend on.

## Verify

```bash
hermes profile list
```

All seven `memoria-*` profiles appear in the output. If a profile is missing, the script reported that its required files weren't present — check [implementation-status.md](../../memoria-vault/docs/project/implementation-status.md) for what's currently wired.

Check that `{{VAULT_PATH}}` was substituted:

```powershell
Get-Content "$env:USERPROFILE\.hermes\profiles\memoria-librarian\mcp.json"
```

The `policy` server path should show an absolute vault path, not the `{{VAULT_PATH}}` placeholder. If the placeholder is still there, re-run `./install.ps1`.

## Related

- Next step: [Set up Obsidian](set-up-obsidian.md)
- Profile secrets: [Set up Hermes](set-up-hermes.md)
- Re-running after a git pull: [Redeploy profiles](../maintenance/redeploy-profiles.md)
- Implementation status: [implementation-status.md](../../memoria-vault/docs/project/implementation-status.md)
