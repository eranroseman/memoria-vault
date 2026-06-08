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

**Decided:** Workspaces · Bookkeeping · Housekeeping · Vault — cognitive models, not
implementation boundaries (originally named Desk / Store; renamed in D24).

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

## D15 — Three doer-tiers; the Linter is an engine *(→ amends ADR-02)*

**Decided:** three tiers — **engines** (deterministic, no posture, no board: ingest,
Linter, search, retraction sweep), **agents** (posture + LLM, board lanes), and **the
human** (the only promoter). The **Linter is an engine, not an agent**.

**Why:** under "profile = posture" (D8), a zero-LLM, no-judgment tool has no posture, so
it isn't an agent — you *run* a linter, you don't *dispatch* it. This sharpens the old
"seven profiles" into six agents + infrastructure.

**Alternatives weighed:** keep the Linter as a 7th profile (rejected — no posture, never
touches the board).

## D16 — Cataloging splits: ingest engine + Librarian agent *(→ amends ADR-30)*

**Decided:** the mechanical half of cataloging (fetch metadata, extract content, build
entity relationships, create records) is the **ingest engine**; the Librarian **agent**
fills only the two LLM holes (the `[!brief]` + the classification proposal).

**Why:** managing the catalog is mostly mechanical — an engine should do it; the
Librarian's optimistic posture only matters for the judgment-adjacent steps. (ADR-30's
pipeline already works this way.)

## D17 — Relationships (Catalog) vs links (Notes) *(→ amends ADR-08)*

**Decided:** entities carry **`relationships`** (cited-by, authored-by, published-in —
*given* facts, built by the ingest engine); notes carry **`links:`** (supports /
contradicts, hub membership — *authored*, agent-proposes / human-confirms). `links:`
replaces the old `relations:` field.

**Why:** "relationships are given; links are authored" — different in nature, owner, and
gating. The rename also removes the `relations`/`relationships` near-synonym clash.

**Alternatives weighed:** references / connections (rejected — "reference" is
citation-narrow and collides with the dropped reference-note); one "relations" term for
both (rejected — conflates given vs authored).

## D18 — Inbox cards on the universal lifecycle; `review-request` dropped *(→ refines D5/D6)*

**Decided:** inbox cards carry the **universal lifecycle** (`proposed → … → archived`),
not a bespoke vocabulary; the Hermes-native execution `status` stays the hidden mechanic.
There is **no `review-request` type** — a card awaiting the human is just any card in
`proposed`.

**Why:** one state vocabulary the human sees everywhere; "awaiting you" is a *state*, not
a *type*. Card-state and note-state stay disjoint by *category scope* (queries scope to
`inbox/`), not by inventing a second vocabulary.

## D19 — Maturity and agent-recommendation are soft signals *(→ refines D5)*

**Decided:** both are informal 3-tier signals — `maturity` (seedling→evergreen; claim
development) and `agent-recommendation` (inconclusive→clean; a check verdict). Same
*kind*, different *subject*; **distinct values, consistent display**; neither is a gate.

**Why:** they look parallel but measure different things (development vs verdict) — keep
values distinct so a `seedling` claim isn't read as an "inconclusive" check; present
consistently so the human reads them the same way.

## D20 — Reports inform; drafts gate *(→ new)*

**Decided:** a **report** (corpus-map, gap-report, verification-report) is an
agent-generated read-only analysis the human *consults* — regenerable, no approval gate,
surfaces as FYI. A **composition** (draft → deliverable) is human work behind a **gate**.

**Why:** a report isn't promoted to canon — its *findings* become Inbox `gap`/`flag`
cards, but the document itself needs no approval. Conflating the two would gate things
that don't need gating.

## D21 — Two kinds of human decision; classify is automated *(→ new)*

**Decided:** every human decision point is either an **approval gate** (review agent
output → accept/reject) or a **work prompt** (do your own thinking). **classify** is
neither a real gate (low-stakes metadata, rubber-stamp-prone) — so **automate it**
(audited, correctable; flag only genuine ambiguity). The real Read gate is at **distill**.

**Why:** the rule — *an Inbox item a human can clear without reading is a design smell* —
exposes classify as a fake gate; the genuine keep/skip judgment belongs at candidate
triage, and the genuine synthesis judgment at distill.

**Alternatives weighed:** keep classify as a gate (rejected — rubber-stamp);
confidence-tiered auto-accept (rejected, D12).

## D22 — Decision transparency is the primary guardrail *(→ supersedes the anti-anchoring mechanics)*

**Decided:** every approval gate ships the **reasoning — pros, cons, and the verdict** —
so the human judges the *process*, not just the output; and **prefer full automation over
a rubber-stamp gate**.

**Why:** assume anything promoted to the human will be approved. The defensive
anti-anchoring mechanics (blind-first, no-assist sampling) were weaker than simply making
the reasoning legible — transparency lets the human catch a bad *process*, the real
failure mode.

**Alternatives weighed:** blind-first capture + no-assist sampling + rankings-off (kept
only as optional aids; transparency is primary).

## D23 — Skill-naming scheme *(→ new)*

**Decided:** `<activity>:<verb>-<object>` (snake for MCP tools) — verb-first, from a
**closed verb set** (extract · link · summarize · check · rank · draft · outline ·
score); the artifact is the object, with **no result slot**.

**Why:** matches the cross-system convention (fabric, MCP, CLI, Google AIP) — verb-noun +
a closed verb set; the candidate third "result" slot was redundant.

**Alternatives weighed:** `<activity>-<action>-<result>` (rejected — the result slot is
redundant). The `read:`/`write:` prefix is borderline — keep only if an eval shows it
aids selection.

## D24 — Final naming pass *(→ refines D1/D2/D7)*

**Decided:** **Workspaces** (was Desk), **Vault** (was Store; the Obsidian vault),
`catalog/` (named for content, not the Librarian); activities are **Read / Write** only
(drop the Compile/Compose double-name); Bookkeeping/Housekeeping spelled out (no
`book`/`house`).

**Why:** the naming discipline — one name per thing, the word the user would say.
Desk/Store were abstractions; Workspaces/Vault are concrete and already in use.
Compile/Compose was a redundant second vocabulary for Read/Write.

---

## The meta-point

This RFC→ADR pipeline is structurally Memoria's own model: `rfc/explorations` = seeds,
an RFC = a proposed claim, an **ADR = an accepted claim with supersession** (ADR-10 is
literally claim-supersession), the generated index = an MOC, `docs/` = the deliverable.
The meta-work of building Memoria runs on Memoria's discipline.
