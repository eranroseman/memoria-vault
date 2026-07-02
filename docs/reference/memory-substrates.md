---
title: Memory substrates
parent: Pipelines and I/O
grand_parent: Reference
---

# Memory substrates

Where each type of state lives in the standalone Memoria workspace: substrate,
provider, scope, lifespan, backing store, and contents.

---

## Substrate table

| Substrate | Provider | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Program memory** | Memoria — vault files | Whole research program | Persistent | Vault root (`steering.md`) | Standing steering: discovery priorities, review mode. The PI's main lever over what the system pursues. |
| **Project memory** | Memoria — vault files | One project, across lanes | Project-bound; archives with the project | `knowledge/projects/<project>.md` | Open questions, decisions, framing for one project. |
| **Audit memory** | Memoria — vault files | Whole vault | Indefinite; append-only | `system/logs/` + `system/metrics/` | Audit trail, capture-intake anchors, pattern provenance, request projections, and metrics. |
| **Request memory** (payload) | Memoria — SQLite | One operation request | Request-bound | `.memoria/memoria.sqlite` | Input refs, output intents, precondition hashes, status, error, and provenance. |
| **Working memory** | Runner/session | One operation run | Session-bound | In-context/runtime process | Current goal, recent tool results, and in-flight reasoning. |
| **Adapter memory** | Optional external adapter | Adapter-defined | Adapter-defined | Outside the core workspace | Not authoritative in alpha.14; adapters must call the CLI/engine and may not replace workspace state. |

---

## Ownership rules

| Rule | Details |
| --- | --- |
| Program memory is the PI's steering | The PI authors `steering.md`; every operation can read it; it never archives. |
| Project memory is the per-project channel | Anything that must survive across operations within one project. Archives with the project. |
| Audit memory is append-only | The policy gate writes an entry at every decision; operations append their own logs (`capture-intake.jsonl`, `patterns.jsonl`). |
| Request memory is per-request, not global | When work resumes, the request row and journal provide the durable handoff. |
| Adapter memory is never authoritative | External chat/session history can inform a human but cannot replace checked workspace state. |
| Working memory is not shared | One operation's in-session reasoning never bleeds into another's. |

---

## What lives where — decision table

| State type | Correct substrate | Wrong substrate (common mistake) |
| --- | --- | --- |
| What you want the system to pursue | Program memory (`steering.md`) | `project-hints.yaml` (that's config, not recall) |
| One project's open questions / decisions | Project memory (`knowledge/projects/<project>.md`) | Handoff memory (card-scoped, dies with the card) |
| Current task goal and context | Handoff memory (payload) | Agent memory (capped, frozen at start — and disabled on lanes) |
| Stable facts about the environment | Co-PI `MEMORY.md` | Working memory (not persistent) |
| The PI's preferences and style | Co-PI `USER.md` | `MEMORY.md` (keep identity vs preference separate) |
| Cross-session retrieval | Session history | Agent memory (too small for bulk recall) |
| Audit trail of all decisions | Audit memory (`system/logs/audit.jsonl`) | Agent memory (wrong granularity) |
| Durable synthesized knowledge | Checked Concepts under `knowledge/` | Any of the above |

`SOUL.md` is **not** memory — it is the profile's identity prompt, stable across sessions by design.

---

## Audit memory

The audit trail (`system/logs/audit.jsonl`) records every policy decision with its before/after hash pair. Its field schema, the eight guarded actions, the `decision` enum, and the per-write hash-pairing mechanism are owned by [Policy audit log](policy-audit-log.md).

---

## Related

- The writer of the audit log: [Policy MCP](policy-mcp.md)
- The capability allowlist that disables specialist memory: [Profile capabilities](profile-capabilities.md)
- The handoff payload schema: [Kanban board reference](kanban-board.md)
