# Alpha.3 open issues — best-practice research & alternatives

**Companion to:** [ui-design-research-report.md](ui-design-research-report.md) (resolves its open [ADR]/[FIX] decisions)
**Date:** 2026-06-14
**Method:** web research against authoritative sources (NN/g, Google SRE, Diátaxis, Material Design, DDD, clig.dev, OWASP/MDN, WCAG, GitHub/Obsidian/Django docs). Each issue: cited best practice → alternatives with pros/cons → recommendation.

Sourcing honesty: claims below rest on primary/authoritative sources except where marked *(secondary)*. Three popular "rules" were checked and **rejected** — don't cite them: the NN/g "5-second dashboard" rule (not NN/g), "max 7 items / Miller's 7±2" as a UI cap (NN/g explicitly rejects it for always-visible displays), and the "context-switching = 40% / $450B" figures (vendor blogs only).

A single principle recurs across all four areas and is worth stating once: **prevent/curate at the source; don't clean up after.** SRE "every alert is actionable," NN/g "error prevention > error messages," Diátaxis "one register per page," and forward-link-first note creation are the same idea applied to attention, data, docs, and links.

---

## Issue 1 — Navigation "gates", number of modes, the maintenance question, JTBD dashboards

> Resolves: report §3 (gates→workspaces mapping; is bookkeeping/health its own gate) and §4 (JTBD dashboards).

### 1a. Should navigation be reframed as intent-based "gates"?

**Best practice.** The successful pattern in every mature tool is **"stable center, swappable periphery"** — and, importantly, these are *views/spaces/filters*, **not** true modes. Jef Raskin's definition: a mode is when *the same gesture produces different results* — the dangerous kind that causes "mode errors" ([NN/g modes](https://www.nngroup.com/articles/modes/)). VS Code's Activity Bar, JetBrains tool-window layouts, Obsidian Workspaces, Notion teamspaces, Things/OmniFocus perspectives, Hey's Imbox/Feed/Paper Trail, Superhuman Split Inbox all change *what is shown/scoped* while keeping action semantics constant. The strongest articulated rationale for spaces is **attention/intent routing**: Hey separates mail because different messages "require different engagement levels"; Things visually demotes Someday so you focus on today.

| Alternative | Pros | Cons |
|---|---|---|
| Keep Desk/Library/Studio, reframe as "gates" cosmetically | Zero rebuild; matches Obsidian Workspaces | "Gate" implies an entry decision the always-available tabs don't enforce — metaphor over-promises |
| **Intent-named gates** ("What needs me?", "What should I read?", "What do I know?", "What am I writing?") | Aligns with Hey/intent-based nav; reads as the user's question | Wordier labels; need short glyphs in the rail |
| Workspaces + user-definable custom gates (OmniFocus model) | Ships defaults, grows per-project later | Complexity creep |

**Recommendation.** Adopt **intent-named gates on the existing workspace machinery**. Keep stable-center/swappable-periphery; guarantee a gate switch only changes the left-nav + main dashboard + where the Co-PI points — **never what an action does** (stay in the "safe spaces, not Raskin-modes" zone). This is a reframing + relabel, not a rebuild.

### 1b. How many top-level gates?

**Best practice.** Do **not** cap with Miller's 7±2 (a working-memory recall finding, irrelevant to on-screen recognition; NN/g and UX Myths debunk it). The defensible basis is **Hick's Law** (decision time rises with choices), **cognitive/extraneous load**, and **switching cost** (Leroy's "attention residue"; Gloria Mark's ~23-min refocus). The concrete convergence: **3–5 primary destinations** — Material Design specifies 3–5 for bottom nav (drawer beyond 5); Slack/Notion/Linear constrain primary nav to ~4–5 *(secondary)*. Hold depth with **progressive disclosure**, not more top-level items.

