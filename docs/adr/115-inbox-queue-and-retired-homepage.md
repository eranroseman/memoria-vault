---
topic: decisions
id: 115
title: "Inbox is the queue, not a space; retire the homepage front door for a startup shell + welcome seed"
nav_exclude: true
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [70, 81, 101, 114]
supersedes: [13]
superseded_by: []
---

# ADR-115: Inbox is the queue, not a space; retire the homepage front door

## Context

[ADR-114](114-left-pane-navigator.md) introduced the left-pane navigation rail and
committed to a principle the rest of the model had not caught up to: **the Inbox is a
*state*, not a *place*.** The rail surfaces the Inbox count as an ambient signal under
*Now* and owns space-switching. Three things still assumed the pre-rail world:

1. **Inbox was the fourth co-equal space** ([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) — `type: space`, `space: inbox`), despite being a triage queue that converges to empty rather than a room you dwell in.
2. **Every space note carried a nav row** — the switcher the rail replaced.
3. **The homepage plugin opened the Inbox on launch** ([ADR-13](13-homepage-front-door.md), [ADR-81](81-persistent-gate-dashboards.md)). With the rail now carrying the "what needs me?" signal, forcing the full queue as the launch workspace is redundant, casts a knowledge/writing tool as inbox-management, and — since empty is the goal — often lands the human on nothing.

## Decision

**Reclassify the Inbox as the queue, drop the nav rows, and retire the forced-landing homepage in favour of Obsidian session restore plus a saved-shell fallback.**

1. **Inbox is the queue (`type: queue`), not a space.** A new `queue` type (`schemas/types/queue.yaml`, category `spaces`, mapped `queue → spaces/`) is added; `spaces/inbox.md` becomes `type: queue` (still titled "Inbox"). The `space` type's enum drops `inbox` → `[library, knowledge, project]`. **The durable spaces are three** — Library, Knowledge, Project; the Inbox is the transient triage surface reached from the rail's *Now*.
2. **Space notes carry no nav row.** The rail owns switching ([ADR-114](114-left-pane-navigator.md)), so a space note is purely its JTBD dashboard — title, brief, embedded views, guides. The four notes' nav rows are removed.
3. **The homepage plugin is retired.** The old forced landing opened the Inbox queue and made Memoria feel like an inbox manager. The `homepage` community plugin, its vendored bundle, and its provenance-lock entry remain removed.
4. **Startup preserves the session and repairs a missing rail.** QuickAdd's `Memoria: restore shell on startup` macro runs after Obsidian's first layout is ready. If the pinned `_nav.md` rail is already present, it only reveals the rail and leaves the main pane where the previous session restored it. If the rail is missing, it calls the core Workspaces plugin's `loadWorkspace("Memoria")`, restoring `home.md` in the main pane, the pinned rail on the left, and the Co-PI pane on the right without reintroducing the old Inbox homepage.
5. **The launch/reset shell seeds `home.md`.** The saved **Memoria** workspace points its main pane at `home.md`, recast as a thin welcome note ("start here": capture your first source, the three places, ask the Co-PI). It is not a dashboard and not a daily front door; it owns no computation. Daily movement belongs to the pinned rail.

## Consequences

- Data model: new `queue` type; `space` enum loses `inbox`; `folders.yaml` and the Linter `detectors.py` folder map gain `queue → spaces/`. Type count 24 → 25; templates exclude `queue` (authored, not template-created), so the template count stays 20.
- App config: `community-plugins.json` drops `homepage`; `src/.obsidian/plugins/homepage/` is deleted and removed from `plugin-provenance-lock.json`; the **Memoria** workspace's main leaf points at `home.md` and pins `_nav.md`.
- `home.md` is rewritten from a homepage-fallback into the welcome note. The launch repair path depends on the already-bundled QuickAdd startup hook plus Obsidian's core Workspaces plugin — no new community plugin or provenance lock.
- Live docs are updated to current-state: the Inbox is "the queue" (not a space), the spaces are three, and the launch surface is the saved **Memoria** shell restored on startup. ADR and `releasing/` prose are left in their own vocabulary; only [ADR-13](13-homepage-front-door.md) is marked superseded.
- The "what needs me?" ambient signal is fully carried by the rail's *Now*; the daily glance still lives on the Inbox queue note.

## Alternatives considered

- **Keep Inbox nominally a "space" but stop launching into it (Phase 1 only).** Rejected: it fixes the launch redundancy but leaves the model saying a converges-to-empty queue is a durable room. Reclassifying is what makes the model say what it means.
- **Keep the homepage plugin to force a stable daily landing.** Rejected: the old plugin opened the Inbox queue and duplicated the rail's ambient signal. The saved-shell startup macro restores the rail without another vendored community plugin.
- **Rely on native last-session restore only.** Rejected after live Obsidian verification: a stale session can reopen without the rail or Co-PI pane, and then the normal shell fails before the user clicks anything. Loading the saved shell on startup is the boundary that makes the rail pattern durable.
- **Delete `home.md` entirely and seed startup into Library.** Rejected: a brand-new user benefits from a curated welcome over an empty dashboard, and onboarding ([ADR-113](113-copi-guided-onboarding.md)) needs a landing to attach to. `home.md` is kept as the startup/reset welcome seed.

## Related

- **Supersedes:** [ADR-13](13-homepage-front-door.md) (the homepage front-door note auto-opened by obsidian-homepage).
- **Refines:** [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) (the four spaces become three + the Inbox queue), [ADR-81](81-persistent-gate-dashboards.md) (dashboards stay persistent notes; only the launch target changes), [ADR-114](114-left-pane-navigator.md) (completes "Inbox is a state, not a place").
- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (system health is ambient).
- **Onboarding seed:** [ADR-113](113-copi-guided-onboarding.md).
- **Source discussion:** the alpha.8 spaces-and-homepage clean-slate review.
