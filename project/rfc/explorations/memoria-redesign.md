---
topic: proposals
title: Memoria redesign — four-layer architecture
status: exploration
created: 2026-06-07
---

# Memoria redesign — four-layer architecture

> **Status: exploration** (a capability bundle in the RFC pipeline). The synthesized
> target vision — a near-total architecture redesign. **Not yet adopted:** firm
> decisions graduate to **ADRs** (each setting `superseded_by` on the ADR it replaces).
> The rationale and alternatives weighed are preserved in
> [memoria-redesign-decisions.md](memoria-redesign-decisions.md), the seed for those ADRs.
>
> **Premise: strictly solo, personal.** One judgment-owner.

## What this changes (ADR impact)

If adopted, this **supersedes** ADR-01 (→ the four-layer model) and ADR-04 (→ type-first
folders); **amends** ADR-02, 08, 13, 17, 19, 30; **creates** ~7 new ADRs (categories ·
Catalog-in-Bases · Inbox · Read/Write · lifecycle + maturity · pattern library ·
two-kinds-of-decision); and **reinforces** ADR-03/05/10/21/22/24/33. The
decision-by-decision map is **Appendix G**; the rationale and alternatives weighed are
in [memoria-redesign-decisions.md](memoria-redesign-decisions.md). Each firm decision
graduates via the [decisions pipeline](../../adr/README.md).

## Contents

1. What Memoria is
2. The four layers, and the three doer-tiers
3. The Vault — categories, types, state
4. The agents and engines (Bookkeeping)
5. Housekeeping (the Linter engine)
6. The Workspaces
7. The pattern library
8. Human decision points
9. Design guardrails
10. To revisit

- Appendix A — topic ontology
- Appendix B — relationship to Zettelkasten
- Appendix C — profile → skills map + naming scheme
- Appendix D — dashboards
- Appendix E — the board (control plane)
- Appendix F — related backlog
- Appendix G — ADR impact (detail)

---

## 1. What Memoria is

Memoria is an **opinionated, phase-gated, bounded, personal tool for thinking and
writing** — a durable research vault that compounds across months and years.

- **Personal** — thinking is private and separate from communication; notes stay
  unfiltered, preserving raw reasoning before audience-aware editing sanitizes it.
- **Opinionated** — enforces specific workflows; eliminates setup paralysis.
- **Phase-gated** — defined phases with explicit outputs; nothing becomes a claim or
  deliverable without human review.
- **Bounded** — agent autonomy is structurally constrained; the human decides what is
  worth keeping and what becomes canonical.

**Central insight:** maintaining a knowledge base is a **bookkeeping problem, not an
intelligence problem.** Memoria gives the bookkeeping to the agent and keeps judgment
human. It solves **capture without synthesis** and **synthesis without rigor**. It is
not an autonomous scientist, a chat assistant, or a one-shot research tool.

**The naming discipline:** everything the user sees is named by the word the user would
say (the "what are you doing?" test); technical names stay internal — so the complexity
hides behind a vocabulary the user already owns.

---

## 2. The four layers, and the three doer-tiers

Two orthogonal views of the system. The **layers** are a cognitive model — how the
human understands *where* things happen. The **doer-tiers** are *who* acts.

### The four layers

| Layer | What it is | Whose actions | Triggered by |
|---|---|---|---|
| **Workspaces** | where the human works; results resurface here | the human | the human |
| **Bookkeeping** | the agent processing your knowledge, *between* human actions | agents | a human action |
| **Housekeeping** | keeping the substrate's integrity in order | engines | human · agent · cron |
| **Vault** | where everything is kept (the Obsidian vault — files & folders) | none — the substrate | — |

The two middle layers are both "-keeping," and the split is the point: **Bookkeeping
processes knowledge** in response to a human action; **Housekeeping maintains
integrity** on a trigger. The loop, everywhere:

```text
   Workspaces (human acts) ──▶ Bookkeeping (agent lanes) ──▶ Inbox (signal) ──▶ Workspaces …
```

The "gate" is just the human's next action in a workspace, prompted by an Inbox signal.

### The three doer-tiers

| Tier | Has a posture? | Uses LLM? | On the board? | Examples |
|---|---|---|---|---|
| **Engines** | no | no (deterministic) | no | the ingest/cataloging engine · the Linter · search · the retraction sweep |
| **Agents** | yes | yes | yes (lanes) | Librarian · Analyst · Writer · Fact-checker · Engineer; Socratic (no lane) |
| **The human** | — | — | — | the only one who promotes to canonical |

