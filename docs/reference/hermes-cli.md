---
title: Hermes CLI
parent: Agents and control
grand_parent: Reference
---

# Hermes CLI

Alpha.14 does not ship a Hermes command surface. The installed product surface is
the standalone [`memoria` CLI](cli.md) plus the local engine state in the
workspace.

The bootstrap installers do not install Hermes, profiles, lane overrides,
profile skills, Hermes crons, or profile-only redeploy commands. The template
must not contain `vault-template/.memoria/profiles/` or
`vault-template/.memoria/lane-overrides/`; [Installed profiles](profile-capabilities.md)
owns that contract.

Hermes remains an optional future adapter: it may wrap the CLI/engine for users
who want a Hermes-hosted chat, dispatcher, or board UI, but it is not the
authority for operation manifests, write policy, provider config, or scheduled
work in alpha.14.

## Current Commands

Use these references for the current shipped surfaces:

- CLI command list: [CLI](cli.md)
- Operation manifests: [Operations](operations.md)
- Write policy: [Policy gate](policy-mcp.md)
- Install flow: [Installer (bootstrap)](installer.md)

## API Server

No Hermes API server is installed by the alpha.14 bootstrap. External API
adapters must call the standalone CLI/engine.

## Board Management

No Hermes board-management CLI is installed by the alpha.14 bootstrap. Use
[CLI](cli.md) request and attention commands for the current control plane.
