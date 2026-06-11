---
topic: explorations
title: Policy gate and permissions — the structural write boundary
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 18
---

# Policy gate and permissions — the structural write boundary

A design capture of the write-permission system as it is actually built in v0.1.1 —
the deterministic policy decision engine, the per-lane override files, the toolset
allowlist, and the Hermes plugin that enforces all of it at runtime. Reconstructed
by reading the real code (`vault/.memoria/`), not from intent. Implements
[ADR-03](../adr/03-structural-review-gate.md),
[ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md),
[ADR-28](../adr/28-write-gate-as-plugin.md),
[ADR-32](../adr/32-external-access-over-mcp.md), and
[ADR-46](../adr/46-seven-layer-architecture.md).

> **Why capture this.** The write gate is the architectural core — the mechanism
> that makes the human review gate *structural* rather than advisory — yet no
> exploration document described its as-built shape. The decisions are recorded
> across five ADRs; this is the single design view of how they compose in code.

## What it is

Every vault write a profile attempts is decided by a deterministic engine before it
reaches disk. The decision is a pure function of `(profile, action, path)` against a
fixed policy — no model, no prompt, no reasoning. A profile that is told (or talks
itself into believing) it may write a claim note still cannot: the engine degrades
the write to a no-op and records the attempt.

Three layers compose the boundary:

