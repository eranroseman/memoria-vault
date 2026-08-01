---
title: CLI
parent: Commands and transports
nav_order: 7
grand_parent: Reference
---

# CLI

`memoria` is the standalone product surface. It operates on a workspace through
`--workspace <path>` and does not require optional adapters.
This page summarizes `src/memoria_vault/cli.py`; use `--help` for exact flags.

## Core

| Command | Purpose |
| --- | --- |
| `memoria init [--no-obsidian]` | Create/scaffold a workspace. By default it seeds Memoria's Obsidian plugin, core settings, root Base views, and first-init agent/MCP host configuration. `--no-obsidian` skips only `.obsidian/` editor settings and root `.base` view settings; it still seeds the agent/MCP configuration. Before writing, init rejects planned paths that traverse a symlink or junction, plus Git-file and common-directory indirection. |
| `memoria status` | Show workspace state. |
| `memoria surface schema --json` | Print the shared surface-contract action registry used by CLI/HTTP/MCP drift checks. |
| `memoria doctor --check search` | Check local search index state. |
| `memoria doctor --check runner [--provider local\|gateway] [--repair]` | Check the configured pydantic-ai runner provider; add `--live` for an opt-in model dispatch. `--repair` restores runtime scaffold files and missing view preferences, while preserving existing PI-owned view preferences; it never recreates or overwrites the PI-owned first-init agent/MCP configuration. |
| `memoria doctor` | Report local runtime checks and backup health. It exits nonzero when blob files lack configured coverage or a current valid local-backup stamp. |
| `memoria doctor bundle [--redacted]` | Emit a diagnostic bundle and propagate the same failing backup-health status; `--redacted` marks the bundle as redacted for sharing. |
| `memoria doctor self-test` | Run local runtime self-tests. |
| `memoria secrets set <NAME>` | Store one named user-scope secret without echoing its value. |
| `memoria secrets list` | Report credential status and provenance without printing secret values. |
| `memoria ask` | Answer a question from checked workspace retrieval. |
| `memoria explore <topic> [--versus <topic>] [--project <project>] [--depth 1\|2]` | [Surface a checked topic neighborhood](../../how-to-guides/knowledge/explore-a-topic-neighborhood.md). This is distinct from `memoria project explore`, which lists exploration-channel candidates. |
| `memoria serve --watch` | Run the polling file-watch loop over the same scan engine. |
| `memoria serve --http [--read-scope <path>]` | Run the [local HTTP transport](local-http-transport.md) over `engine/api`, optionally capped to one or more read scopes. That reference defines its loopback, authentication, rendezvous, and on-demand lifecycle contract. |
| `memoria serve --stop` | Stop the live local HTTP server for this workspace after validating its runtime coordinates. |
| `memoria handshake --vault <path> [--spawn]` | Return live local HTTP coordinates for a vault; `--spawn` starts an on-demand ephemeral server when none is live. |
| `memoria mcp --workspace <path> --read-scope <path>` | Run the optional [FastMCP stdio transport](mcp-transport.md) with a required engine read scope. |
| `memoria help` | Show registered surfaces grouped by the five workspace jobs. |
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
| `memoria steering show/edit` | Show effective steering—derived from active projects, hubs, and unresolved question notes—with per-token provenance; edit the PI-owned `steering.md` watch/mute override. |
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
- `memoria doctor`
- `memoria doctor bundle`
- `memoria doctor self-test`
- `memoria eval run`
- `memoria eval seeded-error-verdict`
- `memoria eval select-models`
- `memoria export`
- `memoria explore`
- `memoria handshake`
- `memoria help`
- `memoria init`
- `memoria journal show`
- `memoria journal tail`
- `memoria journal verify`
- `memoria link`
- `memoria list`
- `memoria mcp`
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
- `memoria secrets list`
- `memoria secrets set`
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
[MCP](mcp-transport.md) is the agent-facing adapter and always records request
actor `agent`. The token-authenticated loopback
[HTTP](local-http-transport.md) transport records request actor `pi`, because
its caller is the PI's own editor plugin holding the per-boot token.
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
