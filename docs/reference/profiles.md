---
title: Profile capabilities
parent: Reference
---

# Profile capabilities

Lane identifiers, capability table, invocation levels, and folder permission matrix for the seven Memoria profiles. For the profile model and design rationale see [explanation/profiles/](../explanation/profiles/).

---

## Lane identifiers

One token governs routing. The Kanban dispatcher matches `task.assignee` to this string. The lane id appears in: card `assignee`, `hermes kanban create --assignee`, cron `assignee:`, skill-note `lane:`.

| Profile (prose) | Assignee = lane id | Lane-override file |
| --- | --- | --- |
| Librarian | `memoria-librarian` | `.memoria/lane-overrides/librarian.yaml` |
| Mapper | `memoria-mapper` | `.memoria/lane-overrides/mapper.yaml` |
| Socratic | `memoria-socratic` | `.memoria/lane-overrides/socratic.yaml` |
| Writer | `memoria-writer` | `.memoria/lane-overrides/writer.yaml` |
| Verifier | `memoria-verifier` | `.memoria/lane-overrides/verifier.yaml` |
| Coder | `memoria-coder` | `.memoria/lane-overrides/coder.yaml` |
| Linter | `memoria-linter` | `.memoria/lane-overrides/linter.yaml` |

**Three forms, one token.** Prose uses the short name ("the Librarian lane"). Config, overrides, board, and cron use `memoria-<name>`. The override file is keyed by its `profile:` field, not the filename. Source of truth: `vault/.memoria/lane-overrides/*.yaml`.

---

## Profile distribution packages

Each profile distribution package lives at `.memoria/profiles/memoria-<name>/`:

| File | Status | Notes |
| --- | --- | --- |
| `SOUL.md` | shipped | Profile prompt. The agent's identity and rules. |
| `config.yaml` | shipped | Model routing (`provider: kilocode` + per-tier model), the `mcp_servers` block (`policy` + `obsidian`; `{{VAULT_PATH}}` substitution target), and a `plugins` block enabling the `memoria-policy-gate` write gate. Required by the profile-install step. |
| `distribution.yaml` | shipped | Install metadata + `env_requires`. Required by the profile-install step. |
| `.env.EXAMPLE` | shipped | **Generated** by `hermes profile install` from `distribution.yaml` `env_requires`, then copied to `.env`. |
| `cron/` | shipped | Placeholder (`.keep`). Linter and Mapper ship `cron/scheduled.yaml` with content. |
| `skills/` | shipped | Holds Memoria-**authored** skills (Librarian: `obsidian-paper-note`; Verifier: `retraction-check`; Linter: `structural-detectors`); the other four ship as `.keep`. Shared skills (K-Dense, official) live in `~/.hermes/skills/` **globally** (K-Dense via `git clone`, auto-discovered), not here. |

---

## Capability table

| Profile | Primary role | Core commands | Allowed skills | Invocation level |
| --- | --- | --- | --- | --- |
| **Librarian** | Find and ingest evidence | `find`, `ingest`, `enrich`, `classify`, `query`, `export prior-labels` | `paper-lookup`, `arxiv`, `pyzotero`, `citation-management`, `literature-review`, `ocr-and-documents`, `obsidian`, `qmd`, `obsidian-paper-note`, `rest-passthrough` | Level 2 (Kanban) |
| **Mapper** | Map the corpus | `scope-project`, `gap-report`, `cluster-map` | `obsidian`, `qmd`, `scikit-learn`, `umap-learn` | Level 1 (cron) + Level 2 (Kanban) |
| **Socratic** | Question without producing | `socratic-processing`, `lens-reading` | `obsidian` (read-only) | Level 3 (interactive only) |
| **Writer** | Draft and synthesize | `draft`, `query`, `lint`, `promote` | `llm-wiki`, `obsidian-markdown`, `scientific-writing`, `obsidian`, `qmd` | Level 2 (Kanban) with review gate |
| **Verifier** | Verify claims, citations, duplicates | `cite-check`, `claim-trace`, `similarity-check`, `find-duplicates`, `retraction-check` | `qmd`, `pyzotero`, `obsidian`, `retraction-check` | Level 2 (Kanban) |
| **Coder** | Code artifacts | `code`, `commit`, `revert`, `workspace`, `scaffold` | `obsidian`, `codex`, `claude-code`, `github-repo-management` | Level 2 (external dispatch) |
| **Linter** | Validate and report | `lint`, `report`, `schema-check`, `schema-migrate`, `health-report`, `graph-analyze`, `session-log`, `dry-run` | `structural-detectors` | Level 1 (cron) |

> **Commands vs. skills.** Core commands are the profile's command surface (CLI / palette). Allowed skills are the Hermes/K-Dense skill IDs the lane-override grants (the policy gate). `obsidian-paper-note`, `retraction-check`, and the Linter's `structural-detectors` are authored as skills; `qmd` is a skills.sh skill. The `structural-detectors` skill wraps the shipped `detectors.py` engine. Source of truth: `vault/.memoria/lane-overrides/*.yaml`.

### Invocation levels

