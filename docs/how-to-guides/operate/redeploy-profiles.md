---
title: Redeploy profiles
parent: Operate
nav_order: 4
---


# Redeploy profiles

Push vault source edits — to `SOUL.md`, `config.yaml`, skills, or cron tasks — out to the installed copies in `~/.hermes/profiles/`.

## When to redeploy

- After editing any author-owned file in `vault/.memoria/profiles/memoria-<name>/`
- After a `git pull` that changed profile files
- After editing `vault/.memoria/lane-overrides/<name>.yaml`
- After the Linter reports profile install drift

## Steps

**1. Redeploy all profiles.** Run from the repo clone (it holds the installer); `--profiles-only` skips the full bootstrap and just re-deploys profiles.

```bash
bash scripts/install.sh --profiles-only      # Linux / WSL2 (where Hermes runs)
```

```powershell
.\scripts/install.ps1 -ProfilesOnly          # Windows (forwards to scripts/install.sh in WSL2)
```

Add `--vault <dir>` (`-Vault <dir>` on Windows) if your runtime vault isn't the default `~/Memoria`. The script is idempotent — safe to run at any time. It:

- Stages each profile's files to a temp directory
- Substitutes `{{VAULT_PATH}}` in `config.yaml`
- Calls `hermes profile install --force` for each profile
- Never overwrites `.env` files

**2. Redeploy a single profile** (faster when only one changed):

```bash
bash scripts/install.sh --profiles-only --only memoria-linter
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Only memoria-linter
```

**3. Confirm the change landed.**

```bash
hermes profile show memoria-<name>
```

The output should reflect the edit you made (e.g., updated model name, new MCP server entry).

For lane-override changes, verify with a test write operation — check `99-system/logs/audit.jsonl` to confirm the new policy is enforced.

## Verify

```bash
hermes profile list
```

All profiles show `status: registered`. No profiles are listed as `missing` or `drift`.

Run the Linter's drift detector:

```bash
hermes -p memoria-linter chat -s health-report
# then, in the session:
/health-report --detectors profile-install-drift
```

Output should show no drift for any profile.

## Related

- Profile configuration guide: [Configure a profile](../hermes-agent/configuration.md)
- Fix profile drift: [Fix profile drift](../recovery/fix-profile-drift.md)
- Set up profiles (first install): [Set up Hermes](../setup/set-up-hermes.md)
- The idempotency mechanism: [Distribution model](../../explanation/deployment/distribution-model.md)
