---
title: The vault
parent: Architecture
grand_parent: Explanation
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
├── spaces/         ← SPACES: three durable spaces plus the Inbox queue and Maintenance
├── system/         ← SYSTEM: visible infrastructure — logs · templates · patterns · dashboards · board
├── .obsidian/      ← hidden Obsidian app config (Bases definitions, layouts)
└── .memoria/       ← hidden runtime (MCP, profiles, schemas, golden copy)
```

**One folder never mixes two categories**, and folders are named for their *content*, not for a doer — both the ingest operation and the Librarian agent operate *on* `catalog/`. The type → folder-home map is machine-read (`.memoria/schemas/folders.yaml`) and is the single source for the Linter, the policy gate, the installer skeleton, and the tests.

## Types and their homes

Each category carries a different trust posture. The full roster and folder map live in [Document types](../../reference/document-types.md).

| Area | Examples | Trust posture |
| --- | --- | --- |
| Catalog | papers, people, organizations | Given facts from ingest; ungated except low-confidence extraction `flag`s ([ADR-56](../../adr/56-extraction-uncertainty-flag.md)). |
| Notes | fleeting, source, claim 🔒, hub 🔒 | Human-authored or human-approved knowledge; claim and hub are gated judgment. |
| Projects, Inbox, Spaces, System | work artifacts, cards, dashboards, infrastructure | Operational surfaces with type-specific lifecycle rules. |

## Gated zones

The review-gated zones 🔒 are structurally protected: no agent writes there without the PI's approval, enforced by the policy MCP. Agents *propose* (cards, staging artifacts); the PI *disposes*. The Catalog is deliberately ungated: its content is given facts, not judgment. Which prefixes are gated is owned by [Document types](../../reference/document-types.md).

## Archived is a state, not a folder

Everything the PI sees uses one lifecycle chain ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)); each type uses a subset. A state change is a frontmatter edit, never a file move: archived notes stay in their type-home, drop from active views, and keep their links. There is no archive folder.

The same trust split applies to connections: `links:` are authored note connections, while entity `relationships` are given facts from ingest ([ADR-52](../../adr/52-links-vs-relationships.md)). Field contracts live in [Frontmatter fields](../../reference/frontmatter.md).

## Bases is the view layer; the Linter keeps it sound

Catalog entities (and the Inbox board, and the per-type note queues) surface through **Obsidian Bases** — saved database views over frontmatter. Every row is a file; the records are the source of truth; nothing reads a Base as data ([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)).

Bases has no schema or constraints. The **Linter operation** supplies that layer: it validates records against `.memoria/schemas/`, flags drift, blocks malformed git-tracked writes at pre-commit, and monitors live edits through cron/CI sweeps. A bad in-app edit can briefly appear in a Base before the next sweep; that window is accepted under the solo premise. System-file drift can be restored from the golden copy ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)).

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The agent→human signal folder in depth: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- The operations that maintain the vault: [Operations](../operations.md)
- Why the review gate is structural: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
