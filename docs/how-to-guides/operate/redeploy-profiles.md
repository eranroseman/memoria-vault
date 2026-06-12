---
title: Redeploy profiles
parent: Operate
nav_order: 4
---


# Redeploy profiles

Push vault source edits — to `SOUL.md`, `config.yaml`, skills, or lane-overrides — out to the installed copies in `~/.hermes/profiles/`.

## When to redeploy

- After editing any author-owned file in `<vault>/.memoria/profiles/memoria-<name>/`
- After editing `<vault>/.memoria/lane-overrides/<name>.yaml`
- After a `git pull` that changed profile files
- After adding or rotating a key in `~/.hermes/.env` (the redeploy propagates it into each profile's `.env`)

## Steps

**1. Redeploy all profiles.** Run from the repo clone (it holds the installer); `--profiles-only` skips the full bootstrap and just re-deploys MCP dependencies, the five profiles, and the crons.

```bash
bash scripts/install.sh --profiles-only --vault <vault>      # Linux / WSL2 (where Hermes runs)
```

```powershell
.\scripts/install.ps1 -ProfilesOnly          # Windows (forwards to scripts/install.sh in WSL2)
```

`--vault <dir>` names your runtime vault if it isn't the default `~/Memoria`. The script is idempotent — safe to run at any time. It:

- Stages each profile's files to a temp directory
- Substitutes `{{PYTHON}}` (the vault venv interpreter) and `{{VAULT_PATH}}` in `config.yaml`
- Calls `hermes profile install --force` for each of the five profiles, and prunes any retired profile still registered ([Installer (bootstrap)](../../reference/installer.md))
- Seeds each profile's `.env` from `~/.hermes/.env` — never overwrites a value already set

**2. Redeploy a single profile** (faster when only one changed):

```bash
bash scripts/install.sh --profiles-only --only memoria-librarian
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Only memoria-librarian
```

**3. Confirm the change landed.**

```bash
hermes profile show memoria-<name>
```

The output should reflect the edit you made (e.g., updated model name, new MCP server entry).

For lane-override changes, verify with a test write operation — check `system/logs/audit.jsonl` to confirm the new policy is enforced.

## Verify

```bash
hermes profile list
```

Exactly the five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`) show as registered — no retired names, none missing.

If you suspect the deployed copies still don't match the vault source, compare them directly:

```bash
diff -r <vault>/.memoria/profiles/memoria-librarian ~/.hermes/profiles/memoria-librarian \
  --exclude .env   # config.yaml will differ by the substituted placeholders
```

See [Fix profile drift](../troubleshooting/fix-profile-drift.md) for the full procedure.

## Related

- Profile configuration guide: [Configure a profile](../hermes-agent/configuration.md)
- Fix profile drift: [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Set up profiles (first install): [Set up Hermes](../setup/set-up-hermes.md)
- The flags and the idempotency mechanism: [Installer (bootstrap)](../../reference/installer.md)
