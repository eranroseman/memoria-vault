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
| `memoria doctor bundle` | Emit a diagnostic bundle and propagate the same failing backup-health status. |
| `memoria doctor self-test` | Run local runtime self-tests. |
| `memoria secrets set <NAME>` | Store one named user-scope secret without echoing its value. |
| `memoria secrets list` | Report credential status and provenance without printing secret values. |
| `memoria ask` | Answer a question from checked workspace retrieval. |
| `memoria explore <topic> [--versus <topic>] [--project <project>] [--depth 1\|2]` | [Surface a checked topic neighborhood](../../how-to-guides/knowledge/explore-a-topic-neighborhood.md). This is distinct from `memoria project explore`, which lists exploration-channel candidates. |
| `memoria serve --watch` | Run the polling file-watch loop over the same scan engine. |
| `memoria serve --http [--read-scope <path>]` | Run the [local HTTP transport](local-http-transport.md) over `engine/api`, optionally capped to one or more read scopes. That reference defines its loopback, authentication, rendezvous, and on-demand lifecycle contract. |
| `memoria serve --stop` | Stop the live local HTTP server for this workspace after validating its runtime coordinates. |
| `memoria handshake --vault <path> [--spawn]` | Return live local HTTP coordinates for a vault; `--spawn` starts an on-demand ephemeral server when none is live. |
| `memoria mcp --workspace <path> --read-scope <path>` | Run the optional [MCPServer stdio transport](mcp-transport.md) with a required engine read scope. |
| `memoria help` | Show registered surfaces grouped by the five workspace jobs. |
| `memoria dashboard` | Print the seven raw-count instrumentation panels (attention flow, dispositions, evidence review, reads/staleness, edge writes, exploration, decision rules). Engine-direct and read-only; raw counts with their denominators, never a composite score. The same panels are served over HTTP at `/v1/views/dashboard`. |
| `memoria cockpit [--project <path>\|--triage]` | Compose the deep-work or triage cockpit screens from registry reads. `--project` selects the deep screen, `--triage` the triage screen; the two never mix. |
| `memoria context` | Read the situated context bundle for the active session. |
| `memoria onboard` | Walk from installed engine to the tutorial open in Obsidian. |
| `memoria eval select-models [--operation <id>] [--mode test\|live]` | Run the seeded-error bar against manifest-declared runner pins and report the selected passing runner. |

## Work

| Command | Purpose |
| --- | --- |
| `memoria work add` | Add a DOI, URL, PDF, or file; attach supplied text with `--text`. |
| `memoria work import` | Import portable BibTeX or CSL JSON files. |
| `memoria seed install` | Install the shipped seed-corpus manifest rows as unchecked catalog Work rows — pinned identifiers, keyless fetches; re-runs skip already admitted rows. PI-only. |
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
| `memoria attention list/show/resolve/worklist` | Review PI attention items. Listings are engine-ordered: blocking cards pin to the top, then `priority: high`, loudness band, project impact, staleness, and oldest-first age as the final tiebreaker. Every row discloses the factors it was ranked on (`rank_factors` in the JSON payload). `list --order-by priority,age` reorders or drops factors for one invocation; the block pin is not a factor and always sorts first. |

## Knowledge And Projects

| Command | Purpose |
| --- | --- |
| `memoria new note/hub/project` | Author new Concepts through the CLI's code-owned frontmatter/body contract. |
| `memoria link` | Curate a PI-owned typed relation between checked Concepts. |
| `memoria mv <old_path> <new_path>` | PI-only rename of a note, hub, or project file; inbound `links:` entries and the Concept's DB `path` move with it in one trusted-writer commit, and the frontmatter `id` identity never changes. |
| `memoria check` | Mark a Concept checked as the PI, or run integrity-owned workspace checks when no target is given. |
| `memoria show/list [--type note\|work\|hub\|project]/export` | Inspect and export Concepts; `--type` filters to exactly one type per invocation — `list --type work` enumerates only catalog Works, never merged with note/hub/project Concepts. |
| `memoria project ask/trace/gaps/frame-paper/slice/compose/verify/resolve-evidence/promote/explore/suggest-hubs/export` | Query, frame, write, verify, record evidence-review dispositions, promote, explore, and export project-level knowledge. Framing, evidence dispositions, and promotion are PI-only. |
| `memoria review list/show/accept/reject/edit/defer/stats` | Work the evidence-set review queue: list and inspect held evidence sets, record one of the four dispositions, and read the review telemetry summary. Engine-direct and PI-only; dispositions go through the same seam as `memoria project resolve-evidence`. See [Evidence-set review](../analysis-and-surfaces/evidence-review.md). |
| `memoria steering show/edit` | Show effective steering—derived from active projects, hubs, and unresolved question notes—with per-token provenance; edit the PI-owned `steering.md` watch/mute override. |
| `memoria decision-rule set <id> <status>` | Record a pre-registered decision rule as `armed`, `fired`, or `retired` in `.memoria/config/decision-rules.yaml`. PI-only. The first write materializes the whole shipped registry, so the file never carries fewer rules than the engine ships — a hand-edited one-entry file would replace the registry rather than override one row of it. |
| `memoria vocab list/add/rename/merge` | Read controlled vocabulary; mutations are PI-only. |
| `memoria journal tail/show/verify/revert-preview` | Inspect journal entries; verify the authoritative hash chain, live-tip anchor, committed anchor prefix, and JSONL export subset; `revert-preview <event-id>` renders the read-only cascade-rollback preview for one event. |

