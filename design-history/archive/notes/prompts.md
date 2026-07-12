---
name: docs-review
description: Review the Memoria docs/ site for Diátaxis-quadrant fit, link integrity, indexing/nav_order, and terminology compliance. Use when adding or changing docs/ pages, or auditing the docs site before a release.
---

# docs-review

Review `docs/` against this repo's conventions (the authority is [AGENTS.md — working guidelines for AI agents in this repo](../../../AGENTS.md) §8). Report findings grouped by severity; fix only when asked.

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


## Output

A findings list grouped Critical / Major / Minor, each with file:line and the quadrant/link/index/terminology rule it violates. Then a one-line summary of the checker results.

## Contradictions

Scan all files in memoria-vault/ and identify contradictions or inconsistencies — including subtle ones across documents. Treat this as a fresh analysis: do not reference or carry over any prior findings. For each issue found, cite the relevant files and explain your reasoning. Be thorough and systematic; consistency across this vault is a high-priority concern.

## Duplications

Scan all files in memoria-vault/ and identify duplicated content — including subtle ones across documents. Treat this as a fresh analysis: do not reference or carry over any prior findings. For each issue found, cite the relevant files and explain your reasoning. Be thorough and systematic; single source of truth across this vault is a high-priority concern.

## Implementation documentaion gaps

Scan all files in memoria-vault/ and identify Implementation documentaion gaps — including subtle ones across documents. Treat this as a fresh analysis: do not reference or carry over any prior findings. For each issue found, cite the relevant files and explain your reasoning. Be thorough and systematic; single source of truth across this vault is a high-priority concern.

## Related

Analyze all files in docs/ to identify page-level relationships. For each file:

1. Scan content and identify ONLY truly related pages (strong semantic/explicit connections)
2. Exclude weak or unrelated pages
3. Rank related pages by relevance (most relevant first)

Compare findings to existing "related" sections and report ONLY meaningful differences:

- Missing links (add)
- Incorrect links (remove)
- Wrong order (reorder)

Only include files with changes.

## diataxis

Analyze all files in docs/explanation docs/how-to-guides docs/tutorials docs/reference for alignment with Diátaxis based on their folder, and readme.md based on best practice for index page. For each file: Identify expected type, Assess alignment, Flag issues. Use subagents to parallelize the work. Summarize findings and produce a concise report with per-file actionable edit recommendations.

## Complex edit

Run one agent for each subfolder in memoria-vault\docs\explanation memoria-vault\docs\how-to memoria-vault\docs\project memoria-vault\docs\reference memoria-vault\docs\tutorials and one for each root folder. Each agent analyzes only its assigned folder, including nested files.

For each folder, analyze the content and produce a markdown table with columns:
Issue Type | Severity (Critical/High/Medium) | File | Line/Section | Finding | Suggested Fix

Analyze the content of memoria-vault/ and produce a markdown table with columns and provide prioritized recommendations. Save your work to reports/

Issue Type | Severity (Critical/High/Medium) | File | Line/Section | Finding | Suggested Fix

Audit:

1. Duplicate or near-duplicate content, including paraphrased restatements.
2. Contradictions, including subtle inconsistencies.
3. Overloaded terms used in conflicting contexts.
4. Overused words or phrases; list the top 15 non-structural terms and suggest alternatives.
5. Claims about Hermes, Obsidian, Zotero, plugins, skills, or other third-party components that conflict with documented behavior.
6. Undefined terms that should be added to a central glossary; propose concise definitions aligned with current usage.
7. Dead wikilinks or embeds; suggest the correct target or removal.
8. Design conformance: verify that memoria-vault\vault matches the design specified in memoria-vault/docs; flag every deviation and cite the defining doc.
9. External links; note whether each is essential or a candidate for removal/internalization.
10. Missing links; flag every reference to a doc or section that doesn't exist.
11. Missing metadata; flag every file missing any of the required frontmatter fields.
12. Missing content; identify topics or workflows that are referenced or implied but not fully documented, and propose a title plus brief scope for each missing doc.
13. Missing or outdated diagrams, code snippets, and CLI examples; flag every reference that doesn't exist or is outdated.

