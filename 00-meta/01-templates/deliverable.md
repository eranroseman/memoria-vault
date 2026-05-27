# `deliverable` template

Finished export — manuscript, slides, or submission-ready artifact. Lives in `50-deliverables/`. Terminal state; never edited in place after submission.

## Frontmatter

```yaml
---
title: ""
type: deliverable
status: final
project: ""
output_kind: manuscript       # manuscript | presentation | export | poster | infographic | web
export_path: ""
related_draft: ""
sources: []                   # additional wikilinks the deliverable derived from (claim notes, code notes, etc.)
design_system: ""             # which 00-meta/06-schema/design-system.md was active during render (open-design-rendered artifacts only)
render_command: ""            # exact command that produced the artifact (open-design-rendered artifacts only); blank for Pandoc/manual builds
exported_at:
schema_version: 1
created:
updated:
---
```

## Body

```md
# Summary
What was delivered, where, and when.

# Provenance
- Source draft: [[draft-x]]
- Build pipeline: [[code-note-y]]
- Bibliography: [[research-wiki-bib]]

# Notes
- Anything to remember about the submission, the venue, or post-submission state.
```

## Notes

Deliverables are terminal artifacts. If a draft needs revision after submission, create a new draft (with provenance back to the original) — don't mutate the deliverable.
