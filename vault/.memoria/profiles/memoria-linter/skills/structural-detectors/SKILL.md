---
name: structural-detectors
description: "Run the Memoria vault's deterministic structural and data-hygiene detectors (zero-LLM, via detectors.py) plus the five context-dependent drift checks that need git, SHA-256, or the audit log, then roll all findings into the lint verdict band. Use for scheduled lint sweeps, on-demand health/drift checks, and post-ingest validation."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Maintenance, Linting, Vault-Health, Drift, Deterministic]
    requires_toolsets: [terminal]
---

# structural-detectors

Detect structural drift and data-hygiene issues across the vault, then report a single
verdict band. **Every check is deterministic and report-only** — you run a fixed script or
follow a fixed procedure, compare values, and report. You contribute **no judgment** about
whether the vault is "correct"; the same vault state yields the same findings every run.
Never auto-fix here beyond what the auto-fix policy in `SOUL.md` explicitly grants.

The capability has two halves:

1. **The engine** — `scripts/detectors.py`, a pure-stdlib, zero-LLM script that runs every
   *self-contained* check (needs only the vault tree).
2. **The procedures** — five detectors that need external context (`git`, SHA-256, the audit
   log) and so can't live in the script. Their step-by-step procedures are in
   `references/structural-detectors.md`.

## When to Use

- A scheduled lint sweep fires (see the profile's `cron/scheduled.yaml`).
- A human asks for a health check, drift check, or `lint` / `health-report`.
- After an ingest batch, to validate structure before the next stage.

## Scope (which checks to run)

Two scopes, selected by how you were invoked:

- **Engine sweep** — run `scripts/detectors.py` only (the 9 self-contained checks). This is
  the nightly cadence (card `nightly-lint`), an on-demand `lint`, and the post-ingest check.
- **Full sweep** — the engine **plus** the five agent-procedure drift detectors. These are
  heavier (git diffs, SHA-256 over `~/.hermes`, an audit-log pass), so they run on the weekly
  cadence (card `weekly-drift-report`) or when a human explicitly asks for a drift check.

A human request scopes itself ("check for drift" → full; "run the linter" → engine). Default
to the engine sweep when the scope is unstated.

## Quick Reference

Run the engine (resolve the vault root from the session, not a hardcoded path):

```bash
python "${HERMES_SKILL_DIR}/scripts/detectors.py" --vault "<vault>"          # human-readable
python "${HERMES_SKILL_DIR}/scripts/detectors.py" --vault "<vault>" --json   # machine-readable findings
python "${HERMES_SKILL_DIR}/scripts/detectors.py" --self-test                # synthetic-fixture unit tests
python "${HERMES_SKILL_DIR}/scripts/detectors.py" --vault "<vault>" --gate dashboard-field-drift
```

`--gate <names>` exits non-zero if any finding from the named detectors exists (for CI);
all other findings stay advisory.

**Engine detectors** (in `detectors.py`): `orphan-working-files`, `stale-fleeting`,
`stale-answer-drafts`, `extract-path-broken`, `frontmatter-schema-check`, `broken-wikilinks`,
`dashboard-field-drift`, `graph-analyze`, `fama-exposure`.

**Procedure detectors** (in `references/structural-detectors.md`, run by you with `git` / SHA-256 / audit-log):
`profile-install-drift`, `vault-hash-drift`, `skeleton-drift`, `command-vocab-drift`, `plugin-config-drift`.

## Procedure

1. **Run the engine.** Execute `scripts/detectors.py --vault <vault> --json` and collect its findings.
2. **(Full sweep only) Run the five procedure detectors.** Follow `references/structural-detectors.md`
   for each. These are report-only; never re-run the installer, restore a hashed file, or
   auto-edit a config to "fix" drift. Skip this step for an engine sweep.
3. **Merge findings** into one list.
4. **Compute the verdict band** from the merged severities (the rule lives in `SOUL.md` —
   `FAIL` only on CRITICAL; `REVIEW` on any HIGH or MEDIUM; otherwise `PASS`).
5. **Report.** Attach the report as a board comment or surface it on the relevant dashboard
   under `00-meta/01-dashboards/`. Record a rejecting `agent_recommendation` only when a
   structural issue blocks review or promotion. Never write silent changes to user notes.
6. **Auto-fix** only within the granted classes, and only when explicitly authorized — see
   `references/operations.md` for the safe-fix recipe. The audit-log rotation procedure is
   there too.

## Verification

- Before trusting a run, confirm the engine is healthy: `scripts/detectors.py --self-test`
  exits `0` when all synthetic-fixture checks pass.
- A clean sweep prints `verdict: PASS` with zero HIGH/CRITICAL findings.

## Reference

- `references/check-catalog.md` — the full catalog of checks with thresholds (which substrate
  runs each), and the per-type enrichment-staleness cadences.
- `references/structural-detectors.md` — per-detector severity table and the full procedure,
  false-positive rules, and remediation paths for the five context-dependent detectors.
- `references/operations.md` — the safe-and-unambiguous-fix Templater recipe and the
  audit-log rotation procedure.
- The profile contract (folders, auto-fix classes, severity scale, verdict band) is in `SOUL.md`.
