---
topic: explorations
title: Structural linter and drift detection — zero-LLM vault health
status: historical
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 24
---

# Structural linter and drift detection — zero-LLM vault health

> **Historical (v0.1.0).** This note describes the pre-v0.1.1 Linter and is kept for
> design rationale only. The current sources are
> [ADR-29](../adr/29-testing-framework.md) and
> [Linter reference](../reference/linter.md).

A design capture of the Linter as built: a deterministic detector engine, a
restorable golden copy, a commit-time schema gate, a verdict band, and the cron
cadence — plus the agent-run drift procedures that stayed on the drawing board.
Reconstructed from
[`src/.memoria/engines/linter/`](../../src/.memoria/engines/linter) — an engine, not a profile (ADR-46/48).
Backed by [ADR-29](../adr/29-testing-framework.md) (layered testing),
[ADR-49](../adr/49-catalog-in-bases-linter-monitor.md) (gates at commit, monitors
between), [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md) (the golden
copy), and [ADR-12](../adr/12-obsidian-linter-reference-only.md) (why not
obsidian-linter).

> **Why capture this.** The Linter is the system's entropy brake — it surfaces the
> silent failures (vocabulary drift, orphans, broken links, obsolete-claim reuse)
> that produce no error on their own. The detectors are fully built but had no design
> exploration.

## What it is

Three pieces, all reporting/proposing by default (never silently fixing canonical
content):

1. **The detector engine** — [`engines/linter/detectors.py`](../../src/.memoria/engines/linter/detectors.py),
   a zero-LLM, pure-stdlib set of self-contained vault checks. Runs daily and in CI.
2. **The golden copy** — [`engines/linter/golden.py`](../../src/.memoria/engines/linter/golden.py)
   ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the installer stages a
   SHA-256-manifested canonical copy of every system file under `.memoria/golden/`;
   `check` reports drift, `restore` is propose-only (a dry-run diff + an Inbox flag)
   unless `--apply` is passed deliberately.
