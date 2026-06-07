---
topic: proposals
title: Memoria redesign — decisions & rationale
status: exploration
created: 2026-06-07
---

# Memoria redesign — decisions & rationale

The decision-journey stripped from [memoria-redesign.md](memoria-redesign.md) (which
is design-only). Each entry records **what** was decided, **why**, and the
**alternatives weighed** — the material an ADR needs. As each firms up, graduate it to
`project/adr/NN-*.md` and set `superseded_by` on the ADR it replaces. Ordered by
topic, not chronology.

---

## D1 — Four-layer cognitive model *(→ supersedes ADR-01)*

**Decided:** Desk · Bookkeeping · Housekeeping · Store — cognitive models, not
implementation boundaries.

**Why:** the layer first called "Research/Production" actually describes the *agent's*
bookkeeping *between* human actions — not the human's research, which happens at the
**Desk** (workspaces). Separating the two agent-bookkeeping kinds matters:
**Bookkeeping** *processes knowledge* (trigger = a human action); **Housekeeping**
*maintains the substrate's integrity* (trigger = human · agent · cron; deterministic,
zero-LLM, CI-gateable). The "-keeping" pair is a memorable cognitive distinction.

**Alternatives weighed:** the original three layers (board/workers/vault, ADR-01);
naming the agent layer "Research" (rejected — it mislabels agent work as the human's);
merging bookkeeping + housekeeping (rejected — different triggers, determinism, and
purpose; the separation is the cognitive model, not a technical one).

## D2 — Type-first folders, four categories *(→ supersedes ADR-04)*

**Decided:** top-level folders by **category** (Catalog · Notes · Projects · Inbox +
System); **one folder never mixes two categories**; no lifecycle numbers.

**Why:** the entity/note/artifact/signal distinction is real and should be structural.
Direction (`10-…50-`) implied a pipeline, but the knowledge is a **network**;
direction now lives in the **state property**, not the folder name (also more
ZK-faithful — ZK has no folder ordering).

**Alternatives weighed:** lifecycle-numbered folders (ADR-04); keeping topic out of
folders is retained (topic stays in frontmatter).

## D3 — Entity/note split; Catalog in Obsidian Bases *(→ new; amends ADR-30)*

**Decided:** **entities** (paper/person/org/venue/dataset/repo) are structured records
in **Obsidian Bases**; **source-notes** are prose. Cataloging produces two outputs:
mechanical (entities + links, agent) and interpretive (the source-note).

**Why:** `paper-note`/`item-note` were entity-note hybrids — a standing source of
tension. The split revives Luhmann's two-box system (bibliographic index vs main
slip-box). Bases chosen because it honors the plain-text/git/lintable/in-Obsidian
discipline; its lack of integrity guarantees is **exactly what Housekeeping (Linter
`schema-check`) supplies**, so the one con is covered natively. Validated by the mature
Zotero + Better BibTeX + ZotLit → frontmatter-notes → Bases workflow (= the Librarian
intake).

**Alternatives weighed:** SQLite / JSON / NoSQL / graph-DB as the store (rejected —
opaque, not git-diffable, outside the plain-text discipline; a derived SQLite *index*
is fine at scale but never the source of truth); keep the hybrid note (rejected). One
source-note type with a `source_type` property replaces paper/item notes.

## D4 — Drop the `reference` note type *(→ new)*

**Decided:** remove `reference`; an `evergreen` `claim` is the settled unit.

**Why:** "reference note" in ZK *means* the literature note (= our `source`), so the
term collided; and a separate "settled" claim subtype **double-encoded maturity**
(D5). Dropping it removes complexity without losing anything.

## D5 — Universal lifecycle chain; maturity as a property *(→ new)*

**Decided:** one chain for knowledge/data — `proposed → provisional → current →
retracted → archived` (each type a subset). **Maturity** (`seedling → budding →
evergreen`) is a **claim property**, not a second state axis. `archived` is a state,
not a folder.

**Why:** one state vocabulary is a simpler mental model. State asks "how trusted?";
maturity asks "how developed?" — orthogonal, and maturity only varies on claims and
gates nothing, so it's a property. `retracted` chosen over `quarantined` (better word;
covers retracted sources and withdrawn claims). The **board's** states
(`status`/`review_status`) stay **disjoint** from this chain by design.

## D6 — Inbox as the agent→human message category *(→ new; amends ADR-17)*

**Decided:** **Inbox** category holds agent→human messages by type (candidate · gap ·
flag · review-request · alert); the kanban board and the queue dashboards are *views*
of it. "Card" is the kanban rendering, not the category.

**Why:** it makes the **signal** end of the `trigger → lanes → signal` loop
first-class, and stops overloading "card." A `gap-report` (a document) is distinct from
a `gap` (an Inbox message). `candidate` (have-a-source) vs `gap` (need-a-source) are
different stages of intake.

**Alternatives weighed:** "Signals" as the name (renamed to Inbox); treating "artifact"
as one category (rejected — Projects and Inbox are separate categories).

## D7 — Read / Write activity spine *(→ new; includes CURATE-first)*

**Decided:** two activities — **Read** (Compile: ①②③ sort·read&note·connect) and
**Write** (Compose: ④⑤⑥ plan·write·check). Applied consistently (workspaces, phase
groups, assist grouping). CURATE is **first** (the multi-fed entry).

