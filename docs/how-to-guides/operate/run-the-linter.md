---
title: Run the Linter
parent: Operate
grand_parent: How-to guides
nav_order: 1
---

# Run the Linter

Run a structural health check on the vault, or review the scheduled report. The Linter is an **operation, not an agent** — deterministic, zero-LLM runtime code under `memoria_vault.runtime.subsystems.integrity.linter`, report-only by design: findings surface for you to act on; nothing is auto-moved or auto-archived ([Linter: detectors and auto-fix](../../reference/linter.md)).

## When it runs without you

- **Operator-managed schedule** — wire the `memoria workspace check --workspace . --json` command through cron, systemd, launchd, Task Scheduler, or another local scheduler if you want unattended checks. The installer does not register that schedule.
- **Pre-commit hook** — every staged `.md` is schema-validated; an invalid typed document blocks the commit.

Run it by hand after a large batch ingest, after structural edits, or when a Dataview query returns something unexpected.

## Steps

**1. Run the detectors.**

From the vault root:

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault .
```

Add `--json` for machine-readable output. The detectors cover schema validity, broken frontmatter and body wikilinks, misplaced typed documents, dashboard field drift, superseded-claim reuse (`fama-exposure`), broken extract paths, orphan synthesis notes, leftover working files, and stale fleeting notes.

**2. Read the report by severity.**

| Severity | Meaning | Action |
| --- | --- | --- |
| CRITICAL | Vault integrity at risk | Fix immediately — the verdict rolls to FAIL and blocks new delegation or worker promotion |
| HIGH | Silent or active breakage | Fix this session |
| MEDIUM | Real drift, will compound | Address in the weekly review |
| LOW | Cosmetic or easily recovered | Defer or accept |

The verdict band rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM or HIGH) / **FAIL** (any CRITICAL) — the same band Maintenance's Drift watch shows.

**3. Fix findings by hand.**

Every detector is report-only — fixes are yours, in Obsidian or the editor. The most common ones have dedicated recovery guides (see Related). Commit when done; the pre-commit hook re-validates what you staged.

**4. Confirm scheduled wiring is alive** (if you configured it):

```bash
memoria workspace check --workspace . --schedule-id lint-manual --json
```

## Verify

- A re-run reports no CRITICAL or HIGH findings
- Request/attention and linter views show the improvement after the next scheduled or manual pass

## Related

- Weekly review (the structural-health step): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)
- The detector inventory and gate flags: [Linter: detectors and auto-fix](../../reference/linter.md)
- Where findings surface: [Dashboards](../../reference/dashboards.md)