## Operations And Eval

| Command | Purpose |
| --- | --- |
| `memoria operation list/run [--mode test\|live]` | List and invoke capability operations with the selected manifest-pinned runner branch. |
| `memoria eval run` | Run the vault eval. |
| `memoria eval seeded-error-verdict [--mode test\|live]` | Run the seeded-error verdict gate for the selected manifest-pinned runner branch. |

## Complete command roster

This roster mirrors the live argparse tree; `scripts/checks/doc_claims_gate.py`
pins the two equal in both directions:

- `memoria ask`
- `memoria attention list`
- `memoria attention resolve`
- `memoria attention show`
- `memoria attention worklist`
- `memoria check`
- `memoria cockpit`
- `memoria context`
- `memoria dashboard`
- `memoria decision-rule set`
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
- `memoria journal revert-preview`
- `memoria journal show`
- `memoria journal tail`
- `memoria journal verify`
- `memoria link`
- `memoria list`
- `memoria mcp`
- `memoria mv`
- `memoria new hub`
- `memoria new note`
- `memoria new project`
- `memoria onboard`
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
- `memoria review accept`
- `memoria review defer`
- `memoria review edit`
- `memoria review list`
- `memoria review reject`
- `memoria review show`
- `memoria review stats`
- `memoria secrets list`
- `memoria secrets set`
- `memoria seed install`
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
`--mode claim|question|definition|work`, `--work-id` to link the note to a
source Work (required when `--mode work`), and a repeatable `--tag` (may be
passed multiple times). `memoria new
hub` accepts `--description` plus optional `--body`;
`memoria new project` accepts `--description` plus optional `--direction`. The
generated files include the same frontmatter defaults and body heading shape as
the CLI concept writers.

Most workspace commands accept `--workspace <path>` and `--json`. `--actor`
records declared provenance; the raw local CLI does not authenticate its caller
and must remain a PI-owned surface. Do not expose it to an untrusted agent.

## Output conventions

Without `--json`:

| Outcome | Printed |
| --- | --- |
| Success with a reportable detail | One allowlisted path, identifier, count, or status. |
| Success with no detail | `ok` |
| Success with an opaque result | A pointer to `--json`. |
| Failure | `FAILED: <detail>` — the engine's error, evidence, or status, or `operation failed` when none is available — with a nonzero exit. Never a path or success token for an operation the engine did not perform. |

The generic presenter never prints a complete worker request, result payload,
or Concept body; use `--json` for full machine-readable operation details. In
`--json` mode a failure carries `"ok": false` alongside the same failing
detail.

## Recorded actor by door

| Door | Request actor | Concept bodies |
| --- | --- | --- |
| CLI | declared via `--actor` | PI-typed body written verbatim. |
| [MCP](mcp-transport.md) | `agent` | Machine-authored; neutralized before write. |
| Loopback [HTTP](local-http-transport.md) | `pi` — the caller is the PI's own editor plugin holding the per-boot token | Machine-authored; neutralized before write. |
| `workspace scan`, `workspace check`, and `serve --watch` scans | `integrity` | — |

`memoria mcp` has no `--json` mode, requires `--read-scope`, and uses
`--actor` only as the concrete agent identity recorded in provenance.

## Request controls

All request controls are PI-only, as are `memoria project resolve-evidence`,
`memoria review accept`/`reject`/`edit`/`defer`, `memoria steering edit`,
`memoria decision-rule set`, and vocabulary mutations.

| Control | Accepts | Effect |
| --- | --- | --- |
| `request answer` / `request amend` | A source request; each call requires a fresh `--idempotency-key`. | Creates a PI-attributed successor without changing the source envelope. A pending source is cancelled as superseded; a terminal source stays terminal and is marked superseded. The successor records the source in provenance and causal references and does not inherit the source schedule. |
| `request cancel` | `pending` only | Cancels the request. |
| `request retry` | `failed`, or explicitly cancelled work that has not been superseded | Re-runs the request. |
| `request resume` | `pending` only | Claims and runs the request. |

Successor rules: one source has one successor — an exact repeat with the same
key and content reuses it; changed content or a second successor is rejected.
An amendment cannot change scope-bearing ID, reference, path, or target
fields; submit a new operation for a different scope. Integrity-only requests
cannot be cloned by a PI request control. If a transition commits but its
lifecycle event does not, an exact repeat repairs that one missing event
without creating another successor or reopening finished work.
