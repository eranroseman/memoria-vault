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

- A checked project Concept under `knowledge/projects/`
- A `thesis` value on the project that points at a checked note
- Checked notes linked with `supports`, `contradicts`, or `extends`

## Steps

**1. Open Memoria Inspector.**

Use the Inspector control panel. Worker actions enqueue jobs only; the plugin
does not edit Concepts or generated projections directly.

**2. Enter the project path.**

Use either form accepted by the worker:

```text
my-project
knowledge/projects/my-project.md
knowledge/projects/my-project/project.md
```

A bare slug resolves to `knowledge/projects/<slug>/project.md` when that nested
project note exists, otherwise to `knowledge/projects/<slug>.md`.

**3. Queue the analysis.**

Click **Analyze project**. The worker returns the argument-health payload:
relation counts, current stage, saturation, gaps or advisories, and the checked
nodes and edges it followed.

**4. Render the Canvas when useful.**

Click **Render canvas** with the same project path. The worker writes a generated
projection at:

```text
knowledge/projects/<project>/argument.canvas
```

Do not edit the generated Canvas as source. Edit the checked project and notes,
then render it again.

## Verify

- The project path is under `knowledge/projects/`
- The project `thesis` resolves to a checked note
- The generated Canvas appears beside the project and can be regenerated

## Related

- Link the checked notes first: [Link checked notes](../knowledge/link-related-claims.md)
- Operation contract: [System actions](../../reference/system-actions.md)
- Project type: [Document types](../../reference/document-types.md)
