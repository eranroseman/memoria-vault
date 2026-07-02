---
title: Installed profiles
parent: Agents and control
grand_parent: Reference
---

# Installed profiles

Alpha.14 does not ship installed Hermes profile packages or lane overrides.
`vault-template/.memoria/profiles/` and `vault-template/.memoria/lane-overrides/`
must be absent.

The product surface is the standalone `memoria` CLI over the local engine. Future
agent or editor adapters must wrap that CLI/engine boundary instead of adding
required installed-profile state to the workspace.

## Checks

- `tests/test_profiles.py` pins that no installed profile or lane package ships.
- `scripts/alpha14_negative_gate.py` rejects the removed profile and lane package
  paths.

## Related

- CLI commands: [CLI](cli.md)
- Operations: [Operations](operations.md)
- Configuration: [Memoria configuration](configuration.md)
