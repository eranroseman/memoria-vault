---
topic: general
---

# Memoria documentation

Memoria is a research operating system that turns sources into durable knowledge through explicit states, specialized Hermes profiles, and a Kanban board that preserves review, retries, and handoffs. This `docs/` tree is the authoritative documentation set: how to run it, how to extend it, and why it is built the way it is.

> **Designed vs. built.** These docs describe the intended system; the starter vault is an early scaffold that implements part of it. [project/implementation-status.md](project/implementation-status.md) is the source of truth for what ships today versus what is *accepted-pending* or *deferred*. A documented artifact that is missing from the vault is a known status — check the ledger before assuming an error.

## How these docs are organized

The four top-level folders follow the [Diátaxis][diataxis] convention — each holds one *kind* of writing, answering a different question:

| Folder | Mode | Answers |
| --- | --- | --- |
| [tutorials/](tutorials/) | Tutorial | "Teach me, from zero." Learning-oriented lessons, in order (01–05). |
| [how-to/](how-to/) | How-to | "How do I do this task?" Goal-oriented recipes. |
| [reference/](reference/) | Reference | "What is the exact value / field / command?" Lookup, no narrative. |
| [explanation/](explanation/) | Explanation | "Why is it built this way?" Concepts and design rationale. |

A fifth folder, [project/](project/), holds **out-of-compass records** — decisions (ADRs), roadmap, status, and evaluated alternatives. These are not one of the four modes; they document the project's history and direction rather than the system itself.

[diataxis]: https://diataxis.fr/

## Reading paths

### Running Memoria — you want to operate the system

1. Start with [tutorials/](tutorials/) — set up from zero, ingest a batch, run the Linter, promote a claim, add a profile.
2. Move to [how-to/](how-to/) for task recipes once you know the shape of the system.
3. Keep [reference/](reference/) open for lookups — the [glossary](reference/glossary.md), [frontmatter schema](reference/frontmatter-schema.md), [note types](reference/note-types.md), and [command catalog](reference/command-catalog.md).

### Extending Memoria — you want to understand or change the design

1. Start with [explanation/architecture/](explanation/architecture/) — the three-layer model (board, workers, vault) and why each layer exists.
2. Read [project/decisions/](project/decisions/) — the ADRs record *why* each non-trivial choice was made (and which were deferred).
3. Then [explanation/profiles/](explanation/profiles/) — the seven Hermes workers, their missions, lanes, and permissions.
4. Consult [project/roadmap/](project/roadmap/) for where the system is headed.

## Conventions

- **Relative Markdown links only.** Every cross-reference is a relative path so the tree is portable and renders on GitHub.
- **`topic:` frontmatter is kept; `mode:` and `audience:` are dropped.** The folder a file lives in now encodes its Diátaxis mode, so declaring the mode in frontmatter was redundant. Each file still carries a `topic:` field naming the concept it belongs to.
- **kebab-case on disk, snake_case in YAML.** Files and folders are kebab-case (`frontmatter-schema.md`); frontmatter *field* names are snake_case (`review_status`). `README.md`, `SOUL.md`, `AGENTS.md`, and `Home.md` are intentional exceptions (runtime conventions reused verbatim).

## Core idea, in one paragraph

The board (Kanban) is the control plane. The workers (Hermes profiles) are the execution layer. The vault (Obsidian folders) is the durable knowledge store. Cards on the board carry state; profiles claim cards within their lane and execute work; outputs land in the vault only after the human review state changes to `approved`. This keeps workflow state, execution, and final knowledge separate but connected through explicit handoffs.
