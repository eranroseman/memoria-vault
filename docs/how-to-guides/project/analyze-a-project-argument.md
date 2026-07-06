---
title: Analyze a project argument
parent: Project
grand_parent: How-to guides
nav_order: 1
---

# Analyze a project argument

Run the checked-note project argument analysis, then optionally render the
argument Canvas projection beside the project.

## Prerequisites

- A checked project Concept under `projects/`
- A `thesis` value on the project that points at a checked note
- Checked notes linked with `supports`, `contradicts`, or `extends`

## Steps

**1. Run the analysis from the CLI.**

Worker actions start from SQLite requests owned by the `memoria` CLI. If the
project does not exist yet, author a checked project Concept under
`projects/`, then run `memoria workspace scan --workspace <vault>`.

**2. Enter the project path.**

Use either form accepted by the worker:

```text
my-project
projects/my-project.md
projects/my-project/project.md
```

A bare slug resolves to `projects/<slug>/project.md` when that nested
project note exists, otherwise to `projects/<slug>.md`.

**3. Run the analysis.**

```bash
memoria project trace --workspace <vault> projects/my-project/project.md
```

The worker returns the argument-health payload:
relation counts, current stage, saturation, gaps or advisories, and the checked
nodes and edges it followed.

**4. Render the Canvas when useful.**

Run export with the same project path when a generated output is useful:

```bash
memoria project export --workspace <vault> projects/my-project/project.md
```

The worker writes generated project output beside the project, including:

```text
projects/<project>/argument.canvas
```

Do not edit the generated Canvas as source. Edit the checked project and notes,
then render it again.

## Verify

- The project path is under `projects/`
- The project `thesis` resolves to a checked note
- The generated Canvas appears beside the project and can be regenerated

## Related

- Link the checked notes first: [Link checked notes](../knowledge/link-checked-notes.md)
- Operation contract: [System actions](../../reference/system-actions.md)
- Project type: [Document types](../../reference/document-types.md)
