---
topic: plugins
---

# obsidian-linter — evaluated, not in the install set

The Obsidian Linter is a frontend Markdown formatter — **not** the Memoria Linter (a different thing: the Memoria Linter does deterministic structural validation under the policy MCP; the Obsidian Linter does inline formatting on save inside the GUI). **Memoria is incompatible with it — do not install it** (see [ADR-12](../decisions/12-obsidian-linter-reference-only.md), hardened 2026-05-31). This page is kept as the record of *why*, and of the configuration that was once proposed; it is **not** a how-to for running the plugin.

**Why it's incompatible (ADR-12).** It is a *second formatter with its own config* doing work the Memoria Linter and `markdownlint` already own, and its writes land in the GUI, outside the policy MCP audit trail. Decisively: `_proposed_classification` and `_enrichment` are **YAML frontmatter namespaces the Librarian writes on every ingest** — so the plugin's frontmatter rules (key-sort, timestamp, attribute insert/remove) would continuously fight the agent for control of frontmatter, corrupting the agent-owned namespaces and destroying the human-vs-agent edit signal the dashboards rely on. The Memoria Linter owns frontmatter/schema authority; `markdownlint` owns Markdown hygiene.

**Why "just exclude the folders" doesn't rescue it.** The plugin has no per-folder rules — `foldersToIgnore` whole-folder exclusion is the only knob. But `40-workbench/` drafts are *both* human-edited (so you'd want formatting) *and* agent-written (so formatting corrupts state); no single exclusion list satisfies both. Whole-folder exclusion can keep it off canonical zones but cannot make it safe on the one folder where on-save tidiness would actually help.

**Historical config (for the record, not for use).** The constraints once proposed under the milder "reference-only" ruling were: exclude every agent-managed folder via `foldersToIgnore`; `yaml-timestamp` / `insert-yaml-attributes` / `remove-yaml-keys` off; `auto-correct-common-misspellings` off (it mangles domain terms, e.g. `JITAI`); and never enable any rule that rewrites or strips note content the agent owns. These are retained to explain the evaluation, not to enable a "careful" install — the current verdict is that no config makes the plugin compatible.
