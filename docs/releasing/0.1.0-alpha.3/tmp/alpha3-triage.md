# Alpha.3 triage — what's in, what's deferred

**Inputs:** [ui-design-research-report.md](ui-design-research-report.md), [open-issues-research.md](open-issues-research.md), [naming-and-diataxis-audit.md](naming-and-diataxis-audit.md)
**Date:** 2026-06-14

## Guiding principle

The design note frames it: *alpha.3 is "the UI build" — resolve the UI issues before project functionality moves to alpha.4.* So:

- **In alpha.3:** the PI's direct in-Obsidian loop must be correct and frictionless — **capture → triage → navigate → dashboards → home.md** — plus the **cheap correctness/docs fixes** that prevent contradictions and the **decisions** the UI work must build on.
- **Deferred:** (1) **project functionality** (the Project gate and its artifacts) — alpha.4 by definition; (2) **high-blast-radius backend refactors** that don't serve the UI (the Operations *code* rename, `scripts/*.py` casing) — a dedicated refactor pass; (3) **net-new heavy features** and internal-quality cleanups not on the core loop.

## Decide now, execute later

A decision can be **made** in alpha.3 (so UI work builds on settled vocabulary) even when its **execution** is deferred. The clearest case is [ADR-69 (Operations naming)](../../../adr/69-operations-layer-naming.md): **accept the vocabulary now**, run the code/tree rename as a later dedicated pass. Each row below is tagged **Decide** and/or **Do** for alpha.3.

---

## Triage

Legend: **α3** = in alpha.3 · **α3-decide** = decide in alpha.3, execute later · **defer** = alpha.4+ / dedicated pass.

### A. Defects — the core loop is broken (highest priority)

| Issue (report ref) | Verdict | Rationale |
|---|---|---|
| Fleeting note not in fleeting base (§9 D-1) | **α3** | breaks tutorial 02 capture |
| URL capture creates no candidate card / no "Needs me" (§9 D-2) | **α3** | breaks tutorial 03 triage |
| Homepage plugin not opening (§9 D-3) | **α3** | first thing the PI sees |
| Resolve-card button broken (§9 D-4) | **α3** | core triage action |
| Zotero capture broken (§6, §9 D-5) | **α3** | core capture path |
| "No Python installed" error (§9 D-6) | **α3** | onboarding dead-end |
| Delegate-task list shows verbs only / `memoria-` prefix (§9 D-7) | **α3** | user-facing, cheap |
| Metrics dashboards show no data (§9 D-8) | **α3** | just confirm graceful "no data yet" |
| Naming defects: reconcile docstring, `TestHarness`, retraction-cron name, Zone.Identifier (audit §1.1) | **α3** | trivial, no decision |

### B. Capture, actions & home.md (the daily UI)

| Issue | Verdict | Rationale |
|---|---|---|
| Adopt **Commander** for ribbon/header placement (§1) | **α3** | the genuine ribbon gap; small, high-value |
| Every action reachable without the co-PI (§1) | **α3** | PI-direct-access rule; audit + fill gaps |
| `system-actions` "how invoked" column (§1) | **α3** | cheap doc fix |
| Adopt **Modal Forms** capture + radios for lifecycle (§2, §4b) | **α3** | capture is the core UI; help-text-stays-out |
| Show only a type's properties, not all (§2) | **α3** | templates/Properties config |
| Document + source `vocabulary.md` in the form (§2) | **α3** | cheap; unblocks controlled values |
| home.md polish + run-command-on-open (§3, §4a) | **α3** | the control panel |
| Status glance: clickable counts + WCAG severity badges + snooze (§4a) | **α3** | core "what needs me" |
| "Create linked claim note" button (§6, §4c) | **α3** | core knowledge affordance in tutorials 05 |
| Enforcement stays in the Linter (§2) | **α3 (no-op)** | already exists; just confirm |

### C. Navigation, gates & dashboards

| Issue | Verdict | Rationale |
|---|---|---|
| Reframe workspaces as **intent-named gates** (3 core) (§3, Issue 1) | **α3** | relabel on existing machinery; ADR-68 already shipped the shells |
| Maintenance = **ambient** (status bar + Action cards), not a gate (Issue 1c) | **α3-decide + Do status bar** | strongest-supported finding; build the status-bar indicator |
| **JTBD dashboards** — action-first Desk, object-first Library/Knowledge (§4, Issue 1d) | **α3** | the dashboards the PI lives in |
| Consolidate one-Dataview-per-pane; move explanation out of panes (§4) | **α3** | layout cleanup |
| **Base Board kanban** (§4) | **α3 = sandbox pilot only** | native Bases has no board; pilot version-pinned, don't ship-commit |
| **Knowledge/ZK gate** — deep link-network management (§3) | **defer** | gate *shell* can be α3 navigation; deep ZK functions are alpha.4 |
| **Project gate** + artifacts (research question, knowledge map, gaps, outline) (§3, Issue 1) | **defer (alpha.4)** | this *is* the alpha.4 project functionality |

### D. Folder model & file visibility

