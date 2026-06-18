# Exec plan — v0.1.0-alpha.7

_Living build doc (alpha.7 `tmp/`). Tracks the **how**; the prose plan
([../release-plan-0.1.0-alpha.7.md](../release-plan-0.1.0-alpha.7.md)) holds the
**what**, and gate/stage **state** lives in the `Release v0.1.0-alpha.7` issue and its
sub-issues. Delete `tmp/` at cut — promote durable decisions to the UI ADR first._
Date opened: 2026-06-18.

## Scope (locked recommendation)

The **clean-slate UI**, verified-subset only. Source of truth = the four design docs
([`ui-architecture-alpha7.md`](ui-architecture-alpha7.md),
[`workspaces-design.md`](workspaces-design.md),
[`portals-design.md`](portals-design.md), deferred set in
[`ui-architecture-future.md`](ui-architecture-future.md)).

- **WS-0 — UI ADR** amending ADR-68 (gate set, dashboard-switching, Desk→Inbox). ADR-only
  decision model: accepted before build.
- **WS-1..6 — build**, mapping 1:1 to G1..G6 (table below).
- **Deferred** (future doc): projector engine, telemetry bases, Canvas/argument graph,
  edge-authoring relate-control. **Scope-reconcile:** the shadow/instrument harvest
  (#370/#611/#416/#371) the alpha.6 roadmap put in alpha.7 is **not** absorbed here —
  fold-in vs roll-to-alpha.8 is a PI call.

## Critical path & sequencing

- **Run two cheap, high-information checks on day 1 — they can move scope:**
  1. **`newLinkFormat: absolute` re-verification** (G1/S4). §7 verified nested-map
     backlink/orphan detection under *shortest-form* wikilinks; §10 ships
     `newLinkFormat: absolute`. If absolute form breaks nested-map backlink registration,
     the orphan / "Open questions" views (G1) and the `link-colors` prefix-keying (G5)
     are both affected. Re-test in the sandbox before locking G1 or G5.
  2. **`gen-forms.py` + drift-test exist?** (G2/Open-before-merge #6). The doc asserts
     the generator + pytest without citing the file. If absent, WS-2 is *build the
     generator*, not *align forms* — a materially bigger WS. Confirm at HEAD first.
- **Decide G6 empty-state before authoring dashboards** — seeded content vs per-surface
  copy shapes WS-3's dashboard text; it is a PI release decision, not a build task.
- **WS-3 (shell/gates) + WS-4 (Portals) are the net-new long poles, but de-risked:**
  base-embed + `#View` targeting, tab-reuse, and the Portals `spaces[]` schema are all
  **sandbox-verified** (workspaces §8 / portals §8). Residual work is authoring +
  vendoring, not discovery.
- **WS-5 (config/CSS) ships as its own PR** (per `ui-architecture-alpha7.md` §10) and is
  coupled to WS-1 only through `newLinkFormat`.
- Each WS lands as its own PR off its own branch/worktree (shared-checkout rule); never
  commit to `main`; runtime/Obsidian work is on the `~/Memoria-test` sandbox only, never
  `~/Memoria`.

## Workstreams

| WS | Gate | Closes | One-line deliverable | Stage proof | Status |
|---|---|---|---|---|---|
| WS-0 | (ADR) | — | UI ADR amending ADR-68 (gate set + switching + Inbox rename) | S0 | not started |
| WS-1 | G1 | #659,#665,#664 | §3 authored bases conform, `title`-led, backlink re-verified | S0+S1+S3+S4 | not started |
| WS-2 | G2 | — | six forms generated from schema + drift test | S0+S1+S5 | not started |
| WS-3 | G3 | #666 | four gate dashboards + nav-row shell; retire workspace-swap | S3+S5 | not started |
| WS-4 | G4 | #667,#663 | Portals folder nav, vendored + provenance-locked | S0+S3+S5 | not started |
| WS-5 | G5 | #668,#659 | `app.json` + core-plugin toggles + CSS snippets | S0+S2+S5 | not started |
| WS-6 | G6 | — | day-1 empty-state (seeded content / copy) | S5 | decision pending |

### WS-0 — UI ADR (amends ADR-68)

Record the settled design as an accepted ADR before build (ADR-only model). Captures:
gate set **Inbox/Library/Knowledge/Project** (Studio deferred); **dashboard-note
switching** in a persistent shell, retiring the workspace-swap mechanism; the
**Desk→Inbox rename** overriding ADR-68's explicit Inbox-rejection (rationale:
`workspaces-design.md` §9 — room metaphor broke; the collision is coherent). Mark ADR-68
amended; note ADR-70 consistency; record ADR-74 provenance for the added Portals plugin.
- **Do not rename `docs/adr/68-workspaces-desk-library-studio.md`** — 5 ADRs (70/77/69/13
  + README) cross-link that filename; the new ADR gets a fresh number/file and 68 gets a
  superseded/amended-by header.
- **Proof:** S0 (adr-index fresh, docs-doctor green).

### WS-1 — View layer (§3 bases) (#659, #665, #664)

The authored bases mostly **exist** (`inbox/inbox.base`, `catalog/catalog.base`,
`system/dashboards/{claims,sources,project-gate,patterns}.base`); this WS **aligns them
to the §3 spec**, it is not net-new.
- **Align each base** to its §3 views; **lead every `order:` with the `title` property**
  (not `file.name`) so collections read as titles (#659), and confirm the four
  `inbox.base` views are non-overlapping (#665 dedup holds by construction).
- **Hubs** = one folded view under `notes/hubs/`, not a dedicated base (avoid a base for
  a handful of files). Confirm whether a minimal `hubs.base` or a `claims.base` view.
- **`board.base`** — verify the existing mirror renders under the §2 spec (`as_of` sort).
- **Pin the home status-strip queries** (#664) — the one Dataview surface; reviews
  pending · blocked · HIGH/CRITICAL; clearer labels than "boards"/"finding".
- **MUST-VERIFY:** re-run the §7 nested-map backlink/orphan fixture **under
  `newLinkFormat: absolute`** (couples to WS-5). If it breaks, either keep shortest-form
  or materialize an `inbound_count` scalar (the §3 structural-rule-2 fallback).
- **Proof:** S0 (parse) + S1 (any base-spec unit) + S3 (render in Obsidian) + S4
  (backlink re-verify).

### WS-2 — Capture forms (§4)

- **Confirm `scripts/gen-forms.py` + the drift pytest exist** (verify-at-head). If not,
  building the generator is the bulk of this WS.
- Generator emits every enum/multiselect stanza of Modal Forms' `data.json` from
  `.memoria/schemas/types/*.yaml` + `system/vocabulary.md`; pytest fails on drift.
- Land the clean-slate deltas: `entity` → catalog note-picker; `sources` → citekey
  multiselect; `output_mode` → radio:2; `inquiry_*`/`finer_*` → assembled `map` kinds.
- Six forms total (`fleeting`/`source`/`claim`/`hub`/`project`/`thesis`); `source` is one
  schema behind three capture buttons (Zotero/URL/manual).
- **Proof:** S0/S1 (drift test) + S5 (each form drives through in Obsidian).

### WS-3 — Persistent shell & gates (#666)

The net-new shell. Replaces the ADR-68 workspace-swap with dashboard notes.
- **Author four gate dashboards** (drafts in [`dashboards/`](dashboards/)):
  `inbox`/`library`/`knowledge`/`project`, each embedding its §3 views via
  `![[base#View]]` (**verified** syntax) + a current-gate-bold **wikilink nav row** +
  empty-state copy (WS-6).
- **Retire the swap mechanism:** delete `src/system/scripts/load-workspace.js` + the 3
  QuickAdd workspace macros; remove the `## Workspaces` button block from
  `src/home.md`; **do not** bundle Workspaces Plus.
- **Repurpose existing dashboards:** `system/dashboards/desk.md`→ the Inbox dashboard;
  `studio.md` content (claims + project-gate + patterns) splits into the Knowledge and
  Project dashboards; `library.md` aligns.
- **One golden "Memoria" workspace** in `workspaces.json` as a *reset* layout only
  (`saveOnSwitch` off); keep the core Workspaces plugin enabled.
- **Homepage** opens the Inbox dashboard on launch; **Commander** carries the global
  actions (capture ×3, delegate, resolve) moved off `home.md` Buttons; gate hotkeys via
  four QuickAdd open-note choices are **optional** (the nav row is the baseline).
- **Verified:** `![[base#View]]` targeting + `openLinkText(target,'',false)` tab-reuse
  (workspaces §8).
- **Proof:** S3 (switch reuses tab; dashboards render) + S5 (drive all four gates).

### WS-4 — Portals navigation (#667, #663)

Adopt Portals as gated folder-nav chrome (`portals-design.md`).
- **Vendor a Portals `data.json`** (verified `spaces[]` shape
  `{portalType:"folder",folderPath,iconName}`): six folder portals
  (`inbox`/`catalog`/`notes/sources`/`notes/claims`/`notes/hubs`/`projects`);
  `replaceFileExplorer: true`; route `system/`+`.memoria` to **Hidden**; relocate
  `tagNotesFolderPath` → `system/_tag-notes`; trim `splitViewTabs` to
  `recent/bookmarks/context-notes/trash`; **no tag-portals**.
- **Keep the core `file-explorer` plugin enabled** (fallback) — adopt via Portals' own
  flag, never by disabling core.
- **Add Portals to `community-plugins.json` + `plugin-provenance-lock.json`** (vendored
  files + sha256). **Do not add Workspaces Plus.**
- **Verify-before-build (minor):** `hiddenItems` key shape (`{path:true}` vs array) and
  the Lucide `iconName` ids — both by a one-time UI-configure-then-read.
- **Proof:** S0 (provenance lock validates) + S3 (navigator renders, `system/` hidden) +
  S5 (navigate to collections).

### WS-5 — Obsidian config & CSS (#668, #659)

Functional changes to shipped `src/.obsidian/` — its own PR (`ui-architecture-alpha7.md`
§10).
- **`app.json`** (today `{}`): ship the nine Memoria-tuned settings — incl.
  `showInlineTitle:false` (#659) and `newLinkFormat:absolute` (**gated on WS-1's
  re-verification**).
- **Core plugins:** disable core `templates` (verify QuickAdd doesn't call it); keep
  `file-explorer` enabled; lean-disable `daily-notes`; keep `workspaces` (reset layout).
- **CSS (#668):** the snippets are already enabled in shipped `appearance.json`; the fix
  is **installer/golden-copy reconciliation applies `appearance.json`** to the runtime
  (drift, not a design gap). Ship value-driven state color as a Bases **formula-glyph**
  column (not `:has()` — Bases exposes the property key, not the value).
- **Proof:** S0 (configs validate) + S2 (installer substitution) + S5 (visual legibility).

### WS-6 — Day-1 empty-state (release decision)

Decide **seeded starter content (ADR-55 golden copy)** vs **per-surface empty-state
copy**. The dashboards already carry empty-state callouts (WS-3); a seeded-content choice
adds golden-copy fixtures instead. **Decide before WS-3 authoring.**
- **Proof:** S5 (fresh-install first-impression reads as deliberate, not broken).

## Verification mapping (WS → stage)

| Stage | WS-1 | WS-2 | WS-3 | WS-4 | WS-5 | WS-6 |
|---|---|---|---|---|---|---|
| S0 static | base parse | drift test present | — | provenance lock | configs validate | — |
| S1 pytest | base-spec unit | gen-forms drift | — | — | — | — |
| S2 dry-run | — | — | dashboards in installer | data.json in installer | app.json + appearance reconcile | seed in installer |
| S3 integration | Bases render | — | switch reuses tab | navigator renders | — | — |
| S4 live | backlink re-verify | — | — | provenance match | snippets active | — |
| S5 E2E | — | forms drive-through | four gates driven | navigate collections | visual legibility | empty-state reads right |

## GitHub setup (to create)

- **Milestone `0.1.0-alpha.7`** — assign the WS issues (to open) + existing UI issues
  #659, #665, #667, #663, #664, #666, #668.
- **Parent `Release v0.1.0-alpha.7`** (label `release`) with **gate sub-issues G1–G6**
  and **stage sub-issues S0–S5**, all linked.
- Open **WS issues** (WS-0..WS-6) and link each to its gate.
- **Scope-reconcile issue/decision:** shadow/instrument harvest (#370/#611/#416/#371) —
  fold into alpha.7 or roll to alpha.8 (set on the board; `env -u GITHUB_TOKEN` for
  Projects-v2 calls).

## Resolved design decisions (carried from the design docs)

- **Gates = dashboard notes, not workspace layouts** — switch = open-note-in-reused-tab
  (verified); retires `load-workspace.js` + Workspaces Plus (workspaces §4/§8).
- **Desk → Inbox** — overrides ADR-68's Inbox-rejection; the collision is coherent (the
  gate *is* the inbox), the room metaphor broke with Knowledge/Project (workspaces §9).
- **Portals = folder nav only** — no tag-portals (we classify by frontmatter, not
  `#tags`); not the gate switcher (no note-pinning, no API) (portals §1/§5).
- **`![[base#View]]` embed targeting** + **tab-reuse** + **Portals `spaces[]` schema** —
  all sandbox-verified; no remaining discovery risk on the shell/nav.

## Open questions

- **Gate-dashboard placement.** Existing dashboards live in `system/dashboards/`, which
  Portals **hides**. Gate dashboards are user-facing landing notes reached by the nav row
  / Homepage — confirm they live in a **non-hidden** location with unambiguous names so
  `[[inbox]]`/`[[library]]`/… resolve (vs the `inbox/` folder + `inbox.base`).
- **`newLinkFormat: absolute`** — the day-1 must-verify; outcome decides G1 + G5.
- **`gen-forms.py` exists?** — decides WS-2 size (align vs build).
- **Empty-state (G6)** — seeded content vs copy; PI decision, gates WS-3 authoring.
- **Scope-reconcile** — shadow/instrument harvest in alpha.7 or alpha.8.