This is the key correction over the old "seven profiles": **deterministic work is an
engine, not an agent.** You don't *dispatch* a linter or an ingest pipeline — you *run*
it. An agent has a **posture** (a stable stance) and makes LLM judgments; an engine is
pure mechanism. (Detail: §4 agents, §5 the Linter engine.)

---

## 3. The Vault — categories, types, state

The substrate is the **Obsidian vault**: files and folders. **Four content categories +
System**, and **one folder never mixes two categories** (type-first; no lifecycle
numbers — direction lives in the state property, and the knowledge is a network, not a
pipeline).

```text
catalog/      CATALOG — structured entity records (Obsidian Bases). Built by the ingest engine.
notes/        NOTES — prose (Zettelkasten).
  fleeting/ · source/ · claims/ 🔒 · hubs/ 🔒 · index/
projects/     PROJECTS — work, divided by project first.
  <project>/  reports/ · sketches/ · composition/ · code/   (deliverable 🔒)
inbox/        INBOX — agent→human messages (the kanban board + dashboards are views of this).
system/       SYSTEM (visible infra) — logs · templates · patterns · dashboards
.memoria/     hidden runtime tooling (MCP, profiles) — not content
```

(`category` = top level, e.g. Catalog; `type` = a member, e.g. paper.) The folder is
named for its **content** (`catalog/`), not for a doer — both the ingest engine and the
Librarian agent operate *on* it.

### 3.1 Relationships vs links — two kinds of connection

| | **Relationships** (Catalog) | **Links** (Notes) |
|---|---|---|
| examples | paper *cited-by* paper, *authored-by* author, *published-in* venue, DOI→ORCID | claim *supports/contradicts* claim, claim ∈ hub |
| nature | **given** — objective facts about sources | **authored** — connections *you* draw |
| built by | the **ingest engine** (from metadata APIs), mechanical | agent **proposes** candidates, **human confirms** |
| gated? | no — it's a fact | yes — the ③ connect gate |
| field | entity `relationships` (in the Base) | note `links:` (some typed: supports/contradicts) |

"Relationships are given; links are authored." `links:` (typed note-links) replaces the
old `relations:` field — and avoids the relations/relationships near-synonym clash.

### 3.2 State — one lifecycle vocabulary

Everything the human sees uses **one chain**:
`proposed → provisional → current → retracted → archived` (each type uses a subset).
`archived` is a **state**, not a folder — the item stays in its type-home and drops from
active views (preserving links + provenance; no move).

**Inbox cards use this same chain** (a card awaiting you is `proposed`; you act → `current`;
closed → `archived`). The Hermes-native execution `status` (triage→…→done) stays the
**hidden mechanic** the user never sees (Appendix E); queries scope to the `inbox/`
category, so card-state and note-state never collide despite sharing the vocabulary.

### 3.3 Maturity and agent-recommendation — soft signals, not states

Two **soft 3-tier judgment signals**, the same *kind* but different *subjects*:

- **maturity** (`seedling → budding → evergreen`) — how *developed* a claim is. Human-set.
- **agent-recommendation** (`inconclusive → issues-found → clean`) — a *verdict* on a
  check. Agent-set.

Neither is a gate or a lifecycle state — they're informal labels, shown with a
consistent 3-tier display. A `seedling` claim is fully `current`; a `clean`
recommendation never substitutes for human approval.

### 3.4 The taxonomy (categories → types)

🔒 = review-gated. Base = surfaced through an Obsidian Base.

**CATALOG** — entity records · built by the ingest engine · Base-backed · not gated

| type | states | key properties |
|---|---|---|
| paper | current → retracted → archived | citekey, doi, title, authors[], year, venue, **relationships** |
| person | current → archived | name, orcid, affiliations[] |
| organization | current → archived | name, type, location |
| venue | current → archived | name, type, issn |
| dataset | current → retracted → archived | name, doi, url, license |
| repository | current → archived | name, url, language, license |

**NOTES** — prose (Zettelkasten) · human or agent

| type | states | properties | 🔒 |
|---|---|---|---|
| fleeting | proposed → archived | origin(human/agent) | |
| source | proposed → provisional → current → retracted → archived | source_type, entity→paper, research-area[], methodology[] | |
| claim | current → retracted → archived | **maturity**, `links:` (supports/contradicts), sources[], topics | 🔒 |
| hub | current → archived | topic, members[] | 🔒 |
| index | current → archived | — | |

**PROJECTS** — work artifacts, project-scoped *(lighter — to revisit, §10)*

