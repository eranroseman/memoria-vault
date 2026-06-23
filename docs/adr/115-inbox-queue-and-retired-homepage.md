---
topic: decisions
id: 115
title: "Inbox is the queue, not a space; retire the homepage front door for session-restore + a welcome seed"
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

**Reclassify the Inbox as the queue, drop the nav rows, and retire the forced-landing homepage in favour of native session-restore seeded by a first-run welcome note.**

1. **Inbox is the queue (`type: queue`), not a space.** A new `queue` type (`schemas/types/queue.yaml`, category `spaces`, mapped `queue → spaces/`) is added; `spaces/inbox.md` becomes `type: queue` (still titled "Inbox"). The `space` type's enum drops `inbox` → `[library, knowledge, project]`. **The durable spaces are three** — Library, Knowledge, Project; the Inbox is the transient triage surface reached from the rail's *Now*.
2. **Space notes carry no nav row.** The rail owns switching ([ADR-114](114-left-pane-navigator.md)), so a space note is purely its JTBD dashboard — title, brief, embedded views, guides. The four notes' nav rows are removed.
3. **The homepage plugin is retired.** There is no forced landing. On launch Obsidian **natively restores the last session**; the human returns to whatever they were working on, with the rail orienting them. The `homepage` community plugin, its vendored bundle, and its provenance-lock entry are removed.
4. **A fresh vault / layout reset seeds `home.md`.** The saved **Memoria** workspace points its main pane at `home.md`, recast as a thin **first-run welcome note** ("start here": capture your first source, the three places, ask the Co-PI). It is not a dashboard and not a daily front door; it owns no computation. Returning users restore past it.

## Consequences

- Data model: new `queue` type; `space` enum loses `inbox`; `folders.yaml` and the Linter `detectors.py` folder map gain `queue → spaces/`. Type count 24 → 25; templates exclude `queue` (authored, not template-created), so the template count stays 20.
- App config: `community-plugins.json` drops `homepage`; `src/.obsidian/plugins/homepage/` is deleted and removed from `plugin-provenance-lock.json`; the **Memoria** workspace's main leaf points at `home.md`.
- `home.md` is rewritten from a homepage-fallback into the first-run welcome note. The launch behaviour now depends on **no startup plugin** — one fewer vendored dependency and one fewer provenance lock to maintain.
- Live docs are updated to current-state: the Inbox is "the queue" (not a space), the spaces are three, and the launch surface is `home.md` via session-restore. ADR and `releasing/` prose are left in their own vocabulary; only [ADR-13](13-homepage-front-door.md) is marked superseded.
- The "what needs me?" ambient signal is fully carried by the rail's *Now*; the daily glance still lives on the Inbox queue note.

## Alternatives considered

- **Keep Inbox nominally a "space" but stop launching into it (Phase 1 only).** Rejected: it fixes the launch redundancy but leaves the model saying a converges-to-empty queue is a durable room. Reclassifying is what makes the model say what it means.
- **Keep the homepage plugin to force a stable daily landing.** Rejected: a forced daily landing duplicates the rail's ambient signal and discards the user's working context every launch. Session-restore returns the human to real work; the rail covers orientation. A forced home and a rich daily home digest are mutually exclusive, and the rail already provides the digest's main value.
- **Delete `home.md` entirely and seed first-run into Library.** Rejected: a brand-new user benefits from a curated welcome over an empty dashboard, and onboarding ([ADR-113](113-copi-guided-onboarding.md)) needs a landing to attach to. `home.md` is kept, but demoted to a first-run welcome seed.

## Related

- **Supersedes:** [ADR-13](13-homepage-front-door.md) (the homepage front-door note auto-opened by obsidian-homepage).
- **Refines:** [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) (the four spaces become three + the Inbox queue), [ADR-81](81-persistent-gate-dashboards.md) (dashboards stay persistent notes; only the launch target changes), [ADR-114](114-left-pane-navigator.md) (completes "Inbox is a state, not a place").
- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (system health is ambient).
- **Onboarding seed:** [ADR-113](113-copi-guided-onboarding.md).
- **Source discussion:** the alpha.8 spaces-and-homepage clean-slate review.
