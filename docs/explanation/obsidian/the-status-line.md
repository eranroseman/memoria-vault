---
title: The status line
parent: Obsidian
---

# The status line

The status line is the vault's one **always-visible ambient indicator** — a single Dataview-rendered line that shows Linter findings and Kanban queue counts at a glance. It is the deliberate exception to "[chrome is hidden by default](visual-discipline.md#why-chrome-is-hidden-by-default)": it stays on screen because its whole job is to let the human *not* go looking.

For the exact format, counters, and design rules, see the reference: [Obsidian status line](../../reference/obsidian-status-line.md). This page explains *why* it exists and why it's shaped the way it is.

---

## What it shows

Two producers share one line — Linter first, then Kanban — e.g. `✓ Schema valid · 2 broken links · Active: 3 · Waiting: 2 · Review: 7 · Retries: 0`. The Linter segment reports lightweight last-pass findings (schema validity, broken-link count); the Kanban segment reports live queue depths (running, blocked, awaiting-review, retrying). It is rendered as a Dataview widget pinned in a note — not the OS status bar, which Dataview cannot write to.

---

## Why an ambient line, not a dashboard

The status line and the dashboards answer different questions. A dashboard answers *"what specifically needs my attention, and what should I do about it?"* — it lists items, and you open it deliberately. The status line answers only *"is everything roughly fine right now?"* — a question you ask constantly, in passing, and want answered without a click.

Forcing that constant question through a dashboard would mean either keeping a dashboard permanently open (chrome that defeats the focus discipline) or repeatedly navigating to one (friction that erodes the habit). A single ambient count costs no attention until a number is non-zero. The line is the cheapest possible "should I look closer?" signal.

---

## Why state, never decisions

The governing rule is **show state, not decisions**. A count is ambient — `Review: 7` tells you a queue has depth without telling you what to do. The list of *which* seven cards, and the act of approving them, belongs in the [board-state dashboard](../dashboards/daily-glance/board-state.md). This division is what keeps the line glance-readable in under a second: it never grows into a panel, because anything that would require reading prose or making a choice is, by rule, escalated to a dashboard.

The same rule bounds the Linter segment: lightweight findings (broken links, schema validity) sit on the line; heavy findings (schema migrations, structural drift) escalate to [drift-watch dashboard](../dashboards/structural-health/drift-watch.md). The line carries the *temperature*, not the diagnosis.

---

## Why two producers maximum

Linter + Kanban is the working set, and the cap is deliberate. Each additional ambient producer competes for the same one-second glance; a third would make the line a string of numbers no one parses — which is exactly the "cockpit of indicators" failure the [visual discipline](visual-discipline.md) exists to prevent. If a new signal seems to deserve the status line, the question to ask first is whether it belongs in a dashboard instead.

---

## Related

- The restraint principle this surface embodies: [Visual-style discipline](visual-discipline.md)
- Where the Kanban counts expand to full detail: [board-state dashboard](../dashboards/daily-glance/board-state.md)
- Where heavy Linter findings escalate: [drift-watch dashboard](../dashboards/structural-health/drift-watch.md)
- Format, counters, and design rules (reference): [Obsidian status line](../../reference/obsidian-status-line.md)
