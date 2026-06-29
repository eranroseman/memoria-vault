---
topic: decisions
id: 27
title: Configure Hermes the way Hermes reads config; the review gate enforces via a toolset allowlist with obsidian as the only write path
nav_exclude: true
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: [28]
---

# ADR-27: Configure Hermes the way Hermes reads config; the review gate enforces via a toolset allowlist with obsidian as the only write path

> **Partial supersession (2026-06-02, [ADR-28](28-write-gate-as-plugin.md)).** ADR-28
> supersedes **only this ADR's *enforcement mechanism*** (shell hook → Python plugin);
> the `superseded_by: [28]` frontmatter scopes to that mechanism, **not** to the ADR
> as a whole. ADR-27's config-model decisions — `mcp_servers` in `config.yaml`,
> a profile-scoped toolset allowlist, obsidian as the only write path — **all stand**.
> Concretely, this ADR's
> *enforcement mechanism* — the `pre_tool_call` **shell hook** with
> `matcher: "obsidian.*"` — does **not** fire on live agent writes: Hermes registers
> the obsidian tool as `mcp_obsidian_obsidian_append_content`, and the shell-hook
> `re.fullmatch` against `obsidian.*` never matches it (shell hooks are also
> consent-gated and fail-open). ADR-27's validation rows were synthetic
> (hand-set `task_id`s), not a live run. **ADR-28 replaces the shell hook with a
> Python plugin** (the gate now enforces live). The rest of ADR-27 — `mcp_servers`
> in `config.yaml`, the profile-scoped toolset allowlist, obsidian as the only
> write path — **stands**; it is what makes one gated path sufficient.
>
> **Hermes 0.17 correction (2026-06-22).** The current allowlist is expressed with
> positive `platform_toolsets` for every Memoria runtime platform. The old
> computed `agent.disabled_toolsets = all − allowlist` model remains only as a
> backstop for known direct-world toolsets if a Hermes path falls back to defaults.

## Context

