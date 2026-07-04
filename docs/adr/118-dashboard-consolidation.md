---
topic: decisions
id: 118
title: "Dashboard consolidation: fold redundant pages into spaces; keep system dashboards read-only; make the Inspector the read-only index"
nav_exclude: true
status: superseded
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [116, 119, 122]
supersedes: []
superseded_by: [130]
---

# ADR-118: Dashboard consolidation and the read-only system window

> **Status note (0.1.0-alpha.15):** superseded by
> [ADR-130](130-read-api-surfaces-and-copi.md). Kept for decision history;
> current architecture is carried by the consolidation ADR. Inspector pane and
> Obsidian plugin implementation references below are historical and not
> alpha.15 implementation scope.


> Status note, 2026-07-01: [ADR-122](122-sqlite-working-state-boundary.md)
> restores the read-only Inspector boundary. SQLite request state is now the
> worker authority, and worker requests run through the `memoria` CLI.

## Context

After [ADR-116](116-obsidian-surface-architecture.md) Phase 1 (collapse duplicate Dataview
pages to single-definition embeds) and Phase 2 (the Queue/Maintenance cadence split), a
walk of `system/dashboards/` found the 13 standalone `.md` pages split cleanly into four
groups: thin aliases of views the spaces already embed; one duplicate base; a pre-Queue
leftover; and the read-only operational dashboards.

ADR-116's **View** primitive says a view has *one definition, surfaced by embedding* — so a
standalone page whose view already lives in a space is redundant. And the
Inspector boundary from [ADR-122](122-sqlite-working-state-boundary.md)
is the natural always-on system window, but the Inspector predates the operational
dashboards it should summarize and the rail health-band
([ADR-116](116-obsidian-surface-architecture.md) Phase 2) it now overlaps.

## Decision

Apply ADR-116's "one view, in its space" rule to `system/dashboards/`, and align the
Inspector with it.

### 1. Delete six redundant pages — their view already lives in a space

| Page | View already in |
| --- | --- |
| `contradictions.md`, `open-questions.md` | Knowledge |
| `discuss-queue.md` | Library |
| `drift-watch.md`, `loose-ends.md` | Maintenance |
| `reading-pipeline.md` | Library + Knowledge |

`reading-pipeline.md` also carries a **broken embed** — `![[sources.base#To read & distill]]`
references a view that does not exist (the real view is `Reading pipeline`), so it renders
empty; deleting the page removes the bug. Point each page's deep-links at the space-section
anchor (`spaces/<space>#<heading>`).

### 2. Merge `project-gate` into the Project space

`project-gate.base` and `projects.base` both define an **"Active projects"** view — two
definitions of one view. Merge `project-gate.base`'s views into `projects.base`, fold the
readiness-gate views into the **Project** space (the gate *is* the project steering surface),
and delete `project-gate.md`.

### 3. Fold `weekly-review`'s unique part into Maintenance, retire the page

`weekly-review.md` is a pre-Queue leftover (created in 0.1.0.1, before the Queue/Maintenance
split): its notice-findings ≈ Maintenance's **Loose ends**, and its fleeting backlog is the
Queue's (the note self-admits the duplication). Its only unique content — the 7-day
**"New this week"** catalog/notes digest — moves into the **Maintenance** space (the weekly
surface). Delete `weekly-review.md`.

### 4. Keep five read-only system dashboards in `system/` — never a space

`board-state`, `audit-log`, `eval-trend`, `fleet-health`, `skill-state` stay where they are.
`system/` is **read-only, system-owned internals** (hidden by Portals); the user *views* these
on a trigger but never authors them. A **space is a user work-context**, so these are
categorically not space material — the same error that made Inbox-as-a-space wrong
([ADR-115](115-inbox-queue-and-retired-homepage.md)). They remain single-decision,
pull-on-trigger dashboards, reached by deep-link and the Inspector.

### 5. Make the Inspector the read-only system index — and update it

The [ADR-122](122-sqlite-working-state-boundary.md) Inspector pane (verdict band ·
board counts · recent audit) is the always-available system window behind the pull
dashboards. Update it:

- **Add a fleet/trust band** — per-lane trust from the `system/metrics/` lane-metric notes. It
  is the one *continuous* system-health signal the Inspector currently lacks (it already reads
  `system/metrics/` for the verdict).
- **Deep-link each panel to its full dashboard** — board → `board-state`, audit → `audit-log`,
  verdict → the Linter/drift surface, fleet → `fleet-health` — turning the Inspector into the
  read-only index for the system dashboards.
- **Carry only the *continuous* signals** (verdict/drift, board, audit, fleet). The *episodic*
  dashboards — `eval-trend` (quarterly) and `skill-state` (on config change) — stay pure
  pull dashboards reached on their own triggers, not in the Inspector.
- **Reconcile with the rail health-band** ([ADR-116](116-obsidian-surface-architecture.md)
  Phase 2): the rail's Now band is the one-glance ambient *signal*; the Inspector is the
  read-only *detail panel* it points to. Ship one signal + one panel — not two competing health
  surfaces, and not a third status-bar indicator.

### 6. Harden the base-embed tests

`tests/test_bases.py` asserts an embed's *text* without checking the view exists — which is why
`reading-pipeline.md`'s broken embed stayed green. Embed tests must assert the `#View` name
exists in the target `.base`.

## Consequences

- `system/dashboards/` drops from 13 `.md` to **5** (the read-only system dashboards) plus the
  `.base` view definitions. The spaces (Knowledge / Library / Maintenance / Project) gain the
  folded views; the Inspector gains the fleet band and deep-links.
- One definition per view, no standalone aliases: the user reaches **content** views in spaces
  and **system** views via the Inspector and on-trigger deep-links.
- The Inspector update is **coupled to the rail health-band** ([ADR-116](116-obsidian-surface-architecture.md)
  Phase 2) — sequence them together so the ambient signal and the read-only panel are designed
  as one.
- Migration touches: updating the deep-links for the six deleted pages (~30 links), the
  `project-gate.base` → `projects.base` merge (tests + docs), the Maintenance space note (the
  "New this week" view), the Inspector plugin (`main.js`), and `tests/test_bases.py`.

## Alternatives considered

- **Merge the five system dashboards into a "System space."** Rejected: `system/` is read-only
  internals, not a user work-context; the five have different triggers and are never used
  together; and a "space" implies a place you *work*, so treating pull-on-trigger diagnostics as
  one repeats the Inbox-as-a-space error. A read-only **index** — the Inspector — is the right
  home.
- **Keep the alias pages as thin embeds.** Allowed by ADR-116, but they add nothing the space
  section does not; deleting them and deep-linking to the space heading is cleaner and removes a
  surface to maintain.
- **Merge `weekly-review` into Maintenance wholesale.** Rejected: most of it is redundant with
  Maintenance and the Queue; only the "New this week" digest is unique.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (the View primitive; spaces are
  view collections; operational dashboards are pull-only), [ADR-122](122-sqlite-working-state-boundary.md)
  (the read-only Inspector and SQLite request boundary).
- **Depends on:** [ADR-119](119-schema-driven-document-creation.md) (Concept schemas and
  checked frontmatter are the source for Bases views).
- **Source discussion:** the alpha.8 dashboards clean-slate review.