Improvements: 15. Verbose passages; suggest concise rewrites that preserve meaning. 16. Content flow; suggest reordering for clearer progression. 17. Cross-file organization; propose a folder/file map with rationale. 18. Naming; use kebab-case for all files and folders. 19. Terminology consistency; flag inconsistent names, stages, statuses, and domain terms. 20. Unclear ownership; flag workflow steps with ambiguous responsibility or scope. 21. Relative links only inside memoria-vault/docs and memoria-vault\vault; flag any absolute memoria-vault paths and replace with relative paths. 14. No relatives links between memoria-vault\docs and memoria-vault\vault. Any reference should be linked to the github <https://github.com/eranroseman/memoria-vault>

After all folder-level analyses, summarize the cross-folder patterns in one markdown table and provide prioritized recommendations. Save your work to reports/

## Writing docs

### Diátaxis quadrant routing

| Quadrant | Folder | Answers |
|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" |
| How-to | `docs/how-to-guides/` | "How do I accomplish X?" |
| Reference | `docs/reference/` | "What is the exact value/command?" |
| Explanation | `docs/explanation/` | "Why is it designed this way?" |

Mixed-quadrant pages are wrong — split them.

- **Links:** `docs/` files → relative links; `vault/` files → absolute website URLs (`https://eranroseman.github.io/memoria-vault/…`).
  - From `docs/`, cross-folder repo references follow the target: ADRs live under `docs/adr/` and design notes under `docs/design/`, so links to them are ordinary intra-`docs/` relative links; release plans (`docs/releasing/`) and test plans (`docs/testing/`) are ordinary intra-`docs/` relative links; links to non-doc files under `vault/` or `scripts/` use **GitHub blob URLs** (`https://github.com/eranroseman/memoria-vault/blob/main/…`), since those have no Pages route.
- **Indexing:** every new page goes in its section README; how-to pages also go in `how-to-guides/README.md`. Assign `nav_order` so the folder reads in logical sequence.
- **How-to titles:** concise, no "How to…" prefix; match the README link text and filename.
- **Citations:** new works go in `reference/bibliography.md` (ACM author-date, `<a id="…"></a>` anchor); link in-text mentions to `[bibliography.md#anchor](../reference/bibliography.md#anchor)`.

### ADR template (`docs/adr/`)

ADRs are the **single home for every decision, at any lifecycle status** — there is no
separate proposals/RFC folder. An open proposal is an ADR with `status: proposed` or
`deferred`; it is revisited each release cycle, never gated on a static adoption
trigger. Full template + nav fields in [`docs/adr/_template.md`](docs/adr/_template.md).

```markdown
---
topic: decisions
id: <NN>
title: <Short title>
status: proposed | accepted | deferred | rejected | superseded
date_proposed: YYYY-MM-DD
date_resolved: YYYY-MM-DD
assumes: []          # ADR/mechanism deps — so a change that invalidates this is detectable
supersedes: []
superseded_by: []
# deferred/proposed ADRs also carry: nav_exclude: true   (unlisted on the site until accepted)
---

# ADR-<NN>: <Title>

## Context
## Decision
## Consequences
## When this matters   # deferred/proposed only — priority context for the cadence review, NOT a gate
## Alternatives considered
```

Background design analysis that informs an ADR lives in [`docs/design/`](docs/design),
not in the ADR itself.

### Release plans (`docs/releasing/`)

One file per version, copied from `docs/releasing/release-plan-template.md` — the durable **prose** (what/why, gate rationale). Readiness **state** lives only in the **"Release vX.Y" tracking issue** (a gate checklist), scope in the milestone, and version/CHANGELOG/Release in release-please — never restated in the plan. `status-doctor` guards the plan against link/path/flag drift. Build gaps go to GitHub issues; scope cuts go to a `deferred`-status ADR in `docs/adr/`.
