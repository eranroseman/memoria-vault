# System map

Plain-language summary of how Memoria fits together. The in-vault counterpart to [architecture/README.md](../../../memoria-docs/architecture/README.md).

## Three layers

1. **The vault** — what you see in Obsidian. Stable folder structure, durable knowledge, audit trail. This is where your work lives.
2. **Hermes** — the agent layer. Seven specialist profiles (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter) with narrow permissions.
3. **The policy MCP** — the runtime gate. Every vault write goes through it; out-of-policy writes are denied or degraded to dry-run.

## Folders encode lifecycle, not topic

- `10-inbox/` → capture and classify
- `20-sources/` → describe what others say
- `30-synthesis/` → your own thinking (human-owned)
- `40-workbench/` → projects and drafts in flight
- `50-deliverables/` → shipped work

A paper note about HCI lives in `20-sources/01-papers/`, not in `HCI/`. Topics belong in frontmatter (`topic:`) and in wikilinks (`` `[[concept]]` ``).

## The review gate is structural, not advisory

Promotion to canonical zones (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) requires explicit human approval. Agents propose; humans decide. The policy MCP enforces this — even an agent that thinks it's done cannot auto-promote. This is the design's defining commitment.

## Three central insights

- **Karpathy's LLM-wiki pattern** — the agent compiles raw sources into a persistent, interlinked wiki, instead of re-retrieving from scratch every query.
- **Luhmann's Zettelkasten** — atomic notes, explicit links, and typed lifecycle distinctions (source / claim / reference) prevent the wiki from becoming a pile.
- **Vannevar Bush's Memex** — associations are first-class objects; the agent preserves trails that would otherwise disappear into chat history.

## What lives where

- **Human notes** → `00-meta/` (this folder), the lifecycle folders above
- **Hermes profiles, MCP servers, lane policies** → `.memoria/` (dot-hidden tooling)
- **Obsidian config** → `.obsidian/` (dot-hidden)
- **Machine config** (`library.bib`, `tool-registry.yaml`, Pandoc CSL files) → `.memoria/`

## What Memoria isn't

- **Not an autonomous research scientist.** It does not run experiments end-to-end or self-promote synthesis to canonical knowledge.
- **Not a general chat assistant.** Conversations are inputs to filing, not the substrate.
- **Not a Deep Research agent.** Memoria is corpus-curating and durable; Deep Research agents are query-driven and ephemeral.
- **Not a team tool** in its current form. It assumes one human reviewer who owns judgment.

---

**For depth:** [architecture/README.md](../../../memoria-docs/architecture/README.md) — the authoritative architecture explainer. [vision.md](../../../memoria-docs/vision.md) — the design philosophy.
