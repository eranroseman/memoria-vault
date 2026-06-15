---
title: "Linter: detectors and auto-fix"
parent: Reference
---

# Linter: detectors and auto-fix

The Linter is an **engine, not an agent** ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)): deterministic, zero-LLM Python under `src/.memoria/operations/integrity/linter`. Its contract is **gates at commit, monitors between** — the pre-commit hook blocks schema-invalid notes from being committed, and the daily cron reports everything else. Scope: detection only. Live in-app edits are caught by the next sweep, and every detector is report-only — findings surface for the PI to act on; nothing is auto-moved or auto-archived.

---

## The detectors

`src/.memoria/operations/integrity/linter/detectors.py` — self-contained (vault tree only), report-only. Constants are **schema-driven**: when `.memoria/schemas/` + PyYAML are available, the type → home map and the legal root folders are derived from `folders.yaml`/`types/*.yaml`; the hardcoded fallbacks keep the engine running without dependencies.

| Detector | Severity | Catches |
| --- | --- | --- |
| `schema-check` | MEDIUM | A typed note failing its schema in `.memoria/schemas/types/` (missing `type`, unknown type, bad field kind/enum). |
| `frontmatter-link` | MEDIUM | A frontmatter wikilink that resolves to no note — every link in the `links:` map and the `entity` field must resolve ([ADR-52](../adr/52-links-vs-relationships.md)). Citekeys in `sources` are bibliographic, checked by the sweeps instead. |
| `broken-wikilink` | MEDIUM | A body wikilink resolving to no note (scaffolding under `system/templates/`, `system/dashboards/`, and `system/patterns/` is skipped). |
| `misplaced-note` | MEDIUM / LOW | A typed note outside its `folders.yaml` home, or a stray vault-root folder outside `catalog · notes · projects · inbox · system`. Skips work-in-flight zones (`inbox/`, `system/logs/`, `system/board/`). |
| `audit-unpaired-writes` | MEDIUM | A mutating allow in `system/logs/audit.jsonl` with no paired `write_complete` record after an hour — the per-write hash pair is incomplete and the write's after-state can no longer be pinned. |
| `vault-hash-drift` | CRITICAL | A path whose latest `write_complete` `after_hash` in `system/logs/audit.jsonl` no longer matches the on-disk SHA-256 — an out-of-band change ([ADR-25](../adr/25-session-logging-two-logs.md)). A legitimate human edit in Obsidian surfaces here too, by design: the finding means the audit trail no longer pins that file's state. A completed delete records the empty-bytes hash, so a deleted-and-still-absent file matches and stays silent. |
| `skeleton-drift` | MEDIUM | A directory from the installer skeleton (the `skeleton` list in `.memoria/schemas/folders.yaml`) missing from the vault — re-run the idempotent installer or create it ([ADR-67](../adr/67-drift-procedures-keep-or-retire.md)). Checked only in installed vaults (golden manifest present); the repo's `src/` ships no empty dirs. |
| `hub-threshold` | LOW | A topic with ≥ 15 notes (papers' `research_area` + claims' `topics`, case-insensitive) and no covering `hub` note — consider creating one ([ADR-19](../adr/19-moc-threshold-alert.md) Tier 1; report-only, never auto-created). |
| `audit-log-size` | LOW | `system/logs/audit.jsonl` over the 50 MB advisory threshold. The log is append-only forever — never rotated ([ADR-25](../adr/25-session-logging-two-logs.md)) — so growth is surfaced here instead of staying silent. |
| `dashboard-field-drift` | HIGH | A dashboard Dataview query referencing a frontmatter field no template declares. |
| `fama-exposure` | HIGH | A downstream note wikilinking a **superseded** claim (`lifecycle: archived` or `superseded_by` set) — reuse of obsolete memory. |
| `extract-path-broken` | HIGH | A paper note whose `extract_path` does not resolve. |
| `graph-analyze` | LOW | Orphan synthesis notes (claims/hubs with zero inlinks). |
| `orphan-working-files` | LOW | Leftover working files (`*.tmp.*`, `*.bak`, `*.orig`, …) outside transient zones. |
| `stale-fleeting` | LOW | Fleeting notes older than 7 days — promote or discard. |
| `stale-answer-drafts` | LOW | Unreviewed answer drafts older than 90 days (folder retired in v0.1.0-alpha.2; the check remains for migrated vaults). |

