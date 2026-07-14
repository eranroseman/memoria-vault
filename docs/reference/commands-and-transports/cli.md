---
title: CLI
parent: Commands and transports
nav_order: 7
grand_parent: Reference
---

# CLI

`memoria` is the standalone product surface. It operates on a workspace through
`--workspace <path>` and does not require optional adapters.
This page mirrors `src/memoria_vault/cli.py` and is kept in sync by hand.

## Core

| Command | Purpose |
| --- | --- |
| `memoria init [--no-obsidian]` | Create/scaffold a workspace. By default it seeds Memoria's Obsidian plugin and core settings; `--no-obsidian` skips `.obsidian/`. |
| `memoria status` | Show workspace state. |
| `memoria surface schema --json` | Print the shared surface-contract action registry used by CLI/HTTP/MCP drift checks. |
| `memoria doctor --check search` | Check local search index state. |
| `memoria doctor --check runner [--provider local\|gateway] [--repair]` | Check the configured pydantic-ai runner provider; add `--live` for an opt-in model dispatch. `--repair` reseeds workspace scaffold files (overwriting existing ones) before reporting. |
| `memoria doctor` | Report local runtime checks and backup health. It exits nonzero when blob files lack configured coverage or a current valid local-backup stamp. |
| `memoria doctor bundle [--redacted]` | Emit a diagnostic bundle and propagate the same failing backup-health status; `--redacted` marks the bundle as redacted for sharing. |
| `memoria doctor self-test` | Run local runtime self-tests. |
| `memoria ask` | Answer a question from checked workspace retrieval. |
| `memoria serve --watch` | Run the on-demand file-watch loop over the same scan engine. |
| `memoria serve --http [--read-scope <path>]` | Run the token-authenticated [local HTTP transport](local-http-transport.md) over `engine/api`, optionally capped to one or more read scopes. |
| `memoria migrate --from-alpha15 <path>` | Import an alpha.15 vault into the current root layout. |
| `memoria mcp --workspace <path> --read-scope <path>` | Run the optional [FastMCP stdio transport](mcp-transport.md) with a required engine read scope. |
| `memoria eval select-models [--operation <id>] [--mode test\|live]` | Run the seeded-error bar against manifest-declared runner pins and report the selected passing runner. |

## Work

| Command | Purpose |
| --- | --- |
| `memoria work add` | Add a DOI, URL, PDF, or file; attach supplied text with `--text`. |
| `memoria work import` | Import portable BibTeX or CSL JSON files. |
| `memoria work enrich <work-id>` | Enrich a work from provider replay/payload inputs. |
| `memoria work digest <work-id> [--mode test\|live]` | Compile a source digest with the selected manifest-pinned runner branch. |
| `memoria work interview <work-id>` | Record PI-owned source interview responses. |
| `memoria work update <work-id> [--research-area <term>] [--methodology <term>]` | Apply PI-owned source/work metadata changes. Classification flags are repeatable; Work has no `--topic` flag. |
| `memoria work export <work-id>` | Export a catalog work record. |

## Requests And Workspace

| Command | Purpose |
| --- | --- |
| `memoria request list/show` | Inspect operation requests. |
| `memoria request answer/amend/cancel/retry/resume` | PI-only request lifecycle controls. Answer and amend create a successor, cancel and retry change eligible states, and resume runs pending work. |
| `memoria workspace backup <target>` | PI-only coherent backup of SQLite, blobs, and journal head into a manifest-bound directory outside the live vault. |
| `memoria workspace restore <source> [--force]` | PI-only validated, rollback-capable restore; `--force` is required while a live database exists. |
| `memoria workspace recover` | PI-only recovery of interrupted backup publication, restore, request, and materialization work. |
| `memoria workspace scan/run/rollback/check/rebuild/export` | Observe valid direct Concept edits under bundle roots; quarantine changed tracked projections; regenerate projections with a current owner (add `--search` to `rebuild` to also rebuild the search index); and run queued work. An orphan `projects/<project>/argument.canvas` remains quarantined. |
| `memoria attention list/show/resolve/worklist` | Review PI attention items. |

## Knowledge And Projects

| Command | Purpose |
| --- | --- |
| `memoria new note/hub/project` | Author new Concepts through the CLI's code-owned frontmatter/body contract. |
| `memoria link` | Curate a PI-owned typed relation between checked Concepts. |
| `memoria check` | Mark a Concept checked as the PI, or run integrity-owned workspace checks when no target is given. |
| `memoria show/list [--type note\|work\|hub\|project]/export` | Inspect and export Concepts; `--type` filters to exactly one type per invocation — `list --type work` enumerates only catalog Works, never merged with note/hub/project Concepts. |
| `memoria project ask/trace/gaps/frame-paper/slice/compose/verify/resolve-evidence/promote/explore/suggest-hubs/export` | Query, frame, write, verify, record evidence-review dispositions, promote, explore, and export project-level knowledge. Framing, evidence dispositions, and promotion are PI-only. |
| `memoria steering show/edit` | Read steering; editing is PI-only. |
| `memoria vocab list/add/rename/merge` | Read controlled vocabulary; mutations are PI-only. |
| `memoria journal tail/show/verify` | Inspect journal entries or verify the authoritative hash chain, live-tip anchor, committed anchor prefix, and JSONL export subset. |

