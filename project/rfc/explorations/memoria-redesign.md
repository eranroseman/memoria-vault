---
topic: proposals
title: Memoria redesign — four-layer architecture
status: exploration
created: 2026-06-07
---

# Memoria redesign — four-layer architecture

> **Status: exploration** (a capability bundle in the RFC pipeline). The synthesized
> target vision — a near-total architecture redesign. **Not yet adopted:** firm
> decisions graduate to **ADRs** (each setting `superseded_by` on the ADR it
> replaces). The **rationale and alternatives weighed** — the decision-journey
> stripped from this spec — are preserved in
> [memoria-redesign-decisions.md](memoria-redesign-decisions.md), the seed for those
> ADRs.
>
> **Premise: strictly solo, personal.** One judgment-owner.

## ADRs this redesign touches

If adopted, this supersedes / amends accepted ADRs and creates new ones. Each firm
decision graduates via the [decisions pipeline](../../adr/README.md).

**Supersedes**

- **ADR-01** (three-layer architecture) → the **four-layer cognitive model**
  (Desk · Bookkeeping · Housekeeping · Store).
- **ADR-04** (lifecycle-over-topic folders) → **type-first folders** (one category per
  folder; lifecycle becomes a state property, not a folder number).

**Amends**

- **ADR-02** (seven specialist profiles) → **team-role names** + layer assignment
  (Librarian · Analyst · Socratic · Writer · Fact-checker · Engineer · Linter).
- **ADR-13** (homepage front-door) → **above-fold "what needs me" (Inbox) + progressive
  disclosure**.
- **ADR-17** (shared candidate frontmatter) → `candidate` becomes an **Inbox** type.
- **ADR-30** (deterministic ingest) → splits into **entity (Catalog) + source-note**
  outputs.
- **ADR-19** (agent-proposed MOCs) → MOC renamed **hub**.

**Creates (new ADRs)**

- Four categories (**Catalog · Notes · Projects · Inbox**) + the category/type taxonomy.
- Catalog entities stored in **Obsidian Bases**; Housekeeping supplies the integrity
  Bases lacks.
- **Inbox** as the agent→human message category (kanban + dashboards are its views).
- **Read / Write** (Compile/Compose) as the activity spine.
- Universal lifecycle chain + **maturity as a property**; **drop the `reference`** type.
- The in-vault **pattern library** (`system/patterns/`).

**Aligns with (reinforced, no change)** — ADR-03 (structural gate), 05 (Zotero
backbone), 08 (typed relations), 10 (claim supersession), 21 (autonomy ceiling),
22 (Hermes runtime), 24 (single-researcher), 33 (BERTopic clustering).

## Contents

1. What Memoria is
2. The four layers (the cognitive model)
3. The Store — categories, types, state
4. The Bookkeeping layer
5. The Housekeeping layer
6. The Desk — workspaces, homepage, assistance
7. The pattern library
8. Design guardrails
9. To revisit

- Appendix A — topic ontology
- Appendix B — relationship to Zettelkasten
- Appendix C — profile → skills map
- Appendix D — dashboards
- Appendix E — the board (control plane)
- Appendix F — related backlog (issues, RFCs, explorations)

---

## 1. What Memoria is

Memoria is an **opinionated, phase-gated, bounded, personal tool for thinking and
writing** — a durable research vault that compounds across months and years.

- **Personal** — thinking is private and separate from communication; notes stay
  unfiltered, preserving raw reasoning before audience-aware editing sanitizes it.
- **Opinionated** — enforces specific workflows; eliminates setup paralysis.
- **Phase-gated** — defined phases with explicit outputs; nothing becomes a claim or
  deliverable without human review.
- **Bounded** — agent autonomy is structurally constrained; the human decides what
  is worth keeping and what becomes canonical.

**Central insight:** maintaining a knowledge base is a **bookkeeping problem, not an
intelligence problem.** Memoria gives the bookkeeping to the agent and keeps judgment
human. It solves **capture without synthesis** and **synthesis without rigor**. It is
not an autonomous scientist, a chat assistant, or a one-shot research tool.

**The naming discipline:** everything the user sees is named by the word the user
would say (the "what are you doing?" test); technical names stay internal. So the
complexity hides behind a vocabulary the user already owns.

---

## 2. The four layers (the cognitive model)

