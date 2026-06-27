---
title: The vault
parent: Architecture
nav_order: 1
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria — the board, the agents, the operations, the dashboards — exists to serve it. This page explains its structure: the category folders, the type homes, the gated zones, and the conventions that keep it sound.

---

## Category folders, not lifecycle numbers

The top level is organized by **category** — one content kind per folder, no lifecycle numbers ([ADR-47](../../adr/47-type-first-category-folders.md)). The knowledge is a *network*, not a pipeline: direction lives in the state property, not in folder ordering.

```text
<vault-root>/
├── home.md         ← launch/reset welcome note
├── catalog/        ← CATALOG: structured entity records (Obsidian Bases)
│   papers · people · organizations · venues · datasets · repositories
├── notes/          ← NOTES: prose (Zettelkasten)
│   fleeting/ · sources/ · claims/ 🔒 · hubs/ 🔒 · indexes/
├── projects/       ← PROJECTS: work artifacts, project-scoped
├── inbox/          ← INBOX: agent→human messages — candidate · gap · flag · alert · work-prompt cards
├── spaces/         ← SPACES: persistent Obsidian dashboard notes for the four working modes
├── system/         ← SYSTEM: visible infrastructure — logs · templates · patterns · dashboards · board
├── .obsidian/      ← hidden Obsidian app config (Bases definitions, layouts)
└── .memoria/       ← hidden runtime (MCP, profiles, schemas, golden copy)
```

**One folder never mixes two categories**, and folders are named for their *content*, not for a doer — both the ingest operation and the Librarian agent operate *on* `catalog/`. The type → folder-home map is machine-read (`.memoria/schemas/folders.yaml`) and is the single source for the Linter, the policy gate, the installer skeleton, and the tests.

## Types and their homes

Each category houses a fixed set of types — Catalog entity records, the prose Notes (fleeting, source, claim 🔒, hub 🔒), project work artifacts, Inbox cards, Space notes, and System infrastructure. The architectural distinction is the trust posture each carries: Catalog frontmatter is **given facts** built by ingest and **not gated** (one escape valve — low-confidence extraction routes to a `flag`, [ADR-56](../../adr/56-extraction-uncertainty-flag.md)), while the claim and hub are the PI's **judgment**. The full type roster and its folder homes are in [Document types](../../reference/document-types.md).

## Gated zones

The review-gated zones 🔒 are structurally protected: no agent writes there without the PI's approval, enforced by the policy MCP. Agents *propose* (cards, staging artifacts); the PI *disposes*. The Catalog is deliberately ungated: its content is given facts, not judgment. Which prefixes are gated is owned by [Document types](../../reference/document-types.md).

## Archived is a state, not a folder

Everything the PI sees uses one lifecycle chain ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md), enumerated in [Frontmatter fields](../../reference/frontmatter.md)), each type using a subset. The architectural point is that a state change is a frontmatter edit, never a file move: an archived note stays in its type-home and drops from active views, preserving links and provenance. There is no archive folder. Likewise `links:` on notes are authored connections the PI confirms, while `relationships` on entities are given facts built by ingest ([ADR-52](../../adr/52-links-vs-relationships.md)) — two kinds of connection, two trust models; their field contract is in [Frontmatter fields](../../reference/frontmatter.md).

## Bases is the view layer; the Linter keeps it sound

Catalog entities (and the Inbox board, and the per-type note queues) surface through **Obsidian Bases** — saved database views over frontmatter. Every row is a file; the records are the source of truth; nothing reads a Base as data ([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)).

Bases has no integrity guarantees — no schema, no constraints. That gap is the **Linter operation's** job: it validates every record against its type schema in `.memoria/schemas/` (required fields, value types, enum vocabularies, `links:`/`relationships` resolving to real targets) and flags drift as Inbox `flag`s. It is a **monitor and a commit gate**: a pre-commit `schema-check` gates git-tracked writes at commit, and the cron/CI sweep monitors between commits. It does not block a live in-app edit — between a bad edit and the next sweep a Base can briefly serve a malformed record; that window is accepted under the solo premise and bounded by the commit gate. On detected drift in system files, the Linter can restore from the golden copy ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)).

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The agent→human signal folder in depth: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- The operations that maintain the vault: [Operations](../operations/README.md)
- Why the review gate is structural: [Why the review gate is structural](../../design/why-human-gate.md)
