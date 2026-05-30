---
topic: obsidian-ui
---

# Workspaces

Dashboards alone aren't the UX. *Where* they sit on the screen is. Memoria uses three Obsidian workspaces (saved via the core Workspaces plugin), one per cognitive mode, bound to keyboard shortcuts so switching is muscle-memory.

> **Prerequisite.** The **Workspaces core plugin must be enabled** before any of this works. Obsidian ships it off-by-default; the `Cmd-1/2/3` bindings have nothing to bind to until the plugin is on. Verify under Settings → Core plugins → Workspaces. The `plugin-config-drift` detector (see the [Linter design summary](../../explanation/profiles/linter.md) and the runtime `M-detectors.md` alongside the Linter SOUL.md in the starter vault) flags vaults where this is off.

| Workspace | Hotkey | What's on screen | When to use it |
| --- | --- | --- | --- |
| **Human** | `Cmd-1` | Left: [Daily Health](../../explanation/dashboards/daily-health.md). Main: empty / scratch. Right: [`board-state`](../../explanation/dashboards/board-state.md). | Default. Open the vault, glance at health, close. Used 30 seconds at a time, multiple times per day. |
| **Reading & Processing** | `Cmd-2` | Left: [`discuss-queue`](../../explanation/dashboards/discuss-queue.md) (primary) and [`reading-pipeline`](../../explanation/dashboards/reading-pipeline.md). Main (split): source PDF on the left, paper note on the right. Right sidebar: Backlinks + Outgoing links + (optional) Socratic profile ACP pane for `socratic-processing` conversations. | Reading sessions. The single most important workspace for protecting upstream discipline — this is where literature → claim-note transformation happens. |
| **Drafting** | `Cmd-3` | Left: project folder tree (`40-workbench/<project>/`). Main (large): the draft. Right: linked claim notes via Backlinks. Bottom pane: latest verification report. | Project work. Single-focus on the draft, with supporting material on the edges. |

The mode shifts are deliberate. Trying to do reading, drafting, and human classification from one view is what makes most Obsidian setups feel chaotic — each mode wants a different visual ratio of inputs, outputs, and ambient state.

## Design rules for workspaces

- **One mode per workspace.** Don't bind a workspace to a topic ("the JITAI workspace") or a project ("the dissertation workspace"). Modes are durable; topics change.
- **Three is the working set.** Adding a fourth means the human forgets which hotkey maps to which mode. If a fourth mode genuinely emerges, it earns its workspace by displacing one of the three, not by extending the set.
- **Workspaces travel with the vault.** `.obsidian/workspaces.json` is deferred. Until it ships, create workspaces manually using Obsidian's Manage Workspaces command; save any layout changes back to the workspace so the configuration survives `git pull` on another machine.

The three `Cmd-1/2/3` bindings are configured under Settings → Hotkeys (the Workspaces core plugin must be enabled first — see the prerequisite callout above).

> **Not the same as profile switching.** These `Cmd-1/2/3` bindings switch *workspace layouts*. Switching the ACP *profile* (Socratic / Mapper / Writer / Verifier) uses a separate set — `Ctrl+Shift+1/2/3/4` — defined in [agent-client.md](../plugins/agent-client.md#mode-switching-hotkeys). The two number-key sets are adjacent but do not collide (`Cmd` vs `Ctrl+Shift`); keep them distinct when configuring hotkeys.
