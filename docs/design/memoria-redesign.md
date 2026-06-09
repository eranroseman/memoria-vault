---
topic: proposals
title: Memoria redesign — architecture
status: exploration
created: 2026-06-07
---

# Memoria redesign — architecture

> **Status: exploration** (a capability bundle in the RFC pipeline). The synthesized
> target vision — a near-total architecture redesign. **Not yet adopted:** firm
> decisions graduate to **ADRs** (each setting `superseded_by` on the ADR it replaces).
> The rationale and alternatives weighed are preserved in
> [memoria-redesign-decisions.md](memoria-redesign-decisions.md), the seed for those ADRs.
>
> **Premise: strictly solo, personal.** One judgment-owner.

## What this changes (ADR impact)

If adopted, this **supersedes** ADR-01 (→ two structural layers + three actors) and ADR-04 (→ type-first
folders); **amends** ADR-02, 08, 13, 17, 19, 30; **creates** ~7 new ADRs (categories ·
Catalog-in-Bases · Inbox · Read/Write · lifecycle + maturity · pattern library ·
two-kinds-of-decision); and **reinforces** ADR-03/05/10/21/22/24/33. The
decision-by-decision map is **Appendix G**; the rationale and alternatives weighed are
in [memoria-redesign-decisions.md](memoria-redesign-decisions.md). Each firm decision
graduates via the [decisions pipeline](../../adr/README.md).

## Contents

1. What Memoria is
2. Structure and actors
3. The Vault — categories, types, state
4. The actors — co-PI, agents, engines
5. The Linter engine
6. The working surface
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
- Appendix H — the project workflow (v0.2)

---

## 1. What Memoria is

Memoria is an **opinionated, phase-gated, bounded, personal tool for thinking and
writing** — a durable research vault that compounds across months and years.

- **Personal** — thinking is private and separate from communication; notes stay
  unfiltered, preserving raw reasoning before audience-aware editing sanitizes it.
- **Opinionated** — enforces specific workflows; eliminates setup paralysis.
- **Phase-gated** — defined phases with explicit outputs; nothing becomes a claim or
  deliverable without human review.
- **Bounded** — agent autonomy is structurally constrained; the PI decides what is
  worth keeping and what becomes canonical.

**Central insight:** maintaining a knowledge base is a **bookkeeping problem, not an
intelligence problem.** Memoria gives the bookkeeping to the agent and keeps judgment
human. It solves **capture without synthesis** and **synthesis without rigor**. It is
not an autonomous scientist, a chat assistant, or a one-shot research tool.

**The naming discipline:** everything the user sees is named by the word the user would
say (the "what are you doing?" test); technical names stay internal — so the complexity
hides behind a vocabulary the user already owns.

---

## 2. Structure and actors

Two simple structural layers, and three kinds of **actor** that move between them.

### The two layers

| Layer | What it is |
|---|---|
| **Workspaces** | where the PI works; results resurface here |
| **Vault** | where everything is kept (the Obsidian vault — files & folders) |

Everything else is an actor acting on the Vault on the PI's behalf. *(The earlier
model had four layers — but "Bookkeeping" and "Housekeeping" were really* what the actors
do, *not places. Folding them into the actor tiers removes the redundancy where the
Linter was both "the Housekeeping layer" and "an engine.")*

### The three actors

| Actor | Posture? | LLM? | On the board? | What it is | Examples |
|---|---|---|---|---|---|
| **Engines** | no | no | no | pure mechanism — you *run* it | ingest/cataloging · the Linter · search · the verification sweeps |
| **Agents** | yes | yes | yes (lanes) | posture + judgment — you *delegate* to it | the co-PI + the background lanes (Librarian · Writer · Peer-reviewer · Engineer) |
| **The PI** | — | — | — | the only one who promotes to canonical | you |

We call the human **the PI** (Principal Investigator) — the role name, matching the
co-PI; *"human-in-the-loop"* stays the design **concept**.

**The key correction over the old "seven profiles": deterministic work is an engine, not
an agent.** You don't *dispatch* a linter or an ingest pipeline — you *run* it. An agent
has a **posture** (a stable stance) and makes LLM judgments; an engine is pure mechanism.
The two work-kinds map onto the actors: **processing knowledge** (in response to a human
action) is agent work; **maintaining integrity** (on a trigger) is engine work — the
distinction the old Bookkeeping/Housekeeping layers carried, now carried by the actors
themselves. The loop, everywhere:

