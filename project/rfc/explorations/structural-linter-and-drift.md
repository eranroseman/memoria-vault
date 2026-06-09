---
topic: proposals
title: Structural linter and drift detection — zero-LLM vault health
status: as-built
created: 2026-06-09
---

# Structural linter and drift detection — zero-LLM vault health

A design capture of the Linter as built: a deterministic detector engine, five
agent-run drift procedures, a verdict band that gates scheduled work, and a cron
cadence. Reconstructed from
[`vault/.memoria/profiles/memoria-linter/`](../../../vault/.memoria/profiles/memoria-linter/).
Backed by [ADR-29](../../adr/29-testing-framework.md) (layered testing) and
[ADR-12](../../adr/12-obsidian-linter-reference-only.md) (why not obsidian-linter).

> **Why capture this.** The Linter is the system's entropy brake — it surfaces the
> silent failures (vocabulary drift, orphans, broken links, obsolete-claim reuse)
> that produce no error on their own. The detectors are fully built but had no design
> exploration.

## What it is

Two tiers of checks, both reporting by default (never silently fixing canonical
content):

1. **The engine** — [`scripts/detectors.py`](../../../vault/.memoria/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py),
   a zero-LLM, pure-stdlib set of self-contained vault checks. Runs nightly.
2. **The drift procedures** — five checks an agent runs because they need context the
   engine lacks (git, SHA-256 against the audit log, deployed-profile state). Run
   weekly.

## How it works

### The engine (deterministic, zero-LLM)

`detectors.py` implements ten checks. Each emits findings at one of four severities
(`CRITICAL · HIGH · MEDIUM · LOW`):

| Detector | Flags |
|---|---|
| `orphan_working_files` | leftover `*.tmp.*`, `*.bak`, `*.orig`, `*~`… outside transient zones |
| `stale_fleeting` | fleeting notes older than 7 days |
| `stale_answer_drafts` | answer drafts older than 90 days (report-only) |
| `extract_path_broken` | a paper-note `extract_path` pointing at a missing file |
| `frontmatter_schema_check` | missing `type`, or type-required fields (claim → `lifecycle`+`maturity`; paper → `citekey`) |
| `broken_wikilinks` | `[[target]]` resolving to no note |
| `dashboard_field_drift` | a dashboard Dataview query referencing a field no template defines |
| `graph_analyze` | orphan synthesis notes (zero inlinks, MOCs excluded) |
| `fama_exposure` | a note citing a superseded/archived claim — the FAMA reuse-of-obsolete-memory failure |
| `misplaced_note` | a typed note outside its schema home, or a stray top-level folder |

Findings roll up to a **verdict band**:

```
FAIL    — any CRITICAL
REVIEW  — any HIGH or MEDIUM
PASS    — only LOW, or none
```

The engine ships a `--self-test` (one of ADR-29's five L1 component self-tests:
gate, hook, board, metrics, detectors).

### The five drift procedures

These need git, hashes, or the audit log, so an agent runs them:

| Procedure | Needs | Catches |
|---|---|---|
| `profile-install-drift` | git + SHA-256 | deployed `~/.hermes/profiles/…` diverging from vault source (allowing for `{{VAULT_PATH}}` substitution) |
| `vault-hash-drift` | SHA-256 + `audit.jsonl` | a file whose current hash ≠ its last recorded `after_hash` — **CRITICAL**, tamper-detection |
| `skeleton-drift` | git log | a skeleton note (`home.md`, `troubleshooting.md`) older than the `docs/` it mirrors |
| `command-vocab-drift` | git + text | command names in docs vs. those declared in each SOUL's `## Core commands` |
| `plugin-config-drift` | git + JSON | a plugin's working `data.json` diverging from the committed version |

### Cadence

[`cron/scheduled.yaml`](../../../vault/.memoria/profiles/memoria-linter/cron/scheduled.yaml):

- **Nightly `0 2 * * *`** → `nightly-lint`: engine sweep only → card in `ready`.
- **Weekly `0 4 * * MON`** → `weekly-drift-report`: engine + the five procedures → card in `ready`.

Both create board cards rather than acting directly — the Linter proposes; the human
disposes.

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
- **Engine vs. procedure split.** Checks that need only the vault run nightly and
  cheap; checks that need git/hashes/deployed state run weekly and as agent procedures.
  Cadence matches cost.
- **Report, then fix.** Defaulting to dry-run and routing fixes through classes keeps
  the Linter from ever silently rewriting canonical content — the one thing a health
  checker must not do.
- **Not obsidian-linter (ADR-12).** A second frontmatter authority would collide
  continuously with the `_proposed_classification` / `_enrichment` namespaces the
  agents write; whole-folder exclusion can't protect live drafts. Memoria's own Linter
  is the only structural formatter.

## Related

- [ADR-29](../../adr/29-testing-framework.md), [ADR-12](../../adr/12-obsidian-linter-reference-only.md), [ADR-10](../../adr/10-claim-supersession.md) (FAMA exposure)
- [session-logging-and-audit.md](session-logging-and-audit.md) — `vault-hash-drift` reads the audit chain
- [dashboards-design.md](dashboards-design.md) — `drift-watch` and `loose-ends` render these findings
- Reference: [`docs/reference/linter.md`](../../../docs/reference/linter.md), [`failure-modes.md`](../../../docs/reference/failure-modes.md)