CLI entry point:

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault <vault> [--json] [--gate dashboard-field-drift]
```

`--gate DETECTORS` makes only the named detectors blocking (exit 1); everything else stays advisory. The verdict rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM/HIGH) / **FAIL** (any CRITICAL).

---

## The pre-commit gate

The commit gate ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)): the installer wires `src/.memoria/operations/integrity/linter/pre-commit` into the deployed vault's `.git/hooks/pre-commit`. On every commit it passes the staged `.md` paths to `src/.memoria/operations/integrity/linter/precommit_check.py`, which validates each typed note against its schema via the shared loader (`src/.memoria/operations/lib/schema.py`). Any error blocks the commit (exit 1). Exempt: untyped `system/` infrastructure, vault-root nav pages, and paths outside the vault.

---

## The golden copy

`src/.memoria/operations/integrity/linter/golden_restore.py` turns the Linter into a _repairer_ ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The installer stages a canonical copy of every system file — `system/templates|dashboards|patterns|eval|scripts/` plus `home.md`, `system/vocabulary.md`, `AGENTS.md` — at `.memoria/golden/` with a SHA-256 `manifest.json`.

This is the human-facing half of template protection (#179): agents are already blocked by the lane ceilings — every shipped lane-override denies writes under `system/**` (see [Policy MCP](policy-mcp.md)) — so the golden copy exists to catch and repair an *accidental human* edit or deletion of a system file.

| Command | Effect |
| --- | --- |
| `golden_restore.py --vault V stage` | Stage/refresh the golden copy from the live system files (fresh-install fallback). |
| `golden_restore.py --vault V upgrade --source SRC [--apply]` | Three-way reconcile old golden vs new source vs live vault; with `--apply`, applies clean release changes, refreshes the golden copy, and preserves conflicts for review. |
| `golden_restore.py --vault V check` | Report drifted/missing system files vs the manifest (exit 1 if any). |
| `golden_restore.py --vault V restore [PATH …]` | **Propose-only by default** — lists what it would restore. |
| `golden_restore.py --vault V restore --apply` | Write the golden bytes back (the PI or cron runs it deliberately). |

Upgrade conflict rule: if a release changes a system file and the live copy also
differs from the old golden baseline, the live file wins for safety. The command
refreshes the golden baseline to the new release and leaves that path reported as
drifted, so the PI can compare and decide rather than losing a customization.

The manifest also covers the **Memoria-shipped Obsidian config** ([ADR-67](../adr/67-drift-procedures-keep-or-retire.md)): each shipped plugin's `data.json` plus `.obsidian/community-plugins.json`, `core-plugins.json`, and the `memoria-link-colors.css` snippet. Per-machine and runtime-generated state never enters the manifest — `agent-client/data.json` (seeded per machine), `obsidian-local-rest-api/data.json` (regenerated on first launch), and workspace/appearance state stay the user's.

---

## Per-session digests

`src/.memoria/operations/integrity/linter/session_summary.py` writes the second of [ADR-25](../adr/25-session-logging-two-logs.md)'s two logs: a **deterministic digest** of each session's audit activity (the Linter is zero-LLM — no narrative). It groups `audit.jsonl` entries by `task_id` and writes one `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` per finished session (named from the session's first timestamp; a deterministic `-2` suffix disambiguates a shared start minute): a header record (task, profiles, start/end, counts by action and decision) plus one record per touched path (actions, final decision, final `after_hash`). Idempotent — an already-digested `task_id` is never rewritten — and sessions active within the last **24 h** (`--quiet-hours`) are left for a later run so in-flight work isn't summarized early.

```bash
python3 .memoria/operations/integrity/linter/session_summary.py --vault <vault> [--quiet-hours H]
```

---

## The daily cron

The installer wires `memoria-lint` (`hermes cron create '0 6 * * *' --script memoria-lint.sh --no-agent`), whose wrapper runs the detectors, `golden_restore.py check`, and the per-session digests over the vault. Findings surface in the drift dashboards (drift-watch, loose-ends) — see [Dashboards](dashboards.md).

---

## Auto-fix classes

Auto-fix is class-gated at the policy layer — the four classes and their dispositions are owned by [Policy MCP](policy-mcp.md#auto-fix-policy). The shipped v0.1.0-alpha.2 engine is report-only — the gate exists for any future fixer, including `golden_restore.py restore --apply`, which is the one shipped repair path.

---

## Related

- The schemas the detectors validate against: [Frontmatter fields](frontmatter.md)
- The class gate enforcing auto-fix policy: [Policy MCP](policy-mcp.md)
- Where the findings surface: [Dashboards](dashboards.md)
- The crons the installer wires: [Installer (bootstrap)](installer.md)
