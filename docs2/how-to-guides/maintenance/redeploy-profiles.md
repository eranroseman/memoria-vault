
# How to redeploy profiles

Push vault source edits — to `SOUL.md`, `config.yaml`, `mcp.json`, skills, or cron tasks — out to the installed copies in `~/.hermes/profiles/`.

## When to redeploy

- After editing any author-owned file in `vault/.memoria/profiles/memoria-<name>/`
- After a `git pull` that changed profile files
- After editing `vault/.memoria/lane-overrides/<name>.yaml`
- After the Linter reports profile install drift

## Steps

**1. Redeploy all profiles.**

```bash
cd vault   # or any subfolder of the vault
./install.ps1
```

The script is idempotent — safe to run at any time. It:

- Stages each profile's files to a temp directory
- Substitutes `{{VAULT_PATH}}` in `mcp.json`
- Calls `hermes profile install --force` for each profile
- Never overwrites `.env` files

**2. Redeploy a single profile** (faster when only one changed):

```powershell
./install.ps1 -Only memoria-linter
```

**3. Confirm the change landed.**

```bash
hermes profile show memoria-<name>
```

The output should reflect the edit you made (e.g., updated model name, new MCP server entry).

For lane-override changes, verify with a test write operation — check `00-meta/02-logs/audit.jsonl` to confirm the new policy is enforced.

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

- Profile configuration guide: [configuration.md](../hermes/configuration.md)
- Fix profile drift: [fix-profile-drift.md](../recovery/fix-profile-drift.md)
- Set up profiles (first install): [set-up-hermes.md](../setup/set-up-hermes.md)
