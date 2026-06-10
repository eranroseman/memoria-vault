---
title: Profile capabilities
parent: Reference
---

# Profile capabilities

The five Memoria profiles ([ADR-48](../adr/48-copi-and-agent-consolidation.md)): posture, board lanes, write scopes, MCP servers, and bundled skills. Every value on this page is read from the shipped sources — the profile packages under [src/.memoria/profiles/](../../src/.memoria/profiles), the lane ceilings under [src/.memoria/lane-overrides/](../../src/.memoria/lane-overrides), and the per-profile tool allowlist in [src/.memoria/tool-registry.yaml](../../src/.memoria/tool-registry.yaml).

---

## The five profiles

One conversational agent (the co-PI) plus four background agents, each defined by a posture rather than a tool list:

| Profile | Posture | Role | Invocation | Default model |
| --- | --- | --- | --- | --- |
| `memoria-copi` | Reflective thinking-partner | The one agent the PI converses with (the desk / ACP pane). Reads directly, delegates every write as a board card. Sole carrier of the memory loop. | `interactive_only` — never dispatched to the board | `claude-opus-latest` |
| `memoria-librarian` | Faithful | Finds, ingests, enriches, and draft-classifies evidence. Four processing lanes: catalog · extract · link · map. | `dispatched` | `claude-haiku-latest` |
| `memoria-writer` | Generative | Drafts and synthesizes into project scratch; review-gated. | `dispatched` | `claude-sonnet-latest` |
| `memoria-peer-reviewer` | Adversarial (flag, don't fix) | The independent verify gate: claim, citation, duplicate, and retraction checks. Writes only Inbox cards. | `dispatched` | `claude-opus-latest` |
| `memoria-engineer` | Coordinating | The code lane: scaffolds handoffs to an external coding agent and owns the commit/revert gate in `projects/*/code/`. | `dispatched` | `claude-haiku-latest` |

---

## Board lanes

A lane _is_ an `assignee` value on the Hermes board. The task-lane → profile map is enforced by the tasks MCP ([src/.memoria/mcp/tasks_mcp.py](../../src/.memoria/mcp/tasks_mcp.py)):

| Task lane | Profile |
| --- | --- |
| `catalog` · `extract` · `link` · `map` | `memoria-librarian` |
| `draft` | `memoria-writer` |
| `verify` | `memoria-peer-reviewer` |
| `code` | `memoria-engineer` |

The co-PI has **no lane** — it converses at the desk and delegates via `delegate_route_task`, which validates every handoff against the receiving lane's ceiling. See [Kanban board reference](kanban-board.md).

---

## Write scopes (lane ceilings)

From `routing.write_scope` and the `policy` block in each lane-override. The policy MCP enforces these per path; a card's `allowed_paths` may narrow but never widen them (lane = ceiling, payload = floor).

| Profile | Write scope | Explicitly denied |
| --- | --- | --- |
| `memoria-copi` | `[]` — **no write paths at all** (`deny.write: "**"`) | everything |
| `memoria-librarian` | `inbox/` · `catalog/` · `notes/fleeting/` · `notes/source/` | `notes/claims/**` · `notes/hubs/**` · `notes/index/**` · `projects/**` · `system/**` |
| `memoria-writer` | `projects/` | `notes/claims/**` · `notes/hubs/**` · `catalog/**` · `inbox/**` · `system/**` |
| `memoria-peer-reviewer` | `inbox/` (flag / gap cards only) | `notes/**` · `catalog/**` · `projects/**` · `system/**` |
| `memoria-engineer` | `projects/*/code/` | `notes/**` · `catalog/**` · `inbox/**` · `system/**` |

All five lanes require `audit_log`; the dispatched four also require `timeout_required`, and the Librarian and Peer-reviewer additionally require `source_tracking`. `routing.external_api_policy` is `explicit_only` everywhere except the Writer (`blocked` — it composes from the vault, never researches).

---

## MCP servers per profile

From each profile's `config.yaml` (`mcp_servers` — the only place Hermes loads servers from, per [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md)). The `policy` and `obsidian` servers are universal; the rest follow the lane's job:

| Server | copi | librarian | writer | peer-reviewer | engineer |
| --- | --- | --- | --- | --- | --- |
| `policy` (the write gate) | ✓ | ✓ | ✓ | ✓ | ✓ |
| `obsidian` (Local REST API native MCP, loopback HTTP) | ✓ (reads only, by lane) | ✓ | ✓ | ✓ | ✓ |
| `ingest` (the deterministic pipeline) | ✓ (read/compute) | ✓ | — | — | — |
| `cluster` (typed graph + topics, read-only) | ✓ | ✓ | — | — | — |
| `tasks` (`delegate_route_task`) | ✓ | — | — | — | — |
| `patterns` (the pattern runner) | ✓ | ✓ | — | — | — |
| `paper_search` (scholarly discovery, 20+ databases) | ✓ | ✓ | — | — | — |
| `pyzotero` (read-only Zotero 7 local API) | — | ✓ | — | ✓ | — |

The `web` toolset is disabled on every lane — all external lookups go through MCP servers (gated, audited, deterministic). The write gate itself is the `memoria-policy-gate` Hermes plugin, enabled per profile and fail-closed; see [Policy MCP](policy-mcp.md).

---

## Bundled skills

Skills that ship inside the vault profiles (under `src/.memoria/profiles/<profile>/skills/`):

| Profile | Skill | What it does |
| --- | --- | --- |
| `memoria-copi` | `delegate-task` | Turn a conversational request into a ceiling-validated board card via the tasks MCP. |
| `memoria-copi` | `explain-the-system` | Answer "how does Memoria work?" questions from the shipped docs and vocabulary. |
| `memoria-librarian` | `obsidian-paper-note` | The full capture → enrich → classify → write flow around the ingest engine. |
| `memoria-librarian` | `cluster-mapping` | The map lane: corpus maps and topic clusters via the cluster MCP. |
| `memoria-peer-reviewer` | `claim-checks` | Judgment verification: claim trace and citation checks, with sub-check references. |

Skill names are migrating to the `<task>:<verb>-<object>` convention — see [Hermes CLI](hermes-cli.md) for the full map with legacy names.

---

## Capability allowlist

[src/.memoria/tool-registry.yaml](../../src/.memoria/tool-registry.yaml) is the authoritative per-profile **tool** allowlist (default-deny). Two layers, deliberately separate: the registry governs _which tools_ a profile may invoke; the lane-override governs _which paths_ those tools may write. Notably:

- `memoria-copi` is the only profile granted `memory` (the self-improving loop — see [Memory substrates](memory.md)) and `tasks`; it is the only one **withheld** `vault_write`.
- `memoria-engineer` is the only profile with `terminal` + `file` (the ADR-21 Coder-lane exception, under its new name).

---

## Retired profiles (v0.1.0 → v0.1.1)

The previous seven-profile fleet consolidated into the five above ([ADR-48](../adr/48-copi-and-agent-consolidation.md)). The installer prunes stale `memoria-*` profiles from `~/.hermes/profiles/` on upgrade so an old SOUL never answers the ACP pane:

| Retired profile | Where its job went |
| --- | --- |
| `memoria-socratic` | The co-PI (`memoria-copi`) — the conversational front, now hard read-only |
| `memoria-mapper` | The Librarian's `map` lane + the cluster MCP |
| `memoria-verifier` | `memoria-peer-reviewer` (judgment checks) + the sweeps engine (deterministic checks) |
| `memoria-coder` | `memoria-engineer` |
| `memoria-linter` | The Linter **engine** — pre-commit gate + daily cron, not an agent (see [Linter: detectors and auto-fix](linter.md)) |

---

## Related

- The write-gate decisions and lane-override shape: [Policy MCP](policy-mcp.md)
- The board the lanes pull from: [Kanban board reference](kanban-board.md)
- The CLI surface per profile: [Hermes CLI](hermes-cli.md)
- Where profiles live on disk: [On-disk layout](on-disk-layout.md)
