# Portals (folder-navigation chrome) — clean-slate design

> **Status:** clean-slate proposal (scratch, `tmp/`). Consolidates the Portals
> material scattered across `ui-architecture-alpha7.md` §5 (#667) / §9 (risk gate) /
> §10 (plugin set) into one first-principles design. Sibling of `workspaces-design.md`
> (gates) — together they specify the persistent shell.
>
> **Live-verified** against Portals **1.4.1** in the `Memoria-test` sandbox (Obsidian
> 1.12.7): plugin schema, side-panel modules, `replaceFileExplorer`,
> `tagNotesFolderPath`, no public API, cannot pin notes.

---

## 0. The reframe in one paragraph

Portals is **navigation chrome and nothing else** — it makes the left sidebar a
legible way to *reach* a folder, replacing the raw type-first file tree that #667
calls "unintuitive." It is **not** a classification system (that is frontmatter), it
is **not** the gate switcher (that is the dashboard nav row — Portals provably can't
pin notes), and it is **not** a content/query layer (that is Bases). Get those three
boundaries right and Portals earns its place as one thin, gated nav layer; blur them
and it becomes a fourth bundled plugin pretending to be a taxonomy.

---

## 1. Framing — we classify by frontmatter, so Portals is folder-only

Memoria classifies by **typed frontmatter properties** (`type`, `lifecycle`,
`maturity`, `topics`, `research_area`, `links:`), not `#tags` — because the system is
machine-curated and needs validated, multi-axis, queryable, relation-bearing metadata
that a flat tag namespace can't give (forms→frontmatter, Linter-on-frontmatter,
Bases-over-frontmatter, `links:` edges). Full pros/cons of tags vs frontmatter is the
upstream decision; the consequence for *this* design is direct:

- **Portals pins folders and tags. We have a folder structure and no tag taxonomy.**
  So **tag-portals are dead weight** and Portals' auto-created `_Tag Notes` folder is
  pure overhead.
- **Property/semantic navigation (`topics`, `research_area`) is not folder-shaped**, so
  Portals fundamentally **cannot** express it — that navigation stays in Bases. Portals
  helps *folder* reach only.

**Design consequence:** folder portals only; no tag-portals; relocate/suppress
`_Tag Notes`; never treat Portals as a classification or property-navigation surface.

---

## 2. Requirements (first principles)

- **N1 — Make the user-facing collections reachable and legible.** The direct fix for
  #667: a curated, icon-led sidebar over the handful of collections the PI actually
  works in, instead of the raw type-first tree.
