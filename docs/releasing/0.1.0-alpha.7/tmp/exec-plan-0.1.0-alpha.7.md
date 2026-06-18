# ExecPlan - v0.1.0-alpha.7

_Living build doc (alpha.7 `tmp/`). Tracks the **how**; the prose plan
([../release-plan-0.1.0-alpha.7.md](../release-plan-0.1.0-alpha.7.md)) holds the
**what**, and gate/stage **state** lives in the `Release v0.1.0-alpha.7` issue and its
sub-issues. Delete `tmp/` at cut after promoting durable decisions to ADRs._

## 0. Metadata

- **Task:** Build the alpha.7 clean-slate Obsidian UI checkpoint from ADR through
  release validation.
- **Worktree / branch:** one worktree per WS branch, created with
  `git worktree add ~/mv-alpha7-<ws> -b <scope>/alpha7-<ws> origin/main`.
- **Related ADRs:** ADR-68 (amended by WS-0); ADR-70 (JTBD gates); ADR-74 (plugin
  provenance); ADR-55 (golden-copy fixtures if G6 chooses seeded content).
- **Related issues / milestone:** milestone `0.1.0-alpha.7`; existing UI issues
  #659, #665, #667, #663, #664, #666, #668; release parent and WS/gate/stage
  sub-issues are still to create.
- **Started:** 2026-06-18. **Last updated:** 2026-06-18.

## 1. Purpose / big picture

alpha.7 makes the vault's first screen and navigation match the clean-slate UI
design that was verified in Obsidian. A fresh install should open to an Inbox gate,
show a stable Portals folder navigator, let the PI switch among Inbox, Library,
Knowledge, and Project by opening dashboard notes in the same tab, and keep capture
forms/schema, Bases views, and shipped Obsidian config in sync.

The plan is the running build document. Durable decisions move to ADRs, readiness
state moves to GitHub release/gate/stage issues, and this `tmp/` file is deleted
before the checkpoint closes.

## 2. Context and orientation

The **clean-slate UI** is the verified subset of the four source design docs:
[`ui-architecture-alpha7.md`](ui-architecture-alpha7.md),
[`workspaces-design.md`](workspaces-design.md),
[`portals-design.md`](portals-design.md), and the deferred set in
[`ui-architecture-future.md`](ui-architecture-future.md). A **gate** is a work mode
derived from the PI's job-to-be-done; a **dashboard** is the authored note that
composes the gate's Bases views; **Portals** is folder-navigation chrome, not the
gate switcher.

Important repository paths:

- `src/` is the shipped vault tree.
- `src/.obsidian/` holds the shipped Obsidian configuration and vendored plugins.
- `src/system/dashboards/` currently holds legacy/internal dashboards and Bases.
- `src/gates/` is the alpha.7 destination for user-facing gate dashboards.
- `src/inbox/`, `src/catalog/`, `src/notes/`, and `src/projects/` are the visible
  content collections surfaced by Bases and Portals.
- `docs/adr/` is the only durable home for UI decisions and deferred scope cuts.

## 3. Plan of work

First, create the GitHub release scaffolding and write the accepted UI ADR so the
gate set, dashboard-switching model, Desk-to-Inbox rename, and deferred future work
are not recorded only in this working plan. Then run the two cheap day-1 checks
that can change implementation size: `newLinkFormat: absolute` backlink behavior
and whether `scripts/gen-forms.py` plus its drift pytest already exist. Decide G6
empty-state before authoring dashboard copy.

Build proceeds by workstream: align the view layer, generate/align capture forms,
author the persistent-shell dashboards under `src/gates/`, vendor Portals from the
Linux `Memoria-test` artifact with ADR-74 provenance, ship the
Obsidian config/CSS tier, and prove the empty-state. Each workstream lands as a
separate PR from its own worktree. The release candidate then reruns S0-S5 from a
fresh clone against `~/Memoria-test`, never the real `~/Memoria`.

## 4. Concrete steps

1. **Create isolated branch/worktree for the current workstream**:

   ```bash
   git fetch origin
   git worktree add ~/mv-alpha7-<ws> -b <scope>/alpha7-<ws> origin/main
   cd ~/mv-alpha7-<ws>
   ```

   Expected output includes `Preparing worktree` and `HEAD is now at <origin/main sha>`.

