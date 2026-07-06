---
title: Fix empty enrichment after ingest
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 5
---

# Fix empty enrichment after ingest

**Symptom:** a source is captured and staged, but Work metadata never fills in
— `research_area`/`methodology` stay empty, classification attention never
appears, and the DOI source stays unchecked.

**Diagnosis:** enrichment (`enrich-source`) either didn't run or failed before
producing a checked result. The two common causes:

1. A required provider key/contact email is missing or invalid, so provider
   calls fail.
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

**1. Check provider config.** DOI enrichment (Crossref, OpenAlex, Unpaywall)
reads `OPENALEX_API_KEY` and `NCBI_EMAIL` from the workspace runtime
environment, declared in `<workspace>/.memoria/config/providers.yaml`; Semantic
Scholar is optional and only called when `SEMANTIC_SCHOLAR_API_KEY` is present.
Confirm these are set — see [Set up Zotero → API keys for enrichment](../setup/set-up-zotero.md#api-keys-for-enrichment).

**2. Rerun enrichment.**

```bash
memoria work enrich --workspace <workspace> <work-id>
```

If the prior request is `failed`, fix the provider/input problem first, then
retry with `memoria request retry --workspace <workspace> <request-id>`
instead of enriching again from scratch.

## Verify

- `memoria work export --workspace . <work-id>` shows populated
  `research_area`/`methodology`.
- The DOI source is checked, not unchecked.
- The classification attention item (if one existed) is gone from
  `memoria attention list`.

## Related

- API keys and rate limits: [External integrations](../../reference/integrations.md#api-keys-and-rate-limits)
- Request commands: [CLI](../../reference/cli.md)
- Failure catalog: [Failure modes](../../reference/failure-modes.md)
