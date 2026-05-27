# `code-note` template

Documents scripts, notebooks (Jupyter and others), pipelines, and code artifacts. Lives in `40-workbench/03-code/`. Shared ownership: agent or human creates; human or coding agent develops.

## Frontmatter

```yaml
---
title: ""
type: code-note
repo: ""
language: ""
format: script           # script | notebook | pipeline | module | config
status: active
purpose: ""
related_sources: []
related_projects: []
moc: []
schema_version: 1
created:
updated:
---
```

## Body

```md
# Purpose
What this code does and why it exists.

# Design
- Architecture.
- Inputs and outputs.
- Dependencies.

# Provenance
- What literature or project question motivated it.
- Which notes connect to it.

# Usage
- How to run it.
- Known limitations.
- Next steps.
```

## Notes

### Jupyter notebooks

Notebooks are treated as a `code-note` with `format: notebook`. The notebook file itself (`.ipynb`) lives alongside the markdown note in `40-workbench/03-code/`. The markdown note carries the same provenance, purpose, and links as any other code note; the notebook holds the executable artifact.

Don't fragment by creating a separate `notebook-note` type — the discipline is the same (provenance, purpose, motivating literature), only the file format differs.
