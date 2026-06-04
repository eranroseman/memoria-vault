---
title: Memory substrates
parent: Reference
---

# Memory substrates

Where each type of state lives across the Memoria + Hermes stack: substrate, provider, scope, lifespan, backing store, and what it holds. Listed by how much the human touches them. For the design rationale see [The memory model](../explanation/architecture/memory-model.md).

---

## Substrate table

| Substrate | Provider | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Program memory** | Memoria — vault files | Whole research program | Persistent | Vault root (`research-focus.md`, `screening-protocol.md`) | Standing steering: discovery priorities, review mode. The human's main lever over what the system pursues. |
| **Project memory** | Memoria — vault files | One sub-project, across lanes | Project-bound; archives with the project | `40-workbench/<project>/` | Open questions, decisions, framing for one project. |
| **Audit memory** | Memoria — vault files | Whole vault | Indefinite; append-only | `99-system/logs/` + `99-system/metrics/` | Audit trail, board snapshots, weekly summaries, fleet metrics. |
| **Handoff memory** (payload) | Memoria — Kanban | One card; travels across profiles | Card-bound | Card `metadata` field | Handoff goal, context, allowed paths, expected outputs, working set of paper notes. |
| **Agent memory** (`MEMORY.md` + `USER.md`) | Hermes native | One agent (profile), all sessions | Durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-<name>/memories/` | `MEMORY.md` (~800 tokens): environment facts, conventions, learned preferences. `USER.md` (~500 tokens): human working style. Injected as a frozen snapshot. |
| **Session history** | Hermes native | One agent, all past sessions | Indefinite; unlimited capacity | SQLite at `~/.hermes/state.db` (full-text) | Searchable history of prior conversations. Retrieved on demand — costs no tokens until queried. |
| **Working memory** | Hermes native | One profile session | Session-bound; cleared on `/clear` | In-context (live conversation) | Current goal, recent tool results, in-flight reasoning. |

Token caps on `MEMORY.md` / `USER.md` are approximate as of the current Hermes runtime — verify exact limits in upstream [Hermes docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory).

---

## Ownership rules

| Rule | Details |
| --- | --- |
| Program memory is the human's steering | The human authors `research-focus` / `screening-protocol`; every profile reads it; it never archives — the program outlives any one project. |
| Project memory is the per-project cross-lane channel | One project's working state — anything that must survive across lanes *within that project*. Archives with the project. |
| Audit memory is append-only | Profiles read it; the Policy MCP writes an audit entry at every gated write. The Linter does not write entries — it only rotates the log. |
| Handoff memory is per-card, not per-profile | When a card moves from Librarian → Writer lane, the handoff payload travels with it. Writer does not inherit Librarian's working memory. |
| Agent memory is frozen at session start | Mid-session writes are not visible until the next session. Keep it small and stable — not in-flight task state. |
| Session history is read-only history | Never gates promotion; never authoritative over the vault. |
| Working memory is not shared | Librarian's in-session reasoning does not bleed into the Writer's session. `/clear` discards it. |

---

## What lives where — decision table

| State type | Correct substrate | Wrong substrate (common mistake) |
| --- | --- | --- |
| What you want the system to pursue | Program memory (`research-focus`) | `project-hints.yaml` (that's config, not recall) |
| One project's open questions / decisions | Project memory (`40-workbench/<project>/`) | Handoff memory (card-scoped, dies with card) |
| Current task goal and context | Handoff memory (payload) | Agent memory (too local, capped, frozen at start) |
| Stable facts about the environment | Agent `MEMORY.md` | Working memory (not persistent) |
| Human preferences and style | Agent `USER.md` | `MEMORY.md` (keep identity vs. preference separate) |
| Cross-session retrieval | Session history | Agent memory (too small for bulk recall) |
| Audit trail of all decisions | Audit memory (`99-system/logs/audit.jsonl`) | Agent memory (wrong granularity) |
| Durable synthesized knowledge | Vault notes (`30-synthesis/`) | Any of the above |

---

## Agent memory file locations

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
| Schedule | Monday 00:00 (start of the ISO week) — the Linter cron runs `0 4 * * MON` |
| Trigger (size) | When `audit.jsonl` exceeds 50 MB |
| Archive path | `99-system/logs/archive/audit-YYYY-WW.jsonl` (ISO week-numbered) |
| Retention | Indefinite (configurable via `.memoria/log-retention.yaml`) |
| Auto-fix class | `authorized-targeted` (policy MCP allows without escalation) |

Session logs (`99-system/logs/sessions/YYYY-MM-DD-HHMM.jsonl`) are written one per Hermes session and not rotated.

---

## Related

- The audit log writer and decision protocol: [Policy MCP](policy-mcp.md)
- Thin control over thick state: [Why three layers, not one](../explanation/rationale/why-three-layers.md)
- The board as the coordination substrate: [Kanban board](../explanation/kanban-board/README.md)
