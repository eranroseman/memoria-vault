---
topic: decisions
id: 67
title: Drift procedures under the golden-copy model — keep or retire
nav_exclude: true
status: accepted
date_proposed: 2026-06-12
date_resolved: 2026-06-12
assumes: [25, 26, 49, 55]
supersedes: []
superseded_by: []
---

# ADR-67: Drift procedures under the golden-copy model — keep or retire

## Context

The original structural-linter design (v0.1.0) specified five **weekly agent-run drift
procedures**: golden-copy, skeleton-drift, profile-install-drift, command-vocab-drift,
and plugin-config-drift. The as-built rewrite (PR #390) shipped only the golden-copy
baseline and marked the rest deferred; the design pages themselves were later retired
into ADRs (PR #406). Each procedure needed a keep-or-retire decision under the
golden-copy model ([ADR-55](55-src-scaffold-populate-golden-copy.md)), tracked in
[#394](https://github.com/eranroseman/memoria-vault/issues/394). A sibling decision —
the audit-chain checks (`vault-hash-drift`) — is recorded in
[ADR-25](25-session-logging-two-logs.md).

A structural observation drives the outcome: nothing here needs a *weekly agent run*.
What is deterministic belongs in the zero-LLM Linter engine on the daily cron
([ADR-49](49-catalog-in-bases-linter-monitor.md)); what needs deploy-host state the
vault cannot see belongs to the idempotent installer; what is repo-consistency belongs
to the repo's CI tests.

## Decision

| Procedure | Decision | Where it lives |
| --- | --- | --- |
| **golden-copy** | **Keep — built** | `operations/integrity/linter/golden_restore.py` (stage / check / restore) on the daily lint cron ([ADR-55](55-src-scaffold-populate-golden-copy.md)). |
| **skeleton-drift** | **Keep — built** | The Linter's `skeleton-drift` detector: every directory in the `skeleton` list of `.memoria/schemas/folders.yaml` must exist in the vault; a missing one is a MEDIUM finding (fix: re-run the idempotent installer or `mkdir`). Checked only in installed vaults — keyed on the golden manifest — because the repo's `src/` deliberately ships no empty dirs ([ADR-55](55-src-scaffold-populate-golden-copy.md)). Needs only the vault tree, so it is a vault-side detector, not an agent run. |
| **plugin-config-drift** | **Keep — via the golden copy** | The installer ships Obsidian plugin config from `src/.obsidian/` into the runtime vault, so the golden manifest now covers the **Memoria-shipped** config files: each shipped plugin's `data.json` plus `community-plugins.json`, `core-plugins.json`, and the `memoria-link-colors.css` and `memoria-property-badges.css` snippets. Per-machine / runtime-generated state never enters the manifest — `agent-client/data.json` is seeded per machine from its `.example`, `obsidian-local-rest-api` regenerates its `data.json` (apiKey + TLS) on first launch, and workspace/appearance/graph state is the user's to mutate. |
| **profile-install-drift** | **Retire** | It needs `~/.hermes` deploy state the vault-side Linter doesn't have. Deploy drift is *fixed*, not just detected, by re-running the idempotent installer (`--profiles-only`), and the vault-side sources of the deployed profiles are golden-copy-covered. A detector that can see only one side of the comparison adds nothing over the fix. |
| **command-vocab-drift** | **Retire** | Config/vocabulary consistency is a repo CI concern, single-sourced and tested there: `tests/test_profiles.py` checks every profile's lane-override exists, lane write-scopes avoid the gated zones, and configs reference real MCP servers; `tests/test_schemas.py` pins the gated-prefix fallbacks in `policy_mcp`/`patterns_mcp` to `folders.yaml`; `tests/test_policy_hook.py` covers the gate plugin's tool matching and hard-denies. A weekly vault-side re-check would re-derive what CI already gates per commit. |

The detectors built here and in ADR-25 (`skeleton-drift`, `vault-hash-drift`,
`audit-log-size`, `hub-threshold`) run with the rest of `detectors.py` on the **daily**
lint cron — strictly more often than the designed weekly cadence.

## Consequences

- No weekly agent-run drift procedure exists or is planned; the category is closed.
  Drift work is split engine (daily cron) / installer (idempotent re-run) / repo CI.
- Retiring profile-install-drift leaves source→deployment drift detectable only by
  re-running the installer; that is accepted because the re-run *is* the repair, and
  [ADR-26](26-repo-as-install-unit.md)'s detector/installer "matched pair" framing is
  amended accordingly.
- The golden manifest now includes shipped Obsidian config, so a PI who deliberately
  tunes a shipped plugin setting will see a `golden check` drift report until the
  golden copy is re-staged — the same propose-only discipline as every system file.

## Alternatives considered

**Implement all five as designed (weekly agent runs).** Rejected: every procedure is
either deterministic (engine), host-side (installer), or repo-side (CI); an LLM agent
adds cost and nondeterminism to checks that need neither.

**Retire plugin-config-drift too.** Rejected: the installer demonstrably ships plugin
config (`rsync src/ → vault`, with `agent-client/data.json` seeded from its example),
so shipped-config corruption is real and the golden copy already has the machinery to
catch and restore it.

## Related

- **Tracking issue:** [#394](https://github.com/eranroseman/memoria-vault/issues/394).
- **Related decisions:** [ADR-55](55-src-scaffold-populate-golden-copy.md) (golden copy), [ADR-25](25-session-logging-two-logs.md) (audit-chain checks), [ADR-26](26-repo-as-install-unit.md) (idempotent installer), [ADR-49](49-catalog-in-bases-linter-monitor.md) (Linter as engine).
- **Reference:** [Linter: detectors and auto-fix](../reference/linter.md).
