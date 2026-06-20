---
title: Profile capabilities
parent: Reference
---

# Profile capabilities

The five Memoria profiles ([ADR-48](../adr/48-copi-and-agent-consolidation.md)): posture, board lanes, write scopes, MCP servers, and bundled skills. Every value on this page is read from the shipped sources — the profile packages under `src/.memoria/profiles`, the lane ceilings under `src/.memoria/lane-overrides`, and the per-profile tool allowlist in `src/.memoria/tool-registry.yaml`.

---

## The five profiles

One conversational agent (the Co-PI) plus four background agents, each defined by a posture rather than a tool list:

| Profile | Posture | Role | Invocation | Production default model |
| --- | --- | --- | --- | --- |
| `memoria-copi` | Reflective thinking-partner | The one agent the PI converses with (the ACP pane). Reads directly, delegates every write as a board card. Sole carrier of the memory loop. | `interactive_only` — never dispatched to the board | `claude-opus-latest` |
| `memoria-librarian` | Faithful | Finds, ingests, enriches, and draft-classifies evidence. Four processing lanes: catalog · extract · link · map. | `dispatched` | `claude-haiku-latest` |
| `memoria-writer` | Generative | Drafts and synthesizes into project scratch; review-gated. | `dispatched` | `claude-sonnet-latest` |
| `memoria-peer-reviewer` | Adversarial (flag, don't fix) | The independent verify gate: claim, citation, duplicate, and retraction checks. Writes only Inbox cards. | `dispatched` | `claude-opus-latest` |
| `memoria-engineer` | Coordinating | The code lane: scaffolds handoffs to an external coding agent and owns the commit/revert gate in `projects/*/code/`. | `dispatched` | `claude-haiku-latest` |

These are the `MEMORIA_ENV=prod` defaults rendered by the installer. Linux/WSL test installs may render all five profiles to a local OpenAI-compatible Ollama endpoint with `MEMORIA_ENV=test`; see [Installer environment overlays](installer.md#environment-overlays).

---

## Board lanes

A lane _is_ an `assignee` value on the Hermes board. The task-lane → profile map is enforced by the tasks MCP (`src/.memoria/mcp/tasks_mcp.py`):

| Task lane | Profile |
| --- | --- |
| `catalog` · `extract` · `link` · `map` | `memoria-librarian` |
| `draft` | `memoria-writer` |
| `verify` | `memoria-peer-reviewer` |
| `code` | `memoria-engineer` |

The Co-PI has **no lane** — it converses in the pane and delegates via `delegate_route_task`, which validates every handoff against the receiving lane's ceiling. See [Kanban board reference](kanban-board.md).

---

## Write scopes (lane ceilings)

From `routing.write_scope` and the `policy` block in each lane-override. The policy MCP enforces these per path; a card's `allowed_paths` may narrow but never widen them (lane = ceiling, payload = floor).

| Profile | Write scope | Explicitly denied |
| --- | --- | --- |
| `memoria-copi` | `[]` — **no write paths at all** (`deny.write: "**"`) | everything |
| `memoria-librarian` | `inbox/` · `catalog/` · `notes/fleeting/` · `notes/sources/` | `notes/claims/**` · `notes/hubs/**` · `notes/indexes/**` · `projects/**` · `system/**` |
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
| `obsidian` (Local REST API native MCP, verified loopback HTTPS) | ✓ (reads only, by lane) | ✓ | ✓ | ✓ | ✓ |
| `ingest` (the deterministic pipeline) | ✓ (read/compute) | ✓ | — | — | — |
| `cluster` (typed graph + topics, read-only) | ✓ | ✓ | — | — | — |
| `tasks` (`delegate_route_task`) | ✓ | — | — | — | — |
| `patterns` (the pattern runner) | ✓ | ✓ | — | — | — |
| `paper_search` (scholarly discovery, 20+ databases) | ✓ | ✓ | — | — | — |
| `pyzotero` (read-only Zotero 7 local API) | — | ✓ | — | ✓ | — |
| `qmd` (local hybrid search over the vault corpus, read-only) | ✓ | ✓ | ✓ | ✓ | — |

The `web` toolset is disabled on every lane — all external lookups go through MCP servers (gated, audited, deterministic). The write gate itself is the `memoria-policy-gate` Hermes plugin, enabled per profile and fail-closed; see [Policy MCP](policy-mcp.md).

---

## Bundled skills

**25 skills** ship inside the vault profiles, under `src/.memoria/profiles/<profile>/skills/`. Lane skills use a single kebab-case name, `<task>-<verb>-<object>` (e.g. `catalog-enrich-record`, in `skills/catalog-enrich-record/`) — the same spelling in prose, on disk, and at load. Co-PI conversational skills that are not lane work use bare names such as `route-task` and `explain-system`.

| Profile | Bundled-skill count |
| --- | --- |
| `memoria-copi` | 5 |
| `memoria-librarian` | 12 |
| `memoria-writer` | 4 |
| `memoria-peer-reviewer` | 4 |
| `memoria-engineer` | 0 — the code lane scaffolds an external-agent handoff |

For the full per-skill map (names and lanes) see the [Hermes CLI](hermes-cli.md) reference.

---

## Capability allowlist

`src/.memoria/tool-registry.yaml` is the authoritative per-profile **tool** allowlist (default-deny). Two layers, deliberately separate: the registry governs _which tools_ a profile may invoke; the lane-override governs _which paths_ those tools may write. Notably:

- `memoria-copi` is the only profile granted `memory` (the self-improving loop — see [Memory substrates](memory.md)) and `tasks`; it is the only one **withheld** `vault_write`.
- **No** profile is granted a direct-world toolset (`terminal`, `file`, `code_execution`, `browser`, `web`, `computer_use`) — every agent reaches the vault, operations, and APIs only through MCP ([ADR-21](../adr/21-l3-autonomy-ceiling.md) retired the v0.1.0-alpha.1 Coder-lane `terminal`+`file` exception, so its successor the Engineer is MCP-only too; enforced by `test_no_profile_has_direct_world_access`).

---

## Retired profiles (historical)

The previous seven-profile fleet consolidated into the five above ([ADR-48](../adr/48-copi-and-agent-consolidation.md)). These names are historical; the installer deploys only the five current profiles.

| Retired profile | Where its job went |
| --- | --- |
| `memoria-socratic` | The Co-PI (`memoria-copi`) — the conversational front, now hard read-only |
| `memoria-mapper` | The Librarian's `map` lane + the cluster MCP |
| `memoria-verifier` | `memoria-peer-reviewer` (judgment checks) + the sweeps operation (deterministic checks) |
| `memoria-coder` | `memoria-engineer` |
| `memoria-linter` | The Linter **operation** — pre-commit hook + daily cron, not an agent (see [Linter: detectors and auto-fix](linter.md)) |

---

## Related

- The write-gate decisions and lane-override shape: [Policy MCP](policy-mcp.md)
- The board the lanes pull from: [Kanban board reference](kanban-board.md)
- The CLI surface per profile: [Hermes CLI](hermes-cli.md)
- Where profiles live on disk: [On-disk layout](on-disk-layout.md)
