---
title: "01: System tour"
parent: Tutorials
nav_order: 1
---

# 01: System tour

This first pass is read-only. You will inspect the workspace shape, the CLI
surface, and the checked-read boundary before adding research material.

## Prerequisites

- A fresh workspace from [Quickstart](../how-to-guides/setup/quickstart.md).
- A shell opened at the workspace root.
- The `memoria` command on `PATH`: activate the venv —
  `source .memoria/.venv/bin/activate` (Linux/macOS/WSL) or
  `.memoria\.venv\Scripts\Activate.ps1` (Windows) — or otherwise ensure
  `memoria` resolves before running the bare `memoria ...` commands below.

## Steps

**1. Confirm the runtime can see the workspace.**

```bash
memoria status --workspace .
memoria doctor bundle --workspace .
```

`status` is the quick health read. `doctor bundle` checks the local runtime and
prints the backup contract without requiring optional adapters.
Notice the workspace path and the absence of adapter requirements in the output.

**2. Rebuild the checked search projection.**

```bash
memoria workspace rebuild --workspace . --search
```

An empty index is normal in a new vault. The command is still useful because it
shows that checked-read projections are rebuilt by the engine, not by an editor
plugin.
Notice that the command completes even before you have added research material.

**3. Inspect the durable roots.**

```bash
ls notes hubs projects digests fulltexts .memoria
memoria list --workspace . --type note
memoria list --workspace . --type work --json
```

The durable file-backed Concept types are `note`, `hub`, `project`, `digest`,
and `fulltext`; `fulltexts/` is the `fulltext` folder. Source catalog state
lives in SQLite and blobs, not as source Markdown files.
Notice that `notes`, `hubs`, and `projects` are visible folders, while Work
records come from the runtime catalog. In a fresh vault, the Work command's
catalog-backed result is:

```json
{"api_version": "engine-read-api.v1", "concepts": [], "ok": true}
```

## What you should have seen

- The CLI is the product surface.
- The workspace is local and git-backed.
- Checked reads come from engine projections over checked Concepts and catalog rows.

Next: [02: First source](02-first-source.md).
