# Gates & gate-switching — clean-slate design (the "workspaces" tier)

> **Status:** clean-slate proposal (scratch, `tmp/`). Supersedes the §9
> "Workspaces + Workspaces Plus" tier of `ui-architecture-alpha7.md`. Derived from
> **requirements**, not from ADR-68's current Desk/Library/Studio implementation.
> Builds on the surfaces already specified in `ui-architecture-alpha7.md` §3–§6.
>
> **Headline:** stop implementing "gates" as Obsidian **workspace layouts**. A gate
> is a *job*, and the cheapest faithful implementation is a **dashboard note in a
> persistent shell** — which removes a plugin, two scripts, the layout-swap model,
> and the §5↔§9 inconsistency in one move.

---

## 0. The reframe in one paragraph

The current design conflates three different things under "workspace." Pulling them
apart: a **gate** is a *mode of work* (a requirement, from ADR-70 JTBD navigation); a
**dashboard** is the *note that composes a gate's surfaces* (an implementation); an
Obsidian **workspace** is a *saved pane layout* (one — heavy — way to implement the
switch). The clean-slate position is that gates should be implemented as **dashboard
notes opened in a persistent shell**, and the Obsidian-workspace-swap mechanism
(ADR-68's `load-workspace.js`, its Workspaces Plus replacement, and the per-gate
layout files) should be **retired entirely**, not improved. Switching gates then
means *opening a different note*, not *rebuilding the window*.

---

## 1. Requirements (first principles)

What does this tier actually have to do, for a single desk-based researcher (ADR-24,
no mobile)?

- **R1 — Switch by job, not by object.** The PI thinks "I'm triaging," "I'm reading,"
  "I'm synthesizing," "I'm steering a project" — not "show me the claims folder." A
  mode is a job-to-be-done (ADR-70), not a folder or an object type.
- **R2 — Each mode shows only its surfaces and hides the rest.** Focus is the entire
  value. This is what kills #667 ("navigation is unintuitive") and prevents #665
  ("same base shown 3–4×").
- **R3 — Capture and core actions are global, not a mode.** Capturing a fleeting note
  or confirming an edge must work *in every mode*. Capture is cross-cutting chrome,
  never a gate.
- **R4 — Switching is one direct action and preserves transient context.** A ribbon
  click or hotkey ([[pi-direct-access-rule]] — no CLI). Switching must not throw away
  the notes the PI currently has open; a mode change is a change of *focus*, not a
  teardown of the window.
- **R5 — Modes ship in the vault and reproduce from the golden copy.** No per-device
  UI state as the source of truth (ADR-55). A fresh install lands in the same gates.
- **R6 — Minimum plugin/risk surface.** Prefer native + already-adopted mechanisms
  over a new plugin, especially one that replaces a core surface or that the agent
  can't self-verify (the §9 risk discipline). Every plugin is ADR-74 supply-chain
  surface.
- **R7 — Honest when empty or deferred.** alpha.7 ships a near-empty vault (§8): a
  mode whose surfaces are blank on day 1 must read as "empty," not "broken." And the
  alpha.7 mode set must contain **no gate whose content is deferred** (Canvas/Studio,
  telemetry).

---

## 2. Three concepts the current design fuses

| Concept | What it is | Layer |
|---|---|---|
| **Gate** | A JTBD mode of work (triage / collect / synthesize / steer) | **Requirement** (ADR-70) |
| **Dashboard** | The authored note that composes a gate's `.base` views + status | **Implementation of a gate** |
| **Obsidian workspace** | A saved arrangement of panes/splits/sidebars | **One way to switch** — and the wrong one |

