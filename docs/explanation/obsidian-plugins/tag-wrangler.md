---
topic: plugins
---

# tag-wrangler

Recommended. Memoria's controlled-vocabulary discipline (`study_design`, `methods`, `topic` lists in `00-meta/04-reference/`) means tags are semi-official — when a vocabulary term renames, every note carrying the old term needs to update. Tag Wrangler is the bulk-rename / merge / inspect tool for that. Without it, vocabulary renames become a manual find-and-replace across hundreds of notes.

Load-bearing settings: none. The plugin's value is its actions (rename, merge, find), not its persistent config.

Operational note: Tag Wrangler operates on `tags:` frontmatter and inline `#tags`. Memoria's tags are primarily in frontmatter (per the [vault/README.md](../vault/README.md) schema); inline `#tags` are human-added in note bodies. Both are visible to Tag Wrangler.