| type | states | notes |
|---|---|---|
| report | current → archived | agent analysis (corpus-map, gap-report, verification-report) — **read-only; informs, doesn't gate** |
| sketch | proposed → current → archived | planning scaffold (framing, outline, canvas) |
| composition | provisional → current → archived | the evolving output; `plan → draft → deliverable` are **states** (deliverable 🔒) |
| code | current → archived | code handoff |

**Reports inform; drafts gate.** A report is an agent-generated read-only analysis the
human *consults* (regenerable → `current/archived`); its findings become Inbox `gap`/`flag`
cards, but the report itself surfaces as an FYI, never an approval. A composition is
human work heading to a **gated** deliverable.

**INBOX** — agent→human messages (the human's slice of the board) · agent-built · transient

| type | description | raised by |
|---|---|---|
| candidate | a *found* source proposed for intake | Librarian (`find`) |
| gap | a *missing*-source need | Analyst / Fact-checker |
| flag | a verification / integrity issue | Fact-checker / Linter |
| alert | drift / retraction notice | Linter / Fact-checker |

(There is no `review-request` type — a card awaiting your gate is just any card in the
`proposed` state, pointing at the artifact under review.)

### 3.5 Bases as the Vault's view layer — and how Housekeeping keeps it sound

A Base is a saved **view over note frontmatter** — every row is a file; the data lives in
the notes. Used across the Vault:

| category | base usage |
|---|---|
| Catalog | **essential** — papers/people/orgs/venues; a per-entity embedded base (`this.file`) shows "this paper's claims / this author's papers" |
| Inbox | **high** — one base grouped by type = the board / queues |
| Notes | **per-type** bases (`claims.base` by maturity/topic, `sources.base` reading list, `fleeting.base` inbox) |
| Projects | low–med (folder suffices; a cross-project compositions-by-state base is handy) |

Bases has **no integrity guarantees** — no schema, no constraints; a renamed link or a
typo'd property silently breaks a record. That gap is exactly what the **Housekeeping
Linter** fills, concretely: `schema-check` validates each record against its **type
schema** — required fields present, value types correct, enum values in-vocabulary, and
`links:`/`relationships` resolve to real targets — keyed off a `type:` discriminator. It
flags malformed records, broken/renamed links, and orphans as Inbox `flag`s. So **Bases
is the view layer, the Catalog is the source of truth, and the Linter is its
integrity guarantor.** (Dataview / the Bases API stay in reserve for citation-graph
traversal.)

---

## 4. The agents and engines (Bookkeeping)

The agent's autonomous work *between* human actions: **trigger → lanes → signal**. A
human acts; that triggers lanes (cards on the board, each assigned a profile); results
resurface as **Inbox** messages. It should feel like **a trusted teammate working in the
background to help you reach your goals** — invisible until it has something for you.

**A profile is a posture; skills attach per lane.** A profile's stable trait is its
**posture** (a stance like *optimistic* or *skeptical*); the **skills** it runs are
assigned to the *lane*, not baked into the profile. So one posture can run several lanes
as different *modes*, and lanes can share skills.

### 4.1 The two activities and six phases

The human's work is **Read** (take knowledge in) and **Write** (put work out). Each phase
aligns a **human verb**, an **agent activity**, a **skill**, and an **Inbox** item.

| Activity | # | Human verb | Agent activity | Lane (profile) | Inbox |
|---|---|---|---|---|---|
| **Read** | ① | sort | catalog | Librarian | candidate |
| | ② | read & note | extract | Librarian | (stubs) |
| | ③ | connect | link | Librarian | (link proposals) |
| **Write** | ④ | plan | map | Analyst | gap |
| | ⑤ | write | draft | Writer | — |
| | ⑥ | check | verify | Fact-checker | flag |

These three Read lanes (catalog/extract/link) are **individually triggered**, not a set —
a human gate (and often a long gap) sits between each: a source is catalogued; *much
later, if ever*, the human distills it (extract); only after a claim is written does
linking fire. So they're three lanes of the **Librarian posture**, not three profiles.
Gaps found in ④/⑥ become Inbox `gap`s that re-trigger ① — the loop that compounds.

### 4.2 The six agents

Each agent's **major components** follow the Hermes profile model: a **SOUL.md**
(posture / system prompt), **config.yaml** (model + tools), **skills/** (per-lane),
**mcp.json** (connections), and **distribution.yaml** (the packaged repo).

**Librarian** — *posture: optimistic* (include generously; the gate filters).

- *Layer/lanes:* Bookkeeping; runs the three Read lanes (catalog · extract · link).
- *Proposes:* a comparative `[!brief]`, a draft classification, claim-stubs, and note-link
  candidates — all into staging.
- *Boundary:* never canonizes; never writes a gated zone. The mechanical half of
  cataloging (fetch metadata, extract text, build **relationships**, create entity
  records) is the **ingest engine**, not the Librarian — the agent only fills the two LLM
  holes (brief + classify-proposal).

**Analyst** — *posture: neutral-analytic* (report state, don't opine).

- *Layer/lanes:* Bookkeeping; the Write `map` lane.
- *Proposes:* corpus-maps, gap-reports, cluster maps, a writability/readiness read, scored
  competing outlines, a seeded canvas.
- *Boundary:* read-only over canonical content; writes only project scratch.

**Writer** — *posture: generative, draft-only* (review-gated).

- *Layer/lanes:* Bookkeeping; the `draft` lane.
- *Proposes:* prose drafts with bound citations, and outline options.
- *Boundary:* drafts never land directly in `claims/` or `deliverables/`; no fact-checking
  (that's the Fact-checker).

**Fact-checker** — *posture: skeptical* (flag, don't fix).

- *Layer/lanes:* Bookkeeping (the `verify` lane) **and** Housekeeping (the periodic
  retraction sweep).
- *Proposes:* a verification report (citekey resolution, claim→source tracing,
  near-duplicates, retractions) + a conceptual red-team pass; spawns `gap`/`flag` cards.
- *Boundary:* never edits a draft; the human closes the gaps. Mostly mechanical, with one
  LLM step (claim↔citation matching) — which is why it's still an *agent*, not an engine.

**Socratic** — *posture: reflective, write-denied.*

- *Layer:* **Workspaces** — it assists *at the desk*, interactively (the ACP pane), **not
  on the board** (no lane, no `done` card).
- *Proposes:* nothing on disk — its product is your sharpened thinking. Questions a source
  or claim (reflective), and runs the conceptual red-team before you commit.
- *Boundary:* zero write paths, enforced at the policy layer.

**Engineer** — *posture: delegating* (a two-agent boundary).

- *Layer/lanes:* Bookkeeping; the `code` lane.
- *Proposes:* a `code` handoff, provenance, and per-task commits.
- *Boundary:* does not write code itself — an external coding agent does; the Engineer
  scaffolds the handoff and owns the commit/revert gate.

The **bounded rule** holds for all six: they **propose** (into staging / `_proposed_*`);
the **human disposes**. Promotions, the `retracted` decision, and gated-zone writes are
human-only, enforced by the policy MCP. (Skills per profile: Appendix C.)

### 4.3 The engines (deterministic, no posture)

Not agents — pure mechanism, triggered or scheduled, never on the board:

- **Ingest / cataloging engine** — fetches metadata, extracts content, builds entity
  **relationships**, creates Catalog records. The mechanical core of ①. *(ADR-30's
  pipeline already works this way.)*
- **Search** — deterministic retrieval over the vault (the `query` skill). Powers "Search"
  (§6.4) and finds link candidates before the Librarian proposes (§3.1).
- **Retraction sweep** — scheduled check against retraction sources (run by the
  Fact-checker's deterministic tooling).
- **The Linter** — §5.

---

## 5. Housekeeping (the Linter engine)

**The Linter is an engine, not an agent** — zero-LLM, no posture, no board lane. It's the
deterministic core of the Housekeeping layer, run on **cron + as a CI gate**. It validates
frontmatter schema, link/relationship resolvability, orphans, and graph health; rotates
logs; and supplies the **schema integrity Bases lacks** (§3.5). Findings surface as Inbox
`flag`/`alert` at a graded loudness (§6.5). `archive` is **propose-only** — the Linter
stages the move; the human executes it (the one move agents/engines never make).

---

## 6. The Workspaces

Where the human works; everything else serves it. Governed by **visual discipline**:
*invisible during normal use, legible when something needs a decision* — it feels like
reading and writing most of the time.

### 6.1 Three workspaces

| Workspace | Holds |
|---|---|
| **Home** | the "what needs me?" surface (triage / overview) |
| **Read** | source + notes + backlinks + Socratic + reading queues (phases ①②③) |
| **Write** | project tree + composition + linked claims + verification (phases ④⑤⑥) |

### 6.2 Homepage — above-fold "what needs me" + progressive disclosure

The front door (`home.md`): a **launchpad, consumer-only** (embeds dashboards, owns no
logic — so it can't drift or error, and degrades to empty). Above the fold: the **Inbox
summary** ("what needs me?"). Below: collapsible detail dashboards (Appendix D). So
homepage, Inbox, and dashboards are one calm surface — a 30-second glance that opens into
depth on demand. The **status line** is the always-visible ambient indicator (Linter +
queue counts).

### 6.3 Active assistance

The human invokes an assist *from the active workspace* (command palette · assist pane ·
text selection); the result is always a **proposal in staging**. Each assist is a
**(posture × skill)** applied to the current context — i.e. the same teammates, invoked
interactively rather than on the board:

| Verb | What it does | Provided by | Where |
|---|---|---|---|
| **Find** | discover **new** sources from outside → Inbox candidates | Librarian posture | Read |
| **Search** | retrieve from **what you have** (vault) | the search engine (deterministic) | both |
| **Patterns** | run a curated pattern → a proposal | the pattern's declared posture | both |
| **Ask** | grounded questioning | Socratic | both |
| **Draft** | generate a proposed artifact (stub / outline / prose) | Writer | Write |
| **Explore** | elicit framings / branches | Writer / Socratic | Write |

### 6.4 Graded loudness — defined outcomes

| Level | Outcome |
|---|---|
| **Quiet** | logged only; aggregated in the weekly review; no interruption |
| **Notice** | appears in the relevant dashboard + weekly review; no push |
| **Alert** | appears in Home's "what needs me" + Daily Health; pushed; does **not** block |
| **Block** | blocks the action (dispatch / promotion) until acknowledged; pushed |

The test for push vs dashboard: *does it change what the human does in the next 30 minutes?*

---

## 7. The pattern library

The substrate for the **Patterns** assist: a curated library of single-purpose
prompt-transformations, stored as markdown in **`system/patterns/`** (visible, git-tracked,
lintable — *not* `.memoria/`, which is hidden runtime).

- **One runner skill executes every pattern.** Patterns are *data* (prompts), not
  individual skills; "using a pattern" = the runner + a pattern id.
- **Each pattern's frontmatter declares** its **posture/agent**, **activity (read/write)**,
  **action type**, **input**, and **output_target** — so we always know which posture runs
  it, and whether it's a read or write pattern. A shared `_preamble.md` enforces Memoria
  voice (your-words, concise, propose-never-assert, cite-don't-fabricate).
- **Finding the right one:** the workspace **pattern-picker** (a `patterns.base` catalog)
  filters by the current activity / phase / selection — it surfaces only the patterns
  relevant *now*. That picker is the discovery mechanism.
- **Constraints (enforced):** never writes a gated zone (output → staging, else dry-run +
  lint failure); propose-not-dispose; the Linter validates pattern files; retrieve-type
  patterns are zero-LLM; versioned + reproducible with per-run provenance.
- **Seeded** by *adapting* fabric patterns (`analyze_claims`, `compare_and_contrast`,
  `check_falsifiability`, …), retargeted to staging. Patterns are themselves gated assets
  (human-authored or agent-proposed → human-approved).
- **Runner:** in-vault MCP. **Invocation:** palette · pane · selection. **Model:**
  per-pattern hint with a global fallback.

---

## 8. Human decision points

Every place the human acts is one of **two kinds**, and they need different Inbox items:

- **Approval gate** — the human reviews *agent-produced output* and accepts/rejects.
  Rubber-stamp risk is high, so the item must carry **reasoning + verdict** (§9), never a
  bare "OK?".
- **Work prompt** — the agent signals it's *time for the human's own thinking/writing*.
  Not an approval; the item is a **rich nudge** with the material to start.

| Decision point | Kind | Right stage? | Meaningful Inbox item |
|---|---|---|---|
| keep this source? (candidate triage) | approval (keep/skip) | ✓ at intake | `candidate` + *why surfaced* (which gap/focus, signals, dupes) |
| classify | — **not a real gate** | ✗ rubber-stamp, low-stakes metadata | **automate** (audited, correctable); `flag` only on genuine ambiguity |
| write the claim (②) | work prompt | ✓ on a kept source | "distill candidate" nudge: why worth distilling + stubs |
| confirm links (③) | approval | ✓ once the claim exists | link proposals **+ evidence + stance reasoning** per edge |
| frame a project (④) | work prompt + choice | ✓ at write-readiness | "ready to write" + corpus-map + scored outlines |
| edit the draft (⑤) | work (continuous) | ✓ in Write | a "draft ready" FYI; not an approval |
| certify & ship (⑥) | approval (strongest) | ✓ before shipping | the verification report: checks, red-team, open gaps |
| archive | approval (human-only move) | ✓ when stale | archival proposal **+ reason** |
| re-adjudicate (retraction) | approval | ✓ on invalidation | retraction `alert` + adjudication options |
| near-tie | approval (same/diff/unsure) | ✓ before a commit | the two objects, side by side |

**The rule:** *an Inbox item a human can clear without reading is a design smell* —
either give it real decision material, or automate it. **classify** fails this test, so
it's automated. The strongest gates (certify, link-confirm, re-adjudicate) are approvals,
so each must ship its reasoning.

---

## 9. Design guardrails

- **Decision transparency (the primary guardrail).** Assume anything promoted to the
  human *will* be approved — so the strongest guard is to hand the human the **reasoning:
  the pros, the cons, and the verdict**, so they judge the *process*, not just the output.
  And **prefer full automation over a rubber-stamp gate** — if a gate is just "click OK,"
  automate it (audited) rather than fake a decision.
- **Calibration gate (hybrid scores only).** `writable-density` and `readiness-score` are
  **deterministic** (graph/coverage metrics — reproducible; calibration = setting
  thresholds). `candidate-rank` and `outline-score` are **hybrid** (embedding/LLM) — these
  ship only with a filled threshold spec: grounded · error-budgeted · drift-bound
  (recalibrate on model-version change) · shadow-first.
- **Diversity reserve.** ≥20% of intake reserved for unranked external/serendipitous
  sources, so the cycle isn't fed only by its own back-pressure (anti-monoculture).
- **Provenance everywhere.** Every claim → a citekey; every gated write → an audit entry
  (SHA-256 chain); shipped deliverables → a frozen provenance snapshot.
- **Archive, never delete.** Obsolescence is handled by `retracted` + supersession with
  lineage links, preserving backward traceability.

---

## 10. To revisit

- **Projects / the Write workspace** — `report · sketch · composition · code` is
  provisional; the plan→draft→deliverable-as-states model needs a pass. **Read workspace
  is finalized first.**
- **Profile renames** ripple through existing docs (Mapper→Analyst, Verifier→Fact-checker,
  Coder→Engineer; Linter reclassified as an engine) — sequence the doc migration.
- **`relations:` → `links:`** field rename (notes) + adding entity `relationships`
  (Catalog) — amends ADR-08; plan the migration.
- **Activity prefix in skill names** (`read:`/`write:`) — keep only if an eval shows it
  improves selection (Appendix C).

---

## Appendix A — topic ontology (starting point)

Two **facets** on source/claim notes (faceted, not a flat `topic[]`):

- **research-area** — seeded from **OpenAlex Topics/Concepts** (the ingest engine already
  enriches from OpenAlex, so the vocabulary is free and consistent).
- **methodology** — a controlled vocab covering method *and* study design (RCT ·
  observational · qualitative · systematic-review · meta-analysis · simulation · …),
  human-extended. *(research-design was merged in — it overlapped methodology too much to
  stand alone.)*

System functions (clustering, gap-finding, writability) read these facets.

## Appendix B — relationship to Zettelkasten

**Data model deeply ZK-faithful** — `fleeting`≈fleeting, `source`≈literature note,
`claim`≈permanent note, `hub`≈structure/hub note, `index`≈register; the **catalog + notes
split** revives Luhmann's two-box system (bibliographic index vs main slip-box); topic
stays out of folders; obsolescence is handled by supersede-with-lineage, not deletion.
**Process model deliberately departs** where an agent + a gate force it: a *standing* axis
(ZK had no agent to distrust) and *retraction* states (ZK superseded via new linked notes —
Memoria keeps the lineage link and adds the state). `reference` was dropped (it collided
with ZK's "reference note" = our `source`, and double-encoded maturity — an `evergreen`
claim is the settled unit). **The docs must make this alignment/divergence explicit when
promoted.**

## Appendix C — profile → skills map + naming scheme

**Skill naming: `<activity>:<verb>-<object>`** (snake `<activity>_<verb>_<object>` if
serialized as an MCP tool) — verb-first, from a **closed verb set**, the artifact is the
object (no redundant result slot). Verbs: `extract · link · summarize · check · rank ·
draft · outline · score`. Examples: `read:extract-claims` · `read:link-claim` ·
`read:check-citation` · `read:score-density` · `write:draft-section` ·
`write:outline-argument`. *(The `read:`/`write:` prefix is borderline — keep only if an
eval shows it aids selection.)*

Existing skills are current `hermes-cli` commands; **(new)** are specified, not built.

| Profile · layer | Existing skills | New (proposed) |
|---|---|---|
| **Librarian** · bookkeeping | find · ingest · enrich · classify · query · obsidian-paper-note | candidate-rank · tension-surface · relation-suggest · distill-candidate-flag |
| **Analyst** · bookkeeping | scope-project · gap-report · cluster-map · cluster-mapping | writable-density · readiness-score · canvas-seed · gap-route |
| **Writer** · bookkeeping | draft · query · lint · promote · counter-outline | claim-stub · outline-score · citation-bind |
| **Fact-checker** · bookkeeping + housekeeping | cite-check · claim-trace · similarity-check · find-duplicates · retraction-check · claim-checks | gap-card · gap-fix-propose · continuous-verify |
| **Engineer** · bookkeeping | code · commit · revert · workspace · scaffold | — |
| **Socratic** · workspaces | socratic-processing · lens-reading | — |
| **Linter** · housekeeping (engine, not an agent) | lint · schema-check · schema-migrate · graph-analyze · health-report · session-log · dry-run · structural-detectors | provenance-snapshot · archive (propose-only) |

The mechanical half of cataloging (fetch · extract · build relationships · create records)
runs in the **ingest engine**, not the Librarian. *(Dropped: `classification-confidence` —
it served confidence auto-accept, which contradicts the propose-not-dispose guardrail.)*

## Appendix D — dashboards (reconciled)

The **Inbox** is the *action queue* — discrete things that need you *now* (it feeds Home's
"what needs me?"). **Dashboards** are *browsable health views* — where things *stand*. All
are Bases/Dataview, consumer-only; a healthy vault shows them near-empty. Grouped by surface:

| Surface | Dashboard | Role |
|---|---|---|
| **Home** | *daily-health* | absorbed into the homepage — the above-fold glance |
| | board-state | the Inbox board (a base over `inbox/`) |
| **Read** | reading-pipeline | sources awaiting classify + claims-by-maturity |
| | discuss-queue | sources worth discussing → Ask / Socratic |
| **Read / Write** | open-questions | unconnected claims — the synthesis backlog |
| | contradictions | `contradicts` links — open tensions |
| **Housekeeping** | drift-watch | active/imminent drift; HIGH → Inbox alert |
| | loose-ends | structural debt; Notice → weekly |
| | weekly-review | the Friday aggregator |
| **Bookkeeping-ops** | audit-log | provenance log; unhandled denies → flag |
| | fleet-health | agent trust score / operational rollup |

**Synthesis vs structural, split by layer:** `open-questions`+`contradictions` are the
*human's* unfinished thinking (Read/Write); `loose-ends`+`drift-watch` are the *Linter's*
structural debt (Housekeeping) — kept separate, not collapsed.

## Appendix E — the board (control plane)

Every unit of agent work — Bookkeeping and Housekeeping — is a **card** on the Hermes
Kanban board (`kanban.db`, projected into Obsidian): the **trigger-and-lanes** end of the
loop. A human action (or cron) creates a card; the dispatcher assigns it to a **lane** (a
profile); the worker runs it; the result resurfaces as an **Inbox** signal.

**Lanes = profiles** (`assignee = memoria-<name>`). **No Socratic and no Linter lane** —
Socratic runs at the desk (ACP pane); the Linter is a deterministic engine (cron/CI).

The board's native **`status`** (`triage → todo → ready → running → done → blocked →
archived`) is the **hidden execution mechanic**. The human-facing card state is the
**lifecycle chain** (§3.2). Three orthogonal review dimensions keep an agent verdict from
rubber-stamping a human decision: `status` (execution) · the human's lifecycle state ·
`agent-recommendation` (the soft verdict, §3.3). **Rejection spawns a new card**
(`supersedes`), mirroring claim supersession — each card is one attempt, so the audit
trail can't lie.

**Handoff payload** (self-contained): `goal · context · allowed_paths · expected_outputs ·
review_checks`. `allowed_paths` may *narrow* but never *widen* the lane's write scope (lane
= ceiling, payload = floor; policy MCP enforces). **WIP limits** (back-pressure on the
human bottleneck): review queue = 5 `done` cards · 1 `running` per lane · Writer lane
bounded. Dispatcher polls every 60s.

## Appendix F — related backlog

A live map between this redesign and the GitHub board + `rfc/`. Reviewed 2026-06-08
against the project-board columns.

### Issues the redesign answers — labelled `resolved-by-redesign`

| # | Resolution |
|---|---|
| 221 | this redesign — the tracking issue |
| 153 | auto-promote at `evergreen`? **No** — maturity is a property (§3.3) |
| 213 | Dataview vs Bases — Bases is the view layer (§3.5) |
| 224 | "Ask chat transform" → the Ask / Patterns assists (§6.3, §7) |
| 185 | ACP→inbox loop → the trigger→lanes→signal loop + Inbox |
| 191 / 180 | tags/properties + starter tag set → faceted ontology (App. A) |
| 142–145 | frontmatter UX → Bases/forms once Catalog/Notes are Bases-backed |

### Issues to resolve inside the redesign — labelled `redesign-input`

`#146` ACP-pane name · `#183` structured-capture forms (Catalog entity creation) ·
`#186` ingest a URL (Find) · `#181` email a fleeting note · `#193` crash-consistency
(Housekeeping-by-convention + git, not ACID) · `#188` LLM per profile · `#196` pin skills
to a lane · `#177` tutorial names.

### RFCs folded (`folded_into: memoria-redesign`)

RFC-03 (→ Inbox card-in-`proposed`) · RFC-04 (→ Find / Librarian / Analyst) · RFC-05
(→ near-tie/dedup + Fact-checker) · RFC-09 (→ profile = posture, §4) · RFC-10 (→ pattern
governance, §7). **Tension:** RFC-08 (advisory gate) vs the transparency guardrail — allow
only as a comparison-study toggle.

### Explorations

`schema-and-retrieval`, `triage-improvements` → resolved; `discovery-loop`, `integrations`,
`measurement-and-verification` → partially folded; `publication-strategy` → parked with
Projects; deployment/`classical-method-displacements` → independent.

### #220 — obsidian-biblib

Plain-text, note-per-reference, DOI/ISBN/arXiv import — philosophy matches Memoria and
would resolve #186/#187 — **but** it stores **nested CSL-JSON** and bypasses native
properties, incompatible with the Catalog's Bases-flat-properties requirement.
**Recommendation:** adopt its import/citekey *engine*, flatten into the flat Catalog
schema; a spike, not a swap.

### Scoping

`#198` (v0.2 scope): this redesign supersedes ADR-01/04 and renames profiles/folders —
**major-version-sized**. Sequence it as superseding ADRs across versions.

## Appendix G — ADR impact (detail)

If adopted, each firm decision graduates via the
[decisions pipeline](../../adr/README.md) (rationale in
[memoria-redesign-decisions.md](memoria-redesign-decisions.md)).

**Supersedes**

- **ADR-01** (three-layer architecture) → the **four-layer cognitive model**
  (Workspaces · Bookkeeping · Housekeeping · Vault) over **three doer-tiers**
  (engines · agents · the human).
- **ADR-04** (lifecycle-over-topic folders) → **type-first folders** (one category per
  folder; lifecycle is a state property, not a folder number).

**Amends**

- **ADR-02** (seven specialist profiles) → **six agents** (Librarian · Analyst · Writer
  · Fact-checker · Socratic · Engineer), each defined by a **posture**; the **Linter is
  reclassified as a deterministic engine**, not an agent.
- **ADR-08** (typed relations) → notes carry **`links:`** (some typed
  supports/contradicts); entities carry **`relationships`** — two distinct kinds.
- **ADR-30** (deterministic ingest) → **cataloging splits**: a mechanical *ingest
  engine* + the Librarian agent's two LLM steps.
- **ADR-13** (homepage) → above-fold "what needs me" (Inbox) + progressive disclosure.
- **ADR-17** (candidate frontmatter) → `candidate` is an **Inbox** type.
- **ADR-19** (agent-proposed MOCs) → MOC renamed **hub**.

**Creates (new ADRs)**

- Four categories (**Catalog · Notes · Projects · Inbox**) + the category/type taxonomy.
- Catalog entities in **Obsidian Bases**; Housekeeping supplies the integrity Bases lacks.
- **Inbox** as the agent→human message category (kanban + dashboards are its views).
- **Read / Write** as the activity spine.
- Universal lifecycle chain + **maturity as a property**; **drop the `reference`** type.
- The in-vault **pattern library** (`system/patterns/`).
- **Two kinds of human decision** (approval gate vs work prompt) + the
  decision-transparency guardrail.

**Aligns with (reinforced)** — ADR-03 (structural gate), 05 (Zotero backbone),
10 (claim supersession), 21 (autonomy ceiling), 22 (Hermes runtime),
24 (single-researcher), 33 (BERTopic clustering).
