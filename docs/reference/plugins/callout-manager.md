---
topic: plugins
---

# callout-manager

Defines the three Memoria-specific callout types used by the [inline agent callouts](../../explanation/obsidian-ui/callouts.md):

- `[!brief]` — Mapper's comparative read on a new paper note.
- `[!suggestions]` — Librarian's link candidates pending human approval.
- `[!verification]` — Verifier's claim trace on a draft.

Load-bearing settings: ship the callout definitions in `vault/.obsidian/plugins/callout-manager/data.json`. The definitions encode the icon, color, and default-collapsed state for each type. Without Callout Manager (or equivalent CSS snippets), these render as plain blockquotes — readable, but the visual affordance that says "this is agent output, not the human's writing" is gone.

It is **Required** because the agent-output affordance depends on it — but its Memoria config is not yet authored, so until then the callouts fall back to default styling (they do not fail). "Required" names the plugin, not a shipped config.

**Template status:** the shipped placeholder is `.obsidian/plugins/callout-manager/data.json.TODO` in the starter vault — a placeholder, not a working file. The plugin's `data.json` schema hasn't been verified against an installed version yet. The TODO file documents what the three callouts should encode (icon, color suggestion, default-collapsed flag) and the next step: install Callout Manager into the Memoria vault, configure the three callouts through its UI, and rename the resulting `data.json` next to the TODO placeholder.
