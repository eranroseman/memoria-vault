---
title: Rebuild the search index
parent: Operate
grand_parent: How-to guides
nav_order: 5
---


# Rebuild the search index

Rebuild the checked-only qmd input tree and refresh qmd's local index. Alpha.14
uses qmd as the required local retrieval engine, with deterministic BM25 fallback
for degraded local runs ([External integrations](../../reference/integrations.md)).

## When to rebuild

- `memoria ask` misses checked Concepts you know exist ([Query the vault](../knowledge/query-the-vault.md))
- A checked source, digest, note, or hub was promoted and does not appear in search
- `qmd search "known term"` returns empty or omits checked Concepts you know exist

## When a rebuild is the fix

Before rebuilding, rule out cheaper causes:

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| One new Concept is not found | Its DB/read API verdict is not `check_status = checked`, or the checked input tree is stale | Confirm the Concept is checked; then rebuild |
| Search misses many checked Concepts or returns empty | Stale or missing checked input tree / qmd index | Run this guide |
| Raw `qmd search` finds it but `memoria ask` does not cite it | Not an index problem | Use [Query the vault](../knowledge/query-the-vault.md) troubleshooting |

## Steps

**1. Check qmd readiness.**

```bash
memoria doctor --workspace <workspace> --check qmd
```

Fix any failed readiness row before rebuilding. `--embeddings` also requires
qmd's model cache; run `qmd pull` if the doctor reports missing models.

**2. Rebuild the checked input tree and qmd index.**

```bash
memoria workspace rebuild --workspace <workspace> --search
```

This copies only checked, current Catalog and Knowledge Concepts plus checked
Work text and graph neighborhoods into `.memoria/index/qmd/checked/`, writes
`.memoria/index/qmd/manifest.json`, registers the qmd collection, and runs
`qmd update`. The index lives inside the workspace and is gitignored — never
commit it.

Add embeddings only after qmd models are present:

```bash
memoria workspace rebuild --workspace <workspace> --search --embeddings
```

**3. Verify the rebuild.**

```bash
memoria ask --workspace <workspace> --question "<term>"
```

Confirm the expected checked retrieval documents now appear. Use raw
`qmd search "<term>"` only when you need to distinguish qmd index state from
Memoria's checked-read filtering.

## Verify

```bash
memoria ask --workspace <workspace> --question "term in checked Work or Concept"
```

Returns the retrieval document, and Ask cites recently checked sources again.

## Related

- Stale-index failure mode: [Failure modes](../../reference/failure-modes.md) — "qmd search index stale"
- The search consumer you'll notice first: [Query the vault](../knowledge/query-the-vault.md)
- Where qmd sits in the toolchain: [External integrations](../../reference/integrations.md)