| Issue | Verdict | Rationale |
|---|---|---|
| Fix `.memoria/...` paths shown to the PI (tutorial 03 extracts) (§5) | **α3** | invariant violation + contradiction |
| Pick a visible export folder; set client-agent export there (§5, §6) | **α3** | cheap config + decision |
| Discoverability docs: `system/eval`, `vocabulary.md`, catalog bases (§5) | **α3** | cheap |
| Co-PI → Co-PI capitalization sweep (§6) | **α3** | mechanical |
| Client Agent config: display name, auto-export on, open-after off (§6) | **α3** | settings |
| Librarian source-note: clarify/implement + match tutorial (§6) | **α3** | core ingest→note loop |

### E. Docs hygiene (cheap, high-trust)

| Issue | Verdict | Rationale |
|---|---|---|
| Purge `(D41)`-style stale refs (§8) | **α3** | link rot / zero-contradiction |
| Sweep docs→`src/` links to inline-code / tag permalink (§8, Issue 3c) | **α3** | broken-on-site; do **before** any path rename |
| Promote `check_site_local_links` warning → error after sweep (§8) | **Done** | locks the rule |
| ADR-link policy: out of body/subheadings; footer "Decisions" + explanation-only (§8, Issue 3b) | **α3** | cheap convention |
| Define "CI invocation"; delete "app" from prose (§7) | **α3** | cheap terminology fix (ahead of the rename) |
| Diátaxis: split sweeps out of `reference/ingest.md`; lift the `engines/README` + `card-schema` reference tables (audit §2) | **α3** | high-impact, contained |
| Diátaxis long tail (minor MIXED pages) (audit §2) | **defer/rolling** | incremental hygiene, not UI-blocking |
| Per-operation reference+explanation split for *all* operations (Issue 3a) | **α3 for ingest; defer rest** | do the worst offender now, rest incremental |

### F. The Operations naming/refactor (ADR-69)

| Issue | Verdict | Rationale |
|---|---|---|
| **Accept the Operations vocabulary** (umbrella + 4 categories + bare-verb leaves) | **α3-decide** | UI/docs work references these terms |
| Code/tree rename `engines/ → operations/{…}`; split `sweeps/`; rehome `cluster`; rename `pipeline.py`/`lib/`/`golden.py` (audit §1.2–1.3) | **defer (dedicated pass)** | high blast radius, not UI-serving; after the §8 link sweep |
| `scripts/*.py` kebab→snake + retire `load_script()` (audit §1.4) | **defer** | CI blast radius, internal |
| Obsidian-side user-facing names: QuickAdd command normalization, co-PI skill renames (audit §1.5) | **α3** | small, user-facing |
| Folder pluralization `notes/source→sources`, `notes/index→indexes` (audit §1.5) | **defer/batch** | touches base filters; low UI value, batch with a structural pass |
| Test suite: split 18 legacy module-named tests (audit §1.6) | **defer** | internal quality |

### G. Plugins (decisions)

| Plugin | Verdict | Rationale |
|---|---|---|
| Commander | **α3 adopt** | ribbon gap (B) |
| Modal Forms | **α3 adopt** | capture (B) |
| Base Board | **α3 pilot** | kanban, sandbox only |
| Slash Commander, Leader Hotkeys | **defer/optional** | Commander covers the core |
| Better Properties (in-panel enum) | **defer (pilot)** | radios via Modal Forms cover α3; off-store/internals risk |
| cli-rest-mcp | **skip** | redundant with ADR-31 MCP; weakens the write gate |
| Apex Dashboard, Buttons Panel, Synaptic View, classic Kanban, Shell Commands, Better Command Palette | **skip** | immature / desktop-only / off-target |

---

## Alpha.3 scope (summary)

**Build/fix (α3):** all core-loop **defects** (A); **capture as forms** (Modal Forms) + **action surfacing** (Commander) + **home.md/status-glance** (B); **intent-named gates + ambient health + JTBD dashboards + kanban pilot** (C); **folder-visibility fixes + Co-PI config** (D); **docs hygiene sweep** incl. src-link convention, D-number purge, ADR-link policy, and the high-impact Diátaxis splits (E); the **cheap naming defects** and **user-facing Obsidian renames** (F).

**Decide in α3, execute later:** [ADR-69 Operations naming](../../../adr/69-operations-layer-naming.md) (accept the vocabulary; rename is a later pass).

## Deferred (alpha.4 / dedicated pass)

- **Project gate + project artifacts** (research question → knowledge map → gaps → outline → writing) — *this is alpha.4's headline.*
- **Knowledge/ZK gate deep functionality** (link-network health, hubs/indexes management) — gate shell may appear in α3 navigation; the management features are alpha.4.
- **Operations code/tree rename** + **`scripts/*.py` snake-case** — one dedicated refactor pass, after the α3 source-link sweep.
- **Folder pluralization**, **test-suite split**, **Diátaxis long-tail**, **per-operation doc split beyond ingest** — incremental/internal.
- **Better Properties / Slash Commander / Leader Hotkeys** — optional pilots, not needed for the core loop.

## Critical sequencing within alpha.3

1. **Defects first** (A) — they break the tutorials.
2. **Docs src-link sweep + convention** (E) **before** any path rename.
3. **Accept ADR-69** early so dashboards/docs use the Operations terms — but **don't** start the code rename in α3.
4. Capture/actions/home.md (B) and gates/dashboards (C) are the bulk of the build.
