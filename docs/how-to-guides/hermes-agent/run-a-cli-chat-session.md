---
title: Run a CLI chat session
parent: Hermes Agent
grand_parent: How-to guides
nav_order: 2
---

# Run a CLI chat session

Alpha.14 does not ship Hermes profile chat sessions. Use the standalone Memoria
CLI for the supported query path:

```bash
memoria ask --workspace <workspace> --question "What needs attention?"
```

For project-scoped questions:

```bash
memoria project ask <project-id> --workspace <workspace> --question "What are the gaps?"
```

If you experiment with Hermes externally, treat it as an adapter that calls the
same `memoria` CLI/engine. Do not rely on Hermes profile aliases, profile skills,
or Hermes board commands as alpha.14 product surfaces.

## Related

- Current CLI commands: [CLI](../../reference/cli.md)
- Hermes boundary: [Hermes CLI](../../reference/hermes-cli.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
