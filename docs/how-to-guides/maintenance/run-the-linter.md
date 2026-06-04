---
title: Run the Linter
parent: Maintenance
nav_order: 2
---


# Run the Linter

Trigger a structural health check on the vault — either on demand or to review a scheduled report. The Linter detects orphaned notes, broken links, stale enrichment, schema drift, and profile install drift.

## When to run

- **On demand:** after a large batch ingest, after editing profile files, or when a Dataview query returns unexpected results
- **Weekly:** as part of the [weekly review](run-the-weekly-review.md), step 8
- **Automatically:** the Linter runs on a cron schedule (see [Linter § Schedule](../../reference/linter.md#schedule)) and after each ingest batch

## Steps

**1. Start a Linter session.**

```bash
hermes -p memoria-linter chat -s lint
```

**2. Run a dry-run scan.**

```text
/lint --dry-run
```

This reports findings without making any changes. Review the output before deciding which fixes to apply.

**3. Scope the scan if needed.**

To limit the scan to a specific folder (faster for targeted checks):

```text
/lint --target 20-sources/ --dry-run
/lint --target 30-synthesis/ --dry-run
```

**4. Read the report by severity.**

The Linter categorizes findings by severity:

| Severity | Meaning | Action |
| --- | --- | --- |
| CRITICAL | Vault integrity or security at risk | Fix immediately, this session |
| HIGH | Silent or active breakage | Fix this session |
| MEDIUM | Real drift, will compound | Address in weekly review |
| LOW | Cosmetic or easily recovered | Defer or accept |

**5. Apply auto-fixes for safe findings.**

For findings the Linter can fix without human judgment (e.g., whitespace normalization, missing `lifecycle` defaults on new notes):

```text
/lint --fix --target 20-sources/
```

Review what was changed with `git diff` before committing.

**6. Fix manual findings by hand.**

For findings that require judgment (broken links, schema mismatches, orphaned notes), address them in Obsidian directly. The most common ones have dedicated recovery guides — see the Related section below.

**7. Run a health report** to check cross-cutting system status:

```text
/health-report
```

This checks profile install drift, policy MCP connectivity, audit log rotation, and the `.bib` sync status in one pass.

## Verify

Run the scan again after fixes:

```text
/lint --dry-run
```

Confirm CRITICAL and HIGH findings are gone. Commit any changes made:

```bash
git add vault/
git commit -m "maintenance: resolve lint findings"
```

## Related

- Weekly review (lint is step 8): [Run the weekly review](run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../recovery/fix-broken-frontmatter.md)
- Fix profile drift: [Fix profile drift](../recovery/fix-profile-drift.md)
- Linter profile design: [The Linter](../../explanation/profiles/linter.md)
- Severity scale: [explanation/profiles/linter.md § severity-scale](../../explanation/profiles/linter.md)
