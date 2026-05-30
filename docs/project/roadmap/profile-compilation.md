---
topic: roadmap
---

# Profile compilation: `memoria-base` and per-profile overrides

> **Status: deferred — not the current architecture.** Memoria's current distribution model is [direct profile management](../../explanation/architecture/on-disk-layout.md): the seven profile directories under `.memoria/profiles/memoria-<name>/` are hand-authored and copied verbatim to `~/.hermes/profiles/` by the install script. There is no compiler today.
>
> This document specifies the Kustomize-style compiler that would generate compiled profile outputs from a shared base + per-profile overrides. It is preserved as a forward-looking design — the natural Phase 2 evolution if drift between the seven sibling profiles becomes painful at scale. Until then, treat this document as **archived design**, not as a description of how Memoria works today. References from other design docs to "the compiler," `build_profiles.py`, `build-info.json`, `templates/base/`, or `templates/profiles/<name>.yaml` refer to this deferred design and do not describe current behavior.

The seven Memoria profile directories under `~/.hermes/profiles/memoria-<name>/` would be **not hand-maintained** in this design. They are compiled outputs from a single source of truth in the project repo, regenerated whenever the base contract or a lane override changes. This is what keeps the seven profiles from drifting apart.

The compiled outputs follow the [Hermes profile-distribution shape](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions) (`SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `.env.EXAMPLE`) so each compiled profile is compatible with `hermes profile list`, `hermes -p memoria-librarian chat`, and the standard alias surface.

Skills bundled under each profile's `skills/` directory follow the [agentskills.io SKILL.md specification](https://agentskills.io) — `name`, `description`, `dependencies`, `trigger`, input/output schemas, and step-by-step instructions in Markdown. Hermes aligns with this spec, which means skills authored against it (including the K-Dense scientific catalog and other community skills) install into Memoria profiles without modification. The same SKILL.md file is portable across any agent supporting agentskills.io.

This reference is the authoritative mechanism. The architecture overview in [architecture/README.md](../../explanation/architecture/README.md) summarizes; this document specifies.

## Source layout

The build inputs live in the project repo at `memoria/`:

```text
memoria/
├── templates/
│   ├── base/
│   │   ├── config.base.yaml      # shared defaults: model, common commands, base MCPs
│   │   ├── SOUL.base.md          # shared contract sections (mission template, common rules)
│   │   ├── env.base              # shared env var declarations (no secret values)
│   │   ├── mcp.base.json         # shared MCP server registrations (obsidian, policy, tasks)
│   │   └── policies.base.yaml    # shared policy invariants (audit_log required, etc.)
│   └── profiles/
│       ├── librarian.yaml       # per-profile override: model, commands, soul sections, tool filters
│       ├── mapper.yaml
│       ├── socratic.yaml
│       ├── writer.yaml
│       ├── verifier.yaml
│       ├── coder.yaml
│       └── linter.yaml
├── lane-overrides/               # read at runtime by the policy MCP (not compiled into profiles)
├── mcp/                          # source for policy_mcp.py and tasks_mcp.py
└── generator/
    └── build_profiles.py         # the compiler
```

The `templates/base/` directory holds shared defaults; each `templates/profiles/<name>.yaml` declares only what is specific to that lane. The compiler merges them.

## Compilation steps

1. Load `templates/base/config.base.yaml`.
2. Load the profile-specific override at `templates/profiles/<name>.yaml`.
3. **Deep-merge maps; replace lists** unless a field is explicitly marked append-only (e.g., `commands.add`, `tools.add`).
4. Render `SOUL.md` by concatenating the shared contract block with the profile-specific lane section.
5. Render `mcp.json` from the base MCP registrations plus any per-profile `tools.include` / `tools.exclude` filters. Emit the same content into `config.yaml` under `mcp_servers:` for Hermes-native loading.
6. Render `.env.EXAMPLE` from `env.base` plus profile-specific declarations — commented-out keys with descriptions, never real secret values.
7. Materialize per-profile `cron/` entries from the override's `cron:` section (one JSON file per scheduled task).
8. Write compiled outputs into `~/.hermes/profiles/memoria-<name>/`:
   - `SOUL.md` — the effective system prompt.
   - `config.yaml` — the effective runtime config, including the `mcp_servers:` block.
   - `mcp.json` — Hermes-standard MCP server connections (mirrors `mcp_servers:` in `config.yaml`).
   - `cron/` — per-profile scheduled tasks (empty for profiles without cron — typical for Socratic, Verifier, and most non-Linter profiles).
   - `skills/` — profile-bundled skills, when narrower than the shared `~/.hermes/skills/`. Empty by default; populated only for profiles that need a private skill (rare).
   - `.env.EXAMPLE` — required and optional env vars, commented out, with descriptions. The human copies this to `.env` and fills in real values on first install.
   - `policy.manifest.yaml` — Memoria-specific extension: the effective policy manifest the policy MCP reads at startup. Not part of Hermes's standard profile shape; Hermes ignores it.
   - `build-info.json` — Memoria-specific extension: SHA-256 hashes of the source files that produced this profile, used by the Linter's drift detector.

## Build-time validation

The build fails if any of these are true. These are the *build-time complement* to the runtime policy MCP — they catch misconfiguration before the worker starts, not after the first write attempt.

| Validation | Meaning |
| --- | --- |
| Missing mission | A profile's `mission` field must be a non-empty string. |
| Unjustified review-gated-zone write | A profile's `policy.allow.write` includes a review-gated zone without `flags.explicit_authorization: true` on the rule. |
| Unknown tool | A profile references a tool not present in `.memoria/tool-registry.yaml`. |
| Missing secret | A profile's `.env` declares a key that isn't supplied by the secret manager. |
| Unknown command | A profile defines a command outside the defined command set in [profiles/README.md](../../explanation/profiles/README.md). |
| Schema drift | A profile's `config.yaml` schema version doesn't match the current `policies.base.yaml`. |

## Why compile, not inherit

Hermes profiles are isolated by directory. There is no native live inheritance — each profile's `config.yaml` is a separate file. Three options exist:

| Option | Pros | Cons |
| --- | --- | --- |
| Hand-edit each profile | Simple, no build step | Drift across six files; "shared" changes require six edits in lockstep |
| Symlinks / includes | No drift if supported | Hermes doesn't document or guarantee runtime include semantics |
| **Compile at build time** | Explicit auditable output; drift is detectable via `build-info.json` | Adds a build step before profile changes take effect |

Memoria adopts the third option. The build step is small (one Python script) and the explicit compiled output means every effective configuration is auditable in Git.

## `SOUL.md` is a generated artifact

The `SOUL.md` in each profile directory is compiled output. **Do not hand-edit it.** For shared changes, edit `memoria/templates/base/SOUL.base.md`. For profile-specific changes, edit the `soul_sections:` field in `memoria/templates/profiles/<name>.yaml`. Then rebuild.

Hermes loads `SOUL.md` reliably at the start of a new session. After regeneration, restart any session for an affected profile so the new system prompt takes effect.

## Drift detection

Each profile's `build-info.json` records the SHA-256 hashes of (a) every base file and (b) the override file that produced it. The Linter's `health-report` check (see [linter.md](../../explanation/profiles/linter.md#log-rotation)) recomputes these hashes and flags profiles whose compiled outputs no longer match their declared sources. This catches accidental hand-edits to compiled files.

## Workflow

1. Edit `memoria/templates/base/` or `memoria/templates/profiles/<name>.yaml`.
2. Run `python memoria/generator/build_profiles.py`.
3. Build validation runs automatically; the build fails on any rule above.
4. The compiler writes outputs into `~/.hermes/profiles/memoria-<name>/`. Restart Hermes sessions for any profile whose `SOUL.md`, `config.yaml`, or `mcp.json` regenerated (`hermes -p memoria-<name> chat` picks up the new system prompt on next start).
5. Optionally commit the regenerated outputs to a `memoria-profiles/` sibling repo or `dist/` subtree if the human wants the audit trail of effective changes alongside the source diff.

The compilation is one-way: source → compiled output. Never hand-edit anything under `~/.hermes/profiles/memoria-*/` — the next rebuild will overwrite it, and the Linter's drift check will flag it as a hash mismatch in the meantime.
