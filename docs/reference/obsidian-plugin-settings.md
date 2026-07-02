---
title: Obsidian plugin settings
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian plugin settings

Alpha.14 has no required Obsidian plugin settings. The standalone workspace does
not ship plugin bundles, plugin settings, editor layouts, or per-plugin secrets.

## Adapter rule

If an optional Obsidian adapter is added later, its settings are adapter-owned
and must call the stable `memoria` CLI/engine. It must not own operation
manifests, request state, source authority, qmd indexing, checks, recovery, or
write policy.

## Related

- Plugin inventory boundary: [Obsidian plugins](obsidian-plugins.md)
- Plugin data-file boundary: [Obsidian plugin data files](obsidian-plugin-data-files.md)
- External integrations: [External integrations](integrations.md)
