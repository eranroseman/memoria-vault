# Hermes administrative commands

Administrative CLI commands for managing profiles, the Kanban board, skills, and scheduled tasks. These are system-maintenance operations; day-to-day research work uses the Obsidian command palette instead.

Command structure: `hermes <command> [subcommand] [args]` — runs from any directory; Hermes resolves the vault path from the profile's `mcp.json`.

---

## Profile management

| Command | What it does |
| --- | --- |
| `hermes profile list` | List all registered profiles: alias, status, installed path |
| `hermes profile install <dir> --alias <alias> --force --yes` | Install or refresh a profile from a staged directory. In practice use `install.ps1` — it handles `{{VAULT_PATH}}` substitution first |
| `hermes profile show <alias>` | Show a profile's `SOUL.md`, MCP servers, allowed skills, and `.env` key names (values redacted) |
| `hermes profile remove <alias>` | Remove the profile registration. Does not delete the vault source files under `.memoria/profiles/` |

---

## Kanban board

| Command | What it does |
| --- | --- |
| `hermes kanban list` | List all cards on the board |
| `hermes kanban show <card-id>` | Full card state: status, retry count, blocker reason, handoff summary |
| `hermes kanban unblock <card-id>` | Clear a blocked card → ready (after fixing the underlying issue) |
| `hermes kanban archive <card-id> --reason "<text>"` | Archive a card with an explicit reason |
| `hermes kanban edit <card-id> --assignee <lane>` | Correct an unresolvable assignee on a stuck-ready card |

---

## Skills

| Command | What it does |
| --- | --- |
| `hermes skills list` | List all available skills |
| `hermes skills install <skill-name>` | Install a skill |
| `hermes profile show <alias> \| grep skills` | Check which skills a profile currently loads |

---

## Scheduled tasks (cron)

| Command | What it does |
| --- | --- |
| `hermes cron list` | List all scheduled tasks with next-run times |
| `hermes cron run <task-name>` | Run a scheduled task immediately |
| `hermes cron enable <task-name>` | Enable a disabled task |
| `hermes cron disable <task-name>` | Disable a task without removing it |

---

## Related

- Profile-specific commands (ingest, lint, draft, etc.): [reference/commands.md](commands.md)
- How to start a chat session: [how-to-guides/hermes/chat-with-hermes.md](../how-to-guides/hermes/chat-with-hermes.md)
- How to configure a profile: [how-to-guides/hermes/configuration.md](../how-to-guides/hermes/configuration.md)
- Kanban how-to (stuck cards, unblocking): [how-to-guides/recovery/fix-stuck-card.md](../how-to-guides/recovery/fix-stuck-card.md)
