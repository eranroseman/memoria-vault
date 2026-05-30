---
topic: plugins
---

# obsidian-homepage — startup front door

[obsidian-homepage](https://github.com/mirnovov/obsidian-homepage) opens a chosen note on launch instead of Obsidian's default "reopen last session." Memoria uses it to open the [`Home.md` front door](../../explanation/obsidian-ui/home.md) every session (see [ADR-25](../../project/decisions/25-homepage-front-door.md)). It is **view-management only — it opens a view and writes no note content**, so unlike a formatter it never touches the policy MCP / audit trail. `recommended/`, not required: without it, pin `Home.md` manually.

**Authoritative config:** shipped at `.obsidian/plugins/homepage/data.json` in the starter vault.

**Load-bearing settings:**

- Target → the vault-root `Home.md` note (the front door).
- `openOnStartup: true` — the deterministic-landing behavior that is the point.
- `view` / open mode → **reading** or live preview (Home is a Dataview note; reading mode renders the queries).
- `revertView` (and the "open on empty pane" behavior) → keep Home from hijacking ordinary navigation; it opens on launch and on the "home" command/ribbon, not on every empty pane unless the human wants that. *(Verify the exact key names against the installed plugin — `openWhenEmpty` is illustrative; the real keys are `revertView` / `openMode` / `manualOpenMode` / `alwaysApply`.)*
- `commands` (optional) → run **"Dataview: Force refresh all views"** on open so the front door is current.
- **Per-device:** use the separate-mobile setting if mobile should land somewhere lighter than the desktop Home.

**What to commit.** `data.json` is configuration — commit it. If Home is ever opened as a *workspace* rather than a single note, the layout lives in `.obsidian/workspaces.json` (also commit). No secrets.

**Why it's safe.** It issues an open-view action, not a write. It cannot mutate canonical notes, so it raises none of the audit/authority concerns that put [obsidian-linter](../../project/evaluated-alternatives/obsidian-linter.md) in `reference/` ([ADR-24](../../project/decisions/24-obsidian-linter-reference-only.md)). Same test, opposite verdict.
