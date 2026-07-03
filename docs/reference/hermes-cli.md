---
title: Hermes CLI
parent: Agents and control
grand_parent: Reference
---

# Hermes CLI

Alpha.15 does not ship a Hermes command surface. The installed product surface is
the standalone [`memoria` CLI](cli.md) plus the local engine state in the
workspace.

The bootstrap installers do not install Hermes, profiles, lane overrides,
profile skills, Hermes crons, or profile-only redeploy commands. The template
must not contain `vault-template/.memoria/profiles/` or
`vault-template/.memoria/lane-overrides/`; [Installed profiles](profile-capabilities.md)
owns that contract.

Hermes is outside the alpha.15 runtime. A user may experiment with it locally,
but Memoria ships no Hermes adapter and Hermes is never the authority for
operation manifests, write policy, provider config, or scheduled work.

## Current Commands

Use these references for the current shipped surfaces:

- CLI command list: [CLI](cli.md)
- Operation manifests: [Operations](operations.md)
- Write policy: [Policy gate](policy-mcp.md)
- Install flow: [Installer (bootstrap)](installer.md)

## API Server

No Hermes API server is installed by the alpha.15 bootstrap. External API
adapters must call the standalone CLI/engine.

## Board Management

No Hermes board-management CLI is installed by the alpha.15 bootstrap. Use
[CLI](cli.md) request and attention commands for the current control plane.
