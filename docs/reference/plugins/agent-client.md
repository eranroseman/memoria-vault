---
topic: plugins
---

# agent-client

Implements ACP — the Agent Client Protocol — inside Obsidian. ACP is what makes the **Agent Client pane** — one of [Obsidian's UI components](../../explanation/obsidian-ui/README.md) — actually exist. The plugin runs configured agents as subprocesses (Hermes, Claude Code, Codex, Gemini CLI, and custom commands like Kilocode) and exchanges messages with them over stdio, attaching the conversation to a side pane keyed off the currently active note.

**Example with placeholder paths:** shipped at `.obsidian/plugins/agent-client/data.json.example` in the starter vault. The example uses `{{HOME}}` placeholders the human must replace with absolute paths before saving as the working `.obsidian/plugins/agent-client/data.json`. After the first launch the plugin will append a `savedSessions[]` array to the file — that's normal human-generated state.

> **Verify field names against your installed version.** `agent-client` (the community [Agent Client](https://community.obsidian.md/plugins/agent-client) plugin) is actively developed; the `data.json` keys below — `customAgents`, `defaultAgentId`, `autoAllowPermissions`, `autoMentionActiveNote`, `chatViewLocation`, `windowsWslMode`, the auto-generated `switch-agent-to-<id>` commands — are documented against the version Memoria was built on and may drift. Confirm them in **Settings → Agent Client** (or the plugin repo) before relying on exact names. The plugin's *capabilities* (ACP, multi-agent Claude Code / Codex / Gemini CLI / custom commands, per-agent permission prompts, note-mention context) are verified at time of writing.

Load-bearing settings:

- **`customAgents` — configure four Memoria profiles, labelled by identity.** The picker entries name the *agent* (Socratic, Mapper, Writer, Verifier), each followed by a one-sentence description of what it does — distinct profiles with fixed permission contracts, not modes of one assistant. For the rationale behind labelling by identity and the full text per entry, see [the picker design](../../explanation/obsidian-plugins/agent-client-picker.md).
- `defaultAgentId: "memoria-socratic"` — Memoria's ACP default is **Socratic**. The human falls into it without choosing; the other three are reached via [mode-switching hotkeys](#mode-switching-hotkeys) or via the [transient palette verbs](../command-catalog.md#interactive-retrieval-3-commands--transient-acp).
- `autoAllowPermissions: false` — **never set to `true`.** When `false`, every tool call the ACP agent makes prompts the human for approval before executing. Setting this to `true` bypasses human approval on every ACP write, which is exactly the failure mode the policy MCP exists to prevent at the Hermes side. The two layers (ACP approval + policy MCP enforcement) compose; turning either off breaks the composition.
- `autoMentionActiveNote: true` — automatically passes the active note's path and frontmatter to the agent as context. This is what makes "ask about the current note" work from one keystroke.
- `chatViewLocation: "right-tab"` — places the ACP pane on the right, matching the [Reading & Processing workspace](../obsidian-ui/workspaces.md) assumption.
- `windowsWslMode: true` — required when the agent commands live inside WSL (the typical Memoria deployment on Windows). The plugin translates Windows paths to `/mnt/c/...` style paths for the subprocess.

## Persistent vs transient ACP sessions

The picker contains four agents but they're used in two architecturally distinct ways, which the `data.json` configuration must respect:

- **Persistent ACP pane.** Socratic. The human opens the ACP pane in the Reading & Processing workspace and has a long conversation while working in adjacent panes. The session has its own lifecycle, persists in `savedSessions[]`, can be resumed later. This is the standard setup for [workflow Discuss](../../how-to/workflows/README.md).
- **Transient ACP session.** Mapper, Writer, Verifier. The human invokes the profile via the command palette for one specific question. The agent-client plugin opens a fresh session, the agent responds, the session closes. No persistent pane to manage; no savedSessions entry to accumulate. See [command-palette.md](../command-catalog.md) for the specific commands.

The distinction matters for `savedSessions[]` hygiene: persistent Socratic sessions accumulate (the closing note covers pruning); transient sessions auto-close and don't build up.

## Mode-switching hotkeys

The agent-client plugin registers a `switch-agent-to-{agentId}` command for every entry in `customAgents` (auto-generated at plugin load, one per configured agent). Memoria binds four **direct-jump hotkeys** to those commands via QuickAdd, one per mode:

| Hotkey | Plugin command | Effect |
| --- | --- | --- |
| `Ctrl+Shift+1` | `switch-agent-to-memoria-socratic` | Switch active chat to **Socratic** |
| `Ctrl+Shift+2` | `switch-agent-to-memoria-mapper` | Switch active chat to **Mapper** |
| `Ctrl+Shift+3` | `switch-agent-to-memoria-writer` | Switch active chat to **Writer** |
| `Ctrl+Shift+4` | `switch-agent-to-memoria-verifier` | Switch active chat to **Verifier** |

Direct-jump (each mode on its own key) beats a cycle hotkey on two counts: one keystroke reaches any mode regardless of starting point, and there's no cross-invocation state to track. The numeric ordering mirrors the [picker labels table](../../explanation/obsidian-plugins/agent-client-picker.md) — Socratic is `1` (the default), Verifier is `4` (closest-to-promotion). After a week of use, the human picks the agent without looking at the picker.

The hotkeys operate on the **active chat view** — they switch its agent in place. Opening a *new* chat without a hotkey uses `defaultAgentId` (Socratic). To open a new chat already in a non-default agent, the [transient palette verbs](../command-catalog.md#interactive-retrieval-3-commands--transient-acp) (`Memoria: find related notes`, `Memoria: counter-outline this section`, `Memoria: similarity-check this claim`) remain the right path — they open a transient session pre-bound to the right profile and close after the response.

Setup: in QuickAdd, register four entries of type **Command**, each pointing at one of the `switch-agent-to-memoria-*` commands above; then bind hotkeys in Obsidian's Settings → Hotkeys page. The hotkeys are human-side configuration like the [command-palette](../command-catalog.md) verbs — they ship as Memoria conventions, not as plugin settings, so devices using non-default modifier conventions can rebind freely.

## Per-device install discipline

Under the [per-device install discipline](../../project/roadmap/timeline.md#per-device-install-sets), secondary devices may have only some profiles installed. The `customAgents` array should match what's locally installed:

- **Primary device** (all seven profiles installed): all four ACP-suitable entries above.
- **Secondary, reader role** (typically only Socratic installed): just the `memoria-socratic` entry. Configuring Mapper / Writer / Verifier would let the picker show them, but invoking would fail with "profile not found" on that device.
- **Secondary, developer role** (all seven installed against a test vault): all four. The dev's Hermes points at a test vault via `HERMES_HOME`, so ACP conversations don't touch production.

Humans editing the example for their device should *delete* entries for profiles not installed locally, rather than leaving them in the picker as broken options.

## Configuring the laptop for non-Socratic ACP

The default secondary-device configuration (Socratic only) covers most human needs — persistent processing chat and lens-based reading. But three scenarios call for *persistent* chat with non-Socratic profiles: Mapper for deep corpus exploration (multi-turn drilling into clusters, density, methodological breadth), Writer for sustained drafting dialog (paragraph diagnostics, voice calibration, transition-finding), and Verifier for systematic auditing (pre-submission claim-by-claim review). These are *override* patterns — [the picker design](../../explanation/obsidian-plugins/agent-client-picker.md) names transient session as the default for these three profiles, and humans should treat persistent chat as a deliberate exception, invoked when one-shot retrieval isn't enough.

Try the [transient command-palette commands](../command-catalog.md#interactive-retrieval-3-commands--transient-acp) first — they cover the one-question, one-answer cases that are most laptop-appropriate. If those don't suffice and the human needs sustained dialog, choose the path that matches the deployment.

### Path 1 — Local install with discipline (the local-mesh option default)

Under [the local-mesh option](../../project/roadmap/deployment-options.md) (desktop + laptop, no VPS), the desktop sleeps; SSH-spawn into it is unreliable. The right path is to install the additional profile(s) locally on the laptop with the [discipline obligations from Phase 3](../../project/roadmap/timeline.md#per-device-install-sets):

1. Clone the same starter vault on the laptop and run `./install.ps1`. Under direct profile management, profile parity follows from cloning the same vault — same `.memoria/profiles/memoria-<name>/` source on every device produces the same deployed copy at `~/.hermes/profiles/memoria-<name>/`.
2. The installer registers each profile with `--alias`, so `memoria-<name>` works as a command shortcut on the laptop the same way it does on the desktop.
3. Verify `approvals.cron_mode: deny` in the profile's `config.yaml` (Memoria's default — should not need changes).
4. Add to the agent-client `customAgents` array with a `displayName` that signals the constraint:

```json
{
  "id": "memoria-writer",
  "displayName": "Writer — distill & draft (laptop, chat-only)",
  "command": "{{HOME}}/.local/bin/hermes",
  "args": ["-p", "memoria-writer", "acp"],
  "env": []
}
```

The `(laptop, chat-only)` suffix in the display name is a guardrail reminder — when the human sees it in the picker, it nudges away from card-creating commands. Small but useful.

The obligations under this path:

- **Never schedule cron jobs** on the laptop. (`approvals.cron_mode` stays at its default `deny`, but the real safeguard is simply not creating cron jobs here.)
- **Never run `hermes gateway`** on the laptop. No dispatcher, no API server, no card claiming.
- **Use only `chat`-mode commands** via ACP. Never `run draft`, never full `cite-check` passes, never `scope-project` invocations that write project-scratch files.
- Treat the laptop's ACP sessions with these profiles as *information surfaces*, not *production surfaces*. The architectural protection (the policy MCP) catches some write attempts, but not all — a Writer `run draft` invoked on the laptop will write to the synced vault if the human isn't careful.

### Path 2 — SSH-spawn into the primary (the always-on option default; optional under local-mesh)

Under [the always-on option](../../project/roadmap/deployment-options.md) (VPS + laptop), the VPS is always reachable and has all seven profiles. Configure the `customAgents` entries to spawn the Hermes process on the VPS over SSH:

```json
{
  "id": "memoria-mapper-remote",
  "displayName": "Mapper — find related (via VPS)",
  "command": "ssh",
  "args": ["vps-host", "hermes", "-p", "memoria-mapper", "acp"],
  "env": []
}
```

No Memoria profile needed on the laptop. The agent-client plugin spawns SSH; SSH connects to the VPS; the VPS runs Hermes with the right profile; stdio streams back to the laptop's ACP pane.

Prerequisites:

- SSH always reachable (Tailscale or VPN connecting laptop to VPS).
- VPS configured to accept SSH from the laptop's key.
- Tolerance for ~100–500ms latency per message (noticeable in fast back-and-forth, unnoticeable in research-paced conversation).

This pattern also works under local-mesh as a fallback when the desktop happens to be on, but it's not the recommended `local-mesh` default because desktops sleep. Under `always-on`, where the primary never sleeps, SSH-spawn is unambiguously preferred.

### Deployment-specific recommendations

| Deployment | Preferred path for non-Socratic ACP on laptop |
|---|---|
| **`local-only`** (single workstation) | N/A — there's no laptop |
| **`local-mesh`** (desktop + laptop, Syncthing) | Path 1 (local install + discipline) — desktop reliability is too low for SSH-spawn to be the default |
| **`obsidian-sync`** (no VPS) | Same as `local-mesh` — desktop reliability dictates Path 1 if there's a laptop; same discipline applies |
| **`obsidian-sync` + VPS** (for cron) | Path 2 (SSH-spawn into the VPS) — same as `always-on` in this respect, since cron requires an always-on machine |
| **`always-on`** (VPS + laptop) | Path 2 (SSH-spawn) — VPS is always-on, no local install needed |

On `local-mesh`, frequently wanting non-Socratic ACP from the laptop is a signal worth taking seriously: the discipline cost compounds, and the per-laptop profile installs accumulate maintenance overhead. The architectural answer is **migrate to `always-on`** — the VPS's always-on availability is exactly what makes SSH-spawn work, and it eliminates the install-and-discipline overhead entirely on every secondary device. Memoria's design explicitly names this trajectory: *"Start with `local-only`; migrate to `local-mesh` when a second device enters the workflow; graduate to `always-on` when you need unattended automation."* Frequent non-Socratic laptop ACP is one of the workflows that pulls humans toward `always-on`.

The plugin also persists `savedSessions` (an array of past ACP conversations with title and timestamp) in its `data.json`. These are useful for resuming a Socratic session, but they grow without bound — humans on long-running vaults should periodically prune them via the plugin's session-manager UI to keep `data.json` small. Unlike [obsidian-local-rest-api](obsidian-local-rest-api.md), this `data.json` contains no secrets and **is** safe to commit (sessions are conversation pointers, not credentials).

## Related

- [agent-client-picker.md](../../explanation/obsidian-plugins/agent-client-picker.md) — why the picker labels profiles by identity, and the full picker labels / descriptions table.
