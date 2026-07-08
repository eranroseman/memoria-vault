---
title: Rebuild the search index
parent: Operate
grand_parent: How-to guides
nav_order: 3
---

# Rebuild the search index

Rebuild the checked-only BM25 input tree and manifest used by `memoria ask`,
`memoria project ask`, and gap analysis.

## When to rebuild

- `memoria ask` misses checked Concepts you know exist.
- A checked Work, digest Work, note, or hub was promoted and does not appear in search.
- You refreshed generated Work text or graph neighborhoods.

## Steps

**1. Rebuild the checked input tree.**

```bash
memoria workspace rebuild --workspace <workspace> --search
```

This copies only checked, current catalog Work rows and Knowledge Concepts plus
checked Work text and graph neighborhoods into `.memoria/index/search/checked/`
and writes `.memoria/index/search/manifest.json`. The index tree is generated
workspace state and should not be committed.

**2. Check the local search state.**

```bash
memoria doctor --workspace <workspace> --check search
```

The search check should report the checked root and manifest as present.

**3. Verify the rebuild.**

```bash
memoria ask --workspace <workspace> --question "<term>"
```

Confirm the expected checked retrieval documents now appear.

## Related

- Stale-index failure mode: [Failure modes](../../reference/system/failure-modes.md)
- Querying the vault: [Query the vault](../knowledge/query-the-vault.md)
- Search reference: [Search](../../reference/pipelines-and-io/search.md)
