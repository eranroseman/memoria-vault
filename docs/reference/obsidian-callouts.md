---
title: Obsidian callouts
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian callouts

Memoria registers three custom callout styles through Callout Manager:
`[!brief]`, `[!suggestions]`, and `[!verification]`.

In alpha.11 these are presentation styles for shipped notes and workspace
orientation. They are not evidence that QuickAdd link/verify producers exist.

## Registered styles

| Callout | Current use |
| --- | --- |
| `[!brief]` | Orientation blocks on Home and space notes. |
| `[!suggestions]` | Collapsed first-action blocks on space notes. |
| `[!verification]` | Read-barrier guidance on the Knowledge space. |

## Behavior

| Property | Value |
| --- | --- |
| Source of truth | `vault-template/.obsidian/plugins/callout-manager/data.json` |
| Custom IDs | `brief`, `suggestions`, `verification` |
| Drift check | `design-system-drift` reports ad-hoc/rainbow callouts in shipped vault notes |

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Plugin settings: [Obsidian plugin settings](obsidian-plugin-settings.md)
- Callout explanation: [Callouts](../explanation/obsidian/callouts.md)
