
# How to use the Hermes CLI

Run Hermes commands for profile management, chat sessions, and system operations. The CLI is the control surface for setup and maintenance — day-to-day research work uses Obsidian instead.

## Core command structure

```
hermes [global flags] <command> [subcommand] [args]
```

All commands can be run from any directory. Hermes resolves the vault path from the profile's `mcp.json`, not from `$PWD`.

## Profile management

**List installed profiles:**

```bash
hermes profile list
```

Shows all registered profiles with their alias, status, and the path to their installed directory.

**Install or refresh a profile:**

```bash
hermes profile install <path-to-profile-dir> --alias <alias> --force --yes
```

In practice, use `install.ps1` rather than calling this directly — the script handles the `{{VAULT_PATH}}` substitution first.

**Inspect a profile:**

```bash
hermes profile show memoria-librarian
```

Shows the profile's `SOUL.md`, configured MCP servers, allowed skills, and `.env` key names (values are redacted).

**Remove a profile:**

```bash
hermes profile remove memoria-librarian
```

Removes the profile registration from Hermes. Does not delete the vault source files under `.memoria/profiles/`.

## Kanban board operations

**List all cards on the board:**

```bash
hermes kanban list
```

**Show a specific card:**

```bash
hermes kanban show <card-id>
```

**Unblock a blocked card** (after fixing the underlying issue):

```bash
hermes kanban unblock <card-id>
```

**Archive a card manually:**

```bash
hermes kanban archive <card-id> --reason "infeasible: source no longer available"
```

## Skill management

**List available skills:**

```bash
hermes skills list
```

**Install a skill:**

```bash
hermes skills install <skill-name>
```

**Check which skills a profile loads:**

```bash
hermes profile show <alias> | grep skills
```

## Scheduled tasks (cron)

**List scheduled tasks:**

```bash
hermes cron list
```

**Run a scheduled task immediately:**

```bash
hermes cron run <task-name>
```

**Enable or disable a task:**

```bash
hermes cron enable <task-name>
hermes cron disable <task-name>
```

## Related

- Starting a chat session: [chat-with-hermes.md](chat-with-hermes.md)
- Profile configuration: [configuration.md](configuration.md)
- Kanban card stuck: [fix-stuck-card.md](../recovery/fix-stuck-card.md)
- Hermes documentation: [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs)
