# Memoria 0.1.0-alpha.20 - Minimal Obsidian Data Collection Plugin

Date: 2026-07-07
Status: scratch design note

## 1. Requirements

The plugin is for alpha.20 self-use testing. It must collect empirical-use events that
answer the beta.1 blocker questions without becoming a workflow product.

Assumptions:

- The user is running Obsidian on the same machine as Memoria.
- Memoria exposes the alpha.20 local HTTP control surface.
- Data collection is local, explicit, and disposable until promoted into a
  release decision.
- The plugin is not the agent surface; agents still use MCP.

Success looks like this:

- A user can start/stop a study session in Obsidian.
- The plugin can record connect, view, queued operation, disposition, fallback,
  and export-attempt events.
- Events match the alpha.20 empirical event contract.
- No source, note, draft, or SRD body text is stored in the event payload.
- Events flush through Memoria when available and spool locally when offline.

## 2. Prior Art

Obsidian's official sample plugin keeps the platform model small: TypeScript,
`manifest.json`, `main.js`, optional `styles.css`, settings tab, commands,
notices, and release artifacts. That supports a small plugin before a custom app
or complex pane is justified:
<https://github.com/obsidianmd/obsidian-sample-plugin>.

The Obsidian API exposes the pieces needed here: settings tabs, modals, notices,
workspace commands/views, vault access, and active file metadata through the
plugin API definitions:
<https://github.com/obsidianmd/obsidian-api>.

VS Code's telemetry guidance is the closest mature editor precedent for the
privacy stance: respect opt-out, collect as little as possible, be transparent,
and avoid PII. Memoria should apply the same principles locally even before any
remote telemetry exists:
<https://code.visualstudio.com/api/extension-guides/telemetry>.

## 3. Clean-Slate Design

The plugin is a **local event recorder**.

It does not render the full Memoria workspace, watch the editor, or write
Memoria-owned files. It gives the user a few explicit controls for recording the
facts beta.1 needs.

### 3.1 Plugin Surface

Use only four Obsidian surfaces:

| Surface | Purpose |
| --- | --- |
| Settings tab | Configure server URL, token source, project ID, collection toggle, and retention. |
| Status bar item | Show connection state, active session, and unsent event count on desktop. |
| Command palette | Start session, stop session, record disposition, record fallback, flush events. |
| Modal | Capture the few fields needed for one event. |

Obsidian status bar items are desktop-only. On mobile, keep the same commands
and show connection/queue state with notices after command execution.

Do not add a custom side pane in alpha.20. Add it only if command/modal capture
is too slow in real dogfood sessions.

### 3.2 Settings

| Setting | Default | Notes |
| --- | --- | --- |
| `enabled` | `false` | User must opt in for each vault. |
| `serverUrl` | `http://127.0.0.1:8765` | Loopback only. |
| `hasToken` | `false` | Token presence only; token value lives in Obsidian secret storage. |
| `workspacePath` | empty | Used only to start/attach to Memoria. |
| `defaultProjectId` | empty | Optional; event modal can override. |
| `retentionDays` | `30` | Deletes local spool events after flush or expiry. |
| `showPrivacyPreview` | `true` | Shows payload before first event in a session. |

Store the bearer token with Obsidian's `app.secretStorage` API under a plugin
key. Plugin settings store only whether a token exists.

### 3.3 Event Types

All events include the alpha.20 base fields: `event_id`, `event_type`,
`timestamp`, `session_id`, and `surface`. The plugin generates `event_id` with
`crypto.randomUUID()` before validation or spooling.

| Event | Required fields beyond base fields |
| --- | --- |
| `session.started` | `workflow`, `project_id` when known |
| `session.stopped` | `outcome`, `duration_s` |
| `http.connected` | `outcome` |
| `view.opened` | `workflow`, `item_type`, `item_id` when known |
| `operation.queued` | `workflow`, `item_type`, `item_id`, `outcome` |
| `disposition.recorded` | `workflow`, `decision`, `reason_code` |
| `fallback.recorded` | `workflow`, `outcome`, `reason_code` |
| `export.attempted` | `workflow`, `variant`, `outcome`, `reason_code` |

