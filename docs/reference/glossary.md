---
title: Glossary
parent: Reference
---

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses. Retired terms are listed at the end.

---

## System

**ACP** (Agent Client Protocol) — the editor-level protocol that exposes Hermes profiles to editor chat panes. The co-PI's desk pane in Obsidian is an ACP pane. Distinct from the Obsidian Local REST API (which gives Hermes vault-level read/write access).

**Co-PI** — the one conversational agent (`memoria-copi`, [ADR-48](../adr/48-copi-and-agent-consolidation.md)): a reflective thinking-partner, system explainer, and delegation front. Hard read-only across the vault (empty write scope); every write it wants goes out as a board card; the sole carrier of the Hermes memory loop.

**Engine** — deterministic, no-LLM (or LLM-free-by-default) code that runs on cron/CI or behind an MCP facade, never as a board lane: the five engines are **ingest**, **search**, **clustering**, **sweeps**, and the **Linter** ([ADR-46](../adr/46-seven-layer-architecture.md)). Engines compute and propose; agents judge; the PI decides.

**Hermes** — the Nous Research agent runtime Memoria runs on: Kanban, profile management, MCP server connections, skills, cron, and the gateway process.

**Memoria** — the whole system: the vault, the co-PI + four background agents, the five engines, the policy gate, the board, and the tooling layer (`.memoria/`).

**PI** — the human principal investigator who owns and runs the vault. Makes every approval, triage, and promotion decision. Single-user by design. (Older pages say "the human".)

**Profile** — a Hermes role with bounded permissions, skills, and tools. Memoria defines five: co-PI, Librarian, Writer, Peer-reviewer, Engineer. See [Profile capabilities](profiles.md).

**Seven-layer architecture** — PI · Interface · co-PI · Tasks · MCP · Engines · Vault ([ADR-46](../adr/46-seven-layer-architecture.md)): conversation at the top, deterministic code at the bottom, the board and the gate in between.

**Vault** — the Obsidian folder tree where durable knowledge lives, organized into five type-first categories: `catalog`, `notes`, `projects`, `inbox`, `system` ([ADR-47](../adr/47-type-first-category-folders.md)).

---

## Board and delegation

**Card** — a task on the Hermes Kanban board. Carries `status`, `assignee`, retry count, and a handoff summary. Lives in `kanban.db`, projected into `system/board/`.

**Ceiling** — a lane's `routing.write_scope` in its lane-override: the outer bound on where its writes may land. A card's `allowed_paths` may _narrow_ but never _widen_ it (lane = ceiling, payload = floor); the tasks MCP refuses widening delegations and the policy MCP re-checks per write.

**Dispatcher** — the Hermes component that polls the board every 60 seconds and claims `ready` cards for matching-lane profiles. Makes no quality or approval decisions.

**Handoff payload** — the self-contained block that provisions the next worker: `goal`, `context`, `allowed_paths`, `expected_outputs`, `review_checks`.

**Lane** — a background agent's execution path on the board; a lane _is_ an `assignee` value. Four lanes: Librarian, Writer, Peer-reviewer, Engineer. The co-PI has no lane; engines run off the board.

**Worklist** — the batch surface for high-cardinality decisions ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)): instead of one card per item, like decisions queue into one batch the PI can sweep (the two decision kinds being approval gates and work prompts).

---

## Notes and lifecycle

**Golden copy** — the canonical, hash-manifested copy of every system file at `.memoria/golden/`, staged by the installer ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The Linter checks drift against it and can restore from it (propose-only by default).

**Honesty card** — an Inbox proposal (`candidate` / `gap`) carrying the honesty body: `argument_for`, `argument_against`, `what_tipped_it`, `certainty` — and **never a verdict** ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). Verification cards (`flag` / `alert`) are the complement: they lead with the `finding` and carry `agent_recommendation`.

**Hub** — a structure note in `notes/hubs/` aggregating a topic's members and links; the renamed MOC ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)). Review-gated.

**Lifecycle vs maturity** — two different axes, never interchangeable ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)). `lifecycle` is the one universal chain (`proposed → provisional → current → retracted → archived`; each type uses a subset) — the PI-facing state of any item. `maturity` (`seedling → budding → evergreen`) is a claim **property** describing how settled it is — never a gate.

**Links vs relationships** — the two kinds of connection ([ADR-52](../adr/52-links-vs-relationships.md)): `links:` are **authored** edges on notes (the PI's thinking — supports, contradicts, …); `relationships` are **given** edges on catalog entities (facts from the record — cited_by, authored_by, …), written by the ingest engine.

**Note type** — one of the 18 types defined in `.memoria/schemas/types/`: 6 catalog entities, 5 notes, 5 inbox cards, the pattern, and the eval task. See [Note types](note-types.md).

**Pattern** — a curated prompt-transformation stored as data in `system/patterns/` ([ADR-53](../adr/53-pattern-library.md)), typed and lifecycle-gated, executed only through the patterns MCP runner (one audited chokepoint; gated output targets degrade to dry-run).

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([ADR-56](../adr/56-extraction-uncertainty-flag.md)): when cross-source identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Lane-override file** — per-lane YAML at `.memoria/lane-overrides/<lane>.yaml` declaring `policy.allow`/`deny`/`require` and `routing` (invocation, external-API policy, write scope). Read by the policy MCP.

**Policy MCP** — the runtime write-gate: intercepts every vault action, returns `allow` / `allow_with_log` / `deny` / `dry_run`, and appends to the audit log. Enforced in-process by the fail-closed `memoria-policy-gate` plugin. See [Policy MCP](policy-mcp.md).

**Review-gated zone** — a folder where the policy MCP degrades all agent writes to `dry_run` regardless of lane policy: `notes/claims/` and `notes/hubs/`, loaded from `folders.yaml`.

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / engines | the soft verdict on a verification card — advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter engine | structural rollup over the detectors |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | the calibrated confidence on an honesty card |

**Trust score** — a 0–100 per-lane operational health aggregate on the fleet-health dashboard (deny rate, retry rate, success rate, drift incidents, secret-access attempts, accept/reject ratios). Bands: 90+ healthy · 70–89 watch · < 70 act.

---

## Retired terms (v0.1.0 → v0.1.1)

| Retired | Replaced by |
| --- | --- |
| **Socratic, Mapper, Verifier, Coder, Linter** (as profiles) | The co-PI (Socratic), the Librarian's map lane (Mapper), the Peer-reviewer + sweeps engine (Verifier), the Engineer (Coder), and the Linter **engine** (no longer an agent). |
| **Reference note** (`reference-note`, `30-synthesis/02-reference/`) | Dropped ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)) — it double-encoded maturity; an `evergreen` claim is the settled unit. |
| **MOC** (`moc`, `30-synthesis/03-moc/`) | The `hub` type in `notes/hubs/`. |
| **`99-system`** (and the numbered folders `00-` … `95-`) | The five type-first categories ([ADR-47](../adr/47-type-first-category-folders.md)); system infrastructure now lives at `system/`. |
| **"The human"** | The **PI** (and the agent fronting for them, the **co-PI**). |

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The note types referenced throughout: [Note types](note-types.md)
- Lane and profile terms: [Profile capabilities](profiles.md)
- Board and delegation terms: [Kanban board reference](kanban-board.md)
