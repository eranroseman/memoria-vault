---
title: Fix profile drift
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 6
---

# Fix profile drift

Alpha.15 should not have profile drift because it does not ship installed
profiles. If you see `vault-template/.memoria/profiles/` or
`vault-template/.memoria/lane-overrides/`, a pre-alpha.14 package was copied
back into the tree.

## Fix

1. Remove the profile or lane-override package.
2. Run the negative gate:

   ```bash
   python scripts/alpha14_negative_gate.py
   ```

3. Use [Operations](../../reference/operations.md) and the `memoria` CLI for the
   current capability surface.

## Related

- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
- Standalone installer: [Installer (bootstrap)](../../reference/installer.md)
- Current CLI commands: [CLI](../../reference/cli.md)
