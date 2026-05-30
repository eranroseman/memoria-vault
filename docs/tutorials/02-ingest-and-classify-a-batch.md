---
topic: tutorials
---

# Tutorial: Ingest and classify a batch

By the end you will have 5–10 sources in `20-sources/01-papers/`, each classified into canonical metadata, and the first `[!brief]` comparative reads with a real corpus to compare against.

> **Status.** See [implementation status](../project/implementation-status.md).

**Prerequisite:** [Tutorial 01](01-set-up-from-zero.md) complete (vault open, Librarian installed, Zotero + Better BibTeX wired).

## Steps

1. **Add the batch to Zotero.** Drag 5–10 PDFs in. Better BibTeX assigns each a citekey; note them (or export `library.bib` and read the keys).
2. **Ingest each source.** For every citekey:

   ```bash
   hermes -p memoria-librarian run llm-wiki ingest --source <citekey>
   ```

   Each run creates a `paper-note` at `lifecycle: proposed` with `_proposed_classification`, enriches via OpenAlex/Crossref, and (for OA PDFs) extracts text to `90-assets/extracts/`. See [workflows/upstream/ingest.md](../how-to/workflows/upstream/ingest.md).
3. **Classify each note.** Open each paper-note, review `_proposed_classification`, promote the fields you agree with into the main YAML, delete the proposed block, and set `lifecycle: current` + `triage_completed`. See [workflows/upstream/classify.md](../how-to/workflows/upstream/classify.md).
4. **Watch the `[!brief]` callouts fill in.** Once 5+ sources share topics, the Mapper's comparative read has a corpus to compare against — re-open an earlier paper-note to see real comparisons.

## What to check

- [`reading-pipeline`](../explanation/dashboards/reading-pipeline.md) shows the batch moving from `proposed` to `current`.
- The audit log records one `allow_with_log` write per note.

## Next

- [Tutorial 03 — Run the Linter](03-run-the-linter.md) to check the batch for structural issues.
