---
title: Obsidian callouts
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian callouts

Alpha.15 does not ship Obsidian integrations, callout plugins, CSS snippets, or
runtime adapters. The template still uses plain Markdown callout syntax for
readable orientation blocks; unsupported editors show them as quoted text.

## Registered styles

| Callout | Current use |
| --- | --- |
| `[!brief]` | Orientation blocks on space notes. |
| `[!suggestions]` | Collapsed first-action blocks on space notes. |
| `[!verification]` | Read-barrier guidance on the Knowledge space. |

## Behavior

| Property | Value |
| --- | --- |
| Source of truth | Markdown note content in `vault-template/` |
| Custom IDs | `brief`, `suggestions`, `verification` |
| Drift check | `design-system-drift` reports ad-hoc/rainbow callouts in shipped vault notes |

## Related

- Optional editor adapters: [Obsidian plugins](obsidian-plugins.md)
- Callout explanation: [Callouts](../explanation/obsidian/callouts.md)
