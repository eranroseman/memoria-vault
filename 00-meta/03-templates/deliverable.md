# `deliverable` template

Finished, submission-ready artifact — a manuscript, presentation, media asset, or release. Lives in `50-deliverables/`. Terminal state; never edited in place after submission.

## Frontmatter

```yaml
---
title: ""
type: deliverable
lifecycle: current
project: ""
output_kind: manuscript       # manuscript | presentation | poster | infographic | web | release
export_path: ""
related_draft: ""
sources: []                   # additional wikilinks the deliverable derived from (claim notes, code notes, etc.)
design_system: ""             # which 00-meta/04-reference/design-system.md was active during render (open-design-rendered artifacts only)
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

Filing by `output_kind`: `manuscript` → `01-manuscripts/`; `presentation` / `poster` → `02-presentations/`; `infographic` / `web` → `03-media/`; `release` → `04-releases/`. "Export" is the Pandoc step that drops the rendered file into one of these — not a folder.