A Tier-4 live investigation (Hermes Agent v0.14.0, WSL2, against the `Memoria-test`
vault with Obsidian open on Windows) set out to verify that the structural review
gate ([ADR-03](03-structural-review-gate.md)) actually blocks an agent's writes to
review-gated zones. It did not — and chasing *why* uncovered that several Memoria
profile artifacts were placed where Hermes does not read them. The gate, the
capability layer ([#51](https://github.com/eranroseman/memoria-vault/issues/51)),
and the obsidian bridge ([#39](https://github.com/eranroseman/memoria-vault/issues/39))
all depend on Hermes loading config from specific files; Memoria had guessed the
locations.

The investigation produced a sequence of wrong intermediate conclusions ("hooks
don't fire in oneshot", "…not in the gateway either", "build a custom obsidian
bridge"). Each was an artifact of the misplacement, not a real Hermes limitation.
This ADR records the corrected model and the resulting plan so the dead ends are
not re-walked. It refines — does not supersede — ADR-03 (the gate is still
structural) and [ADR-22](22-build-on-hermes-runtime.md) (we still build on the
Hermes runtime); it sharpens *how* we configure that runtime.

This decision rests on the authoritative Hermes sources read during the
investigation: `cli-config.yaml.example`, and the `user-guide/{configuration,
profiles,multi-profile-gateways,checkpoints-and-rollback,docker}` +
`developer-guide/{tools-runtime,cron-internals,acp-internals}` docs shipped in the
local install (`~/.hermes/hermes-agent/website/docs/`), plus reads of
`agent/shell_hooks.py`, `tools/mcp_tool.py`, `hermes_cli/config.py`,
`hermes_cli/main.py`, and `agent/tool_executor.py`.

## Findings (the evidence this decision is built on)

1. **Hermes loads MCP servers only from `mcp_servers` in `config.yaml`.**
   `tools/mcp_tool.py::_load_mcp_config()` reads `mcp_servers` via `load_config()`.
   Nothing reads a per-profile `mcp.json` at runtime — `hermes profile install`
   treats `mcp.json` as a distribution-owned file to *copy*, never to load.
   Memoria shipped its `policy` + `obsidian` servers in `mcp.json`, so **neither
   ever loaded** (`hermes -p memoria-writer mcp list` → "No MCP servers
   configured"). This is the single root cause of the gate failure.

2. **With no obsidian tool, the agent writes via the filesystem.** Profiles do
   **not** sandbox (`user-guide/profiles.md`: "Profiles do not sandbox the
   agent… the agent still has the same filesystem access as your user account").
   Lacking the obsidian MCP tool, the agent wrote a note via `code_execution` /
   `file` to an arbitrary host path (`…/OneDrive/Documents/Memoria/…`), entirely
   outside any gate.

3. **`config.yaml` is the home for per-profile settings, and `load_config()` is
   profile-scoped.** Each profile is its own `HERMES_HOME`
   (`~/.hermes/profiles/<name>/`); `load_config()` reads
   `get_hermes_home()/config.yaml`. So `model`, `mcp_servers`, `hooks`,
   `platform_toolsets`, `agent.disabled_toolsets`, `terminal`, and plugins all
   belong in **one** per-profile `config.yaml`. A separate `mcp.json` is dead.

4. **The shell-hook gate *does* fire in every run mode — the matcher was the
   problem, not the mode.** All run modes (CLI/`-z`, gateway, cron, ACP) wrap the
   same `run_agent.AIAgent`; every tool call routes through
   `model_tools.handle_function_call → invoke_hook("pre_tool_call")`
   (`developer-guide/tools-runtime.md`), including MCP tools. Hooks register at
   CLI and gateway startup (`register_from_config`), and cron runs inside the
   gateway ticker (`cron-internals.md`), ACP wraps `AIAgent` with
   `enabled_toolsets=["hermes-acp"]` (`acp-internals.md`). The gate didn't fire
   only because (a) `matches_tool` uses `re.fullmatch` (`agent/shell_hooks.py`),
   so `matcher: "obsidian"` matched *nothing* — fixed to `"obsidian.*"` — and
   (b) the agent never called an obsidian tool (finding 1), so even the correct
   matcher had nothing to match. **The earlier "hooks don't fire / need a custom
   bridge" conclusions are withdrawn.**

5. **The capability denylist `[terminal, file]` is insufficient.** The lane's
   `tool-registry.yaml` intends a default-deny *allowlist*
   (writer = `[web, vault_read, vault_write, skills, todo, policy]`), but the
   profile inherited the global `platform_toolsets.cli` (≈17 toolsets). Disabling
   only `terminal`+`file` left `code_execution`, `delegation`, `cronjob`,
   `messaging`, `browser`, `computer_use` live — several of which write to disk or
   act outside the gate. `code_execution` alone re-opens the hole.

6. **Hermes reads per-profile `.env` only — there is no global `~/.hermes/.env`
   inheritance for a profile run.** Shared keys placed only in the global `.env`
   never reach a profile run (model init fails; `${OBSIDIAN_API_KEY}` resolves
   empty → the original 401). The installer must seed shared keys into each
   profile `.env`.

7. **`hermes config set` stores a scalar string, not a list** — it cannot emit a
   YAML list, so `disabled_toolsets` must be written by editing the file
   (PyYAML), preserving the `model`/`hooks` blocks.

8. **Hermes ships native mechanisms Memoria was reinventing or mis-naming:**
   the terminal `DANGEROUS_PATTERNS` + `command_allowlist` is a real
   command-approval layer; and **"Tirith" is a command-string security scanner
   (`security.tirith_*`), *not* the tool-permission/capability layer** —
   `policy-mcp.md` misnamed it. The capability layer is `platform_toolsets` /
   `agent.disabled_toolsets`. Hermes `checkpoints` are real for native
   `write_file`/`patch`/terminal writes, but Memoria's normal vault writes go
   through the Obsidian MCP path, so profile `checkpoints.enabled` is inert for
   Memoria and no longer ships.

## Decision

**Configure Hermes through the files and keys Hermes actually reads, and enforce
the review gate by making the obsidian MCP server the *only* write path each
non-terminal lane has.** Concretely:

1. **MCP servers live in each profile's `config.yaml` under `mcp_servers`.** The
   installer merges the (now-vestigial) `mcp.json` content into `config.yaml` at
   deploy time and stops relying on `mcp.json`. `policy` + `obsidian` therefore
   load, and obsidian becomes the agent's vault-write tool.

2. **Each lane is locked to a positive toolset allowlist.** The source
   `config.yaml` for every profile lists the permitted toolsets in
   `platform_toolsets` for each runtime platform (`cli`, gateway platforms,
   `cron`, and `api_server`), derived from `tool-registry.yaml`. The
   `agent.disabled_toolsets` list is retained as a backstop for known
   direct-world families only. For the five current lanes this removes
   `code_execution`, `file`, `terminal`, `delegation`, `browser`, etc. **With no
   filesystem write tool, the agent's only way to write the vault is the
   obsidian MCP path — which the policy plugin gates.**

3. **Keep the shell-hook gate as the enforcement mechanism (ADR-03 stands).** It
   fires in CLI, gateway, cron, and ACP via the shared `AIAgent` dispatch. The
   matcher is `obsidian.*` (fullmatch). The custom-bridge alternative is
   **rejected** — it was only ever needed under the withdrawn "hooks don't fire"
   premise. *(Enforcement mechanism superseded by [ADR-28](28-write-gate-as-plugin.md):
   the shell hook never fired on live writes — it is replaced by the
   `memoria-policy-gate` Python plugin. The config-model decisions 1, 2, 4–6 below
   are unaffected.)*

4. **Coder and Linter keep `terminal`+`file` (they need git / `detectors.py`).**
   Their file writes are gated by the hook (`write_file|patch` matcher) and
   scoped by lane `write_scope`; their shell writes are bounded by `write_scope`
   plus, optionally, a Docker terminal backend (see Consequences).
   *(0.1.0-alpha.2 update — this exception is retired by D40/[ADR-46](46-seven-layer-architecture.md):
   the Linter became a cron/CI engine (no agent), and the Engineer — the Coder's
   successor — is MCP-only like every lane. No Memoria profile ships `terminal`,
   `file`, or `code_execution`; the policy-gate plugin additionally hard-denies
   those tool families fail-closed for every lane. The external coding agent the
   Engineer hands off to is third-party code and gets execution isolation when
   introduced, per D40.)*

5. **Shared keys are seeded into each profile `.env`** by the installer
   (`seed_profile_env`, idempotent; re-run `--profiles-only` after adding keys).
   Already landed in PR #57.

6. **Adopt only the Hermes-native safety features that affect Memoria's path:**
   `terminal.cwd` stays set to the vault to anchor stray ops, and the "Tirith =
   capability layer" docs error is corrected. Do **not** ship
   `checkpoints.enabled` unless Memoria gains a native file/terminal write path or
   a test proves checkpoints fire for the actual Obsidian MCP write path.

## Consequences

- **`mcp.json` is retired** as a runtime artifact (kept, if at all, only as the
  source the installer merges from). The ledger row, `profiles.md`, and the
  bootstrap docs update accordingly.
- **`tool-registry.yaml` becomes load-bearing**: it is the source for each lane's
  positive `platform_toolsets` and MCP tool filters, not just a drift-check reference.
- **The gate enforces in all run modes** once (1)+(2) land — no per-mode special
  casing, no custom bridge.
- **Reversibility comes from Memoria's own audit/golden mechanisms, not Hermes
  checkpoints.** Policy writes record before/after hashes; shipped system files are
  restorable from the golden copy. Hermes checkpoints are not claimed for MCP
  writes.
- **Optional defense-in-depth for Coder/Linter**: `terminal.backend: docker`
  sandboxes their `terminal`+`code_execution` in a container, with a vault
  bind-mount scoped to just their write zone (`40-workbench/*/06-code/` for Coder,
  `99-system/logs/` for Linter). Full-Hermes-in-Docker is **not** adopted: in the
  WSL2 + Windows-Obsidian topology it adds container→host REST-bridge networking
  fragility for no gate benefit (the gated path lives on the Windows host).
- **Records to correct** (the investigation invalidated earlier claims):
  - `#39` "resolved via the obsidian bridge" — the observed write was a filesystem
    write, not obsidian; reopen until obsidian MCP actually loads and a gated write
    is confirmed.
  - `#58` "gate is a no-op in oneshot/gateway" — wrong premise; the gate fires, the
    obsidian tool was simply never loaded. Correct and likely close.
  - `policy-mcp.md` Caveat 2 + the ledger "custom bridge" recommendation — replace
    with the `mcp_servers`-placement + allowlist model above.
  - `#51` capability layer — the `[terminal, file]` denylist is superseded by the
    `all − allowlist` computation.

## Implementation plan

Installer (`scripts/install.sh`) and profile sources (`vault/.memoria/profiles/*`):

1. Emit `mcp_servers` into each deployed `config.yaml` (merge from the profile's
   `mcp.json`; substitute `{{VAULT_PATH}}` and the venv interpreter; keep
   `${OBSIDIAN_API_KEY}` for env interpolation).
2. Emit positive `platform_toolsets` per lane from `tool-registry.yaml`, with
   `agent.disabled_toolsets` retained only as the known direct-world backstop.
3. Set `terminal.cwd: {{VAULT_PATH}}` per profile; do not emit `checkpoints` for
   MCP-only lanes.
4. Keep `seed_profile_env` (#57) and the `obsidian.*` matcher (#57).
5. Re-run Tier-4 on `Memoria-test`: confirm `hermes -p <lane> mcp list` shows
   `obsidian`+`policy`; a write to an allowed zone produces an audit row; a write
   to a review-gated zone is **blocked** with no file on disk; the five
   non-terminal lanes have no `code_execution`/`file`/`terminal`.
6. Then correct `#39`/`#58`, `policy-mcp.md`, and the ledger.

Sequencing lives in [Release plan — 0.1.0-alpha.1](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1.md); this ADR records the
choices, not the schedule.

## Alternatives considered

- **Custom obsidian bridge (MCP wrapper that calls `check_permission` internally).**
  Rejected: only attractive under the withdrawn "hooks never fire" premise. The
  native hook fires in all modes once obsidian is the write path; a bridge is more
  to build and maintain and still wouldn't cover `code_execution`/`terminal`.
- **Run automation through the gateway to "make hooks fire".** Moot — hooks fire
  in `-z`/cron/ACP too; the gateway is not required for enforcement (though it
  remains how Hermes-native cron executes).
- **Denylist-only capability (`disabled_toolsets: [terminal, file]`).** Rejected:
  leaves `code_execution` and other write/act paths live. The allowlist
  (`all − allowed`) is the correct default-deny realization of `tool-registry.yaml`.
- **`platform_toolsets` per platform instead of global `disabled_toolsets`.**
  Accepted in Hermes 0.17. It is slightly more verbose, but it fails closed for
  new toolsets on configured platforms; `disabled_toolsets` remains a backstop.
- **Full Hermes-in-Docker for sandboxing.** Rejected as the primary fix: it
  contains blast radius but doesn't load obsidian or remove `code_execution`, and
  the vault bind-mount it requires re-opens ungated writes to the vault. Retained
  only as optional `terminal.backend: docker` scoped to Coder/Linter.
- **SOUL.md / prompt rules as the boundary.** Rejected per ADR-03 and confirmed by
  `profiles.md`: prompts do not enforce a filesystem boundary.
