---
title: How to run a schema migration
parent: Maintenance
---

# How to run a schema migration

Rewrite a frontmatter field across many notes at once — a field rename, a value-set change, or a deprecated-field removal — using the Linter's `schema-migrate` command, always dry-run first.

Use this for **structural** frontmatter changes that touch many notes. For renaming a single controlled-vocabulary term (e.g. a `topic` value), [manage-vocabulary](manage-vocabulary.md) covers the lighter path; this guide is for changes to the schema itself.

> **High-stakes, human-only.** `schema-migrate` falls in the `schema-content` auto-fix class, which is **always dry-run / report-only** under the policy gate ([reference/linter.md](../../reference/linter.md)). The Linter cannot apply a migration on its own — you review the dry-run and re-run without `--dry-run` deliberately. Commit first so the change is reversible.

## Prerequisites

- A clean working tree — `git status` shows nothing uncommitted (so the migration is a single reviewable diff)
- The Linter profile installed and running ([set-up-hermes.md](../setup/set-up-hermes.md))
- A clear before/after for the field you're changing

## Steps

**1. Commit the current vault state.**

```bash
cd ~/Memoria && git add -A && git commit -m "pre-migration snapshot"
```

A migration rewrites frontmatter across many files. A clean commit beforehand makes the migration one diff you can review — and revert in one command if it's wrong.

**2. Start a Linter session.**

```bash
hermes -p memoria-linter chat -s lint
```

**3. Run the migration as a dry-run.**

Name the field and the change. Examples:

```text
# Field value rename
/schema-migrate --field study_design --from rct --to randomized-controlled-trial --dry-run

# Deprecated field removal
/schema-migrate --field legacy_tag --remove --dry-run

# Schema version bump after a breaking field change
/schema-migrate --bump-schema-version --from 1 --to 2 --dry-run
```

The dry-run reports every note it *would* touch and the exact before/after for each — but changes nothing.

**4. Review the dry-run output carefully.**

Confirm the affected-note count matches your expectation and the before/after is correct. If the count is surprisingly high or low, your `--field`/`--from` selector is wrong — fix it and re-run the dry-run. Do not proceed on a surprising count.

**5. Apply the migration.**

Re-run the exact same command with `--dry-run` removed:

```text
/schema-migrate --field study_design --from rct --to randomized-controlled-trial
```

**6. Verify and commit.**

Check the diff, run a lint pass to confirm no schema drift remains, then commit:

```bash
cd ~/Memoria && git diff --stat
git add -A && git commit -m "schema: rename study_design rct → randomized-controlled-trial"
```

If the diff is wrong, `git reset --hard HEAD~1` returns you to the pre-migration snapshot from step 1.

## Verify

- `git diff --stat` shows only the intended field change, across the expected note count
- A follow-up `/lint --dry-run` reports no `schema-content` drift for the migrated field
- Dataview queries that filter on the field still return the expected notes

## Related

**How-to**

- Renaming a single vocabulary term (lighter path): [manage-vocabulary.md](manage-vocabulary.md)
- The structural health check that flags schema drift: [run-the-linter.md](run-the-linter.md)
- Recovering from broken frontmatter after a bad edit: [fix-broken-frontmatter.md](../recovery/fix-broken-frontmatter.md)

**Reference**

- The `schema-content` auto-fix class (always dry-run): [linter.md](../../reference/linter.md)
- Frontmatter field definitions: [frontmatter.md](../../reference/frontmatter.md)

**Explanation**

- Why the Linter cannot apply schema changes unattended: [linter.md](../../explanation/profiles/linter.md)
