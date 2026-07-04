
name: docs-review
description: >
  Comprehensive audit of the Memoria `docs/` site against Diátaxis quadrant fit,
  link integrity, indexing/nav_order, and terminology compliance. Also performs
  cross-file contradiction, duplication, and implementation-gap analysis across
  `memoria-vault/`. Use when adding or changing `docs/` pages, auditing before a
  release, or writing new documentation.
triggers:

- adding or modifying docs/ pages
- pre-release docs audit
- writing new documentation
- reviewing memoria-vault/ for consistency
authority: AGENTS.md §8
output_destination: chat

---

# docs-review

Review `docs/` and `memoria-vault/` against this repo's conventions. The authority
is [AGENTS.md §8](../../../AGENTS.md). **Report findings grouped by severity; fix
only when explicitly asked.**

---

## Inputs

| Parameter | Type | Required | Description |
|---|---|---|---|
| `target` | path | no | Scope the review to a specific folder (default: full `docs/` + `memoria-vault/`) |
| `fix` | bool | no | If `true`, apply safe mechanical fixes (default: `false`) |
| `chat_output` | bool | no | Write findings directly to chat (default: `true`) |

---

## Steps

### Step 1 — Diátaxis Quadrant Fit

Every page sits in exactly one quadrant. Apply the test: would a reader come here
to *do*, *learn*, *look up*, or *understand*?

| Quadrant | Folder | Answers |
|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" |
| How-to | `docs/how-to-guides/` | "How do I accomplish X?" |
| Reference | `docs/reference/` | "What is the exact value/command?" |
| Explanation | `docs/explanation/` | "Why is it designed this way?" |

Rules:

- `docs/tutorials/` — learn by doing; no reference tables, no rationale.
- `docs/how-to-guides/` — accomplish a task; no conceptual background; titles are
  **concise** (no "How to …" prefix), matching the filename + README link text.
- `docs/reference/` — exact values/schemas/commands; no instructional steps.
- `docs/explanation/` — why it's designed this way; no step-by-step, no lookup tables.

Flag any mixed-quadrant page — it should be split.

---

### Step 2 — Link Integrity

- `docs/` → `docs/` links are **relative**.
- `vault/` → `docs/` links are **absolute** website URLs
  (`https://eranroseman.github.io/memoria-vault/…`).
- Links from `docs/` to non-doc files under `vault/` or `scripts/` use
  **GitHub blob URLs** (`https://github.com/eranroseman/memoria-vault/blob/main/…`).
- **No relative links** between `docs/` and `vault/`.

Run the checkers and report all failures:

```bash
python scripts/docs-doctor.py docs
bash scripts/check-vault-links.sh
```

Flag any link whose visible text restates the target filename — link text should
be the page title, not the slug.

---

### Step 3 — Indexing & Ordering

- Every page appears in its section `README.md`; every how-to is also in the guide
  map in `how-to-guides/README.md`.
- Every page has a `nav_order` so the folder reads top-to-bottom logically; the
  README child-table order matches the sidebar order.
- New subsections have a `README.md` with `parent`, `has_children: true`, and an
  explicit `permalink`.
- Section READMEs are thin navigation hubs (intro + child table + optional
  "where next"), not article-length prose.

---

### Step 4 — Terminology Compliance

- The two flows are **Compile** (knowledge in) and **Compose** (knowledge out);
  the pair is **the knowledge cycle**. `discuss` (Compile) and `sketch` (Compose)
  are the reflective phases.
- **Never** "upstream/downstream pipeline" or "the two pipelines" for the flows.
  `pipeline` / `upstream` / `downstream` are fine in other senses (ingest pipeline,
  Pandoc export, upstream dep).
- New citations: add an ACM author-date entry with an anchor in
  `reference/bibliography.md` and link in-text mentions to it.

---

### Step 5 — Contradiction Scan (`memoria-vault/`)

Scan **all files** in `memoria-vault/`. Treat this as a fresh analysis — do not
carry over prior findings.

For each contradiction or inconsistency (including subtle cross-document ones):

- Cite the relevant files and line/section.
- Explain the reasoning.

Priority: **high** — consistency across this vault is a core invariant.

---

### Step 6 — Duplication Scan (`memoria-vault/`)

Scan **all files** in `memoria-vault/`. Treat this as a fresh analysis.

For each duplicated or near-duplicated passage (including paraphrased restatements):

- Cite the relevant files and line/section.
- Identify the canonical source and the redundant copy.

Goal: single source of truth.

---

### Step 7 — Implementation Documentation Gaps (`memoria-vault/`)

Scan **all files** in `memoria-vault/`. Treat this as a fresh analysis.

Flag every topic, workflow, or component that is referenced or implied but not
fully documented. For each gap, propose:

- A title for the missing doc.
- A one-sentence scope statement.

---

### Step 8 — Related-Pages Audit (`docs/`)

For each file in `docs/`:

1. Identify **only** truly related pages (strong semantic or explicit connections).
2. Exclude weak or tangential pages.
3. Rank related pages by relevance (most relevant first).

Compare findings to existing `related:` sections. Report **only meaningful differences**:

- Missing links → add
- Incorrect links → remove
- Wrong order → reorder

Only include files with actionable changes.

---

### Step 9 — Diátaxis Deep Audit (`docs/`)

Analyze all files in `docs/` for alignment with Diátaxis based on their folder.

For each file:

