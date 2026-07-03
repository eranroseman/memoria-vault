---
title: Agent Client pane
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 3
---

# Agent Client pane

Alpha.15 does not ship an Agent Client/Hermes profile chat pane. Use the
standalone CLI for the supported conversational query path:

```bash
memoria ask --workspace <workspace> --question "What needs attention?"
```

Obsidian remains useful as a human reading and editing surface, but the core
runtime does not depend on the Agent Client plugin. Any future pane adapter must
call the same `memoria` CLI/engine and must not become the authority for
operation manifests, write policy, or scheduled work.

## Related

- Current CLI commands: [CLI](../../reference/cli.md)
- Hermes boundary: [Hermes CLI](../../reference/hermes-cli.md)
- Set up the standalone workspace: [Set up the vault](../setup/set-up-the-vault.md)
