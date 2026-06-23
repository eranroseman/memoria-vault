---
title: Run a CLI chat session
parent: Hermes Agent
nav_order: 2
---


# Run a CLI chat session

Start a terminal session with a Memoria profile — the Co-PI without Obsidian, or a background lane for debugging. (This is the `hermes … chat` CLI — not the in-Obsidian Agent Client pane, which speaks ACP to the same profiles.)

Reach for a CLI chat session when Obsidian isn't running, when debugging a lane profile directly outside board dispatch, or to verify a redeployed profile loads its MCP servers and skills. For normal task dispatch, use the Obsidian command palette first; the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) is for conversation and handoff shaping. Note that lint and the retraction sweep are now **operations**, not chat sessions ([Run the Linter](../operate/run-the-linter.md), [Run a retraction sweep](../operate/run-a-retraction-sweep.md)).

```bash
hermes -p <profile-alias> chat
```

- `-p <profile-alias>` — which profile to invoke (a **global** Hermes flag, so it also works with other subcommands, e.g. `hermes -p memoria-copi acp` for the pane's stdio server)

The five aliases: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`.

## Common session starters

| Goal | Command |
| --- | --- |
| Talk to the Co-PI from the terminal | `hermes -p memoria-copi chat` |
| Shape a task when Obsidian is unavailable | `hermes -p memoria-copi chat`, then e.g. "help me frame a verify request for projects/jitai/draft.md" |
| Debug the ingest path | `hermes -p memoria-librarian chat`, then ask it to dry-run `catalog-find-source` on a citekey |
| Debug the verify checks | `hermes -p memoria-peer-reviewer chat`, then ask for a `verify-trace-claim` pass on a claim note |

The Co-PI is the only profile designed for conversation — it reads the vault, answers, and delegates writes as board cards via `delegate_route_task`. The dispatched lanes normally run from the Kanban board, so a direct chat with them is a debugging posture, not a workflow.

Type `exit` or Ctrl-C to end a session cleanly.

## Chatting safely

No special flag is needed — the policy gate enforces it ([Policy MCP](../../reference/policy-mcp.md)): the Co-PI's lane denies every path, and any lane write to a review-gated prefix degrades to `dry_run` and lands in the review queue ([Work the review queue](../inbox/work-the-review-queue.md)). To test a single permission decision without any agent, use the policy MCP's `--decide` one-shot mode ([Configure a profile § Verify a configuration change](configuration.md#verify-a-configuration-change)).

## Watching what a session did

- `system/logs/audit.jsonl` — every gated action the session attempted
- `system/logs/sessions/` — per-session digests the Linter writes from the audit log
- `hermes kanban list` — cards a Co-PI session delegated to the board

## Related

- Profile configuration: [Configure a profile](configuration.md)
- The pane that replaces most CLI chats: [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)
- Ingest: [Capture and ingest a source](../library/capture-and-ingest.md)
- Administrative CLI commands (profile, kanban, skills, cron): [Hermes CLI](../../reference/hermes-cli.md)
