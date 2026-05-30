---
topic: operations
---

# Installing and redeploying profiles

How the seven Hermes profiles get from the vault into `~/.hermes/profiles/`, and how to refresh them. The installer (`install.ps1`) is referenced by several failure-mode fixes; this is the procedure those fixes assume.

> **Status.** In the v0.1 scaffold each profile ships only its `SOUL.md` prompt. `install.ps1` requires `SOUL.md` + `config.yaml` + `mcp.json` + `distribution.yaml` and **skips** profiles missing the latter three, so no profile registers until the v0.2 wiring lands. See [implementation-status.md](../../project/implementation-status.md).

## What the installer does

`install.ps1` is idempotent. For each target profile under `.memoria/profiles/memoria-<name>/` it:

1. Checks the required file set is present; skips the profile with a message if not.
2. Stages the profile files to a temp dir.
3. Substitutes `{{VAULT_PATH}}` in `mcp.json` with the vault's absolute path (forward-slash form), written UTF-8 no-BOM.
4. Runs `hermes profile install <staged> --alias memoria-<name> --force --yes`.
5. On first install only, Hermes writes `.env.EXAMPLE` to the installed profile directory; `install.ps1` copies it to `.env` (never overwrites an existing `.env`).

Author-owned files (`SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`) are overwritten on every run; the human-owned `.env` is preserved.

## Common runs

| Goal | Command |
| --- | --- |
| Install / refresh all profiles | `./install.ps1` |
| Refresh one profile | `./install.ps1 -Only memoria-linter` |
| Re-deploy after `git pull` | `./install.ps1` (overwrites deployed copies from vault source) |
| Hermes installed but not on PATH | `./install.ps1 -SkipHermesCheck` |
| No MCP server source yet (v0.1) | `./install.ps1 -SkipPythonCheck` |

## Verify

- `hermes profile list` shows the installed `memoria-*` profiles.
- The Linter's `profile-install-drift` detector ([linter.md](../../explanation/profiles/linter.md)) reports any deployed copy that diverges from the vault source (the signal to re-run the installer).

## Owners

The **human** runs the installer and fills each `.env`. `install.ps1` does the staging, substitution, and registration. No agent runs this step.

## Related

- [tutorials/01-set-up-from-zero.md](../../tutorials/01-set-up-from-zero.md) — Step 4 walks through a first install.
- [operations/failure-modes.md](failure-modes.md) — fixes that redeploy profiles.
- [implementation-status.md](../../project/implementation-status.md) — which profile files ship today.
