---
topic: explorations
title: Memoria redesign — decisions & rationale
status: exploration
created: 2026-06-07
parent: Design notes
grand_parent: Explanation
nav_order: 12
nav_exclude: true
---

# Memoria redesign — decisions & rationale

The decision-journey stripped from [Memoria redesign — architecture](memoria-redesign.md) (which
is design-only). Each entry records **what** was decided, **why**, and the
**alternatives weighed** — the material an ADR needs. As each firms up, graduate it to
`docs/adr/NN-*.md` and set `superseded_by` on the ADR it replaces. Ordered by
topic, not chronology.

---

## D1 — Four-layer cognitive model *(→ supersedes ADR-01; collapsed to two layers + actors in D25)*

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

## D8 — Team-role profile naming *(→ amends ADR-02; consolidated by D26/D27)*

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

## D15 — Three doer-tiers; the Linter is an engine *(→ amends ADR-02; renamed "actors" in D30, layers collapsed in D25)*

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

## D22 — Decision transparency is the primary guardrail *(→ supersedes the anti-anchoring mechanics; card schema in D35)*

**Decided:** every approval gate ships the **reasoning — pros, cons, and the verdict** —
so the human judges the *process*, not just the output; and **prefer full automation over
a rubber-stamp gate**.

**Why:** assume anything promoted to the human will be approved. The defensive
anti-anchoring mechanics (blind-first, no-assist sampling) were weaker than simply making
the reasoning legible — transparency lets the human catch a bad *process*, the real
failure mode.

**Alternatives weighed:** blind-first capture + no-assist sampling + rankings-off (kept
only as optional aids; transparency is primary).

## D23 — Skill-naming scheme *(→ new; prefix changed to task in D31)*

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

## D25 — Collapse to two layers + three actors *(→ refines D1/D15; build-view stack in D36)*

**Decided:** the model is **two structural layers** (Workspaces · Vault) + **three
actors** (engines · agents · the human). "Bookkeeping" and "Housekeeping" are no longer
layers — they're *what* the agent and engine tiers *do*.

**Why:** the four-layer model made the Linter both "the Housekeeping layer" *and* "an
engine" — a redundancy. Layers answer *where* (Workspaces, Vault); actors answer *who*.
The process-vs-maintain distinction the old `-keeping` pair carried is carried by the
agent-vs-engine split instead, with no parallel taxonomy.

**Alternatives weighed:** keep the four layers (rejected — the layer/tier doubling *is*
the confusion); keep "Housekeeping" as the engine tier's function name only (rejected —
half-measure, two names floating).

## D26 — One co-PI fronts everything; specialists are background lanes *(→ refines D8/D9)*

**Decided:** the human converses with **one agent — the co-PI** — and **delegates** tasks
to the background lanes. The co-PI is the desk partner and **subsumes Socratic**; the
specialists are never separate chats.

**Why:** "who do I talk to?" was the multi-agent pane's core confusion. Concentrating
every conversation in one agent lets it own Hermes' self-improving loop (memory · /goals ·
skills), where it compounds into a true co-PI; the background lanes stay stateless
propose-then-dispose executors. Socratic was already desk-only, write-denied, and off the
board — a natural fold-in.

**Alternatives weighed:** co-PI + a few directly-conversable specialists (rejected for now
— reintroduces "who do I talk to", splits the loop; revisit if a specialist conversation
proves necessary); the status-quo 4-agent pane (rejected — the confusion this fixes).

## D27 — Profiles consolidate to three postures + Engineer *(→ amends D8; renamed Librarian/Writer/Fact-checker in D34)*

**Decided:** three background postures — **Process** (catalog · extract · link · map; the
merged Librarian + Analyst), **Write** (draft), **Verify** (independent judgment) — plus
**Engineer** (code, kept), plus the co-PI. Cut by **posture**, not by task.

**Why:** under "profile = posture", catalog/extract/link/map share one *faithful* stance,
so they're one profile running four lanes — not four profiles. Writing (generative) and
verifying (skeptical, independent) are genuinely different postures, so they stay separate;
Engineer's narrow code scope is orthogonal.

**Alternatives weighed:** keep the five specialists (rejected — artificial catalog→map
handoffs, more to maintain); two postures, Researcher + Verify (rejected — collapses
generative writing into faithful research, too broad a write-scope).

## D28 — Fact-checker splits by determinism *(→ refines D15/D27)*

