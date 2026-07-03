---
title: "Linter: detectors and auto-fix"
parent: Agents and control
grand_parent: Reference
---

# Linter: detectors and auto-fix

The Linter is an **operation, not an agent** ([ADR-69](../adr/69-operations-layer-naming.md));
its schema contract comes from [ADR-119](../adr/119-schema-driven-document-creation.md).

| Question | Answer |
| --- | --- |
| What is it? | Deterministic, zero-LLM Python under `src/memoria_vault/runtime/subsystems/integrity/linter`. |
| What blocks? | The pre-commit hook blocks schema-invalid notes from being committed. |
| What reports? | A manual or operator-managed scheduled lint run reports everything else, including live in-app edits caught by the next sweep. |
| What never happens? | Detectors do not auto-move or auto-archive files; findings surface for the PI. |

---

## The detectors

`memoria_vault.runtime.subsystems.integrity.linter.detectors` — self-contained (vault tree only), report-only. Constants are **schema-driven**: when `.memoria/schemas/` + PyYAML are available, the type → home map and the legal root folders are derived from `folders.yaml`/`types/*.yaml`; the hardcoded fallbacks keep the operation running without dependencies.

| Detector | Severity | Catches |
| --- | --- | --- |
| `schema-check` | MEDIUM | A typed document failing its schema in `.memoria/schemas/types/` (missing `type`, unknown type, undeclared field, bad field kind/enum, bad nested `links:` shape). |
| `frontmatter-link` | MEDIUM | A frontmatter wikilink that resolves to no note — every link in the `links:` map and the `entity` field must resolve ([ADR-52](../adr/52-links-vs-relationships.md)). Citekeys in `sources` are bibliographic, checked by the sweeps instead. |
| `broken-wikilink` | MEDIUM | A body wikilink resolving to no note (scaffolding under `system/templates/`, `system/dashboards/`, and `system/patterns/` is skipped). |
| `misplaced-note` | MEDIUM / LOW | A typed document outside its `folders.yaml` home, or a stray vault-root folder outside `catalog · knowledge · spaces · system`. Skips hidden implementation folders (`.githooks/`, `.git`, `.memoria`, `node_modules`) and runtime/work-in-flight zones declared in the skeleton. |
| `audit-unpaired-writes` | MEDIUM | A mutating allow in `system/logs/audit.jsonl` with no paired `write_complete` record after an hour — the per-write hash pair is incomplete and the write's after-state can no longer be pinned. |
| `vault-hash-drift` | CRITICAL | A path whose latest `write_complete` `after_hash` in `system/logs/audit.jsonl` no longer matches the on-disk SHA-256 — an out-of-band change ([ADR-25](../adr/25-session-logging-two-logs.md)). A legitimate human edit in Obsidian surfaces here too, by design: the finding means the audit trail no longer pins that file's state. A completed delete records the empty-bytes hash, so a deleted-and-still-absent file matches and stays silent. |
| `skeleton-drift` | MEDIUM | A directory from the installer skeleton (the `skeleton` list in `.memoria/schemas/folders.yaml`) missing from the vault — rerun the installer/refresh helper or create it. Checked only in installed vaults (`.git` present); the repo's `vault-template/` ships no empty dirs. |
| `hub-threshold` | LOW | A topic with >= 15 checked notes and no covering `hub` Concept — consider creating one ([ADR-19](../adr/19-moc-threshold-alert.md) Tier 1; report-only, never auto-created). |
| `audit-log-size` | LOW | `system/logs/audit.jsonl` over the 50 MB advisory threshold. The log is append-only forever — never rotated ([ADR-25](../adr/25-session-logging-two-logs.md)) — so growth is surfaced here instead of staying silent. |
| `dashboard-field-drift` | HIGH | A dashboard Dataview query referencing a frontmatter field no template declares. |
| `design-system-drift` | MEDIUM / LOW | Visual-discipline drift from `.memoria/design-system.md`: off-palette colors, font sizes outside the scale, emoji in note titles, ad-hoc/rainbow callout variants, and terminology/capitalization drift. |
| `fama-exposure` | HIGH | A downstream note wikilinking a **superseded** claim (`lifecycle: archived` or `superseded_by` set) — reuse of obsolete memory. |
| `extract-path-broken` | HIGH | A legacy `catalog/sources/**/source.md` file whose extract/content path does not resolve. Alpha.15 catalog Work rows use SQLite plus source-content blobs instead. |
| `graph-analyze` | LOW | Orphan synthesis notes (claims/hubs with zero inlinks). |
| `orphan-working-files` | LOW | Leftover working files (`*.tmp.*`, `*.bak`, `*.orig`, …) outside transient zones. |
| `stale-fleeting` | LOW | Fleeting notes older than 7 days — promote or discard. |

CLI entry point:

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault <vault> [--json] [--gate dashboard-field-drift,design-system-drift]
python3 -m memoria_vault.runtime.subsystems.integrity.linter.hub_handoff --vault <vault> [--threshold 15] [--json]
```

`--gate DETECTORS` makes only the named detectors blocking (exit 1); everything else stays advisory. The verdict rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM/HIGH) / **FAIL** (any CRITICAL).

---

## The pre-commit hook

The pre-commit hook ([ADR-119](../adr/119-schema-driven-document-creation.md)): the installer wires `vault-template/.githooks/pre-commit` into the deployed vault's `.git/hooks/pre-commit`. On every commit it passes the staged `.md` paths to `memoria_vault.runtime.subsystems.integrity.linter.precommit_check`, which validates each typed document against its schema via the shared loader (`memoria_vault.runtime.subsystems.lib.schema`). Any error blocks the commit (exit 1). Exempt: untyped `system/` infrastructure, vault-root nav pages, and paths outside the vault.

---

## Per-request digests

`memoria_vault.runtime.subsystems.integrity.linter.session_summary` writes the second log from [ADR-25](../adr/25-session-logging-two-logs.md): a deterministic audit digest, not an LLM summary.

| Aspect | Contract |
| --- | --- |
| Input | `audit.jsonl`, grouped by `request_id`. |
| Output | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl`. |
| Records | One header plus one row per touched path. |
| Idempotency | An already-digested `request_id` is never rewritten. |
| Quiet window | Requests active within the last **24 h** (`--quiet-hours`) wait for a later run. |

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.session_summary --vault <vault> [--quiet-hours H]
```

---

## Scheduled checks

The standalone baseline can run linter checks on demand through
`memoria workspace check`. Operators may wire the same check through cron,
systemd timers, launchd, Task Scheduler, or another local scheduler. The lint
wrapper runs the detectors, the per-session digests, and the worker
`integrity-sweep` over the vault. Findings surface in Maintenance views and CLI
output; no Hermes scheduler is required.

---

## Auto-fix classes

Auto-fix is class-gated at the policy layer — the four classes and their dispositions are owned by [Policy auto-fix](policy-auto-fix.md). The Linter operation is report-only; any future fixer must go through that gate.

---

## Related

- The schemas the detectors validate against: [Frontmatter fields](frontmatter.md)
- The class gate enforcing auto-fix policy: [Policy auto-fix](policy-auto-fix.md)
- Where the findings surface: [Dashboards](dashboards.md)
- Scheduler wiring boundary: [Installer (bootstrap)](installer.md)
