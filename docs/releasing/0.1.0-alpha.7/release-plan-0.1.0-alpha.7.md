---
release: v0.1.0-alpha.7
status: draft        # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan — v0.1.0-alpha.7
parent: Releasing
nav_order: 2
---

# Release plan — v0.1.0-alpha.7

**Current status: pre-release (draft).** alpha.7 is the **clean-slate Obsidian UI /
navigation** checkpoint: it lands the view layer (Bases), capture forms, the
persistent-shell gate model (Inbox/Library/Knowledge/Project), Portals folder
navigation with the core file explorer retained as fallback, and the Memoria-tuned
Obsidian config — the buildable, sandbox-verified subset of the UI redesign. The
design is settled across four `tmp/` design docs and verified live against Obsidian
1.12.7; the net-new persistent shell + Portals are the long pole, and three day-1
items can change scope: one **MUST-VERIFY**
(`newLinkFormat: absolute` vs the verified backlink behavior), one **generator
existence check** (`gen-forms.py` + drift pytest), and one **release decision**
(day-1 empty-state).
`released:` flips to `true` only for a tagged GitHub Release; this internal checkpoint
closes at `status: complete`, `released: false`.

**Scope-reconcile (read first).** The alpha.6 roadmap penciled the **shadow/instrument
telemetry harvest** (#370 / #611 / #416 / #371) into alpha.7. This plan scopes alpha.7
as the **UI release** and does **not** absorb that harvest. Whether the harvest folds
into alpha.7 alongside the UI work or rolls forward to alpha.8 is a **PI decision**
(§5/§8) — flagged, not silently dropped.

## 1. Scope — what this release is

alpha.7 ships the **verified, buildable subset of the clean-slate UI** — the half the
independent review kept after demoting everything speculative. **In:** the **view
layer** (the §3 authored Bases — `inbox`/`sources`/`catalog`/`claims`+hubs/`projects`/
`patterns` — plus the single Dataview status strip and the *already-existing*
`kanban.db → system/board` mirror); the **six capture forms** generated from schema with
a drift test; the **persistent-shell gate model** — four dashboard notes
(Inbox/Library/Knowledge/Project, shipped under `src/gates/`) switched by a
zero-plugin nav row, *retiring* the
ADR-68 workspace-swap mechanism (`load-workspace.js`, the QuickAdd workspace macros, and
Workspaces Plus) for one reset workspace; **Portals** as gated folder-navigation
chrome, bundled from the Linux `Memoria-test` artifact and provenance-locked under
ADR-74 while keeping the core file explorer enabled as fallback; and the
**Memoria-tuned `src/.obsidian/` config + CSS** legibility tier. It **closes** the
shipped-UI issues #659 (one title), #665 (de-duplicated Inbox), #666 (workspace
switching — by elimination), #667 (navigation), #663 (`system/` hidden), #668 (CSS
snippets). It explicitly does **not** build the general projector engine, the projected
telemetry bases, the Canvas/argument-graph spatial axis, or the dedicated edge-authoring
"relate" control — all deferred (§5,
[`tmp/ui-architecture-future.md`](tmp/ui-architecture-future.md)).

## 2. Definition of done — gates

