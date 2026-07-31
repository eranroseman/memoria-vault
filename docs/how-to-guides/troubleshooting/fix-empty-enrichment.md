---
title: Fix empty enrichment after ingest
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 5
---

# Fix empty enrichment after ingest

**Symptom:** a source is captured and staged, but provider or full-text
enrichment does not complete and the DOI source stays unchecked.

**Diagnosis:** enrichment (`enrich-source`) either did not run or failed before
the source could be promoted as checked. The two common causes:

1. A configured provider fails, or an enhancing credential leaves its result
   thinner than expected.
2. The enrichment request is stuck (`pending`/`running`/`failed`) rather than
   never started.

## Detect

```bash
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
memoria journal tail --workspace <workspace> --json
```

Check the request's `status` and `error`, and confirm an `enrich-source`
request exists for the work at all.

## Fix

**1. Inspect provider credentials and the recorded error.** DOI enrichment
(Crossref, OpenAlex, Unpaywall) reads `OPENALEX_API_KEY` and `NCBI_EMAIL` from
the local runtime environment. `OPENALEX_API_KEY` is enhancing: without it,
OpenAlex still runs in keyless polite-pool mode and reports a notice. `NCBI_EMAIL`
is an identity value, while Semantic Scholar is optional and only called when
`SEMANTIC_SCHOLAR_API_KEY` is present. Use `memoria secrets list` to inspect
credential status, then follow the request's exact provider error rather than
assuming that an absent OpenAlex key caused the failure. See [External
integrations → Credentials and keyless behavior](../../reference/evidence-and-integrations/integrations.md#credentials-and-keyless-behavior).

**2. Rerun enrichment.**

```bash
memoria work enrich --workspace <workspace> <work-id>
```

If the prior request is `failed`, fix the provider/input problem first, then
retry with `memoria request retry --workspace <workspace> <request-id>`
instead of enriching again from scratch.

## Verify

- The DOI source is checked, not unchecked.
- Any provider-derived metadata or full text expected for the source is present.

## Classify separately

`research_area` and `methodology` are PI-owned Work classifications, not
enrichment output. Set or revise them deliberately with `memoria work update`:

```bash
memoria work update --workspace <workspace> <work-id> --research-area <term>
memoria work update --workspace <workspace> <work-id> --methodology <term>
```

There is no classification-attention lifecycle to wait for or clear.

## Related

- Credentials and keyless behavior: [External integrations](../../reference/evidence-and-integrations/integrations.md#credentials-and-keyless-behavior)
- Request commands: [CLI](../../reference/commands-and-transports/cli.md)
- Failure catalog: [Failure modes](../../reference/system/failure-modes.md)
