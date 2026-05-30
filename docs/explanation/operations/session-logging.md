---
topic: operations
---

# Session logging

**Concern.** Observability / audit.
**Goal.** Preserve a durable, traceable record of agent activity.

Session logging is a **system mechanism, not a workflow.** Every agent session produces a per-session log that Git preserves — there is no card, nothing to claim, and no state transition. It runs *underneath* the card-driven workflows rather than being one; contrast [Lint](../../how-to/workflows/maintenance/lint.md) and [Refactor](../../how-to/workflows/maintenance/refactor.md), which are.

## Two logs in `00-meta/02-logs/`

Don't conflate them — different writers, different lifecycles:

- **Per-session log summaries** (`sessions/YYYY-MM-DD-HHMM.jsonl`) — one per Hermes session; the activity summary this doc is about. Hermes records the raw session activity; the [memoria-linter](../profiles/linter.md) (which owns `00-meta/02-logs/`) writes the summarized per-session log. **Not** rotated — each is small and they accumulate. **Note:** Run `mkdir -p .memoria/sessions` (or create `00-meta/02-logs/sessions/` in the vault) on first setup; this directory is not pre-created in the starter vault.
- **Policy-MCP audit log** (`audit.jsonl`) — the append-only write-decision trail, written by the policy MCP and rotated weekly by the memoria-linter. This is what the [audit-log](../dashboards/audit-log.md) and [fleet-health](../dashboards/fleet-health.md) dashboards read — not the per-session logs.

## How it works

1. Hermes runs a session and records the raw activity.
2. The memoria-linter writes the per-session log *summary* under `00-meta/02-logs/sessions/`.
3. Git captures the history; the human commits / pushes when needed.

## Related

- **Granularity:** [ADR-7 session log granularity](../../project/decisions/07-session-log-granularity.md) — per-session files, not per-action.
- **Multi-machine sync:** per-session files survive sync without conflict; see [roadmap/sync-and-coordination.md](../../project/roadmap/sync-and-coordination.md).
- **Rotation & retention:** the policy-MCP audit log is rotated by the [memoria-linter](../profiles/linter.md#log-rotation); per-session logs are not.
