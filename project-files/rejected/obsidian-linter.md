---
topic: plugins
---

# obsidian-linter — evaluated, not in the install set

The Obsidian Linter is a frontend Markdown formatter — **not** the Memoria Linter (a different thing: the Memoria Linter does deterministic structural validation under the policy MCP; the Obsidian Linter does inline formatting on save inside the GUI). Memoria **does not ship or recommend it** — see [ADR-12](../decisions/12-obsidian-linter-reference-only.md). Held here because the safe-config knowledge is worth keeping if a human chooses to run it anyway, or if the decision is ever revisited.

**Why it's held out (ADR-12).** Even fully de-fanged, it is a *second formatter with its own config* doing work the Memoria Linter and `markdownlint` already own — and its writes land in the GUI, outside the policy MCP audit trail. The marginal value (whitespace + frontmatter key-sort on human-draft folders) doesn't justify the maintenance and per-upgrade audit burden (see the HTML-comment footgun below). The Memoria Linter owns frontmatter/schema authority; `markdownlint` owns Markdown hygiene.

**If a human runs it anyway, these constraints are non-negotiable** — they are what keep it from acting as a control-plane formatter:

- `foldersToIgnore` must **exclude every agent-managed / canonical folder** (`00-meta`, `10-inbox`, `20-sources`, `30-synthesis`, `40-workbench`, `50-deliverables`, `90-assets`, `95-archive`). The Linter has no per-folder rules; whole-folder exclusion is the only knob, so it must touch *only* content the agent never writes.
- `yaml-timestamp`, `insert-yaml-attributes`, `remove-yaml-keys` **off** — frontmatter is Memoria's authority; the agent's frequent writes would fight timestamp/field rules and destroy the human-vs-agent edit signal the dashboards rely on.
- `auto-correct-common-misspellings` **off** — it mangles domain terms (e.g., `JITAI` → `Just-In-Time-AI`).
- **Never enable any HTML-comment-stripping rule.** `_proposed_classification` / `_enrichment` blocks live as `<!-- ... -->` inside notes; a comment-removal rule deletes every one on the next pass, with no undo. As of `v1.31.2` no such rule ships — this is forward-looking discipline: before accepting any upgrade, diff the rule registry for new rules mentioning "html", "comment", or "strip".

Keep any on-save set minimal and mechanical (`trailing-spaces`, `remove-multiple-spaces`, `yaml-trailing-newline`, schema-aligned `yaml-key-sort`); everything content-changing belongs to manual invocation only. Even so, Memoria's position is that this work belongs to the Memoria Linter and `markdownlint`, not to a GUI formatter — hence reference, not recommended.
