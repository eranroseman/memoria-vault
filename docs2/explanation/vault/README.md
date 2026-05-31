---
topic: vault
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria — the board, the profiles, the dashboards — exists to serve it. This document explains the vault's structure: what the folders mean, how notes move through it, and the conventions that keep it navigable.

For the conceptual model behind the design choices (why lifecycle folders, what note types represent, why promotion is gated), see [knowledge/](../knowledge/).

---

## Folder structure

Folders encode **lifecycle stage**, not subject area. The top-level number indicates where in the capture → describe → think → work → ship progression a note sits.

```text
<vault-root>/
├── 00-meta/             ← schema, templates, dashboards, logs, config
│   ├── 01-dashboards/
│   ├── 02-logs/
│   ├── 03-templates/
│   ├── 04-reference/    ← human-facing skeleton notes
│   ├── 05-eval/
│   └── 07-skills/
├── 10-inbox/            ← not yet classified; queue, not storage
│   ├── 01-fleeting/
│   ├── 02-answers/
│   └── 03-candidates/
├── 20-sources/          ← describes the world
│   ├── 01-papers/
│   ├── 02-items/
│   └── 03-entities/
├── 30-synthesis/        ← expresses the human's thinking
│   ├── 01-claims/       ← review-gated; human-authored
│   ├── 02-reference/    ← review-gated
│   └── 03-moc/          ← review-gated
├── 40-workbench/        ← active work, organized by project
│   └── <project>/
│       ├── 01-map/
│       ├── 02-framing/
│       ├── 03-canvas/
│       ├── 04-drafts/
│       ├── 05-verification/
│       └── 06-code/
├── 50-deliverables/     ← finished and shipped; review-gated
├── 90-assets/           ← attachments and binary files
├── 95-archive/          ← deprecated or superseded notes
├── .obsidian/           ← Obsidian config (auto-hidden)
└── .memoria/            ← Memoria tooling (auto-hidden)
    ├── profiles/        ← seven Hermes profile directories
    ├── mcp/
    ├── lane-overrides/
    └── library.bib
```

The four **review-gated zones** (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) are structurally protected — no profile can write to them without a human `review_status: approved`. The policy MCP enforces this at the filesystem level.

---

## Why the structure is this way

**Lifecycle over topic** — a paper about attention lives in `20-sources/01-papers/`, not `cognitive-science/`. Topics live in frontmatter where they can be many-to-many; lifecycle stage lives in the folder where it is one-to-one. See [../knowledge/lifecycle-over-topic.md](../knowledge/lifecycle-over-topic.md).

**`30-synthesis/` is human territory** — claim notes and MOCs are human-authored. Agents draft candidates that land in `10-inbox/`; the human writes the canonical synthesis. The review-gated-zone deny rule enforces this structurally.

**`40-workbench/` is the one exception** — its unit is the project, not the lifecycle stage. A project folder holds all working artifacts for one effort (map, framing, drafts, verification, code) and archives as a unit when it ships. See [../knowledge/lifecycle-over-topic.md#the-workbench-exception](../knowledge/lifecycle-over-topic.md).

**`90-assets/` does not hold PDFs** — PDFs live in Zotero's storage; paper notes reference them via `pdf_uri`. `90-assets/` holds Marker-extracted markdown and binary attachments.

---

## Special files

A small set of singleton files in `00-meta/` shape how the system runs:

| File | Purpose | Owned by |
|---|---|---|
| `00-meta/research-directions.md` | Current research priorities and synthesis gaps. The Librarian reads this at session start. An empty or stale file produces an unfocused Librarian. | Human (refresh weekly) |
| `00-meta/system-status.md` | Runtime health snapshot: API status, MCPs up, profiles available. Distinct from the board, which tracks work in flight. | Human |
| `00-meta/04-reference/getting-started.md` | First-time setup checklist. | Human |
| `00-meta/04-reference/agent-roles.md` | Plain-language summary of each profile's role. | Human (sync with profile changes) |
| `00-meta/04-reference/schema-reference.md` | Canonical list of every frontmatter field. The source of truth that templates and the Linter point at. | Human + Linter |

---

## Promotion map

Knowledge moves left-to-right through the folder numbers. The legal moves:

```text
fleeting-note ──► paper-note        (Librarian enriches, human classifies)
fleeting-note ──► claim-note        (human writes directly)
fleeting-note ──► (discarded)

answer-note   ──► claim-note        (human distills)
answer-note   ──► (discarded)

claim-note    ──► reference-note    (when evergreen and cross-linked)
draft         ──► deliverable       (on export)
```

Rules: a `paper-note` never becomes a `claim-note` directly — the distinction between "what the source says" and "what the human thinks" is preserved. Archived notes stay in place for provenance. Only humans move notes to `95-archive/`.

See [../knowledge/promotion-model.md](../knowledge/promotion-model.md) for the full reasoning.

---

## Common pitfalls

See [../knowledge/common-pitfalls.md](../knowledge/common-pitfalls.md) for the recurring failure modes: unpinned citekeys, inbox accumulation, summaries masquerading as synthesis, and promotion anti-patterns.

---

## Related reference

- Frontmatter fields: [../../reference/frontmatter.md](../../reference/frontmatter.md)
- Note types (all 15, with templates): [../../reference/note-types.md](../../reference/note-types.md)
- Linking patterns: [../../reference/linking.md](../../reference/linking.md)
- On-disk layout (full tree): [../../reference/on-disk-layout.md](../../reference/on-disk-layout.md)
