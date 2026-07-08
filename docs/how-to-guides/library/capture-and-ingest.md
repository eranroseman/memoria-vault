---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
nav_order: 1
---

# Capture and ingest a source

Capture one source into the catalog so you can read, enrich, digest, and cite it
later.

## Prerequisites

- A working vault and `memoria` on your `PATH`
- A DOI, URL, local file, BibTeX file, or CSL JSON file for the source

## Steps

**1. Capture one source from the CLI.**

```bash
memoria work add --workspace <vault> --url https://example.test/source
```

Use `--doi <doi>` or `--file <path>` instead when that is the source you have.

**2. Import portable bibliographic files when you have a batch.**

Use `memoria work import --format bibtex|csl --file <path>` for portable
metadata:

```bash
memoria work import --workspace <vault> --format bibtex --file sources.bib
```

**3. Confirm the catalog row.**

Use JSON output or `memoria work export` to inspect the Work:

```bash
memoria work export --workspace <vault> <work-id>
```

Copy the `work_id`; you will use it for enrichment, digesting, citation, and
troubleshooting.

**4. Enrich or fix missing metadata.**

If provider evidence or full text is missing, finish the enrichment pass before
depending on the source in a checked note.

```bash
memoria work enrich --workspace <vault> <work-id>
```

## Verify

- `memoria work export --workspace <vault> <work-id>` returns the captured Work
- The Work has enough metadata and text for your next step
- Any attention item raised by capture or enrichment is resolved or deliberately deferred

## Related

- Pipeline details: [Ingest routing](../../reference/pipelines-and-io/ingest.md)
- Trusted writer: [System actions](../../reference/commands-and-transports/system-actions.md)
