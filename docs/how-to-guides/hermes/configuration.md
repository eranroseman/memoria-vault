
# How to configure a Hermes profile

Edit a profile's `.env`, `config.yaml`, `mcp.json`, or `lane-overrides` to change its behavior — model routing, allowed skills, write permissions, or API credentials.

## Where profile files live

Each profile has two locations:

| Location | Purpose |
| --- | --- |
| `vault/.memoria/profiles/memoria-<name>/` | **Vault source** — version-controlled, authoritative |
| `~/.hermes/profiles/memoria-<name>/` | **Deployed copy** — what Hermes actually runs |

Always edit the vault source. Re-deploy with `bash install.sh --profiles-only` (`.\install.ps1 -ProfilesOnly` on Windows) to push changes to the deployed copy. Never edit the deployed copy directly — it will be overwritten on the next install.

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
  provider: kilocode                       # your gateway/provider
  base_url: https://api.kilo.ai/api/gateway
  default: ~anthropic/claude-opus-latest   # the model string (provider/model)
```

The key is `default` (not `name`). For direct Anthropic instead, use `provider: anthropic`, `default: claude-opus-4-8`, and omit `base_url`. The shipped profiles set **only** the `model` block (plus a `hooks` block) — everything else inherits from the global `~/.hermes/config.yaml`, because Hermes replaces a config section wholesale rather than deep-merging.

3. Save and re-deploy: `bash install.sh --profiles-only` (`.\install.ps1 -ProfilesOnly` on Windows).

## Auxiliary models (set globally, not per-profile)

Hermes runs several cheap, high-frequency tasks through *auxiliary* model slots — title generation, context compression, command approval, MCP tool routing, skills-hub search. Each defaults to `provider: auto`, meaning it **reuses the profile's main model**. For Memoria that's wasteful: a Verifier or Socratic compression/title call would burn **Opus**.

Set these once in your **global** `~/.hermes/config.yaml` — *not* in a profile's `config.yaml`. Hermes replaces a config section wholesale, so a per-profile `auxiliary:` block would clobber the global one. Point the bookkeeping tasks at the Haiku tier:

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: ~anthropic/claude-haiku-latest }
  compression:      { provider: kilocode, model: ~anthropic/claude-haiku-latest }
  approval:         { provider: kilocode, model: ~anthropic/claude-haiku-latest }
  mcp:              { provider: kilocode, model: ~anthropic/claude-haiku-latest }
  skills_hub:       { provider: kilocode, model: ~anthropic/claude-haiku-latest }
  # vision / web_extract: point at a cheap multimodal model only if you use image/page analysis
```

This keeps the expensive tiers (Sonnet/Opus) for actual agent work and routes the high-frequency bookkeeping calls to Haiku. Restart Hermes after editing the global config.

## Change write permissions (lane overrides)

Lane overrides control which vault folders a profile can write to. They live at `vault/.memoria/lane-overrides/<name>.yaml`, not inside the profile directory.

Example — restrict the Librarian to write only to `10-inbox/` and `20-sources/`:

```yaml
profile: memoria-librarian
policy:
  allow:
    write:
      - "10-inbox/**"
      - "20-sources/**"
  deny:
    write:
      - "30-synthesis/**"
      - "40-workbench/**"
      - "50-deliverables/**"
  require:
    - audit_log
routing:
  invocation: dispatched
  external_api_policy: explicit_only
  write_scope:
    - "10-inbox/"
    - "20-sources/"
```

You do **not** declare review-gating per lane: writes to the review-gated zones (`30-synthesis/01-claims`, `02-reference`, `03-moc`, `50-deliverables`) are automatically degraded to `dry_run` by the policy MCP. `audit_log` is a token in the `require:` list (the log path is fixed at `00-meta/02-logs/audit.jsonl`), not a key.

After editing, re-deploy (`bash install.sh --profiles-only`) — the installer picks up lane-override changes on every run.

## Add or remove a skill

Skills live in `vault/.memoria/profiles/memoria-<name>/skills/`. Each skill is a `.yaml` or `.md` file defining the skill's commands and context.

To add a skill, copy the skill file into the profile's `skills/` directory and re-deploy (`bash install.sh --profiles-only`). To remove one, delete the file and re-deploy.

## Update API credentials

Edit the `.env` in the **deployed** copy directly (never in the vault source — `.env` files are gitignored):

```powershell
notepad "$env:USERPROFILE\.hermes\profiles\memoria-librarian\.env"
```

No installer run needed — `.env` changes take effect on the next session start.

## Verify a configuration change

After re-deploying:

```bash
hermes profile show memoria-<name>
```

Confirms the deployed profile reflects your vault source changes.

For lane-override changes, check the audit log after the next write operation to confirm the new policy is enforced.

## Related

- Deploy vault source to profiles: [redeploy-profiles.md](../maintenance/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [fix-profile-drift.md](../recovery/fix-profile-drift.md)
- Lane override reference: [reference/policy-mcp.md](../../reference/policy-mcp.md)
- Profile design: [explanation/profiles/](../../explanation/profiles/)