- Identify the expected quadrant type.
- Assess actual alignment.
- Flag issues with a concise, per-file edit recommendation.

Use subagents to parallelize per-folder work. Summarize findings in a single
consolidated report.

---

### Step 10 — Complex Edit Audit (`memoria-vault/`)

Spawn one subagent per folder:

```
memoria-vault/docs/explanation/
memoria-vault/docs/how-to/
memoria-vault/docs/project/
memoria-vault/docs/reference/
memoria-vault/docs/tutorials/
```

Plus one agent per root-level folder. Each agent analyzes only its assigned
folder (including nested files).

Each agent produces a markdown table:

| Issue Type | Severity | File | Line/Section | Finding | Suggested Fix |
|---|---|---|---|---|---|

Audit checklist per agent:

1. Duplicate or near-duplicate content, including paraphrased restatements.
2. Contradictions, including subtle inconsistencies.
3. Overloaded terms used in conflicting contexts.
4. Overused words/phrases — list top 15 non-structural terms and suggest alternatives.
5. Claims about Hermes, Obsidian, Zotero, plugins, skills, or third-party components
   that conflict with documented behavior.
6. Undefined terms — propose concise definitions aligned with current usage.
7. Dead wikilinks or embeds — suggest correct target or removal.
8. Design conformance — verify `vault/` matches the design in `docs/`; flag every
   deviation and cite the defining doc.
9. External links — flag each as essential or candidate for removal/internalization.
10. Missing links — flag every reference to a doc or section that doesn't exist.
11. Missing metadata — flag every file missing required frontmatter fields.
12. Missing content — flag unreferenced but implied topics; propose title + scope.
13. Missing or outdated diagrams, code snippets, CLI examples.
14. No relative links between `docs/` and `vault/`; any cross-boundary reference
    must link to GitHub (`https://github.com/eranroseman/memoria-vault`).
15. Verbose passages — suggest concise rewrites that preserve meaning.
16. Content flow — suggest reordering for clearer progression.
17. Cross-file organization — propose a folder/file map with rationale.
18. Naming — use kebab-case for all files and folders.
19. Terminology consistency — flag inconsistent names, stages, statuses, domain terms.
20. Unclear ownership — flag workflow steps with ambiguous responsibility or scope.
21. Relative links only inside `docs/` and `vault/`; flag any absolute
    `memoria-vault/` paths and replace with relative paths.

After all folder-level analyses, produce a **cross-folder summary table** with
prioritized recommendations — output directly to **chat**.

---

### Step 11 — Writing New Docs (Reference)

When writing or scaffolding new documentation, apply these conventions:

#### Diátaxis routing

| Quadrant | Folder | Answers |
|---|---|---|
| Tutorial | `docs/tutorials/` | "How do I learn X by doing it?" |
| How-to | `docs/how-to-guides/` | "How do I accomplish X?" |
| Reference | `docs/reference/` | "What is the exact value/command?" |
| Explanation | `docs/explanation/` | "Why is it designed this way?" |

#### Links

- `docs/` files → relative links for intra-`docs/` targets.
- ADRs → `docs/adr/` (relative); design notes → `docs/design/` (relative);
  release plans → `docs/releasing/` (relative); test plans → `docs/testing/` (relative).
- `vault/` or `scripts/` references from `docs/` → GitHub blob URLs.

#### Indexing

- Add every new page to its section README and assign a logical `nav_order`.
- How-to pages also appear in `how-to-guides/README.md`.
- How-to titles: concise, no "How to…" prefix; match README link text and filename.

#### Citations

- New works → `reference/bibliography.md` (ACM author-date, `<a id="…"></a>` anchor).
- In-text: link to `[bibliography.md#anchor](../reference/bibliography.md#anchor)`.

#### ADR template (`docs/adr/`)

ADRs are the **single home for every decision** at any lifecycle status — no
separate proposals/RFC folder. An open proposal is an ADR with
`status: proposed` or `deferred`; revisited each release cycle, never gated on a
static trigger. Full template in [`docs/adr/_template.md`](docs/adr/_template.md).

```markdown
***
topic: decisions
id: <NN>
title: <Short title>
status: proposed | accepted | deferred | rejected | superseded
date_proposed: YYYY-MM-DD
date_resolved: YYYY-MM-DD
assumes: []
supersedes: []
superseded_by: []
# deferred/proposed: nav_exclude: true
***

# ADR-<NN>: <Title>

## Context
## Decision
## Consequences
## When this matters   # deferred/proposed only
## Alternatives considered
```

Background design analysis lives in `docs/design/`, not in the ADR itself.

#### Release plans (`docs/releasing/`)

One file per version, copied from `docs/releasing/release-plan-template.md`.
Contains durable **prose** (what/why, gate rationale). Readiness **state** lives
only in the "Release vX.Y" tracking issue; scope in the milestone;
version/CHANGELOG/Release in release-please — **never restated in the plan**.
Build gaps → GitHub issues; scope cuts → `deferred`-status ADR in `docs/adr/`.

---

## Output Format (to Chat)

```
## Findings

### Critical
- `<file>:<line>` — [rule] <description>

### Major
- `<file>:<line>` — [rule] <description>

### Minor
- `<file>:<line>` — [rule] <description>

## Checker Results
<one-line summary of docs-doctor.py and check-vault-links.sh output>
```

All findings are output directly to **chat** — no file writing unless explicitly requested.