These are **cognitive models** — how the human understands what's happening — not
implementation boundaries.

| Layer            | Whose actions                                    | Triggered by         | What it is                             |
| ---------------- | ------------------------------------------------ | -------------------- | -------------------------------------- |
| **Desk**         | the human (reads/writes); results resurface here | the human            | where the work happens (workspaces)    |
| **Bookkeeping**  | the agent, autonomously, _between_ human actions | a human action       | the agent processing your knowledge    |
| **Housekeeping** | the agent (a tool), maintenance/integrity        | human · agent · cron | the agent keeping the house in order   |
| **Store**        | none — the substrate the others act on           | —                    | where everything is kept (the Library) |

The two agent layers are both "-keeping," and the distinction is the point:
**Bookkeeping** _processes knowledge_ in response to a human action; **Housekeeping**
_maintains the substrate's integrity_ on a trigger. The loop, everywhere:

```text
   Desk (human acts) ──▶ Bookkeeping (agent lanes) ──▶ Inbox (signal) ──▶ Desk (human acts) …
```

The "gate" is just the human's next action at the Desk, prompted by an Inbox signal.

---

## 3. The Store — categories, types, state

The substrate (the **Library**). Four content categories + System; **one folder
never mixes two categories** (type-first, no lifecycle numbers — direction lives in
the state property, and the knowledge is a network, not a pipeline).

```text
catalog/      CATALOG — structured entity records (Bases). Library, Librarian-tended.
notes/        NOTES — prose (Zettelkasten).
  fleeting/ · source/ · claims/ 🔒 · hubs/ 🔒 · index/
projects/     PROJECTS — work, divided by project first.
  <project>/  reports/ · sketches/ · composition/ · code/   (deliverable 🔒)
inbox/        INBOX — agent→human messages (the kanban + dashboards are views of this).
system/       SYSTEM (visible infra) — logs · templates · patterns · dashboards
.memoria/     hidden runtime tooling (MCP, profiles) — not content
```

(`category` = top level e.g. Catalog; `type` = a member e.g. paper. Standard pair.)

### 3.1 State — two disjoint vocabularies

**Knowledge/data** (Catalog · Notes · Projects) use one **lifecycle chain**:
`proposed → provisional → current → retracted → archived` (each type a subset).
`archived` is a **state**, not a folder — the note stays in its type-home and drops
from active views (preserving links + provenance; no move). **Maturity** is a separate
**property** of a claim (below), not a second state axis.

The **Inbox** is different: it is the human-facing projection of **board cards**, which
carry the board's own state machine (`status` / `review_status`) — **deliberately
disjoint** from the lifecycle chain so the two never collide (Appendix E).

### 3.2 The taxonomy (categories → types)

🔒 = review-gated. Base = surfaced through an Obsidian Base.

**CATALOG** — entity records · agent-built · Base-backed · not gated

| type         | description                      | states                         | key properties                              |
| ------------ | -------------------------------- | ------------------------------ | ------------------------------------------- |
| paper        | bibliographic record of a source | current → retracted → archived | citekey, doi, title, authors[], year, venue |
| person       | author / researcher              | current → archived             | name, orcid, affiliations[]                 |
| organization | institution / lab / company      | current → archived             | name, type, location                        |
| venue        | journal / conference / publisher | current → archived             | name, type, issn                            |
| dataset      | data resource                    | current → retracted → archived | name, doi, url, license                     |
| repository   | code / software                  | current → archived             | name, url, language, license                |

**NOTES** — prose (Zettelkasten) · human or agent

| type     | description                           | states                                                  | properties                                                              | 🔒  |
| -------- | ------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------- | --- |
| fleeting | quick raw capture, transient          | proposed → archived                                     | origin(human/agent)                                                     |     |
| source   | your-words summary of a source        | proposed → provisional → current → retracted → archived | source_type, entity_ref→paper, research-area[], methodology[], design[] |     |
| claim    | atomic, source-grounded assertion     | current → retracted → archived                          | **maturity**, relations(supports/contradicts), sources[], topics…       | 🔒  |
| hub      | structure note linking related claims | current → archived                                      | topic, members[]                                                        | 🔒  |
| index    | top-level navigation                  | current → archived                                      | —                                                                       |     |

**PROJECTS** — work artifacts, project-scoped _(lighter — to revisit, §9)_

