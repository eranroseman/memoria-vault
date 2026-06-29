---
topic: decisions
id: 120
title: Profile config capability blocks are materialized from the tool registry
nav_exclude: true
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [28, 48]
supersedes: []
superseded_by: []
---

# ADR-120: Profile config capability blocks are materialized from the tool registry

## Context

ADR-48 made the old SOUL/profile compiler unnecessary: the five profile postures are
short and genuinely distinct. The drift that remains is narrower. Hermes reads one
plain per-profile `config.yaml`; that file owns `mcp_servers`, runtime platform
toolsets, plugins, and the other profile settings Hermes loads. There is no runtime
`mcp.json`, and each profile gets its own `.env` for secrets such as the Obsidian API
key.

`vault-template/.memoria/tool-registry.yaml` is the source for each profile's positive
`platform_toolsets` and MCP tool filters, but the checked-in `config.yaml` files
still repeated those derived blocks by hand.

Hermes v0.17 reads plain per-profile `config.yaml`; the local docs and
`cli-config.yaml.example` do not provide profile-config includes or inheritance.

## Decision

Keep plain checked-in Hermes `config.yaml` files, but materialize their capability
blocks from `vault-template/.memoria/tool-registry.yaml` with
`scripts/render_profile_configs.py`.

The render script owns only the mechanical parts:

- `platform_toolsets` for every Hermes runtime platform
- MCP `tools.include` filters for non-Obsidian MCP servers

Profile posture, MCP server endpoints/commands/timeouts, model placeholders, memory
settings, plugin enablement, and package metadata stay ordinary profile source.

The materialized configs keep Obsidian MCP as the normal vault-write path. Direct-world
tool families such as `file`, `terminal`, and `code_execution` are not a Memoria lane
write boundary; the `memoria-policy-gate` plugin hard-denies them fail-closed, and
ADR-28 owns that enforcement mechanism.

## Consequences

- Capability edits happen in one file: `tool-registry.yaml`.
- CI can fail on stale generated profile configs instead of relying on humans to
  copy allowlist changes into five files.
- Runtime remains boring: Hermes receives normal `config.yaml` files; no install-time
  template language or runtime include mechanism is introduced.
- Comments inside generated profile configs are intentionally sparse. The rationale
  lives in ADRs and reference docs; the config is the deployable machine view.

## Alternatives considered

**Keep hand-authored configs.** Rejected: it preserves five-way copying for the
highest-risk profile capability surface.

**Full profile compiler.** Rejected: too broad for the actual duplication. The SOUL files
and package manifests remain small and profile-specific.

**Hermes-native inheritance.** Not available on the installed v0.17 configuration model.

**Runtime `mcp.json`.** Rejected because Hermes does not load it for profile runtime
configuration. MCP servers belong in profile `config.yaml`.

## Related

- **Assumes:** [ADR-28](28-write-gate-as-plugin.md), [ADR-48](48-copi-and-agent-consolidation.md)
- **Implementation:** `scripts/render_profile_configs.py`
