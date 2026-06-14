# Alpha.3 UI build — design-research report

**Source:** [design-notes-1.md](design-notes-1.md) (issues found after reviewing alpha.2)
**Date:** 2026-06-14
**Scope:** UI/UX and information-architecture issues to resolve in alpha.3, *before* project functionality lands in alpha.4.

## How to read this

Every raw note in `design-notes-1.md` is folded into one of **ten categories** below. For each category you get: the issues it covers, the relevant best practice (researched against real Obsidian-ecosystem options), the alternatives with honest pros/cons, and a recommendation.

Each recommendation is tagged so we keep two tracks separate (per our working style):

- **[FIX]** — a defect or contradiction against an already-approved goal (re-implement what we said we'd do). No new decision needed.
- **[ADR]** — a net-new component or direction that needs a decision/ADR before building.
- **[DONE-68]** — already addressed by [ADR-68 workspaces v2](../../../adr/68-workspaces-desk-library-studio.md) (PR #450, merged); the note described alpha.2. Listed so we don't re-litigate, with any residual gap called out.

**Plugin maturity is load-bearing.** Several attractive plugins are too young, single-maintainer, or desktop-only to ship in a product. Maturity verdicts (verified against GitHub/manifests, mid-2026) are in the matrix in §10.

A grounding fact that recurs: **we already own a strong native baseline** — Obsidian core (hotkeys, palette pinning, Properties, Workspaces), native **Bases**, **Homepage** (healthy), **Buttons** (functional, but our highest-risk dependency), **QuickAdd**, and the **Local REST API** plugin's native MCP (ADR-31). Most issues are solved by *using that baseline better*, not by adding plugins.

---

## Category 1 — Action invocation & surfacing

**Issues:** pin Memoria commands in the ribbon (Tutorial 02); make the right command reachable in the right place; "every task should be performable without the co-PI — co-PI is always *on top of* the standard process, reserved for things that genuinely need two-way LLM conversation"; `system-actions` should state *how each action is invoked*; the **Resolve card** and **Delegate a task** buttons on `home.md`.

### Best practice
A command should be reachable through the cheapest affordance that fits its frequency: **frequent → visible button/ribbon**, **occasional → command palette / pinned palette**, **power-user → hotkey or chord**, **in-flow while typing → slash menu**. Crucially, the co-PI (LLM chat) must never be the *only* path to an action — it's an escalation, not the front door. This is our [PI-direct-access rule](../../../../../.claude/projects/-home-eranr-memoria-vault/memory/pi-direct-access-rule.md): every feature must be PI-accessible directly from the Obsidian UI; the co-PI is additive.

### What native already covers (no plugin needed)
- **Hotkeys** — Settings → Hotkeys assigns any combo to any command. Done.
- **Palette pinning** — Settings → Command palette → "New pinned command" floats frequent commands to the top. Done.
- **Ribbon for arbitrary commands** — *not* native. Core only shows ribbon icons a plugin registers. This is the one genuine gap.

### Options for the ribbon/placement gap
| Option | What it gives | Pros | Cons |
|---|---|---|---|
| **Commander** (`cmdr`) | Add any command to ribbon, page-header, statusbar, titlebar, mobile toolbar | Covers the most surfaces; mobile + per-device targeting; pairs cleanly with our QuickAdd commands; mature (v0.5.5, Apr 2026) | High open-issue backlog; doesn't do hotkeys (use native) or slash |
| **Slash Commander** | In-editor `/` menu of curated commands | Delivers the "slash command" path; complementary to Commander by design | Editor-context only; nothing for ribbon/mobile |
| **Leader Hotkeys** | tmux-style chords (`<leader> c f`) | Solves hotkey exhaustion elegantly | **Self-described experimental with a data-loss warning**; keyboard-only |
| **Shell Commands** | Run OS shell commands as Obsidian commands | Powerful external automation | **Off-target** (our actions are in-vault) and **conflicts with the MCP-only sandbox** — grants arbitrary local execution. Recommend against |
| **Better Command Palette** | Enhanced palette + macros | Macros could chain steps | **Likely abandoned** (last release 2023, reported breakage). Recommend against for a shipped product |

### Recommendation
- **[ADR] Adopt Commander** as the canonical way to place Memoria's QuickAdd commands in the ribbon / page-header, and rely on **native hotkeys + native palette pinning** for the rest. Optionally add **Slash Commander** if in-editor `/capture-*` is desired. Skip Leader Hotkeys (risk), Shell Commands (sandbox violation), Better Command Palette (abandoned).
- **[FIX] "Every action without the co-PI."** Audit the action catalog: for each action currently reachable only by asking the co-PI, ensure a deterministic command exists (QuickAdd command + ribbon/palette entry). Tutorial 04 Step 1 ("Ask the co-PI for a batch") must show the direct path first, co-PI as the optional conversational alternative.
- **[FIX] `system-actions` "how invoked" column.** The page lists *performer* and *context* (e.g. "daily cron") but not the invocation. Add an **Invocation** column: the command name, hotkey, or cron script for each action. There's already a "Scheduled crons" table with script names — extend that pattern to non-cron actions.
- **[FIX] Resolve card / Delegate a task buttons** — both are reported broken/awkward; tracked in the defect log (§9).

---

## Category 2 — Structured capture & frontmatter governance

**Issues:** "creating a note should be done with a form — structure, a clear divide between note structure and free text, and instructions that aren't part of the final note" (modalforms); auto-updated frontmatter (`update-time-on-edit`); *enforce* correct frontmatter (`propsec`); derive/normalize properties (`conditional-properties`); "do we need to show all properties in all note types?"; what `system/vocabulary.md` is and whether to enforce it.

### Best practice
Capture should be a **form, not a free-text template**: typed fields, labels/help that live in the form (not the note), validation at entry. Then keep two layers distinct: **scaffold-time** correctness (the form/template fills required fields right) and **drift detection** (a validator flags notes that fall out of spec later). Avoid showing every property on every note — show the fields that type actually has.

### Options
| Plugin | Job | Pros | Cons / maturity |
|---|---|---|---|
| **Modal Forms** | Form UI → `FormResult` handed to Templater/QuickAdd | Real field/body separation; help text stays out of the note; healthiest plugin in this set (v1.66, ~900 commits); desktop+mobile | Forms defined in JSON (UI builder exists); it *captures*, doesn't *enforce*; still needs Templater/QuickAdd to route the note |
| **Update time on edit** | Auto-refresh `updated` on save | Reliable single purpose; folder-ignore for templates; mobile | Timestamps only; **stale** (last release Jan 2024) — dependency-risk |
| **Propsec** | Per-type required-field *validation* by path/tag | The only plugin that does per-type required-field checks; non-destructive; status-bar + sidebar violation views | **Advisory, not blocking** — reports violations, doesn't refuse saves; pre-1.0, single maintainer |
| **Conditional Properties** | IF/THEN frontmatter *setter* (not a validator despite the name) | Flexible rule engine; normalizes derived fields vault-wide | A setter, not a gate; scheduled scans ≥5 min; pre-1.0 |

**Native + Templater/QuickAdd baseline** already gives: typed Properties editing, template-time scaffolding, QuickAdd routing. The three real gaps: (1) no form abstraction, (2) no on-edit updates, (3) **no per-type required-field enforcement**.

### Recommendation
- **[ADR] Adopt Modal Forms for capture** (fleeting, candidate/URL, source note). It directly delivers the "form with structure + non-leaking instructions" goal. Wire it into the existing QuickAdd capture commands.
- **[FIX/ADR] Enforcement is the subtle one.** Note clearly: *none* of these plugins is a hard gate. We already have a **deterministic enforcement layer** — the Linter (`detectors.py`, schema-check) and the schema YAMLs in `.memoria/schemas/`. Recommendation: keep **enforcement server-side in the Linter** (already approved, already runs in cron + CI), use **Modal Forms** to get capture right at entry, and treat Propsec as *optional in-app advisory feedback* only if we want live red-squiggle UX. Don't make Propsec the system of record — that would duplicate the Linter and risk docs↔implementation drift.
- **[FIX] `update-time-on-edit`** is a reasonable adoption for the `updated` field *if* we want it maintained on manual edits (agents already stamp it). Flag its staleness; it's low-risk but unmaintained.
- **[FIX] "Show all properties on all types?"** No. Configure the Properties view / templates per type so each note shows only its schema's fields. This is a templates + Properties-settings change, not a plugin.
- **[FIX] Document `system/vocabulary.md`.** It's the controlled-value registry for `research_area`/`methodology`/`topics`. It's currently undiscoverable — give it a one-line reference page and link it from the capture form's relevant fields (Modal Forms can source a dropdown from a list).

---

## Category 3 — Workspaces, home.md & the "gates" navigation model

**Issues (large block):** workspace design "lacking," not using the native Workspaces plugin; `home.md` as the only open tab is pointless; co-PI not in the right pane; "home" workspace name is not self-describing; library right pane empty/enigmatic; redesign `home.md` from scratch; shared layout across all 3 workspaces; left pane = navigation, right pane = co-PI; treat workspaces as **gates** (system/maintenance gate → sources/library gate → knowledge/ZK gate → project gate); homepage plugin "not working"; buttons in a line; status glance as a link; dashboard callout shows only a list of links; "review all homepage plugin settings."

### Status: largely **[DONE-68]**, with residual design work
Most of this block describes **alpha.2** and is already resolved by **ADR-68 (PR #450)**. Confirmed live in `src/.obsidian/workspaces.json` and `src/home.md`:

- Three workspaces **Desk / Library / Studio** under one shared layout contract (replaces the enigmatic "home"/"library" names). ✅
- **Co-PI (`agent-client-chat-view`) pinned in the right pane of every workspace.** ✅
- Main pane is always a real file; **`home.md` is no longer pinned** anywhere (Homepage opens it on launch). ✅
- Left pane = 2–4 drill-down tabs + file explorer last; right pane = co-PI. ✅
- `home.md` rebuilt as a four-block control panel: **Status glance** (already a link: `[[board-state|board]]`), **Act** (buttons), **Workspaces** (buttons), **Dashboards** (callouts). ✅

So: "co-PI not in right pane," "home as only tab," "home/library naming," "shared layout," "redesign home.md," "status as a link" — **already done.** Don't re-recommend.

### Residual design gaps (still open)
1. **The "gates" model isn't fully expressed.** ADR-68 gives Desk (what-needs-me) / Library (reading) / Studio (drafting). The notes' richer framing is **gates**: a *maintenance/housekeeping* gate (where you go when the system needs you; status bar signals it), a *sources/library* gate, a *knowledge/ZK* gate, and later a *project* gate. Desk ≈ maintenance gate, Library ≈ sources gate, Studio ≈ drafting — but the **knowledge/ZK gate** (link-network health, hubs, indexes) and the eventual **project gate** are not first-class. There's even an open question in the notes worth deciding: *should bookkeeping/health be its own gate, separate from a knowledge-management gate?*
   - **[ADR] Decision needed:** map gates → workspaces explicitly. Option A: keep 3 workspaces, fold "network health" into Desk. Option B: add a 4th "Network/ZK" workspace. Option C (notes' second thought): split a dedicated **bookkeeping/health** gate from a **knowledge** gate (→ 4–5 workspaces). Recommend **B** for alpha.3 (a Studio-adjacent knowledge gate) and defer the project gate to alpha.4, since ADR-68 already reserved Studio's slot for project work.
2. **Native Workspaces plugin can't automate.** Confirmed: the core Workspaces plugin only saves/restores layout snapshots — no command-on-load, no startup. That's *why* we pair it with Homepage + a QuickAdd `load-workspace.js` script (already done in ADR-68). The note's "doesn't take advantage of the plugin" is satisfied as much as the plugin allows; the automation lives in Homepage + QuickAdd, which is the correct division.
3. **Homepage settings review.** Homepage is healthy (v4.4.4, actively maintained; author handle is **mirnovov**, "novov" was the blog domain). The setting worth exploiting we're **not** using: **"run an Obsidian command on open."** Use it to refresh Dataview/Bases on landing or to focus a tab. Other useful, already-set options: open-on-startup, reading view, `refreshDataview`, pin. **[FIX]** Add a `commands` entry (e.g. a Dataview refresh) and document the full settings in `reference/obsidian-plugins`.
4. **`home.md` polish.** **[FIX]** Buttons currently render as stacked blocks; the Buttons plugin supports inline/`<button>` placement to put an Act row on one line. The "Dashboards" block is three collapsed callouts of bare links — fine, but per JTBD (§4) consider leading each with its *outcome metric* instead of a bare link.

### "Homepage plugin isn't working" / "Resolve card broken"
These are **defects**, not design — see §9.

---

## Category 4 — Bases, dashboards & lifecycle (kanban) views

**Issues:** "one dataview per pane is a waste — they can all be together"; the pane is for *information*, not explanation (move explanation to a help link); workspaces can open multiple pages, frequent/navigational info in the left pane, deeper dives on pages, bases embeddable in pages; which views per base; which dashboard pairs with each base; which kanban view (base-board) fits; cluster by job-to-be-done; frictionless next action from the dashboard; functional dashboards get a help link, diagnostic dashboards get step-by-step guidance; status glance statuses.

### Best practice (JTBD-driven)
Organize dashboards around **jobs**, not data types (Ulwick's Outcome-Driven Innovation): name each dashboard with a **verb-object-context** job ("triage system health," "find new sources," "resolve link-network issues," "synthesize toward a project"); populate it with that job's **desired-outcome metrics** as widgets (not a generic note list); and **sequence the controls along the job's steps** (locate → prepare → execute → monitor). Put a **next-action button** at each step so the dashboard is a launchpad, not a readout.

This directly answers the notes: a pane should carry *information* (the outcome metrics) with a *help link* for explanation; multiple Dataview/Bases blocks can co-exist on one **page** (deep dive), while the **left pane** holds the compact, frequent, navigational slice; bases embed in pages.

### The kanban question (verified)
As of mid-2026, **native Bases has no board/kanban view** — built-ins are Table, Cards, List, Map. A native kanban is on the official roadmap but **unshipped**. Obsidian 1.10 added the API for plugins to register Bases view types. Options for status/lifecycle boards today:

| Option | Pros | Cons |
|---|---|---|
| **Wait for native Bases kanban** | Zero dependency; aligned with our Bases-first model | Not shipped; no date |
| **Base Board** (`base-board`) | Kanban *over* native Bases; drag writes back to frontmatter (no lock-in); WIP limits, color filters; desktop+mobile; MIT | **Very young** (repo Feb 2026), fast-churning, single maintainer, empty release notes — real breakage risk |
| **Kanban** (mgmeyers, classic) | Mature-ish, widely used | Board is its **own special file**, *not* Bases/frontmatter-backed — diverges from our data-first model; "maintainers wanted," last tag 2024 |

### Recommendation
- **[ADR] Adopt the JTBD dashboard pattern** as the design language for alpha.3 dashboards: job-named, outcome-metric widgets, step-ordered next-action buttons, one help link per dashboard. Define **which views each base exposes** and **which dashboard owns each base** in a single reference table (we have the bases: `catalog`, `inbox`, `fleeting`, `claims`, `sources`, `patterns`).
- **[ADR] Kanban:** pilot **Base Board** in the sandbox (Memoria-test), version-pinned, treating native Bases kanban as the eventual target. Do **not** adopt classic Kanban (diverges from Bases). If Base Board's churn proves unstable, fall back to a Bases **Cards view grouped by status** as the interim board.
- **[FIX] Consolidate panes.** Where a workspace shows "one Dataview per pane," combine related queries into a single **dashboard page** with multiple embedded blocks, and keep the left pane to the compact navigational set. This is a layout edit to the dashboards + `workspaces.json`.
- **[FIX] Move explanation out of panes.** Replace in-pane prose with a one-line help link to the relevant docs page. Functional dashboards (used often) → help link; diagnostic dashboards (rare) → embedded step-by-step.
- **[FIX] Status glance statuses.** Today it shows review-queue / blocked / HIGH-CRITICAL findings. Decide the canonical status set (candidates: untriaged inbox count, overdue sweeps, broken-link count, stale-fleeting) and make each a link to its dashboard.

---

## Category 5 — Folder model & file visibility

**Issues:** "the system folder is for system files that can't be in `.memoria`; if the user needs to access a file, it can't be in `.memoria`"; "expecting the user to find `.memoria/data/extracts/<citekey>.md` is unreasonable — the user should never access `.memoria`, it's not even in the folder view"; export should go to a dedicated folder in the system folder; "what are the files in the eval folder?"; "where are the catalog bases?"

### Best practice
One clean invariant: **`.memoria/` = hidden infrastructure the user never opens; everything user-reachable lives in visible folders** (`system/`, `catalog/`, `notes/`, `inbox/`). Any workflow that asks the user to open a `.memoria/...` path is a design bug.

### Grounding (important contradiction found)
- The current ingest implementation produces a paper note at **`catalog/papers/<citekey>.md`** — the canonical, *visible* form. **`.memoria/data/extracts/` does not exist** in the vault. Yet Tutorial 03 Step 4 tells the user to open `.memoria/data/extracts/<citekey>.md`. That's a **docs↔implementation contradiction** (zero-contradiction rule) *and* a violation of the never-touch-`.memoria` invariant.
- `catalog.base` lives at `src/catalog/catalog.base`; the catalog records live under `catalog/papers|people|...`. The "where are the catalog bases?" question is **discoverability**, not a missing artifact — the base isn't surfaced in any obvious place outside the Library workspace's left pane.
- The `eval/` folder is `system/eval/` — gold-task fixtures for the quarterly vault-eval (diagnostic, non-gating), with a README. Again a discoverability/labeling issue.

### Recommendation
- **[FIX] Fix Tutorial 03 Step 4** to point at the visible `catalog/papers/<citekey>.md` (or wherever the extract actually surfaces), and **audit the whole tutorial/doc set** for any other `.memoria/...` path shown to the user. If a paper "extract" genuinely needs to be a distinct readable artifact, it must live in a visible folder, not `.memoria/data/`.
- **[ADR] Export destination.** Decide a single visible export folder (e.g. `system/exports/`) and set the Client Agent's auto-export there (see §6). Keep it out of `.memoria`.
- **[FIX] Discoverability.** Add short reference pages / labels for `system/eval/`, `system/vocabulary.md`, and the catalog bases, and make sure each visible folder's purpose is documented. The catalog base should be reachable from the Library gate's dashboard, not only a left-pane tab.
- **[FIX] Confirm the invariant in docs.** State plainly in the folder-model reference: "`.memoria/` is never opened by the PI; if you're told to open a `.memoria` path, that's a bug."

---

## Category 6 — Co-PI / Client Agent configuration

**Issues:** "co-PI should be **Co-PI**" (capitalization, sitewide); Client Agent — export to a dedicated system folder, auto-export **on**, open-note-after-export **off**, display name **"Memoria Co-PI"**; "the Zotero capture doesn't work"; "does the librarian create the proposed source note?"; the source note should have a **button to create a claim note** linked to it.

### Recommendation
- **[FIX] Capitalization:** sitewide rename **co-PI → Co-PI**. Note the boundary from our [don't-call-the-user-PI](../../../../../.claude/projects/-home-eranr-memoria-vault/memory/dont-call-the-user-pi.md) rule: "Co-PI" is the agent's name; "PI" remains an internal role, never a form of address. Do the rename as a careful find/replace across `docs/`, `src/` notes, templates, and the agent display config, then re-run docs-doctor.
- **[FIX] Client Agent settings:** set **display name = "Memoria Co-PI"**, **auto-export = on**, **open-after-export = off**, **export folder = the visible folder chosen in §5**. These are config changes in the Agent Client plugin data.
- **[FIX/defect] Zotero capture** ("capture from Zotero selection") is broken — defect log §9.
- **[FIX] Librarian → source note.** Clarify and, if missing, implement: does the Librarian *create the proposed source note*, or only the candidate card? Tutorial 03 Step 5 must match the implementation. The honesty-card flow suggests the Librarian proposes (card) and the PI/Co-PI creates the source note — confirm and document.
- **[ADR] "Create linked claim note" button on source notes.** Net-new affordance. Implement as a Buttons command (or Commander page-header button) on the source-note template that runs a QuickAdd command creating a claim note pre-linked to the source. Aligns with the Studio/synthesis flow (Tutorial 05).

---

## Category 7 — Documentation: engines, ingest & reference

**Issues:** "Engines are Memoria's deterministic app" — naming clash: "if there are apps, why do we call them engines?"; "what is CI invocation?" (never explained); ingest is a complex standalone page — why standalone, which Diátaxis category; `engines/ingest/pipeline.py` is too generic; naming should be consistent (ingest/search/cluster/verify/lint); "processing/maintenance vs bookkeeping/housekeeping" engines; `reference/ingest` includes *other* engines too; need separate **engine reference** (procedure) and **explanation** (rationale) pages.

### Grounding
- Engines README defines: "Engines are Memoria's **deterministic apps** — pure mechanism, no posture, no LLM judgment" (ADR-46). The five engines: **Ingest, Search, Clustering, Verification sweeps, Linter**.
- **Naming is genuinely inconsistent in code:** `engines/ingest/` exists, but Search has no `engines/search/` (it's the external qmd MCP), Clustering is `mcp/cluster_mcp.py` (not under `engines/`), Verification is `engines/sweeps/` (not `verify/`), only Linter is clean. So the doc lists five peer "engines" that don't have peer code structure.
- `reference/ingest.md` is Reference-category but mixes procedure *and* rationale, and its "The sweeps" section documents `reconcile.py` / `retraction.py` (sweeps engine), confirming "includes other engines."

### Recommendation
- **[ADR] Resolve the "engines vs apps" naming.** Pick one user-facing word. Recommend **drop "apps" entirely** — say "Engines are Memoria's deterministic **mechanisms** (no LLM judgment)." The parenthetical "(apps)" is the source of the confusion the note flags ("two names or parentheses → naming issue").
- **[FIX] Define "CI invocation"** on first use, for non-developers: "CI (the automated check that runs when changes are proposed) can invoke engines directly, at the same trust level as cron and the PI — bypassing the MCP boundary that agents must use." Or, if "CI" is too developer-centric for the audience, replace with "automated checks."
- **[ADR] Split ingest docs by Diátaxis.** Create `explanation/engines/ingest` (rationale: why the uncertainty floor, why automated-not-gated) and keep `reference/ingest` purely procedural (pipeline stages, outputs, recovery). Move the sweeps content out of `reference/ingest` into a **sweeps** reference (or the sweeps engine's own page). This generalizes to: each engine gets a procedural reference page + a rationale explanation page.
- **[ADR] Naming consistency.** Decide a single engine-naming form (recommend the bare verb: `ingest`, `search`, `cluster`, `verify`, `lint`) and apply it to **both** docs and code folders: rename `engines/ingest/pipeline.py` to something specific (e.g. `ingest/ingest.py` or `ingest/run.py`), give Clustering an `engines/cluster/` home (or stop calling the MCP an "engine"), rename `engines/sweeps/` ↔ `verify` consistently. This is a structural rename — sequence it carefully and update every doc link (§8).
- **[ADR] "Processing vs bookkeeping" taxonomy.** The note asks whether engines split into processing/maintenance vs bookkeeping/housekeeping. Worth a one-paragraph taxonomy in the engines explanation: *processing* (ingest, search, cluster) vs *integrity/housekeeping* (verify sweeps, lint). This also feeds the "gates" model in §3 (the maintenance gate surfaces the housekeeping engines' findings).

---

## Category 8 — Site-wide docs hygiene & links

**Issues:** "(D41)"-style references (annotations from purged work docs); links in engine/ingest pages are **broken** and use a different format — "why are all the links broken?"; how should we refer to a **system file** (does `engines/ingest/pipeline.py` need to be a link at all, and how formatted?); do the **ADR links** add value or distract?; subheadings with "(ADR-..)" in parentheses followed by the link in the text.

### Grounding (confirmed)
- **D-numbers** (D41, D21, D51) appear as plain text, sometimes paired with an ADR link (`(D21 / [ADR-54](...))`). They are **never link targets** and reference purged design-note numbering — meaningless to a reader.
- **Broken links are systematic and path-depth-driven.** Reference pages at `docs/reference/` correctly use `../../src/...`. Nested pages at `docs/explanation/engines/` use `../../../src/...` or `../../src/...` — **both wrong** for that depth (should be `../../../../src/...`). So links to source files break from the deeper pages. Confirmed by sampling.

### Recommendation
- **[FIX] Purge D-numbers.** Remove all `(D##)` references sitewide; where they paired with an ADR, keep just the ADR link. They're noise referencing deleted documents.
- **[FIX] Fix the broken source-file links.** This is a relative-path-depth bug concentrated in nested `explanation/` pages. Best fix: **stop hand-rolling relative paths to source.** Decide a single convention for referencing a system file — recommend **inline code, not a link**, for source paths (`` `src/.memoria/engines/ingest/...` ``), since a docs reader rarely needs to open the file and a stable link is fragile across the rename in §7. Reserve actual links for ADRs and other docs. Then run docs-doctor to confirm clean.
- **[ADR] ADR-link policy.** Decide whether inline ADR links help or distract. Recommend: **keep ADR references but demote them** — no ADR in subheadings/parentheses; instead a "Decisions" footer line per page linking the governing ADRs. This declutters the prose (the note's "subheadings include the ADR in parentheses" complaint) while preserving traceability. Note our existing [docs-doctor link-text rule](../../../../../.claude/projects/-home-eranr-memoria-vault/memory/docs-doctor-link-text-rule.md): link text must be the page title, not a filename — keep that when reworking links.
- **[FIX] Re-run `python scripts/docs-doctor.py docs`** after the link/D-number sweep; the lint job's docs-doctor will fail the build otherwise.

---

## Category 9 — Defect log (concrete bugs to fix)

These are reported as broken behavior, not design choices. Each needs reproduction + fix in alpha.3.

| # | Defect | Notes / first diagnosis |
|---|---|---|
| D-1 | **Fleeting note doesn't appear in the fleeting base** | `fleeting.base` filters `file.inFolder("notes/fleeting")`. Manual captures must land *under* `notes/fleeting/` (root or subfolder) **and** be `.md` with `type: fleeting`. Verify the capture command's destination matches the filter; canvas maps in `notes/fleeting/maps/` are `.canvas` (correctly excluded). Likely the manual capture writes elsewhere or omits frontmatter. |
| D-2 | **No Inbox tab / "Needs me" view surfaced; no candidate card created for the added URL** (Tutorial 03 Step 3) | Desk has an `inbox.base` "Needs me" view, but the URL-capture flow apparently didn't write a candidate card to `inbox/`. Check the capture-from-URL → `inbox.py` write path. |
| D-3 | **Homepage plugin "isn't working"** | Config looks correct (`openOnStartup`, `home`, reading view). Reproduce: is `home.md` resolving? Is the QuickAdd workspace script interfering? Check Homepage v4.4.4 compatibility with current Obsidian. |
| D-4 | **Resolve card button broken** | `home.md` button runs `QuickAdd: Memoria: resolve inbox card` → `resolve-inbox-card.js`. Verify the QuickAdd command + script exist and are wired. |
| D-5 | **Zotero capture doesn't work** | `QuickAdd: Memoria: capture from Zotero selection` — verify the integration path (Zotero → vault) end-to-end. |
| D-6 | **"No Python installed" error** | Engines are Python (`.memoria/engines/`). The vault/runtime expects Python; onboarding/installer must ensure it, and the error must guide the user to fix it rather than dead-end. Tie to installer test plan. |
| D-7 | **Delegate-a-task list shows verbs only / `memoria-` prefix** | Task list should show a phrase ("Rank new candidates"), not a bare verb, and drop the `memoria-` agent-name prefix in the UI. |
| D-8 | **Metrics dashboards show no data** | `eval-trend` / `fleet-health` read `system/metrics/...` which doesn't exist yet — expected until cron sweeps populate it; confirm graceful "no data yet" messaging (not an error). |

**[FIX]** all of the above. D-1, D-2, D-4, D-5 are user-facing capture/triage breakages and should be the **highest priority** — they break the core tutorials. Per our verify-independently rule, reproduce each live before declaring fixed.

---

## Category 10 — Plugin adoption decision matrix

Consolidated verdicts (verified mid-2026 against GitHub/manifests). "Adopt" = recommend for the product; "Pilot" = sandbox trial, version-pinned; "Skip" = do not adopt.

| Plugin | Job | Maturity | Verdict |
|---|---|---|---|
| **Commander** (`cmdr`) | Place commands in ribbon/header/statusbar/mobile | Mature, active (v0.5.5) | **Adopt** — fills the real ribbon gap |
| **Slash Commander** | In-editor `/` command menu | Active (v0.4.0) | **Adopt (optional)** — if `/capture-*` desired |
| **Modal Forms** | Form-based capture | Healthiest in set (v1.66) | **Adopt** — the form layer |
| **Update time on edit** | Auto `updated` field | Stable but stale (2024) | **Adopt (low-risk, optional)** — note staleness |
| **Propsec** | Per-type frontmatter validation | Pre-1.0, active | **Skip as system-of-record** (Linter owns enforcement); optional advisory only |
| **Conditional Properties** | IF/THEN frontmatter setter | Pre-1.0 | **Skip** — Templater/QuickAdd + agents cover derivation |
| **Base Board** | Kanban over Bases | Very young, churning | **Pilot** — architecturally aligned; watch the risk |
| **Kanban** (classic) | Board-as-own-file | Mature-ish, "maintainers wanted" | **Skip** — diverges from Bases-first model |
| **Apex Dashboard** | Self-contained homepage | New, own storage | **Skip** — duplicates Bases/Dataview/Homepage |
| **Buttons Panel** | Sidebar button panel | 4★, not store-reviewed, JS exec | **Skip** — unproven + security surface |
| **Synaptic View** | Launcher dashboard | Desktop-only, stale, 7★ | **Skip** — desktop-only disqualifies |
| **Leader Hotkeys** | Chorded hotkeys | Experimental, data-loss warning | **Skip** — risk |
| **Shell Commands** | Run OS commands | Slowing; desktop-only | **Skip** — violates MCP-only sandbox |
| **Better Command Palette** | Enhanced palette + macros | Likely abandoned (2023) | **Skip** — maintenance risk |
| **cli-rest-mcp** | REST + MCP via official CLI | Active but young | **Skip** — redundant with our Local REST API MCP (ADR-31); its single `execute` tool defeats the named-tool write gate |
| **Buttons** (shabegom) | In-note buttons *(in use)* | Functional, bursty single-maintainer | **Keep + monitor** — our highest-risk current dependency; plan an exit (native Bases actions / Commander) |
| **Homepage** (mirnovov) | Landing page *(in use)* | Healthy (v4.4.4) | **Keep** — exploit "run command on open" |
| **Local REST API** (native MCP) | Vault MCP *(in use, ADR-31)* | Established | **Keep** — the gated access path |
| **Native Bases / Workspaces / Properties / Hotkeys / Palette** | Core | Core | **Keep** — the baseline most issues resolve against |

---

## Suggested sequencing for alpha.3

1. **Defects first** (§9 D-1/D-2/D-4/D-5/D-6) — they break the core tutorials.
2. **Folder-visibility + docs contradictions** (§5, §8) — fix `.memoria` leaks, broken links, purge D-numbers; cheap and high-trust.
3. **Co-PI capitalization + Client Agent config** (§6) — mechanical, sitewide.
4. **Capture as forms** (§2: Modal Forms) and **action surfacing** (§1: Commander) — the biggest UX wins.
5. **Dashboards/JTBD + gates model + kanban pilot** (§3 residual, §4) — the design-heavy work; needs the ADR decisions flagged above.
6. **Engine/ingest naming + doc split** (§7) — structural rename; do once, update all links.

**Open decisions that need your call (ADR-level):** the gates→workspaces mapping (§3, esp. whether bookkeeping/health is its own gate); the engine naming form + ingest doc split (§7); the ADR-link policy (§8); Base Board adoption after pilot (§4); Modal Forms + Commander adoption (§1, §2).
