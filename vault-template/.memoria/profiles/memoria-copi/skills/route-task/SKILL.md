---
name: route-task
description: "Route work from the conversation to the right active background lane via the tasks MCP (delegate_route_task): pick the lane, compose the self-contained handoff payload (goal · context · allowed_paths · expected_outputs · review_checks), and tell the PI what was sent. The Co-PI's only mutation path is enqueue/delegation; it never writes canonical vault files."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Delegation, Kanban, Lanes]
    related_skills: [obsidian, qmd]
  memoria:
    skill_id: "route-task"
    profile: memoria-copi
    lane: delegate
    mcp_tools:
      - tasks.delegate_route_task
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
    write_scope: []
    outputs: []
---

# route-task

Route work from the conversation to the right active background lane via the tasks MCP
(`delegate_route_task`). You converse; the worker/lane runs; results surface through
generated attention and projection views.

## Lane routing

| The PI wants… | lane | runs on |
|---|---|---|
| a source found / catalogued / enriched | `catalog` | Librarian |
| a kept source distilled into claim stubs | `extract` | Librarian |
| link candidates / tensions surfaced | `link` | Librarian |
| the corpus mapped / coverage / clusters / a canvas seed | `map` | Librarian |
| a claim or draft verified (judgment checks + red-team) | `verify` | Peer-reviewer |

Drafting/writing and code lanes are deferred in alpha.11; do not route `draft`
or `code` tasks.

## The handoff payload

Always self-contained: **goal** (one imperative sentence) · **context** (what the lane
can't infer — the conversation's conclusions, relevant citekeys/paths) · **allowed_paths**
(narrow the lane's ceiling to what this task needs — never widen; the MCP validates) ·
**expected_outputs** · **review_checks** (what the PI should look at when results surface).

## Discipline

- One task per card; batch-shaped work (a screening list) is ONE card pointing at a
  worklist, never N cards (ADR-54).
- Use an `idempotency_key` for re-runnable requests (e.g. `reingest:<citekey>`).
- Tell the PI what you sent and where ("delegated to the catalog lane; the candidate
  card will land in the Inbox"). If the board is unreachable, give the palette/CLI
  fallback the tool returns — never silently drop work.
