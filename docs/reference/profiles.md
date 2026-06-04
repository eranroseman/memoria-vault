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
| `skills/` | shipped | Holds Memoria-**authored** skills (Librarian: `obsidian-paper-note`; Verifier: `retraction-check`); the other five ship as `.keep`. Shared skills (K-Dense, official) live in `~/.hermes/skills/` **globally** (K-Dense via `git clone`, auto-discovered), not here. |

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
| **Linter** | Validate and report | `lint`, `report`, `schema-check`, `schema-migrate`, `health-report`, `graph-analyze`, `session-log`, `dry-run` | *(none — runs `detectors.py` via terminal)* | Level 1 (cron) |

> **Commands vs. skills.** Core commands are the profile's command surface (CLI / palette). Allowed skills are the Hermes/K-Dense skill IDs the lane-override grants (the policy gate). Only `obsidian-paper-note` and `retraction-check` are authored as skills; `qmd` is a skills.sh skill; the Linter runs the shipped `detectors.py`. Source of truth: `vault/.memoria/lane-overrides/*.yaml`.

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

## Linter: the eight structural detectors

Eight deterministic, zero-LLM checks. Full per-detector procedures live in [Structural detectors: silent-failure checks](https://github.com/eranroseman/memoria-vault/blob/main/vault/.memoria/profiles/memoria-linter/structural-detectors.md). For design rationale see [The Linter](../explanation/profiles/linter.md).

**Implementation:** three detectors are functions in `detectors.py` (pure Python stdlib); five run as live-Linter agent procedures that need runtime context the script lacks (git diff, SHA-256 audit-log pass, commit timestamps). `detectors.py` defines nine functions in total — these three structural detectors plus six housekeeping checks — so the "nine functions vs. eight structural detectors" counts measure different things and do not contradict.

| Slug | Severity | Implementation | Catches |
| --- | --- | --- | --- |
| `profile-install-drift` | LOW | agent procedure (git diff) | Deployed copy under `~/.hermes/profiles/memoria-<name>/` differs from its vault source (usually a `git pull` without re-running `scripts/install.sh --profiles-only`). |
| `vault-hash-drift` | CRITICAL | agent procedure (SHA-256 vs audit log) | File written outside the policy MCP, or tampered with — the audit-log SHA-256 chain no longer matches. |
| `skeleton-drift` | MEDIUM | agent procedure (git timestamps) | Human-facing `00-meta/` skeleton notes lag the design spec they mirror. |
| `dashboard-field-drift` | HIGH | `detectors.py` (stdlib) | A Dataview query references a field no template emits → query returns zero rows and human sees "nothing to do" when there is work. |
| `command-vocab-drift` | MEDIUM | agent procedure (SOUL.md scan) | A command named in the design isn't declared in its owner profile's SOUL.md (or vice versa). |
| `plugin-config-drift` | MEDIUM | agent procedure (git HEAD diff) | Working `.obsidian/plugins/<plugin>/data.json` differs from the version committed at git HEAD. HIGH if `agent-client.autoAllowPermissions` flips to `true`. |
| `orphan-working-files` | LOW | `detectors.py` (stdlib) | Editor backups / `.tmp.*` / `.bak` leftovers accumulated outside transient zones. |
| `extract-path-broken` | HIGH | `detectors.py` (stdlib) | A paper-note's `extract_path` points at a Marker extract file that doesn't exist. |

The defining property of all eight: **silent** — each failure looks like "nothing to do" while something is actually wrong.

---

## Linter: auto-fix classes

Every proposed fix carries a class, hard-coded by the detector. The class determines whether the fix applies automatically or requires human action; the policy MCP enforces the gate at the tool layer.

| Class | Examples | Default behavior |
| --- | --- | --- |
| `safe-and-unambiguous` | Trailing whitespace, missing `created` timestamp, missing required template field with one obvious value | **Auto-fix** (granted; delegated to Templater) |
| `authorized-targeted` | Audit-log rotation, lint-findings file truncation, dashboard `last_updated` refresh | **Auto-fix** (granted; Linter's own logs/dashboards only) |
| `schema-content` | Frontmatter field rename, value-set change, deprecated field removal | **Dry-run always** (not granted; requires `schema-migrate`) |
| `review-gated-edit` | Any write to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/` | **Deny** |

Policy gate: `policy.allow.auto_fix.classes: ["safe-and-unambiguous", "authorized-targeted"]` in `lane-overrides/linter.yaml` — the two granted classes; the other two appear under `deny.auto_fix.classes`. The `review-gated-edit` *class* is denied outright; separately, a mutating write to a review-gated *zone* (a distinct mechanism) degrades to `dry_run`.

---

## Linter: severity scale

| Severity | Meaning | Dashboard surfacing |
| --- | --- | --- |
| `LOW` | Cosmetic or eventually-fixable. Does not block. | Aggregated weekly in `weekly-review`. |
| `MEDIUM` | Real drift that hasn't yet caused breakage. | Surfaced in `weekly-review`; reviewed in the Friday ritual. |
| `HIGH` | Active or imminent breakage. | Surfaced in Daily Health and `drift-watch`; pushed to Telegram. |
| `CRITICAL` | System integrity at risk. Blocks dispatch until acknowledged. | Always pushed to Telegram. |

**Verdict band rollup:** `PASS` if only LOW/INFO findings (or none). `REVIEW` if any HIGH or MEDIUM and no CRITICAL. `FAIL` only if any CRITICAL. A HIGH-only run is `REVIEW`, never `FAIL`.

---

## Related

- Conceptual grouping and rationale: [Profiles](../explanation/profiles/README.md)
- Linter detectors, auto-fix classes, and severity scale: [Linter: detectors and auto-fix](linter.md)
