---
title: Archive distillation report
date: 2026-06-01
scope: All substantive files in _archived/ not yet documented in the current project
---

# Archive distillation report

**Scope.** Every non-trivial file in `_archived/` — predecessor design conversations
(`old/research-wiki-conv-*`), external repo analysis (`raw/Analyze the following repos…`),
Hermes capability assessments (`reports/hermes-*`), migration-draft ADR/reference/how-to files
(`reports/migration-drafts/`), predecessor vault templates and schema (`research-wiki/`), and
process docs (`Zettelkasten processes.md`, `The daily rhythm.md`).

**Method.** For each candidate finding, verified against current `docs/`, `vault/`, and
`project-files/` to confirm it is genuinely absent before recording it here.

**Status of prior salvage reports.** The five existing reports in `_archived/reports/`
(`raw-salvage-report`, `raw-harvest-findings`, `research-wiki-salvage-report`,
`hermes-capabilities-design-report`, `hermes-features-design-report`) concluded "zero
genuine architecture gaps in raw/." That finding holds — this report covers the *reference
and tooling* gaps the prior reports deferred as "low priority but worth a future note."

---

## Summary table

> **Disposition (2026-06-01).** All findings have now been integrated or dropped. The
> **Status** column below records where each one landed. Two findings were dropped after a
> full-tree re-verification (the original findings only grepped `docs/` and `project-files/`,
> missing `vault/`): **F1** was already shipped in the vault, and **F11** was already a member
> of ADR-16's deferred systematic-review cluster. No new PROPs or ADRs were needed — every
> live finding became a doc enrichment, a vault artifact, or a fold into the existing
> `schema-and-retrieval.md` proposal.

| # | Finding | Status | Landed in |
|---|---|---|---|
| 1 | Screening-protocol.md "not shipped" | **Dropped — already done** | `vault/00-meta/04-reference/screening-protocol.md` (current taxonomy) |
| 2 | Per-type enrichment staleness cadence | **Integrated** | `docs/reference/frontmatter.md` (mirrors the Linter SOUL authority) |
| 3 | Slug collision disambiguation rules | **Integrated** | `docs/reference/note-types.md` |
| 4 | Delegation ladder ASCII visual | **Integrated** | `docs/explanation/profiles/README.md` |
| 5 | PDF extraction alternatives | **Integrated** | `docs/reference/ingest.md` |
| 6 | Citation-format parser stack | **Integrated** | `docs/reference/ingest.md` |
| 7 | Vocabulary example artifact | **Shipped** | `vault/00-meta/04-reference/vocabulary-example.md` (+ index in on-disk-layout) |
| 8 | `vision_analyze` figure reading | **Folded + noted** | `schema-and-retrieval.md` §2 + `docs/reference/ingest.md` |
| 9 | Browser capability (discover) | **Integrated** | `docs/explanation/profiles/librarian.md` |
| 10 | Inciteful + reconciliation helpers | **Integrated** | `zotero-plugins.md` (Inciteful) + `ingest.md` (helpers) |
| 11 | Multi-reviewer screening mode | **Dropped — already covered** | ADR-16 (`review_mode: systematic-review` + dual-rater) |
| 12 | `uses-method` typed relation | **Folded** | `schema-and-retrieval.md` §1 |
| 13 | Terminology hazard table | **Reference-only** | this report (archive-reading aid; not promoted to glossary) |

---

## Finding 1 — Screening-protocol.md not shipped in the starter vault

**Priority: HIGH.**

The systematic-review how-to ([`docs/how-to-guides/sources/`](docs/how-to-guides/sources/))
and ADR-16 (adopt-on-demand) both assume a `00-meta/04-reference/screening-protocol.md` fill-
in-the-blank artifact exists in the vault. It does not: `vault/` ships no such file.

A production-ready template already exists in
[`_archived/reports/migration-drafts/screening-protocol.md`](_archived/reports/migration-drafts/screening-protocol.md).
It has been translated to the current taxonomy (candidates in `10-inbox/03-candidates/`,
systematic-review mode gated by ADR-16). The template covers review metadata, research
question, inclusion/exclusion criteria, database sources with search strings, PRISMA decision
log, and per-citekey screening decisions. It is ready to copy verbatim.

