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

## Steps

**1. Capture or import without adapters.**

```bash
memoria work add --workspace <workspace> --doi <doi>
memoria work import --workspace <workspace> --format bibtex --file sources.bib
```

If enrichment providers are unavailable, keep the work unchecked and rerun
`memoria work enrich <id>` when provider inputs are available.

**2. Review and triage from the terminal.**

```bash
memoria attention list --workspace <workspace>
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
```

Do not bulk-accept proposed notes or attention items. Anything `proposed` still
requires human review.

**3. Export a draft from the terminal.**

```bash
memoria project export --workspace <workspace> projects/<project>/project.md \
  --format docx --output /tmp/output.docx
```

If the export command is blocked by missing Pandoc or citation tooling, use
Pandoc directly after verifying `bibliography.bib`.

**4. Run a quick system check.**

```bash
memoria doctor bundle --workspace <workspace>
memoria workspace rebuild --workspace <workspace> --search
git -C <workspace> status --short
```

## Verify

- The task you needed is complete through CLI/Git without adapter state
- `git -C <workspace> status --short` shows only changes you expect
- Any deferred provider-backed work has an open request or attention item you can return to later

## Related

- Return-to-work checklist: [Return to work](../inbox/return-to-work.md)
- Fix stuck request: [Fix a stuck request](fix-stuck-card.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
