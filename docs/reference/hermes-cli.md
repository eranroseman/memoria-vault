---
title: Hermes CLI
parent: Reference
---

# Hermes CLI

Every `hermes …` command-line operation: the per-profile research commands, the administrative commands (profiles, skills, cron), and the Kanban board commands. These are the **terminal** surface. For the in-Obsidian `Memoria:` palette see [Obsidian command palette](obsidian-command-palette.md).

Command structure: `hermes <command> [subcommand] [args]` — runs from any directory; Hermes resolves the vault path from the profile's `config.yaml`. Per-profile research commands run as `hermes -p memoria-<name> chat -s <command> [args]`.

---

## Per-profile commands

Run as: `hermes -p memoria-<name> chat -s <command> [args]`

### Librarian

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `find` | Forward/backward citation search or concept-driven search. Writes candidates to `10-inbox/03-candidates/`. | No |
| `ingest` | Create the note for a source in the right folder with enrichment. | No |
| `enrich` | Re-run API enrichment on existing notes. | No |
| `classify` | Re-propose `_proposed_classification` on a note still needing review. | No |
| `obsidian-paper-note` | Full ingest pipeline including PDF extraction via Marker and the inline `[!brief]` comparative read. | No |
| `query` | Deterministic vault search (standalone retrieval). | No |
| `export prior-labels` | Export vault papers as ASReview priors for pre-ingest screening (frontmatter filter + format conversion). | No |

### Mapper

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `scope-project` | Corpus map for a project. Writes `corpus-map.md` to `<project>/01-map/`. | No |
| `gap-report` | Thin-coverage topics adjacent to a project brief. | No |
| `cluster-map` | Density / recency map for an arbitrary topic. | No |

### Socratic

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `socratic-processing` | Question-only conversation about a note. No writes. | N/A (read-only) |
| `lens-reading` | Read through a named theoretical lens. Parameterized by lens slug. | N/A (read-only) |

### Writer

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `draft` | Search vault and produce an answer note for human review. | No |
| `query` | Pre-draft vault search step. | No |
| `lint` | Request a Linter pass on the current draft (Linter executes; Writer only requests). | N/A (handoff) |
| `promote` | Propose promotion of a claim → reference note (handoff; human approves). | N/A (handoff) |

### Verifier

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `cite-check` | Verify every citekey in a draft resolves to a real paper note. | Yes (default) |
| `claim-trace` | Trace each substantive claim to a supporting claim note (wikilink walk → citekey+similarity → similarity search; LLM only on the ambiguous middle band). | Yes |
| `similarity-check` | Top-N most-similar notes; flag at threshold ~0.8; never auto-merge. | Yes |
| `find-duplicates` | Identify semantically similar claim notes for merge review. | Yes; never auto-merges |
| `retraction-check` | Scan paper notes against Zotero retraction alerts and CrossRef. | Yes (default) |

### Coder

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `code` | Scaffold a `code-note` handoff for the external coding agent. | No |
| `commit` | Commit one logical change per call. | No |
| `revert` | Revert a prior Coder commit; scoped small. | No |
| `workspace` | Set up VS Code workspace (vault read-only; code zone writable). | N/A |
| `scaffold` | Generate the `code-note` skeleton from the template. | No |

### Linter

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `lint` | Structural health check across the vault. | Yes (default) |
| `schema-check` | Verify frontmatter against the authoritative schema. | Yes |
| `schema-migrate` | Propose schema changes between versions. Always dry-run first. | Yes (always required first) |
| `graph-analyze` | Knowledge graph health: orphans, hubs, clusters, link density. | Yes |
| `health-report` | Rolls structural findings into the verdict band (PASS / REVIEW / FAIL). | Yes |
| `session-log` | Write per-session log to `99-system/logs/`. | N/A |
| `dry-run` | Run any check in report-only mode. | Yes (by definition) |

---

## Board management

| Command | What it does |
| --- | --- |
| `hermes kanban list` | List all cards on the board. |
| `hermes kanban show <card-id>` | Full card state: status, retry count, blocker reason, handoff summary. |
| `hermes kanban create "<title>" --assignee memoria-<name>` | Create a new card in `triage`. |
| `hermes kanban specify <id>` | Flesh out a `triage` card into a concrete spec → `todo`. |
| `hermes kanban release <id>` | Release a `todo` card to `ready` for dispatch. |
| `hermes kanban dispatch` | Run one dispatcher pass (claims all `ready` cards for matching lanes). |
| `hermes kanban claim <id>` | Manually claim a `ready` card (script/debug use only). |
| `hermes kanban unblock <id>` | Clear a `blocked` card → `ready` (after fixing the underlying issue). |
| `hermes kanban edit <id> --assignee <lane>` | Correct an unresolvable assignee on a stuck-ready card. |
| `hermes kanban archive <id> --reason "<text>"` | Archive a terminal card with an explicit reason. |
| `hermes kanban decompose <id>` | Fan out a `triage` card into child task cards. |

See [policy-mcp.md — Review-gated zones](policy-mcp.md) for the rule on commands that target synthesis or deliverable folders.

---

## Profile management

| Command | What it does |
| --- | --- |
| `hermes profile list` | List all registered profiles: alias, status, installed path. |
| `hermes profile install <dir> --alias <alias> --force --yes` | Install or refresh a profile from a staged directory. In practice use `scripts/install.sh --profiles-only` — it handles `{{VAULT_PATH}}` substitution first. |
| `hermes profile show <alias>` | Show a profile's `SOUL.md`, MCP servers, allowed skills, and `.env` key names (values redacted). |
| `hermes profile remove <alias>` | Remove the profile registration. Does not delete the vault source files under `.memoria/profiles/`. |

---

## Skills

| Command | What it does |
| --- | --- |
| `hermes skills list` | List all available skills. |
| `hermes skills install <skill-name>` | Install a skill. |
| `hermes profile show <alias> \| grep skills` | Check which skills a profile currently loads. |

---

## Scheduled tasks (cron)

| Command | What it does |
| --- | --- |
| `hermes cron list` | List all scheduled tasks with next-run times. |
| `hermes cron run <task-name>` | Run a scheduled task immediately. |
| `hermes cron enable <task-name>` | Enable a disabled task. |
| `hermes cron disable <task-name>` | Disable a task without removing it. |

---

## Related

**Reference**

- In-Obsidian command palette (`Memoria:` entries): [Obsidian command palette](obsidian-command-palette.md)
- Lane identifiers the commands map to: [Profile capabilities](profiles.md)

**How-to**

- How to start a chat session: [How to chat with a Hermes profile](../how-to-guides/using-hermes-agent/chat-with-hermes.md)
- How to configure a profile: [How to configure a Hermes profile](../how-to-guides/using-hermes-agent/configuration.md)
- Kanban how-to (stuck cards, unblocking): [How to fix a stuck card](../how-to-guides/recovery/fix-stuck-card.md)

**Explanation**

- The profile explanation pages: [Profiles](../explanation/profiles/README.md)
