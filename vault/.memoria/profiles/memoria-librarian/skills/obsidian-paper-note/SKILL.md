---
name: obsidian-paper-note
description: "Create a populated paper-note in the vault from a Zotero citekey — Zotero metadata + PDF extraction → 20-sources/01-papers/<citekey>.md, with an agent classification proposal."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Zotero, Obsidian, Ingest, Literature]
    related_skills: [pyzotero, ocr-and-documents, obsidian, paper-lookup]
---

# obsidian-paper-note

The Librarian's ingest pipeline: turn a Zotero citekey into a populated paper-note in
`20-sources/01-papers/<citekey>.md`. Composes existing skills — `pyzotero` (metadata),
`ocr-and-documents` (PDF → markdown), `obsidian` (vault write) — and seeds the agent's
`_proposed_classification`. **Deterministic except the one classification-proposal step.**

## Inputs

- `citekey` (required) — Better BibTeX citekey of the Zotero item (resolves in `.memoria/library.bib`).
- `--skip-enrichment` (optional) — write the note from Zotero metadata only; defer API enrichment.
- `--dry-run` (optional) — report the note path + fields that would be written; write nothing.

## Procedure

1. **Resolve the item.** Look up `citekey` in `.memoria/library.bib` (Better BibTeX export); use `pyzotero` for the full item record (authors, year, DOI, journal, attachments).
2. **Extract the PDF.** If the item has a PDF attachment, run `ocr-and-documents` (Marker) → write `90-assets/extracts/<citekey>.md`; set `extract_path` to that vault-relative path. If no PDF or extraction fails, continue with an empty extract and leave `extract_path` blank (do **not** abort the ingest).
3. **Build frontmatter** from the `00-meta/03-templates/paper-note.md` template: populate `title`, `authors`, `year`, `citekey`, `doi`, `url`, `zotero_uri`, `pdf_uri`, stable IDs; set `created`/`updated` to now; `lifecycle: proposed`; `pub_status` from the item; leave the human-owned classification fields (`study_design`, `methods`, `topic`, `moc`, `projects`) **empty**.
4. **Propose classification.** Fill the `_proposed_classification:` YAML namespace (`study_design`, `methods`, `topic`) from abstract + metadata — values must come from the controlled vocabularies in `00-meta/04-reference/`. This is the single non-deterministic step; the human promotes fields at triage.
5. **Enrich** (unless `--skip-enrichment`): fill the `_enrichment:` namespace (citation metrics, taxonomy, discovery) via API calls; promote stable IDs (DOI, OpenAlex ID) to main frontmatter; set top-level `enriched_date`.
6. **Write** to `20-sources/01-papers/<citekey>.md` via the `obsidian` skill. **Never overwrite an existing note** — if one exists, append a `## New import` section instead. **Never overwrite human-set frontmatter.**
7. **Log** the action (citekey, path, timestamp) to `00-meta/02-logs/`.

## Rules

- Use the `obsidian` skill for all vault reads/writes — not shell heredocs.
- The PDF lives in Zotero, not the vault; only the Marker extract is stored (`90-assets/extracts/`).
- Stable identifiers go in main frontmatter; derived metrics and taxonomy stay in `_enrichment`.
- All writes route through the policy gate (lane-override allows `10-inbox/**` + `20-sources/**`).