2. **Confirm the baseline is clean and current**:

   ```bash
   git status --short
   git log -1 --oneline
   ```

   Expected output: `git status --short` prints nothing; the log commit matches
   `origin/main` fetched in step 1.

3. **Create release tracking before implementation**:

   ```bash
   gh api repos/eranroseman/memoria-vault/milestones -f title='0.1.0-alpha.7'
   gh issue create --title "Release v0.1.0-alpha.7" --label release
   ```

   Expected output: GitHub URLs for the milestone/parent issue. Then create/link
   gate issues G1-G6, stage issues S0-S5, and WS issues WS-0-WS-6; record their
   numbers back into this plan and the release plan.

4. **Run the day-1 scope checks**:

   ```bash
   test -f scripts/gen-forms.py
   rg -n "gen-forms|modalforms|data.json" tests scripts src/.obsidian/plugins/modalforms
   python scripts/docs_doctor.py docs/releasing/0.1.0-alpha.7
   ```

   Expected output: `test -f` exits 0 if WS-2 is alignment work; otherwise WS-2
   becomes generator construction. `rg` identifies the drift test or confirms it is
   absent. `docs-doctor` prints `clean`.

5. **Implement each WS in order** using the Workstreams section below. After each
   WS, run the mapped stage proof and update Progress, Execution log, Surprises,
   and Artifacts before opening the PR.

6. **Validate the release candidate from a fresh clone**:

   ```bash
   python scripts/docs_doctor.py docs
   python -m pytest tests/
   bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test
   ```

   Expected output: docs and pytest pass; the installer writes only to
   `~/Memoria-test`. Manual S3-S5 evidence is recorded in the stage sub-issues and
   summarized in Artifacts.

## 5. Validation and acceptance

- **Claim:** Given a fresh alpha.7 install, when Obsidian opens the vault, then the
  PI lands on the Inbox gate dashboard and the near-empty vault reads as intentional.
  **Prove with:** S5 fresh install on `~/Memoria-test`.
- **Claim:** Given `newLinkFormat: absolute`, when nested-map `links:` frontmatter
  points at another note, then Obsidian still registers the backlink and orphan/open
  question views remain correct. **Prove with:** S4 live fixture in the sandbox.
- **Claim:** Given the shipped schemas/vocabulary, when the forms generator runs,
  then Modal Forms `data.json` is reproduced and pytest fails on drift. **Prove
  with:** S1 drift test.
- **Claim:** Given the persistent shell, when the PI clicks a gate nav-row link,
  then the active tab is reused and the target dashboard renders its Bases embeds.
  **Prove with:** S3 Obsidian integration check.
- **Claim:** Given Portals is enabled, when the navigator opens, then visible
  collection folders are present and `system/` plus `.memoria` are hidden while the
  core file explorer remains available as fallback. **Prove with:** S3/S5 manual
  check plus S0 provenance validation.

## 6. Idempotence and recovery

- **Safe to re-run:** static checks, docs-doctor, pytest, installer dry-runs, and
  sandbox installs target a disposable worktree/vault and can be repeated.
- **Rollback:** abandon a failed WS by closing its PR and removing only that task
  worktree with `git worktree remove ~/mv-alpha7-<ws>` after confirming it is clean.
  Runtime experiments happen only in `~/Memoria-test`, so the real `~/Memoria` vault
  is untouched.
- **Generated artifacts:** regenerate Modal Forms data and Portals/plugin locks from
  their source scripts/config, then review the diff by explicit path before staging.

## 7. Progress

- [x] 2026-06-18 - Alpha.7 scope split, release plan, and first execution matrix
  created.
- [ ] 2026-06-18 - GitHub release parent, gate/stage issues, WS issues, and milestone
  created.
- [x] 2026-06-18 - WS-0 UI ADR accepted and linked.
- [x] 2026-06-18 - Day-1 scope checks recorded (`newLinkFormat`, `gen-forms`).
- [x] 2026-06-18 - G6 empty-state decision recorded before WS-3 authoring.
- [x] 2026-06-18 - WS-1 through WS-6 implemented and validated in-repo.

## 8. Execution log

