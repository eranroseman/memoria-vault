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

A design capture of the write-permission system as it is actually built — the
deterministic policy decision engine, the per-lane override files, the toolset
allowlist, and the Hermes plugin that enforces all of it at runtime. Reconstructed
by reading the real code (`vault/.memoria/`), not from intent. Implements
[ADR-03](../adr/03-structural-review-gate.md),
[ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md),
[ADR-28](../adr/28-write-gate-as-plugin.md), and
[ADR-32](../adr/32-external-access-over-mcp.md).

> **Why capture this.** The write gate is the architectural core — the mechanism
> that makes the human review gate *structural* rather than advisory — yet no
> exploration document described its as-built shape. The decisions are recorded
> across four ADRs; this is the single design view of how they compose in code.

## What it is

Every vault write a profile attempts is decided by a deterministic engine before it
reaches disk. The decision is a pure function of `(profile, action, path)` against a
fixed policy — no model, no prompt, no reasoning. A profile that is told (or talks
itself into believing) it may write a claim note still cannot: the engine degrades
the write to a no-op and records the attempt.

Three layers compose the boundary:

1. **The policy decision engine** — [`vault/.memoria/mcp/policy_mcp.py`](../../vault/.memoria/mcp/policy_mcp.py).
2. **The per-lane overrides** — seven YAML files in [`vault/.memoria/lane-overrides/`](../../vault/.memoria/lane-overrides) that scope each profile's write paths and skills.
3. **The enforcement plugin** — [`vault/.memoria/plugins/memoria-policy-gate/`](../../vault/.memoria/plugins/memoria-policy-gate), a Hermes Python plugin that runs the engine on every tool call and fails closed.

A fourth file, [`vault/.memoria/tool-registry.yaml`](../../vault/.memoria/tool-registry.yaml), is the *capability* allowlist (which tools a profile may invoke at all), complementary to the lane-overrides' *path* allowlist (where a profile may write).

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
matches.

**Review-gated zones degrade, they don't error.** Any mutating action under one of

```
30-synthesis/01-claims/   30-synthesis/02-reference/
30-synthesis/03-moc/      50-deliverables/
```

is forced to `dry_run` regardless of which profile asks and regardless of what its
prompt says — the write never lands; it surfaces as a board comment for human
approval. This is the structural review gate of ADR-03, expressed in four path
prefixes.

**Auto-fix is classed, not blanket.** The Linter's repairs are gated by class:

| Class | Verdict |
|---|---|
| `safe-and-unambiguous` | allow |
| `authorized-targeted` | allow |
| `schema-content` | `dry_run` (needs schema-migrate) |
| `review-gated-edit` | `deny` (always) |

### The audit trail

Every decision is appended (one JSON object per line) to
`99-system/logs/audit.jsonl` via `append_audit`. Fields: `timestamp`, `profile`,
`action`, `path`, `task_id`, `decision`, `policy_rule`, optional `reason`, and for
mutating actions `before_hash` / `after_hash`. Each allowed write records the file's
`before_hash` (a `sha256:`-prefixed digest; a missing file hashes as the empty
string, never null) at pre-check, and a second `write_complete` record pairs it with
`after_hash` post-write. The continuity of these hashes is what makes tampering
*detectable* — see [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md).

### Enforcement: a plugin, not a hook

`memoria-policy-gate` binds two Hermes hooks (`plugin.yaml` → `provides_hooks`):

- `pre_tool_call` → `_gate`: evaluates the write; returns `{"action": "block", …}` for `deny`/`dry_run`.
- `post_tool_call` → `_complete`: records the completion + `after_hash`.

It is **fail-closed**: any exception inside the gate returns a block, never a pass
(`except Exception → {"action": "block", "message": "policy gate failed-closed …"}`).
This is ADR-28's decision — a plugin runs in every mode (CLI, gateway, cron, ACP),
where a shell hook (ADR-27's original mechanism) would not.

### Per-lane scoping

Each `lane-overrides/<profile>.yaml` declares `policy.allow.write` / `policy.deny.write`
globs, a `policy.allow.skills` allowlist, `policy.require` invariants (e.g.
`audit_log`, `read_only_mode`, `review_gated_write`, `dry_run_default`), and a
`routing` block. The scopes, verbatim from the files:

| Lane | Allowed write globs | Notable keys |
|---|---|---|
| **librarian** | `10-inbox/01-fleeting/**`, `10-inbox/03-candidates/**`, `20-sources/**` | `external_api_policy: explicit_only` |
| **writer** | `10-inbox/02-answers/**`, `40-workbench/*/{02-framing,03-canvas,04-drafts}/**`, `30-synthesis/02-reference/**`, `50-deliverables/**` (last two review-gated) | `require: review_gated_write` |
| **mapper** | `40-workbench/*/01-map/{corpus-map.md,gap-report.md,cluster-maps/**}` | `require: read_only_mode` |
| **socratic** | *(empty — hard write-denial; `deny.write: "**"`)* | `invocation: interactive_only` |
| **verifier** | `40-workbench/*/05-verification/**`, `10-inbox/03-candidates/**` | `require: read_only_mode` |
| **coder** | `40-workbench/*/06-code/**` | `external_api_policy: explicit_only` |
| **linter** | `99-system/logs/**` + `auto_fix.classes: [safe-and-unambiguous, authorized-targeted]` | `require: dry_run_default` |

### Capability allowlist (tool-registry.yaml)

Tools are grouped and granted per profile; anything not listed is denied
(default-deny). Groups:

```
vault_read  : obsidian.get_file_contents · list_files · search
vault_write : obsidian.append_content · patch_content · put_content · delete_file
web         : web_search · web_extract
policy      : policy.check_permission · policy.complete_write
```

Socratic is granted `vault_read` but **not** `vault_write` — a second, independent
wall behind the empty lane-override. Coder and Linter alone hold `terminal`/`file`
(for git and `detectors.py`); `web` and `code_execution` are off everywhere else,
per ADR-32. The obsidian MCP is the only write path any non-terminal lane has, per
ADR-27.

## Design rationale

- **Structural beats advisory.** A prompt rule degrades on session restart, context
  loss, or a confidently-wrong agent. A filesystem-level decision does not. The gate
  is the same whether the agent is careful or compromised.
- **Determinism is auditable.** A reasoning router's choices are hard to verify; a
  glob match against a YAML file is trivially inspectable, testable in isolation
  (`policy_mcp.py --self-test`), and diffable in git.
- **Degrade, don't fail.** Review-gated writes become `dry_run` and surface for
  approval rather than erroring — the human sees the *proposal*, which is the whole
  point of the gate.
- **Fail closed.** A gate that fails open is not a gate. Every error path blocks.
- **Two independent walls.** Capability (tool-registry) and path scope (lane-overrides)
  are separate; Socratic's read-only posture survives even if one is misconfigured.

## Related

- [ADR-03](../adr/03-structural-review-gate.md), [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), [ADR-28](../adr/28-write-gate-as-plugin.md), [ADR-32](../adr/32-external-access-over-mcp.md)
- [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md) — the audit + hash-chain consumer of this engine
- [Profiles and the SOUL model — seven specialists, no orchestrator](profiles-and-soul-model.md) — the seven lanes the gate scopes
- Reference docs: [`docs/reference/policy-mcp.md`](../reference/policy-mcp.md)
- Explanation: [`docs/explanation/architecture/control-plane.md`](../explanation/architecture/control-plane.md), [`why-human-gate.md`](../explanation/rationale/why-human-gate.md)
