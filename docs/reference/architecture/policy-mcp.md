---
topic: architecture
---

# Policy MCP

Profile permissions and lane scopes are not just documentation — they are enforced at the tool layer by a **policy MCP** that intercepts every vault write. This document is the detailed contract; the summary lives in [architecture/README.md](../../explanation/architecture/README.md).

## Why a runtime gate

Prompts are advisory. A profile that *should* only write to `10-inbox/` can be coaxed by a malformed task, a hallucinated path, or an overreaching delegation into writing somewhere it shouldn't. The review gate (see [kanban-board/README.md](../../explanation/kanban-board/README.md)) catches this at the human-decision level, but the policy MCP catches it at the file-system level — before the write happens, not after.

This is what makes the lane-override files (see [profiles/README.md](../../explanation/profiles/README.md#lane-override-files)) executable rather than aspirational.

## The decision protocol

Every vault action goes through `check_permission(profile, action, path, task_id, flags?)`. The MCP returns one of four decisions:

| Decision | Meaning | When it fires |
| --- | --- | --- |
| `allow` | Action proceeds. Logged only if the lane's `policy.require` includes `audit_log`. | Path matches the lane's `policy.allow` patterns, no `policy.deny` matches, and the action is routine. |
| `allow_with_log` | Action proceeds. Audit entry is **mandatory** regardless of lane policy. | The action is allowed but operationally significant — cross-zone moves, reads of canonical content, any action with `flags.explicit_authorization`. |
| `deny` | Action is blocked; the worker must escalate or pick a different path. Always logged. | Path matches a `policy.deny` rule, or no rule matches at all (default-deny). |
| `dry_run` | Action is logged and reported but not performed; the worker should escalate to a board comment for human approval. Always logged. | Path is in a review-gated zone (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) even if the profile is otherwise allowed. |

`task_id` is **required**, not optional. Hermes delegated children return summaries rather than sharing live state, so every MCP request must carry full identity from the parent handoff packet — the MCP cannot ask the worker "which task are you running?" mid-decision.

## Action vocabulary

The MCP guards eight distinct actions. The distinction matters: a Librarian with `write` access to `10-inbox/` should not be able to `delete` from it, and a Linter with `auto_fix` should not be able to `write` arbitrary content.

| Action | Meaning | Default disposition |
| --- | --- | --- |
| `read` | Read a file's content. | `allow` for paths inside `policy.allow.read`; `allow_with_log` for review-gated zones and cross-zone reads. |
| `write` | Create or overwrite a file's content. | The dominant case. Governed by `policy.allow.write`. |
| `append` | Add to the end of an existing file. | Used for audit logs, session logs. Allowed for the file's own lane. |
| `move` | Rename or relocate a file. | `allow_with_log` for same-zone; `dry_run` for cross-zone unless `flags.explicit_authorization`. |
| `delete` | Remove a file. | `deny` by default for all profiles. Requires `flags.explicit_authorization` and `allow_with_log`. |
| `mkdir` | Create a folder. | `allow` for paths inside `routing.write_scope`. |
| `auto_fix` | Linter-only repair action. | Class-gated by `flags.class` (see [linter.md](../../explanation/profiles/linter.md#auto-fix-policy)). |
| `report` | Attach a dry-run report or board comment. | Always allowed within the worker's lane. |

Two structural rules sit above the lane configuration:

- **Review-gated zones are never auto-written.** Even if a worker's lane policy would otherwise allow it, writes to a review-gated zone degrade to `dry_run`. The human approves the write; the worker does not perform it directly.
- **Linter auto-fix is class-gated.** When `profile = "memoria-linter"` and `action = "auto_fix"`, the MCP requires `flags.class ∈ {"safe-and-unambiguous", "authorized-targeted"}`. Schema / content changes and review-gated-zone edits are always `deny` regardless of who requests them. This is the runtime enforcement of the auto-fix policy in [linter.md](../../explanation/profiles/linter.md#auto-fix-policy).

## Skill-conditional policy

Lane-overrides are the baseline policy a profile carries through a session. A small set of skills need to *tighten* that baseline. The currently-shipped example: `counter-outline` (loaded by Writer during the Frame stage) must narrow Writer's write scope from `40-workbench/*/04-drafts/**` to `40-workbench/*/02-framing/**` only — so the human can't accidentally use Writer-with-counter-outline to write actual drafts. Skill-conditional policy is the mechanism.

(For why `socratic-processing` and `lens-reading` are now native to the Socratic profile rather than restrictive skills — and the one-way promotion rule that motivates the choice — see the [restrictive-skills note in profiles/README.md](../../explanation/profiles/README.md#skills-with-restrictive-policy).)

### The frontmatter contract

A skill that needs to tighten policy declares the additional rules in its SKILL.md frontmatter under a top-level `policy:` block. Shape:

```yaml
---
name: counter-outline
description: Generate competing project outlines before drafting
model: anthropic/claude-sonnet-4-6
policy:
  deny:
    write:
      - "30-synthesis/**"
      - "50-deliverables/**"
      - "10-inbox/**"
      - "40-workbench/*/04-drafts/**"
  require:
    - audit_log
---
```

The `policy:` block has the same three sub-keys as a lane-override (`allow`, `deny`, `require`) but only `deny` and `require` are honored at the skill level. Skills **cannot** declare `policy.allow` — a skill may only narrow the host lane's permissions, never widen them. If a skill needs a permission its host lane doesn't grant, it must be loaded by a profile whose lane grants it.

### Composition semantics

When a session loads a skill with a `policy:` block, the effective policy for that session is:

```text
session_policy = lane_policy ∩ skill_policy
              = lane_policy with skill's deny rules added,
                lane_policy's require rules unioned with skill's require rules
```

Concretely:

- **Deny composition is additive.** Every `policy.deny` rule from the lane *and* every `policy.deny` rule from the skill applies. The narrower set wins.
- **Allow composition is intersection-style.** Since the skill cannot declare `policy.allow`, the lane's `policy.allow` is the ceiling. The skill's denies can only carve from that ceiling, never raise it.
- **Require composition is union.** Any `require` invariant from either the lane or the skill must hold.
- **The session cannot loosen itself.** No tool call, no delegation, and no nested skill load can override a deny rule the skill brought in. The narrowing is one-way for the session's lifetime.

### Enforcement path

The MCP enforces skill-conditional policy at the same place it enforces lane policy: every `check_permission` call. The session identifier (carried in `task_id`) lets the MCP look up which skill, if any, is currently loaded for the session and apply the composed policy. If a skill is unloaded mid-session, the MCP returns to the lane-only policy for subsequent calls — but unloading does not retroactively change decisions already made.

A worker that tries to evade skill-conditional policy by loading and unloading the skill repeatedly will see every write between the load points return `deny`; the unload boundaries don't move the goalposts.

### Memoria's restrictive skills

One skill currently ships with a skill-conditional `policy.deny` block: `counter-outline` (Writer-loaded; scratch-only writes to `40-workbench/*/02-framing/`). The catalog and rationale live in [profiles/README.md](../../explanation/profiles/README.md#skills-with-restrictive-policy). New restrictive skills are added by editing the host lane's `policy.allow.skills` list and dropping the `SKILL.md` (with the additive `policy.deny` block in its frontmatter); the review is that the deny rules don't contradict the host lane's allow rules into uselessness. The richer lifecycle governance overlay ([roadmap/skill-governance.md](../../project/roadmap/skill-governance.md)) is deferred.

When a capability needs **strict** write-denial that survives all host profiles, promote it to its own profile (as `socratic-processing` and `lens-reading` were promoted into the Socratic profile). Skill-conditional policy is the right tool for "narrow this profile's writes for one specific kind of work"; profile-level lane policy is the right tool for "this capability has no business writing anywhere, ever, full stop."

## Request and response contracts

The MCP is invoked over MCP-standard JSON. Every request carries full identity; the response always includes the matched `policy_rule` so the audit trail can be reconstructed.

**Request:**

```json
{
  "profile": "memoria-coder",
  "action": "write",
  "path": "40-workbench/project-x/06-code/main.py",
  "reason": "implement parser fix",
  "task_id": "TASK-2026-05-25-014",
  "flags": {
    "explicit_authorization": false,
    "proposed_only": false,
    "class": null
  }
}
```

- `profile` and `action` are required.
- `path` is normalized relative to the vault root (no leading `./`, forward slashes only).
- `reason` is short prose for the audit log; useful when the same `policy_rule` fires for many paths.
- `task_id` is required (see "decision protocol" above for why).
- `flags.explicit_authorization` upgrades the disposition for `move` and `delete` actions.
- `flags.proposed_only` permits a soft write to a review-gated zone that lives outside the canonical file (e.g., a board comment proposing a change).
- `flags.class` is required when `action = "auto_fix"`.

**Response — allow / allow_with_log:**

```json
{
  "decision": "allow",
  "policy_rule": "Coder.write.40-workbench-code",
  "log_required": false
}
```

**Response — deny:**

```json
{
  "decision": "deny",
  "policy_rule": "Writer.deny.30-synthesis-claims",
  "message": "memoria-writer cannot write to canonical claim notes"
}
```

**Response — dry_run:**

```json
{
  "decision": "dry_run",
  "policy_rule": "review_gated.dry_run",
  "message": "Review-gated zone write requires explicit approval — surface as board comment"
}
```

Workers must surface `deny` and `dry_run` responses to the board as either a `declined` move or an explicit comment with the `policy_rule` cited. A worker that swallows a `deny` and tries a different path silently is misconfigured.

## What gets logged

Every decision — `allow`, `allow_with_log`, `deny`, or `dry_run` — is appended to `00-meta/02-logs/audit.jsonl` as one JSON object per line:

```json
{
  "timestamp": "2026-05-25T14:32:11Z",
  "profile": "memoria-writer",
  "action": "write",
  "path": "10-inbox/02-answers/2026-05-25-effect-of-X.md",
  "task_id": "TASK-2026-05-25-014",
  "decision": "allow",
  "policy_rule": "Writer.write.10-inbox",
  "before_hash": "sha256:8a4c5...",
  "after_hash": "sha256:e7d92..."
}
```

The `before_hash` and `after_hash` fields are SHA-256 hashes of the file content immediately before and after the write. They serve two functions:

- **Tamper detection.** If a file's current hash doesn't match the last `after_hash` recorded for its path, the file was modified outside the audit trail — either by a non-MCP write or by direct hand-editing. The Linter surfaces these mismatches (see [linter.md](../../explanation/profiles/linter.md)).
- **Reversibility.** Every write is reversible because the `before_hash` plus the previous audit entry's `after_hash` pins the prior state. Reverting a bad write means restoring the content whose hash matches `before_hash`.

For `read` actions, only `before_hash` is set (no after). For `deny` and `dry_run`, neither hash is set (no write occurred).

The append-only JSONL format means the trail survives crashes, is grep-friendly, and feeds the [audit-log dashboard](../../explanation/dashboards/audit-log.md) directly. The Linter is responsible for weekly rotation (see [linter.md](../../explanation/profiles/linter.md)).

## Implementation requirement: SHA-256 hashing

Computing `before_hash` and `after_hash` is the policy MCP's responsibility, not the worker's. The rule:

- **Hash the file, not the request.** The MCP reads the file content at the moment of the check (for `before_hash`) and immediately after the write completes (for `after_hash`). Workers never compute or supply hashes — they would be the wrong source of truth.
- **Always SHA-256.** No configurable algorithm, no truncation. Stored as `"sha256:<64-hex-chars>"` so the algorithm is self-describing.
- **Hash empty files too.** A newly created file's `before_hash` is the SHA-256 of an empty byte string (`e3b0c442...`), not `null`. Skipping the hash on creates breaks tamper detection on the create event.
- **Performance is not a concern at this scale.** SHA-256 runs at hundreds of MB/sec on modern hardware; for typical vault notes (single-digit KB), the hash takes microseconds. The cost is rounding error compared to the policy lookup itself.
- **Hash failures are `deny`.** If the MCP can't read the file to hash it (permissions error, race with a concurrent delete), the decision is `deny`, not "log without hash." The hash is part of the contract — no hash, no allow.

This is the only piece of vault state the policy MCP touches outside the audit log itself. Everything else — the lane-override files, the task registry, the board state — lives in other components.

## What the policy MCP is not

- **Not a substitute for the review gate.** It enforces *where* a worker may write; the board enforces *whether* the output becomes canonical. Both gates exist for different failure modes.
- **Not a content checker.** It does not inspect the body of a write — only the path, profile, and action.
- **Not a hidden controller.** Every rule lives in a versioned lane-override file. Nothing is encoded in the MCP that isn't also in the lane files.

## Relationship to Hermes Tirith

Memoria's policy MCP is the canonical enforcement layer for vault writes — the design treats it as self-contained, not as a bridge to another engine. Hermes ships with its own policy primitive (**Tirith**, configured via `tirith_enabled` and `tirith_fail_open` keys) that operates at a different scope: per-profile tool-call gating (which tools a profile may *invoke*). Memoria's policy MCP operates at the vault-write scope (what each invocation may *write to disk*, including which paths, with which audit-log shape, with which SHA-256 hashes).

The two coexist without conflict:

- **Tirith decides which tools a profile may call.** Hermes-side, per-profile, runtime-internal.
- **Memoria's policy MCP decides what each call may write.** Memoria-side, per-lane via lane-overrides, MCP-pattern, externally specifiable.

The policy MCP's contract — action vocabulary, four-decision protocol, SHA-256 audit hashes, skill-conditional composition — is what the rest of Memoria depends on: the [M-series drift detectors](../../explanation/profiles/linter.md), the [audit-log dashboard](../../explanation/dashboards/audit-log.md), the inline-callout writes, the reversibility guarantee. Those aren't features Memoria could drop to use Tirith alone; they're how Memoria's design holds together.

**Framework portability.** Because the enforcement contract is documented and self-contained, Memoria's design works against any MCP-capable agent — Hermes, Claude Code, Aider, custom clients. Humans using Hermes can leave Tirith enabled; humans running Memoria against a different agent framework only need the policy MCP.

**Debugging.** An unexpected `deny` is a Memoria-side question: check the lane-override YAML for what the rule says, then the policy MCP's audit log for the actual decision. Tirith logs would surface a different category of failure (tool-call rejected entirely) that's distinct from path-level write denials.

## Related design documents

- [architecture/README.md](../../explanation/architecture/README.md) — three-layer model the MCP sits inside
- [profiles/README.md](../../explanation/profiles/README.md#lane-override-files) — the lane-override YAML files the MCP reads
- [linter.md](../../explanation/profiles/linter.md) — the Linter's auto-fix policy classes the MCP enforces; vault hash drift detection
- [audit-log dashboard](../../explanation/dashboards/audit-log.md) — human view of decisions