- 2026-06-18 - Treat alpha.7 as a UI release and keep the alpha.6
  shadow/instrument harvest as an explicit scope-reconcile decision instead of
  silently absorbing it.
- 2026-06-18 - Gate dashboards are user-facing landing notes, so their build
  destination is `src/gates/{inbox,library,knowledge,project}.md`, not hidden
  `src/system/dashboards/`.
- 2026-06-18 - Implemented the persistent gate shell, generated capture forms,
  aligned Bases, vendored Portals 1.4.1 from Linux `~/Memoria-test`, and
  provenance-locked the shipped plugin set. Runtime Obsidian S3-S5 still need an
  attended sandbox pass before release cut.
- 2026-06-18 - Staged the alpha.7 UI/plugin/config files into disposable
  `~/Memoria-test` and verified the actual sandbox files headlessly: JSON parses,
  Portals spaces/hidden settings match spec, `community-plugins.json` excludes
  Workspaces Plus, Portals provenance hashes match, and every gate embed references
  an existing Base. Attempted to launch `/opt/Obsidian/obsidian` against the sandbox,
  but no desktop process stayed available for the CLI bridge, so the visual S3-S5
  Obsidian pass remains attended/manual.

## 9. Surprises & discoveries

- 2026-06-18 - `newLinkFormat: absolute` may invalidate backlink/orphan behavior
  that was verified under shortest-form wikilinks; S4 must rerun before G1/G5 lock.
- 2026-06-18 - The plan asserts `gen-forms.py` and a drift test, but their existence
  must be verified at HEAD before sizing WS-2.

## 10. Interfaces & dependencies

- **Obsidian:** validated against Obsidian 1.12.7 in the design docs.
- **Bases:** dashboard embeds depend on verified `![[base#View]]` targeting.
- **Modal Forms:** `src/.obsidian/plugins/modalforms/data.json` must be generated
  from `.memoria/schemas/types/*.yaml` plus `system/vocabulary.md`.
- **Portals:** vendored plugin config depends on the verified `spaces[]` shape and
  ADR-74 provenance lock.
- **Homepage / QuickAdd / Commander:** Homepage opens Inbox; QuickAdd may provide
  optional gate hotkeys; Commander carries global actions.

## 11. Artifacts & notes

Add concise evidence here as each WS lands: command transcripts, Obsidian sandbox
observations, generated-file excerpts, and links to PRs/issues. Do not paste secrets
or output from the real runtime vault.

## 12. Outcomes & retrospective

- **Shipped:** to fill at cut.
- **Still open:** to fill at cut; unresolved work rolls to GitHub issues.
- **Routed to:** UI ADR, release parent issue, gate/stage issues, milestone, and PRs.
- **Lessons:** to fill at cut.

## 13. Scope (locked recommendation)

The **clean-slate UI**, verified-subset only. Source of truth = the four design docs
listed above.

- **WS-0 - UI ADR** amending ADR-68 (gate set, dashboard-switching, Desk-to-Inbox).
  ADR-only decision model: accepted before build.