```text
   Workspaces (PI acts) ──▶ agent lanes ──▶ Inbox (signal) ──▶ Workspaces …
```

The "gate" is just the PI's next action, prompted by an Inbox signal.

### The co-PI fronts everything

The PI converses with **one agent — the co-PI** — and **delegates** the rest. The
co-PI is the conversational front at the desk (it subsumes the old **Socratic** role);
the specialist agents (Librarian · Writer · Peer-reviewer · Engineer) run as **background
lanes** it delegates to, never as separate chats. Concentrating every conversation in one
agent lets it use Hermes' self-improving loop — **memory · /goals · skills** — so it
compounds into a genuine co-PI rather than a stateless assistant. (Detail: §4.)

The **full runtime stack** — the seven system-architecture layers (PI · Interface ·
co-PI · tasks · MCP · engines · vault), the MCP sandbox boundary, and the
*decisions-down / information-up* flow — is in
[system-architecture.md](system-architecture.md). This section is the *cognitive* model;
that doc is the *build* view, and they map one-to-one.

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
.obsidian/    hidden Obsidian app config (Bases definitions, graph color-groups, layouts)
```

(`category` = top level, e.g. Catalog; `type` = a member, e.g. paper.) The folder is
named for its **content** (`catalog/`), not for a doer — both the ingest engine and the
Librarian agent operate *on* it.

### 3.1 Relationships vs links — two kinds of connection

| | **Relationships** (Catalog) | **Links** (Notes) |
|---|---|---|
| examples | paper *cited-by* paper, *authored-by* author, *published-in* venue, DOI→ORCID | claim *supports/contradicts* claim, claim ∈ hub |
| nature | **given** — objective facts about sources | **authored** — connections *you* draw |
| built by | the **ingest engine** (from metadata APIs), mechanical | agent **proposes** candidates, **PI confirms** |
| gated? | no — it's a fact | yes — the ③ connect gate |
| field | entity `relationships` (in the Base) | note `links:` (some typed: supports/contradicts) |

"Relationships are given; links are authored." `links:` (typed note-links) replaces the
old `relations:` field — and avoids the relations/relationships near-synonym clash.

### 3.2 State — one lifecycle vocabulary

Everything the PI sees uses **one chain**:
`proposed → provisional → current → retracted → archived` (each type uses a subset).
`archived` is a **state**, not a folder — the item stays in its type-home and drops from
active views (preserving links + provenance; no move).

**Inbox cards use this same chain** (a card awaiting you is `proposed`; you act → `current`;
closed → `archived`). The Hermes-native execution `status` (triage→…→done) stays the
**hidden mechanic** the user never sees (Appendix E); queries scope to the `inbox/`
category, so card-state and note-state never collide despite sharing the vocabulary.

### 3.3 Maturity and agent-recommendation — soft signals, not states

Two **soft 3-tier judgment signals**, the same *kind* but different *subjects*:

- **maturity** (`seedling → budding → evergreen`) — how *developed* a claim is. PI-set.
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

**PROJECTS** — work artifacts, project-scoped *(the producing workflow is Appendix H)*

| type | states | notes |
|---|---|---|
| report | current → archived | agent analysis (corpus-map, gap-report, verification-report) — **read-only; informs, doesn't gate** |
| sketch | proposed → current → archived | planning scaffold (framing, outline, canvas) |
| composition | provisional → current → archived | the evolving output; `plan → draft → deliverable` are **states** (deliverable 🔒) |
| code | current → archived | code handoff |

**Reports inform; drafts gate.** A report is an agent-generated read-only analysis the
PI *consults* (regenerable → `current/archived`); its findings become Inbox `gap`/`flag`
cards, but the report itself surfaces as an FYI, never an approval. A composition is the
PI's work heading to a **gated** deliverable. **Batch screening:** when a report lists
many items each needing a keep/reject call (a relevance scan, a literature search), the
report **is** the review surface — a Bases-backed worklist where each row carries a
lifecycle `decision` the PI toggles (accept → linked to the project; reject → archived +
reason), acted on at *group or item* granularity (like a systematic-review screening
tool). The Inbox gets **one aggregate work-prompt** ("N sources to screen for
‹project›"), never N cards (§8).

**INBOX** — agent→human messages (the PI's slice of the board) · agent-built · transient

| type | description | raised by |
|---|---|---|
| candidate | a *found* source proposed for intake | Librarian (`find`) |
| gap | a *missing*-source need | Librarian / Peer-reviewer |
| flag | a verification / integrity issue | Peer-reviewer / Linter |
| alert | drift / retraction notice | Linter / Peer-reviewer |

(There is no `review-request` type — a card awaiting your gate is just any card in the
`proposed` state, pointing at the artifact under review.)

### 3.5 Bases as the Vault's view layer — and how the Linter keeps it sound

A Base is a saved **view over note frontmatter** — every row is a file; the data lives in
the notes. Used across the Vault:

| category | base usage |
|---|---|
| Catalog | **essential** — papers/people/orgs/venues; a per-entity embedded base (`this.file`) shows "this paper's claims / this author's papers" |
| Inbox | **high** — one base grouped by type = the board / queues |
| Notes | **per-type** bases (`claims.base` by maturity/topic, `sources.base` reading list, `fleeting.base` inbox) |
| Projects | low–med (folder suffices; a cross-project compositions-by-state base is handy) |

Bases has **no integrity guarantees** — no schema, no constraints; a renamed link or a
typo'd property silently breaks a record. That gap is exactly what the **Linter
engine** fills, concretely: `schema-check` validates each record against its **type
schema** — required fields present, value types correct, enum values in-vocabulary, and
`links:`/`relationships` resolve to real targets — keyed off a `type:` discriminator. It
flags malformed records, broken/renamed links, and orphans as Inbox `flag`s. So **Bases
is the view layer, the Catalog is the source of truth, and the Linter is its
integrity guarantor.** (Dataview / the Bases API stay in reserve for citation-graph
traversal.)

---

## 4. The actors — co-PI, agents, engines

The PI **delegates** work and it runs in the background: **trigger → lane → signal**.
An action (a palette command, or a slash command to the co-PI) creates a card on the
board, assigned to a lane; the lane's agent runs it; the result resurfaces as an
**Inbox** message. It should feel like **a teammate working in the background** —
invisible until it has something for you.

**A profile is a posture; skills attach per lane.** A profile's stable trait is its
**posture** (a stance like *faithful* or *skeptical*); the **skills** it runs are
assigned to the *lane*, not baked into the profile. So one posture can run several lanes
as different *modes*, and lanes can share skills. **The PI converses with one agent —
the co-PI — and delegates to the rest.**

### 4.1 Two activities, six delegable tasks

The PI's work is **Read** (take knowledge in) and **Write** (put work out) — two
*activities*, not a six-step pipeline the PI walks. Within them, six **tasks** can be
delegated to a background lane (each pairs a human verb, an agent task, and an Inbox
item):

| Activity | # | Human verb | Delegable task | Lane (agent) | Inbox |
|---|---|---|---|---|---|
| **Read** | ① | sort | catalog | Librarian | candidate |
| | ② | read & note | extract | Librarian | (stubs) |
| | ③ | connect | link | Librarian | (link proposals) |
| **Write** | ④ | plan | map | Librarian | gap |
| | ⑤ | write | draft | Writer | — |
| | ⑥ | check | verify | Peer-reviewer | flag |

The tasks are **individually triggered, not a set** — a human gate (often a long gap)
sits between each: a source is catalogued; *much later, if ever*, distilled (extract);
only after a claim is written does linking fire. Catalog/extract/link/map are four lanes
of the one **Librarian posture**, not four profiles. All six are reachable from either
perspective via the palette; each perspective just surfaces its natural tasks first (§6).
Gaps found in ④/⑥ become Inbox `gap`s that re-trigger ① — the loop that compounds.

### 4.2 The agents

The PI talks to the **co-PI**; four background agents run as lanes it delegates to.
Each follows the Hermes profile model: a **SOUL.md** (posture / system prompt),
**config.yaml** (model + tools), **skills/** (per-lane), **mcp.json** (connections),
**AGENTS.md** (the shared "how we work in this vault" instructions, distinct from SOUL's
personality), and **distribution.yaml** (the packaged repo).

**co-PI** — *posture: reflective thinking-partner; the only agent you converse with.*

- *Where:* **Workspaces** — the desk pane (ACP), interactive, **not on the board**.
- *Does:* holds the conversation, asks the sharpening questions (the old **Socratic**
  role, folded in), and **delegates** tasks to the background lanes (the Ask / Explore
  assists are it, in the moment). Read-only itself — it can run any read-only skill
  directly, but every *write* goes out as a delegated task card.
- *Why one:* concentrating every conversation here lets it use Hermes' learning loop —
  **memory · /goals · skills** — and grow into a true co-PI. It never writes canonical
  content; its product is your sharpened thinking and well-routed work.

**Librarian** — *posture: faithful* (include generously and report state; the gate filters).

- *Lanes:* the four processing tasks — **catalog · extract · link · map** (now also the
  old Analyst's map/scope work — a research librarian does both intake and lit-search).
- *Proposes:* a comparative `[!brief]`, draft classifications, claim-stubs, note-link
  candidates, corpus-/gap-/cluster-maps, a writability read, scored outlines, a seeded
  canvas — all into staging.
- *Boundary:* read-only over canonical content; writes only staging / project scratch;
  never canonizes. The mechanical half of cataloging (fetch metadata, extract text, build
  **relationships**, create records) is the **ingest engine**, not the agent.

**Writer** — *posture: generative, draft-only* (review-gated).

- *Lane:* **draft**.
- *Proposes:* prose drafts with bound citations, and outline options.
- *Boundary:* drafts never land directly in `claims/` or `deliverables/`; no fact-checking
  (that's the Peer-reviewer).

**Peer-reviewer** — *posture: skeptical, and deliberately independent* (flag, don't fix).

- *Lane:* **verify** — the **formal, independent review gate** (the academic peer-review
  pass), distinct from the co-PI's *informal, continuous* sparring: the *judgment* checks
  (citekey resolution, claim→source tracing, near-duplicate adjudication) + the conceptual
  red-team *for soundness, not just facts*; spawns `gap`/`flag` cards.
- *Boundary:* **independent of the Librarian** — the agent that synthesizes must not also
  grade its own work (separation of duties; the anti-rubber-stamp principle, §9). The
  *deterministic* sweeps (retraction, dedup, broken-citation) are **engines**, not this
  agent (§4.3).

**Engineer** — *posture: delegating* (a two-agent boundary).

- *Lane:* **code**.
- *Proposes:* a `code` handoff, provenance, and per-task commits.
- *Boundary:* does not write code itself — an external coding agent does; the Engineer
  scaffolds the handoff and owns the commit/revert gate.

The **bounded rule** holds for all: they **propose** (into staging / `_proposed_*`); the
**PI disposes**. Promotions, the `retracted` decision, and gated-zone writes are
PI-only, enforced by the policy MCP. (Skills per profile: Appendix C.)

### 4.3 The engines (deterministic, no posture)

Not agents — pure mechanism, triggered or scheduled, never on the board:

- **Ingest / cataloging engine** — fetches metadata, extracts content, builds entity
  **relationships**, creates Catalog records. The mechanical core of ①. *(ADR-30's
  pipeline already works this way.)*
- **Search** — deterministic retrieval over the vault (the `query` skill). Powers "Search"
  (§6.3) and finds link candidates before the Librarian proposes (§3.1).
- **Verification sweeps** — scheduled, deterministic checks split out from the old
  Peer-reviewer: retraction lookups, near-duplicate detection, broken-citation detection.
  Their *findings* become Inbox `flag`/`alert`s; the *judgment* verification stays the
  Peer-reviewer (§4.2).
- **The Linter** — §5.

---

## 5. The Linter engine

**The Linter is an engine, not an agent** — zero-LLM, no posture, no board lane. It's the
deterministic integrity guard, run on **cron + as a CI gate**. It validates frontmatter
schema, link/relationship resolvability, orphans, and graph health; rotates logs; and
supplies the **schema integrity Bases lacks** (§3.5). Findings surface as Inbox
`flag`/`alert` at a graded loudness (§6.4). `archive` is **propose-only** — the Linter
stages the move; the PI executes it (the one move actors never make).

---

## 6. The working surface

Where the PI works; everything else serves it. Governed by **visual discipline**:
*invisible during normal use, legible when something needs a decision* — it feels like
reading and writing most of the time.

### 6.1 One working surface, two perspectives

There is **one working surface plus Home** — not two walled-off workspaces. The surface
adapts to a **Library** or **Project** perspective (a saved layout), and **every task is
reachable from both** via the palette; the perspective just surfaces its natural tasks
and panes first. Reading and writing interleave too tightly for a hard wall.

| Surface | Holds |
|---|---|
| **Home** | the "what needs me?" surface (triage / overview) |
| **Library** perspective | the *Read* surface — source + notes + backlinks + co-PI + reading queues (tasks ①②③) |
| **Project** perspective | the *Write* surface — project tree + composition + linked claims + verification (tasks ④⑤⑥) |

**Deep vs. task work stays separated.** The perspectives are for **deep work** (close
reading, the project brief, the canvas, drafting); **task-mode** triage (clearing the
Inbox, confirming link proposals, screening a relevance report) lives in **Home / the
Inbox**, batched — it never interrupts the deep surfaces. They are different mindsets and
should not be mixed.

### 6.2 Homepage — above-fold "what needs me" + progressive disclosure

The front door (`home.md`): a **launchpad, consumer-only** (embeds dashboards, owns no
logic — so it can't drift or error, and degrades to empty). Above the fold: the **Inbox
summary** ("what needs me?"). Below: collapsible detail dashboards (Appendix D). So
homepage, Inbox, and dashboards are one calm surface — a 30-second glance that opens into
depth on demand. The **status line** is the always-visible ambient indicator (Linter +
queue counts).

### 6.3 Active assistance

The PI invokes an assist *from the working surface* (command palette · assist pane ·
text selection); the result is always a **proposal in staging**. Each assist is a
**(posture × skill)** applied to the current context — i.e. the same actors, invoked
interactively rather than on the board:

| Verb | What it does | Provided by | Where |
|---|---|---|---|
| **Find** | discover **new** sources from outside → Inbox candidates | Librarian posture | Library |
| **Search** | retrieve from **what you have** (vault) | the search engine (deterministic) | both |
| **Patterns** | run a curated pattern → a proposal | the pattern's declared posture | both |
| **Ask** | grounded questioning | co-PI | both |
| **Draft** | generate a proposed artifact (stub / outline / prose) | Writer | Project |
| **Explore** | elicit framings / branches | co-PI | Project |

### 6.4 Graded loudness — defined outcomes

| Level | Outcome |
|---|---|
| **Quiet** | logged only; aggregated in the weekly review; no interruption |
| **Notice** | appears in the relevant dashboard + weekly review; no push |
| **Alert** | appears in Home's "what needs me" + Daily Health; pushed; does **not** block |
| **Block** | blocks the action (dispatch / promotion) until acknowledged; pushed |

The test for push vs dashboard: *does it change what the PI does in the next 30 minutes?*

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
- **Finding the right one:** the working-surface **pattern-picker** (a `patterns.base`
  catalog) filters by the current activity / task / selection — it surfaces only the patterns
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

Every place the PI acts is one of **two kinds**, and they need different Inbox items:

- **Approval gate** — the PI reviews *agent-produced output* and accepts/rejects.
  Rubber-stamp risk is high, so the item must carry **reasoning + verdict** (§9), never a
  bare "OK?".
- **Work prompt** — the agent signals it's *time for the PI's own thinking/writing*.
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
| archive | approval (PI-only move) | ✓ when stale | archival proposal **+ reason** |
| re-adjudicate (retraction) | approval | ✓ on invalidation | retraction `alert` + adjudication options |
| near-tie | approval (same/diff/unsure) | ✓ before a commit | the two objects, side by side |

**The rule:** *an Inbox item a human can clear without reading is a design smell* —
either give it real decision material, or automate it. **classify** fails this test, so
it's automated. The strongest gates (certify, link-confirm, re-adjudicate) are approvals,
so each must ship its reasoning. **High-cardinality** per-item decisions (screening a
relevance report) are the exception that proves the rule: they belong in a **batch
worklist** (§3.4), not N cards — one aggregate work-prompt points at the worklist.

---

## 9. Design guardrails

- **Decision transparency (the primary guardrail).** Assume anything promoted to the
  PI *will* be approved — so the strongest guard is to hand the PI the **reasoning:
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

- **Projects / the Project perspective** — the project workflow is now defined in
  **Appendix H** (v0.2: brief → relevance scan → lit-search → canvas → outline). Still
  open: the `plan→draft→deliverable`-as-states model, and **write · code · verify** detail
  — **v0.3**.
- **Profile consolidation** ripples through existing docs — old Librarian + Analyst now
  unify as **Librarian** (catalog·extract·link·map); Verifier splits (judgment →
  **Peer-reviewer**, sweeps → engines); Coder → **Engineer**; **Socratic folds into the
  co-PI**; Linter + sweeps are engines — sequence the migration.
- **`relations:` → `links:`** field rename (notes) + adding entity `relationships`
  (Catalog) — amends ADR-08; plan the migration.
- **Task prefix in skill names** (`catalog:`/`verify:`…, not `read:`/`write:`) — confirm
  via an eval that the prefix aids selection (Appendix C).

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

**Skill naming: `<task>:<verb>-<object>`** (snake `<task>_<verb>_<object>` if serialized
as an MCP tool) — the **task/lane** is the prefix (`catalog · extract · link · map · draft
· verify · find · search`), the verb is from a **closed set** (`extract · link ·
summarize · check · rank · draft · outline · score`), and the artifact is the object (no
result slot). Examples: `catalog:enrich-record` · `extract:summarize-source` ·
`link:suggest-claim` · `map:report-gaps` · `verify:check-citation` · `search:find-source`
· `draft:write-section`. The task prefix matches the **board card / lane**, so a skill's
name says which task delegates it *(the earlier `read:`/`write:` activity prefix was too
coarse to disambiguate).*

Existing skills are current `hermes-cli` commands; **(new)** are specified, not built.

| Actor (agent / engine) | Existing skills | New (proposed) |
|---|---|---|
| **co-PI** · agent (conversational, desk) | socratic-processing · lens-reading | ask · explore · delegate-task |
| **Librarian** · agent (catalog · extract · link · map) | find · enrich · classify · query · scope-project · gap-report · cluster-map · cluster-mapping · obsidian-paper-note · counter-outline | candidate-rank · tension-surface · relation-suggest · distill-candidate-flag · writable-density · readiness-score · canvas-seed · gap-route · map:claim-graph · map:hub-canvas |
| **Writer** · agent (draft) | draft · query · promote | claim-stub · outline-score · citation-bind |
| **Peer-reviewer** · agent (verify, judgment) | cite-check · claim-trace | gap-card · gap-fix-propose |
| **Engineer** · agent (code) | code · commit · revert · workspace · scaffold | — |
| **Ingest** · engine | ingest · enrich (mechanical) | build-relationships · create-records |
| **Search** · engine | query | — |
| **Verification sweeps** · engine | similarity-check · find-duplicates · retraction-check · claim-checks | continuous-verify |
| **Linter** · engine | lint · schema-check · schema-migrate · graph-analyze · health-report · session-log · dry-run · structural-detectors | provenance-snapshot · archive (propose-only) |

The mechanical half of cataloging (fetch · extract · build relationships · create records)
runs in the **Ingest engine**, not the Librarian; the **deterministic** verification
sweeps are an engine, while the *judgment* checks (cite-check · claim-trace) are the
**Peer-reviewer**. *(Dropped: `classification-confidence` — it served confidence
auto-accept, which contradicts the propose-not-dispose guardrail.)*

## Appendix D — dashboards (reconciled)

The **Inbox** is the *action queue* — discrete things that need you *now* (it feeds Home's
"what needs me?"). **Dashboards** are *browsable health views* — where things *stand*. All
are Bases/Dataview, consumer-only; a healthy vault shows them near-empty. Grouped by surface:

| Surface | Dashboard | Role |
|---|---|---|
| **Home** | *daily-health* | absorbed into the homepage — the above-fold glance |
| | board-state | the Inbox board (a base over `inbox/`) |
| **Library** | reading-pipeline | sources awaiting classify + claims-by-maturity |
| | discuss-queue | sources worth discussing → Ask / co-PI |
| **Library / Project** | open-questions | unconnected claims — the synthesis backlog |
| | contradictions | `contradicts` links — open tensions |
| **Maintenance** (engines) | drift-watch | active/imminent drift; HIGH → Inbox alert |
| | loose-ends | structural debt; Notice → weekly |
| | weekly-review | the Friday aggregator |
| **Agent-ops** | audit-log | provenance log; unhandled denies → flag |
| | fleet-health | agent trust score / operational rollup |

**Synthesis vs structural, split by actor:** `open-questions`+`contradictions` are the
*PI's* unfinished thinking (Library/Project); `loose-ends`+`drift-watch` are the *Linter
engine's* structural debt — kept separate, not collapsed.

## Appendix E — the board (control plane)

Every unit of **agent** work is a **card** on the Hermes Kanban board (`kanban.db`,
projected into Obsidian): the **trigger-and-lanes** end of the loop. A human action (or
cron) creates a card; the dispatcher assigns it to a **lane** (a background agent); the
worker runs it; the result resurfaces as an **Inbox** signal. (Engines run *off* the
board — on cron/CI, not as cards.)

**Lanes = the background agents** (`assignee = memoria-<name>`: Librarian · Writer ·
Peer-reviewer · Engineer). **No co-PI lane** — it converses at the desk (ACP pane), never
on the board — and **no engine lanes** (ingest · search · sweeps · Linter run on cron/CI).

The board's native **`status`** (`triage → todo → ready → running → done → blocked →
archived`) is the **hidden execution mechanic**. The human-facing card state is the
**lifecycle chain** (§3.2). Three orthogonal review dimensions keep an agent verdict from
rubber-stamping a human decision: `status` (execution) · the PI's lifecycle state ·
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
(by convention + git, not ACID) · `#188` LLM per profile · `#196` pin skills
to a lane · `#177` tutorial names.

