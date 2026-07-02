---
title: Obsidian plugin data files
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian plugin data files

Alpha.14 ships no Obsidian plugin data files. There is no committed plugin
`data.json`, plugin build artifact, editor secret file, or first-launch plugin
setup in the standalone baseline.

## Adapter rule

Optional editor adapters may keep local settings outside the baseline workspace
contract. Secret-bearing adapter files must stay gitignored and must never become
an authority for Memoria state, checks, policy, or operation definitions.

## Related

- Plugin inventory boundary: [Obsidian plugins](obsidian-plugins.md)
- Plugin settings boundary: [Obsidian plugin settings](obsidian-plugin-settings.md)
- Memoria configuration: [Memoria configuration](configuration.md)