| Level | Cadence | Description |
| --- | --- | --- |
| Level 1 | Background / cron | Runs unattended on a schedule. Produces reports only; never acts on canonical content. |
| Level 2 | Kanban-pulled | Picks up cards from its lane queue. Produces output to review-gated paths. |
| Level 2 (review gate) | Kanban-pulled | Produces drafts that require explicit human approval before becoming canonical. |
| Level 2 (external dispatch) | Kanban-pulled | Hands off to an external coding agent (Claude Code, Aider, Codex) via handoff payloads. |
| Level 3 | Interactive | Invoked synchronously by the human (ACP pane, command palette). No queue. |

---

## Denied capabilities

| Profile | Hard denials |
| --- | --- |
| **Librarian** | Review-gated publish, destructive shell, unrestricted HTTP |
| **Mapper** | All write tools outside its scratch paths, external APIs, drafting |
| **Socratic** | All write tools (`policy.allow.write: []`); all external APIs; queue dispatch |
| **Writer** | `rest-passthrough`; external-API skills; publish without review gate |
| **Verifier** | All write tools except verification reports and gap candidate-notes (`source: gap`); drafting |
| **Coder** | Review-gated-zone edits; prose ownership |
| **Linter** | Review-gated-zone edits; schema-content auto-fixes; work spawning |

---

## Folder permission matrix

`W` = write · `R` = read · `—` = no access. The grid shows the coarse read/write stance; the **per-profile write detail** below specifies the exact subfolder, note types, and command/skill responsible.

Read access is universal — agents ground on the whole vault to do narrow work well. The trust boundary is the write gate. The one read withheld from all profiles is secrets: `.env` and `auth.json` are outside the vault. See [Why specialist profiles, not a generalist agent](../explanation/rationale/why-specialist-profiles.md) for the design rationale.

| Profile | `00-meta` | `10-inbox` | `20-sources` | `30-synthesis/01-claims` | `30-synthesis/02-reference` | `30-synthesis/03-moc` | `40-workbench` | `50-deliverables` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Librarian** | R | W (`01-fleeting`, `03-candidates`) | W (create, enrich) | R | R | R | R | R |
| **Mapper** | R | R | R | R | R | R | W (`*/01-map/` only) | R |
| **Socratic** | R | R | R | R | R | R | R | R |
| **Writer** | R | W (`02-answers/`) | R | R | W drafts (review-gated) | R (suggest only) | W (drafts, framing, canvas) | R (export = dry-run) |
| **Verifier** | R | W (`03-candidates/` only) | R | R | R | R | W (`*/05-verification/*`) | R |
| **Coder** | R | R | R | R | R | R | W (`*/06-code/`) | R (export = dry-run) |
| **Linter** | W (`99-system/logs/` only) | R | R | R | R | R | R | R |

### Per-profile write detail — where, what, why

| Profile | Where (exact subfolder) | What (note types) | Why (command / skill) |
| --- | --- | --- | --- |
| **Librarian** | `10-inbox/03-candidates/`, `20-sources/01-papers/`, `20-sources/02-items/`, `20-sources/03-entities/` | `candidate-note`, `paper-note`, `item-note`, entity notes | `find` (candidates), `ingest` / `obsidian-paper-note` skill (sources), `enrich` |
| **Mapper** | `40-workbench/*/01-map/` only | `corpus-map.md`, `gap-report.md` | `scope-project`, `gap-report`, `cluster-map` |
| **Socratic** | *(none — `policy.allow.write: []`)* | — | write-denied by design |
| **Writer** | `10-inbox/02-answers/`; `40-workbench/*/{02-framing,03-canvas,04-drafts}/`; `30-synthesis/02-reference/**` and `50-deliverables/**` (both review-gated → `dry_run`) | `answer-note`, framing/canvas/`draft`; proposed `reference-note`, `deliverable` | `draft`, `query`, `promote` (handoff); `llm-wiki` / `obsidian-markdown` / `scientific-writing` skills |
| **Verifier** | `10-inbox/03-candidates/` (gap cards), `40-workbench/*/05-verification/` | gap candidate notes, `[!verification]` reports | `cite-check`, `similarity-check`, `find-duplicates` |
| **Coder** | `40-workbench/*/06-code/` | `code-note`, code artifacts | `code`, `scaffold`, `commit`, `revert` |
| **Linter** | `99-system/logs/` only | audit/session logs, rotation archive | `session-log`, log rotation (auto-fix class `authorized-targeted`) |

**Canonical synthesis (`30-synthesis/`) and schema governance (`00-meta/`) remain human-owned.** The Linter's only write zone is `99-system/logs/`. Project scratch (`40-workbench/`) and the inbox (`10-inbox/`) are the multi-profile write zones — each profile writes only to its own named subfolder. Writes to review-gated paths (`30-synthesis/02-reference/`, `50-deliverables/`) are allowed in the lane-override but the policy MCP degrades them to `dry_run` until a human approves. Source of truth for every path: `vault/.memoria/lane-overrides/*.yaml`.

---

## Linter: detectors, auto-fix, severity

The Linter's eight structural detectors, the four auto-fix classes, the severity scale, and the verdict-band rollup are documented once in [Linter: detectors and auto-fix](linter.md) — the canonical reference. For design rationale see [The Linter](../explanation/profiles/linter.md).

---

## Related

- Conceptual grouping and rationale: [Profiles](../explanation/profiles/README.md)
- Linter detectors, auto-fix classes, and severity scale: [Linter: detectors and auto-fix](linter.md)
