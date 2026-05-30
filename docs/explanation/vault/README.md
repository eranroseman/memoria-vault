---
topic: vault
---

# Notes, folders, and linking

The vault is where durable knowledge lives. This document covers the conceptual model: the layered folder structure, what each layer means, the promotion map, and the conventions that keep the vault navigable.

For reference content, see the sibling docs:

- [note-types.md](../../reference/note-types.md) — the 15 note types, their lifecycles, and the templates that ship with the vault.
- [frontmatter-schema.md](../../reference/frontmatter-schema.md) — frontmatter field categorization, controlled vocabularies, and the agent/human namespace split.
- [linking-patterns.md](../../reference/linking-patterns.md) — link types, the expected cross-link graph, and MOC creation thresholds.

## Folder structure

Folders encode **lifecycle stage**, not subject area. The top-level number indicates where in the capture → describe → think → work → ship progression a note sits.

```text
<vault-root>/                  ← starter vault; human picks the folder name
├── 00-meta/
│   ├── 01-dashboards/         # 12 Dataview dashboards (Daily Health + 11)
│   ├── 02-logs/               # audit.jsonl, board-state.jsonl, lint-findings.jsonl, cron-history.jsonl
│   ├── 03-templates/          # 15 note templates
│   ├── 04-reference/          # human-facing reference notes
│   ├── index.md               # vault landing page (pinned)
│   ├── research-directions.md # Librarian's session-start input
│   └── system-status.md       # runtime health snapshot
├── 10-inbox/
│   ├── 01-fleeting/
│   ├── 02-answers/
│   └── 03-candidates/
├── 20-sources/
│   ├── 01-papers/
│   ├── 02-items/
│   └── 03-entities/
│       ├── 01-people/
│       ├── 02-organizations/
│       └── 03-venues/
├── 30-synthesis/
│   ├── 01-claims/
│   ├── 02-reference/
│   └── 03-moc/
├── 40-workbench/
│   └── <project>/            # 01-map/ 02-framing/ 03-canvas/ 04-drafts/ 05-verification/ 06-code/
├── 50-deliverables/
│   ├── 01-manuscripts/
│   ├── 02-presentations/
│   ├── 03-media/
│   └── 04-releases/
├── 90-assets/
├── 95-archive/
│
├── .obsidian/                 ← Obsidian config (auto-hidden)
└── .memoria/                  ← Memoria tooling (dot-prefix: auto-hidden by Obsidian)
    ├── profiles/              ← seven hand-authored Hermes profile directories
    ├── mcp/                   ← policy_mcp.py, tasks_mcp.py, requirements.txt
    ├── lane-overrides/        ← per-lane YAML the policy MCP reads at startup
    ├── csl/                   ← Pandoc citation styles
    ├── library.bib            ← Zotero BibTeX export  # exported from Zotero by user — not pre-created
    └── tool-registry.yaml     ← machine-read tool config  # scaffolded by install.ps1 on first run — not pre-created
```

