---
title: Run the Linter
parent: Operate
grand_parent: How-to guides
nav_order: 1
---

# Run the Linter

Run a structural health check on the vault, or review the scheduled report.
Findings surface for you to act on; the Linter does not move or archive files
for you.

## When it runs without you

- **Operator-managed schedule** — wire the `memoria workspace check --workspace . --json` command through cron, systemd, launchd, Task Scheduler, or another local scheduler if you want unattended checks. The installer does not register that schedule.
- **Pre-commit hook** — every staged `.md` is schema-validated; an invalid typed document blocks the commit.

Run it by hand after a large batch ingest, after structural edits, or when a filtered view returns something unexpected.

## Steps

**1. Run the detectors.**

From the vault root, use the interpreter installed with the vault:

```bash
./.memoria/.venv/bin/python -m memoria_vault.runtime.subsystems.integrity.linter.detectors \
  --vault . --json
```

On Windows, replace `./.memoria/.venv/bin/python` with
`.\.memoria\.venv\Scripts\python.exe`.

**2. Read the report by severity.**

| Severity | Meaning | Action |
| --- | --- | --- |
| CRITICAL | Vault integrity at risk | Fix immediately — the verdict rolls to FAIL. Only an installed optional policy hook pauses review-gated adapter writes. |
| HIGH | Silent or active breakage | Fix this session |
| MEDIUM | Real drift, will compound | Address in the weekly review |
| LOW | Cosmetic or easily recovered | Defer or accept |

The verdict band rolls up to PASS, REVIEW, or FAIL.

**3. Fix findings by hand.**

Every detector is report-only — fixes are yours, in Obsidian or the editor. The most common ones have dedicated recovery guides (see Related). Commit when done; the pre-commit hook re-validates what you staged.

**4. Confirm scheduled wiring is alive** (if you configured it):

```bash
memoria workspace check --workspace . --schedule-id lint-manual --json
```

## Verify

- A re-run reports no CRITICAL or HIGH findings
- A fresh command run no longer reports the resolved finding

## Related

- Weekly review (the structural-health step): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)
- The detector inventory and gate flags: [Linter: detectors and auto-fix](../../reference/analysis-and-surfaces/linter.md)
- Shipped and planned finding surfaces: [Dashboards](../../reference/analysis-and-surfaces/dashboards.md)
