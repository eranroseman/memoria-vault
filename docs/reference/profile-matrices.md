---
topic: profiles
---

# Profile permission matrices

The lookup tables for what each Hermes profile may do: the consolidated lane-permissions view, the invocation levels (cadence), and the folder-by-profile access map. For the profile *model* — what the seven profiles are, the core design rule, profile boundaries, delegation, routing, handoff patterns, and anti-patterns — see [the profiles overview](../explanation/profiles/README.md). The machine-readable encoding the policy MCP reads is in [lane-override files](../explanation/profiles/README.md#lane-override-files).

> **Naming.** Prose refers to a profile by its short name (Librarian, Writer, …); its runtime identity is `memoria-<name>` (`memoria-librarian`, `memoria-writer`, …) — the same profile. Use the short name in prose and `memoria-*` in any config, lane-override, or policy reference.

## Lane permissions matrix

The **consolidated lane view** — what each lane may run (skills), what tools it uses, what's denied, and where it can write. It's the human-readable summary to check first when a worker behaves unexpectedly. A complementary [folder × profile view](#folder-permission-matrix) appears below; the YAML form the policy MCP actually reads is in [lane-override files](../explanation/profiles/README.md#lane-override-files).

| Profile | Primary role | Core commands | Allowed skills | Allowed tools | Denied capabilities | Write scope |
| --- | --- | --- | --- | --- | --- | --- |
| **Librarian** | Find and ingest evidence | `find`, `ingest`, `enrich`, `classify`, `query` | `paper-lookup`, `arxiv-search`, `pyzotero`, `citation-management`, `literature-review`, `obsidian-paper-note`, `rest-passthrough` | `search_web`, `fetch_url`, vault read/write | review-gated publish, destructive shell, unrestricted HTTP | `10-inbox/`, `20-sources/` |
| **Mapper** | Map the corpus | `scope-project`, `gap-report`, `cluster-map`, `comparative-brief` | `scope-project`, `gap-report`, `cluster-mapping`, `comparative-brief` | vault read | all write tools, external APIs, drafting | `40-workbench/*/01-map/corpus-map.md`, `*/01-map/gap-report.md`, `*/01-map/comparative-briefs/*`, `*/01-map/cluster-maps/*` |
| **Socratic** | Question without producing | `socratic-processing`, `lens-reading` | `socratic-processing`, `lens-reading` (parameterized: `mamykina-lens`, `veinot-equity-lens`, etc.) | vault read | **all write tools** (`policy.allow.write: []`), external APIs, drafting, queue dispatch (`routing.invocation: interactive_only`) | (none — `read_only_mode`, hard) |
| **Writer** | Draft and synthesize | `draft`, `query`, `lint`, `promote` (handoff) | `llm-wiki draft`, `note-refactor`, `scientific-writing`, `counter-outline` | `search_web`, `fetch_url`, vault read/write | `rest-passthrough`, external-API skills, publish-review-gated | `10-inbox/02-answers/`, `40-workbench/*/04-drafts/`, `40-workbench/*/03-canvas/`, `40-workbench/*/02-framing/` (via `counter-outline`) |
| **Verifier** | Verify claims, citations, duplicates | `cite-check`, `similarity-check`, `find-duplicates`, `retraction-check` | `cite-check`, `similarity-check`, `find-duplicates`, `retraction-check` | `search_web`, `fetch_url`, vault read | all write tools except verification reports and gap-candidate cards, drafting | `40-workbench/*/05-verification/*`, `10-inbox/03-candidates/` (gap-candidate cards only) |
| **Linter** | Validate, report, and log | `lint`, `schema-check`, `schema-migrate`, `health-report`, `graph-analyze`, `session-log`, `dry-run`, `report` | `schema-check`, `graph-analyze`, `health-report`, `session-log` | vault read, file indexer, Git | review-gated-zone edits, schema-content auto-fixes, work spawning | `00-meta/02-logs/` (audit and session logs only), dry-run reports |
| **Coder** | Code artifacts | `code`, `commit`, `revert`, `workspace`, `scaffold` | `scaffold-code-note`, `workspace-coordinate`, `commit-and-document` (thin Hermes-side wrappers; substantive coding work lives in the external coding agent — see [Coder ↔ external coding agent](../explanation/profiles/README.md#coder--external-coding-agent)) | Git, filesystem, repo APIs | review-gated-zone edits, prose ownership | `40-workbench/*/06-code/` |

Rules of thumb:

- **Networked skills are lane-restricted.** Only Librarian can call `rest-passthrough`. The passthrough is the escape hatch (see [architecture/capability-stack.md](architecture/capability-stack.md#rest-passthrough--the-escape-hatch)); confining it to one lane keeps external I/O auditable.
- **Socratic is write-denied; Mapper and Verifier are canonically read-only.** Socratic has `policy.allow.write: []` — no writes anywhere. Mapper and Verifier have `canonical_read_only_mode` — any `decision: allow` for `profile: memoria-mapper` or `profile: memoria-verifier` on a `write` action outside their declared scratch paths is a configuration bug — surfaced by the [audit-log dashboard](../explanation/dashboards/audit-log.md).
- **No lane writes to review-gated zones.** The four [review-gated zones](glossary.md#system-and-architecture) are policy-MCP `dry_run` for every lane. Promotion is always synchronous with human attention.

## Invocation levels (cadence)

Each profile's invocation level (its cadence) is part of its contract. *(This 1–3 scale is about **how a profile is invoked** — distinct from the system-wide **automation tier** and from Chen 2026's **L1–L5** field taxonomy; see [glossary: Automation tier](glossary.md#profile-management-and-configuration).)*

- **Level 1 (background)** — runs unattended on a cron schedule. Produces reports; never acts on canonical content. Linter is the definitive example.
- **Level 2 (Kanban-pulled)** — picks up cards from its lane queue. Produces output to review-gated paths. The bulk of Memoria's work.
- **Level 2 with review gate** — produces drafts that don't promote to canonical without explicit human approval. Writer.
- **Level 3 (interactive)** — invoked synchronously by the human (via ACP, command palette, or Telegram). No queue. Socratic.
- **Level 2 (external dispatch)** — handoffs to an external agent (Claude Code, Aider, Codex) via handoff payloads. Coder.

A profile can span two levels when it runs on more than one cadence. Librarian is **Level 1–2**: it runs background discovery on cron (Level 1) and also pulls ingest/enrich cards from its queue (Level 2).

The invocation level governs both the cadence (background / kanban-pulled / interactive) and the expected output mode (report / artifact / conversation). It does not loosen any policy MCP rule.

## Folder permission matrix

This is the operational access map. For the layered folder structure these columns refer to, see [vault/README.md](../explanation/vault/README.md).

| Profile | 00-meta | 10-inbox | 20-sources | 30-synthesis/01-claims | 30-synthesis/02-reference | 30-synthesis/03-moc | 40-workbench | 50-deliverables |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Librarian | Read | Write (discovery, candidates) | Write (create, enrich) | Read only | Read for context | Read for context | Read | Read only |
| Mapper | Read | Read only | Read only | Read only | Read only | Read only | Write (`*/01-map/corpus-map.md`, `*/01-map/gap-report.md`, `*/01-map/comparative-briefs/*`, `*/01-map/cluster-maps/*`) | Read only |
| Socratic | Read | Read only | Read only | Read only | Read only | Read only | Read only | Read only |
| Writer | Read | Write (answer drafts) | Read only | Read only | Write drafts (review-gated) | Read; suggest | Write (drafts, framing, canvas) | Read; export writes degrade to `dry_run` (human-gated) |
| Verifier | Read | Write (gap-candidate cards in `03-candidates/`) | Read only | Read only | Read only | Read only | Write (`*/05-verification/*`) | Read only |
| Coder | Read | Read only | Read only | Read only | Read for context | Read | Write (`40-workbench/*/06-code/`) | Read; export writes degrade to `dry_run` (human-gated) |
| Linter | Read; write `02-logs/` (audit, session) | Read | Read | Read | Read | Read | Read | Read |

Rule of thumb: **canonical synthesis remains human-owned** across the `30-synthesis/` review-gated zones (`01-claims/`, `02-reference/`, `03-moc/`). **Schema governance remains human-owned** in `00-meta/` except for the logs subfolder Linter writes to. Project scratch (`40-workbench/`) and the inbox (`10-inbox/`) are the zones where multiple profiles write. In project scratch each profile writes to its own named subfolder; in the inbox, Writer owns `02-answers/` while `03-candidates/` is intentionally shared by Librarian discovery and Verifier gap cards.

## Related

- [profiles/README.md](../explanation/profiles/README.md) — the profile model, core design rule, boundaries, delegation ladder, routing, handoff patterns, and anti-patterns; also the [lane-override files](../explanation/profiles/README.md#lane-override-files) that encode these matrices for the policy MCP.
