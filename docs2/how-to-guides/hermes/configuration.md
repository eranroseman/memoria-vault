
# How to configure a Hermes profile

Edit a profile's `.env`, `config.yaml`, `mcp.json`, or `lane-overrides` to change its behavior — model routing, allowed skills, write permissions, or API credentials.

## Where profile files live

Each profile has two locations:

| Location | Purpose |
| --- | --- |
| `vault/.memoria/profiles/memoria-<name>/` | **Vault source** — version-controlled, authoritative |
| `~/.hermes/profiles/memoria-<name>/` | **Deployed copy** — what Hermes actually runs |

Always edit the vault source. Run `install.ps1` to push changes to the deployed copy. Never edit the deployed copy directly — it will be overwritten on the next install.

## File roles

| File | Controls | Who edits |
| --- | --- | --- |
| `SOUL.md` | Profile identity, persona, behavioral constraints | Author (you) |
| `config.yaml` | Model routing, temperature, context window | Author |
| `mcp.json` | Which MCP servers the profile connects to | Author (installer substitutes `{{VAULT_PATH}}`) |
| `skills/` | Skill definitions the profile can load | Author |
| `cron/` | Scheduled task definitions | Author |
| `.env` | API keys and secrets | **Human only** — never committed to git |

## Change the model for a profile

1. Open `vault/.memoria/profiles/memoria-<name>/config.yaml`
2. Edit the `model` field:

```yaml
model:
  provider: anthropic
  name: claude-opus-4-8
  temperature: 0.3
```

3. Save and run `./install.ps1` to deploy.

## Change write permissions (lane overrides)

Lane overrides control which vault folders a profile can write to. They live at `vault/.memoria/lane-overrides/<name>.yaml`, not inside the profile directory.

Example — restrict the Librarian to write only to `10-inbox/` and `20-sources/`:

```yaml
policy:
  allow:
    write:
      - "10-inbox/"
      - "20-sources/"
  degrade:
    write:
      - path: "30-synthesis/01-claims/"
        to: dry_run
  audit_log: "00-meta/02-logs/audit.jsonl"
```

After editing, run `./install.ps1` — the installer picks up lane-override changes on every run.

## Add or remove a skill

Skills live in `vault/.memoria/profiles/memoria-<name>/skills/`. Each skill is a `.yaml` or `.md` file defining the skill's commands and context.

To add a skill, copy the skill file into the profile's `skills/` directory and run `./install.ps1`. To remove one, delete the file and re-run the installer.

## Update API credentials

Edit the `.env` in the **deployed** copy directly (never in the vault source — `.env` files are gitignored):

```powershell
notepad "$env:USERPROFILE\.hermes\profiles\memoria-librarian\.env"
```

No installer run needed — `.env` changes take effect on the next session start.

## Verify a configuration change

After running `./install.ps1`:

```bash
hermes profile show memoria-<name>
```

Confirms the deployed profile reflects your vault source changes.

For lane-override changes, check the audit log after the next write operation to confirm the new policy is enforced.

## Related

- Deploy vault source to profiles: [redeploy-profiles.md](../maintenance/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [fix-profile-drift.md](../recovery/fix-profile-drift.md)
- Lane override reference: [reference/architecture/policy-mcp.md](../../memoria-vault/docs/reference/architecture/policy-mcp.md)
- Profile design: [explanation/profiles/](../../memoria-vault/docs/explanation/profiles/)
