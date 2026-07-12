# Researcher's personal notes (primary source — reasoning/intent layer)

> Pasted by Eran Roseman, 2026-07-04. This is the origin story + round-by-round design
> reasoning in the researcher's own voice — NOT in git/docs. Use as the authoritative
> "why" layer for the design-history document. **The pasted message was TRUNCATED at ~50k
> chars** (cut off mid-sentence in "Entities VS Notes … item-note and paper-note are a
> mixture of a"). The rest still needs to be captured.

## Origin story
Memoria began with a straightforward goal: integrate rigorous research practices into the
**Karpathy Wiki LLM**. Chose **Obsidian** for the wiki (popularity), **Hermes** as the LLM
(built-in learning loop), **Zotero** for academic bibliographies.

Karpathy's three-step model — **ingest, query, lint** — was too limited: needed background
AND user-triggered processes, some deterministic, some LLM-driven. Hermes offered the
infrastructure but was **adopted without evaluating fit**. Unasked questions:
- Is the Hermes **kanban board** suitable? Kanban is good for workflow, but Hermes enforces
  a rigid predefined structure; Memoria needs multiple workflows and actors Hermes doesn't
  natively accommodate.
- Are **Hermes profiles** the right mechanism for the LLM aspects? Enough granular control?
  Should all librarian tasks use the same LLM?

Next major decision: adopt **ZK** as the knowledge-layer foundation. Linking source notes to
Zotero records was insufficient (couldn't manage knowledge-graph sources or creator forms) →
introduced **entity notes** → evolved into the **catalog**. Still kept using existing tools
without assessing suitability. Obsidian is good for markdown note-taking/KM but **not the best
option for a structured knowledge graph**.

Adapting Obsidian as the UI led to warning-sign changes: an **inbox** to mediate Hermes'
background processes ↔ the user; **layers to restrict direct file access** and enforce rules
Obsidian wasn't built for. The **seven-layer architecture** deliberately picked Hermes for the
Co-PI and Obsidian for the vault, but later choices lacked requirements analysis. **Layer 7
(the vault) became a mix of original notes + extra data repositories → lack of clarity.** Never
conceptualized Memoria as an application, never implemented a proper agentic application stack.

6 weeks old, pre-beta, no working installations → the ideal time to **reconsider the application
stack from first principles** and propose a clean-slate design from requirements + best practice,
not the current implementation. Other teams solve similar problems; two notable frameworks not
adopted: **ARD spec** (github.com/ards-project/ard-spec) and **OKF spec**
(github.com/GoogleCloudPlatform/knowledge-catalog okf/SPEC.md).

## Round 1 — what Memoria is
- Opinionated, **personal** tool for thinking and writing — a durable research vault compounding
  across months/years. Personal = thinking is private, separate from communication; notes stay
  unfiltered (raw reasoning before audience-aware editing sanitizes it). One human owns judgment
  (review, synthesis, scope). **Not a team tool.**
- Opinionated = enforces specific workflows, kills setup paralysis. Vault structure, document
  types, review gates are **the design**, not configurable surfaces.
- **Knowledge production, not storage.**
- **Local-first is a current implementation constraint, not a goal.** Single user across several
  computers would be an advantage. The storage-local + exportable-ownership requirement was
  derived from the local-first assumption rather than first principles/requirements.
- File-based DB + markdown-with-frontmatter makes sense. **SQLite/"DQLite" chosen as default
  without considering alternatives** by requirement.
- ≥2 UI surfaces: markdown+frontmatter, and "the rest." **Obsidian chosen as default without
  alternatives.** The "rest" should integrate into the chosen editor for a unified experience.
- **Safety** = limit blast radius of human/agent/system errors and poisoned input; traceable +
  reversible.
- Not replacing Zotero, but does most of what Zotero does → study Zotero + **JabRef** designs.
- Source-capture is academic-paper-based but should apply to **any digital source**. On capture:
  1. immutable raw copy (PDF, web page, audio, …)
  2. extract content to machine-friendly markdown
  3. extract metadata (rich for academic; APIs; min = ACM bibliographic data)
  4. add source + immediate entities to the **catalog graph** (source, authors, orgs, venue,
     cited-by, references)
  5. create a (candidate?) **source note**
- **Catalog graph = deterministic objective** representation of sources. The **source note**
  connects the catalog graph to the **knowledge/notes subjective graph** (ZK + **Toulmin model**).

## Round 2
- What's the difference between the two project types (system POV)? Does two types outweigh the
  cognitive-model complexity? What if I start a project with no seed bibliography?
- **Gap analysis** should analyze the sources graph, the notes graph, AND the gaps between them.
  Dense knowledge+resources = desired state; thin = new topic; **graph mismatch = the interesting
  case.**
- Should a project be an **independent knowledge bundle** inside the vault?
- Is Razlogova's annotation note a type of permanent note?
- Terminology: adopt ZK terminology? Why is source-note the only "-note"? If we use "-note",
  we can't have "note" as a type. Do we need the ZK index? Should non-source notes link directly
  to a source, or via the source note?
- Notes "in your own words" distinguish source vs permanent/annotation. Adding a source assumes
  the user knows what it's about; LLM writing a source note = delegation. Permanent/annotation
  note = two tasks: decide whether to have a note (needs context; system can suggest via guided
  reading / open-notebook; a project provides context) + writing it.
- **Toulmin model relevant only to a project graph; optional; don't force the overlay on every
  note.**
- SQLite FTS5 + sqlite-vec vs **QMD** — pros/cons?
- On-disk layout: use self-explanatory, industry-standard terminology. Why do projects have a
  **slug and not an ID**? Catalog Concepts have creators[]/venue and links authored_by/published_in.
- What are the plugin's two panels?
- **Separation of duties**: the operation that generates is never the one that checks. (Understood
  as: for each agent/human op, a QA op; repeat until approved; then integrity check on the
  graph/system; repeat until approved; then human approval if needed + log for traceability.)
- **Milestones**: many milestones = false discipline. Current design hit a wall; can't proceed
  without beta.1. Ideal: test everything checkable before implementing → implement the **basic
  knowledge cycle** (Open a project (question/thesis) → seed → gap analysis → source to fill gaps
  → capture any digital source [immutable raw + content + metadata] → extract atomic annotations
  → develop notes/claims toward thesis → re-run gap analysis) **+ plugin** → test → more milestones
  if needed. Any milestone that doesn't enable the basic cycle (which requires the plugin) is
  meaningless. **First milestone is 0.1.0-beta.1.**
- **ADRs should enable retiring as many ADRs as possible.** Prune stale ADRs to the minimum.

## Round 3
- How does each concept type map to **OKF**? How do we use tags? How do Toulmin elements map?
- Terminology: Source vs digest; Note vs idea vs thought vs insight; Hub vs topic vs index;
  Catalog vs library.
- Since two modules are still missing (writing and coding), the version is **alpha.11 not beta.1**.

## Alpha.15 notes
- Is the **journal as forensic truth** the right model? Basic assumption: knowledge integrity is
  NOT asserted by semantic evaluation of a single node/edge, but by the **structural integrity of
  the knowledge graph**. A validity incident arises from: (1) any graph change (human/machine)
  triggers verification → maybe an integrity incident; (2) the user decides there's an error; (3)
  periodic maintenance verification. Once an incident happens, system defines **blast radius** +
  suggests solutions. Question: is forensic evidence required to resolve it? → Can't wait until
  beta.2 for immediate file-change response.
- **QMD** was chosen when the system was markdown/obsidian-based with no DB. Still the right
  search/query infra?
- **Fallacy**: "if a project is a concept, then all its artifacts are concepts too." Go back to
  the **3 criteria (fit, human access, recovery)** and decide per artifact: concept, db, or file.
- The **two types of notes feel like lazy design** for unresolved issues.
- Should **Semantic Scholar** be optional in the pipeline? Great metadata source.
- Need a method for choosing/evaluating the model + prompt for each LLM API call type.
- Terminology: Capture vs import; suggest alternatives to **Co-PI, keep-set, steering, act/ask/drop,
  checked/unchecked/quarantined, standing: current|archived** — based on requirements + best
  practice, not current implementation. Is **lifecycle** used anywhere?

## Memoria concepts and workflows — the information flow
- **Import**: Work imported to catalog from file, URL, ID (DOI/arXiv), or BibTeX. Support any file
  type/origin, but beta.1 focuses on **academic papers + GitHub repos**.
- **Sync** (subtype of import): BibTeX for uni/bi-directional sync with a bib manager. Beta.1 =
  unidirectional sync with **Zotero as source of new work**.
- **Enrich**: APIs add metadata per work (for corpus mapping + gap analysis). Authors, citations,
  cited-by = base for the catalog knowledge graph.
- **Entities**: connect new work to existing/new entities.
- **Digest**: each new work → new interconnected **wiki page** with tags linking to hubs. This is
  the **wiki-LLM phase**. Karpathy suggests LLM-only or interview-style.
- **Annotate**: first gate to new ZK notes = work annotation; guided reading/annotation process.
- **Fleeting**: second source of notes = fleeting thoughts not from a work.
- **Idea note**: one coherent self-contained unit of meaning. Annotations + fleeting may mature
  into idea notes. ZK idea-note types: **Concept, Claim/argument, Question, Hypothesis/speculation,
  Tension/conflict.**
- **Corpus mapping / gap analysis**: an idea may trigger it → triggers more annotations/fleeting/
  idea notes based on the current catalog.
- **Discovery**: gap analysis may indicate need for more resources → system helps discover new
  resources → re-triggers the whole flow.
- **Project**: can evolve from an idea note or start as one; project note has similar subtypes.

## Beta.1 (the review that opened this whole task)
- Are Obsidian Canvas and JSON Canvas being used?
- Isn't the review discipline at odds with the design?
- Linux only, or Windows too?
- Vault layout makes no sense: root has two subfolders (existing notes + memoria); looks like
  memoria IS <vault> and <existing notes> are unrelated vaults/folders.
- works/ mixes db projection (record.md), concept (digest.md), blob (source.pdf), extracted
  content (fulltext.md).
- Review alpha.15 knowledge bundle + pre-alpha.11 vault structure — **real regression.**
- OKF compliant: **every concept needs frontmatter regardless of author. Notes is a concept.**
  Real regression — detailed concepts with frontmatter + body schemas replaced by an incoherent
  mess.
- Stopped reading: lots of architecture thought, but functionality was ruined.

## Alpha.4 — Project Starter / the Project gate
- Add Toulmin model of Argumentation or **Miles' Taxonomy of Research Gaps** to
  intellectual-foundations? Can Toulmin/Miles improve other areas?
- Accept ADR-61? Other ADR updates? Thesis vs project-question template — two artifacts or
  lifecycle stages? Is research-focus.md still needed or does the project question replace it?
- Can an operation run notify the PI to refresh? Thesis supersession mid-project dry run?
- Test environment (WSL2 process-testing env): why exclude the REST path? Why vLLM not
  ollama/llama.cpp/litert-lm? Why hardcode base_url in profiles not config.yml? Why not install
  Zotero+Obsidian on Linux? Use Obsidian CLI to expand testing? Why a filesystem-backed Obsidian
  MCP shim not a real environment? **Test env too minimalistic — should be a full install
  (Obsidian+Hermes+Zotero), most/all functionality, Obsidian CLI to trigger all command-palette
  commands, emulate real-life + edge cases. Should include L0-L4, cross-cutting, ≥partial L5.**

## Alpha.3 — the UI build (issues found in alpha.2 to fix before project functionality → alpha.4)
- Ribbon pinning of memoria commands; cmdr/leader-hotkeys/shell-commands/slash-commander/
  better-command-palette/apex-dashboard plugins.
- Fleeting note capture should use a **form** (modalforms); update-time-on-edit; propsec to
  enforce frontmatter; conditional-properties; base-board for lifecycle status/state.
- system/ folder is for files that can't be in .memoria; if the user needs a file it can't be
  there. Created fleeting note didn't appear in the fleeting base. Navigating folders to find
  dashboards is bad.
- Library workspace: icons on left pane; one-dataview-per-pane wastes space; pane is for
  information not explanation (help link instead); frequently-used/navigation info in left pane,
  deeper info in pages; embed bases in pages.
- Tutorial 03: no Inbox tab / Needs-me view; user shouldn't access .memoria/data/extracts/
  <citekey>.md; does the librarian create the proposed source note?
- Tutorial 04: asking co-PI is never the ONLY way — every task doable by co-PI on top of the
  standard process; only co-PI-exclusive things require LLM-human two-way conversation. Zotero
  capture broken.
- Tutorial 05: source note should have a button to create a linked claim note.
- home.md: homepage plugin not working; buttons in a line; make status a link (status-link pairs);
  Resolve-card button broken; Delegate-a-task great (task list needs a phrase; drop "memoria-"
  prefix); review all homepage plugin settings.
- reference/system-actions: each action needs how-to-invoke.
- explanation/engines: "Engines are Memoria's deterministic app" — naming issue (apps vs engines);
  what is CI invocation (never explained); ingest is complex (own page); file naming too generic;
  consistent naming form (ingest/search/cluster/verify/lint); processing/maintenance vs
  bookkeeping/housekeeping naming.
- Site-wide: (D41)-style refs to purged docs; broken links + inconsistent format; how to refer to
  a system file; ADR links — useful or distraction?; broken links everywhere.
- General: cli-rest-mcp plugin?; eval folder files?; system/vocabulary.md?; catalog bases location;
  "no Python installed" error; show all properties in all note types?; co-PI capitalization; two
  navigation ways (bases vs dashboards/reports) — don't navigate via file view; cluster navigation
  by job-to-be-done; which views per base; which dashboard per base; base-board kanban views;
  quick-nav left pane vs task dashboards vs deep-work dashboards; frictionless next action.
- Client Agent: export to dedicated system folder; auto-export on; open-after-export off; display
  name = "Memoria Co-PI".
- Workspaces: don't use plugin capabilities; both use home.md as only tab (pointless); don't open
  co-PI in right pane. home/library workspaces critiqued in detail; all 3 workspaces should share
  layout; relevant info + drill-down; easy access to actions; home.md = always-needed common cards
  or discard; left pane = navigation; co-PI in right pane; **workspaces as gates**: (1)
  system/maintenance/housekeeping gate, (2) sources/library gate (navigate catalog + notes +
  reports; catalog health; find new sources via gap analysis), (3) knowledge base/ZK gate (resolve
  link-network issues incl hubs/indexes; maybe a separate bookkeeping gate for entity+note network
  health). Project (out of scope) artifacts: research question, knowledge map, knowledge gap,
  sources gap, outline — iterative; project gate drives catalog/library/source work + basis for
  writing/coding.

## Mapping to the cognitive model
- Single model as both architecture + cognitive model? They're close; a single shared model may
  be a better cognitive model than a perfect separate one.
- 3.4 taxonomy: how are inbox gap/candidate different from project's gap-report/corpus-map?
- 4.1 two activities, six delegable tasks: still uses read/write instead of library/projects;
  drop the # column; merge human verb + delegated task into one name; align with skill names.
- 4.2 agents: same agents for all — best practice? Maybe shared content but unique context per
  agent; do agents besides co-PI need /personality?
- 4.3 engines: ingest/cataloging engine — pick a name (ingest follows wiki-llm; cataloging is
  thematic); clustering engine?; merge linter in, section 5 redundant.
- 6 working surface: adopt Obsidian terminology; explain Diversity reserve.
- Appendix C: consistent skill naming convention.
- **Installation**: drop the repo vault/ folder (error-prone); use src/ with all files; install
  script creates folder structure with .gitkeep then populates from repo; OR copy all to .memoria/
  and populate from there (linter can restore). Script: create folder → download → populate →
  install Hermes → install profiles → install Obsidian? → explain finishing setup. Remove Zotero
  (covered in tutorial).

## System Architecture — the seven layers
Guiding principle: **decisions flow top-down, information flows bottom-up.**
- **L1 The human** (call it PI? PI more descriptive; human aligns with human-centered design).
- **L2 The workspace**: all Obsidian UI (homepage, dashboards, inbox, workspace, command palette).
- **L3 The co-PI**: permanent AI agent in the ACP pane. Inherits Socratic agent + full system
  knowledge (can explain how to do things — a memoria skill). No write privilege but can use the
  same tasks the human can; maybe all read-only skills too. Most like a standard chatbot/agent.
  Uses full Hermes capabilities — the built-in self-improving learning loop: memory, /goals, skills.
- **L4 The tasks layer**: ephemeral profiles, kanban board, task cards. Given tasks by co-PI +
  human; execute under a structured process.
- **L5 The MCP server(s)**: agents fully sandboxed; MCP = lightweight app fetching data/executing
  tools (vault + enrichment APIs). (Should we use MCP apps?)
- **L6 The engines layer**: all engines (better name? applications/apps). Invoked by human/agents/
  cron for bookkeeping + maintenance.
- **L7 The vault/data/knowledge/library layer**: all files + folders.
- **Guardrails** ("Honesty is the best policy"): biggest pitfall = synthetic index with a
  threshold. Every recommendation (all inbox items) should include: impact level (high/med/low —
  fear >3 levels collapses), certainty level, the impact (accept), what happens if rejected,
  reasoning behind impact level, reasons to accept, reason to reject, verdict justification.
  Formulate each part + order; research best practice.
- **Analyst+librarian merger**: review the project phase first. Human needs before writing/coding:
  formulate research question (co-PI or writer); check catalog for relevant items (scan, categorize,
  rationale, adopt/borrow/reject); literature search for new resources; reports are inbox-like
  project-specific items (merge or per-workspace inbox?); build canvas/mind-map/sketch (ZK phase);
  outline derived from canvas (one-time export or synced?); writing/coding/verification. Deep vs
  task-oriented work must be separated (distinct mindsets).

## doer-tiers / four-layer cognitive model / states
- "doer-tiers" — find a common term (Actors?).
- Vault: also .obsidian/. Activity vs workspace same? Are those really phases from the human POV?
  Two workspaces: read/write. Six delegable tasks: **catalog, extract, link, map, draft, verify.**
  Should workspace limit which are delegable? Tasks delegated via command palette or slash command
  in the client-agent pane. Pros/cons of catalog+extract+link+map+verify under one profile.
- Six agents; agents.md + /personality? Pane provides 4 agents — needed, or does task delegation
  make it redundant? Humans always talk to the same agent, delegate to others → fixes current
  implementation → the pane native agent fully uses Hermes' self-improving loop → evolve into a
  true co-PI.
- Engines vs housekeeping (linter) confusing (linter belongs to both) → drop housekeeping, just
  engines. Read vs write workspace difference; pros/cons of two vs one.
- Naming: read:/write: prefix redundant; add task/card prefix? (search: find-source / verify:
  cite-check). obsidian-biblib (220) — add to redesign?

## Graph / four-layer (cognitive model) / states (later round)
- Split fact-checker between bookkeeping skills (→ analyst) and housekeeping skills?
- **Two names/parentheses = naming issue.** Desk → workspace(s). Store → files/folders/filesystem/
  Obsidian vault. catalog/ → library/librarian. Board states = Hermes native; a card gets
  review_status once its native state is done; should inbox/review_status share states with other
  categories? **Universal state**: `Review_status: proposed → provisional → current / archived`
  (instead of unreviewed → requested → approved / rejected). Review-request: aren't all inbox items
  done cards awaiting human approval? → keep card name + give lifecycle state. maturity +
  agent_recommendation parallels: `inconclusive → issues-found → clean` vs `seedling → budding →
  evergreen` (both judgment calls, not objective).
- 4.1 read/write or compile/compose (not both). Human verb + agent activity + agent name + inbox
  item should share a name. Librarian carries whole reading process — split into 3 profiles? Do
  lanes share skills? Assign skills per lane so librarian has 3 modes. "colleagues" → "team". Is
  the linter zero-LLM?
- 6.1 three workspaces: drop "mode" (double-naming); read/write workspace good. Which agent gives
  each active-assistance type. Rethink profile division: profile = skills (per-lane assignable) +
  posture (constant); per agent, which skills + which posture + is the combo optimal.
- 7 pattern library: does a pattern require a skill? same skill for all? which agent per pattern?
  which pattern per action type? read vs write patterns? how does the user find the right pattern?
- 8 guardrails: **a fully automated process is better than one requiring a human to click OK
  without reading.** Are score-emitting skills deterministic? Propose-not-dispose + anti-anchoring:
  assume the system approved everything promoted for human approval → the best guardrail is giving
  the human the reasoning (pros, cons, verdict) so they judge the process, not just the result.

## Memoria — New Components / knowledge cycle / What Memoria is (later round)
- Drop history, leave design details. graded warning loudness — each level needs a defined outcome.
- Homepage: good intuitive name; integrate all dashboards into homepage? "what's needed" above the
  fold, click/collapse for detail — compare options.
- Workspaces: defined in docs but never implemented; redesign for new structure; think-and-write /
  compile-compose distinction keeps recurring → apply the "phone call test", define conceptually,
  name properly, apply consistently.
- Active assistance per workspace: design solid, naming not — need a consistent self-explanatory
  scheme so complexity hides behind a simple cognitive model.
- In-vault pattern library: system/ or .memoria/? Is system/ the right name?
- **Three layers** — "we got something very basic very wrong": this isn't the research/production
  layer, it's the **bookkeeping layer** (autonomous agent actions between human actions): human
  acts in the workspace → agent handles all bookkeeping → resurfaces results in the workspace
  (dashboards). The **upkeep layer** is a different bookkeeping type, triggered by human/agent/cron
  → its own layer (names: integrity/linter/upkeep/housekeeping). Third layer = where the human
  works (workspaces/work layer).
- **Folders** (currently "vault layer" — not self-explanatory): keep numbers? (numbers denote a
  direction — is there a direction or a network?). notes/ works (basic concept). Adopt ZK note
  names? entities/ is technical/uninspiring (library/index/catalog); artifacts/ technical. projects/
  good (first subdivided by project, then artifacts). Project artifacts: corpus-map, gap-report,
  framing, outline, canvas, draft, verification-report, code-note, deliverable(🔒); project-scoped:
  candidate-card, gap-card. Reports: gap-report, verification-report, candidates-report. Is
  gap-report = gap-card? candidate-card vs gap-card difference?
- **State framework**: universal scheme `proposed → provisional → current → retracted → archived`.
  Only one state; `seedling → budding → evergreen` = a property of a claim-note. Do other notes
  have properties? artifacts?
- 5.3 gate triad: rethink → sequence is human action/trigger → agents' lanes → notification/signal.
- Upkeep layer (no gate): follow same sequence. **Entity storage options**: SQLite, Obsidian bases,
  JSON/XML schemas in files, NoSQL — pros/cons of each.
- "Almost there": most open issues = naming, refinement, missing details; none change what's agreed.

## What Memoria is (final round) / knowledge cycle
- Memoria = opinionated, **phase-gated, bounded, personal** tool for thinking and writing — durable
  research vault compounding over months/years. Personal = private thinking separate from
  communication; unfiltered notes preserve raw reasoning before audience-aware editing distorts.
- Phases ①–⑤ pipeline-driven — each fires on the single output of the previous. Does phase 1 fire
  on the single output of 6? Make explicit.
- **Why CURATE is last, not first** → maybe it should be FIRST (logically consistent; CURATE as
  phase 1 doesn't fire on a single output — triggered by any other phase or by the human).
- 4.2 gate triad: agent sets → human judge → agent carries. Terminology: human doesn't only judge
  → maybe "human thinks and writes". Conceptual: each phase ends with agent-carries → triggers next
  agent-sets; is there a clear structural divide or one process arbitrarily split?
- 4 knowledge cycle (production layer): dual name = carryover; use new-new (previously: old) →
  "knowledge production layer"?
- 4.4 maintenance band — under all phases, no gate: same layer or separate?
- Workspaces: change to align with new phases? Workspace per space, home cueing which phase needs
  attention. Active assistance per phase — see Open Notebook (chat assistant, AI notes,
  transformations, search) + Fabric (patterns) + learnprompting thought-generation + arxiv
  2502.18600. Both have APIs.
- **Entities VS Notes** (full text — resolves the earlier truncation): implicit distinction —
  making it explicit may simplify the design. Entities have properties, currently in `20-sources/`.
  Notes = units of data inherited from ZK. **The item-note and paper-note are a mixture of a note
  and an entity — a source of tension in the design.** Implications:
  - Cataloging a source triggers **two action types**, outputs stored separately: (1) *mechanical* —
    create entities (paper/people/orgs), gather metadata, extract content, link to existing
    entities; (2) *create a source note + link to other notes* (agent-doable, human-gated if needed).
  - Clear distinction between the entity's **objective** properties and the source note's
    **vault-specific** properties (topic, project).
  - Clear distinction between entity links and note links.
  - **A single source-note type** — item-note vs paper-note differ only in metadata/connections, not
    essence or usage.
  - Enables more granular **source types** (book chapter, journal article, preprint, repository,
    dataset) as a single property, without convoluting the vault/source-note.
  - Re-examine whether other note types are entities forced to be notes.
  - Re-examine whether an Obsidian note is the best store for entities (source notes mix structured +
    unstructured; entities have only structured data).
  - Clear distinction between a **candidate-note** and a **source-note** (distinct at different
    lifecycle phases).
- **Note types** (gap analysis): `fleeting-note`, `reference-note`, `project-note`, `code-note`
  don't appear in the design; `framing`, `corpus-map`, `gap-card`, `gap-report`, `outlines`,
  `report` are not currently defined. **ZK core**: Fleeting (temporary capture), Literature/Source
  (own-words summary + reference), Permanent/Evergreen (atomic, context-free, linked). **ZK
  supporting**: Structure/Hubs (TOC / narrative threads), Project (task-scoped, archived on
  completion), Index (high-level navigation pointer).
- **State model & non-monotonic knowledge**: Do new states apply to all note types? How differ from
  current lifecycle — replacing or adding? How per type? Are fleeting/answer/claim different *types*
  or one type in different *states*?
- **Beyond this point** (scoping rule): everything up to here *changes the current design*;
  everything from "Validation status" onward *introduces NEW components with no parallel*. Finalize
  the first part first (ripple effects); mark new components explicitly with a clear goal. First half
  implicitly adopts the approved design goal → only *implementation* needs agreement; for a new
  component, first clarify the problem + whether this solves it, then implementation.
