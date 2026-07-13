---
title: Surfaces
parent: Explanation
nav_order: 4
has_children: true
permalink: /explanation/surfaces/
---

# Surfaces

Surfaces explain what the PI sees. They render engine state and editor context,
but they do not own workflow state or write authority.

## The division of labor

Three surfaces, one envelope: the **editor** is where judgment happens — the
researcher reading, writing, and deciding in plain files; the **plugin** is an
ambient layer — status, inbox cards, one-click dispositions — that only
enqueues through the engine, never writes on its own; the **agent** is voice
and hands — it converses and files dispositions through the same operation
envelope with its true actor. **Planned: F1 alpha.21; U1/U3/U4 beta.1.** A fourth,
invisible role (the engine's own jobs) validates and indexes behind them all.
Every surface goes through the same queue; none is a second authority.

**Planned beta.1 — U1.** Five jobs organize the work regardless of surface:
Read, Knowledge, Project, Review, and Upkeep.

**Planned beta.1 — U2.** Deep work (compose, canvas, drafting) stays separate
from task work (inbox, review queues, maintenance) — the compose surface never
shows the recommendation stream. And the keep-test governs all of it: the
product must remain fully operable with `vim` and a file browser; every
deep-work artifact is a plain file; the plugin is never the only way in.

| Page | What it covers |
| --- | --- |
| [Dashboards](dashboards/README.md) | How health, queues, and maintenance surface |
| [Obsidian](obsidian/README.md) | Optional editor integration boundaries |