| Alternative | Pros | Cons |
|---|---|---|
| **3 gates now** (Action, Sources, Knowledge) + Project as planned 4th | Lowest switching cost; low end of 3–5; headroom for Project | Maintenance must live somewhere (see 1c) |
| 4 gates now (incl. dedicated Maintenance) → 5 with Project | Each intent a clean home | Hits the upper bound; maintenance gate is mostly ambient work (see 1c) |
| 2 gates + heavy progressive disclosure | Minimal switching | Under-segments distinct intents; risks "too abstract" failure; loses visible-rail discoverability |

**Recommendation.** **3 core gates now, Project as a planned 4th, never exceed 5.** Use progressive disclosure inside each gate. Retire any "7±2" reasoning from the design docs; cite Hick's Law + cognitive load + the Material 3–5 convergence.

### 1c. Should "system health / maintenance" be its own gate? *(the sharp sub-question)*

**Best practice — points clearly one way: ambient by default, escalate only what's actionable.** NN/g's taxonomy: a persistent low-stakes status is an *indicator* (passive, ambient); only a real "act now" event is a *notification*. Google SRE: interrupt only for "a significant event… that consumes a large fraction of the error budget" — unconditional "not-green" surfacing is the documented cause of **alert fatigue**. Calm Technology: tech "should require the smallest possible amount of attention… make use of the periphery." Real tools converge and **none make "everything degraded" a forced destination**: VS Code surfaces problems ambiently (squiggles + status-bar count) with the Problems panel *on demand* (maintainers repeatedly declined to auto-open it); GitHub puts blocking state *at the point of action* (merge box) + a separate triage inbox for the actionable subset; Datadog/Grafana separate pull-dashboards from push-monitors.

| Alternative | Pros | Cons |
|---|---|---|
| Ambient status bar + actionable items flow into the Action/Desk queue (no gate) | Matches every authority; lowest switching; user only switches for real jobs | A deep "show all system state" view needs a home |
| Dedicated Maintenance gate | One obvious housekeeping place | Contradicts ambient-first guidance; spends a slot near the 3–5 ceiling; risks an ignored "wall of yellow"; usually an empty room |
| **Hybrid: ambient status bar + on-demand "Health detail" view (NOT a top-level gate)** | Ambient-first *and* gives power-cleanup a real surface; no slot spent; no forced switch | Slightly more to build (status bar + a pull view) |

