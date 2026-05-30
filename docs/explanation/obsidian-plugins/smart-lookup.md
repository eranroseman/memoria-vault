---
topic: plugins
---

# smart-lookup

> [!warning] Held for evaluation — details not verified against current plugin version.
> The sections below are carried forward from earlier Memoria design notes. Confirm Smart Lookup is still maintained and that its index-sharing behaviour with Smart Connections holds in the installed versions before treating this as a standard install.

Smart Lookup is recommended paired with [smart-connections](smart-connections.md). Both are by the same author (brianpetro) and **share one embeddings index**, approaching semantic search from opposite directions: Smart Connections surfaces notes *similar to the one you're looking at*; Smart Lookup is **question-first** — type a natural-language question, get the most relevant vault notes back.

Like Smart Connections, it's a **parallel peer to Memoria, not a wired component**: agent retrieval goes through Hermes tools (`qmd` and the search skills in [workflows/README.md](../../how-to/workflows/README.md)), not this plugin. Use it for human navigation ("what do I have on receptivity detection?"); don't feed it into agent workflows.

## Notes (unverified)

Load-bearing settings: none specific to Memoria. Because it shares Smart Connections' index, configure the embeddings once — point them at the cheap model tier, not Claude (see [smart-connections](smart-connections.md)). Installing Smart Lookup without Smart Connections is unusual; the pairing is the point.
