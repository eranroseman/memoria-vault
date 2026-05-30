---
topic: architecture
---

# Human channels

Memoria's primary UI is **Obsidian** — the focused desktop surface where nearly all daily work happens. Beyond it are two **secondary channels** for reaching the system when Obsidian isn't the right place — the **CLI** (precise, occasional, forensic) and **Telegram** (mobile, async) — plus one **non-human integration path**, the **API server**, which programs use and humans never touch directly. This document carries the per-path detail; the architecture overview that names them lives in [README.md §"Human channels"](README.md#human-channels).

The three layers ([board](../kanban-board/README.md), [workers/profiles](../profiles/README.md), [vault](../vault/README.md)) are *what the system is*. The access paths below are *where the human sees it and acts on it*. The defining discipline: **each access path owns one mode.** Using one for the wrong mode (Telegram for desktop work, CLI for daily ops, the API for something a command already does) produces the "every operation feels slightly off" drift that erodes a workflow.

| Access path | Mode | Use it for |
| --- | --- | --- |
| **Obsidian** (the primary UI) | Desktop, focused, deliberate | Daily triage, reading, authoring, agent conversations on the active note. Its internal components — dashboards, workspaces, callouts, status line, command palette, the Agent Client pane — are detailed in [obsidian-ui/README.md](../obsidian-ui/README.md). |
| **CLI** (`hermes …`) | Desktop, occasional, precise | Forensic queries against the audit log, profile administration, manual dispatch, anything benefiting from precision over discoverability. |
| **Telegram** | Mobile, async, lightweight | Fleeting capture on the go, source-URL capture, urgent push notifications (retry threshold hit, drift alarm, cron failure). Not for drafting or review. |
| **API server** (port 8642) | Programmatic, integration (not human) | File-system watchers, Zotero hooks, git post-commit, cross-machine dispatch. Never the path for direct human action. |

The command palette and the Agent Client pane are **components of Obsidian**, not separate access paths — they live inside the primary UI, alongside dashboards, workspaces, callouts, and the status line. That inside-Obsidian breakdown is the companion to this table: this table answers "which access path," and [obsidian-ui/README.md](../obsidian-ui/README.md) answers "which part of the Obsidian UI."

## Channel failure modes

The point is consciously picking the right channel for each operation. The failure modes happen when one channel gets used for another's job:

- **Telegram for things that need the desktop** → ignored notifications. Once Telegram has cried wolf with a message that should have been a dashboard query, the human starts ignoring all Telegram messages — including the urgent ones.
- **CLI for daily operations** → eroded habit. If `hermes kanban ...` is the human's path to approving link suggestions, the friction of dropping to a terminal compounds across the day; eventually the suggestions stop getting approved.
- **Dashboards for things that need a script** → manual repetition that should be automated. A weekly "check this query, copy these card IDs, run this command" pattern is an API integration the human hasn't written yet.
- **API directly when a command exists** → reinventing wheels. Curl-ing the API to do what `Memoria: capture fleeting` already does is technical debt disguised as flexibility.

The corrective is one question per operation: "what channel is this *kind* of work?" Most failures are answered by the table above.

Two principles:

- **Notifications must change what the human would do in the next 30 minutes**, or they shouldn't be notifications. Routine approvals wait for the dashboard; only hard blockers and drift alarms page Telegram.
- **An admin GUI, if ever built, is an Obsidian plugin — not a separate web app.** Extending Obsidian-as-interface composes cleanly with the existing access paths; adopting a peer system (e.g., a hackathon-grade Hermes-admin web UI) would create a competing channel vying for the same modes, and a chat tab that bypasses the policy MCP entirely. The recommended shape — a read-only sidebar pane reaching the API on loopback — lives in [roadmap/future-directions.md](../../project/roadmap/future-directions.md#memoria-inspector-obsidian-plugin).

## CLI is the forensic channel

The CLI channel is for **rare, precise operations** — debugging stuck cards, inspecting audit trails, manual dispatch outside the normal workflow. The rule: CLI is right for forensic work because forensic work is rare and benefits from precision. A UI for rare operations is mostly empty real estate; a CLI for rare operations is invisible until needed and then exactly the right shape.

Six use case categories cover what the CLI is for:

**1. Card inspection.** When a card has been retried repeatedly over two days, the human wants to know why. `hermes kanban show card-<id>` returns full state, retry count, blocker reason, and handoff summary in one screen — faster than navigating to the board dashboard and clicking through.

**2. Lane health checks.** `hermes lane status librarian` shows [trust score](../../reference/glossary.md#observability-and-verdicts), recent deny rate, last successful task, current queue depth. Run when something feels off but the dashboards haven't flagged anything yet.

**3. Audit forensics.** `hermes audit --card <id>` or `hermes audit --lane mapper --since 24h` walks the audit log filtered to the slice the human cares about. Faster than opening the audit-log dashboard for narrow queries; the dashboard is for trends, the CLI is for specific traces.

**4. Manual dispatch.** `hermes dispatch --lane mapper --task scope-project --project jitai-review` creates a card without waiting for a file-system trigger or cron. Useful when the human wants to invoke something on demand outside the normal flow — for example, re-running a scope when new sources have been added mid-project.

**5. Profile administration.** Update lane-override files in `.memoria/lane-overrides/`, reload the policy MCP, edit profile sources in `.memoria/profiles/memoria-<name>/` and re-run `install.ps1` to deploy them, install new skills. All CLI operations, not dashboard ones, because they're rare and consequential — exactly the kind of operation that should require typing.

**6. Backup and migration.** Vault snapshots, audit log archival, profile config exports, schema migrations. CLI is the right home for anything that's "do once carefully."

Example commands across the categories:

```bash
# 1. Card inspection
hermes kanban show card-2026-05-26-042

# 2. Lane health
hermes lane status librarian

# 3. Audit forensics
hermes audit --card card-2026-05-26-042
hermes audit --lane verifier --since 7d

# 4. Manual dispatch
hermes dispatch --lane mapper --task scope-project --project jitai-review

# 5. Profile administration
./install.ps1    # re-deploy all seven profiles from .memoria/profiles/
hermes profile reload memoria-linter

# 6. Backup / migration
hermes audit export --since 2026-01-01 --to logs/2026-archive.jsonl
```

These are examples, not an authoritative catalog. The full Hermes CLI surface is upstream of Memoria (documented at [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/)); Memoria pins specific commands only as illustrations. When the Hermes CLI changes between versions, Memoria docs may lag — the principle (CLI for forensic work) stays true even when the specific flag names shift.

**What CLI is NOT for.** Daily operations (capture, processing, drafting) go through the command palette inside Obsidian — see [`obsidian-ui/command-palette.md`](../../reference/command-catalog.md). Triage of approval queues belongs in the dashboards plus inline callout buttons, not the terminal. Reading content belongs in Obsidian; opening files in a terminal is hostile.

**Mental model.** CLI is the surgical tool. Sharp, precise, occasional. If the human finds themselves using the CLI more than a few times a week, something else (the dashboards, inline UI, or command palette) needs improving — the friction of dropping to a terminal is a signal that a more frequent operation lacks its proper channel.

## Telegram has two distinct uses

Telegram is the asynchronous, mobile-reachable channel. It serves two distinct purposes that are worth keeping separate in the human's mental model — they have different disciplines and different failure modes.

### Use 1: Notifications that can't wait

The dashboards tell the human what needs attention when they open them. Telegram pushes the human when something can't wait until the next dashboard glance. The distinction matters because over-notifying turns Telegram into noise the human ignores — which is strictly worse than not having notifications at all.

**Wire notifications for:**

- **Hard blockers.** A card hit the retry threshold (`max_retries`, default 3) and auto-moved to `blocked`. The policy MCP denied an unexpected write (security signal). A skill broke catastrophically.
- **Time-sensitive workflows.** The human triggered an overnight ingest of 30 papers and wants a morning summary when it's done, not on their next dashboard check.
- **Drift alarms.** Linter's M-series detectors found something at HIGH or CRITICAL severity. Audit deny rate spiked above baseline.
- **Cron failures.** A scheduled task (nightly hygiene, weekly drift report) didn't run, or ran but failed. The human wants to know before the next day's cron cycle.

**Do not wire notifications for:**

- Anything that surfaces in the morning [Daily Health](../dashboards/daily-health.md) glance.
- Per-card events ("new card created", "card moved to active"). Volume kills signal.
- Routine approvals. Those wait until the human chooses to do them; the queue surfaces them in the daily/weekly dashboards.

**The discipline, in one sentence.** If a notification doesn't change what the human would do in the next 30 minutes, it shouldn't be a notification.

### Use 2: Mobile capture and lightweight interaction

Telegram is where the human reaches Hermes when they're not at their desk. The interactions that fit a phone screen:

- **Fleeting capture.** `/fleeting save: <thought>` drops the text into `10-inbox/01-fleeting/` with a timestamp. Zero friction; the human types and the thought is captured.
- **Source capture from URL.** Paste a link, get back a confirmation that it's queued for ingest. The actual ingest happens overnight; the phone interaction is just the queue-up.
- **Quick lookups.** "What do I have on therapeutic alliance?" — Mapper returns a short list. Useful when the human is in conversation and wants to reference their own work.
- **Socratic conversations on the go.** The killer feature. Invoke Socratic on a paper note from the phone while walking, have the conversation, then come back to the desk and write the claim note. The thinking happens in motion; the artifact happens at the desk.
- **Approval triage on long queues.** If 30 approvals have accumulated over a busy week, the human can clear them on a train ride — card, quick summary, approve or reject, next. Phone screens are right-sized for binary decisions.

**Doesn't belong on Telegram:**

- Drafting. Phone keyboards are wrong for prose.
- Reviewing drafts. Too much context for the screen.
- Anything that needs the dashboard view. Use the desktop.

**Mental model.** Telegram is the always-available channel for things that fit on a phone and notifications that can't wait. Most of the value comes from a small number of well-chosen capture and Socratic flows, not from being a generic chat interface.

### Telegram toolset is narrower than CLI

Hermes profiles can expose the same capability surface (browser, code execution, terminal, delegation, memory, skills, etc.) through any registered channel. Telegram is the **single channel where the toolset should be deliberately narrower** than the host profile. Mobile is for thinking and capture; running code, opening browsers, or shelling out from a phone is a footgun without commensurate value — the small screen makes auditing the action's effects unreliable, and the always-on connectivity makes accidental triggers easier than at the desk.

Memoria's recommended Telegram toolset per profile (subset of the full capability surface):

- `clarify` — ask the human a follow-up question
- `memory` — read profile / lane / project memory
- `messaging` — send replies
- `todo` — read or update task lists (does *not* include scheduling external commitments; that's Todoist)
- `session_search` — look up prior conversations
- `skills` — invoke pre-approved skills and switch to read-only profiles (notably Socratic for on-the-go thinking via `lens-reading` with a chosen lens)

Explicitly **not** on Telegram: `code_execution`, `terminal`, `delegate_task`, `web_search`, `fetch_url`. These are desktop-CLI tools; routing them through Telegram is what produces the "I dispatched a long-running job from my phone and forgot about it" failure mode. The narrowing is enforced per profile in the Hermes runtime config, not just by convention.

### Other messaging channels

Hermes can integrate with Discord, WhatsApp, Slack, Signal, Teams, and others. **Leave them off until there's a concrete need.** Each enabled channel competes for the human's attention; each one becomes a place notifications can land, and every channel demands its own discipline about what to wire. Telegram covers the mobile-async case adequately for a single-human vault. If a collaborator joins, or a specific channel is the human's existing primary (e.g., a Slack workspace), enabling that channel becomes worth the attention cost — but never as a parallel to Telegram. One mobile-async channel is the working set.

## API server: integration and automation

The API server on port 8642 is where Hermes connects to other systems. It's the least-used channel day-to-day but the most enabling for everything else — most of Memoria's "this just happens automatically overnight" magic relies on the API being reachable to triggers, watchers, and hooks.

Seven integration patterns cover what the API is used for:

**1. File-system triggers.** A watcher script monitors `10-inbox/00-pdfs/` as a side-channel capture surface — for PDFs the human receives outside Zotero (downloads, colleague handoffs). New file appears → watcher imports it into Zotero (via the Zotero HTTP connector or `zotero-cli`) so Better BibTeX can assign a citekey → POST to the API → card created in Librarian's queue → standard ingest runs (Marker extract, paper-note creation, frontmatter URIs). The dropped PDF leaves the vault during the Zotero-import step; the authoritative PDF store remains Zotero (see [workflows/upstream/zotero-capture.md](../../how-to/workflows/upstream/zotero-capture.md)).

**2. Zotero hooks.** Better BibTeX can run a script on save. Wire it to POST to the API when a new entry is added. Librarian picks up the citekey and runs ingest. The Zotero workflow becomes the Memoria workflow with no extra effort.

**3. Email-to-Memoria.** A custom mail filter forwards arXiv alerts to a script that extracts the arXiv ID and POSTs to the API. Subscription feeds become candidate-discovery cards automatically.

**4. Git hooks.** On commit to `40-workbench/*/04-drafts/`, a `post-commit` hook POSTs to the API to create a `verify` card. Verifier picks it up; the human gets a verification report by the time they next open the draft.

**5. Calendar integration.** If the human uses a research-block calendar, a script can check the calendar and create a daily card with "today's reading queue" pulled from [`discuss-queue.md`](../dashboards/discuss-queue.md). Useful for keeping rhythm against scheduled focus time.

**6. Cross-machine dispatch.** If the human works across laptop and desktop, the API is how a command on one machine creates a card the other machine's Hermes instance picks up. Assumes a shared vault (Syncthing, git, or Obsidian Sync per the [deployment options](../../project/roadmap/deployment-options.md)).

**7. Custom dashboards or scripts.** Anything that needs to query Kanban state programmatically reads from the API. Cleaner than parsing the vault filesystem directly — the API returns structured data; the vault has notes that happen to encode state.

**What API is NOT for:**

- **Direct human interaction.** That's CLI, command palette, or Telegram. The API is for *programs* invoking Memoria, not humans.
- **Bypassing the policy MCP.** Every write that enters through the API still goes through the policy MCP. The API doesn't grant elevated permission; it's just another caller subject to the same lane-override rules.

**Security and binding.** Per the [fail-closed startup](control-plane.md#fail-closed-startup) rules, the API binds to `127.0.0.1` by default. Non-loopback binding requires the API's auth token to be set. For a laptop that travels (coffee shops, conferences), loopback is the right default — local scripts can reach the API; nothing on the network can. Cross-machine integration earns its non-loopback binding only with explicit token configuration.