3. **The commit gate** — [`engines/linter/precommit_check.py`](../../src/.memoria/engines/linter/precommit_check.py)
   wired as the vault's git `pre-commit` hook: every staged `.md` note must pass its
   type schema (`.memoria/schemas/types/`) or the commit blocks. This is ADR-49's
   "gates at commit, monitors between" — the cron sweep is the *monitors* half.
   (A second commit-time trigger — a draft commit raising a Peer-reviewer verify
   card — is deferred,
   [#377](https://github.com/eranroseman/memoria-vault/issues/377).)

## How it works

### The engine (deterministic, zero-LLM)

`detectors.py` implements twelve checks. Each emits findings at one of four
severities (`CRITICAL · HIGH · MEDIUM · LOW`):

| Detector | Flags |
|---|---|
| `orphan_working_files` | leftover `*.tmp.*`, `*.bak`, `*.orig`, `*~`… outside transient zones |
| `stale_fleeting` | fleeting notes older than 7 days |
| `stale_answer_drafts` | answer drafts older than 90 days (report-only) |
| `extract_path_broken` | a paper-note `extract_path` pointing at a missing file |
| `frontmatter_schema_check` | missing `type`, an unknown type, or a typed note failing its `.memoria/schemas/types/` schema |
| `frontmatter_link_check` | an authored frontmatter connection (`links:` map, `entity`) whose wikilink resolves to no note (ADR-52) |
| `broken_wikilinks` | a body `[[target]]` resolving to no note |
| `dashboard_field_drift` | a dashboard Dataview query referencing a field no template defines |
| `graph_analyze` | orphan synthesis notes (zero inlinks, MOCs excluded) |
| `fama_exposure` | a note citing a superseded/archived claim — the FAMA reuse-of-obsolete-memory failure |
| `misplaced_note` | a typed note outside its schema home, or a stray top-level folder |
| `audit_unpaired_writes` | a mutating allow in `audit.jsonl` whose paired `write_complete` never arrived within 1 h — a hole in the reversibility chain (PR [#384](https://github.com/eranroseman/memoria-vault/pull/384)) |

Findings roll up to a **verdict band**:

```
FAIL    — any CRITICAL
REVIEW  — any HIGH or MEDIUM
PASS    — only LOW, or none
```

A `--gate` flag makes only the *named* detectors blocking (exit 1) while everything
else stays advisory — CI gates `dashboard-field-drift` against `src/` this way; the
engine's tests live in the pytest tree (`tests/test_detectors.py`, ADR-44).

### The drift procedures — designed, not shipped

The v0.1.0 design added five agent-run drift checks needing context the engine
lacks (git, `~/.hermes` deploy state, docs-tree history): `profile-install-drift`,
`vault-hash-drift` (current file hash vs. the audit log's last `after_hash` —
tamper-detection), `skeleton-drift`, `command-vocab-drift`, and
`plugin-config-drift`. **None ship in v0.1.1**: the Linter *profile* that would
have run them was retired to this engine (ADR-46/48), and the
[`detectors.py`](../../src/.memoria/engines/linter/detectors.py) docstring names
them out of scope. The one audit-state check that fit the engine's
vault-tree-only constraint — `audit_unpaired_writes` — landed in the table above;
the rest are deferred with no dedicated tracking issue yet.

### Cadence

The installer wires one daily cron, `memoria-lint` (`0 6 * * *`): the detector
sweep plus the golden-copy `check`. It is report-only — output is not yet
persisted to `system/logs/lint-findings.jsonl` or raised as board cards, so
between commits the findings surface only when the engine is run by hand (the
v0.1.0 nightly-card / weekly-drift-report design did not ship). The commit gate
covers the write-time half.

### Auto-fix discipline

Default is dry-run. Repairs are gated by class (enforced by the
[policy gate](policy-gate-and-permissions.md)): `safe-and-unambiguous` and
`authorized-targeted` may apply; `schema-content` is always dry-run (needs a
schema-migrate); `review-gated-edit` is always denied.

## Design rationale

- **Deterministic by mandate.** Vault health is bookkeeping, not judgment. A zero-LLM
  engine is fast, free, reproducible, and trustworthy — the same input always yields
  the same verdict, and the verdict can gate scheduled work without a human in the loop.
- **Silent failures need proactive surfacing.** Vocabulary drift, orphans, broken
  links, and obsolete-claim reuse return no error — queries just quietly go thin. The
  detectors exist to make that loud before it compounds (the "lint or decay" principle).
- **Engine vs. procedure split.** Checks that need only the vault tree run daily
  and cheap in the engine; checks that need git, deploy state, or external history
  were designed as agent procedures — and deferred rather than half-shipped when
  the Linter profile was retired. The boundary is the input set, not the cadence.
- **Report, then fix.** Defaulting to dry-run and routing fixes through classes keeps
  the Linter from ever silently rewriting canonical content — the one thing a health
  checker must not do.
- **Not obsidian-linter (ADR-12).** A second frontmatter authority would collide
  continuously with the `_proposed_classification` / `_enrichment` namespaces the
  agents write; whole-folder exclusion can't protect live drafts. Memoria's own Linter
  is the only structural formatter.

## Related

- [ADR-29](../adr/29-testing-framework.md), [ADR-12](../adr/12-obsidian-linter-reference-only.md), [ADR-10](../adr/10-claim-supersession.md) (FAMA exposure)
- [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md) — the audit chain `audit_unpaired_writes` guards (and `vault-hash-drift` would verify)
- [Dashboards — ten views, four groups, two data sources](dashboards-design.md) — `drift-watch` and `loose-ends` render these findings
- Reference: [`docs/reference/linter.md`](../reference/linter.md), [`failure-modes.md`](../reference/failure-modes.md)
