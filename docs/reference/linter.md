---
title: "Linter: detectors and auto-fix"
parent: Reference
---

# Linter: detectors and auto-fix

The Linter is an **engine, not an agent** ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)): deterministic, zero-LLM Python under [src/.memoria/engines/linter/](../../src/.memoria/engines/linter). Its contract is **gates at commit, monitors between** — the pre-commit hook blocks schema-invalid notes from being committed, and the daily cron reports everything else. Scope: detection only. Live in-app edits are caught by the next sweep, and every detector is report-only — findings surface for the PI to act on; nothing is auto-moved or auto-archived.

---

## The detectors

[src/.memoria/engines/linter/detectors.py](../../src/.memoria/engines/linter/detectors.py) — self-contained (vault tree only), report-only. Constants are **schema-driven**: when `.memoria/schemas/` + PyYAML are available, the type → home map and the legal root folders are derived from `folders.yaml`/`types/*.yaml`; the hardcoded fallbacks keep the engine running without dependencies.

| Detector | Severity | Catches |
| --- | --- | --- |
| `schema-check` | MEDIUM | A typed note failing its schema in `.memoria/schemas/types/` (missing `type`, unknown type, bad field kind/enum). |
| `frontmatter-link` | MEDIUM | A frontmatter wikilink that resolves to no note — every link in the `links:` map and the `entity` field must resolve ([ADR-52](../adr/52-links-vs-relationships.md)). Citekeys in `sources` are bibliographic, checked by the sweeps instead. |
| `broken-wikilink` | MEDIUM | A body wikilink resolving to no note (scaffolding under `system/templates/`, `system/dashboards/`, and `system/patterns/` is skipped). |
| `misplaced-note` | MEDIUM / LOW | A typed note outside its `folders.yaml` home, or a stray vault-root folder outside `catalog · notes · projects · inbox · system`. Skips work-in-flight zones (`inbox/`, `system/logs/`, `system/board/`). |
| `audit-unpaired-writes` | MEDIUM | A mutating allow in `system/logs/audit.jsonl` with no paired `write_complete` record after an hour — the per-write hash pair is incomplete and the write's after-state can no longer be pinned. |
| `dashboard-field-drift` | HIGH | A dashboard Dataview query referencing a frontmatter field no template declares. |
| `fama-exposure` | HIGH | A downstream note wikilinking a **superseded** claim (`lifecycle: archived` or `superseded_by` set) — reuse of obsolete memory. |
| `extract-path-broken` | HIGH | A paper note whose `extract_path` does not resolve. |
| `graph-analyze` | LOW | Orphan synthesis notes (claims/hubs with zero inlinks). |
| `orphan-working-files` | LOW | Leftover working files (`*.tmp.*`, `*.bak`, `*.orig`, …) outside transient zones. |
| `stale-fleeting` | LOW | Fleeting notes older than 7 days — promote or discard. |
| `stale-answer-drafts` | LOW | Unreviewed answer drafts older than 90 days (folder retired in v0.1.0-alpha.2; the check remains for migrated vaults). |

CLI entry point:

```bash
python3 .memoria/engines/linter/detectors.py --vault <vault> [--json] [--gate dashboard-field-drift]
```

`--gate DETECTORS` makes only the named detectors blocking (exit 1); everything else stays advisory. The verdict rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM/HIGH) / **FAIL** (any CRITICAL).

---

## The pre-commit gate

The commit gate ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md) D50): the installer wires [src/.memoria/engines/linter/pre-commit](../../src/.memoria/engines/linter/pre-commit) into the deployed vault's `.git/hooks/pre-commit`. On every commit it passes the staged `.md` paths to [src/.memoria/engines/linter/precommit_check.py](../../src/.memoria/engines/linter/precommit_check.py), which validates each typed note against its schema via the shared loader ([src/.memoria/engines/lib/schema.py](../../src/.memoria/engines/lib/schema.py)). Any error blocks the commit (exit 1). Exempt: untyped `system/` infrastructure, vault-root nav pages, and paths outside the vault.

---

## The golden copy

[src/.memoria/engines/linter/golden.py](../../src/.memoria/engines/linter/golden.py) turns the Linter into a _repairer_ ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The installer stages a canonical copy of every system file — `system/templates|dashboards|patterns|scripts/` plus `home.md`, `system/vocabulary.md`, `AGENTS.md` — at `.memoria/golden/` with a SHA-256 `manifest.json`.

| Command | Effect |
| --- | --- |
| `golden.py --vault V stage` | Stage/refresh the golden copy from the live system files (installer runs this). |
| `golden.py --vault V check` | Report drifted/missing system files vs the manifest (exit 1 if any). |
| `golden.py --vault V restore [PATH …]` | **Propose-only by default** — lists what it would restore. |
| `golden.py --vault V restore --apply` | Write the golden bytes back (the PI or cron runs it deliberately). |

---

## The daily cron

The installer wires `memoria-lint` (`hermes cron create '0 6 * * *' --script memoria-lint.sh --no-agent`), whose wrapper runs the detectors and `golden.py check` over the vault. Findings surface in the drift dashboards (drift-watch, loose-ends) — see [Dashboards](dashboards.md).

---

## Auto-fix classes

Auto-fix is class-gated at the policy layer — the four classes and their dispositions are owned by [Policy MCP](policy-mcp.md#auto-fix-policy). The shipped v0.1.0-alpha.2 engine is report-only — the gate exists for any future fixer, including `golden.py restore --apply`, which is the one shipped repair path.

---

## Related

- The schemas the detectors validate against: [Frontmatter fields](frontmatter.md)
- The class gate enforcing auto-fix policy: [Policy MCP](policy-mcp.md)
- Where the findings surface: [Dashboards](dashboards.md)
- The crons the installer wires: [Installer (bootstrap)](installer.md)