| type        | description                                                       | states                           | notes             |
| ----------- | ----------------------------------------------------------------- | -------------------------------- | ----------------- |
| report      | agent analysis (corpus-map, gap-report, verification-report)      | current → archived               | in `reports/`     |
| sketch      | planning scaffold (framing, outline, canvas)                      | proposed → current → archived    | structure-finding |
| composition | the evolving output — `plan → draft → deliverable` are **states** | provisional → current → archived | deliverable 🔒    |
| code        | code handoff                                                      | current → archived               | —                 |

**INBOX** — the human-facing projection of **board cards** (agent→human) · agent-built
· transient

| type           | description                          | raised by              |
| -------------- | ------------------------------------ | ---------------------- |
| candidate      | a _found_ source proposed for intake | Librarian (`find`)     |
| gap            | a _missing_-source need              | Analyst / Fact-checker |
| flag           | a verification / integrity issue     | Fact-checker / Linter  |
| review-request | a `done` card awaiting your gate     | any lane               |
| alert          | drift / retraction notice            | Linter / Fact-checker  |

Inbox items carry **board state** (`status` / `review_status`), not the lifecycle chain
(§3.1, Appendix E). The kanban board and the queue dashboards are views of this.

### 3.3 Maturity (a claim property)

`seedling → budding → evergreen` describes a claim's **intellectual development**, not
its trust. `seedling` = rough new idea; `evergreen` = atomic, polished, densely
linked, "done thinking." **Not a gate** — a `seedling` claim is fully `current`. Set
by the human (agent may propose). Used by `writable-density`, the board's maturity
view, and the human's sense of how much to lean on a claim when writing. State asks
"how trusted?"; maturity asks "how developed?".

### 3.4 Bases as the Store's view layer

A Base is a saved **view over note frontmatter** — every row is a file; data lives in
the notes. Used across the Store:

| category | base usage                                                                                                |
| -------- | --------------------------------------------------------------------------------------------------------- |
| Catalog  | **essential** — papers/people/orgs/venues; per-entity embedded base (`this.file`) = "this paper's claims" |
| Inbox    | **high** — one base grouped by type = the board / queues                                                  |
| Notes    | **per-type** bases (`claims.base` by maturity/topic, `sources.base` reading list, `fleeting.base` inbox)  |
| Projects | low–med (folder suffices; a cross-project compositions-by-state base is handy)                            |

Bases has **no integrity guarantees** (no schema enforcement, no constraints) — which
is exactly what the **Housekeeping layer supplies** (`schema-check`, `type:`
discriminators, the Debug view). So Bases is the view layer and Catalog source of
truth; Housekeeping is its integrity guarantor; Dataview/Bases-API are held in reserve
for citation-graph traversal. Under-used powers to design around: **`this.file`
embedded bases** (per-record dashboards), `reduce/filter/map` over list properties,
and the `[[Link#]]` empty-anchor trick for typed relations without extra properties.

---

## 4. The Bookkeeping layer

The agent's autonomous work _between_ human actions: **trigger → lanes → signal**. A
human acts at the Desk; that triggers agent lanes (cards on the board, each assigned a
profile); results resurface as **Inbox** messages. It should feel like **a trusted
colleague working in the background to help you reach your goals** — invisible until
it has something for you.

### 4.1 Two activities, six phases

The human's work splits into two activities — **Read** (take knowledge _in_) and
**Write** (put work _out_) — internally Compile/Compose. Each phase pairs a **human
verb** (Desk) with an **agent activity** (Bookkeeping) and a profile.

| Activity  | #   | Human verb (Desk) | Agent activity (Bookkeeping) | Profile      | Inbox                 |
| --------- | --- | ----------------- | ---------------------------- | ------------ | --------------------- |
| **Read**  | ①   | sort              | cataloging                   | Librarian    | candidate             |
|           | ②   | read & note       | extracting                   | Librarian    | (stubs)               |
|           | ③   | connect           | linking                      | Librarian    | (relation proposals)  |
| **Write** | ④   | plan              | analysing                    | Analyst      | gap                   |
|           | ⑤   | write             | drafting                     | Writer       | —                     |
|           | ⑥   | check             | verifying                    | Fact-checker | flag · review-request |

