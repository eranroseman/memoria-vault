---
topic: plugins
---

# hover-editor

Recommended. In a citation-heavy draft, a paragraph with 8 wikilinks (`[[mamykina2010sense]]`, `[[veinot2018good]]`, `[[chen2021pipeline]]`, etc.) becomes a chore to verify when each link requires opening a new pane. Hover Editor lets the human hover over any wikilink and see the linked note in a popup, dismissed by moving the cursor away. The drafting flow becomes: write a citation, hover-check that the linked claim note really says what's being cited, continue writing.

> **Verify setting keys against your installed version.** The key names below are illustrative and unvalidated against an installed build. Note in particular that the **hover trigger delay is a core *Page Preview* setting**, not a Hover Editor one — Hover Editor depends on core Page Preview. Confirm the real keys before relying on them.

Load-bearing settings:

- `popoverHoverParent: "workspace-leaf"` — pin the popover to the workspace, not to the cursor. Cursor-anchored popovers move when scrolling, which is disorienting in a long draft.
- `triggerDelay` (core Page Preview) — set to ~200ms. Lower than that and accidental hovers create flashing popovers; higher and the verification flow feels slow.
- The plugin also enables editable popovers — Memoria's discipline is **read-only popovers**: hover to verify, click to open in a real pane to edit. Set `editableInPopover: false` if the version exposes it.
