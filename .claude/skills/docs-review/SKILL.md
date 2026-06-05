---
name: docs-review
description: Review the Memoria docs/ site for Diátaxis-quadrant fit, link integrity, indexing/nav_order, and terminology compliance. Use when adding or changing docs/ pages, or auditing the docs site before a release.
---

# docs-review

Review `docs/` against this repo's conventions (the authority is [AGENTS.md](../../../AGENTS.md) §8). Report findings grouped by severity; fix only when asked.

## 1. Diátaxis quadrant fit

Every page sits in exactly one quadrant. Apply the test: would a reader come here to *do*, *learn*, *look up*, or *understand*?

- `docs/tutorials/` — learn by doing. No reference tables, no rationale.
- `docs/how-to-guides/` — accomplish a task. No conceptual background. Titles are **concise** (no "How to …" prefix), matching the filename + README link text.
- `docs/reference/` — exact values/schemas/commands. No instructional steps.
- `docs/explanation/` — why it's designed this way. No step-by-step, no lookup tables.

Flag any mixed-quadrant page — it should be split.

## 2. Links

- `docs/` → docs/ links are **relative**. `vault/` → docs links are **absolute** website URLs.
- Run the checkers and report failures:
  - `python scripts/docs-doctor.py docs`
  - `bash scripts/check-vault-links.sh`
- Spot filename-style link text (visible text restates the target filename) — link text should be the page title.

## 3. Indexing & ordering

- Every page is in its section `README.md`; every how-to is also in the guide map in `how-to-guides/README.md`.
- Every page has a `nav_order` so the folder reads top-to-bottom logically; the README child-table order matches the sidebar order.
- New subsections have a `README.md` with `parent`, `has_children: true`, and an explicit `permalink`.
- Section READMEs are thin navigation hubs (intro + child table + optional "where next"), not article-length prose.

## 4. Terminology

- The two flows are **Compile** (knowledge in) and **Compose** (knowledge out); the pair is **the knowledge cycle**. `discuss` (Compile) and `sketch` (Compose) are the reflective phases.
- **Never** "upstream/downstream pipeline" or "the two pipelines" for the flows. `pipeline`/`upstream`/`downstream` are fine in other senses (ingest pipeline, Pandoc export, upstream dep).
- New citations: add an ACM author-date entry with an anchor in `reference/bibliography.md` and link to it.

## Output

A findings list grouped Critical / Major / Minor, each with file:line and the quadrant/link/index/terminology rule it violates. Then a one-line summary of the checker results.
