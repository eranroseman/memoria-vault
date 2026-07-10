# User workflow — agent, editor, Memoria plugin — 2026-07-09

The target experience across the three components, under the decided
architecture (`roadmap.md` item 12 reactive substrate + Tier 3 surface
strategy). Two views, deliberately distinct: the **inquiry loop** (the
researcher's arc — how a project actually proceeds) and the **daily
rhythm** (the moment-to-moment interaction pattern inside it). An earlier
draft of this document narrated the system's information-flow topology
(capture → export) as the workflow; corrected by the owner — the
researcher's workflow is pull-driven: inquiry first, capture fourth.

Division of labor throughout: **the editor is where judgment lives, the
plugin is how the vault looks back at you, the agent is the voice and
hands.** Everything funnels through the same envelope and queue; plugin
and agent never write files directly; direct PI edits are observed and
revalidated.

## The inquiry loop (the arc)

1. **A project opens.** A question worth months: new project, thesis stub
   in the editor, steering.md updated with the inquiry's priorities — the
   one file that mechanically re-aims the whole system's attention.
2. **Gap analysis before any reading.** "What do I already have, and what's
   missing?" — analyze_gaps against the *existing* vault: which prior
   claims bear on this thesis, what's under-warranted, which topics sit
   undigested, where the argument is thin. This is where compounding shows:
   project N starts from everything projects 1…N−1 built, not from zero.
   (Also the best-built co-PI machinery in the product today — the first
   thing a new project experiences is the strongest thing Memoria has.)
3. **Discovery.** The citation neighborhood and steering-ranked candidates
   propose what to read; the exploration channel adds coverage and — by
   design — the contrary channel surfaces what disagrees with the thesis.
   Triage in the inbox: capture-worthy, defer, reject.
4. **Capture — pulled, not pushed.** Now sources enter: the DOIs and PDFs
   the gaps and discovery pointed at, not whatever crossed a feed. Capture
   → enrichment → checked → engine-authored interview (grounding questions
   about *this* source against *this* thesis) → digest with the interview
   sealed in.
5. **Knowledge building.** Digests → claim notes → typed links; tensions
   surface as contradiction candidates; argument health on the project
   updates as edges accumulate.
6. **Iterate 2→5.** Re-run gaps: the argument stage advances, new gaps
   open, discovery refreshes against the grown graph. The project drives
   repeated passes; the loop narrows as saturation approaches (which
   requires counter-evidence by mechanism — the system will not call an
   argument saturated until it has survived refutation).
7. **Output.** Slice → outline (reordered by hand — it is the PI's) →
   compose → verify → evidence dispositions → export refuses until every
   finding is dispositioned.
8. **Close the circle.** The deliverable is captured back into the catalog
   as a work: its claims join the graph, future gap analyses see the PI's
   own published positions, and the same integrity machinery now applies
   to them — fama-exposure will flag reuse of one's own superseded claim.
   Project N+1's step 2 is richer because of project N's step 8. This is
   "compounds over months and years" as a mechanism, not a slogan.

## The daily rhythm (inside the loop)

- **Morning triage.** Overnight Tier C ran gaps, tensions, digestion, the
  integrity sweep. The plugin badge shows the inbox count; quick items get
  one-click dispositions in the plugin; substantive ones go to the agent
  ("walk me through the inbox") — it shows a contradiction's both claims
  with evidence, the PI decides, it files with `actor=agent`.
- **Thinking.** A claim note is written raw in the editor. On save, the
  Tier-A chain: badge flips unchecked, template validates (broken
  frontmatter is an inline card now, not a discovery three weeks later),
  index updates, a `[[supports::…]]` link becomes an edge candidate. A
  second later: checked. Search and ask already know the note.
- **Situated questioning.** Select a paragraph, ask the agent "what
  contradicts this?" — `context.read` tells it which claim is on screen;
  it queries the graph and answers with grounded items; files nothing
  unless told.
- **A claim falls.** One "decided wrong" disposition → the typed blast
  radius returns ("three notes lost their only grounds; the thesis
  regressed; two warrants now unstated"); downstream badges flip in the
  editor; the agent walks through what to repair first. The central
  operation as a lived experience.

## Roles

| Component | Job | Never does |
|---|---|---|
| **Editor** (Obsidian first, VS Code probable second) | Reading, writing, thinking — notes, drafts, outlines, steering.md | Gating, chatting |
| **Memoria plugin** | Ambient layer: badges, inbox count, question/finding cards, one-click dispositions, context share, editor-event push | Conversation, inference, direct file writes |
| **Agent** (user's choice via MCP + shipped Memoria skill) | Fluent layer: converses from engine-authored payloads, runs operations, triages with the PI | Deciding anything — every disposition is the PI's, journaled with true actor |
| *Daemon (invisible fourth)* | Watches, validates, indexes, checks, re-promotes (Tier A/B/C) | Anything requiring judgment |

## Component-design implications

**Obsidian plugin — project-centric, attention-centric (not
capture-centric):** home surface is a two-panel sidebar (Project health:
argument stage/saturation/under-warranted; Inbox filtered to the inquiry)
with typed cards (gap, discovery, contradiction, evidence finding,
blast-radius) and one-click dispositions; file badges as the ambient
Tier-A layer; two passive duties (publish `context.set`, push
`observe-file-event`). Ruled out by the workflow: chat, capture forms
(capture is pulled from gap output — a capture button would re-encourage
the push habit), dashboard re-creation. Build order: badges + inbox with
item 12; project panel + question cards with Tier 3. All writes via the
existing `/operation/run` path.

**Claude/Codex integration — a skill organized by loop stage:** playbooks
per inquiry-loop stage (open project, triage, discovery review, pulled
capture, interview, argument standup, verify/disposition, close the
circle); a session-opening ritual (`status.read` + `attention.list`);
posture rules as skill law (never dispose without an explicit PI decision,
file with true actor, present contradictions as both claims with quoted
evidence, `context.read` when the PI says "this"); the async
enqueue-then-poll pattern taught once. Same skill content ships to both
agents.

**The handoff bus:** "quick in the plugin, substantive with the agent"
requires escalatable cards — implemented with *no plugin↔agent channel*:
the plugin writes the attention id into shared context (`context.set`),
the agent's next `context.read` picks it up. The engine mediates the
handoff as it mediates everything; either front-end is replaceable without
the other noticing. The context action pair is the integration seam of the
three-component experience.

## Onboarding (the Zotero question, ~1000 papers)

**Admit all to the catalog; admit none to knowledge; let projects pull.**
Bulk-import the full library as bibliographic capture (BibTeX + PDFs as
local full text — mints checked, correctly: the artifact is the evidence;
metadata-only entries stay unchecked pending enrichment, paced overnight).
This makes the first gap run genuinely informed — discovery proposes from
the citation neighborhoods of the whole library. Do **not** bulk-digest:
a thousand digests with zero interview turns is machine reading without
PI reading, exactly what the interview-sealed-digest design prevents;
digestion is pulled per-project, single digits a week, by design.

Sequence: init → write steering.md **before** importing (discovery ranking
reads it) → staged import 10 → 100 → 1000 (the pipeline has never run at
volume; watch enrichment provider load, journal/DB growth, and index
rebuild time — the O(vault) refresh may promote the incremental-indexing
prerequisite) → open project #1 → first gap run against the full library →
pull. Do this after Tier 0 lands (today the catalog is un-enumerable and
failures print `ok` — a bad pairing with a 1000-item import). This
onboarding **is** roadmap item 19: the staged import doubles as the
product's first real acceptance test.

## What's real when

- **Today:** the agent workflow substantially works (MCP + `operation.run`
  + `requests.get`); gap analysis and discovery — the loop's steps 2–3 —
  are among the best-built machinery; the plugin shows counts; statuses
  update on read. Step 8's import-back is ordinary capture (local full
  text) — a workflow, not new machinery.
- **After the reactive substrate (roadmap item 12):** live badges, on-save
  validation, the overnight inbox.
- **After Tier 3 (items 14–15):** engine-authored interview questions,
  the argument-health panel, situated context.

Every element traces to a numbered roadmap item; API gaps between here and
there are listed in roadmap item 12.
