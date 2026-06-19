---
title: Fix empty enrichment
parent: Troubleshooting
nav_order: 9
---

# Fix empty enrichment

**Symptom:** a paper ingested "successfully" — the Catalog entity and Inbox candidate appeared — but the note carries no enrichment: the `_enrichment` block is empty, `research_area` and `methodology` were never applied, and there's no `[!brief]` comparative read.

- A captured paper's `_enrichment.*` namespace is empty or absent
- `research_area` / `methodology` stayed unset even though the paper is clearly classifiable
- No Inbox `flag` was raised explaining the ambiguity — it simply looks like nothing happened

**Diagnosis:** the Librarian's `OPENALEX_API_KEY` is missing. OpenAlex has required a key since 2026-02; without it the enrichment call degrades silently. Tier-0 capture still succeeds (it works from the local `.bib` alone — the offline floor), so the note lands and ingest *looks* done — but the OpenAlex topics that drive classification never arrive, so `classify` is a no-op and the enrichment block stays thin. This is the trap: degraded data, no error.

**Fix:** seed the key, then re-ingest the affected paper(s) — the fix is not retroactive, the enrichment has to be re-run.

## Detect

**1. Confirm the key is missing.**

```bash
grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env || echo "not set"
```

**2. Confirm the symptom on the note.** Open the paper at `catalog/papers/<citekey>.md` and check that the `_enrichment` namespace is empty and `research_area` is unset.

**3. Confirm classify saw no data.** The classify audit names the cause — a no-data run logs a no-op rather than an applied or flagged decision:

```bash
grep '"citekey": "<citekey>"' system/logs/classify.jsonl
```

## Fix

**1. Add the OpenAlex key and propagate it.**

Register a free key at `openalex.org/settings/api`, add it to the global secrets file, then redeploy so each profile's `.env` is seeded (the redeploy never overwrites a value already set):

```bash
echo 'OPENALEX_API_KEY=your-key-here' >> ~/.hermes/.env
bash scripts/install.sh --profiles-only --vault <vault>
grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env   # confirm seeded
```

See [Set up Hermes](../setup/set-up-hermes.md) and [External integrations](../../reference/integrations.md) for the full key roster.

**2. Re-ingest the affected paper.**

Enrichment ran once and degraded; re-running it on the single citekey backfills it. From Obsidian, re-run the catalog step on the one paper:

`Cmd/Ctrl-P` → **Memoria: catalog source**, enter the `<citekey>`. This stages a Librarian `catalog-enrich-record` card that re-runs enrichment with the key now present. (Equivalently, ask the Co-PI: "re-enrich `<citekey>`".)

For a paper that never completed past Tier-0 (`ingest_status: tier0`), the `memoria-sweeps` cron's `--retry` backstop re-enqueues it automatically every 15 minutes — once the key is set, the next sweep recovers it with no action needed ([Sweeps](../../reference/sweeps.md)).

**3. For a whole batch captured key-less,** re-catalog each citekey the same way. Each enqueues its own card and the Librarian processes them one at a time.

## Verify

- `catalog/papers/<citekey>.md` now has a populated `_enrichment` block and a `[!brief]` read
- `research_area` (and `methodology` where derivable) is applied, or one Inbox `flag` explains a genuine ambiguity — not silence
- `system/logs/classify.jsonl` shows an `applied` or `flagged` decision for the citekey, not a no-op

## If enrichment is still empty after re-ingest

- **The key didn't propagate.** Re-check `grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env`; if absent, the redeploy didn't run against the right vault — re-run `--profiles-only --vault <vault>`.
- **The paper genuinely resolves no OpenAlex topics.** Some preprints and non-indexed works have no topics; classification staying unset is then correct, not a bug — tag `research_area` by hand.
- **Other enrichment sources also empty.** If Semantic Scholar / Crossref / PubMed fields are blank too, this is a broader network or `.bib` problem, not the OpenAlex key — see [Failure modes](../../reference/failure-modes.md).

## Related

- The enrichment and classify stages: [Ingest routing](../../reference/ingest.md)
- The re-ingest backstops: [Sweeps](../../reference/sweeps.md)
- Where the keys live: [Set up Hermes](../setup/set-up-hermes.md), [External integrations](../../reference/integrations.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
