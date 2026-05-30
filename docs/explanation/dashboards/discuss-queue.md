---
topic: dashboards
---

# `discuss-queue` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/discuss-queue.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

List every fully-classified (`lifecycle: current`) paper note that hasn't yet had a Socratic processing pass. Open it during a reading session, when deciding which source to think about next. This is the **upstream-cognitive-discipline dashboard** — a long list means the human's processing is falling behind their ingest rate; a short one means it's keeping up. Making that asymmetry visible early is the point, before it hardens into a synthesis backlog three months later.

## What this dashboard is not

- **Not [`reading-pipeline`](reading-pipeline.md).** See also: [reading-pipeline](reading-pipeline.md) for the full contrast between the two dashboards.
- **Not a generic to-do list.** The implied next action is specifically *Socratic processing* (workflow Discuss) — invoke the Socratic profile, work through the questions, then write a claim note. Surfacing the queue without the implied next action would just be a list.
- **Not Mapper's territory.** Discuss-queue is per-source upstream work. Mapper's outputs (corpus-map, gap-report, comparative-brief) operate across sources at a different abstraction.

## Design decisions

- **Five-or-fewer rows = healthy. Ten or more = schedule a reading session.** These are human-facing health thresholds called out in the dashboard, not enforced by any system. The point is to make the queue's depth read at a glance.
- **`lifecycle: current` AND no `processed:` tag is the gate.** A paper note is on the queue when classification is complete and Socratic hasn't happened yet. Adding a `processed:` task line removes it from the queue.
- **A reading-session cadence, not a daily glance.** Unlike [Daily Health](daily-health.md)'s morning health check, discuss-queue is consulted only at reading time — a deliberate cadence choice that keeps it from becoming another daily alarm.
- **The Reading & Processing workspace includes this dashboard.** Per [obsidian-ui/workspaces.md](../../reference/obsidian-ui/workspaces.md), discuss-queue is the left pane of the Cmd-2 workspace alongside [`reading-pipeline`](reading-pipeline.md). The workspace exists specifically to protect this discipline.

## Related

- [workflows/upstream/discuss.md](../../how-to/workflows/upstream/discuss.md) — the workflow this dashboard feeds
- [Socratic design summary](../profiles/socratic.md) — the profile invoked to drain the queue
- [`reading-pipeline`](reading-pipeline.md) — broader sibling view
- [vault/README.md](../vault/README.md) — definitions of the `lifecycle` states (`proposed` / `current`) this dashboard gates on
- [obsidian-ui/workspaces.md](../../reference/obsidian-ui/workspaces.md) — the Reading & Processing workspace this dashboard anchors