Read = ①②③ (Compile); Write = ④⑤⑥ (Compose). Gaps found in ④ and ⑥ become Inbox
`gap` messages that re-trigger ① — the loop that makes the vault compound.

### 4.2 The colleagues

The bookkeeping agents are named as **team roles you'd hire** (self-explanatory):

- **Librarian** — finds, captures, enriches, catalogs sources; proposes
  classifications and relations. Owns Read's agent side (cataloging/extracting/linking).
- **Analyst** — surveys the corpus, maps clusters, finds gaps, judges readiness.
- **Writer** — drafts prose, generates outlines.
- **Fact-checker** — traces every claim to a source, catches retractions, flags gaps.
- **Engineer** — code handoff and provenance.

The **bounded rule** holds for all: they **propose** (into staging / `_proposed_*`);
the **human disposes** (promotes to canonical). Promotions, the `retracted` decision,
and gated-zone writes are human-only; the Policy MCP enforces this at the filesystem.
(Full skills per profile: Appendix C.)

---

## 5. The Housekeeping layer

The maintenance **tool** — **Linter** — that keeps the substrate sound. Same loop
shape (**trigger → lanes → signal**), but triggered by human · agent · **cron**, and
**deterministic (zero-LLM)** so it can be a CI gate. It validates frontmatter schema,
link health, orphans, graph health; rotates logs; runs the periodic retraction sweep
(with Fact-checker); and supplies the **schema integrity Bases lacks**. Findings
surface as Inbox `flag` / `alert` at a graded loudness (§6.6). `archive` proposals are
propose-only — the human executes the move (or the state flip).

---

## 6. The Desk — workspaces, homepage, assistance

Where the human works; everything else serves it. Governed by **visual discipline**:
_invisible during normal use, legible when something needs a decision_ — it feels like
reading/writing most of the time.

### 6.1 Three workspaces

One per cognitive mode (the established rule: _one per mode, three is the working
set_):

| Workspace | Mode              | Holds                                                     |
| --------- | ----------------- | --------------------------------------------------------- |
| **Home**  | triage / overview | the "what needs me?" surface                              |
| **Read**  | Compile (①②③)     | source + notes + backlinks + Socratic + reading queues    |
| **Write** | Compose (④⑤⑥)     | project tree + composition + linked claims + verification |

