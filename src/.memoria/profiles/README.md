# Profiles

Each `memoria-*` directory is a deployable Hermes profile:

- `SOUL.md` defines posture.
- `config.yaml` defines runtime wiring and MCP servers.
- `distribution.yaml` defines package metadata.
- `skills/` and `cron/` contain profile-owned additions.

Capability ownership lives in `../tool-registry.yaml`; path and routing ceilings
live in `../lane-overrides/`. Profile files consume those contracts and must not
silently widen them. Run `scripts/agents-doctor.py --write` after profile or lane
changes to refresh the derived profile-policy matrix.
