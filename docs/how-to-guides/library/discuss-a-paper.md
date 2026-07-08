---
title: Discuss a paper
parent: Library
grand_parent: How-to guides
nav_order: 2
---

# Discuss a paper

Work through a checked source before turning it into notes or synthesis.

## Prerequisites

- A checked Work row and acquired full text from [Capture and ingest a source](capture-and-ingest.md).
- A current search index.

## Steps

**1. Pick the work.**

Use the Work ID shown by capture or enrichment.

**2. Orient yourself first.**

Read the digest, provider metadata, and full-text extract. Bring a position, not
a blank page.

**3. Record the interview/takeaway.**

```bash
memoria work interview --workspace . <work-id> --response "<takeaway>"
```

Use the prompt to capture what the source argues, what it changes in your
project, what might falsify it, and where you stand.

**4. Compile or update the digest.**

```bash
memoria work digest --workspace . <work-id>
```

**5. Keep your own note if needed.**

Draft or edit a note under `notes/`, then run:

```bash
memoria workspace scan --workspace .
```

## Verify

- The interview or digest request is visible in `memoria request list --workspace .`.
- Durable takeaways are PI-authored notes, direct PI edits, or worker-owned
  digest/interview events.
- Unchecked material is not used by `memoria ask` or digest compilation.

## Related

- Capture and ingest a source: [Capture and ingest a source](capture-and-ingest.md)
- Query the vault: [Query the vault](../knowledge/query-the-vault.md)
- System actions: [System actions](../../reference/commands-and-transports/system-actions.md)
