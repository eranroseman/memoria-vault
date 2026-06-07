---
title: Run a CLI chat session
parent: Hermes Agent
nav_order: 2
---


# Run a CLI chat session

Start a terminal chat session with a specific Memoria profile to run skills, ingest sources, lint the vault, or run any other profile-specific command. (This is the `hermes … chat` CLI — not the Telegram messaging gateway, which is covered in [Set up messaging](../setup/set-up-messaging.md).)

## When to use the CLI vs. Obsidian

Use the Hermes CLI chat when:

- Running **setup or maintenance tasks** (ingest, lint, rebuild index, check profile drift)
- Running a **one-off skill** outside of the normal Kanban flow (e.g., re-ingesting a single source)
- **Debugging** a profile's behavior or checking audit logs

Use the **Obsidian command palette** (Cmd-P → Memoria: …) for day-to-day work: discussing a paper, requesting a draft, checking the board. Those commands route to Hermes profiles over the agent-client plugin without needing a terminal.

## Start a session

```bash
hermes -p <profile-alias> chat -s <skill-name>
```

- `-p <profile-alias>` — which profile to invoke (e.g., `memoria-librarian`)
- `-s <skill-name>` — load a specific skill at session start (e.g., `obsidian-paper-note`, `lint`, `draft`)

If `-s` is omitted, the profile starts with no skill loaded — useful for exploratory sessions.

## Common session starters

| Goal | Command |
| --- | --- |
| Ingest a source | `hermes -p memoria-librarian chat -s obsidian-paper-note` |
| Lint the vault | `hermes -p memoria-linter chat -s lint` |
| Check vault health | `hermes -p memoria-linter chat -s health-report` |
| Run a similarity check | `hermes -p memoria-verifier chat -s similarity-check` |
| Get a draft outline | `hermes -p memoria-writer chat -s draft` |
| Scope a writing project | `hermes -p memoria-mapper chat -s scope-project` |
| Discuss a paper (CLI fallback) | `hermes -p memoria-socratic chat --command socratic-processing --source <citekey>` |

## Inside a session

Once in a session, type `/skill-command [args]` to invoke the loaded skill:

```text
/obsidian-paper-note --source mamykina2010sense
/lint --dry-run
/lint --target 20-sources/
/draft "outline the argument on JITAI receptivity"
/similarity-check "receptivity decreases under cognitive load"
```

Type `help` or `/help` to list available commands for the loaded skill.

Type `exit` or Ctrl-C to end the session cleanly.

## Dry-run mode

Most write-producing commands accept `--dry-run`. This reports what would be written without touching the vault:

```text
/obsidian-paper-note --source mamykina2010sense --dry-run
```

Use dry-run when testing a new profile configuration or checking a command's behavior before committing.

## Piping output to a file

For commands that produce a report (lint, health-report, scope-project), redirect output to a file for review in Obsidian:

```bash
hermes -p memoria-linter chat -s lint <<< "/lint --dry-run" > lint-report.md
```

Or run the session normally and copy the output — the profile logs session output to `99-system/logs/session-log.md` if session-logging is enabled.

## Related

- Profile configuration: [Configure a profile](configuration.md)
- Ingest: [Capture and ingest a source](../compile/capture-and-ingest.md)
- Lint: [Run the Linter](../operate/run-the-linter.md)
- Administrative CLI commands (profile, kanban, skills, cron): [Hermes CLI](../../reference/hermes-cli.md)
