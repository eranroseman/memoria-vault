---
title: "Linter: detectors and auto-fix"
parent: Analysis and surfaces
nav_order: 1
grand_parent: Reference
---

# Linter: detectors and auto-fix

The Linter is an **operation, not an agent** ([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md));
its schema contract comes from the YAML schemas under `.memoria/schemas/`.

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
| `frontmatter-link` | MEDIUM | A frontmatter wikilink that resolves to no note — every link in the `links:` map must resolve. Catalog Work evidence is checked by catalog and citation sweeps instead. |
| `broken-wikilink` | MEDIUM | A body wikilink resolving to no note; scaffolding under `.memoria/patterns/` is skipped. |
| `misplaced-note` | MEDIUM / LOW | A typed document outside its `folders.yaml` home, or a stray vault-root folder outside declared bundle, infrastructure, runtime, or work-in-flight roots. |
| `audit-unpaired-writes` | MEDIUM | A mutating allow in `system/logs/audit.jsonl` with no paired `write_complete` record after an hour — the per-write hash pair is incomplete and the write's after-state can no longer be pinned. |
| `vault-hash-drift` | CRITICAL | A path whose latest logged `after_hash` no longer matches the on-disk SHA-256 — an out-of-band change or unpaired edit. |
| `skeleton-drift` | MEDIUM | A directory from `.memoria/schemas/folders.yaml` `skeleton` is missing from an installed vault. |
| `hub-threshold` | LOW | A topic with >= 15 checked notes and no covering `hub` Concept — consider creating one; report-only, never auto-created. |
| `audit-log-size` | LOW | `system/logs/audit.jsonl` crossed the 50 MB advisory threshold. |
| `fama-exposure` | HIGH | A downstream note wikilinking a **superseded** claim (`lifecycle: archived` or `superseded_by` set) — reuse of obsolete memory. |
| `graph-analyze` | LOW | Orphan synthesis notes (claims/hubs with zero inlinks). |
| `orphan-working-files` | LOW | Leftover working files (`*.tmp.*`, `*.bak`, `*.orig`, …) outside transient zones. |
| `stale-fleeting` | LOW | Fleeting notes older than 7 days — promote or discard. |

Detector notes:

- `vault-hash-drift` includes legitimate human edits: the finding means the
  audit trail no longer pins the file. Completed deletes record the empty-bytes
  hash, so a deleted-and-still-absent file stays clean.
- `skeleton-drift` runs only in installed vaults (`.git` present); the package
  seed ships no empty directories.
- `audit-log-size` is advisory because the audit log is append-only and never
  rotated ([quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

CLI entry point:

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault <vault> [--json] [--gate detector-name]
python3 -m memoria_vault.runtime.subsystems.integrity.linter.hub_handoff --vault <vault> [--threshold 15] [--json]
```

`--gate DETECTORS` makes only the named detectors blocking (exit 1); everything else stays advisory. The verdict rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM/HIGH) / **FAIL** (any CRITICAL).

---

## The pre-commit hook

The installer wires the package seed's `.githooks/pre-commit` into the deployed vault's `.git/hooks/pre-commit`. On every commit it passes the staged `.md` paths to `memoria_vault.runtime.subsystems.integrity.linter.precommit_check`, which validates each typed document against its schema via the shared loader (`memoria_vault.runtime.subsystems.lib.schema`). Any error blocks the commit (exit 1). Exempt: untyped `system/` infrastructure, vault-root nav pages, and paths outside the vault.

---

## Per-request digests

`memoria_vault.runtime.subsystems.integrity.linter.session_summary` writes the second log from the [quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md): a deterministic audit digest, not an LLM summary.

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
output; no external scheduler is required.

---

## Auto-fix classes

Auto-fix is class-gated at the policy layer: the four classes and their dispositions are owned by [Policy gate](../control-and-policy/policy-mcp.md#auto-fix-classes). The Linter operation is report-only.

---

## Related

- The schemas the detectors validate against: [Frontmatter fields](../data-model/frontmatter.md)
- The class gate enforcing auto-fix policy: [Policy gate](../control-and-policy/policy-mcp.md#auto-fix-classes)
- Where the findings surface: [Dashboards](dashboards.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../system/installer.md)
