---
topic: architecture
---

# Capability stack

The minimum capability stack to operate Memoria:

1. **Hermes**, configured with seven profiles (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter).
2. **The Hermes built-in Kanban** with the required state machine and schema fields (see [kanban-board/README.md](../../explanation/kanban-board/README.md)).
3. **Obsidian** as the vault editor and Dataview query host.
4. **Zotero + Better BibTeX** for the bibliographic backbone.
5. **External APIs**: OpenAlex, Semantic Scholar, PubMed, Crossref, Unpaywall, ORCID, ROR for enrichment.
6. **Git** for vault history.
7. **The Obsidian Local REST API** to let Hermes read/write the vault. (The **Agent Client pane (ACP)** is the *complementary* editor-level agent interaction surface — not an alternative; see the table below.)
8. **Pandoc** for export.

**Optional, adopt-when-needed: agent-side retrieval.** When the agent needs semantic recall over the vault (the Mapper's corpus queries, the search skills), Memoria uses **`qmd`** ([tobi/qmd](https://github.com/tobi/qmd) — local BM25 + vector + LLM-rerank over Markdown) as its retrieval substrate. It is *not* in the minimum stack — add it when corpus size makes keyword search insufficient. It is distinct from the human-side **Smart Connections** plugin (see [glossary: qmd](../glossary.md#computational-methods) and [obsidian-plugins/recommended/smart-connections.md](../../explanation/obsidian-plugins/smart-connections.md)).

## Use pre-built skills, don't roll your own

Pre-built skills cover most of the enrichment and ingest work; the agent should use them rather than writing API clients from scratch.

### K-Dense scientific-agent-skills

| Skill | Purpose |
| --- | --- |
| `paper-lookup` | Unified search across 10 databases (PubMed, PMC, bioRxiv, medRxiv, arXiv, OpenAlex, Crossref, Semantic Scholar, CORE, Unpaywall). Includes OpenAlex DOI/ORCID/ROR batch lookups, citation graph traversal, OA PDF discovery, and bibliometrics. |
| `pyzotero` | Read/write Zotero — including writing stable IDs back to the `Extra` field after enrichment. |
| `citation-management` | Crossref DOI resolution and reference normalization. |

### Obsidian skills

Hermes-side skills that operate inside the vault via the Obsidian Local REST API:

- `obsidian-paper-note` — full ingest pipeline (Zotero → PDF → Markdown → vault note).
- Vault read/write skills for note creation, frontmatter updates, and link maintenance.

### Hermes built-in skills

- `llm-wiki` — the umbrella ingest/enrich/classify/draft/lint skill bundle for vault operations. Invoked in a Librarian session — `hermes -p memoria-librarian chat -s llm-wiki`, then `/llm-wiki ingest --source {citekey}` — or card-dispatched by the board.

### REST passthrough — the escape hatch

A single reusable Hermes skill that wraps any REST endpoint. Used when an API matters once or twice but doesn't justify a dedicated skill yet. Lane-gated to the Librarian lane only via the policy MCP (see [profiles/README.md](../../explanation/profiles/README.md#lane-override-files)).

| Aspect | Value |
| --- | --- |
| Skill name | `rest-passthrough` |
| Inputs | `{base_url, path, method, headers, query, body, timeout, bearer_env}` |
| Output shape | `{ok: bool, status: int, summary: str, data: any, error?: str}` |
| Lane access | Librarian only |
| Network policy | `external_api_policy: explicit_only` — must be invoked with explicit URL, not via prompt-driven URL synthesis |
| Auth | Reads bearer tokens from environment variables; no secrets in the skill itself |

The rule: if the same endpoint is called repeatedly through the passthrough, that's the signal to promote it to a dedicated skill (a `<service>-fetch` skill with a narrower contract). The passthrough is for the long tail; dedicated skills are for the head.

## Model routing: synthesis on Claude, cheap tasks elsewhere

Not every model call needs the most capable model. The rule:

| Task class | Examples | Recommended model | Why |
| --- | --- | --- | --- |
| **Synthesis / writing** | `draft`, claim-note generation, reference page compilation | Claude (the primary synthesis model) | Quality matters most; cost is justified by the irreducibly judgment-laden nature of the work. |
| **Verify / similarity / claim trace** | `cite-check`, `claim-trace`, `similarity-check`, `find-duplicates`, `retraction-check` | Claude (smaller variant acceptable) or cheap model with strong retrieval | Decisions are mostly mechanical; precision matters more than depth. |
| **Code generation** | Coder profile work, delegated to Kilocode / Aider / Claude Code | Claude or Codex via the external coding agent | Best handled by the dedicated coding tool's chosen model, not by Hermes directly. |
| **Bulk / mechanical** | Embedding for `qmd` hybrid search, classification of `_proposed_classification` fields, short summaries during enrichment | Cheap model via OpenRouter or similar (e.g., `gemini-flash`, `llama-3.1-8b`) | High volume, low judgment; cost dominates and small models are accurate enough. |

The model selection is configured in each profile's `config.yaml` — not at the workflow layer. The lane-override declares *what skills the profile may run*; the profile's config decides *which model* runs them. This keeps cost discipline operational rather than aspirational:

- The discovery loop's `$1–3/day` budget (see [roadmap/future-directions.md](../../project/roadmap/future-directions.md)) is achievable *because* embed and classify calls go to a cheap model; routing everything through Claude would push the budget several times higher.
- Cost regressions surface in the [fleet-health dashboard](../../explanation/dashboards/fleet-health.md) at the per-skill level — if `paper-lookup` cost-per-task triples, the routing config drifted (or a cheap model was retired and the call now silently falls back to Claude).

OpenRouter and similar gateways (Kilopass, OpenAI's own model fan-out) are the practical access path to cheap models — they expose a single API surface with many backend models, so the profile config picks the model name rather than negotiating credentials per provider.

## Plugins, apps, and external tools

These are not skills — they are the surrounding ecosystem the agent integrates with.

| Tool | Role |
| --- | --- |
| **Scite** | Citation context (supporting / contrasting / mentioning signals). |
| **Marker** | PDF full-text extraction (no GROBID needed for this workflow). |
| **MarkItDown** | Fallback extractor for non-PDF sources. |
| **MarkDB-Connect** | Zotero add-on — tags Zotero items that have vault notes (runs in Zotero, not under `.obsidian/plugins/`). |
| **qmd** | Hybrid BM25 + vector search over the vault. |
| **Obsidian Local REST API** | Obsidian plugin — exposes the vault to Hermes for read/write. **Distinct from ACP**: REST API is *vault-level* read/write; ACP is *editor-level* agent interface. Complementary — REST API gives Hermes vault access; ACP exposes Hermes to Obsidian / VS Code / Zed agent panes. |
| **Claude API** | The primary synthesis model. |
| **Kilocode or Aider** | Repository-level coding work delegated by the Coder profile. |

## Related

- Obsidian plugins (detailed per-plugin configuration): [obsidian-plugins/README.md](../plugins/README.md)
- Per-profile skill catalogs: [profiles/README.md](../../explanation/profiles/README.md)
- Lane-override mechanism: [profiles/README.md lane-override files](../../explanation/profiles/README.md#lane-override-files)
- Cost-discipline dashboard: [dashboards/fleet-health.md](../../explanation/dashboards/fleet-health.md)