v0.1.0-alpha.7 ships when **every gate sub-issue under `Release v0.1.0-alpha.7`
({{ #NN }}) is closed.** Definitions (state lives in the sub-issues, never in this
table):

| Gate | Proves | Verified by | Issues |
| --- | --- | --- | --- |
| G1 | **View layer conforms & renders.** The §3 authored bases match spec and lead `order:` with `title` (#659/#665); the board mirror's `board.base` renders; the home status-strip queries are pinned (#664); and the load-bearing **nested-map backlink / orphan detection re-verifies under the *shipped* `newLinkFormat`** (Open-before-merge #1). | S0 + S1 + S3 + S4 | Gate {{ #NN }}; #659, #665, #664 |
| G2 | **Capture forms, schema-generated.** The six forms (`fleeting`/`source`/`claim`/`hub`/`project`/`thesis`) are emitted by `gen-forms.py` from `.memoria/schemas/`, a pytest fails on `data.json` drift, and the clean-slate deltas land (catalog note-pickers, citekey multiselect fields, `output_mode` radio, `inquiry`/`finer` maps). | S0 + S1 + S5 | Gate {{ #NN }} |
| G3 | **Persistent shell & gates (ADR-68 amended).** Four dashboard notes under `src/gates/` (Inbox/Library/Knowledge/Project) embed their §3 views; the nav-row switch reuses the active tab; Homepage opens Inbox; `load-workspace.js` + the QuickAdd workspace macros are retired for one "Memoria" reset workspace; Workspaces Plus is not bundled. | S3 + S5 | Gate {{ #NN }}; #666 |
| G4 | **Portals navigation, gated (ADR-74).** A vendored Portals artifact ships with `data.json` (six folder portals; `system/`+`.memoria` Hidden; `_Tag Notes` relocated), `replaceFileExplorer: true` with the core `file-explorer` kept enabled, and `community-plugins.json` + `plugin-provenance-lock.json` sha256 coverage. | S0 + S3 + S5 | Gate {{ #NN }}; #667, #663 |
| G5 | **Obsidian config & CSS legibility.** The shipped `src/.obsidian/app.json` lands the Memoria-tuned settings; core-plugin toggles apply; both CSS snippets are enabled by golden-copy reconciliation (#668); value-driven state color ships as a Bases formula-glyph column. | S0 + S2 + S5 | Gate {{ #NN }}; #668, #659 |
| G6 | **Day-1 empty-state.** A near-empty fresh vault reads as *empty, not broken* — via seeded starter content (ADR-55 golden copy) **or** per-surface empty-state copy. The choice is made, not deferred. | S5 | Gate {{ #NN }} |

ADR prerequisite (not a runtime gate): the gate set + dashboard-switching mechanism +
the **Desk→Inbox** rename **amend ADR-68** and are recorded in an accepted ADR before
build (ADR-only decision model). Tracked in the exec plan.

## 3. Validation — stages

The staged plan that turns `shipped` into `approved`; a release candidate re-runs **all
stages green from a fresh clone on the disposable `~/Memoria-test` vault** (never
`~/Memoria`). Stage state lives in the stage sub-issues (S0–S5) under the release parent.

| Stage | Proves |
| --- | --- |
| S0 | static: every `.base` parses; `app.json` / Portals `data.json` / `plugin-provenance-lock.json` validate; the `gen-forms` drift pytest is present; `docs-doctor` green; adr-index fresh |
| S1 | component pytest: `gen-forms` schema→`data.json` drift; any base-spec/config conformance units |
| S2 | dry-run: installer substitution carries the four `src/gates/` dashboards, `app.json`, the Portals `data.json`, and the snippet enablement; golden-copy reconciliation applies `appearance.json` (#668) |
| S3 | integration (Obsidian, sandbox): the §3 Bases render their views; gate dashboards embed `![[base#View]]`; the nav-row switch reuses the active tab; the Portals navigator renders the folder portals with `system/` hidden while `src/gates/` remains reachable |
| S4 | live/enforcement: **`newLinkFormat: absolute` re-verified** — nested-map `links:` still registers as a backlink so orphan/"Open questions" views hold; the provenance lock matches the vendored Portals files; CSS snippets active in the running vault |
| S5 | E2E: fresh install → land on **Inbox**; drive all four gates via the nav row; capture through each form; confirm the near-empty vault reads as a deliberate empty-state, not breakage |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers are** any
open gate/stage sub-issue under the release parent, plus any open High-priority blocker
in the [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1). Three
hard facts this release: **the `newLinkFormat: absolute` re-verification (G1/S4) is the
one finding that can silently invalidate orphan/backlink views** — run it first;
**the `gen-forms.py` + drift-test existence check can resize G2 from alignment to
generator construction** — verify it before sizing WS-2; and **the day-1 empty-state
(G6) is a release decision, not a build task** — decide it before the dashboards are
authored, because it shapes their copy.

## 5. Out of scope (deferred)

Deliberately later, each for a named reason. While the release is in design, the
per-surface deferred analysis lives in
[`tmp/ui-architecture-future.md`](tmp/ui-architecture-future.md); before cut, the
durable deferred set must move into the UI ADR (or a linked deferred ADR), because
`tmp/` is deleted.

- **The general projector engine** — reconcile/delete/recurrence/quarantine/reverse-index
  beyond the existing board mirror. Speculative, unbuilt, single-user-disproportionate;
  promote on real vault-size / shown need.
- **Projected telemetry bases** (`fleet-health` / `eval-trend` / `skill-lifecycle`) —
  projector-dependent, so they follow the engine.
- **The Canvas / argument-graph spatial axis** — the most novel idea and the least
  built; gated on a layout-feasibility spike and real demand. "Studio" returns with it.
- **The dedicated edge-authoring "relate" control** — net-new UI; alpha.7's interim
  authoring is the existing agent propose→confirm + hand-edited `links:` frontmatter
  (a known [[pi-direct-access-rule]] gap, §6).
- **Tab/title-bar prose title** (front-matter-title plugin / `aliases`) — extra plugin
  cost; the slug + `title`-led `order:` covers #659 without it.
- **Shadow / instrument telemetry harvest** (#370 / #611 / #416 / #371) — the alpha.6
  roadmap's committed-next. **Scope-reconcile:** fold into alpha.7 or roll to alpha.8 —
  PI decision (§8); not silently dropped.

## 6. Known limitations (state in the release notes)

- **No PI-direct edge-authoring control.** `links:` frontmatter remains the only system
  of record for an edge, but the PI can originate one only via agent propose→confirm or
  by hand-editing frontmatter — the dedicated "relate" control is deferred.
- **No Canvas / argument graph.** The spatial axis ships nothing in alpha.7; the
  "Retracted (lineage)" view is a flat-table stopgap for DAG-shaped `superseded_by`.
- **Telemetry dashboards are absent** (`fleet-health`/`eval-trend`/`skill-lifecycle`) —
  projector-dependent, deferred.
- **Empty-on-arrival.** Most dashboards render blank on a fresh vault; G6 mitigates the
  first impression but the vault genuinely starts near-empty by design.
- **Portals is a gated core-surface replacement.** If it breaks on an Obsidian upgrade,
  navigation degrades to the retained core file-explorer fallback; it rides the ADR-74
  version smoke-test.

## 7. Cut procedure

1. **Every gate + stage sub-issue closed** under the release parent; required CI green on
   `main`; no open High-priority blocker.
2. **Re-run all stages from a fresh clone** on `~/Memoria-test` → all green; record
   evidence in the sub-issues / Actions artifacts. The `newLinkFormat` and Portals
   provenance checks (S4) are mandatory.
3. **ADR status maintenance.** Accept the new UI ADR that **amends ADR-68** (gate set
   Inbox/Library/Knowledge/Project, dashboard-note switching, the Desk→Inbox rename
   overriding ADR-68's Inbox-rejection); update **ADR-74** provenance for the added
   Portals plugin; note ADR-70 consistency; and promote the durable deferred set from
   `tmp/ui-architecture-future.md` into that ADR or a linked deferred ADR. Run the
   retire-sweep (expected no-op).
4. **Merge the release-please PR** (folding §6 known-limitations into the notes) — or,
   for this internal checkpoint, skip the tag.
5. **Set frontmatter** — internal checkpoint: `status: complete`, `released: false`.
6. **Delete `tmp/`** scratch (the four source design docs, draft dashboards, exec
   plan, and any extra design notes) — promote the durable decisions into the UI ADR
   first.
7. **Close the milestone and the release parent issue**, rolling unfinished issues
   forward.

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Shadow & instrument harvest | alpha.8 (or fold into alpha.7 — §5 reconcile) | #370 / #611 / #416 / #371 dark-launch telemetry against a seeded corpus |
| Projector engine | trigger-gated (vault size / shown need) | extend the board mirror → reconcile/delete/recurrence/quarantine + telemetry bases ([`tmp/ui-architecture-future.md`](tmp/ui-architecture-future.md)) |
| Spatial axis (Canvas / argument graph) | after a layout-feasibility spike + demand | projected argument canvas, incremental-stable layout, "Studio" gate returns |
| Edge-authoring "relate" control | priority UI follow-on | direct PI edge origination → `links:` (closes the alpha.7 [[pi-direct-access-rule]] gap) |

Full phase steps live in
[`tmp/ui-architecture-future.md`](tmp/ui-architecture-future.md) and would move to
`release-plan-v0.1.0-alpha.7-appendix.md` if worth preserving.

## 9. Appendix — what does NOT belong in this file

The living build plan (workstreams, sequencing, per-issue steps) is
[`tmp/exec-plan-0.1.0-alpha.7.md`](tmp/exec-plan-0.1.0-alpha.7.md). The design research
that produced this scope is the four `tmp/` design docs
([`ui-architecture-alpha7.md`](tmp/ui-architecture-alpha7.md),
[`workspaces-design.md`](tmp/workspaces-design.md),
[`portals-design.md`](tmp/portals-design.md),
[`ui-architecture-future.md`](tmp/ui-architecture-future.md)). Durable decisions become
the UI ADR; issue/PR evidence stays on GitHub.
