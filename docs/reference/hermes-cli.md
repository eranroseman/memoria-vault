---
title: Hermes CLI
parent: Reference
---

# Hermes CLI

Every `hermes …` command-line operation: the per-profile research skills, the administrative commands (profiles, skills, cron), and the Kanban board commands. These are the **terminal** surface; the primary day-to-day surface is the co-PI conversation (the ACP pane), which delegates board work for you. For the in-Obsidian palette see [Obsidian command palette](obsidian-command-palette.md).

Command structure: `hermes <command> [subcommand] [args]` — runs from any directory; Hermes resolves the vault path from the profile's `config.yaml`. Per-profile sessions run as `hermes -p memoria-<name> chat` (or `hermes -p memoria-copi acp` for the desk pane).

---

## The profile set

Five profiles: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer` (see [Profile capabilities](profiles.md)). The v0.1.0-alpha.1 profiles `memoria-mapper` / `-socratic` / `-verifier` / `-coder` / `-linter` are retired; the installer prunes them.

---

## Skill names: the `<task>:<verb>-<object>` convention

Every skill follows **`<task>:<verb>-<object>`** (snake `<task>_<verb>_<object>` when serialized as an MCP tool; **hyphen-joined on disk and at the `-s` flag**, since directory and skill-load names cannot carry `:` — `catalog:enrich-record` lives in `skills/catalog-enrich-record/` and loads as `hermes -p memoria-librarian chat -s catalog-enrich-record`): the task/lane is the prefix, the verb comes from a closed set, the object is the artifact — so a skill's name says which task delegates it. The on-disk registry under `src/.memoria/profiles/<profile>/skills/` matches this table exactly (enforced by `tests/test_profiles.py`); **legacy v0.1.0-alpha.1 names in parentheses**:

| Actor | Skills (all shipped in `src/.memoria/profiles/<profile>/skills/`) |
| --- | --- |
| **co-PI** (desk) | `ask:question-source` · `ask:read-lens` (lens-reading) · `explore:branch-framings` · `delegate:route-task` (delegate-task) — plus `explain-the-system`, the co-PI's meta skill outside the lane registry (ADR-48) |
| **Librarian** (catalog · extract · link · map) | `catalog:find-source` (find) · `catalog:enrich-record` (obsidian-paper-note) · `catalog:classify-source` (classify) · `catalog:rank-candidate` (candidate-rank) · `extract:stub-claim` · `extract:flag-distill` (distill-candidate-flag) · `link:suggest-claim` (relation-suggest) · `link:surface-tension` (tension-surface) · `map:scope-project` (scope-project) · `map:report-coverage` (gap-report) · `map:cluster-corpus` (cluster-mapping) · `map:seed-canvas` (canvas-seed) |
| **Writer** (draft) | `draft:write-section` (draft) · `draft:outline-argument` (counter-outline) · `draft:score-outline` (outline-score) · `draft:bind-citation` (citation-bind) |
| **Peer-reviewer** (verify) | `verify:check-citation` (cite-check, ex-claim-checks) · `verify:trace-claim` (claim-trace, ex-claim-checks) · `verify:card-gap` (gap-card) · `verify:propose-fix` (gap-fix-propose) |
| **Ingest** engine | `ingest:fetch-metadata` · `ingest:extract-text` · `ingest:build-relationships` · `ingest:create-records` |
| **Search** engine | `search:query-vault` (query) · `search:find-similar` |
| **Clustering** engine | `cluster:model-topics` · `cluster:build-graph` |
| **Sweeps** engine | `sweep:check-retraction` (retraction-check) · `sweep:find-duplicates` (find-duplicates) · `sweep:check-similarity` (similarity-check) |
| **Linter** engine | `lint:check-schema` (schema-check) · `lint:migrate-schema` (schema-migrate) · `lint:analyze-graph` (graph-analyze) · `lint:report-health` (health-report) |

Engine "skills" run on cron/CI or behind MCP facades, not as agent chat commands. Four map-lane entries from the design's full registry are **deferred, not shipped**: `map:score-writability` / `map:score-readiness` need the v0.1.0-alpha.3 project workflow, and `map:graph-claims` / `map:canvas-hub` belong to the graph-visualization exploration.

Every shipped `SKILL.md` carries a machine-checkable `metadata.memoria` block (`skill_id`, `profile`, `lane`, `mcp_tools`, `write_scope`, `outputs`): the MCP tools must resolve against the [tool registry](../../src/.memoria/tool-registry.yaml) and the write scope must sit inside the lane-override ceiling — `tests/test_profiles.py` enforces both.

---

## The MCP tool surface

Tools the profiles call (and you can exercise directly when debugging — each server also runs one-shot from the CLI):

| Server | Tool | Does |
| --- | --- | --- |
| tasks | `delegate_route_task(lane, goal, context, allowed_paths, expected_outputs, review_checks, idempotency_key)` | The co-PI's delegation path: validates the handoff against the lane ceiling, then creates the board card. See [Kanban board reference](kanban-board.md). |
| cluster | `cluster_build_graph(seed)` | NetworkX over authored `links:` + given `relationships` → nodes, typed edges, communities, centrality, layout. Read-only; params echoed. |
| cluster | `cluster_model_topics(folder, min_cluster_size)` | BERTopic over note text → topics, doc-topic map, outliers (needs the opt-in cluster stack). |
| patterns | `patterns_list(mode)` | Runnable (`lifecycle: current`) patterns, optionally filtered by `library` / `project`. |
| patterns | `patterns_run(pattern_id, input_text, input_ref)` | Compose preamble + pattern + input → the prompt + staging target; gated targets degrade to dry-run; every run provenance-logged to `system/logs/patterns.jsonl`. |
| ingest | `ingest_pipeline(citekey, enrich, pdf_path)` | The deterministic draft bundle with the two LLM holes. See [Ingest routing](ingest.md). |
| policy | `check_permission` / `complete_write` | The write gate. See [Policy MCP](policy-mcp.md). |

---

## Board management

| Command | What it does |
| --- | --- |
| `hermes kanban list` | List all cards on the board. |
| `hermes kanban show <card-id>` | Full card state: status, retry count, blocker reason, handoff summary. |
| `hermes kanban create "<title>" --assignee memoria-<name>` | Create a card (the tasks MCP shells out to this same command; `--idempotency-key` dedupes). |
| `hermes kanban specify <id>` | Flesh out a `triage` card into a concrete spec → `todo`. |
| `hermes kanban release <id>` | Release a `todo` card to `ready` for dispatch. |
| `hermes kanban dispatch` | Run one dispatcher pass. |
| `hermes kanban unblock <id>` | Clear a `blocked` card → `ready`. |
| `hermes kanban edit <id> --assignee <lane>` | Correct an unresolvable assignee. |
| `hermes kanban archive <id> --reason "<text>"` | Archive a terminal card with an explicit reason. |
| `hermes kanban decompose <id>` | Fan out a `triage` card into child task cards. |

---

## Profile management

| Command | What it does |
| --- | --- |
| `hermes profile list` | List registered profiles: alias, status, installed path. |
| `hermes profile install <dir> --name <name> --alias --force --yes` | Install or refresh a profile from a staged directory. In practice use `scripts/install.sh --profiles-only` — it handles the `{{PYTHON}}`/`{{VAULT_PATH}}` substitution and the env seeding first. |
| `hermes profile show <alias>` | A profile's `SOUL.md`, MCP servers, skills, and `.env` key names (values redacted). |
| `hermes profile remove <alias>` | Remove the registration (used by the installer to prune the retired five). Does not delete the vault source under `.memoria/profiles/`. |

---

## Skills

| Command | What it does |
| --- | --- |
| `hermes skills list` | List installed skills. |
| `hermes skills install <id> --yes` | Install a hub skill (the installer fetches `obsidian-markdown` and `qmd` this way). |

---

## Scheduled tasks (cron)

| Command | What it does |
| --- | --- |
| `hermes cron list` | List scheduled tasks with next-run times (you should see `memoria-board-export`, `memoria-sweeps`, `memoria-lint`). |
| `hermes cron create '<spec>' --script <name>.sh --no-agent --name <name> --deliver local` | The shape the installer uses for the deterministic crons. |
| `hermes cron run <task-name>` | Run a scheduled task immediately. |
| `hermes cron enable <task-name>` / `disable <task-name>` | Toggle a task without removing it. |

---

## Related

- In-Obsidian command palette (`Memoria:` entries): [Obsidian command palette](obsidian-command-palette.md)
- The lane identifiers the commands map to: [Profile capabilities](profiles.md)
- The delegation path behind the board: [Kanban board reference](kanban-board.md)
- What the installer wires for you: [Installer (bootstrap)](installer.md)
