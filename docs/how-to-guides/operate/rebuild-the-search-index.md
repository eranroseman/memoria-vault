---
title: Rebuild the search index
parent: Operate
grand_parent: How-to guides
nav_order: 5
---


# Rebuild the search index

Rebuild the checked-only qmd input tree and refresh qmd's local index. Alpha.11
uses checked-only BM25 as the accepted retrieval baseline; vector and hybrid
retrieval are later eval work ([External integrations](../../reference/integrations.md)).

## When to rebuild

- The Co-PI's vault answers miss checked Concepts you know exist ([Query the vault](../knowledge/query-the-vault.md))
- A checked source, digest, note, or hub was promoted and does not appear in search
- `qmd search "known term"` returns empty or omits checked Concepts you know exist

## When a rebuild is the fix

Before rebuilding, rule out cheaper causes:

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| One new Concept is not found | It is not `check_status: checked`, or the checked input tree is stale | Confirm the Concept is checked; then rebuild |
| Search misses many checked Concepts or returns empty | Stale or missing checked input tree / qmd index | Run this guide |
| Raw `qmd search` finds it but the Co-PI does not cite it | Not an index problem | Use [Query the vault](../knowledge/query-the-vault.md) troubleshooting |

## Steps

**1. Rebuild the checked input tree.**

```bash
cd <vault>
python -m memoria_vault.runtime.worker enqueue-operation \
  --vault . \
  --operation-id rebuild-checked-qmd-source \
  --idempotency-key rebuild-checked-qmd-source
python -m memoria_vault.runtime.worker run-pending --vault . --limit 1
```

This copies only checked, current Catalog and Knowledge Concepts into
`.memoria/index/qmd/checked/` and writes `.memoria/index/qmd/manifest.json`.

**2. Register and update qmd.**

```bash
qmd collection add .memoria/index/qmd/checked --name memoria-checked --mask '**/*.md'
qmd update
```

The index lives inside the vault and is gitignored — never commit it.

**3. Verify the rebuild.**

```bash
qmd search "<term>"
```

Confirm the expected checked retrieval documents now appear. Then test the
consumer you actually noticed the staleness in — ask the Co-PI a question whose
answer lives in a recently checked Concept or Work and check that it cites that
source.

## Verify

```bash
qmd search "term in checked Work or Concept"
```

Returns the retrieval document, and the Co-PI's vault answers cite recently
checked sources again.

## Related

- Stale-index failure mode: [Failure modes](../../reference/failure-modes.md) — "qmd search index stale"
- The search consumer you'll notice first: [Query the vault](../knowledge/query-the-vault.md)
- Where qmd sits in the toolchain: [External integrations](../../reference/integrations.md)
