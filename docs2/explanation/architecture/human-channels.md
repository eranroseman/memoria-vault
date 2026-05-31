# Human channels

Memoria's primary UI is Obsidian. Beyond it are two secondary channels for reaching the system when Obsidian isn't the right place — the CLI (precise, occasional, forensic) and Telegram (mobile, async) — plus one non-human integration path, the API server, which programs use and humans never touch directly.

The defining discipline: **each channel owns one mode.** Using one for another's job produces the "everything feels slightly off" drift that erodes a workflow.

| Channel | Mode | Use it for |
| --- | --- | --- |
| **Obsidian** | Desktop, focused, deliberate | Daily triage, reading, authoring, agent conversations on the active note |
| **CLI** (`hermes …`) | Desktop, occasional, precise | Forensic queries, profile administration, manual dispatch, backup |
| **Telegram** | Mobile, async, lightweight | Fleeting capture, source-URL queuing, urgent push notifications |
| **API server** (port 8642) | Programmatic, integration | File-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch |

---

## Channel failure modes

The failure modes happen when one channel is used for another's job:

- **Telegram for things that need the desktop** → ignored notifications. Once Telegram sends a message that should have been a dashboard query, the human starts ignoring all Telegram messages — including the urgent ones.
- **CLI for daily operations** → eroded habit. If `hermes kanban ...` is the path to approving link suggestions, the terminal friction compounds; eventually suggestions stop getting approved.
- **Dashboards for things that need a script** → manual repetition. A weekly "check query, copy IDs, run command" pattern is an API integration the human hasn't written yet.
- **API directly when a command exists** → reinventing wheels.

---

## CLI: the forensic channel

CLI is for **rare, precise operations** — debugging stuck cards, inspecting audit trails, manual dispatch outside the normal workflow. A UI for rare operations is mostly empty real estate; a CLI is invisible until needed and then exactly the right shape.

Six use-case categories:

**1. Card inspection.** `hermes kanban show <card-id>` returns full state, retry count, blocker reason, and handoff summary.

**2. Lane health checks.** `hermes lane status librarian` shows trust score, recent deny rate, last successful task, current queue depth.

**3. Audit forensics.** `hermes audit --card <id>` or `hermes audit --lane mapper --since 24h` walks the audit log for a specific slice.

**4. Manual dispatch.** `hermes dispatch --lane mapper --task scope-project --project jitai-review` creates a card on demand outside the normal trigger flow.

**5. Profile administration.** Edit lane-override files, reload the policy MCP, edit profile sources and re-run `install.ps1`, install new skills.

**6. Backup and migration.** Vault snapshots, audit log archival, profile config exports, schema migrations.

```bash
hermes kanban show card-2026-05-26-042
hermes lane status librarian
hermes audit --lane verifier --since 7d
hermes dispatch --lane mapper --task scope-project --project jitai-review
hermes audit export --since 2026-01-01 --to logs/2026-archive.jsonl
```

**What CLI is NOT for:** daily operations (capture, processing, drafting) belong in the command palette. Triage belongs in dashboards. Reading content belongs in Obsidian.

If the human finds themselves using the CLI more than a few times a week, something else needs improving — the friction is a signal that a more frequent operation lacks its proper channel.

---

## Telegram: two distinct uses

### Notifications that can't wait

The dashboards tell the human what needs attention when opened. Telegram pushes when something can't wait.

**Wire for:**
- Hard blockers: a card hit `max_retries` and moved to `blocked`; unexpected policy-MCP deny (security signal); a skill broke catastrophically
- Time-sensitive completions: an overnight ingest batch finished
- Drift alarms: Linter M-series detector found HIGH or CRITICAL severity
- Cron failures: a scheduled task didn't run

**Do not wire for:**
- Anything that surfaces in the morning Daily Health glance
- Per-card events ("new card created", "card moved") — volume kills signal
- Routine approvals — those wait for the dashboards

**The discipline in one sentence:** if a notification doesn't change what the human would do in the next 30 minutes, it shouldn't be a notification.

### Mobile capture and lightweight interaction

Interactions that fit a phone screen:

- **Fleeting capture:** `/fleeting save: <thought>` drops text into `10-inbox/01-fleeting/` with a timestamp.
- **Source capture from URL:** paste a link, get confirmation it's queued for ingest.
- **Quick lookups:** "what do I have on therapeutic alliance?" — Mapper returns a short list.
- **Socratic on the go:** invoke Socratic on a paper note while walking; come back to the desk and write the claim note. The thinking happens in motion.
- **Approval triage on long queues:** clear binary decisions on a train ride.

**Doesn't belong on Telegram:** drafting, reviewing drafts, anything that needs the dashboard view.

### Telegram toolset is narrower than CLI

Mobile is for thinking and capture; running code, opening browsers, or shelling out from a phone is a footgun. Memoria's recommended Telegram toolset per profile:

- `clarify`, `memory`, `messaging`, `todo`, `session_search`, `skills`

Explicitly **not** on Telegram: `code_execution`, `terminal`, `delegate_task`, `web_search`, `fetch_url`. These are desktop-CLI tools.

**Leave other messaging channels (Discord, Slack, WhatsApp) off** until there is a concrete need. Each enabled channel competes for attention and demands its own notification discipline. Telegram covers the mobile-async case for a single-human vault.

---

## API server: integration and automation

The API server (port 8642) is where programs connect to Memoria. Humans never use it directly.

Seven integration patterns:

1. **File-system watchers.** A watcher on `10-inbox/00-pdfs/` catches PDFs dropped outside Zotero, imports them into Zotero, then POSTs to the API to trigger ingest.
2. **Zotero hooks.** Better BibTeX runs a script on save → POST to the API → Librarian ingest card created.
3. **Email-to-Memoria.** Mail filters extract arXiv IDs from alerts and POST them as discovery candidates.
4. **Git hooks.** `post-commit` on `40-workbench/*/04-drafts/` creates a `verify` card for the Verifier.
5. **Calendar integration.** A script checks the research calendar and creates a daily "today's reading queue" card.
6. **Cross-machine dispatch.** A command on the laptop creates a card the desktop's Hermes instance picks up.
7. **Custom scripts.** Anything needing programmatic Kanban state reads from the API rather than parsing the vault filesystem.

**Security:** the API binds to `127.0.0.1` by default. Non-loopback binding requires the auth token to be set. Every write through the API still passes through the policy MCP — the API does not grant elevated permissions.

---

## Related

- Obsidian UI components: [reference/obsidian/workspaces.md](../../reference/obsidian/workspaces.md)
- CLI commands: [reference/commands.md](../../reference/commands.md)
- Messaging gateway setup: [how-to-guides/setup/set-up-messaging.md](../../how-to-guides/setup/set-up-messaging.md)
- Policy MCP (what API calls go through): [reference/architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)
