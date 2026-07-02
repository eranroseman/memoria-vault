---
title: Run the Linter
parent: Operate
grand_parent: How-to guides
nav_order: 1
---

# Run the Linter

Run a structural health check on the vault, or review the scheduled report. The Linter is an **operation, not an agent** — deterministic, zero-LLM runtime code under `memoria_vault.runtime.subsystems.integrity.linter`, report-only by design: findings surface for you to act on; nothing is auto-moved or auto-archived ([Linter: detectors and auto-fix](../../reference/linter.md)).

## When it runs without you

- **Daily cron** — the installer wires `memoria-lint` at 06:00: the detectors plus a golden-copy drift check. Findings feed Maintenance's Drift watch and Loose ends views.
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

**3. Check golden-copy drift.**

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault . check
```

Reports any system file (templates, dashboards, patterns, eval tasks, scripts, `home.md`, `system/vocabulary.md`, `AGENTS.md`) that drifted from the installer-staged golden copy. To repair:

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault . restore          # propose-only: lists what it would restore
python3 -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault . restore --apply  # write the golden bytes back, deliberately
```

**4. Fix findings by hand.**

Every detector is report-only — fixes are yours, in Obsidian or the editor. The most common ones have dedicated recovery guides (see Related). Commit when done; the pre-commit hook re-validates what you staged.

**5. Confirm scheduled wiring is alive** (occasionally):

```bash
.memoria/scripts/lint-cron.sh
memoria workspace check --workspace . --schedule-id lint-manual --json
```

## Verify

- A re-run reports no CRITICAL or HIGH findings
- `golden_restore.py check` exits clean
- Maintenance's Drift watch and Loose ends views show the improvement after the next cron pass

## Related

- Weekly review (the structural-health step): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)
- The detector inventory and gate flags: [Linter: detectors and auto-fix](../../reference/linter.md)
- Where findings surface: [Dashboards](../../reference/dashboards.md)