## Operations And Eval

| Command | Purpose |
| --- | --- |
| `memoria operation list/run [--mode test\|live]` | List and invoke capability operations with the selected manifest-pinned runner branch. |
| `memoria eval run` | Run the vault eval. |
| `memoria eval seeded-error-verdict [--mode test\|live]` | Run the seeded-error verdict gate for the selected manifest-pinned runner branch. |

## Complete command roster

This roster mirrors the live argparse tree:

- `memoria ask`
- `memoria attention list`
- `memoria attention resolve`
- `memoria attention show`
- `memoria attention worklist`
- `memoria check`
- `memoria doctor bundle`
- `memoria doctor self-test`
- `memoria eval run`
- `memoria eval seeded-error-verdict`
- `memoria eval select-models`
- `memoria export`
- `memoria init`
- `memoria journal show`
- `memoria journal tail`
- `memoria journal verify`
- `memoria link`
- `memoria list`
- `memoria mcp`
- `memoria migrate`
- `memoria new hub`
- `memoria new note`
- `memoria new project`
- `memoria operation list`
- `memoria operation run`
- `memoria project ask`
- `memoria project compose`
- `memoria project explore`
- `memoria project export`
- `memoria project frame-paper`
- `memoria project gaps`
- `memoria project promote`
- `memoria project resolve-evidence`
- `memoria project slice`
- `memoria project suggest-hubs`
- `memoria project trace`
- `memoria project verify`
- `memoria request amend`
- `memoria request answer`
- `memoria request cancel`
- `memoria request list`
- `memoria request resume`
- `memoria request retry`
- `memoria request show`
- `memoria serve`
- `memoria show`
- `memoria status`
- `memoria steering edit`
- `memoria steering show`
- `memoria surface schema`
- `memoria vocab add`
- `memoria vocab list`
- `memoria vocab merge`
- `memoria vocab rename`
- `memoria work add`
- `memoria work digest`
- `memoria work enrich`
- `memoria work export`
- `memoria work import`
- `memoria work interview`
- `memoria work update`
- `memoria workspace backup`
- `memoria workspace check`
- `memoria workspace export`
- `memoria workspace rebuild`
- `memoria workspace recover`
- `memoria workspace restore`
- `memoria workspace rollback`
- `memoria workspace run`
- `memoria workspace scan`

Run `memoria <command> --help` for exact flags.

`memoria new note` accepts `--description` plus `--body` or `--file`, optional
`--mode claim|question|definition|work`, `--work-id` when `--mode work` is
selected, and a repeatable `--tag` (may be passed multiple times). `memoria new
hub` accepts `--description` plus optional `--body`;
`memoria new project` accepts `--description` plus optional `--direction`. The
generated files include the same frontmatter defaults and body heading shape as
the CLI concept writers.

Most workspace commands accept `--workspace <path>` and `--json`. `--actor`
records declared provenance; the raw local CLI does not authenticate its caller
and must remain a PI-owned surface. Do not expose it to an untrusted agent.
Without `--json`, a successful command prints an allowlisted path, identifier,
count, or status when one is available. A detail-free success prints `ok`, and
an opaque result points to `--json`; the generic presenter never prints a
complete worker request, result payload, or Concept body. Use `--json` for full
machine-readable operation details. When a command fails, the non-`--json`
presenter prints `FAILED: <detail>` — the engine's error, evidence, or status,
or `operation failed` when none is available — and the command exits nonzero;
it never prints a path or success token for an operation the engine did not
perform. In `--json` mode the payload carries `"ok": false` alongside the same
failing detail.
Agent-facing adapters use [HTTP](local-http-transport.md) or
[MCP](mcp-transport.md), which always record request actor `agent`.
`workspace scan`, `workspace check`, and scans performed by `serve --watch`
always record actor `integrity`. `memoria mcp` has no `--json` mode, requires
`--read-scope`, and uses `--actor` only as the concrete agent identity recorded
in provenance.

`memoria request answer` and `memoria request amend` are PI-only. Each requires
a fresh `--idempotency-key`, creates a PI-attributed successor request, and
cancels a pending source as superseded without changing its envelope. A
terminal source stays terminal and is marked as superseded. The successor
records the source in provenance and causal references, and it does not inherit
the source schedule. One source can have one successor: an exact repeat with
the same key and content reuses it; changed content or a second successor is
rejected.
An amendment cannot change scope-bearing ID, reference, path, or target fields;
submit a new operation for a different scope.
Integrity-only requests cannot be cloned by a PI request control.
`cancel`, `retry`, and `resume` are PI-only lifecycle controls. Cancel accepts only
`pending`; retry accepts `failed` or explicitly cancelled work that has not
been superseded; resume claims and runs only `pending`. If a transition commits
but its lifecycle event does not, an exact repeat repairs that one missing event
without creating another successor or reopening finished work. `memoria project
resolve-evidence`, `memoria steering edit`, and vocabulary mutations are also
PI-only.
