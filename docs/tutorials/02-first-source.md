---
title: "02: First source"
parent: Tutorials
nav_order: 2
---

# 02: First source

This tutorial captures one local text file so the first source path works
without network or reference-manager setup.

## Steps

**1. Create a tiny source file.**

```bash
mkdir -p tmp/tutorial
printf 'A short source about just-in-time adaptive interventions.\n' > tmp/tutorial/first-source.txt
```

**2. Add it as a Work.**

```bash
memoria work add --workspace . \
  --file tmp/tutorial/first-source.txt \
  --title "First tutorial source" \
  --json
```

The command creates a worker request, writes a catalog row, stores source blobs
under `.memoria/blobs/source-content/`, and journals the capture. It does not
create a legacy source-note Markdown file.
In the JSON output, notice the `work_id`. You will use that stable ID in the
next command.

**3. Inspect the Work record.**

Use the `work_id` from the JSON output:

```bash
memoria work export --workspace . <work-id> --json
```

Look for `check_status`, `content_path`, `raw_path`, and hash fields. Those are
the provenance anchors the rest of the system reads.
The paths should point under `.memoria/blobs/source-content/`.

**4. Check the Work after reviewing it.**

The local-file capture starts unchecked. After inspecting the exported record
and source text, record the PI decision that makes it available to checked-read
operations:

```bash
memoria work update --workspace . <work-id> --check-status checked
```

**5. Compile a digest when the source is ready.**

```bash
memoria work digest --workspace . <work-id> --mode test
```

The digest path uses the manifest-pinned runner for the selected mode. Use
`--mode live` only after provider config and the seeded-error gate support it.
Notice the digest path or request result. The digest is the first source-derived
artifact you can inspect.

## What you should have seen

- Capture enters through the request/worker path.
- Source bytes and normalized text are blobs, not frontmatter.
- A captured Work remains unchecked until the PI checks it.
- A digest is source-derived material keyed by `work_id`.

For more detail on capturing sources by DOI, URL, or PDF (skipped here for
simplicity): [Capture and ingest](../how-to-guides/library/capture-and-ingest.md).

Next: [03: Connect notes](03-connect-notes.md).