**Recommendation.** **Do not make maintenance its own gate.** Use the **hybrid**: ambient status-bar indicator by default; blocking/actionable items appear as cards in the Action/Desk queue (GitHub's point-of-action pattern); a pull-based "Health detail" reached by clicking the status bar for deliberate housekeeping. Spend the freed slot on the Project gate. (This is the most strongly-supported conclusion in the whole research set.) — *This refines report §3, which had floated adding a 4th "Network/ZK" workspace; health should be ambient, and the knowledge/ZK surface can be a gate in its own right rather than a health gate.*

### 1d. JTBD dashboards — which views cluster, frictionless next action

**Best practice.** Design the dashboard's *job* first (Stephen Few: a dashboard is the info needed "to do a job"); organize "the way users think about their work, not how the database is structured." Every widget must pass the **Decision Test** — "what action changes based on this number?" (drop vanity metrics). Kaushik's Action Dashboard pairs each metric with trend + insight + **action** + **owner**. Cluster by audience/decision/task, not data source; put the most action-demanding items top-left. Make the next action frictionless by embedding it **on the card** (Next-Best-Action pattern; Linear/GitHub/Things), not in a remote screen. One real tension (OOUI): people think noun-first for *exploration*, task-first for daily *action* → **task-organized action surface, object-organized exploratory nav**.

| Alternative | Pros | Cons |
|---|---|---|
| One JTBD dashboard per gate, each answering that gate's question | Clean job-per-gate mapping; passes Decision Test by construction | Needs curation to avoid drifting into a data dump |
| **Hybrid (OOUI):** action-first Action dashboard + object-first bases for Library/Knowledge | Matches the documented reconciliation | Two organizing philosophies to keep consistent |
| Single unified home command-center across gates | One place; low switching | Violates "tailor by job / show only what this job needs"; overcrowds |

**Recommendation.** **Hybrid.** Make the Action/Desk dashboard strictly action-oriented (every card = status + next action + one-click control via Buttons; non-actionable items don't appear). Let Library and Knowledge gates lean **object-first** (catalog bases, MOCs/hubs, the note graph) since browsing sources and the Zettelkasten is inherently noun-first. This also resolves 1c: actionable housekeeping shows up as Action cards; ambient health lives in the status bar.

**Forward note for the eventual Project gate:** every authority on thinking/writing work insists it is *non-linear* (Zettelkasten stages skippable; Ahrens calls writing "circular"; NN/g: don't force a wizard when users benefit from non-linear access). Present the project stages (research question → knowledge map → gaps → outline → writing) as **visible stages with free movement**, never an enforced wizard.

---

## Issue 2 — Naming: the deterministic layer, CLI verbs, generic filenames, the work taxonomy

> Resolves: report §7 (engines vs apps; consistent naming; `pipeline.py`; processing-vs-housekeeping taxonomy).
> **Naming convention used below (derived from the definitions, ignoring the current names):** the deterministic layer is **Operations**, split into four self-descriptive categories — **Processing · Integrity · Cleanup · Telemetry**. Rationale in 2a and 2d.

### 2a. The umbrella noun (was "engine" / "app")

**Best practice.** DDD's **Ubiquitous Language**: one term per concept, no synonyms, used identically in code, docs, and conversation; keep a glossary. A dual vocabulary ("engine" *and* "app" for one thing) forces a mental translation table — the textbook anti-pattern. The further test (from the "derive from the definition" pass): the term should be **self-descriptive and commonly understood**. The unifying trait of these components is "deterministic, automated, no LLM judgment" — the opposite pole from *agents*.

| Alternative | Pros | Cons |
|---|---|---|
| **Operations** | Self-descriptive ("the operations the system performs"); neutral on scheduling; clean opposite of "agents" | New term to adopt; folder/ADR churn |
| Keep "engine," delete "app" | Minimal churn (`engines/` + ADR-46 already use it) | "engine" is mildly overloaded (game/search/rules engine); not as plainly self-descriptive |
| Switch to "service" | Industry-standard | Implies an always-on RPC daemon — wrong for on-demand + cron mix |
| Switch to "tool" | Matches CLI/MCP framing | Collides with "MCP tool" → a *new* dual vocabulary |

**Recommendation.** **Adopt "Operations" as the umbrella, delete both "engine" and "app."** It reads cleanly: *"Memoria's deterministic **operations**: Processing, Integrity, Cleanup, Telemetry."* Keep the good existing gloss, reworded: "you *run* an operation, you *delegate* to an agent." (This supersedes the earlier "keep engine" lean — once you derive the name from the definition rather than from the existing folder, the self-descriptive choice wins. If churn is unacceptable, "engine" remains an acceptable fallback, but then still delete "app.")

### 2b. CLI verbs / component naming form

**Best practice.** clig.dev + Microsoft CLI guidance: leaf commands that are *actions on one implicit object* should be **bare imperative verbs** (`git commit`, `cargo build`, `kubectl get`), not gerunds (`ingesting`) or agent-nouns (`ingester`). Be consistent; avoid near-homophones. Memoria's five are actions on one object (the vault) → flat verbs, no `noun verb` nesting needed. The current display names mix forms (Ingest, Search = verb; Clustering = gerund; Verification sweeps = noun phrase; Linter = agent-noun) — that's the inconsistency.

| Alternative | The five | Pros | Cons |
|---|---|---|---|
| **Bare imperative verbs everywhere** | `ingest, search, cluster, verify, lint` | Matches git/cargo/kubectl + MS guidance; shortest; 1:1 with CLI; one token per operation | "cluster" as a verb mildly unusual (fine) |
| Agent nouns (-er) | `ingester, searcher, clusterer, verifier, linter` | "Linter" already this form | `clusterer` awkward; **"Verifier" collides with the retired agent name**; poor as CLI subcommands |
| Gerunds (-ing) | `ingesting, …` | — | MS guidance disprefers; poor as commands |

**Recommendation.** **One token per operation, used as proper name + directory + module stem + CLI verb:** `ingest`, `search`, `cluster`, `verify`, `lint`. Demote "Linter"/"Clustering"/"Verification sweeps" to informal aliases. (`memoria ingest` runs the Ingest operation — cheapest to remember, maximally consistent.) These are the *leaf operations*; the four *categories* they group into are named in 2d.

### 2c. The generic filename `engines/ingest/pipeline.py`

**Best practice.** Generic module names (`utils.py`, `manager.py`, `pipeline.py`) are a recognized anti-pattern: they carry no intent, become entropy sinks, and breed circular deps. Fix = name by **responsibility**. Within `engines/ingest/`, *everything* is the ingest pipeline, so `pipeline.py` says nothing the directory didn't. The sibling files (`extract.py`, `classify.py`, `link.py`, `resolve_merge.py`) are already well-named — `pipeline.py` is the lone offender.

| Option | Pros | Cons |
|---|---|---|
| `runner.py` / `orchestrator.py` (if it's the stage-wiring entry point) | Names the role | Still mildly generic — a step up, not a leap |
| `__main__.py` / `cli.py` (if it's literally `python -m engines.ingest`) | Standard Python convention | Only fits a true entry point |
| `catalog.py` (if it holds the cataloging core; docs call it "the mechanical core of cataloging") | Domain term from your own prose | Possible confusion with the Catalog data model |

**Recommendation.** Inspect what the file *is*: if it sequences the stages, name it `runner.py` (or `__main__.py` if run as a module); if it's the cataloging core, `catalog.py`. Either way **delete "pipeline."** Secondary: `engines/lib/` is the same generic smell — prefer naming by content (the `schema.py`/`inbox.py` inside are fine; consider hoisting them out of `lib/`).

### 2d. The work taxonomy — four self-descriptive categories

The original note (report §7) floated four loose words — *"Processing and maintenance vs bookkeeping and housekeeping."* Two of them ("maintenance"/"housekeeping") are near-synonyms in ops usage, and one ("bookkeeping") is a metaphor; lumping them as two buckets mis-cuts the space. Deriving names from what the jobs **actually produce** (and ignoring the current ones) yields four crisp, commonly-understood categories.

**Best practice.** Background work is widely categorized by its output: **data-flow/ETL** (transform input → usable output), **validation/integrity checks** (confirm data is correct/consistent), **cleanup/garbage-collection** (reclaim and tidy), and **telemetry/auditing** (record activity + metrics). These are four distinct, established vocabularies — not synonyms — so four categories read cleaner than the two-bucket framing. The discriminator that matters for Memoria is **what the PI does with each category's output: use it, act on it, ignore it, or consult it.**

The four categories (each defined by the PI relationship), and the actual jobs that map to them:

| Category | Definition | PI relationship | Jobs |
|---|---|---|---|
| **Processing** | Build & serve the knowledge base (transform sources → structured knowledge; retrieve/analyze) | **uses** the artifact | `ingest`, `search`, `cluster` |
| **Integrity** | Detect & repair correctness/consistency problems; surface findings | **acts on** (cards/alerts) | lint `detectors`, `retraction`, `golden` |
| **Cleanup** | Routine, silent tidying / normalizing / archiving / reclaiming | **never sees** it | `reconcile`/stamp-chats, retry, `archive_inbox` |
| **Telemetry** | Record what happened + emit metrics for later review | **consults** on demand | board+telemetry export, `metrics`, session digests, `eval` |

| Alternative scheme | Pros | Cons |
|---|---|---|
| **Processing · Integrity · Cleanup · Telemetry** (recommended) | Each word is self-descriptive + industry-standard; no two overlap; maps 1:1 to PI relationship and to a UI home | New vocabulary; folder/ADR churn |
| Processing / Maintenance (2 buckets) | Simplest; exactly the MCP-facade boundary | Lumps "findings you act on" with "records you consult" with "silent tidying" — loses the distinctions that drive the dashboards |
| The note's pairing: {Processing+Maintenance} vs {Bookkeeping+Housekeeping} | Clean "substantive vs clerical" line | Splits the synonyms into different buckets; pairs the two genuinely-different ops concepts (record vs tidy); "bookkeeping" is a metaphor |
| Keep "maintenance"/"housekeeping" words | Familiar | They overlap → the merge confusion that prompted this question; not self-descriptive about *what* they do |

**Why four, not three:** earlier I leaned toward collapsing to three (folding housekeeping into maintenance) precisely because "maintenance" and "housekeeping" overlap. **With these names the merge question dissolves** — "Integrity" and "Cleanup" are obviously different work, so four crisp categories are clearer than three. Better names removed the problem that motivated the collapse.

**Recommendation.** Adopt **Operations → Processing · Integrity · Cleanup · Telemetry** as first-class categories. Concretely:

- Add a **category column** to the operations table in the docs.
- Restructure the tree by category: `operations/processing/{ingest,search,cluster}/`, `operations/integrity/{verify,lint,golden}/`, `operations/cleanup/{reconcile,archive_inbox,…}/`, `operations/telemetry/{export,metrics,digests,eval}/`. This *also* fixes the structural inconsistency — it gives **Cluster** a real home (logic moves out of `mcp/cluster_mcp.py`; the MCP file stays as the *facade* only) and gives **Search** a directory.
- The categories line up with everything else: **Processing** carries the MCP facade (agent-reachable); **Integrity/Cleanup/Telemetry** are cron/CI-only. Per the navigation work (Issue 1): **Integrity** → status bar + Action cards; **Telemetry** → pull dashboards (`audit-log`, `fleet-health`, `eval-trend`); **Cleanup** → invisible; **Processing** → the knowledge itself.
- Keep "sweep"/"reconcile" as verbs *inside* Cleanup (correct industry terms). One terminology aside: **"Validation"** is a fine alt for *Integrity*, **"Auditing"** for *Telemetry* if provenance is the emphasis — but the recommended four read best together.

**Zero-contradiction caution:** restructuring `engines/` → `operations/` (and renaming the layer) touches ADR-46 and every doc/path hardcoding `engines/ingest/`, `engines/sweeps/`, etc. — sweep them in the same change, and sequence it *after* the source-link convention (Issue 3c) so links aren't pinned to paths you're about to move.

---

## Issue 3 — Docs: ingest split, ADR-link policy, source-link convention

> Resolves: report §7 (ingest Diátaxis split) and §8 (ADR-link policy; link-to-source convention). **Sequence A before B** — confining ADR links to explanation pages only works once the split creates those pages.

### 3a. Splitting the ingest docs across reference and explanation

**Best practice.** Diátaxis splits on **work vs study**, not subject: reference is "what a user needs… while they are working" (lists/tables, neutral description); explanation is "what someone will turn to… to acquire knowledge" (the "readable in the bath" test). Mixing is a named anti-pattern — it "interrupts and obscures" the reference *and* prevents the explanation from developing. A reference page should also map **1:1** to the thing described (so documenting sweeps inside `reference/ingest.md` is a second, independent defect). Django (the project Diátaxis came from) gives the cross-link rule: **"link to reference material rather than repeat it,"** with reciprocal links — each fact has one home. Rust ships Book (learn) / Reference / API as three artifacts for three reader stances.

| Option | Pros | Cons |
|---|---|---|
| Keep one merged page (status quo) | Zero work; one URL | The exact anti-pattern; sweeps misfiled; not skimmable |
| **Split per concern, one engine per page** (`reference/<engine>` + `explanation/<engine>`; sweeps gets its own pair) | Matches Diátaxis + Django; skimmable; sweeps correctly owned; 1:1 | Most pages; needs a cross-link convention |
| Split reference/explanation but keep engines grouped | Fewer files | Multi-engine reference is harder to consult; weak 1:1; grows unwieldy |
| Reference-only, rationale pushed into ADRs | Minimal surface | ADRs are point-in-time records, not living explanation; readers lose a synthesized mental model |

**Recommendation.** **Split per-concern** for genuinely complex engines (ingest, sweeps), with a light rule that *simple* engines may keep a one-paragraph "Why" inline rather than spawn a near-empty explanation page (Diátaxis "use intuition"). **First action regardless:** move the sweeps material out of `reference/ingest.md`. Adopt **Django's "link, don't repeat"** discipline: rationale lives only on the explanation page; the reference carries a single top-of-page "Background" link; explanation links forward to the procedure.

### 3b. ADR references in user-facing docs

**Best practice.** ADRs are readable by non-developers but are **decision logs, not user docs** — they're the rationale/trade-off layer (the *explanation* register). An inline "(ADR-46)" in a how-to, or worse in a *subheading*, is register-mixing. ADRs also have a lifecycle (proposed → accepted → superseded) that a bare code doesn't reflect; MADR's supersession rule (old record status→superseded **with a forward link**) is the model for any stale pointer. A bare "(D41)" to a deleted doc is textbook **link rot**.

| Option | Pros | Cons |
|---|---|---|
| Inline codes everywhere (status quo) | Cheap; traceable for contributors | Register-mixing; clutters prose; unstable subheadings; breeds stale "(D41)" |
| No ADR refs in user docs | Cleanest prose; ADRs free to evolve | Loses the legitimate "why is it like this?" bridge |
| **Footer "Decisions" section** (titled links) | Diátaxis-clean; one maintained spot per page; auditable; title-text links | Slight per-page curation |
| **Rationale links only from explanation pages** | Confines decision machinery to the rationale register | Requires 3a done first |

**Recommendation.** **Combine the last two.** Keep ADR pointers out of tutorials/how-to/reference body text and especially subheadings. Allow them (a) inline within **explanation** pages and (b) in an optional per-page footer **"Decisions"** section, always as **title-text links** (never bare "(ADR-46)" codes — also satisfies the docs-doctor link-text rule). Treat stale "(D41)"-style refs as zero-contradiction defects: delete them, or apply MADR supersession with a forward link. docs-doctor's link check catches new breakage.

### 3c. Referencing source code from the docs site

**Best practice.** GitHub's own guidance: branch-tip URLs can change under you; press **`y`** to get a **commit-pinned permalink** (SHA) that "will not change." Community consensus: share commit-hash links for permanence; branch links are a deliberate "evergreen" exception. Trade-off is **permanence vs freshness**, and **line anchors drift hardest** (any edit above shifts them). Mature toolchains *auto-generate* source links (Sphinx `linkcode`, "View on GitHub") — **just-the-docs has no equivalent**, so Memoria needs a manual convention.

| Option | Pros | Cons |
|---|---|---|
| Relative links to `src/` (a current practice) | Works in local editor/repo view | **Breaks on the live site** — `src/` isn't published. Never use for rendered docs |
| **Inline code-span path** (`` `src/...` ``) | Never rots; zero maintenance; survives renames as approximate locator | Not clickable |
| `blob/main/…` hyperlink | Always current; clickable | Silently breaks on rename/delete; line anchors drift; not reproducible |
| **`blob/<sha>` or `blob/<tag>` permalink** (`y` key) | Stable; reproduces exactly the code described | Goes stale as code moves; SHAs ugly; needs periodic refresh |
| Build-time auto-linking (Sphinx-style) | No hand-maintenance; never stale | Not native to just-the-docs; build a plugin/CI step; overkill now |

**Recommendation (two-tier; matches report §8).** **Default: inline code-span path** for the common "the implementation lives at `src/…`" case — lowest-maintenance, never-rots, survives the §7 renames. **When a clickable, line-precise link genuinely adds value:** a **tag-pinned permalink** (`blob/0.1.0-alpha.3/…`) so each doc version points at matching code — the middle ground between `main` (drifts) and a raw SHA (opaque). Avoid `blob/main` for anything line-specific; reserve it for "browse this directory" links. Defer build-time auto-linking until the API surface justifies it. (docs-doctor now flags published→`src/` relative links as advisories — promote to error after the sweep.)

---

## Issue 4 — home.md: status glance, structured capture/enforcement, linked-note button

> Resolves: report §4 (status glance), §2 (capture forms + enforcement), §6 ("create linked claim note" button).

### 4a. Status-glance / "what needs me"

**Best practice.** **Surface only what's actionable** (Google SRE: "every page should be actionable"; if the response is automatable, it shouldn't appear on a human surface — that's the Co-PI's job). **Scope by relationship** ("involves me" — Linear/GitHub `reason:`). Treat it as a **queue emptied by deciding**, with a finite action set (Inbox Zero's Delete/Delegate/Respond/Defer/Do; Linear Triage's Accept/Decline/Merge/Snooze). **Make every number drillable** (NN/g: reveal detail without leaving the screen). Prefer **actionable over vanity** counts. **Status badges: never color alone** (WCAG 1.4.1 — pair color with icon/text; Datadog/Grafana name discrete states). No rigorous indicator cap exists; "3–10, keep under 10" is vendor guidance *(secondary)* — cap by **actionability**, not a number.

| Alternative | Pros | Cons |
|---|---|---|
| Single count line (current) | Minimal; fast scan | Counts without context risk vanity; not obviously clickable |
| **Clickable count line + severity icon** | Drillable; WCAG-safe; still one line | Small build (links + filtered views) |
| "What needs me now" curated item list | Every item actionable; forces decisions | Longer; needs ranking; heavy on launch |
| Hybrid: glance line + collapsible triage queue | Fast scan + one-click triage; snooze first-class | Most build; two focal points |

**Recommendation.** **Clickable count line + severity icon now; evolve toward the hybrid.** Each number links to a filtered view; each gets an icon+text badge (WCAG-safe). Apply the SRE actionability test: an indicator earns its place only if non-zero prompts action — suppress anything the Co-PI should auto-handle. Add a first-class **snooze/defer** (the one noise-reducer common to Linear/Things/OmniFocus/GitHub/Superhuman).

### 4b. Structured capture + schema enforcement

**Best practice.** **Constrain at entry; prevention > detection** (NN/g Heuristic #5; poka-yoke "control beats warning"). **Controlled vocabularies kill typos** — and pick the right control by option count: **≤5 options → radio buttons** (not a dropdown), 5–15 → dropdown, 15+ → listbox. So a 3-value lifecycle (proposed/current/archived) is best as **radio buttons**. *(This refines the earlier dropdown answer: native Obsidian still has no enum type, but at 3 values radios are the better control where the UI allows them; Modal Forms supports both.)* Keep **help text in the form, not the saved note** (the core reason a form beats a markdown template). **Enforce in both places:** client form for UX, server validator as authority ("never trust the client"; OWASP: validate server-side; treat an out-of-set value as a tamper signal). "Parse, don't validate" at the boundary; "make illegal states unrepresentable"; be **strict, not liberal** for internal schemas you own (RFC 9413 — Postel's robustness principle is now considered harmful). **Derive form + types + validator from one schema** so layers can't drift.

| Option | Pros | Cons |
|---|---|---|
| Lint only (status quo) | Simple; one authoritative point | Detection not prevention; bad data exists transiently; help text leaks into notes |
| Form only (Modal Forms) | Prevents bad entry; help text stays out; pleasant | Client-side = bypassable; misses notes created by Co-PI/API/bulk |
| Form + Lint (defense in depth) | OWASP client-UX + server-authority; covers non-form paths | Two layers can drift |
| **Form + Lint + one shared schema** | Layers can't contradict; closest to illegal-states-unrepresentable; one place to evolve vocab | Most upfront engineering |

**Recommendation.** **Target Form + Lint + shared schema; ship Form + Lint first.** Keep the deterministic **Linter as authority** (Co-PI/API/bulk all bypass any form). Add **Modal Forms** for human capture (prevention + help-text-stays-out); use **radio buttons** for the 3-value lifecycle; progressive disclosure for advanced fields. Then drive both the form's vocabularies and the Linter's allowed-values from **one per-type schema** (you already have `.memoria/schemas/`), so the two layers can't diverge. Metadata Menu's `fileClass` typed-field model is a strong reference / possible accelerator. — *Matches report §2's "keep enforcement in the Linter, use forms for entry"; the new precision is radios-over-dropdown and the single-schema binding.*

### 4c. "Create a linked claim note from a source"

**Best practice.** **Forward-link-first** creation (the backlink exists before the note): Obsidian Ctrl/Cmd-click on `[[New Note]]` creates it already linked; Roam/Logseq auto-create from `[[ ]]`. **Templated child + backlink in one command:** QuickAdd's Template choice creates from a template with computed filename/folder, opens it, and **inserts a link back into the current note**; a QuickAdd **Macro** chains it into one hotkey; Buttons can fire that macro. **Split/extract** an existing claim: Obsidian's Note composer extracts a selection into a new note and replaces it with a link. **Typed child creation** (the aspiration): Tana supertags instantiate a typed-field template; Notion relations are bidirectional.

| Option | Pros | Cons |
|---|---|---|
| Bare forward-link (`[[claim]]`, Ctrl-click) | Zero plugins; native; backlink pre-exists | Blank note (no schema/frontmatter); manual naming |
| Buttons → "New Note From Template" | Visible affordance; one click; templated frontmatter | Limited templating; doesn't auto-write the backlink |
| **Buttons/command → QuickAdd Macro** | True one-click spawn+backlink; computed path; templated; opens note | Two plugins to configure |
| Button → Modal Form → Templater create | Structured (ties to 4b); valid-by-construction; help text in form | Most moving parts; heavier for a quick claim |

**Recommendation.** **Buttons → QuickAdd Macro as the default; Modal Form variant for the structured path** (same trigger). Put a button in the source note that fires a macro: create the claim from a template (correct frontmatter), compute its path, **insert a wikilink back into the source**, open it — the canonical one-click "spawn + backlink." Because a claim is a *typed* object, route the template through the same per-type schema as 4b (button opens a Modal Form for the claim's fields) so it's valid-by-construction — the Tana-supertag / Notion-relation model adapted to Obsidian. Keep the bare forward-link as the no-friction fallback (Linter flags missing frontmatter later).

---

## The reusable building block

The single highest-leverage artifact across these issues is **one per-note-type schema** feeding three places: the **capture form** (4b), the **Linter** (4b), and the **claim-creation button's template** (4c). One definition, three enforcement/affordance points — that's what turns "form + lint" from two bug surfaces into one, and makes the linked-note button produce valid notes by construction.

## Sequencing notes

- **Docs:** do **3a (split) before 3b (ADR-link policy)** — confining ADR links to explanation pages needs those pages to exist.
- **Operations:** if you adopt the `Operations → Processing/Integrity/Cleanup/Telemetry` tree (2a/2d), sweep ADR-46 + all hardcoded `engines/...` doc paths in the same change; do the source-link convention (3c) sweep *after* the operation renames (2b/2c) so you don't pin links you immediately break.
- **home.md:** the shared-schema work (4b) unblocks the best version of the linked-note button (4c).
