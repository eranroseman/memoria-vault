---
title: Redeploy profiles
parent: Operate
grand_parent: How-to guides
nav_order: 4
---

# Redeploy profiles

Alpha.15 has no installed profile packages and no profile redeploy command.

Do not run `--profiles-only`; that installer mode was removed with the
pre-alpha.14 Hermes profile packaging. The shipped runtime is the standalone
CLI/engine workspace. If system template files need to be refreshed, create a
fresh workspace with the bootstrap installer and copy user-authored content
intentionally.

## Verify

```bash
python scripts/alpha14_negative_gate.py
```

The check fails if `vault-template/.memoria/profiles/` or
`vault-template/.memoria/lane-overrides/` reappears.

## Related

- Install the standalone workspace: [Set up the vault](../setup/set-up-the-vault.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
- Installer reference: [Installer (bootstrap)](../../reference/installer.md)
