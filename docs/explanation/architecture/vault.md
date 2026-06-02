---
title: The vault
parent: Architecture
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria — the board, the profiles, the dashboards — exists to serve it. This document explains the vault's structure: what the folders mean, how notes move through it, and the conventions that keep it navigable.

For the conceptual model behind the design choices (why lifecycle folders, what note types represent, why promotion is gated), see [Knowledge](../knowledge/).

---

## Folder structure

Folders encode **lifecycle stage**, not subject area. The top-level number indicates where in the capture → describe → think → work → ship progression a note sits.

```text
<vault-root>/
├── home.md              ← front door (obsidian-homepage opens it on launch)
├── research-directions.md  ← Librarian's session-start input (human-edited)
├── troubleshooting.md   ← offline-fallback help (kept in-vault by design)
├── 00-meta/             ← the human's read surface: dashboards
│   └── 01-dashboards/
│   (reference notes live on the website; templates live in 99-system/)
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
├── 99-system/           ← machine-consumed/generated, Obsidian-visible: logs, board, metrics, eval, skills, templates
│   ├── logs/
│   ├── board/
│   ├── metrics/
│   ├── eval/
│   ├── skills/
│   └── templates/      ← 16 note templates (QuickAdd instantiates these)
├── .obsidian/           ← Obsidian config (auto-hidden)
└── .memoria/            ← Memoria tooling (auto-hidden)
    ├── profiles/        ← seven Hermes profile directories
    ├── mcp/
    ├── lane-overrides/
    └── memoria.bib
```

The four **review-gated zones** (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) are structurally protected — no profile can write to them without a human `review_status: approved`. The policy MCP enforces this at the filesystem level.

---

## Why the structure is this way

**Lifecycle over topic** — a paper about attention lives in `20-sources/01-papers/`, not `cognitive-science/`. Topics live in frontmatter where they can be many-to-many; lifecycle stage lives in the folder where it is one-to-one. See [Why folders encode lifecycle, not topic](../knowledge/lifecycle-over-topic.md).

**`30-synthesis/` is human territory** — claim notes and MOCs are human-authored. Agents draft candidates that land in `10-inbox/`; the human writes the canonical synthesis. The review-gated-zone deny rule enforces this structurally.

**`40-workbench/` groups by project — the downstream half of the same principle.** The upstream zones (`10`–`30`) hold a *web* of notes, navigated many-to-many through MOCs and queries; the workbench holds the *downstream*, where one project distills a single train of thought. Its sub-folders (`01-map`, `02-framing`, `04-drafts`, …) are the stages of that one thread, and the whole project archives as a unit when it ships. A project is not a topic — it's a bounded, transient effort. See [lifecycle-over-topic.md → "The workbench"](../knowledge/lifecycle-over-topic.md#the-workbench-web-upstream-thread-downstream).

**`90-assets/` does not hold PDFs** — PDFs live in Zotero's storage; paper notes reference them via `pdf_uri`. `90-assets/` holds Marker-extracted markdown and binary attachments.

---

## Special files

A small set of singleton files at the **vault root** shape how the system runs:

| File | Purpose | Owned by |
|---|---|---|
| `home.md` | The front door, opened on launch by obsidian-homepage. One status glance, then links to the dashboards, the in-vault help note, and the website. | Human (rarely changes) |
| `research-directions.md` | Current research priorities and synthesis gaps. The Librarian reads this at session start. An empty or stale file produces an unfocused Librarian. | Human (refresh weekly) |
| `troubleshooting.md` | Offline-fallback help: verify the plumbing, the three core workflows (ingest / review / export) with minimal commands, and recovery. Folds in the former runtime-health snapshot. Kept in-vault — needed precisely when Hermes or ACP is down. | Human (rarely changes) |

---

## Promotion map

Knowledge moves left-to-right through the folder numbers: capture (`10-inbox/`) into sources (`20-sources/`) or synthesis (`30-synthesis/`), and on to deliverables (`50-deliverables/`). Each move is a *promotion* — a fleeting note becomes a classified paper- or item-note (Librarian enriches, human classifies) or a claim note (human writes directly); an answer note distills into a claim note; a claim note matures into a reference note or joins a MOC; a draft exports to a deliverable. A `paper-note` never becomes a `claim-note` directly — the distinction between "what the source says" and "what the human thinks" is preserved. Archived notes stay in place for provenance, and only humans move notes to `95-archive/`.

The move-by-move map, the disallowed moves, and the reasoning behind the synthesis gate live in [Why promotion is gated](../knowledge/promotion-model.md) — the single source for the promotion model. This overview states the path in prose rather than reproducing the diagram, so the two cannot drift.

---

## Common pitfalls

See [Common pitfalls](../knowledge/common-pitfalls.md) for the recurring failure modes: unpinned citekeys, inbox accumulation, summaries masquerading as synthesis, and promotion anti-patterns.

---

## Related

**Explanation**

- Why notes move through the folders: [The knowledge cycle](../knowledge/knowledge-cycle.md)
- Why review-gated zones exist: [Why the review gate is structural](../rationale/why-human-gate.md)
- How the vault ships and deploys: [Distribution model](../deployment/distribution-model.md)

**Reference**

- Frontmatter fields: [Frontmatter fields](../../reference/frontmatter.md)
- Note types (all 16, with templates): [Note types](../../reference/note-types.md)
- Linking patterns: [Wikilink and link conventions](../../reference/linking.md)
- On-disk layout (full tree): [On-disk layout](../../reference/on-disk-layout.md)
