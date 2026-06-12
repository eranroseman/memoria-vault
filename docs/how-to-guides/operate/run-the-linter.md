---
title: Run the Linter
parent: Operate
nav_order: 1
---

# Run the Linter

Run a structural health check on the vault, or review the scheduled report. The Linter is an **engine, not an agent** — deterministic, zero-LLM Python under `.memoria/engines/linter/`, report-only by design: findings surface for you to act on; nothing is auto-moved or auto-archived ([Linter: detectors and auto-fix](../../reference/linter.md)).

## When it runs without you

- **Daily cron** — the installer wires `memoria-lint` at 06:00: the detectors plus a golden-copy drift check. Findings feed the drift-watch and loose-ends dashboards.
- **Pre-commit gate** — every staged `.md` is schema-validated; an invalid typed note blocks the commit.

Run it by hand after a large batch ingest, after structural edits, or when a Dataview query returns something unexpected.

## Steps

**1. Run the detectors.**

From the vault root:

```bash
python3 .memoria/engines/linter/detectors.py --vault .
```

Add `--json` for machine-readable output. The detectors cover schema validity, broken frontmatter and body wikilinks, misplaced typed notes, dashboard field drift, superseded-claim reuse (`fama-exposure`), broken extract paths, orphan synthesis notes, leftover working files, and stale fleeting notes.

**2. Read the report by severity.**

| Severity | Meaning | Action |
| --- | --- | --- |
| CRITICAL | Vault integrity at risk | Fix immediately — the verdict rolls to FAIL and scheduled work pauses |
| HIGH | Silent or active breakage | Fix this session |
| MEDIUM | Real drift, will compound | Address in the weekly review |
| LOW | Cosmetic or easily recovered | Defer or accept |

The verdict band rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM or HIGH) / **FAIL** (any CRITICAL) — the same band drift-watch shows.

**3. Check golden-copy drift.**

```bash
python3 .memoria/engines/linter/golden.py --vault . check
```

Reports any system file (templates, dashboards, patterns, eval tasks, scripts, `home.md`, `system/vocabulary.md`, `AGENTS.md`) that drifted from the installer-staged golden copy. To repair:

```bash
python3 .memoria/engines/linter/golden.py --vault . restore          # propose-only: lists what it would restore
python3 .memoria/engines/linter/golden.py --vault . restore --apply  # write the golden bytes back, deliberately
```

**4. Fix findings by hand.**

Every detector is report-only — fixes are yours, in Obsidian or the editor. The most common ones have dedicated recovery guides (see Related). Commit when done; the pre-commit gate re-validates what you staged.

**5. Confirm the cron is alive** (occasionally):

```bash
hermes cron list        # memoria-lint should show with a next-run time
hermes cron run memoria-lint   # force a pass now
```

## Verify

- A re-run reports no CRITICAL or HIGH findings
- `golden.py check` exits clean
- Drift-watch and loose-ends show the improvement after the next cron pass

## Related

- Weekly review (the structural-health step): [Run the weekly review](../curate/run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)
- The detector inventory and gate flags: [Linter: detectors and auto-fix](../../reference/linter.md)
- Where findings surface: [Dashboards](../../reference/dashboards.md)