The vault is a single repo, opened directly by Obsidian. The numbered top-level folders are human-visible workspace; `.obsidian/` and `.memoria/` (both dot-prefixed and therefore auto-hidden by Obsidian's vault scanner) hold tooling. `.memoria/profiles/` is the source of truth for the seven Hermes profiles — `install.ps1` copies these verbatim into `~/.hermes/profiles/memoria-<name>/` at install time. See [architecture/on-disk-layout.md](../architecture/on-disk-layout.md) for the full picture, including the install flow and the source-vs-runtime relationship.

### Why this layout

The biggest gain over a flat structure is that **source**, **synthesis**, **workbench**, and **deliverable** become visibly different zones. The agent and human both see at a glance what a folder is *for*: things that describe the world (sources), things that express the human's thinking (synthesis), things being worked on (workbench), and things that have shipped (deliverables).

The split inside `30-synthesis/` (`claims/`, `reference/`, `moc/`) is especially important because it makes the three kinds of conceptual knowledge distinct: claims, reference pages, and navigation hubs.

### Folder roles and access

Coarse access summary. The authoritative per-profile permissions live in [profiles/README.md](../../reference/profile-matrices.md#lane-permissions-matrix); per-write policy is enforced by the [policy MCP](../../reference/architecture/policy-mcp.md) via the [lane-override files](../profiles/README.md#lane-override-files).

| Folder | Role | Human | Agent |
| --- | --- | --- | --- |
| `00-meta/` | Schema, templates, dashboards, logs, configuration. | Full | Read; write logs and dashboards only. |
| `00-meta/01-dashboards/` | Dataview dashboard pages. | Full | Read; update under instruction. |
| `00-meta/02-logs/` | Session logs and audit trail. | Full | Write (own logs). |
| `00-meta/03-templates/` | Note templates. | Full | Read. |
| `00-meta/04-reference/` | Human-facing reference notes (design-system, schema-reference, system-map, agent-roles, etc.). | Full | Read. |
| `10-inbox/01-fleeting/` | Raw captures, unprocessed thoughts. | Write | Read / write. |
| `10-inbox/02-answers/` | Draft answers awaiting review. | Review | Write. |
| `10-inbox/03-candidates/` | Discovery leads and screening queue. | Review | Write. |
| `20-sources/01-papers/` | One note per citable paper (journal article, conference paper, preprint, report, thesis). A paper is a specialized item; it gets its own folder for volume and workflow reasons. | Review | Write. |
| `20-sources/02-items/` | Tools, repos, packages, products, standards, datasets, software. | Review | Write. |
| `20-sources/03-entities/01-people/` | People (authors, advisors, collaborators, developers). | Review | Write. |
| `20-sources/03-entities/02-organizations/` | Labs, universities, companies, funders. | Review | Write. |
| `20-sources/03-entities/03-venues/` | Journals, conferences, workshops. | Review | Write. |
| `30-synthesis/01-claims/` | Durable claims in the human's own words. | Write | Read; suggest links only. |
| `30-synthesis/02-reference/` | Stable reference pages. | Review / edit | Draft and limited updates. |
| `30-synthesis/03-moc/` | Maps of Content; navigation hubs. | Write | Read; suggest only. |
| `40-workbench/<project>/` | One folder per project; all working artifacts nest inside. | Write | Read / write. |
| `40-workbench/*/01-map/` | Corpus maps, gap reports, cluster maps, comparative briefs. | Review | Write (Mapper scratch). |
| `40-workbench/*/02-framing/` | Competing project framings (Writer `counter-outline`; Socratic lens captures). | Write | Write (scratch). |
| `40-workbench/*/03-canvas/` | Argument mapping, spatial planning. | Write | Read only or limited assist. |
| `40-workbench/*/04-drafts/` | Manuscripts in progress. | Write | Read only unless asked. |
| `40-workbench/*/05-verification/` | Per-claim verification reports. | Review | Write (Verifier scratch). |
| `40-workbench/*/06-code/` | Code artifacts and scripts (including Jupyter notebooks). | Write | Read / write. |
| `50-deliverables/` | Final manuscripts, slides, submission-ready exports. | Write | Read / write on explicit export tasks. |
| `90-assets/` | Machine-extracted markdown and non-PDF binary attachments. `90-assets/extracts/<citekey>.md` holds Marker output from ingest; other binaries (figures, datasets, supplementary materials) live alongside as needed. **PDFs do not live here** — they stay in Zotero's storage and are reached via `pdf_uri` on the paper-note. | Hidden / managed | Read only. |
| `95-archive/` | Deprecated, superseded, or archived notes. | Read only | Read only. |

### Lifecycle organizes knowledge; project organizes work

As established above, the numbered folders encode lifecycle stage rather than subject — a BCI paper lives in `20-sources/01-papers/`, not a `BCI/` folder, and its topics live in frontmatter. `40-workbench/` is the one deliberate exception: its unit is the **project**, not the lifecycle stage. A project folder (`<project>/`) holds every working artifact for one effort — `01-map/`, `02-framing/`, `03-canvas/`, `04-drafts/`, `05-verification/`, `06-code/` — so the whole effort is co-located and archives as a unit.

This doesn't violate the principle, because the principle is really an *anti-duplication* rule for many-to-many data: a source has many topics, so it can't live in one topic folder. Workbench artifacts are single-project (a draft belongs to exactly one manuscript), so the duplication problem never arises. A **project is not a topic** — it's a bounded, transient effort that gets archived when it ships. Durable knowledge still lives in the lifecycle layers (`20-sources/`, `30-synthesis/`) and carries its topics in frontmatter.

## Special files

A small set of `00-meta/` files are not folders and not templates — they are human-facing singletons that shape how the system runs.

| File | Purpose | Owner |
| --- | --- | --- |
| `00-meta/research-directions.md` | Current research priorities, open questions, synthesis gaps, papers to prioritize. The Librarian reads this at session start. | Human (refresh weekly) |
| `00-meta/system-status.md` | Runtime health snapshot: Hermes API running, MCPs up, plugin enabled, profiles available. **Distinct from `board-state`**, which tracks work in flight. | Human (occasional refresh) |

`research-directions.md` is the most operationally important of these: an empty or stale file produces an unfocused Librarian. See [workflows/README.md](../../how-to/workflows/README.md) for how it feeds the find workflow.

## Vault skeleton: human-facing notes

A freshly-cloned vault ships with a small set of plain-language human notes in `00-meta/`. These are the *human-facing* counterpart to the technical contracts in `.memoria/profiles/memoria-<name>/SOUL.md` (in the vault) and the topic-specific reference docs scattered across the design repo (`architecture/policy-mcp.md`, `vault/frontmatter-schema.md`, `profiles/profile-commands.md`, etc.) — they let someone opening the vault for the first time understand what they're looking at without reading the design docs.

| Note | Purpose | Maintained by |
| --- | --- | --- |
| `00-meta/index.md` | Vault landing page. Pinned in sidebar. Links to system status, dashboards, lane views, key files. | Human (rarely changes) |
| `00-meta/04-reference/getting-started.md` | First-time setup checklist. The 5 steps from clone to first ingest. | Human (rarely changes) |
| `00-meta/04-reference/system-map.md` | High-level architecture summary in plain language. The vault-resident companion to [architecture/README.md](../architecture/README.md). | Human (sync with design changes) |
| `00-meta/04-reference/agent-roles.md` | Plain-language one-paragraph summary of each Hermes profile. Mirrors the SOUL.md contracts at `.memoria/profiles/memoria-<name>/SOUL.md` in the vault. | Human (sync with profile changes) |
| `00-meta/04-reference/profile-policies.md` | Plain-language summary of who-can-write-where. Tracks the lane-override YAML files and the [Lane permissions matrix](../../reference/profile-matrices.md#lane-permissions-matrix). | Human (sync with lane-override changes) |
| `00-meta/04-reference/schema-reference.md` | Canonical list of every frontmatter field used in the vault, with type and allowed values. The source of truth that templates and the Linter point at. | Human + Linter (Linter flags drift) |
| `00-meta/04-reference/dataview-cheatsheet.md` | Reference patterns for dashboard authors — TABLE / LIST / TASK / FROM / WHERE / SORT / FLATTEN / LIMIT examples. | Human (rarely changes) |
| `00-meta/04-reference/performance-checklist.md` | Dashboard performance discipline (see [obsidian-ui/dashboards.md](../../reference/obsidian-ui/dashboards.md#performance-discipline)). | Human (rarely changes) |
| `00-meta/04-reference/safe-mode.md` | The three core workflows (ingest, review, export) with minimal commands and fallbacks when something is broken. Open this when Hermes, the ACP connection, or the watcher is down. Pairs with [operations/failure-modes.md](../../how-to/operations/failure-modes.md) for the Detect/Fix/Verify recipes. | Human (rarely changes) |
| `00-meta/04-reference/obsidian-config.md` | Plain-language summary of which Obsidian community plugins Memoria uses and the load-bearing settings the human should not change. Mirrors [obsidian-plugins/README.md](../../reference/plugins/README.md). | Human (sync with plugin changes) |
| `00-meta/04-reference/design-system.md` | Canonical visual-style source for the vault — palette, typography, spacing, layout, components, motion, voice, brand, anti-patterns. Format follows [open-design](https://github.com/nexu-io/open-design)'s 9-section DESIGN.md schema so the same file can drive open-design's render pipeline. Read by CSS-snippet generators, by Pandoc export configs, and by open-design when rendering deliverables. Templated by [obsidian-ui/design-system.md](../../reference/templates/design-system.md). | Human (edits define the brand); design-system schema versioned independently |

The design folder is the *engineering* spec — it describes how to build and reason about the system. The vault skeleton is what a *human* needs in front of them while using the vault day-to-day. The skeleton notes are intentionally short and plain-language; if a section needs architectural detail, it links to the relevant `memoria-docs/` document.

### Drift discipline

When the design changes — a new profile added, a lane-override rule updated, a schema field introduced — the corresponding skeleton note must be updated. The Linter's structural-drift check (see [profiles/linter.md](../profiles/linter.md)) flags skeleton notes whose `updated` is older than the corresponding design file. Treat skeleton drift the same way as code-doc drift: pay it down promptly.

## Common pitfalls

These failure modes recur. Treat them as anti-patterns to actively avoid.

### Capture and classify

- **Unpinned citekeys.** If Zotero metadata changes before the BBT key is pinned, the key regenerates and every wikilink pointing to the old key breaks silently. **Pin all keys immediately after import.**
- **Promoting `_proposed_classification` without checking the vocabulary.** If the schema says `receptivity-detection` and `topic: [receptivity]` is promoted, queries miss the note. Always check vocabulary when classifying.
- **Writing claim notes before classifying the paper note.** The `_proposed_classification` often surfaces project connections that should appear in the claim note. Classify first.
- **Letting `10-inbox/` accumulate without review.** The inbox is a queue, not storage. Notes older than 7 days are either worth promoting or worth discarding. An inbox that grows is a system capturing without synthesizing — the most common failure mode.

### Synthesis quality

- **Summary notes masquerading as synthesis.** A paper note that lists bullet points is a summary, not synthesis. Synthesis means connecting what the paper says to what the human already knows — if there are no wikilinks in the Summary section, no synthesis has happened.
- **Too many claims in one claim note.** If the title contains "and" doing real work, split the note. One claim, one note.
- **Treating agent synthesis as verified content.** An `answer-note` is a proposal. The agent may cite a paper for a claim that paper doesn't actually make. Always verify citekeys before promoting.

### Promotion and structure

- **Using `30-synthesis/02-reference/` for work-in-progress.** Reference notes should be stable. If a page changes substantially every week, it's a claim note with `maturity: budding`, not a reference note. Move it back.
- **MOC-as-folder-dump.** A MOC that's just a list of every note on a topic is a folder. MOCs add context and annotation. A bare list of wikilinks is not a MOC.
- **Orphan claim notes.** A claim note with no incoming links has not made it into the knowledge graph. The weekly orphan query catches these — act on them.

### Operational hazards

- **Running `schema-migrate` without reviewing the diff.** Running it without `--dry-run` first can silently alter frontmatter across hundreds of notes. **Always dry-run first.**
- **Auto-promotion of `_proposed_classification`.** The agent should never promote proposed fields without explicit classification. If the urge arises, write a better dashboard query that surfaces candidates for batch review instead.

## Routing and action policy

- Route each note to the folder that matches its **type**, not its **topic**.
- If the type is ambiguous, ask before creating or moving the note.
- Do not store a `paper-note` under `40-workbench/`, or a `claim-note` in the inbox.
- Do not use `30-synthesis/02-reference/` for unstable work-in-progress.
- Do not use `30-synthesis/01-claims/` for source summaries.
- Do not use `40-workbench/*/04-drafts/` as a general notes folder.
- If a note could fit more than one type, choose the **most specific epistemic role**.
- If a note's purpose changes substantively, create a new note rather than mutating the old one. Link the new note to the old for provenance.

### Delete and move

The note-types table above answers *who creates and edits*. This adds *delete and move*:

- **Delete** is universally human-only and discouraged across the board. Prefer archive for anything with provenance value.
- **Move into a [review-gated folder](../../reference/glossary.md#system-and-architecture)** (the four review-gated zones) is human-only.
- **Move to `95-archive/`** is human-only. The agent never archives.
- **Move within working zones** (e.g., `10-inbox/` → `20-sources/` after classification) may be agent-initiated when the type and state warrant it.

## Promotion map

The lifecycle moves left-to-right through the folder numbers. The arrows below show legal promotion paths — what type a note becomes when promoted.

```text
fleeting-note ──┬──► answer-note ──► claim-note ──► reference-note
                │         (Writer)        (human)         (Writer + human)
                ├──► paper-note (classified)
                │         (Librarian → human)
                └──► (discarded)

claim-note ────► moc membership (via frontmatter moc:)
claim-note ────► draft section (cited in body)
draft ─────────► deliverable (on export)
canvas ────────► draft (informs structure; canvas is then archived — informally "frozen")
code-note ─────► project-note (linked from project)
```

Rules that constrain the map:

- `fleeting-note` is reviewed and either promoted or discarded — it does not linger.
- `answer-note` → `claim-note` only after human review.
- `claim-note` → `reference-note` only when the claim is `evergreen` and sufficiently cross-linked.
- `paper-note` never becomes a `claim-note`. A source describes what the paper says; a claim is what the human thinks.
- Archived notes remain in place for historical traceability; never delete a note with provenance value. Only humans move notes to `95-archive/`.

## Linking patterns

Linking is the cross-cutting discipline that turns the vault into a graph rather than a flat folder hierarchy. Two cardinal rules anchor the practice: **every `claim-note` traces to at least one `paper-note` citekey**, and **provenance direction is preserved** — claims point to evidence, never the reverse.

**Full reference** — five link types (`citekey-link`, `concept-link`, `moc-link`, `entity-link`, `agent-cross-link`), the full rule set (including indirect co-authorship and the orphan-rescue rule), the expected cross-link graph by note type, the topic/domain/child-MOC creation thresholds, and slug-collision resolution patterns — live in [linking-patterns.md](../../reference/linking-patterns.md).