- **N2 — Hide infrastructure.** `system/` and `.memoria` disappear from the explorer
  (the clean answer to #663 "is `system/` user-facing?").
- **N3 — Ship in the vault, reproducible.** The whole config is a vendored
  `data.json` under the golden copy (ADR-55) — not per-device UI state.
- **N4 — Stay in its lane.** Portals must not duplicate or absorb the other two
  layers (gate switching, content query) — see §5.
- **N5 — Minimum surface, no dead features.** No tag-portals (no taxonomy), no stray
  `_Tag Notes` folder, only the side-panel modules that earn their place.
- **N6 — Gated adoption.** It replaces a *core* Obsidian surface, so it ships only
  behind ADR-74 provenance with the core explorer retained as fallback (§7).

---

## 3. What Portals is / isn't (verified 1.4.1)

**Is:** a left-sidebar navigator that pins **folders/tags as tabs** (icons, colors,
collapsible *stacks*), can **replace the core file explorer**, and carries a Side
Panel with modules: `recent · context-notes · bookmarks · journal · hidden ·
properties · trash` (verified `splitViewTabs`). Folder portals and side modules are
**command-bindable** (`portals:open-portal-1…10`, `portals:open-side-*`), so folder
navigation can be keyboard-driven / put on the Commander ribbon.

**Isn't / can't (verified):**
- **No public API** (`plugin.api` undefined; only a `cleanupDeadSpaces` method).
- **Cannot pin a note as a tab** — "spaces" are folder/tag entries
  (`portalType: "folder"|"tag"`, `folderPath`/`tagPath`, `iconName`), not notes. So
  **Portals is not the gate switcher** (that's the dashboard nav row,
  `workspaces-design.md` §8).
- **Doesn't touch Bases/Dataview/search** — it navigates, it doesn't query or modify
  content.

---

## 4. The design

**Replace the raw file-explorer tab with a Portals navigator** (`replaceFileExplorer:
true`), keeping the core `file-explorer` plugin **enabled** as fallback (§7).

- **Folder portals — the user-facing collections only**, each with a type icon:
  `inbox`, `catalog`, `notes/sources`, `notes/claims`, `notes/hubs`, `projects`.
  These are the gates' content homes; the order mirrors the gate order
  (Inbox · Library · Knowledge · Project).
- **Hide infrastructure:** route `system/` and `.memoria` to the **Hidden** module
  (`hiddenItems`) — N2 / #663.
- **No tag-portals** (N5 / §1) — we maintain no tag taxonomy.
- **Relocate the tag-notes folder:** set `tagNotesFolderPath` out of the user
  namespace (e.g. `system/_tag-notes`) or leave it Hidden — verified configurable, so
  the §8 folder-hygiene flag is resolved by config, not a stray root folder.
- **Side-panel modules — keep only what earns it:** `recent`, `bookmarks`,
  `context-notes` (lightweight folder-level orientation), `trash` (pairs with
  `trashOption: local`, §10). **Drop `journal`** (no daily-notes workflow — capture is
  form-based `fleeting`) and **`properties`** is redundant with the Bases/badge tier.
- **Stacks** can group the collections if the list grows; not needed at six entries.

---

## 5. The three orthogonal layers (the boundary that keeps Portals honest)

The persistent shell has exactly three navigation/query layers, and each does one job:

| Layer | Job — "how do I…" | Mechanism | Keyed on |
|---|---|---|---|
| **Portals** | *reach* a folder/note in the sidebar | folder portals | folder path |
| **Gate dashboards** | *switch the mode* I'm working in | dashboard note + nav row | the job (Inbox/Library/Knowledge/Project) |
| **Bases** | *see/query* a collection's contents | `.base` views | frontmatter properties |

They are orthogonal and must not bleed: Portals never classifies (that's frontmatter),
never switches gates (it can't pin notes), never queries (that's Bases). This is the
same discipline `workspaces-design.md` applied to "gate vs dashboard vs workspace."

---

## 6. Shippable config (`data.json` sketch)

Vendored under the golden copy + `plugin-provenance-lock.json` (sha256). The `spaces[]`
shape is **verified** (§8) — a folder portal is exactly
`{ portalType, folderPath, iconName }`, persisted unchanged across a plugin reload:

```jsonc
{
  "replaceFileExplorer": true,        // adopt as the explorer; core file-explorer stays enabled (fallback)
  "spaces": [
    { "portalType": "folder", "folderPath": "inbox",         "iconName": "inbox" },
    { "portalType": "folder", "folderPath": "catalog",       "iconName": "library" },
    { "portalType": "folder", "folderPath": "notes/sources", "iconName": "book-open" },
    { "portalType": "folder", "folderPath": "notes/claims",  "iconName": "git-branch" },
    { "portalType": "folder", "folderPath": "notes/hubs",    "iconName": "network" },
    { "portalType": "folder", "folderPath": "projects",      "iconName": "target" }
  ],
  "hiddenItems": { "system": true, ".memoria": true },        // N2 / #663
  "tagNotesFolderPath": "system/_tag-notes",                  // keep the auto-folder out of the user namespace
  "splitViewTabs": ["recent", "bookmarks", "context-notes", "trash"],  // drop journal + properties
  "enableContextNotes": true,
  "pinVaultRoot": false,
  "tabNameDisplay": "activeOnly"
}
```

---

## 7. Adoption gate (carried from §9)

Portals **replaces a core surface**, so it is adopted **gated, not freely**:

- **ADR-74 provenance** — it is a bundled community plugin (vendored files + sha256);
  if it breaks on an Obsidian upgrade, *navigation* breaks, so it rides the version
  smoke-test.
- **Core `file-explorer` stays enabled** — adopt via Portals' own
  `replaceFileExplorer: true`, never by disabling the core plugin (which would break
  reveal-in-explorer, context menus, drag-and-drop, and Portals' own integration).
- **Agent-unverifiable fraction** — installing/inspecting Portals needed explicit human
  authorization (untrusted-code policy). Shippability itself is **confirmed** (config
  vendors to `data.json`); behavior on upgrade is the standing human-gated risk.

---

## 8. Verified vs verify-before-build

**Pinned ✅ (Portals 1.4.1, Memoria-test):**
- Settings vendor to `data.json` → **shippable**.
- Side-panel modules = `recent/context-notes/bookmarks/journal/hidden/properties/trash`.
- `replaceFileExplorer` and `tagNotesFolderPath` are real, settable keys → the
  `_Tag Notes` hygiene item is **resolved by config**.
- No API; cannot pin notes → **Portals is not the gate switcher** (settles the old
  "one switcher" question).
- **`spaces[]` shape verified** — a folder portal is exactly
  `{ portalType:"folder", folderPath, iconName }`; written, `saveSettings()`,
  plugin-reloaded, and read back **unchanged** (no injected `id`/`name`), folder
  validated (not culled as dead), portal view opened. Optional `name`/`color` exist in
  the bundle but are **not required**. (Tag form is `{ portalType:"tag", tagPath, … }`
  — unused here.) The candidate space was written then **restored** to the original
  empty config.
- **Folder portals + side modules are command-bindable** (`portals:open-portal-1…10`,
  `portals:open-side-*`) → keyboard/ribbon navigation is available.

**Verify-before-build ⚠ (minor, config-shape only):**
- **`hiddenItems` shape** — confirm it keys folders as sketched (`{path: true}` vs an
  array) by hiding `system/` once in the UI and reading it back.
- **Icon names** — confirm each `iconName` against Obsidian's Lucide icon ids (the
  shape is proven; the specific ids are cosmetic).

---

## 9. ADR impact & requirements traceability

**ADR impact.** Folds into the same ADR as the gates work (amending ADR-68 /
consistent with ADR-70): Portals is the **navigation layer of the persistent shell**.
It also touches **ADR-74** (a bundled core-surface plugin → provenance) and is the
concrete answer to issues **#667** (navigation) and **#663** (`system/` visibility).
Per the ADR-only model, record it there before build.

**Traceability.**

| Req | Satisfied by |
|---|---|
| N1 reach collections | §4 folder portals over the six user collections, icon-led |
| N2 hide infrastructure | `hiddenItems` routes `system/` + `.memoria` to Hidden |
| N3 ship-in-vault | vendored `data.json` (§6) + provenance lock |
| N4 stay in lane | §5 three-orthogonal-layers boundary |
| N5 min surface | folder-portals only, no tag-portals, `_Tag Notes` relocated, trimmed modules |
| N6 gated adoption | §7 ADR-74 + `replaceFileExplorer` with core-explorer fallback |
