---
title: CLI
parent: Agents and control
grand_parent: Reference
---

# CLI

`memoria` is the alpha.14 product surface. It operates on a standalone workspace
through `--workspace <path>` and does not require Hermes, Obsidian, or Zotero.

## Core

| Command | Purpose |
| --- | --- |
| `memoria init` | Create/scaffold a workspace. |
| `memoria status` | Show workspace state. |
| `memoria doctor bundle` | Emit a diagnostic bundle. |
| `memoria doctor self-test` | Run local runtime self-tests. |
| `memoria ask` | Answer a question from checked workspace retrieval. |

## Work

| Command | Purpose |
| --- | --- |
| `memoria work capture` | Capture a DOI, URL, PDF, file, or supplied text. |
| `memoria work import` | Import portable BibTeX or CSL JSON files. |
| `memoria work enrich` | Enrich a work from provider replay/payload inputs. |
| `memoria work digest` | Compile a source digest. |
| `memoria work interview` | Record source interview responses. |
| `memoria work update` | Update source/work metadata. |

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
| `memoria note capture/propose/accept/reject/link` | Manage PI notes and proposed note candidates. |
| `memoria project ask/trace/gaps/suggest-hubs/export` | Query and maintain project-level knowledge. |
| `memoria steering show/edit` | Read or update steering. |
| `memoria vocabulary list/add/rename` | Maintain controlled vocabulary. |
| `memoria journal list/show` | Inspect journal entries. |

## Operations And Eval

| Command | Purpose |
| --- | --- |
| `memoria operation list/run` | List and invoke capability operations. |
| `memoria eval run` | Run the vault eval. |
| `memoria eval seeded-error-verdict` | Run the seeded-error verdict gate. |

Run `memoria <command> --help` for exact flags.