1. **The policy decision engine** — [`vault/.memoria/mcp/policy_mcp.py`](../../src/.memoria/mcp/policy_mcp.py).
2. **The per-lane overrides** — five YAML files in [`vault/.memoria/lane-overrides/`](../../src/.memoria/lane-overrides) (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer` — the [ADR-48](../adr/48-copi-and-agent-consolidation.md) lane set) that scope each profile's write paths and skills.
3. **The enforcement plugin** — [`vault/.memoria/plugins/memoria-policy-gate/`](../../src/.memoria/plugins/memoria-policy-gate), a Hermes Python plugin that runs the decision core (`policy_hook.py`) on every tool call and fails closed.

Two more files complete the picture: [`vault/.memoria/tool-registry.yaml`](../../src/.memoria/tool-registry.yaml)
is the *capability* allowlist (which tools a profile may invoke at all), complementary
to the lane-overrides' *path* allowlist (where a profile may write); and
[`vault/.memoria/schemas/folders.yaml`](../../src/.memoria/schemas/folders.yaml) is the
canonical home of the review-gated prefixes ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)).

## How it works

### The decision engine

`policy_mcp.py` decides eight actions:

```
read · write · append · move · delete · mkdir · auto_fix · report
```

and returns one of four verdicts:

```
allow · allow_with_log · deny · dry_run
```

Path matching is a hand-written glob-to-regex translator (`glob_to_regex`): `**`
crosses `/` (any number of segments, including zero), `*` stays within a segment,
`?` is a single non-`/` char. `path_matches(path, patterns)` is true if any pattern
matches. Paths are normalized to vault-relative POSIX form first; a path that
escapes the vault root (`..` traversal) is denied and audited with the raw path
(`policy_rule: path.traversal`).

The precedence, faithful to `decide()`:

1. Invalid action → `deny`.
2. **Skill-conditional deny** → `deny`. A loaded skill's `policy.deny.write` block
   narrows the lane for the session (registered via `set_session_skill`); the
   narrowing is one-way — a skill can never *widen* a lane.
3. `report` → `allow` within the lane.
4. `read` → default-allow; a read inside a review-gated zone returns
   `allow_with_log`; an explicit `deny.read` wins.
5. `auto_fix` → class-gated (table below).
6. `delete` → `deny` unless `flags.explicit_authorization` and the path is inside
   the lane's write globs (then `allow_with_log`); review-gated → `dry_run`.
7. `mkdir` → allow within `routing.write_scope`, else `deny`.
8. `write` / `append` / `move` → `deny.write` wins; else a matching `allow.write`
   is required (no match → **default-deny**). An otherwise-allowed mutating action
   in a review-gated zone degrades to `dry_run`. Every surviving mutating allow
   returns **`allow_with_log`** — never plain `allow` — so each one lands in the
   audit log with a `before_hash` to pair against its `write_complete`. (A bare
   `allow` here used to skip the audit for lanes without `require: audit_log`,
   leaving holes in the chain; PR
   [#384](https://github.com/eranroseman/memoria-vault/pull/384) closed them.
   Plain `allow` survives only on non-mutating actions — `read` / `report` —
   and `mkdir`.)

**Review-gated zones degrade, they don't error.** Any mutating action under one of

```
notes/claims/   notes/hubs/
```

is forced to `dry_run` regardless of which profile asks and regardless of what its
prompt says — the write never lands; it surfaces for human approval. This is the
structural review gate of ADR-03, expressed in two path prefixes. The prefixes are
read from `folders.yaml` (`gated_prefixes` — the canonical type→folder map of
[ADR-47](../adr/47-type-first-category-folders.md)/ADR-49); a hardcoded fallback
tuple in `policy_mcp.py` keeps the core dependency-free and is test-enforced to
stay in sync.

**Auto-fix is classed, not blanket.** Deterministic repairs are gated by class:

| Class | Verdict |
|---|---|
| `safe-and-unambiguous` | `allow_with_log` (when the lane allows the class and the path) |
| `authorized-targeted` | `allow_with_log` (same conditions) |
| `schema-content` | `dry_run` (always — needs schema-migrate) |
| `review-gated-edit` | `deny` (always) |

No shipped v0.1.1 lane grants any auto-fix class — the Linter left the profile set
for the engine layer ([ADR-46](../adr/46-seven-layer-architecture.md)), so the
class machinery is live but currently exercised only by tests.

### The audit trail

Every decision that requires logging — and all `allow_with_log` / `deny` /
`dry_run` decisions unconditionally — is appended (one JSON object per line) to
`system/logs/audit.jsonl` via `append_audit`. Fields: `timestamp`, `profile`,
`action`, `path`, `task_id`, `decision`, `policy_rule`, optional `reason`, and for
mutating actions `before_hash` / `after_hash`. Each allowed write records the file's
`before_hash` (a `sha256:`-prefixed digest; a missing file hashes as the empty
string, never null) at pre-check, and a second `write_complete` record pairs it with
`after_hash` post-write. `complete_write` does not trust the caller's `before_hash`
silently: it is validated against the latest matching pre-decision record for that
`(path, task_id)`, and a disagreement is recorded on the completion record as
`hash_mismatch: true` plus the `expected_before_hash`. `task_id` is mandatory on
every request — a request without one is denied. The continuity of these hashes is
what makes tampering *detectable* — see
[Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md).
The chain has its own watchdog: the Linter engine's `audit_unpaired_writes`
detector ([`detectors.py`](../../src/.memoria/engines/linter/detectors.py)) flags
any mutating allow whose `write_complete` never arrived within an hour — a hole in
the reversibility chain (see
[Structural linter and drift detection — zero-LLM vault health](structural-linter-and-drift.md)).

### Enforcement: a plugin, not a hook

`memoria-policy-gate` binds two Hermes hooks (`plugin.yaml` → `provides_hooks`):

- `pre_tool_call` → `_gate`: evaluates the write; returns `{"action": "block", …}` for `deny`/`dry_run`.
- `post_tool_call` → `_complete`: records the completion + `after_hash`.

The pre/post pair is correlated through a `.pending/` stash under `system/logs/`
keyed by tool-call id; stash files older than 24 hours are pruned opportunistically
on each `pre_tool_call` pass (cheap glob, never raises), so an interrupted write
can't leave the stash growing forever.

It is **fail-closed**: any exception inside the gate returns a block, never a pass
(`except Exception → {"action": "block", "message": "policy gate failed-closed …"}`).
This is ADR-28's decision — a plugin runs in every mode (CLI, gateway, cron, ACP),
where a shell hook (ADR-27's original mechanism) would not. The plugin reuses the
tested decision core verbatim (`policy_hook.evaluate_pre` / `evaluate_post`); no
policy logic lives in the plugin itself.

Beyond path-gating the obsidian writes, the decision core hard-denies two tool
families for **every** lane:

- **`DENY_DIRECT_TOOLS`** — the direct-capability families (`file`: `write_file`,
  `patch`, `read_file`, `search_files`; `terminal`: `terminal`, `run_command`;
  code-exec: `code_execution`, `execute_code`). The sandbox model is MCP-only
  (D40/ADR-46, enforced literally by PR [#364](https://github.com/eranroseman/memoria-vault/pull/364)):
  **no Memoria profile ships the `file`, `terminal`, or `code_execution` toolsets**
  (every `config.yaml` lists them in `agent.disabled_toolsets`, test-enforced), so a
  direct-capability call reaching the gate at all means config drift — it is blocked
  rather than trusted to the capability layer.
- **`DENY_OBSIDIAN`** — the native obsidian MCP's `command_execute` (arbitrary
  Obsidian command, no single path to gate), `vault_delete`, and `vault_move`
  (destructive ops the workflows don't need; least privilege).

The capability layer (`disabled_toolsets`) is the first wall; this in-process
hard-deny is the second.

### Per-lane scoping

Each `lane-overrides/<lane>.yaml` declares `policy.allow.write` / `policy.deny.write`
globs, a `policy.allow.skills` allowlist, `policy.require` invariants (every lane
sets `audit_log`; the dispatched lanes add `timeout_required`, the evidence lanes
`source_tracking`), and a `routing` block (`invocation`, `external_api_policy`,
`write_scope`). The `routing.write_scope` entries are **globs**, and the tasks MCP
validates every delegation target against them with the same `within_scope` glob
matcher the gate uses (`policy_mcp.glob_to_regex`) — so the delegation ceiling and
the write gate can never disagree about a path like `projects/x/code/main.py`
(PR [#384](https://github.com/eranroseman/memoria-vault/pull/384), B1). The scopes,
verbatim from the files:

| Lane | Allowed write globs | Denied writes | Notable keys |
|---|---|---|---|
| **copi** | *(empty — hard write-denial; `deny.write: "**"`)* | everything | `invocation: interactive_only` — the desk pane, never dispatched |
| **librarian** | `inbox/**`, `catalog/**`, `notes/fleeting/**`, `notes/source/**` | `notes/claims/**`, `notes/hubs/**`, `notes/index/**`, `projects/**`, `system/**` | `external_api_policy: explicit_only` |
| **writer** | `projects/**` | `notes/claims/**`, `notes/hubs/**`, `catalog/**`, `inbox/**`, `system/**` | `external_api_policy: blocked` — composes from the vault, never researches |
| **peer-reviewer** | `inbox/**` (flag/gap cards only) | `notes/**`, `catalog/**`, `projects/**`, `system/**` | flag-don't-fix: never edits the thing under review |
| **engineer** | `projects/*/code/**` | `notes/**`, `catalog/**`, `inbox/**`, `system/**` | the code lane only — [ADR-21](../adr/21-l3-autonomy-ceiling.md)'s Coder-lane autonomy exception is retired (MCP-only, no execution); defining the lane is [#369](https://github.com/eranroseman/memoria-vault/issues/369) |

### Capability allowlist (tool-registry.yaml)

Tools are grouped and granted per profile; anything not listed is denied
(default-deny). The groups, abridged:

```
vault_read   : obsidian.get_file_contents · list_files · search
vault_write  : obsidian.append_content · patch_content · put_content · delete_file
policy       : policy.check_permission · policy.complete_write
tasks        : tasks.delegate_route_task
cluster_read : cluster.cluster_build_graph · cluster_model_topics
cluster_map  : cluster.cluster_emit_canvas
ingest_read  : ingest.ingest_pipeline
patterns     : patterns.patterns_list · patterns_run
discovery    : paper_search.search_* (search tools only — no download_*)
zotero_read  : pyzotero.get_references · get_citations · find_related · search_semantic_scholar
qmd_read     : qmd.search · vsearch · deep_search · get · status
```

`qmd_read` is the local hybrid-search group over the shared `qmd` vector index
(BM25 + vector; the index lives outside the vault, so qmd never writes it) —
granted to the four lanes whose skills lean on similarity (co-PI, Librarian,
Writer, Peer-reviewer) and wired as an MCP server (`qmd mcp`, stdio) in those
four profile configs (PR [#384](https://github.com/eranroseman/memoria-vault/pull/384), B4).
Bootstrapping the index at install time (`qmd collection add` + `qmd embed`) is
deferred — [#385](https://github.com/eranroseman/memoria-vault/issues/385).

The co-PI is granted `vault_read` but **not** `vault_write` — a second, independent
wall behind the empty lane-override — and is the only profile granted `memory` and
`tasks` (it delegates every write as a board card). The registry is today the drift
source-of-truth the Linter checks profile configs against; having the gate *read* it
at runtime is an acknowledged TODO in the file header. One reconciliation is also
pending: the engineer's registry entry still lists `terminal` + `file` from the
v0.1.0 Coder posture, while the deployed `config.yaml` disables both and the gate
hard-denies them (PR #364) — the deny layers win.

## Design rationale

- **Structural beats advisory.** A prompt rule degrades on session restart, context
  loss, or a confidently-wrong agent. A filesystem-level decision does not. The gate
  is the same whether the agent is careful or compromised.
- **Determinism is auditable.** A reasoning router's choices are hard to verify; a
  glob match against a YAML file is trivially inspectable, testable in isolation
  (`policy_mcp.py --decide '<json>'` one-shot debugging; `tests/test_policy_mcp.py`),
  and diffable in git.
- **Degrade, don't fail.** Review-gated writes become `dry_run` and surface for
  approval rather than erroring — the human sees the *proposal*, which is the whole
  point of the gate.
- **Fail closed.** A gate that fails open is not a gate. Every error path blocks —
  including the plugin's own exceptions and any tool call the core cannot identify
  (missing profile, path, or task_id).
- **Two independent walls.** Capability (tool-registry + `disabled_toolsets`) and
  path scope (lane-overrides) are separate; the co-PI's read-only posture survives
  even if one is misconfigured.
- **MCP-only, no exceptions.** Direct filesystem/shell access is denied to every
  lane, so the obsidian MCP is the single, gateable write path — and a Hermes
  update shipping a new toolset cannot silently reopen a side door.

## Related

- [ADR-03](../adr/03-structural-review-gate.md), [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), [ADR-28](../adr/28-write-gate-as-plugin.md), [ADR-32](../adr/32-external-access-over-mcp.md), [ADR-46](../adr/46-seven-layer-architecture.md), [ADR-47](../adr/47-type-first-category-folders.md), [ADR-48](../adr/48-copi-and-agent-consolidation.md)
- [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md) — the audit + hash-chain consumer of this engine
- [Profiles and the SOUL model — one co-PI, four lanes, no orchestrator](profiles-and-soul-model.md) — the five lanes the gate scopes
- Reference docs: [`docs/reference/policy-mcp.md`](../reference/policy-mcp.md)
- Explanation: [`docs/explanation/architecture/control-plane.md`](../explanation/architecture/control-plane.md), [`why-human-gate.md`](../explanation/rationale/why-human-gate.md)
