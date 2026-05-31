---
topic: decisions
id: 12
title: obsidian-linter is reference-only, not a control-plane formatter
status: accepted
date_proposed: 2026-05-29
date_resolved: 2026-05-29
supersedes: []
superseded_by: []
---

# ADR-12: obsidian-linter is reference-only, not a control-plane formatter

## Context

The Obsidian Linter (platers/obsidian-linter) is a deterministic, on-save Markdown formatter — superficially aligned with Memoria's "bookkeeping, not intelligence" thesis, and previously carried in the `recommended/` plugin set with a carefully de-fanged config (agent/canonical folders excluded, frontmatter timestamp/insert/remove rules off, schema-aligned key sort, no HTML-comment rules). The question is whether a vault that already runs the **Memoria Linter** (deterministic structural validation under the Policy MCP, with an audit trail) and **markdownlint** (Markdown hygiene) should also ship a third formatter. Two prior commitments frame it: the Policy MCP makes every canonical write audited and hash-chained, and frontmatter has a single declared authority ([frontmatter.md](../../docs/reference/frontmatter.md)).

## Decision

Memoria treats obsidian-linter as **reference-only**: documented for the record, **not installed and not recommended**. It must never act as a **control-plane formatter** — it never writes to Policy-MCP-audited zones, and it is never the authority for frontmatter or schema. The formatting concerns it would cover are owned elsewhere: the **Memoria Linter** owns frontmatter/schema validation and structural drift; **markdownlint** owns Markdown hygiene. The plugin's safe-config knowledge (folder exclusion, frontmatter rules off, the HTML-comment footgun) is preserved in [obsidian-linter.md](../rejected/obsidian-linter.md) in case a human chooses to run it anyway or the decision is revisited.

## Consequences

- One fewer formatter to install, configure, keep in sync with the schema, and re-audit on every upgrade (the HTML-comment-strip risk that would silently delete `_proposed_classification` / `_enrichment` blocks).
- No second frontmatter authority — the single-source-of-truth invariant for frontmatter is preserved by construction.
- The human loses on-save whitespace / key-sort tidiness on hand-written draft folders. This is the cost; it is judged marginal against markdownlint + the Memoria Linter already covering hygiene and structure.
- Moves obsidian-linter from `recommended/` (11 → 10) to `reference/` (3 → 4); the prior config doc is reframed as held knowledge.
- Reversible: the reference doc records the exact constraints under which it *could* be re-adopted (human-surface folders only, frontmatter rules off, never the control plane).

## Alternatives considered

**Keep it recommended, de-fanged (the prior state).** Rejected: even correctly scoped to human-only folders with frontmatter rules off, it duplicates work the Memoria Linter and markdownlint already own, and adds a standing upgrade-audit burden (diff the rule registry for HTML-comment rules every release) for marginal whitespace / key-sort value. The risk/benefit doesn't justify a place in the install set.

**Have the Memoria Linter profile *use* obsidian-linter.** Rejected on runtime grounds: obsidian-linter is TypeScript-in-Obsidian with no standalone CLI; the headless Linter profile can't call it as a library, and the deterministic formatting it needs it already performs directly (regex / markdownlint-class checks) under the audit trail.

**Remove it entirely (no doc).** Rejected: the de-fanged-config and HTML-comment-footgun knowledge is hard-won and worth keeping; `reference/` is exactly the "held, not installed" shelf for it.

## Related

- **Files affected:** [obsidian-linter.md](../rejected/obsidian-linter.md) (moved from `recommended/` to `rejected/`), [plugins.md](../../docs/reference/plugins.md) (recommended 11→10, reference 3→4).
- **Profiles affected:** the [Linter](../../docs/explanation/profiles/linter.md) — owns the formatting/validation concern obsidian-linter would otherwise touch.
- **Related decisions:** the frontmatter namespace discipline this protects ([frontmatter.md](../../docs/reference/frontmatter.md)).
- **Source discussion:** the control-plane-authority analysis — a deterministic tool still fails the architecture if it writes outside the Policy MCP / audit trail.
