---
topic: plugins
---

# omnisearch

Recommended human-side search, alongside [smart-connections](smart-connections.md) and [smart-lookup](smart-lookup.md): Omnisearch is **fuzzy full-text** (filenames, note bodies, optionally PDF text), where the Smart\* pair is **semantic**. Most humans want one of each. It's a genuine quality-of-life tool, but **Memoria's design does not depend on it** — agent-side search goes through Hermes tools and the `qmd` retrieval substrate (see [workflows/README.md](../../how-to/workflows/README.md)), so the [Librarian](../profiles/librarian.md) behaves identically whether or not Omnisearch is installed.

Memoria ships no config for it: its load-bearing settings — index depth, excluded folders, whether to index PDF text — are **workflow-personal, not design-standard**. Tune them to taste.

- **Install it if** your vault is large enough that core search feels slow and you want fast human-driven lookup.
- **Don't wire it into agent workflows** — that's what the Hermes retrieval tools are for, and their results are auditable in a way a plugin's private index is not.