- **WS-1..6 - build**, mapping 1:1 to G1..G6 (table below).
- **Deferred** (future doc): projector engine, telemetry bases, Canvas/argument graph,
  edge-authoring relate-control. **Scope-reconcile:** the shadow/instrument harvest
  (#370/#611/#416/#371) the alpha.6 roadmap put in alpha.7 is **not** absorbed here -
  fold-in vs roll-to-alpha.8 is a PI call.

## 14. Critical path & sequencing

- **Run two cheap, high-information checks on day 1 - they can move scope:**
  1. **`newLinkFormat: absolute` re-verification** (G1/S4). Section 7 verified
     nested-map backlink/orphan detection under shortest-form wikilinks; section 10
     ships `newLinkFormat: absolute`. If absolute form breaks nested-map backlink
     registration, the orphan / "Open questions" views (G1) and the `link-colors`
     prefix-keying (G5) are both affected. Re-test in the sandbox before locking G1
     or G5.
  2. **`gen-forms.py` + drift-test exist?** (G2/Open-before-merge #6). The doc
     asserts the generator + pytest without citing the file. If absent, WS-2 is
     *build the generator*, not *align forms* - a materially bigger WS. Confirm at
     HEAD first.
- **Decide G6 empty-state before authoring dashboards** - seeded content vs
  per-surface copy shapes WS-3's dashboard text; it is a PI release decision, not a
  build task.
- **WS-3 (shell/gates) + WS-4 (Portals) are the net-new long poles, but de-risked:**
  base-embed + `#View` targeting, tab-reuse, and the Portals `spaces[]` schema are
  all **sandbox-verified** (workspaces section 8 / portals section 8). Portals is
  vendored from the Linux `Memoria-test` install and provenance-locked.
- **WS-5 (config/CSS) ships as its own PR** (per `ui-architecture-alpha7.md`
  section 10) and is coupled to WS-1 only through `newLinkFormat`.
- Each WS lands as its own PR off its own branch/worktree (shared-checkout rule);
  never commit to `main`; runtime/Obsidian work is on the `~/Memoria-test` sandbox
  only, never `~/Memoria`.

## 15. Workstreams

| WS | Gate | Closes | One-line deliverable | Stage proof | Status |
|---|---|---|---|---|---|
| WS-0 | (ADR) | - | UI ADR amending ADR-68 (gate set + switching + Inbox rename) | S0 | implemented |
| WS-1 | G1 | #659,#665,#664 | Section 3 authored bases conform, `title`-led, backlink re-verified | S0+S1+S3+S4 | implemented; runtime S4 pending |
| WS-2 | G2 | - | six forms generated from schema + drift test | S0+S1+S5 | implemented |
| WS-3 | G3 | #666 | four gate dashboards + nav-row shell; retire workspace-swap | S3+S5 | implemented; runtime S3/S5 pending |
| WS-4 | G4 | #667,#663 | Portals folder nav, vendored + provenance-locked | S0+S3+S5 | implemented |
| WS-5 | G5 | #668,#659 | `app.json` + core-plugin toggles + CSS snippets | S0+S2+S5 | implemented |
| WS-6 | G6 | - | day-1 empty-state (seeded content / copy) | S5 | copy implemented; runtime S5 pending |

### WS-0 - UI ADR (amends ADR-68)

Record the settled design as an accepted ADR before build (ADR-only model). Captures:
gate set **Inbox/Library/Knowledge/Project** (Studio deferred); **dashboard-note
switching** in a persistent shell, retiring the workspace-swap mechanism; the
**Desk-to-Inbox rename** overriding ADR-68's explicit Inbox-rejection (rationale:
`workspaces-design.md` section 9 - room metaphor broke; the collision is coherent).
Mark ADR-68 amended; note ADR-70 consistency; record ADR-74 provenance for the added
Portals plugin; record the deferred projector/telemetry/Canvas/relate-control set so
`ui-architecture-future.md` is not the only durable home.

- **Do not rename `docs/adr/68-workspaces-desk-library-studio.md`** - 5 ADRs (70/77/69/13
  + README) cross-link that filename; the new ADR gets a fresh number/file and 68
  gets a superseded/amended-by header.
- **Proof:** S0 (adr-index fresh, docs-doctor green).

### WS-1 - View layer (section 3 bases) (#659, #665, #664)

The authored bases mostly **exist** (`inbox/inbox.base`, `catalog/catalog.base`,
`system/dashboards/{claims,sources,project-gate,patterns}.base`); this WS **aligns
them to the section 3 spec**, it is not net-new.

- **Align each base** to its section 3 views; **lead every `order:` with the `title`
  property** (not `file.name`) so collections read as titles (#659), and confirm the
  four `inbox.base` views are non-overlapping (#665 dedup holds by construction).
- **Hubs** = one folded view under `notes/hubs/`, not a dedicated base (avoid a base
  for a handful of files). Confirm whether a minimal `hubs.base` or a `claims.base`
  view.
- **`board.base`** - verify the existing mirror renders under the section 2 spec
  (`as_of` sort).
- **Pin the home status-strip queries** (#664) - the one Dataview surface; reviews
  pending, blocked, HIGH/CRITICAL; clearer labels than "boards"/"finding".
- **MUST-VERIFY:** re-run the section 7 nested-map backlink/orphan fixture **under
  `newLinkFormat: absolute`** (couples to WS-5). If it breaks, either keep
  shortest-form or materialize an `inbound_count` scalar (the section 3
  structural-rule-2 fallback).
- **Proof:** S0 (parse) + S1 (any base-spec unit) + S3 (render in Obsidian) + S4
  (backlink re-verify).

### WS-2 - Capture forms (section 4)

- **Confirm `scripts/gen-forms.py` + the drift pytest exist** (verify-at-head). If
  not, building the generator is the bulk of this WS.
- Generator emits every enum/multiselect stanza of Modal Forms' `data.json` from
  `.memoria/schemas/types/*.yaml` + `system/vocabulary.md`; pytest fails on drift.
- Land the clean-slate deltas: `entity` -> catalog note-picker; `sources` -> citekey
  multiselect; `output_mode` -> radio:2; `inquiry_*`/`finer_*` -> assembled `map`
  kinds.
- Six forms total (`fleeting`/`source`/`claim`/`hub`/`project`/`thesis`); `source` is
  one schema behind three capture buttons (Zotero/URL/manual).
- **Proof:** S0/S1 (drift test) + S5 (each form drives through in Obsidian).

### WS-3 - Persistent shell & gates (#666)

The net-new shell. Replaces the ADR-68 workspace-swap with dashboard notes.

- **Author four gate dashboards** (drafts in [`dashboards/`](dashboards/)):
  `src/gates/{inbox,library,knowledge,project}.md`, each embedding its section 3
  views via `![[base#View]]` (**verified** syntax) + a current-gate-bold **wikilink
  nav row** + empty-state copy (WS-6). This keeps user-facing gate dashboards out of
  `src/system/dashboards/`, which Portals hides.
- **Retire the swap mechanism:** delete `src/system/scripts/load-workspace.js` + the
  3 QuickAdd workspace macros; remove the `## Workspaces` button block from
  `src/home.md`; **do not** bundle Workspaces Plus.
- **Repurpose existing dashboards:** `system/dashboards/desk.md` content becomes
  `src/gates/inbox.md`; `studio.md` content (claims + project-gate + patterns)
  splits into `src/gates/knowledge.md` and `src/gates/project.md`; `library.md`
  content moves to `src/gates/library.md`. Keep `src/system/dashboards/` for
  internal/legacy dashboards and reusable Bases.
- **One golden "Memoria" workspace** in `workspaces.json` as a *reset* layout only
  (`saveOnSwitch` off); keep the core Workspaces plugin enabled.
- **Homepage** opens the Inbox dashboard on launch; **Commander** carries the global
  actions (capture x3, delegate, resolve) moved off `home.md` Buttons; gate hotkeys
  via four QuickAdd open-note choices are **optional** (the nav row is the baseline).
- **Verified:** `![[base#View]]` targeting + `openLinkText(target,'',false)` tab-reuse
  (workspaces section 8).
- **Proof:** S3 (switch reuses tab; dashboards render) + S5 (drive all four gates).

### WS-4 - Portals navigation (#667, #663)

Adopt Portals as gated folder-nav chrome (`portals-design.md`) from the Linux
`Memoria-test` installed artifact. A config-only placeholder is not enough for ADR-74.

- **Vendor a Portals `data.json`** (verified `spaces[]` shape
  `{portalType:"folder",folderPath,iconName}`): six folder portals
  (`inbox`/`catalog`/`notes/sources`/`notes/claims`/`notes/hubs`/`projects`);
  `replaceFileExplorer: true`; route `system/`+`.memoria` to **Hidden**; relocate
  `tagNotesFolderPath` -> `system/_tag-notes`; trim `splitViewTabs` to
  `recent/bookmarks/context-notes/trash`; **no tag-portals**.
- **Keep the core `file-explorer` plugin enabled** (fallback) - adopt via Portals'
  own flag, never by disabling core.
- **Add Portals to `community-plugins.json` + `plugin-provenance-lock.json`**
  with vendored files + sha256. **Do not add Workspaces Plus.**
- **Verify-before-build (minor):** `hiddenItems` key shape (`{path:true}` vs array)
  and the Lucide `iconName` ids - both by a one-time UI-configure-then-read.
- **Proof:** S0 (provenance lock validates) + S3 (navigator renders, `system/`
  hidden) + S5 (navigate to collections).

### WS-5 - Obsidian config & CSS (#668, #659)

Functional changes to shipped `src/.obsidian/` - its own PR
(`ui-architecture-alpha7.md` section 10).

- **`app.json`** (today `{}`): ship the nine Memoria-tuned settings, including
  `showInlineTitle:false` (#659) and `newLinkFormat:absolute` (**gated on WS-1's
  re-verification**).
- **Core plugins:** disable core `templates` (verify QuickAdd does not call it); keep
  `file-explorer` enabled; lean-disable `daily-notes`; keep `workspaces` (reset
  layout).
- **CSS (#668):** the snippets are already enabled in shipped `appearance.json`; the
  fix is **installer/golden-copy reconciliation applies `appearance.json`** to the
  runtime (drift, not a design gap). Ship value-driven state color as a Bases
  **formula-glyph** column (not `:has()` - Bases exposes the property key, not the
  value).
- **Proof:** S0 (configs validate) + S2 (installer substitution) + S5 (visual
  legibility).

### WS-6 - Day-1 empty-state (release decision)

Decide **seeded starter content (ADR-55 golden copy)** vs **per-surface empty-state
copy**. The dashboards already carry empty-state callouts (WS-3); a seeded-content
choice adds golden-copy fixtures instead. **Decide before WS-3 authoring.**

- **Proof:** S5 (fresh-install first-impression reads as deliberate, not broken).

## 16. Verification mapping (WS -> stage)

| Stage | WS-1 | WS-2 | WS-3 | WS-4 | WS-5 | WS-6 |
|---|---|---|---|---|---|---|
| S0 static | base parse | drift test present | - | provenance lock | configs validate | - |
| S1 pytest | base-spec unit | gen-forms drift | - | - | - | - |
| S2 dry-run | - | - | dashboards in installer | data.json in installer | app.json + appearance reconcile | seed in installer |
| S3 integration | Bases render | - | switch reuses tab | navigator renders | - | - |
| S4 live | backlink re-verify | - | - | provenance match | snippets active | - |
| S5 E2E | - | forms drive-through | four gates driven | navigate collections | visual legibility | empty-state reads right |

## 17. GitHub setup (to create)

- **Milestone `0.1.0-alpha.7`** - assign the WS issues (to open) + existing UI issues
  #659, #665, #667, #663, #664, #666, #668.
- **Parent `Release v0.1.0-alpha.7`** (label `release`) with **gate sub-issues G1-G6**
  and **stage sub-issues S0-S5**, all linked.
- Open **WS issues** (WS-0..WS-6) and link each to its gate.
- **Scope-reconcile issue/decision:** shadow/instrument harvest (#370/#611/#416/#371)
  - fold into alpha.7 or roll to alpha.8 (set on the board; `env -u GITHUB_TOKEN`
  for Projects-v2 calls).

## 18. Resolved design decisions (carried from the design docs)

- **Gates = dashboard notes, not workspace layouts** - switch =
  open-note-in-reused-tab (verified); retires `load-workspace.js` + Workspaces Plus
  (workspaces sections 4/8).
- **Desk -> Inbox** - overrides ADR-68's Inbox-rejection; the collision is coherent
  (the gate *is* the inbox), the room metaphor broke with Knowledge/Project
  (workspaces section 9).
- **Portals = folder nav only** - no tag-portals (we classify by frontmatter, not
  `#tags`); not the gate switcher (no note-pinning, no API) (portals sections 1/5).
- **Gate dashboard placement = `src/gates/`** - user-facing gate dashboards must
  remain visible while `system/` is hidden by Portals; internal dashboards and Bases
  stay under `src/system/dashboards/`.
- **`![[base#View]]` embed targeting** + **tab-reuse** + **Portals `spaces[]` schema**
  - all sandbox-verified; no remaining discovery risk on the shell/nav.

## 19. Open questions

- **`newLinkFormat: absolute`** - the day-1 must-verify; outcome decides G1 + G5.
- **`gen-forms.py` exists?** - decides WS-2 size (align vs build).
- **Empty-state (G6)** - seeded content vs copy; PI decision, gates WS-3 authoring.
- **Scope-reconcile** - shadow/instrument harvest in alpha.7 or alpha.8.