ADR-68 picked the third row as the switching primitive, then §9 tried to make it
shippable with Workspaces Plus. From requirements, the third row is an
over-implementation: it rebuilds the window (violates R4's "preserve context"), it
must be re-vendored as plugin state (fights R5), and it needs a fourth/fifth bundled
plugin (fights R6). The **dashboard note** (second row) satisfies every requirement
with vault-native content.

---

## 3. The gate set — derived, not inherited

Deriving from R1 + R7 against the surfaces that actually ship (`ui-architecture-alpha7.md`
§3): one gate per distinct job that has a non-deferred surface.

| Gate | Job (what it is for) | Composes (already specified in §3/§6) |
|---|---|---|
| **Inbox** | *Triage* — what needs me now | `inbox.base` (Needs me · Drift watch · Loose ends) + home status strip + `board.base` (secondary, mechanic's view) |
| **Library** | *Collect* — read & organize sources | `sources.base` (reading pipeline · discuss queue) + `catalog.base` |
| **Knowledge** | *Synthesize* — build & test claims | `claims.base` (by maturity · open questions · contradictions · retracted) + hubs view |
| **Project** | *Steer* — drive inquiry to output | `projects.base` (active · saturation · gaps) + per-project page |

**This is four gates, and it matches §5 exactly.** The legacy **Desk / Library /
Studio** triple (ADR-68) is the artifact to discard. (Naming: the triage gate is
**renamed Desk → Inbox** to name it after its surface — one self-describing name per
gate, no room metaphor; **Studio** retires to the future spatial axis. Code + ADR
terminology align to this single set.)

- It predates the Knowledge/Project gate split (§5, ADR-77/78/79) — "Studio" was
  carrying both synthesis and project work.
- **"Studio" is the spatial-synthesis (Canvas) mode, and Canvas is deferred**
  (`ui-architecture-future.md`). Per R7, alpha.7 must not ship a gate whose content
  is future. So **Studio drops to the future doc**, returning when the spatial axis
  does — at which point it is the scratch-Canvas home, not a duplicate of Knowledge.

This resolves the §5↔§9 mismatch in favour of the requirements: **four gates {Inbox,
Library, Knowledge, Project}; Studio deferred.**

*Not gates:* **Capture** (cross-cutting, R3) and **Telemetry** (pull-class +
projector-dependent, deferred). Telemetry, when it ships, is a section inside Inbox or
a minor 5th gate — decided then, not now.

---

## 4. The mechanism — persistent shell + dashboard-per-gate

Two candidate implementations; pick by the requirements.

- **Option A — Workspace-per-gate (layout swap).** Each gate is a saved Obsidian
  workspace; switching loads it. ✗ R4 (tears down open notes), ✗ R5 (layout lives in
  plugin state, must be re-vendored), ✗ R6 (needs Workspaces Plus). This is today's
  design.
- **Option B — One persistent shell; a gate is a dashboard note (recommended).** The
  window frame never changes; only the **main pane's dashboard note** changes.
  ✓ R1–R7.

### The persistent shell (identical in every gate)

- **Left sidebar — Portals navigator** (already adopted, §9): curated folder portals
  (`catalog`, `notes/claims`, `notes/sources`, `notes/hubs`, `inbox`, `projects`),
  `system/`+`.memoria` routed to Hidden. Constant across gates → one stable mental
  map (directly serves #667).
- **Ribbon — Commander** (already adopted, §9): the **global** actions — capture ×3
  (`fleeting`, `source(Zotero)`, `source(URL)`), delegate, resolve — *plus the four
  gate-switch buttons*. Available in every gate (R3).
- **Status bar** — active-gate indicator + the at-a-glance status strip.
- **Main pane** — the active gate's **dashboard note**. This is the only thing a
  switch changes.

### The switch

A gate-switch is a Commander command/hotkey that **opens that gate's dashboard note
in the main pane, reusing the same tab** (no new split, no layout load). Four buttons
(Inbox/Library/Knowledge/Project) + four hotkeys. Homepage (ADR-13) opens **Inbox** on
launch — the PI lands on "what needs me?" every session.

Because the shell is constant and only the dashboard note swaps, switching is instant
and **preserves whatever else the PI has open** (R4).

### Keep exactly one Obsidian workspace — as a reset, not a switch

Ship a single golden workspace ("Memoria") capturing the canonical shell (sidebar +
ribbon + main pane). It is loaded **rarely** — to *reset* a disarranged window back to
the golden layout — never per gate. This preserves reproducibility (R5) without
adopting the per-gate swap. The core Workspaces plugin covers this; **Workspaces Plus
is not needed.**

---

## 5. Gate dashboard shape

Each gate dashboard is an ordinary authored note (golden-copy-shipped) that **embeds
the gate's `.base` views** and carries its own empty-state copy. Sketch for
`inbox.md`:

```markdown
# Inbox — what needs me

> [!tip] Inbox is empty? That's the goal. New agent proposals land here.   ← R7 empty-state

```base
source: inbox.base
view: "Needs me"
```

## At a glance
`= status strip (Dataview one-liner: reviews pending · blocked · HIGH/CRITICAL)`

## Board (mechanic's view)
```base
source: system/board/board.base
view: "By lane"
```
```

The other three dashboards (`library.md`, `knowledge.md`, `project.md`) follow the
same pattern over their §3 bases. Nothing new is invented — the bases already exist;
the dashboard just *composes and labels* them and adds empty-state copy. (Exact
base-embed syntax is the one thing to confirm — §8.)

---

## 6. What this retires (and why that's the point)

Retiring the layout-swap model is a **net simplification**, which is the strongest
argument for it under R6:

- **Drop Workspaces Plus** entirely — the gate switcher is Commander + dashboard
  notes. (Resolves issue **#666** by elimination: there is no workspace-switching
  mechanism to build.)
- **Delete `load-workspace.js` + the 3 QuickAdd workspace macros** (ADR-68's
  workaround) — already slated in §9, but now with *nothing replacing them*.
- **Collapse `workspaces.json`** to a single golden "Memoria" reset layout (§4),
  instead of one layout per gate.
- **One fewer bundled plugin** on the ADR-74 supply-chain ledger; no plugin in this
  tier replaces a core surface (Portals is navigation chrome, already gated in §9).

Gates become **vault content** (notes + bases), which is exactly what R5 wants and
what the golden copy already covers.

---

## 7. Trade-offs (honest)

- **You lose per-gate *peripheral* layout** (different sidebars/splits per mode). The
  requirements never asked for it, and a constant shell is arguably better for #667.
  If a gate genuinely needs a different peripheral arrangement later (e.g. Project +
  a future argument-canvas pane), express it *inside* the dashboard note (an embed),
  not via a layout swap.
- **A dashboard note is a softer "mode change"** than a full window rebuild — less
  visually dramatic. Given R4 (preserve context) and the single-user desk setting,
  that's the right side of the trade; the status-bar active-gate cue carries the
  "where am I" signal cheaply.
- **Embedded-base performance** rides the §7 verification (warm render of a large
  grouped base ≈1.4 s). Day-1 vaults are tiny, so this is a non-issue at alpha.7
  scale; re-check only if a dashboard embeds several heavy bases at full vault size.

---

## 8. Implementation — verified live (Memoria-test, Obsidian 1.12.7)

> Both mechanical unknowns are now **pinned by sandbox testing** (CLI `eval` +
> DOM inspection against `claims.base` with 7 fixture claims).

### PINNED ✅ — base-embed + per-view targeting

- **`![[name.base]]`** embeds the base and renders its **first view** (rendered the
  "By maturity" view, 7 results — real rows, not a link). ✅
- **`![[name.base#View Name]]`** **targets a specific view** — spaces allowed.
  `![[claims.base#By maturity]]` → By-maturity/7 rows; `![[claims.base#Retracted]]` →
  the Retracted view with its own 0-result filter. ✅
- *Build implication:* dashboards embed the wanted view directly via
  `![[base#View]]`. The "set the gate view first in the .base file" fallback is **not
  needed** — but still works as a default for a bare embed.

### PINNED ✅/⚠ — the switch binding

- **Tab-reuse capability works:** `app.workspace.openLinkText(target,'',false)`
  switches the **active leaf in place** — `sameLeaf:true`, tab count unchanged, no new
  split. A modifier-less internal-link click does the same (`focusNewTab:true`). ✅
- **There is no *native* per-note "open" command** ⚠ — confirmed by enumeration:
  core/bookmarks/Portals/Commander expose no "open `inbox.md`" command. Specifically:
  - **Bookmarks** register no per-bookmark command (`bookmarks:open` only opens the
    pane).
  - **Portals** stores folder/tag **"spaces," not note-tabs**, and exposes **no API** —
    so Portals is navigation chrome only and **cannot be the gate switcher**. (This
    settles the old "pick one switcher" question: the switcher is *not* Portals.)
  - **Commander** macros only *chain existing commands* — with no underlying
    open-`X` command to chain, Commander alone can't host the gate buttons.
- **Two verified ways to bind the switch:**
  1. **Zero-plugin internal-link nav row (recommended primary).** A row of wikilinks
     `[[inbox|Inbox]] · [[library|Library]] · …` in each dashboard header. Click reuses
     the active tab (verified). No plugin, no command, ships as vault content. Limit:
     click-only (no global hotkey) and only present on a dashboard — which is fine,
     because the shell always shows a dashboard and Homepage lands on Inbox.
  2. **QuickAdd open-note choices → `quickadd:choice:<id>` commands (optional, for
     hotkeys/ribbon).** Verified that QuickAdd registers a bindable command per choice
     (28 already exist in this vault). Four lightweight "open `<gate>`" choices give
     global hotkeys and Commander-ribbon buttons. This is *much* lighter than ADR-68's
     `load-workspace.js` (open-a-note, not load-a-layout) but it does keep four
     QuickAdd choices.
- **Recommendation:** ship the **nav row** as the always-present switcher; add the
  **four QuickAdd open-note choices** only if the PI wants global hotkeys / ribbon
  buttons. Either way **Workspaces Plus is not needed** and **Portals is not the
  switcher**. (Note: this means the §9 "Commander carries the gate buttons" line is
  *conditional* on adopting the QuickAdd choices; the zero-plugin baseline puts the
  switcher in the dashboard header instead.)

### Remaining build steps (not unknowns)

- **WRITE — four dashboard notes** with the nav-row header + empty-state copy
  (drafted: `tmp/dashboards/`).
- **SHIP — one golden "Memoria" workspace** as the reset layout; `saveOnSwitch` off.
- **DECIDE — hotkeys?** If yes, add the four QuickAdd open-note choices + Commander
  ribbon bindings; if no, the nav row alone suffices.

---

## 9. ADR impact & requirements traceability

**ADR impact.** This **amends ADR-68** on three points — the **gate set** (four
{Inbox/Library/Knowledge/Project}, Studio deferred), the **switching mechanism**
(dashboard notes in a persistent shell, retiring workspace-swap), and the **gate
naming** — and is **consistent with ADR-70** (JTBD gates) and ADR-72 (Commander as the
action layer). Per the ADR-only decision model, fold this into an ADR before build.

**On the name "Inbox" (overriding ADR-68).** ADR-68 explicitly *rejected* "Inbox" for
the triage gate, on the grounds it "collides with the `inbox/` folder," and chose
"Desk" as a self-describing *room*. We override that here for two reasons: (1) the
room metaphor (Desk/Library/Studio) **broke** once Knowledge and Project gates were
added — those aren't rooms — so "Desk" is now the odd label in a mixed set, not part
of a consistent one; (2) the "collision" is **coherent, not harmful** — the Inbox gate
*is* the `inbox/` queue, so one name for one concept is exactly the
one-name-per-thing rule, not a violation of it, and link resolution is unaffected
(`[[inbox]]`→`inbox.md`; the base is reached as `[[inbox.base]]`). Naming gates after
their content was rejected as a *system* (every domain name — Sources/Claims/Projects
— would clash with a folder/base, and Library/Knowledge each span two collections); we
accept it only for the one gate where the name and the surface genuinely coincide.

**Traceability.**

| Req | Satisfied by |
|---|---|
| R1 job-not-object | §3 gate set derived from JTBD verbs |
| R2 focus / hide rest | dashboard composes only its gate's bases; constant nav (#665/#667) |
| R3 capture global | Commander ribbon carries capture ×3 in every gate |
| R4 one action, keep context | switch = open one note in reused tab; shell never rebuilds |
| R5 ship-in-vault | gates are notes + bases (golden copy); one reset workspace |
| R6 min plugin/risk | drops Workspaces Plus + 2 scripts; no core-surface plugin added here |
| R7 empty/deferred-honest | empty-state copy per dashboard; Studio + telemetry kept out of the alpha.7 set |

**Issues resolved:** #666 (workspace-switching — by elimination), and reinforces the
§5 fixes for #665/#667. **Open:** the single switch-binding verify (§8).
