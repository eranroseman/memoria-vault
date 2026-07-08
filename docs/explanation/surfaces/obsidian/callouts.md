---
title: Callouts
parent: Surfaces
grand_parent: Explanation
nav_order: 22
---


# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria uses plain Markdown callouts in shipped template notes. The Obsidian
adapter does not make them special product state: editors that do not understand
callouts still show them as quoted text. That is why callouts are safe as local
reading context but unsuitable as workflow state.

For the exact shipped identifiers, see [Design system](../../../design/surfaces/design-system.md).

## Ownership and updates

- Template callouts are normal Markdown note content.
- Direct edits are observed by the same scan/check loop as other authored
  Markdown.
- Future generated callout content would need to enter through the request and
  trusted-writer path; the proof adapter does not ship that generator.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../../../design/boundaries/why-deterministic-methods.md)
