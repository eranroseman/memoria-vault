---
title: Memory substrates
parent: Reference
---

# Memory substrates

Where each type of state lives across the Memoria + Hermes stack: tier, backing store, scope, lifespan, and what it holds. For the design rationale see [explanation/architecture/memory-tiers.md](../explanation/architecture/memory-tiers.md).

---

## Substrate table

| Tier | Provider | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Working context** | Hermes native | One profile session | Session-bound; cleared on `/clear` | In-context (live conversation) | Current goal, recent tool results, in-flight reasoning. |
| **Profile memory** (`MEMORY.md` + `USER.md`) | Hermes native | One profile, all sessions | Durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-<name>/memories/` | `MEMORY.md` (~800 tokens): environment facts, conventions, learned preferences. `USER.md` (~500 tokens): human working style. Injected into system prompt at session start as a frozen snapshot. |
| **Session search** | Hermes native | One profile, all past sessions | Indefinite; unlimited capacity | SQLite at `~/.hermes/state.db` (full-text) | Searchable history of prior conversations. Retrieved on demand — costs no tokens until queried. |
| **Board memory** (handoff payload) | Memoria — Kanban | One card; travels across profiles | Card-bound | Card `metadata` field | Handoff goal, context, allowed paths, expected outputs, working set of paper notes. |
| **Vault project memory** | Memoria — vault files | One project, across lanes | Project-bound | `40-workbench/<project>/` | `research-directions`, open questions, decisions log. Shared across all profiles touching the project. |
| **Vault audit memory** | Memoria — vault files | Whole vault | Indefinite; append-only | `99-system/logs/` + `99-system/metrics/` | Audit trail, board snapshots, weekly summaries, fleet metrics. |

Token caps on `MEMORY.md` / `USER.md` are approximate as of the current Hermes runtime — verify exact limits in upstream [Hermes docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory).

---

## Ownership rules

| Rule | Details |
| --- | --- |
| Working context is not shared | Librarian's in-session reasoning does not bleed into the Writer's session. `/clear` discards it. |
| Profile memory is frozen at session start | Mid-session writes are not visible until the next session. Keep it small and stable — not in-flight task state. |
| Session search is read-only history | Never gates promotion; never authoritative over the vault. |
| Board memory is per-card, not per-profile | When a card moves from Librarian → Writer lane, the handoff payload travels with it. Writer does not inherit Librarian's working context. |
| Vault project memory is the cross-lane channel | Anything that must survive across lanes within a project belongs here, not in profile memory. |
| Vault audit memory is append-only | Profiles read it; only the Linter writes to it. |

---

## What lives where — decision table

| State type | Correct substrate | Wrong substrate (common mistake) |
| --- | --- | --- |
| Current task goal and context | Board memory (handoff payload) | Profile memory (too local, capped, frozen at start) |
| Stable facts about the environment | Profile `MEMORY.md` | Working context (not persistent) |
| Human preferences and style | Profile `USER.md` | Working context (not persistent) |
| Cross-session retrieval | Session search | Profile memory (too small for bulk recall) |
| Project-level decisions | Vault project memory (`40-workbench/<project>/`) | Board memory (card-scoped, dies with card) |
| Audit trail of all decisions | Vault audit memory (`99-system/logs/audit.jsonl`) | Profile memory (wrong granularity) |
| Durable synthesized knowledge | Vault notes (`30-synthesis/`) | Any of the above |

---

## Profile memory file locations

| File | Location | Token cap (approx.) | Injected as |
| --- | --- | --- | --- |
| `MEMORY.md` | `~/.hermes/profiles/memoria-<name>/memories/MEMORY.md` | ~800 tokens | Frozen snapshot in system prompt slot |
| `USER.md` | `~/.hermes/profiles/memoria-<name>/memories/USER.md` | ~500 tokens | Frozen snapshot in system prompt slot |

`SOUL.md` is **not** memory — it is the profile's identity prompt (stable across sessions by design).

---

## Audit log event fields

Every policy MCP decision appended to `99-system/logs/audit.jsonl`:

| Field | Type | Notes |
| --- | --- | --- |
| `timestamp` | ISO datetime | When the decision occurred (UTC, `...Z`). |
| `profile` | string | `memoria-<name>` — which profile triggered the write. |
| `action` | string | The vault action attempted (one of the eight: `read`/`write`/`append`/`move`/`delete`/`mkdir`/`auto_fix`/`report`). |
| `path` | string | Vault path the action targeted. |
| `task_id` | string | The Kanban card that triggered the action (required on every request). |
| `decision` | enum | `allow` · `allow_with_log` · `deny` · `dry_run` |
| `policy_rule` | string | Which lane-override rule matched (for audit-trail reconstruction). |
| `before_hash` | SHA-256 | Hash of the file before the write (tamper-detection chain). For a create, the empty-string SHA-256, not null. |
| `after_hash` | SHA-256 | Hash after the write (set on the `write_complete` record written by the `post_tool_call` hook). |

The `before_hash` / `after_hash` chain must be unbroken across the entire log. `vault-hash-drift` fires if any link fails.

### Log rotation

| Setting | Value |
| --- | --- |
| Schedule | Sunday 00:00 local time |
| Trigger (size) | When `audit.jsonl` exceeds 50 MB |
| Archive path | `99-system/logs/archive/audit-YYYY-WW.jsonl` (ISO week-numbered) |
| Retention | Indefinite (configurable via `.memoria/log-retention.yaml`) |
| Auto-fix class | `authorized-targeted` (policy MCP allows without escalation) |

Session logs (`99-system/logs/sessions/YYYY-MM-DD-HHMM.jsonl`) are written one per Hermes session and not rotated.

---

## Related

- The audit log writer and decision protocol: [policy-mcp.md](policy-mcp.md)
- Thin control over thick state: [why-three-layers.md](../explanation/rationale/why-three-layers.md)
- The board as the coordination substrate: [kanban-board/README.md](../explanation/kanban-board/README.md)
