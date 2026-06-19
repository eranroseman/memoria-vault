---
title: Memory substrates
parent: Reference
---

# Memory substrates

Where each type of state lives across the Memoria + Hermes stack: substrate, provider, scope, lifespan, backing store, and what it holds. Listed by how much the PI touches them.

**The Co-PI is the sole carrier of the Hermes memory loop**: only `memoria-copi` keeps the `memory` toolset (plus `/goals`, skills, `/personality`) — it alone accumulates working preferences and environment facts across sessions. The four specialist lanes ship with `memory` in `agent.disabled_toolsets`: a dispatched worker gets everything it needs from the handoff payload and the vault, so per-lane memory would only drift. See the per-profile allowlists in `src/.memoria/tool-registry.yaml`.

---

## Substrate table

| Substrate | Provider | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Program memory** | Memoria — vault files | Whole research program | Persistent | Vault root (`research-focus.md`) | Standing steering: discovery priorities, review mode. The PI's main lever over what the system pursues. |
| **Project memory** | Memoria — vault files | One project, across lanes | Project-bound; archives with the project | `projects/<project>/` | Open questions, decisions, framing for one project. |
| **Audit memory** | Memoria — vault files | Whole vault | Indefinite; append-only | `system/logs/` + `system/metrics/` | Audit trail, capture-intake anchors, pattern provenance, board projections, fleet metrics. |
| **Handoff memory** (payload) | Memoria — Kanban | One card; travels across lanes | Card-bound | Card `metadata` | The handoff payload — schema owned by the [Kanban board reference](kanban-board.md). |
| **Agent memory** (`MEMORY.md` + `USER.md`) | Hermes native | **The Co-PI only** | Durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-copi/memories/` | `MEMORY.md` (~800 tokens): environment facts, conventions, learned preferences. `USER.md` (~500 tokens): the PI's working style. Disabled on the four specialist lanes. |
| **Session history** | Hermes native | One profile, all past sessions | Indefinite | SQLite at `~/.hermes/state.db` (full-text) | Searchable history of prior conversations; costs no tokens until queried. |
| **Working memory** | Hermes native | One session | Session-bound; cleared on `/clear` | In-context | Current goal, recent tool results, in-flight reasoning. |

Token caps on `MEMORY.md` / `USER.md` are approximate — verify in the upstream [Hermes docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory).

---

## Ownership rules

| Rule | Details |
| --- | --- |
| Program memory is the PI's steering | The PI authors `research-focus.md`; every profile reads it; it never archives. |
| Project memory is the per-project cross-lane channel | Anything that must survive across lanes within one project. Archives with the project. |
| Audit memory is append-only | The policy gate writes an entry at every decision; operations append their own logs (`capture-intake.jsonl`, `patterns.jsonl`). |
| Handoff memory is per-card, not per-profile | When work moves Librarian → Writer, the payload travels with the card; the Writer does not inherit the Librarian's working memory. |
| Agent memory is the Co-PI's alone | Frozen at session start; mid-session writes show up next session. Keep it small and stable — not in-flight task state. Specialists have it disabled. |
| Session history is read-only history | Never gates anything; never authoritative over the vault. |
| Working memory is not shared | One lane's in-session reasoning never bleeds into another's. |

---

## What lives where — decision table

| State type | Correct substrate | Wrong substrate (common mistake) |
| --- | --- | --- |
| What you want the system to pursue | Program memory (`research-focus.md`) | `project-hints.yaml` (that's config, not recall) |
| One project's open questions / decisions | Project memory (`projects/<project>/`) | Handoff memory (card-scoped, dies with the card) |
| Current task goal and context | Handoff memory (payload) | Agent memory (capped, frozen at start — and disabled on lanes) |
| Stable facts about the environment | Co-PI `MEMORY.md` | Working memory (not persistent) |
| The PI's preferences and style | Co-PI `USER.md` | `MEMORY.md` (keep identity vs preference separate) |
| Cross-session retrieval | Session history | Agent memory (too small for bulk recall) |
| Audit trail of all decisions | Audit memory (`system/logs/audit.jsonl`) | Agent memory (wrong granularity) |
| Durable synthesized knowledge | Vault notes (`notes/claims/`, `notes/hubs/`) | Any of the above |

`SOUL.md` is **not** memory — it is the profile's identity prompt, stable across sessions by design.

---

## Audit memory

The audit trail (`system/logs/audit.jsonl`) records every policy decision with its before/after hash pair. Its field schema, the eight guarded actions, the `decision` enum, and the per-write hash-pairing mechanism are owned by [Policy MCP](policy-mcp.md#audit-log-format).

---

## Related

- The writer of the audit log: [Policy MCP](policy-mcp.md)
- The capability allowlist that disables specialist memory: [Profile capabilities](profiles.md)
- The handoff payload schema: [Kanban board reference](kanban-board.md)