### RFCs folded (`folded_into: memoria-redesign`)

RFC-03 (→ Inbox card-in-`proposed`) · RFC-04 (→ Find / Librarian) · RFC-05
(→ near-tie/dedup + Peer-reviewer) · RFC-09 (→ profile = posture, §4) · RFC-10 (→ pattern
governance, §7). **Tension:** RFC-08 (advisory gate) vs the transparency guardrail — allow
only as a comparison-study toggle.

### Explorations

`schema-and-retrieval`, `triage-improvements` → resolved; `discovery-loop`, `integrations`,
`measurement-and-verification` → partially folded; `publication-strategy` → parked with
Projects; deployment/`classical-method-displacements` → independent.
[`graph-visualization`](graph-visualization.md) → captured separately (typed
claim/relationship-graph projections; the Librarian gains the `map:claim-graph` /
`map:hub-canvas` skills; activates #197's deferred NetworkX/InfraNodus threads).
[`system-architecture`](system-architecture.md) → the 7-layer runtime stack + the
cognitive-model mapping + the MCP boundary.

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

- **ADR-01** (three-layer architecture) → **two structural layers** (Workspaces · Vault)
  with **three actors** (engines · agents · the PI); "Bookkeeping/Housekeeping" are
  *what the actors do*, not separate layers. (Full stack: [system-architecture.md](system-architecture.md).)
- **ADR-04** (lifecycle-over-topic folders) → **type-first folders** (one category per
  folder; lifecycle is a state property, not a folder number).

**Amends**

- **ADR-02** (seven specialist profiles) → **one co-PI** (conversational, subsumes
  Socratic) + **four background agents** (**Librarian · Writer · Peer-reviewer · Engineer**),
  each defined by a **posture**; the **Linter and the deterministic verification sweeps
  are engines**, not agents. The old Librarian + Analyst unify as **Librarian**; the old
  Peer-reviewer splits by determinism (judgment → **Peer-reviewer**, sweeps → engines).
- **ADR-08** (typed relations) → notes carry **`links:`** (some typed
  supports/contradicts); entities carry **`relationships`** — two distinct kinds.
- **ADR-30** (deterministic ingest) → **cataloging splits**: a mechanical *ingest
  engine* + the Librarian agent's two LLM steps.
- **ADR-13** (homepage) → above-fold "what needs me" (Inbox) + progressive disclosure.
- **ADR-17** (candidate frontmatter) → `candidate` is an **Inbox** type.
- **ADR-19** (agent-proposed MOCs) → MOC renamed **hub**.

**Creates (new ADRs)**

- Four categories (**Catalog · Notes · Projects · Inbox**) + the category/type taxonomy.
- Catalog entities in **Obsidian Bases**; the **Linter engine** supplies the integrity
  Bases lacks.
- **Inbox** as the agent→human message category (kanban + dashboards are its views).
- **Read / Write** as the activity spine, on **one working surface (Library/Project perspectives)**.
- The **co-PI + delegation** model — one conversational agent; specialists are background
  lanes.
- Universal lifecycle chain + **maturity as a property**; **drop the `reference`** type.
- The in-vault **pattern library** (`system/patterns/`).
- **Two kinds of human decision** (approval gate vs work prompt) + the
  decision-transparency guardrail.

**Aligns with (reinforced)** — ADR-03 (structural gate), 05 (Zotero backbone),
10 (claim supersession), 21 (autonomy ceiling), 22 (Hermes runtime),
24 (single-researcher), 33 (BERTopic clustering).

## Appendix H — the project workflow (v0.2)

A project moves through phases — **iterative, not linear**, but with a natural progression
from *gathering* (Library side) to *producing* (Project side). **v0.2 defines phases 1–5**
(brief → outline); **write · code · verify (6–8) are v0.3** — sequenced, not yet detailed.
Each phase composes the six delegable tasks (§4.1); the agent is chosen by **posture**.

| # | Phase | Agent | Input | Output (type) | Gate / mechanism |
|---|---|---|---|---|---|
| 1 | **Brief** — the research question | **co-PI** (dialogic) + PI; Writer may draft prose | the PI's intent | a **project brief** (`sketch`) — scope · problem · question | deep work; *guides every later phase, so getting it wrong cascades* |
| 2 | **Relevance scan** | **Librarian** (`map`) | brief + the Catalog | a **relevance report** (`report`) | per-source keep/reject **batch worklist** (D37); accepted → linked to the project |
| 3 | **Literature search** | **Librarian** (`find` + `map`) | brief + linked sources | a **new-sources report** (`report`) | same worklist shape; recommends catalog additions, then re-links |
| 4 | **Canvas** — the thread | **Librarian** proposes (`canvas-seed`); **PI** authors | linked claims/sources | a **canvas** (`sketch`) | deep work; the ZK-style connecting phase |
| 5 | **Outline** | **Writer** (`draft`) | the canvas | an **outline** (`sketch` → `composition`) | **one-way seed** from the canvas, then it diverges (no two-way sync) |
| 6 | **Write** | **Writer** (`draft`) | outline + claims | `composition` (draft → deliverable 🔒) | **v0.3** |
| 7 | **Code** | **Engineer** (`code`) | composition | `code` handoff | **v0.3** |
| 8 | **Verify** | **Peer-reviewer** (`verify`) | the draft / deliverable | the ⑥ certify gate | **v0.3** |

**The relevance / new-source report structure** (phases 2–3): a *scope + screening header*
(the question, the catalog scanned, and an include/exclude line *with reason* per source —
PRISMA-style); a **synthesis matrix** (one row per source: theme · finding · relevance
verdict); then **thematic sections** — grouped by concept, not source-by-source — each
source carrying *what it is / why relevant / what to adopt-borrow-reject + rationale*.
Sources are grouped by their **`relationships`** (paper + repo, review + source, paper +
counter-paper), so related items are judged together.

**Two principles carried in:** reports are **project artifacts** (`projects/<p>/reports/`),
browsed in the Project perspective, each surfacing **one aggregate work-prompt** — never N
cards (D37); and the loop **compounds** — gaps found in ④/⑥ become Inbox `gap`s that
re-trigger intake (①).
