---
topic: decisions
id: 12
title: obsidian-linter is reference-only, not a control-plane formatter
status: accepted
date_proposed: 2026-05-29
date_resolved: 2026-05-29
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 12
---

# ADR-12: obsidian-linter is reference-only, not a control-plane formatter

> **Update (2026-05-31): hardened to incompatible — do not install.** The original decision held obsidian-linter at "reference-only," documenting a de-fanged config for anyone who chose to run it anyway. The current verdict is stronger: **obsidian-linter cannot be used together with Memoria.** Two reinforcing reasons: (1) the [classification-storage decision](../reference/frontmatter.md) confirmed `_proposed_classification` / `_enrichment` are **YAML frontmatter namespaces the agent writes constantly** — so obsidian-linter's frontmatter rules (key-sort, timestamp, attribute insert/remove) are no longer a corner-case footgun but a guaranteed, continuous collision with a second frontmatter authority; and (2) whole-folder exclusion can't protect `40-workbench/` drafts, which are *both* human-edited and agent-written. The "run it carefully" path is withdrawn. The Decision/Consequences below are retained as the record of the original, milder ruling; where they say "not installed and not recommended," read "not compatible — do not install." The held config is preserved under *Held configuration (historical)* below — kept as the record of what was once proposed, not as a how-to.

## Context

The Obsidian Linter (platers/obsidian-linter) is a deterministic, on-save Markdown formatter — superficially aligned with Memoria's "bookkeeping, not intelligence" thesis, and previously carried in the `recommended/` plugin set with a carefully de-fanged config (agent/canonical folders excluded, frontmatter timestamp/insert/remove rules off, schema-aligned key sort, no HTML-comment rules). The question is whether a vault that already runs the **Memoria Linter** (deterministic structural validation under the Policy MCP, with an audit trail) and **markdownlint** (Markdown hygiene) should also ship a third formatter. Two prior commitments frame it: the Policy MCP makes every canonical write audited and hash-chained, and frontmatter has a single declared authority ([Frontmatter fields](../reference/frontmatter.md)).

## Decision

Memoria treats obsidian-linter as **incompatible — do not install**: documented for the record only. (This is the hardened ruling per the Update banner above; it strengthens the original "reference-only … not installed and not recommended" verdict — no config makes the plugin safe to run alongside Memoria.) It must never act as a **control-plane formatter** — it never writes to Policy-MCP-audited zones, and it is never the authority for frontmatter or schema. The formatting concerns it would cover are owned elsewhere: the **Memoria Linter** owns frontmatter/schema validation and structural drift; **markdownlint** owns Markdown hygiene. The plugin's safe-config knowledge (folder exclusion, frontmatter rules off, the HTML-comment footgun) is preserved under *Held configuration (historical)* below in case a human chooses to run it anyway or the decision is revisited.

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

## Held configuration (historical, not a how-to)

This records what was once proposed under the milder "reference-only" ruling, and why even a careful config does not rescue the plugin. The current verdict (the Update banner above) is that **no config makes it compatible** — this section is the evaluation record, not an enable path.

The constraints once proposed were: exclude every agent-managed folder via `foldersToIgnore`; `yaml-timestamp` / `insert-yaml-attributes` / `remove-yaml-keys` **off** (they fight the Librarian for the `_proposed_classification` / `_enrichment` frontmatter namespaces it writes on every ingest); `auto-correct-common-misspellings` **off** (it mangles domain terms, e.g. `JITAI`); and never enable any rule that rewrites or strips note content the agent owns.

**Why "just exclude the folders" doesn't rescue it.** The plugin has no per-folder rules — whole-folder `foldersToIgnore` exclusion is the only knob. But `40-workbench/` drafts are *both* human-edited (so you'd want on-save tidiness) *and* agent-written (so formatting corrupts state); no single exclusion list satisfies both. Whole-folder exclusion can keep the plugin off canonical zones but cannot make it safe on the one folder where on-save tidiness would actually help.

## Related

- **Files affected:** the `recommended/`→`reference/` reframing of the prior plugin doc (recommended 11→10, reference 3→4) is recorded in [Obsidian plugins](../reference/obsidian-plugins.md); the held config it carried is folded into this ADR (above).
- **Profiles affected:** the [Linter](../explanation/profiles/linter.md) — owns the formatting/validation concern obsidian-linter would otherwise touch.
- **Related decisions:** the frontmatter namespace discipline this protects ([Frontmatter fields](../reference/frontmatter.md)).
- **Source discussion:** the control-plane-authority analysis — a deterministic tool still fails the architecture if it writes outside the Policy MCP / audit trail.
