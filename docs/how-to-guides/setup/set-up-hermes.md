---
title: Set up Hermes
parent: Setup
grand_parent: How-to guides
nav_order: 4
---

# Set up Hermes

Alpha.15 does not ship a Hermes setup path. The supported install is the
standalone CLI/runtime workspace from [Set up the vault](set-up-the-vault.md).

The bootstrap installers do not create Hermes profiles, profile `.env` files,
lane overrides, Hermes crons, or `--profiles-only` redeploy modes. The current
profile boundary is documented in [Installed profiles](../../reference/profile-capabilities.md).

If you experiment with Hermes, keep it outside the bootstrap contract. Memoria
does not ship a Hermes adapter; the `memoria` CLI/engine remains the authority
for operations, provider config, and write policy.
