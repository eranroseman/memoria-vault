---
topic: profiles
---

# Lane naming

Memoria has **one** lane identifier: the **assignee** — the `memoria-<name>` profile id the Kanban dispatcher routes by. There is no separate lane token. This matches Hermes exactly: a task carries an `assignee` field and **no `lane` field** — "each lane has an identity (the assignee string)."

## The canonical table

| Profile (prose) | Assignee = lane id (the routing token) | Lane-override file | Loads skills for |
| --- | --- | --- | --- |
| Librarian | `memoria-librarian` | `.memoria/lane-overrides/librarian.yaml` | discover, ingest, enrich, classify |
| Mapper | `memoria-mapper` | `.memoria/lane-overrides/mapper.yaml` | scope-project, gap-report, cluster-mapping, comparative-brief |
| Socratic | `memoria-socratic` | `.memoria/lane-overrides/socratic.yaml` | socratic-processing, lens-reading |
| Writer | `memoria-writer` | `.memoria/lane-overrides/writer.yaml` | llm-wiki-draft, counter-outline, note-refactor, scientific-writing |
| Verifier | `memoria-verifier` | `.memoria/lane-overrides/verifier.yaml` | cite-check, similarity-check, find-duplicates, retraction-check |
| Coder | `memoria-coder` | `.memoria/lane-overrides/coder.yaml` | scaffold-code-note, workspace-coordinate, commit-and-document |
| Linter | `memoria-linter` | `.memoria/lane-overrides/linter.yaml` | schema-check, graph-analyze, health-report, session-log |

## Three forms, one token

- **Prose short name** — "the Librarian lane" / "Librarian." Use in narrative.
- **Filename** — `librarian.yaml`. A convenience only; the override is keyed by its `profile:` field, not the filename.
- **Assignee = lane id** — `memoria-librarian`. **The only token the board, cron, and skills route by.** Use it in every machine-read slot: `task.assignee`, `hermes kanban create "…" --assignee memoria-<name>`, a cron job's `assignee:`, a `skill-note`'s `lane:`, a command payload's `assignee:`.

## What not to do

- **No `lane:` key in a lane-override file.** The file's `profile: memoria-<name>` is the identity; a second `lane:` token (the retired `library` / `mapping` / `verification` style) re-introduces the lane↔profile mapping the design exists to remove — and it drifts (`verify` vs `verification`, `writer` vs `writing`).
- **No stray lane words** (`library`, `mapping`, `writing`, `coding`, `verification`, `linting`) in prose or config. A lane is named by its assignee.

## Why one token

The dispatcher routes by matching `task.assignee` to a profile — there is nothing else to match against. A separate lane name would need a lane→profile lookup table that can (and did) drift out of sync. Collapsing to the assignee makes routing a string compare and removes the drift surface entirely. See [Routing without an Orchestrator](../explanation/profiles/README.md#routing-without-an-orchestrator) and the [glossary](glossary.md) **Lane** entry.
