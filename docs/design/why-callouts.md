---
title: Why callouts exist
parent: Design Book
grand_parent: Developers
nav_order: 30
---

# Why callouts exist

Dashboards answer questions across the vault. Callouts answer questions about
the note currently open. Keeping those surfaces separate avoids forcing a reader
to context-switch for note-level context and keeps dashboards from filling with
per-note detail.

Callout content follows the hybrid pattern: deterministic selection first, LLM
composition second. Selection and ranking must be reproducible and auditable;
the prose has no single deterministic form, so it is where LLM judgment is
spent.

Produced callouts are producer-owned but human-curated. Producers do not
overwrite human edits on later runs; they append updated output. That keeps
freshness from destroying local curation.

## Related

- Operational callout model: [Callouts](../explanation/obsidian/callouts.md)
- Callout reference: [Obsidian callouts](../reference/obsidian-callouts.md)
- Hybrid methods: [Why Memoria uses deterministic methods alongside LLMs](why-computational-methods.md)
