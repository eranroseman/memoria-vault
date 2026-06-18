---
topic: decisions
id: 68
title: Workspaces v2 — Desk / Library / Studio, home.md as control panel
status: superseded
date_proposed: 2026-06-12
date_resolved: 2026-06-12
assumes: [13, 48]
supersedes: []
superseded_by: [81]
parent: Decisions
grand_parent: Explanation
nav_order: 68
---

# ADR-68: Workspaces v2 — Desk / Library / Studio, home.md as control panel

## Context

The shipped workspace set was two layouts (**Home**, **Library**) with a promised
third ("Project", slated for v0.1.0-alpha.3) that never shipped. The two layouts had
no shared contract: Home put the board in the *right* pane and the homepage in the
main pane, Library opened on an empty tab, the Co-PI chat pane appeared in neither,
and the catalog base was serialized as a `markdown` leaf. Meanwhile `home.md` had
grown prose (explanatory header, "Start here", a web link-dump) around its working
parts, and every quick action still required a palette round-trip.

## Decision

**Three workspaces — Desk, Library, Studio — under one shared layout contract**, and
`home.md` rewritten as a four-block control panel.

The shared contract, in every workspace:

- **Main pane** is the mode's work surface — a real file, never `home.md`, never an
  empty leaf.
- **Left sidebar** (~320) is navigation: 2–4 pinned tabs of that mode's drill-down
  views, with the file explorer always the **last** tab.
- **Right sidebar** (~360) is the Co-PI: the agent-client chat view
  (`agent-client-chat-view`) pinned in every workspace — the conversation partner
  travels with the mode.
- `home.md` is pinned in **no** workspace; the obsidian-homepage plugin opens it on
  launch ([ADR-13](13-homepage-front-door.md)).

| Workspace | Mode | Main pane | Left tabs (then file explorer) |
| --- | --- | --- | --- |
| **Desk** | "What needs me?" | `system/dashboards/board-state.md` | `inbox/inbox.base`, `drift-watch.md`, `weekly-review.md` |
| **Library** | Reading & synthesis | `system/dashboards/reading-pipeline.md` | `catalog/catalog.base`, `discuss-queue.md`, `open-questions.md`, `contradictions.md` |
| **Studio** | Drafting | `research-focus.md` (projects/ ships empty — the priorities note is the drafting anchor) | `system/dashboards/claims.base`, `system/patterns/patterns.base` |

Studio's right sidebar carries a second tab — the core backlink view — behind the
Co-PI tab: backlinks finally live where there is an active note. **Studio replaced
the original empty "Project" workspace promise for alpha.3; the later
[Project gate](77-project-gate.md) uses the same workspace machinery for bounded
inquiry rather than reviving that empty workspace.** `.base` leaves serialize as view type `bases`
(the core Bases view registered for the `base` extension), fixing the previous
`markdown` mis-serialization.

`home.md` becomes a **four-block control panel** (still a consumer-only Dataview
note per ADR-13): (1) a one-line **status strip** (reviews pending · blocked ·
HIGH/CRITICAL findings, linking board and drift-watch); (2) an **action row** of
command buttons (capture fleeting / Zotero / URL, delegate, resolve card, talk to
Co-PI); (3) a **navigation row** (Desk · Library · Studio · Project gate, with
Project opening inside Studio rather than adding a fourth saved workspace); (4) the **drill-down
index** — the collapsed dashboard callouts plus research-focus and
troubleshooting. Everything else (prose, link-dumps, docs-site links beyond
troubleshooting) is dropped.

Two mechanisms support the panel:

- **Buttons** (shabegom/buttons) is adopted as a **bundled (required) plugin** —
  vendored under `src/.obsidian/plugins/buttons/`, listed in
  `community-plugins.json`, golden-copy-covered. Standing rule: **command-type
  buttons only.** The plugin's `template` / `text` / `calculate` button types write
  to notes outside the policy gate and are banned.
- The core Workspaces plugin has no per-workspace load commands, so a QuickAdd user
  script (`system/scripts/load-workspace.js`) loads a named workspace via the
  internal-plugin API, and three macro choices ("Memoria: open Desk workspace / Library /
  Studio") pass the target name via QuickAdd's per-command settings — giving one
  one-click palette command (and button) per workspace.

## Consequences

- Switching workspaces is one click or one palette command; the Co-PI pane is
  present in every mode, so "talk to the agent" never requires layout surgery.
- `home.md` is glance-and-go: status, actions, navigation — no duplicated dashboard
  queries, no prose to rot. It remains git-tracked, lintable, consumer-only.
- One new required plugin (Buttons). Its write-capable button types are banned by
  rule; the linter's golden manifest covers its shipped files, and it needs no
  `data.json` (defaults suffice).
- The three QuickAdd workspace choices and the loader script are shipped config —
  covered by the existing QuickAdd consistency tests plus new workspace-layout
  tests.
- Docs that described the Home/Library pair or the promised alpha.3 Project
  workspace are rewritten; Studio supersedes that workspace promise, while
  [ADR-77](77-project-gate.md) owns the later Project gate.

## Alternatives considered

**Names.** *Inbox* (for Desk) rejected: collides with the `inbox/` folder,
`inbox.base`, and the inbox card category — "open the Inbox" would be ambiguous
three ways. *Triage* rejected: mixes a medical metaphor into the rooms metaphor.
*Office* rejected: not mode-specific (everything happens in an office). *Lab*
rejected for now: reserved for a future code-experiment surface
([#369](https://github.com/eranroseman/memoria-vault/issues/369)). Desk / Library /
Studio are consistent rooms, each self-describing of its cognitive mode.

**Keep home.md in a workspace's main pane.** Rejected: the homepage plugin already
opens it on launch; pinning it in a layout makes the work surface a launchpad and
double-opens it on every load.

**Per-workspace hotkeys instead of commands/buttons.** Rejected as the only path:
hotkeys are per-device, unshippable config; commands ship in the vault and feed
both the palette and the buttons. Hotkeys remain available on top.

**Meta Bind (or raw HTML) instead of Buttons.** Rejected: Meta Bind is a much
larger surface for the same command-dispatch need; raw HTML buttons can't dispatch
Obsidian commands without custom JS. Buttons restricted to `type command` is the
minimal writing-free mechanism.

## Related

- **Files affected:** `src/.obsidian/workspaces.json`, `src/home.md`,
  `src/system/scripts/load-workspace.js`, `src/.obsidian/plugins/buttons/`,
  `src/.obsidian/plugins/quickadd/data.json`, `src/.obsidian/community-plugins.json`.
- **Related decisions:** [ADR-13](13-homepage-front-door.md) (the front door —
  unchanged; its note is now the control panel), [ADR-48](48-copi-and-agent-consolidation.md)
  (the Co-PI the right pane pins), [ADR-49](49-catalog-in-bases-linter-monitor.md)
  (catalog in Bases), [ADR-55](55-src-scaffold-populate-golden-copy.md) (golden copy
  covers the shipped plugin files), [ADR-77](77-project-gate.md) (bounded inquiry
  surface).
- **Reference:** [Obsidian workspaces](../reference/obsidian-workspaces.md),
  [Obsidian plugins](../reference/obsidian-plugins.md).