(The doc'd workspaces were never implemented; these are the redesign.)

### 6.2 Homepage — above-fold "what needs me" + progressive disclosure

The front door (`home.md`): a **launchpad, consumer-only** (embeds dashboards, owns no
logic, can't drift, can't error, degrades to empty). Top, above the fold: the **Inbox
summary** — "what needs me?". Below: collapsible detail dashboards (full catalog:
Appendix D). So homepage, Inbox, and dashboards are one calm surface — a 30-second
glance that opens into depth on demand.
The **status line** is the always-visible ambient indicator (Linter + queue counts).
Dashboards are **Bases views** of the Inbox / Catalog / Notes.

### 6.3 Socratic — the thinking-partner

**Socratic** is write-denied and conversational; it questions to sharpen your thinking
(reflective during Read/Write; conceptual red-team before you commit). It assists _at
the Desk_, in the moment — a **Work-layer partner**, not a background bookkeeper.

### 6.4 Active assistance per workspace

Six self-explanatory affordances; the first two deterministic, the rest LLM; **all
propose-class** (output lands in staging, the human disposes):

| Verb                 | What it does                                                                 | Where |
| -------------------- | ---------------------------------------------------------------------------- | ----- |
| **Find**             | discover **new** sources from outside → Inbox candidates                     | Read  |
| **Search**           | retrieve from **what you have** (vault)                                      | both  |
| **Patterns** (apply) | run a curated pattern → a proposal (extract / summarize / compare / analyse) | both  |
| **Ask**              | grounded questioning (Socratic)                                              | both  |
| **Draft**            | generate a proposed artifact (stub / outline / prose)                        | Write |
| **Explore**          | elicit framings / branches (for the reflective beats)                        | Write |

### 6.5 Graded loudness — defined outcomes

Every signal has a level with a **defined outcome**:

| Level      | Outcome                                                                      |
| ---------- | ---------------------------------------------------------------------------- |
| **Quiet**  | logged only; aggregated in the weekly review; no interruption                |
| **Notice** | appears in the relevant dashboard + weekly review; no push                   |
| **Alert**  | appears in Home's "what needs me" + Daily Health; pushed; does **not** block |
| **Block**  | blocks the action (dispatch / promotion) until acknowledged; pushed          |

The test for push vs dashboard: _does it change what the human does in the next 30
minutes?_

---

## 7. The pattern library

The substrate for **Patterns** assistance: a curated library of single-purpose
prompt-transformations, stored **as markdown in `system/patterns/`** (visible,
git-tracked, lintable — _not_ `.memoria/`, which is hidden runtime tooling).

- **Format:** frontmatter (`id · type · activity · binds_to · input · output_target ·
determinism · anchoring_guard · version · adapted_from`) + a prompt body with a
  `{{input}}` placeholder. A shared `_preamble.md` enforces Memoria voice
  (your-words, concise, propose-never-assert, cite-don't-fabricate). A `patterns.base`
  catalog drives the workspace picker.
- **Patterns vs skills:** a _pattern_ is the transform core; an _assist skill_ = a
  pattern wrapped in deterministic gather/route/audit. So the new assist skills are
  patterns + thin wrappers, not bespoke code.
- **Constraints (enforced):** never writes a gated zone (`output_target` ∈ staging or
  the write degrades to dry-run + fails lint); propose-not-dispose; Linter validates
  pattern files; `type: retrieve`/Find/Search is zero-LLM; versioned + reproducible
  with per-run provenance.
- **Seeded** by _adapting_ fabric patterns (`analyze_claims`, `compare_and_contrast`,
  `check_falsifiability`, `create_recursive_outline`…), retargeted to staging.
  Patterns are themselves gated assets (human-authored or agent-proposed→human-approved).
- **Runner:** in-vault MCP. **Invocation:** command-palette · assist-pane ·
  selection-driven. **Model routing:** per-pattern hint with a global fallback.

---

## 8. Design guardrails

The cross-cutting rules every mechanism honors:

- **Propose, not dispose.** Agents propose into staging; only humans promote to
  canonical. No confidence-tiered auto-accept — the gate is structural and uniform
  (confident-wrong is the failure mode the gate exists to catch).
- **Anti-anchoring.** Where a proposal frames a human decision (stubs, relations,
  outlines, ranked candidates): blind-first capture, rankings off by default,
  no-assist sampling, stubs marked "rewrite required." Reflective beats stay human.
- **Calibration gate.** Any score-emitting skill (`writable-density`,
  `readiness-score`, `outline-score`, `candidate-rank`) ships only with a filled
  threshold spec: defined · grounded · error-budgeted · drift-bound (recalibrate on
  model-version change) · override-logged · shadow-first.
- **Diversity reserve.** ≥20% of intake reserved for unranked external/serendipitous
  sources, so the cycle isn't fed only by its own back-pressure (anti-monoculture).
- **Provenance everywhere.** Every claim → a citekey; every gated write → an audit
  entry (SHA-256 chain); shipped deliverables → a frozen provenance snapshot.
- **Archive, never delete.** Obsolescence is handled by `retracted` + supersession
  with lineage links, preserving backward traceability.

---

## 9. To revisit

- **Projects / the Write workspace** — `report · sketch · composition · code` is
  provisional; the plan→draft→deliverable-as-states model needs a pass. **Focus is the
  Read workspace first.**
- **Profile renames** ripple through existing docs (Librarian kept; Mapper→Analyst,
  Verifier→Fact-checker, Coder→Engineer; Socratic + Linter kept) — sequence the doc
  migration.
- **Retraction trigger** when a retracted source sits under a `current` claim: reuse
  `review-request` (re-open) + supersession; confirm no extra state is needed.

---

## Appendix A — topic ontology (starting point)

Three **separate facets** on source/claim notes (faceted, not a flat `topic[]`):

- **research-area** — seeded from **OpenAlex Topics/Concepts** (the Librarian already
  enriches from OpenAlex, so the vocabulary is free and consistent).
- **methodology** — controlled vocab: RCT · observational · qualitative ·
  systematic-review · meta-analysis · simulation · …
- **research-design** — controlled vocab: study/design types; human-extended.

System functions (clustering, gap-finding, writable-density) read these facets.

## Appendix B — relationship to Zettelkasten

**Data model deeply ZK-faithful** — `fleeting`≈fleeting, `source`≈literature note,
`claim`≈permanent note, `hub`≈structure/hub note, `index`≈register; the **catalog +
notes split** revives Luhmann's two-box system; topic stays out of folders.
**Process model deliberately departs** where an agent + a gate force it: a _standing_
axis (ZK had no agent to distrust) and _retraction_ states (ZK superseded via new
linked notes — Memoria keeps the lineage link, adds the state). `reference` was dropped
(it collided with ZK's "reference note" = our `source`, and added complexity without
value — an `evergreen` claim is the settled unit). **The docs must make this
alignment/divergence explicit when promoted.**

## Appendix C — profile → skills map

Existing skills are current `hermes-cli` commands; **(new)** are specified, not built.

| Profile · layer               | Existing skills                                                                                                     | New (proposed)                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Librarian** · book          | find · ingest · enrich · classify · query · export-prior-labels · obsidian-paper-note                               | candidate-rank · tension-surface · relation-suggest · distill-candidate-flag |
| **Analyst** · book            | scope-project · gap-report · cluster-map · cluster-mapping                                                          | writable-density · readiness-score · canvas-seed · gap-route                 |
| **Writer** · book             | draft · query · lint · promote · counter-outline                                                                    | claim-stub · outline-score · citation-bind                                   |
| **Fact-checker** · book/house | cite-check · claim-trace · similarity-check · find-duplicates · retraction-check · claim-checks                     | gap-card · gap-fix-propose · continuous-verify                               |
| **Engineer** · book           | code · commit · revert · workspace · scaffold                                                                       | —                                                                            |
| **Socratic** · desk           | socratic-processing · lens-reading                                                                                  | —                                                                            |
| **Linter** · house            | lint · schema-check · schema-migrate · graph-analyze · health-report · session-log · dry-run · structural-detectors | provenance-snapshot · archive (propose-only)                                 |

_(Dropped: `classification-confidence` — it served confidence auto-accept, which
contradicts the propose-not-dispose guardrail.)_

## Appendix D — dashboards (reconciled)

**The split that organizes them:** the **Inbox** is the _action queue_ — discrete
things that need you _now_ (it feeds Home's "what needs me?"). **Dashboards** are the
_browsable health views_ — where things _stand_ (read in a workspace or the weekly
review). Every dashboard is an **Inbox view**, a **Store health view**, or an
**agent-ops / ritual view**. All are Bases/Dataview, consumer-only, single-source; a
healthy vault shows them near-empty.

Re-grouped by **surface** (replacing the old agenda/health split):

| Surface             | Dashboard        | Kind         | Role in the new model                                                                        |
| ------------------- | ---------------- | ------------ | -------------------------------------------------------------------------------------------- |
| **Home** (Desk)     | _daily-health_   | —            | **absorbed into the homepage** — it _is_ the above-fold "what needs me?" glance              |
|                     | board-state      | Inbox view   | **the Inbox board** (a base over `inbox/`): active cards · review queue · retries · maturity |
| **Read**            | reading-pipeline | Store view   | sources awaiting classify (Inbox) + claims-by-maturity (`claims.base`)                       |
|                     | discuss-queue    | Store view   | sources worth discussing → **Ask / Socratic**; moves into the Read workspace                 |
| **Read / Write**    | open-questions   | Store view   | unconnected claims — the human's **synthesis backlog**                                       |
|                     | contradictions   | Store view   | `contradicts` relations — open tensions to resolve                                           |
| **Housekeeping**    | drift-watch      | view + Inbox | active / imminent drift; HIGH → Inbox **alert** (push)                                       |
|                     | loose-ends       | Store view   | structural debt (orphans · broken links · cosmetic); Notice → weekly                         |
|                     | weekly-review    | ritual       | the Friday aggregator of Notice-level findings                                               |
| **Bookkeeping-ops** | audit-log        | view + Inbox | provenance log; unhandled denies/dry-runs → Inbox **flag**                                   |
|                     | fleet-health     | Store view   | agent trust score / operational rollup                                                       |

**What the reconciliation changes:**

- **daily-health dissolves into the homepage** — the 30-second glance _is_ the
  homepage's above-fold Inbox summary, not a separate page.
- **board-state becomes the Inbox board** — a base over `inbox/`, the canonical view of
  the agent→human queue.
- **Action items route to the Inbox; dashboards keep the browse.** The _actionable_
  slices (review-requests, HIGH drift, unhandled denies) surface as Inbox items on
  Home; the dashboards stay the deeper "where things stand" views.
- **Synthesis vs structural, split by layer.** `open-questions` + `contradictions` are
  the _human's_ unfinished thinking (Read/Write); `loose-ends` + `drift-watch` are the
  _Linter's_ structural debt (Housekeeping). They overlap on "orphans" but through
  different lenses — keep both; don't collapse across the layer line.
- **Profile renames** update labels (`fleet-health`; `discuss-queue` → Socratic) —
  sequence with the doc migration (§9).

## Appendix E — the board (control plane)

Every unit of agent work — in **Bookkeeping** and **Housekeeping** — is a **card** on
the Hermes Kanban board (`kanban.db`, projected into Obsidian). The board is the
**trigger-and-lanes** end of the loop: a human action (or cron) creates a card; the
dispatcher assigns it to a **lane** (= a profile); the worker runs it; the result
resurfaces as an **Inbox** signal. **Card state is deliberately disjoint from note
state** — cards use `status` / `review_status`, notes use `lifecycle` / `maturity`
(§3.1) — so the two vocabularies never collide.

**Lanes = profiles** (the card's `assignee`, `memoria-<name>`). **No Socratic lane** —
Socratic runs synchronously at the Desk (ACP pane), never on the board.

| Lane                   | Profile · layer           | Typical cards                               |
| ---------------------- | ------------------------- | ------------------------------------------- |
| `memoria-librarian`    | Librarian · book          | catalog · enrich · classify · link          |
| `memoria-analyst`      | Analyst · book            | scope-project · gap-report · cluster-map    |
| `memoria-writer`       | Writer · book             | draft · outline                             |
| `memoria-fact-checker` | Fact-checker · book/house | cite-check · claim-trace · retraction-check |
| `memoria-engineer`     | Engineer · book           | code · commit                               |
| `memoria-linter`       | Linter · house            | lint · schema-check · graph-analyze         |

**Execution lifecycle** (`status`, Hermes-fixed 7-value enum):

```text
triage → todo → ready → running → done → archived
                  ▲        │
        (retry) ──┘        └─→ blocked ──(human unblock)──→ ready
```

`triage` = created, spec incomplete (dispatcher ignores until a human releases it) ·
`ready` = dispatchable · `running` = a worker owns it (WIP = 1/lane) · `done` = worker
finished (review overlay now applies) · `blocked` = unrecoverable, only a human clears
it (after `max_retries: 3`) · `archived` = terminal.

**Three orthogonal review dimensions** (so an agent verdict can never rubber-stamp a
human decision):

- `status` (execution) — where the work is.
- `review_status` (human) — `unreviewed → requested → approved` / `rejected`.
- `agent_recommendation` (Fact-checker / Linter) — `clean` · `issues-found` ·
  `inconclusive`.

**Rejection spawns a new card** (`supersedes: <id>`; original archived `superseded`) —
the same lineage-preserving move as the data model's supersession. Rework is never an
in-place edit; each card is one attempt, so the audit trail can't lie.

**Handoff payload** (self-contained, forward-looking): `goal · context · allowed_paths
· expected_outputs · review_checks`. `allowed_paths` may _narrow_ but never _widen_ the
lane's write scope (lane = ceiling, payload = floor; the policy MCP enforces).

**WIP limits** (the only governance — all back-pressure on the human bottleneck):
review queue = **5** `done` cards · **1** `running` card per lane · Writer lane bounded
(protects synthesis quality). Dispatcher polls every 60 s.

**Card ↔ Inbox.** The board is the _agent's_ work queue; the **Inbox** (§3.4) is the
_human's_ slice of it — `review_status: requested` with `review_owner: human`
(→ review-request), `blocked` cards, and agent-surfaced messages (candidate / gap /
flag / alert). Board = trigger + lanes; Inbox = signal.

## Appendix F — related backlog (issues, RFCs, explorations)

A live map between this redesign and the GitHub board + `rfc/`. Reviewed 2026-06-07.

### Issues the redesign answers — labelled `resolved-by-redesign`

| # | Question / request | Resolution |
|---|---|---|
| 221 | Conceptual work (rename folders, update layers, single storyline) | this redesign — the tracking issue for it |
| 153 | Auto-promote a claim at `evergreen`? | **No** — maturity is a property, not a gate (D5) |
| 213 | Dataview vs … | Bases is the view layer; Dataview in reserve (D3) |
| 224 | Ask chat transform | the **Ask** / **Patterns** assist verbs (D11) |
| 185 | ACP auto-export → inbox loop | the `trigger→lanes→signal` loop + Inbox (D6) |
| 191 | tags vs properties vs nested tags | faceted ontology + per-note properties (App. A / D2) |
| 180 | authoritative starter tag set | research-area seeded from OpenAlex (App. A) |
| 202 | link audit after `99-system` refactor | folder renamed `99-system`→`system/` (D2) |
| 142–145 | frontmatter UX (placeholders · `maturity` dropdown · fragile `relation` · buried `lifecycle`) | Bases/forms affordances once Catalog/Notes are Bases-backed (D3) |

### Issues to fold in as open design questions _(keep on the board)_

`#146` ACP-pane name → Desk/ACP naming · `#183` structured-capture forms → Catalog
entity creation (D3) · `#186` ingest a URL → Find/intake · `#181` email a fleeting
note → fleeting intake · `#193` crash-consistency → answered by Housekeeping-by-convention
and git, not ACID (D3) · `#188` LLM per profile → D8 + D11 model routing · `#196` pin
skills to a task → D11 + board · `#177` tutorial names → Read/Write naming · `#212`
"tutorial to the method" → App. B + naming discipline.

### RFCs — folded (annotated `folded_into: memoria-redesign`)

| RFC | Folds to |
|---|---|
| 03 Dedicated review-note type | Inbox `review-request` (D6) |
| 04 Retriever/Scout profile | Find assist / Librarian discovery / Analyst (D7/D8) |
| 05 Ratchet (qmd similarity gate) | near-tie/dedup residue (R2) + Fact-checker |
| 09 Profile compilation | team-role profile definition (D8) |
| 10 Skill governance & lifecycle | pattern-library governance (D11) |

**Tension — not folded:** RFC-08 (configurable blocking|advisory gate) conflicts with
**D12** (propose-not-dispose is structural and uniform). Allow only as a
comparison-study toggle.

### Explorations

- `schema-and-retrieval`, `triage-improvements` → **resolved-by-redesign**.
- `discovery-loop`, `integrations`, `measurement-and-verification` → **partially
  folded** (`folded_into`, reconcile remainder).
- `publication-strategy` → **parked** with Projects (§9 "to revisit").
- `multi-machine-deployment`, `multi-vault-and-multi-machine`,
  `classical-method-displacements` → independent.

### #220 — obsidian-biblib (analysis)

**What it is:** a single Obsidian plugin that stores each reference as a Markdown note
with **CSL-JSON in YAML frontmatter** — no external DB; plain-text, git-friendly. Native
metadata import via **DOI / ISBN / PubMed / arXiv / URL**, Pandoc citekey generation,
PDF attachment handling, BibTeX/CSL-JSON export.

**Fit:** its _philosophy matches Memoria exactly_ (plain-text, note-per-reference,
in-vault), and it directly addresses **#187** (Zotero-as-an-Obsidian-plugin) and
**#186** (ingest a URL) — it could replace the external Zotero-app dependency with a
single in-vault plugin.

**The blocker:** biblib stores **nested CSL-JSON** frontmatter and explicitly _bypasses
Obsidian's native properties_ — which is **incompatible with the Catalog's
Bases-flat-properties requirement** (D3). Bases queries flat properties
(`citekey · doi · authors[] · year · venue`); nested CSL-JSON won't surface.

**Recommendation:** _adopt the engine, not the storage shape._ Take biblib's
identifier-import + citekey generation (in-vault, resolving #186/#187), but **flatten
its CSL-JSON into Memoria's flat Catalog schema** for Bases. Worth a spike/RFC, not an
immediate swap; informs ADR-05 (Zotero backbone), ADR-30 (ingest), and D3.

### Scoping

`#198` (decide v0.2 scope): this redesign supersedes **ADR-01** and **ADR-04** and
renames most profiles/folders — **major-version-sized**. Sequence it as superseding
ADRs across versions, not a single v0.2 drop.