**Decided:** the old Fact-checker splits along the determinism line — the **deterministic
sweeps** (retraction, near-duplicate, broken-citation) become **engines**; the **judgment
checks** (cite-check, claim-trace) become the independent **Verify** agent. Verify is
**not** merged into Process.

**Why:** deterministic→engine, judgment→agent is the same rule as D15. And verification
independence is a deliberate safeguard — the agent that synthesizes must not also grade
its own work (separation of duties; the anti-rubber-stamp logic behind the three review
dimensions). Merging Verify into Process would break that.

**Alternatives weighed:** merge Fact-checker's bookkeeping into Process, sweeps → engines
(rejected — breaks independence); keep Fact-checker standalone spanning book/house
(rejected — the "· book/house" awkwardness; deterministic sweeps need no posture).

## D29 — One working surface, two perspectives *(→ refines D7/D24; perspectives named Library/Project in D33)*

**Decided:** **Read** and **Write** are two **perspectives** (saved layouts) on **one
working surface** plus Home — not two walled-off workspaces. Every task is reachable from
both via the palette. The "six phases" framing is dropped — there are two activities and
six **delegable tasks**.

**Why:** reading and writing interleave too tightly for a hard wall (you write notes while
reading, read claims while writing). The perspective keeps ergonomic focus without
switch-friction; "phase" wrongly implied a pipeline the human walks.

**Alternatives weighed:** two hard workspaces (rejected — switch-friction, two layouts);
one undifferentiated surface (rejected — loses reading-vs-writing ergonomics).

## D30 — "actors" is the tier term *(→ renames D15's doer-tiers)*

**Decided:** the three tiers are **actors** — engines · agents · the human (replacing
"doer-tiers").

**Why:** "actors" carries the UML/actor-model lineage (who performs the action), is
self-teaching, and naturally includes the human; "workers" is taken (Hermes lanes).

**Alternatives weighed:** doers (kept as a plain fallback); operators (implies
runtime-ops); performers (theatrical).

## D31 — Task-prefix skill naming *(→ refines D23)*

**Decided:** skill names are **`<task>:<verb>-<object>`** — the prefix is the **task/lane**
(catalog · extract · link · map · draft · verify · find · search), not the activity. E.g.
`verify:check-citation`, `catalog:enrich-record`, `search:find-source`.

**Why:** the `read:`/`write:` activity prefix was too coarse to disambiguate; the task
prefix matches the board card / lane, so a skill's name says which task delegates it.

**Alternatives weighed:** `<activity>:` prefix (D23 — rejected as too coarse); no prefix
(rejected — loses the lane signal).

---

## D32 — The human's role name is the PI *(→ new; locks the §10 naming-open)*

**Decided:** the human in charge is **the PI** (Principal Investigator); *"human-in-the-loop"*
stays the design **concept**, "PI" is the **role**.

**Why:** "co-PI" requires a referent — `co-` is meaningless without a PI, so naming
coherence is near-decisive. "PI" is agentive and accountable (the human-in-charge
principle), where "human/user" is a passive role label.

**Alternatives weighed:** "the human" / "user" as the role name (kept only as the
interaction-paradigm *concept*, not the role). [Shneiderman, *Human-Centered AI*.]

## D33 — Library / Project perspectives *(→ refines D29)*

**Decided:** the two perspectives on the one working surface are **Library** (the *Read*
surface — sources, catalog, notes) and **Project** (the *Write* surface — canvas, outline,
draft). The **activities stay Read / Write**; "the Library" is retired as a nickname for
the **Vault** to clear the collision.

**Why:** concrete, domain-apt names beat the bare verbs for the *surfaces*, while the verbs
remain the activity spine (D7). Two distinct vocabularies — activity vs surface — map 1:1.

**Alternatives weighed:** Read/Write as the perspective names (rejected — bare verbs; kept
as activities); Sources/Project.

## D34 — Librarian for the unified processing agent *(→ amends D27; verify agent renamed Peer-reviewer in D38)*

**Decided:** the consolidated processing posture is named **Librarian** (not "Process").
For coherence **Writer** and **Fact-checker** re-attach too. **Agents are role-named**
(co-PI · Librarian · Writer · Fact-checker · Engineer); **lanes/tasks stay function-named**
(catalog · extract · link · map · draft · verify · code).

**Why:** a research/reference librarian does *both* intake and lit-search/gap-analysis, so
"Librarian" is accurate for catalog+map and more thematic than "Process"; consistent with
D8's "who would I hire?" naming. The D27 *consolidation* is unchanged — only the name.