**Proposed action.** Copy the migration-draft to
`vault/00-meta/04-reference/screening-protocol.md` (the destination already named in the
file's comment header). Add a single row in the vault's `docs/reference/` inventory.

---

## Finding 2 — Per-type enrichment staleness cadence missing from reference docs

**Priority: MEDIUM.**

The current docs record `enriched_date` as a top-level frontmatter field, and the Linter has
a generic stale-enrichment check. What is **not** documented is how long is "stale" per
source type:

| Source type | Re-enrich every | What changes |
| --- | --- | --- |
| Article | 180 days | Citation count, related papers |
| Preprint | 30 days | May have been formally published |
| Person | 90 days | New papers, affiliation changes |
| Organization | 365 days | Rarely changes |
| Repository | 30 days | Stars, issues, releases |
| Package | 30 days | New versions, deprecation |

**Source:** `_archived/reports/migration-drafts/reference-topups.md` §3, originally from
`_archived/old/04_background_decisions.md` §S. The generic 90-day default in the old design
was explicitly noted there as "sharper once per-type cadences are documented."

**Proposed action.** Add a **"Staleness cadences"** table to
[`docs/reference/frontmatter.md`](docs/reference/frontmatter.md) near the `enriched_date`
field description (or to `docs/reference/ingest.md`). The Linter's stale-enrichment detector
should reference this table rather than a single universal threshold.

---

## Finding 3 — Slug collision disambiguation rules missing

**Priority: MEDIUM.**

The current docs have no guidance on what to do when two entities would generate the same
slug. Without a rule, the human either picks arbitrarily or has to maintain a lookup table.
The following deterministic rules are documented in the archive and require no lookup table:

| Collision scenario | Resolution |
| --- | --- |
| Two researchers with the same name | Append affiliation: `smith-john-iowa` vs `smith-john-stanford` |
| Two labs with similar names | Use full institution: `hci-lab-iowa` vs `hci-lab-cmu` |
| Company vs person, same surname | Person keeps bare slug; organization gets `-org` suffix |
| Same package name across registries | Registry prefix: `pypi-requests` vs `npm-requests` |
| Repo vs person, same slug | Repos always carry `{owner}-` prefix — no collision possible by construction |

**Source:** `_archived/reports/migration-drafts/reference-topups.md` §4.

**Proposed action.** Add a **"Slug collision resolution"** subsection to
[`docs/reference/note-types.md`](docs/reference/note-types.md) (entity notes section) or
to `docs/reference/glossary.md` near the "citekey" definition.

---

## Finding 4 — Delegation ladder ASCII visual missing from profiles README

**Priority: MEDIUM.**

`docs/explanation/profiles/README.md` has a delegation-posture table (who may delegate what
at what strength). What it lacks is the at-a-glance *ordering* — a visual showing, from
strongest to weakest, which profiles delegate more versus less. The archive prepared a clean
ASCII version:

```text
Delegation posture — who may hand a narrow, temporary subtask to a child or external
agent. Never the role's defining judgment. Strongest at top.

  more ┌─────────────────────────────────────────────────────────────────┐
   ▲   │ Coder      Moderate    helper/lookup + substantive coding to    │
   │   │                        the external agent; commits per-task     │
   │   │ Writer     Supportive  facts / cleanup; synthesis stays local   │
   │   │ Librarian  Targeted    narrow enrichment / source lookups;      │
   │   │                        keeps discovery ownership                │
   │   │ Mapper     Low         mechanical retrieval (qmd); keeps the map│
   │   │ Verifier   Very low    delegation weakens independence; traces   │
   │   │ Linter     Lowest      does not spawn work; may request context │
   ▼   │ Socratic   None        can't write; questions are the product   │
  less └─────────────────────────────────────────────────────────────────┘

Rule: delegate narrow, temporary, low-risk subtasks; never the defining judgment.
```

**Source:** `_archived/reports/migration-drafts/diagrams-ascii.md` (relabeled to current
seven profiles; the original SVG used the old six-profile set with "Orchestrator" at top —
there is no orchestrator in the current design).

**Proposed action.** Add this ASCII block to
[`docs/explanation/profiles/README.md`](docs/explanation/profiles/README.md) immediately
above the existing delegation table, as a quick visual before the detail.

---

## Finding 5 — PDF extraction alternatives comparison not documented

**Priority: MEDIUM.**

Current docs name Marker as the chosen PDF extractor and MarkItDown as the fallback for
non-PDF files. The archive documents a broader tool comparison that is worth preserving as
reference:

| Tool | Best for | Status |
| --- | --- | --- |
| **Marker** (Datalab, ~31k) | Math-heavy papers; structured Markdown; `--use_llm` flag for accuracy | Chosen |
| **Docling** (IBM/LF, ~58k stars; v2.94.0) | General PDFs + tables/figures; `docling-mcp` MCP companion available | Strong alternative for table/figure-heavy corpora |
| **PyMuPDF4LLM** | Fastest CPU-only path for clean text-based PDFs | Pre-processing step |
| **MarkItDown** (Microsoft) | Web pages, Office docs, HTML → Markdown | Current fallback; adjunct |
| **GROBID** (Inria) | Header/reference field parsing for DOI-less PDFs (~0.87–0.90 F1) | Edge case only; not a pipeline stage |
| **Nougat** (Meta) | Math LaTeX | Unmaintained — avoid |

**Docling** is particularly notable: it is larger by installs than Marker, donated to the
Linux Foundation, and has a companion `docling-mcp` server that can sit alongside the Zotero
and Obsidian MCP servers in `config.yaml`. The recommendation from the archive: keep Marker
for the Obsidian-readable extract; reach for Docling if the corpus is table/figure-heavy.

**GROBID** fills an unstated gap: papers that arrive without a DOI cannot go through the
normal OpenAlex/Semantic Scholar enrichment path. GROBID's header/reference parsing recovers
metadata from the PDF itself in that case.

**Source:** `_archived/reports/migration-drafts/reference-topups.md` §1.

**Proposed action.** Add a PDF extraction tools table to
[`docs/reference/ingest.md`](docs/reference/ingest.md) or as a short section in
[`docs/reference/computational-toolbox.md`](docs/reference/computational-toolbox.md). Update
the existing "Content extraction fallback" note to mention Docling and GROBID by name with
their specific use cases.

---

## Finding 6 — Citation-format parser stack "do not reimplement" guidance missing

**Priority: LOW.**

No current doc tells a developer which libraries underpin citation handling and discourages
reimplementation. The archive has a compact reference table:

| Format | Library | Note |
| --- | --- | --- |
| BibTeX / BibLaTeX | `bibtexparser` ≥ 2.0 | Handles encoding, special chars, cross-refs |
| RIS | `rispy` | Round-trip; used internally by ASReview |
| CSL-JSON | `citeproc-py` + `citeproc-py-styles` | CSL 1.0.1; ~40 MB style repo |
| JATS XML (publisher) | `pubmed-parser` or `lxml` | PMC + most publishers |
| Convert between formats | `pypandoc` | Swiss-army knife between the above + Markdown |

**Source:** `_archived/reports/migration-drafts/reference-topups.md` §2.

**Proposed action.** Add as a small reference subsection to
[`docs/reference/ingest.md`](docs/reference/ingest.md) or
[`docs/reference/computational-toolbox.md`](docs/reference/computational-toolbox.md) under
"Citation format handling."

---

## Finding 7 — Vocabulary example not shipped as a starter artifact

**Priority: LOW.**

The current design leaves `study_design`, `methods`, and `topic` vocabularies deliberately
open ("open by design" per ADR schema decisions). A user starting a blank vault has no
worked example. The archive has a fully realized HCI + digital health vocabulary
(`_archived/reports/migration-drafts/vocabulary-example.md`) with ~30 topic terms, 12 study
designs, and ~30 method terms, explicitly framed as "one worked example, not a Memoria
default — copy what fits, edit freely."

The key rules from that file worth preserving regardless of domain:
- Keep `topic` to ≤30 terms — a smaller vocabulary produces more consistent Librarian classification.
- `_enrichment` is where richer taxonomy (MeSH, ACM CCS, OpenAlex concepts) belongs; the
  hand-curated list is intentionally short.
- `maturity` (`seedling / budding / evergreen`) and MOC `scope` (`topic / domain / project /
  method`) are fixed conventions, not open vocabulary — worth repeating in any example.

**Source:** `_archived/reports/migration-drafts/vocabulary-example.md`.

**Proposed action.** Ship the vocabulary example as
`vault/00-meta/04-reference/vocabulary-example.md` with a comment header making clear it is
a starting point, not a default. Link from `docs/reference/schema-reference.md`.

---

## Finding 8 — `vision_analyze` (figure/table reading) not documented in any profile

**Priority: MEDIUM.**

The Librarian's ingest pipeline uses Marker to extract text from PDFs. Hermes provides a
`vision_analyze` capability that lets a profile interpret embedded figures, tables, and chart
screenshots directly from PDFs — without text extraction. Current docs do not mention this
capability for the Librarian.

The archive's capability report identifies this as **the highest-value multimodal feature for
Memoria**: the Librarian reading figures and tables at ingest can populate `_aspects.method`
and `_aspects.outcome` more accurately than reading text alone, particularly for papers where
the key result is a figure rather than a paragraph.

This composes naturally with the MASSW-aspects proposal in
[`project-files/proposals/schema-and-retrieval.md`](project-files/proposals/schema-and-retrieval.md)
— `_aspects.key_idea`, `_aspects.method`, `_aspects.outcome` can be figure-informed rather
than abstract-only.

**Source:** `_archived/reports/hermes-capabilities-design-report.md` §11 (Group D —
Multimodal stack, "Vision: adopt (high value for literature ingest)").

**Proposed action.** Add a note on `vision_analyze` to
[`docs/explanation/profiles/librarian.md`](docs/explanation/profiles/librarian.md) under the
ingest section — specifically for the PDF extract step — and to
[`docs/reference/ingest.md`](docs/reference/ingest.md) as an alternative extraction path for
figure/table-heavy papers.

---

## Finding 9 — Browser capability not documented for Librarian discover

**Priority: LOW.**

Several relevant discovery sources (publisher pages, lab sites, preprint servers,
GitHub research repos) do not expose a structured API that the Librarian's existing enrichment
tools (OpenAlex, Semantic Scholar, PubMed) can reach. Hermes provides a browser capability
(headless browser for page rendering and element extraction) specifically suited to the
discover lane's long tail of sources.

The archive recommends: scope it narrowly to the `discover` skill, never to canonical-zone
writes. Used sparingly it covers discovery targets the API path cannot reach.

**Source:** `_archived/reports/hermes-capabilities-design-report.md` §15 (Group B,
"Browser: adapt").

**Proposed action.** Add a short note in
[`docs/explanation/profiles/librarian.md`](docs/explanation/profiles/librarian.md) under the
`discover` skill section noting the browser capability as an opt-in fallback for sources
without an API endpoint.

---

## Finding 10 — Inciteful and identifier reconciliation helpers not documented

**Priority: LOW.**

Two tooling gaps in the enrichment reference:

**Inciteful** (citation-network discovery tool; Zotero plugin + public API): surfaces related
papers not yet in the Zotero library via citation-graph proximity. A complement to OpenAlex
forward/backward snowballing in the discover stage — specifically useful for finding the most
central papers in a neighborhood rather than just temporally adjacent ones.

**Identifier reconciliation helpers** (for the Librarian's enrichment path):
- `habanero.content_negotiation(doi, format="bibtex")` — one call converts a DOI to
  BibTeX/CSL-JSON/RIS.
- [`drAbreu/alex-mcp`](https://github.com/drAbreu/alex-mcp) — author disambiguation via
  OpenAlex autocomplete + ORCID matching; a natural MCP server companion.
- OpenRefine + ORCID/ROR/Wikidata — bulk entity reconciliation for person and org notes.
- `python-orcid` (public search) and `pyalex.Institutions()["search"]` (→ ROR) — programmatic
  institution lookup.

**Source:** `_archived/reports/migration-drafts/reference-topups.md` §5.

**Proposed action.** Add Inciteful to the "Evaluated, not in use" row of
[`docs/reference/zotero-plugins.md`](docs/reference/zotero-plugins.md) or to
[`docs/reference/ingest.md`](docs/reference/ingest.md). Add identifier reconciliation helpers
as a reference subsection in `docs/reference/ingest.md` under "Enrichment tools."

---

## Finding 11 — Multi-reviewer systematic review screening mode (PROP candidate)

**Priority: LOW — new PROP-11 candidate.**

The systematic-review mode (ADR-16) defines *when* to do a systematic review. What it does
not define is *how* to structure multi-agent screening within a single review pass. The
archive's repo analysis describes the LatteReview pattern:

> Multiple reviewer-agent prompts with different screening criteria (e.g., Reviewer A:
> methods focus; Reviewer B: outcome focus) independently vote on each candidate; a "senior
> reviewer" prompt summarizes disagreements and proposes a recommendation. The human still
> makes the final inclusion decision.

This differs from the current design (single Librarian classify pass) in that it surfaces
*disagreement* at the screening stage — the human sees contested candidates separately from
agreed ones, reducing rubber-stamping risk on the agreed set.

**Source:** `_archived/raw/Analyze the following repos… -part1.md` §2 (Literature-review and
screening assistants, LatteReview analysis).

**Proposed action.** Write as PROP-11 proposal if/when ADR-16's systematic-review mode is
being actively built out. The core addition to the current design is: a
`review_mode: systematic-review` flag on discovery runs that activates multiple independent
screening passes and a disagreement-surfacing step before the human's triage card.

---

## Finding 12 — `uses-method` typed relation not in schema (PROP candidate)

**Priority: LOW — extends existing ADR-08 / schema-and-retrieval proposal.**

ADR-08 established `supports` and `contradicts` as first-class frontmatter typed relations.
The `schema-and-retrieval.md` proposal extends this to `similar`. Neither covers a
methodological-provenance relation.

The repo analysis recommends a `uses-method` (or `operationalizes`) relation on claim notes
pointing to method notes, enabling queries like "find all claims that used X measurement
approach." This composes with the MASSW `_aspects.method` field from the
`schema-and-retrieval` proposal — the aspect says *what* method; the typed relation says
*which existing method note* it reuses.

**Source:** `_archived/raw/Analyze the following repos… -part1.md` §5 (Richer knowledge
representation).

**Proposed action.** Add as a deferred extension item inside the existing
[`project-files/proposals/schema-and-retrieval.md`](project-files/proposals/schema-and-retrieval.md)
§1 (Scenario-typed retrieval) rather than a new file, since it is sequenced after `similar`.

---

## Terminology hazard reference table

For anyone reading archive files: a lookup table of old names that do not match current
design. These are fully superseded — do not import or document them.

| Archive term | Current equivalent | Notes |
| --- | --- | --- |
| Orchestrator profile | *none* | No orchestrator; routing is dispatcher + lane-overrides |
| Researcher profile | Librarian | Renamed; scope shifted |
| Curator / Maintainer profile | Mapper | Renamed |
| Reviewer profile | Verifier (+ human review gate) | Agent-verdict part = Verifier; blocking part = human gate |
| `40-permanent/` | `30-synthesis/01-claims/` | Folder renamed in lifecycle schema |
| `10-literature/` | `20-sources/` | Folder renamed |
| `60-projects/` | `40-workbench/` | Folder renamed |
| `70-drafts/` | `40-workbench/<project>/04-drafts/` | Moved into workbench |
| `_draft_classification` | `_proposed_classification` | Field renamed |
| Corpus profile (full scoring matrix) | `project-hints.yaml` (lightweight topic hint) | Simplified; matrix not restored |
| `ops-intake` / `ops-maintainer` | Librarian / Linter | Old profile naming |
| `watcher` | Fleet-health dashboard + audit log | Distributed across existing dashboards |
| `framer` | Writer profile (`framing` skill) | Profile renamed; skill survives |
| `claim-tracer` | Verifier (`cite-check` skill) | Profile renamed; skill survives |

---

## What the prior salvage reports correctly concluded (not re-reported here)

The following were explicitly processed by earlier reports and confirmed absorbed or
consciously rejected:

- All architecture diagrams (SVGs) → superseded by ASCII in current docs; only delegation
  ladder was residue (covered as Finding 4 above).
- The four named raw/ specs (policy MCP, profile generator, task registry, agent workflows)
  → fully absorbed and often improved in current docs.
- research-wiki/ vault architecture broadly → fully superseded.
- The migration-draft ADRs 26–30 → all resolved: ADR-26 → ADR-14; ADR-27 → PROP-05;
  ADR-28 → PROP-06; ADR-29 → PROP-07; ADR-30 → ADR-15 + `project-hints.yaml`.
- `research-directions.md`, workspaces (Cmd+1/2/3), lens-based reading, accept/reject ratio
  tracking → all in current docs.
- Export routes A–D (static Pandoc, live Word, live LibreOffice, Google Docs) → in
  `docs/reference/export.md` and ADR-14.
