---
title: Callouts
parent: Obsidian
grand_parent: Explanation
nav_order: 3
---


# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria uses three plain Markdown callout identifiers in shipped template notes.
Alpha.15 does not ship Obsidian integrations, callout plugins, CSS snippets, or
runtime adapters; editors that do not understand callouts still show them as
quoted text.

For the exact shipped-vs-deferred contract, see the reference: [Obsidian callouts](../../reference/obsidian-callouts.md).

## The three callouts and what they represent

| Callout | Current use | Default |
| --- | --- | --- |
| `[!brief]` | Orientation blocks on space notes. | Expanded |
| `[!suggestions]` | Collapsed first-action blocks on space notes. | Collapsed |
| `[!verification]` | Read-barrier guidance on the Knowledge space. | Expanded |

The identifiers and drift check are in the [reference](../../reference/obsidian-callouts.md).

## Ownership and updates

- Template callouts are normal Markdown note content.
- Direct edits are observed by the same scan/check loop as other authored
  Markdown.
- Future generated callout content would need to enter through the request and
  trusted-writer path; alpha.15 does not ship that generator.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../../design/why-deterministic-methods.md)
- Callout field reference: [Obsidian callouts](../../reference/obsidian-callouts.md)