The plugin should not invent more event names until one of these fails to answer
a beta.1 blocker question.

### 3.4 Data Flow

1. User enables collection in settings.
2. User starts a session from the command palette.
3. Plugin creates a `session_id` and shows status through the status bar or a
   notice.
4. User records explicit events through commands or plugin-owned buttons.
5. Plugin creates `event_id` and validates the event against the alpha.20
   empirical schema.
6. Plugin sends the event through Memoria local HTTP:
   `POST /operation/run` with an `empirical_event.record` operation.
7. Plugin sets `idempotency_key` to `empirical-event:<event_id>`.
8. If Memoria is offline, plugin appends the event to a plugin-owned local
   spool.
9. On reconnect, plugin flushes the spool through the same operation path.

The operation path keeps Memoria as the state owner and preserves the one-write
route rule. The local spool is only a temporary queue.

### 3.5 Privacy Rules

- Never store note/source/draft/SRD body text.
- Never store absolute OS paths.
- Prefer Memoria IDs returned by HTTP reads over Obsidian file paths.
- Validate with a strict schema that rejects every field not explicitly allowed
  by `engine/empirical_events.py`.
- If only a file path exists, store a vault-relative path hash and a local
  lookup note in the diary, not in the event.
- Show the first event payload in a session before recording when
  `showPrivacyPreview` is enabled.
- Provide a command to delete the local spool.

### 3.6 Minimal UI Copy

Commands:

- `Memoria: Start data collection session`
- `Memoria: Stop data collection session`
- `Memoria: Record disposition`
- `Memoria: Record fallback`
- `Memoria: Flush queued events`
- `Memoria: Delete queued events`

Status bar states:

- `Memoria off`
- `Memoria recording`
- `Memoria offline: N queued`
- `Memoria error`

Modal fields:

- event type select
- workflow select
- decision select
- outcome select
- reason code select
- project ID input
- item type select
- item ID input

## 4. Boundaries

The plugin must not:

- read note bodies for telemetry;
- watch every editor change;
- modify Memoria-owned files directly;
- start MCP servers;
- call external network services;
- implement dashboard charts;
- implement canvas, SRD, evidence review, or export workflows.

## 5. Acceptance Checks

- Disabled by default.
- One command starts a session and emits `session.started`.
- One command records `disposition.recorded`.
- Offline mode writes one local queued event and shows the queued count.
- Reconnect flush sends queued events through `/operation/run`.
- Replaying a queued event uses the same `event_id` and idempotency key.
- A schema test rejects every field outside the event allowlist.
- A leak test proves fields such as note text, excerpts, paths, and URIs cannot
  be queued or sent.
- Token values are stored only through Obsidian secret storage; settings store
  only token presence.
- Manual deletion removes the local spool.
- The plugin can run against a disposable vault without writing Memoria-owned
  files.

## 6. Trade-Offs

| Option | Pros | Cons | Recommendation |
| --- | --- | --- | --- |
| Commands plus modal | Smallest plugin; low UI surface; easy to test | Slower for high-volume review | Use for alpha.20 |
| Dedicated side pane | Faster repeated disposition entry | Starts becoming a workflow product | Defer until modal capture is too slow |
| Passive editor watchers | More complete behavioral trace | High privacy risk and noisy data | Do not build |
| Direct local JSONL only | Works without Memoria HTTP | Splits state ownership | Use only as offline spool |
| New `/events` HTTP route | Cleaner event API | Breaks one-write-route rule | Defer unless `/operation/run` is painful |

## 7. Migration Sketch

1. Scaffold from the Obsidian sample plugin.
2. Add settings, status bar item, commands, and one event modal.
3. Add an event validator matching `engine/empirical_events.py`.
4. Store the bearer token through Obsidian secret storage.
5. Implement `/operation/run` submission for `empirical_event.record` with
   `idempotency_key=empirical-event:<event_id>`.
6. Add plugin-owned spool and flush/delete commands.
7. Dogfood for five sessions before adding any pane or passive capture.
