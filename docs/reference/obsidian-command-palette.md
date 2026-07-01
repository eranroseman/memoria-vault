---
title: Obsidian command palette
parent: Agents and control
grand_parent: Reference
---

# Obsidian command palette

The `Memoria:` command-palette surface is deliberately small in alpha.11.
QuickAdd handles direct PI conveniences; the `memoria` CLI owns worker actions
for capture, checks, rollback, and source processing. The command palette is not
the canonical worker API.

---

## Commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture note` | Opens the `memoria-note-capture` Modal Forms form and writes one unchecked `note` Concept to `knowledge/notes/`. The worker/check loop owns later eligibility. | QuickAdd Macro -> `vault-template/system/scripts/capture-note.js` |
| `Memoria: open Inbox` | Opens `spaces/inbox.md` in the active pane without mutating the active note. | QuickAdd Macro -> `vault-template/system/scripts/open-inbox.js` |
| `Memoria: record exploration trace` | Captures a rejected direction/dead end beside an active or selected map/gap report under `knowledge/notes/maps/` as an unchecked `note`. | QuickAdd Macro -> `vault-template/system/scripts/record-exploration-trace.js` |
| `Memoria: resolve inbox card` | Resolves the active alpha.11 attention projection under `inbox/` by setting `attention_status: resolved` and appending attention/triage telemetry rows. | QuickAdd Macro -> `vault-template/system/scripts/resolve-inbox-card.js` |
| `Memoria: dismiss inbox card` | Same resolver with `Outcome: Dismiss`, then returns the pane to the Inbox when possible. | QuickAdd Macro -> `vault-template/system/scripts/resolve-inbox-card.js` |

The startup macro `Memoria: restore shell on startup` is not command-palette
visible. It lets Obsidian restore the previous session first, then loads the
saved Memoria shell only when the pinned rail is missing.

---

## Related

- The read-only Inspector boundary: [Obsidian plugin settings](obsidian-plugin-settings.md)
- The generated forms: [Frontmatter fields](frontmatter.md)
- Current Concept types: [Document types](document-types.md)