**Why:** the phone test — "I'm reading" / "I'm writing" — symmetric, dignified,
phone-natural, and non-overloaded. CURATE-first makes "phase 2 fires on phase 1's
output" explicit and treats the one multi-fed node as the (rightly multi-fed) entry,
removing the hidden wrap that CURATE-last needed.

**Alternatives weighed:** Study/Write (Study sounds studenty); Research/Write (overloads
the "research vault" identity — "research" reserved for the practice); think/write;
CURATE-last (fewer backward arcs but hides the trigger); CURATE as an unnumbered hub.

## D8 — Team-role profile naming *(→ amends ADR-02)*

**Decided:** name agents by the team role you'd hire — **Librarian · Analyst · Writer
· Fact-checker · Engineer** (colleagues); **Socratic** (thinking-partner, a method
name); **Linter** (a tool, kept).

**Why:** self-explanatory via the "who would I hire?" test. The naming *teaches the
model*: colleagues get human roles; the Desk thinking-partner gets a method name; the
maintenance utility gets a tool name (you don't hire someone to lint — you run a
linter).

**Alternatives weighed:** Mapper (→ Analyst, names the value not the artifact);
Verifier (→ Fact-checker); Coder (→ Engineer); Linter→Copyeditor (rejected — copyediting
is prose, Linter is structural integrity); Socratic→Critic/Interlocutor (kept Socratic
— the user preferred it; it names a known method).

## D9 — Socratic is a Desk partner, not a board lane *(→ aligns with board states)*

**Decided:** Socratic assists *at the Desk* (ACP pane), in the moment; it is **not** a
Bookkeeping lane and never appears on the board.

**Why:** write-denied and conversational; its product is the human's sharpened
thinking, not a `done` card. The kanban-board docs independently state "Socratic is not
a board lane" — the redesign and the existing architecture agree.

## D10 — Homepage: above-fold "what needs me" + progressive disclosure *(→ amends ADR-13)*

**Decided:** Home stays a consumer-only launchpad; above the fold = the **Inbox
summary** ("what needs me?"); below = collapsible detail dashboards.

**Why:** preserves visual-discipline (calm, ~30-second glance) while giving depth on
demand; single-source-of-truth (Home embeds, never computes).

**Alternatives weighed:** all dashboards embedded inline (buries the glance); pure
launchpad with only links (no overview); per-workspace only (no single overview).

## D11 — The in-vault pattern library *(→ new)*

**Decided:** assist "Patterns" are curated prompt-transformations stored as markdown in
**`system/patterns/`** (visible, lintable, git-tracked — *not* `.memoria/`, which is
hidden runtime). Runner in-vault; invocation via palette · pane · selection; per-pattern
model with a global fallback.

**Why:** fabric "patterns" / open-notebook "transformations" *are* the assist skills —
adopt the toolkit, not a new mechanism. Borrow the affordances; reject the
chat-with-docs epistemic model (the "synthesis without rigor" failure Memoria prevents).
Patterns are propose-class (output to staging, human disposes) and themselves gated
assets (human-authored or agent-proposed→human-approved). Seeded by adapting fabric
patterns.

## D12 — No confidence-tiered auto-accept *(→ reinforces ADR-03 / ADR-21)*

**Decided:** drop the proposed `classification-confidence` auto-accept tier; the gate
stays structural and uniform (propose-not-dispose).

**Why:** the docs are explicit — "confident-wrong is the failure mode; confidence-routing
would wave through exactly the outputs the gate exists to catch." Optimistic proposals
are safe because they land in the `_proposed_*` namespace, not because of a score.

## D13 — Most proposed "new components" dissolve into existing mechanisms *(→ design note)*

**Decided:** the original Part-2 component list (validation status, visible modes,
notifications, etc.) is mostly *not* new — re-deriving each problem from
`docs/explanation` shows Memoria already solves it:

- operating surface → visual-discipline + status-line + dashboards (not a mode machine)
- graded loudness → the existing `LOW/MED/HIGH/CRITICAL` severity ladder → channel
- attention routing → dashboards that mirror where the cycle stalls
- truth vs settledness → promotion ⟂ maturity (already two axes)
- non-monotonic knowledge → `superseded_by` + `retracted` + archive
- provenance at decision → the audit-log dashboard
- near-ties → "flag, don't fix" + "informational, never blocking"

**Genuine residue:** the retraction trigger (R1), generalized near-tie surfacing (R2),
the pattern library (D11). The lesson: re-derive from existing philosophy before
importing generic patterns.

## D14 — Dashboards reconciled: Inbox = action queue, dashboards = browse views *(→ design note)*

**Decided:** the Inbox is the *action queue* (discrete things needing you now);
dashboards are *browsable health views* (where things stand). `daily-health` dissolves
into the homepage; `board-state` becomes the Inbox board; `open-questions`/`contradictions`
are the human's synthesis backlog (Read/Write) while `loose-ends`/`drift-watch` are the
Linter's structural debt (Housekeeping) — kept separate **by layer**, not collapsed.

---

## The meta-point

This RFC→ADR pipeline is structurally Memoria's own model: `rfc/explorations` = seeds,
an RFC = a proposed claim, an **ADR = an accepted claim with supersession** (ADR-10 is
literally claim-supersession), the generated index = an MOC, `docs/` = the deliverable.
The meta-work of building Memoria runs on Memoria's discipline.
