---
title: Safe mode
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 1
---

# Safe mode

Use safe mode when optional UI adapters, scheduled jobs, or provider-backed
steps are unavailable. The rule is simple: use the standalone `memoria` CLI and
Git directly.

## Capture Or Import

```bash
memoria work capture --workspace <workspace> --doi <doi>
memoria work import --workspace <workspace> --format bibtex --file sources.bib
```

If enrichment providers are unavailable, keep the work unchecked and rerun
`memoria work enrich --work-id <id>` when provider inputs are available.

## Review And Triage

```bash
memoria attention list --workspace <workspace>
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
```

Do not bulk-accept proposed notes or attention cards. Anything `proposed` still
requires human review.

## Export A Draft

```bash
memoria project export --workspace <workspace> knowledge/projects/<project>/project.md \
  --format docx --output /tmp/output.docx
```

If the export command is blocked by missing Pandoc or citation tooling, use
Pandoc directly after verifying `references.bib`.

## Quick System Check

```bash
memoria doctor bundle --workspace <workspace>
memoria workspace rebuild --workspace <workspace> --search
git -C <workspace> status --short
```

## Related

- Return-to-work checklist: [Return to work](../inbox/return-to-work.md)
- Fix stuck request: [Fix a stuck card](fix-stuck-card.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
