---
title: CLI
parent: Agents and control
grand_parent: Reference
---

# CLI

`memoria` is the alpha.15 product surface. It operates on a standalone workspace
through `--workspace <path>` and does not require Hermes, Obsidian, or Zotero.

## Core

| Command | Purpose |
| --- | --- |
| `memoria init` | Create/scaffold a workspace. |
| `memoria status` | Show workspace state. |
| `memoria doctor --check qmd` | Check required qmd search prerequisites. |
| `memoria doctor --check runner [--provider local\|gateway]` | Check the configured pydantic-ai runner provider; add `--live` for an opt-in model dispatch. |
| `memoria doctor bundle` | Emit a diagnostic bundle. |
| `memoria doctor self-test` | Run local runtime self-tests. |
| `memoria ask` | Answer a question from checked workspace retrieval. |

## Work

| Command | Purpose |
| --- | --- |
| `memoria work add` | Add a DOI, URL, PDF, file, or supplied text. |
| `memoria work import` | Import portable BibTeX or CSL JSON files. |
| `memoria work enrich <work-id>` | Enrich a work from provider replay/payload inputs. |
| `memoria work digest <work-id> [--mode test\|live]` | Compile a source digest with the selected manifest-pinned runner branch. |
| `memoria work interview <work-id>` | Record source interview responses. |
| `memoria work update` | Update source/work metadata. |
| `memoria work export <work-id>` | Export a catalog work record. |

## Requests And Workspace

| Command | Purpose |
| --- | --- |
| `memoria request list/show` | Inspect operation requests. |
| `memoria request answer/amend/cancel/retry/resume` | Continue or change a request. |
| `memoria workspace scan/run/recover/rollback/check/rebuild/export` | Observe file edits, run queued work, recover interrupted work, and maintain projections/search. |
| `memoria attention list/show/resolve/worklist` | Review PI attention items. |

## Knowledge And Projects

| Command | Purpose |
| --- | --- |
| `memoria new note/hub/project` | Author new Concepts. |
| `memoria link` | Curate a typed relation between checked Concepts. |
| `memoria check` | Mark a Concept checked, or run workspace checks when no target is given. |
| `memoria show/list/export` | Inspect and export Concepts. |
| `memoria project ask/trace/gaps/frame-paper/suggest-hubs/export` | Query, frame, and maintain project-level knowledge. |
| `memoria steering show/edit` | Read or update steering. |
| `memoria vocab list/add/rename/merge` | Maintain controlled vocabulary. |
| `memoria journal tail/show` | Inspect journal entries. |

## Operations And Eval

| Command | Purpose |
| --- | --- |
| `memoria operation list/run [--mode test\|live]` | List and invoke capability operations with the selected manifest-pinned runner branch. |
| `memoria eval run` | Run the vault eval. |
| `memoria eval seeded-error-verdict [--mode test\|live]` | Run the seeded-error verdict gate for the selected manifest-pinned runner branch. |

Run `memoria <command> --help` for exact flags.

Common runtime flags include `--workspace <path>`, `--json`, and
`--actor pi|agent`. The default actor is `pi`; shell agents should pass
`--actor agent` so queued writes record the correct request-envelope actor while
still landing unchecked.
