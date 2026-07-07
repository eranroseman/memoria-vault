---
title: "Tutorial 02: Bring in your first source"
parent: Tutorials
nav_order: 2
---

# Tutorial 02: Bring in your first source

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

**3. Inspect the Work record.**

Use the `work_id` from the JSON output:

```bash
memoria work export --workspace . <work-id>
```

Look for `check_status`, `content_path`, `raw_path`, and hash fields. Those are
the provenance anchors the rest of the system reads.

**4. Compile a digest when the source is ready.**

```bash
memoria work digest --workspace . <work-id> --mode test
```

The digest path uses the manifest-pinned runner for the selected mode. Use
`--mode live` only after provider config and the seeded-error gate support it.

## What you should have seen

- Capture enters through the request/worker path.
- Source bytes and normalized text are blobs, not frontmatter.
- A digest is source-derived material keyed by `work_id`.

Next: [Build notes and connect them](03-build-claims-and-connect-them.md).
