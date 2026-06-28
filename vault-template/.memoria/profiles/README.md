# Profiles

Each `memoria-*` directory is a deployable Hermes profile:

- `SOUL.md` defines posture.
- `config.yaml` defines runtime wiring and MCP servers. Its capability blocks
  are materialized by `scripts/render_profile_configs.py` from
  `../tool-registry.yaml`; edit the registry, then regenerate.
- `distribution.yaml` defines package metadata.
- `skills/` contains profile-owned skills when a profile ships them.
- `.no-bundled-skills` records that Memoria owns deployed profile skills: the
  installer refreshes source `skills/` when present and clears stale deployed
  skills when they are absent.
- Shared cron wrappers live in `../scripts/`, not under each profile.

Capability ownership lives in `../tool-registry.yaml`; path and routing ceilings
live in `../lane-overrides/`. Profile files consume those contracts and must not
silently widen them. Run `scripts/render_profile_configs.py --write` after tool
changes, and `scripts/agents_doctor.py --write` after profile or lane changes to
refresh the derived profile-policy matrix.