**Alternatives weighed:** functional names Process/Write/Verify (rejected — bland, and
inconsistent with the colleague-name philosophy); keep Librarian alone but leave
Write/Verify functional (rejected — mixed register).

## D35 — Recommendation-card schema *(→ refines D22)*

**Decided:** every approval-gate item uses **BLUF + progressive disclosure** in three tiers
— **Glance** (recommended *action* · verdict + one-line justification · *impact* ·
*certainty*) · **Reasoning** (why-impact · reasons-for · reasons-against ·
what-it's-uncertain-about · provenance) · **Consequences** (if-accept · if-reject ·
reversibility · alternatives). The **Toulmin** model is the spine (claim · grounds ·
warrant · backing · qualifier · rebuttal). **Impact and certainty are 3 levels each,
labelled by action** ("act now / later / skip"), never a numeric % scale. Clearing the
gate **requires expanding the rebuttal**, not just reading the verdict.

**Why:** the original element set was all verdict-side and missed five action-side elements
(action, provenance, reversibility, uncertainty, alternatives). BLUF + progressive
disclosure fits the visual-discipline glance→expand; 3 action-labelled levels suit a single
uncalibrated rater and dodge the middle-bin trap; **handing a verdict induces automation
bias** (people scrutinise less), so gate on the rebuttal and present for/against
symmetrically (inform, don't persuade).

**Alternatives weighed:** verdict-only or >3-level / numeric scales (rejected); a
reasons-for-only gate (rejected — automation bias). [NIST IR 8312; Tintarev & Masthoff
2012; Preston & Colman 2000; the Toulmin model.]

## D36 — Seven-layer system architecture; MCP is a policy boundary *(→ complements D25; sandbox model in D40, engine invocation in D41)*

**Decided:** adopt a **seven-layer build/runtime stack** (PI · Interface · co-PI · Tasks ·
MCP · Engines · Vault) with the principle **decisions flow top-down, information bottom-up**.
It *complements* — does not replace — the D25 cognitive model (two layers + three actors);
they map one-to-one. **MCP is the agent sandbox boundary, but a *policy/permission* gate,
not an *execution* sandbox.** Detail: [Memoria system architecture — the seven-layer stack](system-architecture.md).

**Why:** the stack makes the MCP trust boundary and the co-PI/tasks split explicit, which
the cognitive model folds away. Two *named* lenses (cognitive vs build) avoid the
layer-model competition D25 fixed. The policy-vs-execution caveat is honest about what MCP
alone provides (process isolation, if wanted, is a separate boundary).

**Alternatives weighed:** a single layer model (rejected — D25 showed competing cognitive
models confuse); rename engines → "apps" (rejected — collides with "MCP apps").

## D37 — Batch-worklist pattern; reports are project artifacts; one unified inbox *(→ refines D6/D20)*

**Decided:** **high-cardinality per-item decisions live in a batch worklist, not N inbox
cards.** A report that lists many items each needing a keep/reject call (relevance scan,
lit-search) **is** the review surface — a Bases-backed worklist where each row carries a
lifecycle `decision` the PI toggles, at group or item granularity; the Inbox gets **one
aggregate work-prompt**. Reports are **project artifacts** (`projects/<p>/reports/`),
browsed in the Project perspective; there is **one global Inbox** with project-scoped
*views*, not per-workspace inboxes.

**Why:** dozens of atomic cards flood a queue meant to converge to zero and are exactly the
"clear-without-reading" smell (D21); a worklist is the systematic-review screening model
(Rayyan/Covidence). Reports inform, they aren't promoted (D20). Unified-inbox-plus-views is
the dominant notification UX (one source of truth + filters) over siloed inboxes.

**Alternatives weighed:** one card per item (rejected — flood + rubber-stamp);
per-project inboxes (rejected — fragments attention, multiple unread counts). [PRISMA;
synthesis matrix; NN/g inbox pattern.]

---

## D38 — The verify agent is the Peer-reviewer (not Fact-checker) *(→ amends D34)*

**Decided:** the independent verification agent is named **Peer-reviewer**. Agents stay
role-named; the **lane stays `verify`**.

**Why:** for a research vault, peer review is the **native pre-publication quality-gate
metaphor**, and it completes the **PI · co-PI · Peer-reviewer** triad (the same thematic
instinct as D32/D34). It also matches **scope** — the agent judges *soundness*, not just
facts: a claim can be well-cited yet unsound, which is peer review, not fact-checking. And
it cleanly **separates the two red-teams**: the co-PI is *informal, continuous* sparring;
the Peer-reviewer is the *formal, independent* gate (⑥ certify).

**Alternatives weighed:** **Fact-checker** (journalism — precise to cite-check/claim-trace
but undersells soundness, and a mixed register against PI/co-PI); **Verifier** (the pre-D8
functional name — agents get role names, not tool names); **Editor** (editors *fix*,
violating flag-don't-fix; overlaps the Writer and the Linter); **Reviewer** (too generic;
clashes with the board's `review_status`). [Tolerable cost: minor `review_status` overlap.]

## D39 — The project workflow (v0.2) *(→ new; defines §3 Projects / the Project perspective)*

**Decided:** the Project workflow is defined for **v0.2** as phases 1–5 —
**brief → relevance scan → lit-search → canvas → outline** — each with a per-phase agent
chosen by posture: *brief* = co-PI (+ Writer for prose); *relevance scan* & *lit-search* =
Librarian (`map`/`find`, surfaced as batch-worklist reports, D37); *canvas* =
Librarian-seeds / PI-authors; *outline* = Writer, a **one-way seed** from the canvas.
**Write · code · verify (phases 6–8) are sequenced but v0.3** (not yet detailed). Detail:
[Memoria redesign — architecture](memoria-redesign.md) Appendix H.

**Why:** the brief is the cascade root (get it wrong and every later phase inherits the
error), so it's deep co-PI work, not a delegated task; relevance/lit-search are faithful
Librarian processing presented as screening worklists; the canvas is the ZK connecting
phase (PI-authored); the outline seeds once because two-way canvas↔outline sync is
high-cost, low-value. The Librarian + Analyst merge (D27/D34) holds across all five — one
faithful-processing posture.

**Alternatives weighed:** RQ-formulation as a Librarian task (rejected — generative/
dialogic, belongs to co-PI/Writer); two-way canvas↔outline sync (rejected — complexity);
detailing write/code/verify now (deferred to v0.3 — not yet specified).

## D40 — Sandbox model: policy-via-MCP baseline; execution isolation only for untrusted code *(→ refines D36)*

**Decided:** under the **solo, local premise**, "sandboxed" means **policy-sandboxed via
MCP** — allow-listed tools, vault-path-scoped writes, validation, logging — which, with
propose-not-dispose + the gated zones + the SHA-256 audit log + git, is the right guard for
first-party agents. **No process/execution isolation** for Memoria's own agents. Execution
isolation (container / separate OS user) applies **only to untrusted third-party code** (a
community MCP server, the Engineer's external coding agent) and is **deferred** until such
code is actually run.

**Why:** the threat model for one trusted user on their own vault isn't tenant-escape — it's
*wrong writes*, covered by the policy gate + gate + git. Process isolation is multi-tenant
hygiene: operational cost for no marginal safety here. State it honestly as
"policy-sandboxed," not "completely sandboxed."

**Alternatives weighed:** literal process isolation for all agents (rejected — overkill for
solo/local); no boundary at all (rejected — the MCP policy gate is load-bearing).

## D41 — Engine invocation: agents via MCP, trusted callers direct *(→ refines D36)*

**Decided:** **the path follows the caller.** Agents reach engines **only through MCP** (no
exceptions — that is the sandbox); **cron, CI, and the PI invoke engines directly.**
Agent-reachable *processing* engines (ingest, search) carry an **MCP-tool facade + a direct
entry**; *maintenance* engines run only by cron/CI (the Linter, the verification sweeps)
need **no MCP facade**.

**Why:** MCP must gate every agent→{engine, vault, API} path — that's the boundary; trusted
callers don't need the sandbox and shouldn't pay its overhead. Matches reality: the Linter
is a CI gate, the sweeps are cron.

**Alternatives weighed:** everything through MCP uniformly (rejected — needless facades for
cron-only engines); agents calling engines directly (rejected — breaks the sandbox).

---

## The meta-point

This decision pipeline is structurally Memoria's own model: `docs/design/` = seeds, a
`proposed`/`deferred` ADR = a proposed claim, an **accepted ADR = an accepted claim with
supersession** (ADR-10 is literally claim-supersession), the generated index = an MOC,
`docs/` = the deliverable. The meta-work of building Memoria runs on Memoria's discipline.
