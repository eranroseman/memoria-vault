---
title: Run a schema migration
parent: Operate
nav_order: 3
---

# Run a schema migration

Rewrite a frontmatter field across many notes at once — a field rename, a value-set change, or a deprecated-field removal. In v0.1.0-alpha.2 there is **no automated migration command**: a migration is a deliberate, git-disciplined manual pass, validated by the schemas. That's by design — schema changes fall in the `schema-content` class, which the policy gate never lets run unattended ([Linter: detectors and auto-fix](../../reference/linter.md)).

Use this for **structural** changes that touch many notes. For renaming a single vocabulary term, [Manage your topic vocabulary](../curate/manage-vocabulary.md) covers the lighter path.

## Prerequisites

- A clean working tree — `git status` shows nothing uncommitted, so the migration is one reviewable diff
- A clear before/after for the field you're changing
- If the schema itself changes: the matching edit ready for `.memoria/schemas/types/<type>.yaml` (the single schema source the Linter, the pre-commit gate, and the policy MCP all read)

## Steps

**1. Commit the current vault state.**

```bash
cd ~/Memoria && git add -A && git commit -m "pre-migration snapshot"
```

A clean commit beforehand makes the migration one diff you can review — and revert in one command.

**2. Enumerate the affected notes — your dry run.**

```bash
grep -rl "^methodology: rct" notes/ catalog/ | tee /tmp/migration-files.txt
wc -l /tmp/migration-files.txt
```

If the count is surprisingly high or low, your selector is wrong — fix it before touching anything. Do not proceed on a surprising count.

**3. Update the schema first (if the field definition changes).**

Edit `.memoria/schemas/types/<type>.yaml` so the new field name or value set is legal *before* the notes change — otherwise every migrated note fails validation.

**4. Apply the change.**

For a mechanical rename over the reviewed file list:

```bash
xargs -a /tmp/migration-files.txt sed -i 's/^methodology: rct$/methodology: randomized-controlled-trial/'
```

For anything non-mechanical (restructuring a map, splitting a field), edit by hand or with a one-off script — but always over the step-2 list.

**5. Validate.**

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

`schema-check` must report nothing for the migrated field. The pre-commit gate will re-validate every staged note at commit, so a missed file blocks rather than lands.

**6. Review and commit.**

```bash
git diff --stat       # only the expected files, only the expected change
git add -A && git commit -m "schema: rename methodology rct → randomized-controlled-trial"
```

If the diff is wrong, `git reset --hard HEAD~1` returns you to the step-1 snapshot.

## Verify

- `git diff --stat` showed only the intended change across the expected note count before commit
- The detectors report no `schema-check` findings for the migrated field
- Dataview/Bases views that filter on the field still return the expected notes

## Related

**How-to**

- The lighter, single-term path: [Manage your topic vocabulary](../curate/manage-vocabulary.md)
- The validation pass: [Run the Linter](run-the-linter.md)
- Recovering from a bad edit: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)

**Reference**

- The schema source and what reads it: [Note types](../../reference/note-types.md)
- Why `schema-content` never runs unattended: [Linter: detectors and auto-fix](../../reference/linter.md)
