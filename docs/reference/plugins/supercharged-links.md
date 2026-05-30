---
topic: plugins
---

# supercharged-links + obsidian-style-settings

Used together. Supercharged Links reads frontmatter and applies CSS classes; Style Settings configures the colors. Memoria ships a snippet that distinguishes:

- Paper notes (`20-sources/`) — neutral accent.
- Claim notes (`30-synthesis/01-claims/`) — primary accent.
- Reference notes (`30-synthesis/02-reference/`) — secondary accent, denoting canonical status.
- MOCs (`30-synthesis/03-moc/`) — italic + accent.
- Workbench drafts (`40-workbench/*/04-drafts/`) — muted.

Load-bearing settings:

- `targetTags` or `targetAttributes` — must include the `type` frontmatter field (Memoria's standard type discriminator). If it points at something else (e.g., a tag), the styling won't apply to agent-created notes whose `type` is set but tags aren't.
- The CSS snippet itself ships at `.obsidian/snippets/memoria-link-colors.css` in the starter vault — installed as-is when the human clones the vault. Enable it under Settings → Appearance → CSS snippets. The snippet uses Style Settings' `@settings` block to expose all five lifecycle-folder colors as human-tunable variables.
