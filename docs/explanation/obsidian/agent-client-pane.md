---
title: The Agent Client pane
parent: Obsidian
grand_parent: Explanation
nav_order: 2
---

# The Agent Client pane

Alpha.15 does not ship an Agent Client pane. The supported conversational path
is `memoria ask`, which reads checked retrieval documents through the engine and
returns a sourced answer in the terminal.

The old pane idea remains useful as an adapter constraint: a future editor pane
may improve ergonomics, but it must call the same CLI/engine and stay read-only
unless it enters the normal request lifecycle. It cannot own operation manifests,
write policy, scheduled work, or source authority.

## Related

- Query from the CLI: [Query the vault](../../how-to-guides/knowledge/query-the-vault.md)
- Plugin boundary: [Obsidian plugins](../../reference/obsidian-plugins.md)
- CLI reference: [Memoria CLI](../../reference/cli.md)
