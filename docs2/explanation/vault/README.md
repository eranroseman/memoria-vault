---
status: stub
---

# Vault

> **Stub** — this section explains the vault's structure: the folder model, note types in context, the promotion map, and common pitfalls.

## What goes here

The vault is the durable knowledge layer of Memoria. This section covers the conceptual model behind its organization.

### Planned documents

- **[folder-structure.md](folder-structure.md)** — the full folder tree with each folder's role, access rules, and the relationship between `.memoria/` tooling and the numbered content folders.
- **[promotion-map.md](promotion-map.md)** — legal lifecycle transitions, with the rules that constrain each one.
- **[special-files.md](special-files.md)** — the singleton files in `00-meta/` that shape how the system runs: `research-directions.md`, `system-status.md`, the skeleton reference notes.
- **[pitfalls.md](pitfalls.md)** — common failure modes in capture, synthesis, and promotion, and how to recognize them.

## Overview

The conceptual principles behind the vault's design:

- Why folders encode lifecycle, not topic: [../knowledge/lifecycle-over-topic.md](../knowledge/lifecycle-over-topic.md)
- The three epistemic roles of notes: [../knowledge/note-types.md](../knowledge/note-types.md)
- Why promotion is gated: [../knowledge/promotion-model.md](../knowledge/promotion-model.md)

For the complete folder tree and access tables, see [reference/note-types.md](../../reference/note-types.md).
