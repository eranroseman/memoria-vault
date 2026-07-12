# Owner design notes — Pillar 3 (intent layer)

> **North star:** Memoria is an opinionated, single-person
> knowledge-production tool. It is an AI-enhanced Zettelkasten utilizing the
> LLM-wiki framework.

**Canonical source: [`design-history/sources/researcher-notes.md`](../../../../design-history/sources/researcher-notes.md)** —
the owner's round-by-round notes, already in `sources/` and cited by the
history report. **This material was available to the beta.1 agents and
dismissed as a historical artifact — it was not missing.** This file is a
2026-07-05 re-emphasis the owner pasted (a selection, plus the north-star
sentence above); the canonical file governs where they differ.

*Owner's framing: "This is my personal notes. They may not be the absolute
truth but they include the design philosophy and a lot of questions worth
asking." Epistemic status: the authoritative record of design INTENT and the
DECISION AGENDA — not settled fact. Where it states philosophy, it governs
direction; where it asks a question, the redesign must answer or explicitly
defer it.*

> **⚠ TRUNCATED:** the owner's paste exceeded the 50,000-character message
> limit and was cut off inside the **Alpha.15** section (at "A validity
> incident can occur in response to 3 types of events…"). The remainder of
> alpha.15 and anything after it is NOT yet captured. Owner to re-paste the
> rest.

---

## Alpha.4 — Project Starter / the Project gate design

- Should we add the **Toulmin model of Argumentation** or **Miles' Taxonomy of Research Gaps** to explanation/overview/intellectual-foundations?
- Can the Toulmin and Miles models be used to improve other areas of the system?
- Should ADR-61 be accepted? Any other updates to ADRs?
- What should the template for the thesis and the project question be? Are these two distinct artifacts or different lifecycle stages?
- Create a list of pages that need to be added to the docs as part of implementation.
- Is `research-focus.md` still needed or does the project question replace it?
- Can the operation run notify the PI they need to refresh?
- Can we do Thesis supersession mid-project dry run?
- Appendix — external methodological grounding should be turned into at least one explanation file.

### Test environment design — WSL2 process-testing env
- Why does WSL2 run exclude the REST path?
- Why vLLM and not another framework (ollama / llama.cpp / litert-lm)?
- Why do profiles today hardcode the same literal base_url? Shouldn't it be in the config.yml?
- Why not install Zotero and Obsidian on a Linux system?
- Can we use Obsidian CLI to expand testing?
- Why use a filesystem-backed Obsidian MCP shim and not a real Obsidian environment?
- **The testing environment should be as real and extensive as possible.** It should include a complete installation of memoria with Obsidian, Hermes, and Zotero. It should include most or all functionality. The Obsidian CLI should be used to trigger all the Memoria command palette commands and analyze the product. It should try to emulate as many real-life and edge cases as possible. The current design is too minimalistic.
- Is there a reason that the test environment won't include L0–L4, Cross-cutting, and at least partial L5?

## Alpha.3 — the UI build (issues to resolve)

*After reviewing alpha.2 it became apparent there are many UI issues to resolve before adding project functionality (alpha.4). For each issue, research best practices, suggest alternatives with pros/cons, group into categories.*

### Ribbon / command palette
- Can we pin memoria commands in the ribbon?
- Community plugins to evaluate for putting the right command in the right place: cmdr, leader-hotkeys-obsidian, obsidian-shellcommands, slash-commander, obsidian-better-command-palette, apex-dashboard.

### Capture a fleeting note
- **Creating a new note should be done with a form.** A form gives structure, creates a clear divide between the note structure and the new text, and enables instructions that are not part of the final note. (modalforms)
- update-time-on-edit — for updated frontmatter?
- propsec — to enforce frontmatter use?
- conditional-properties?
- base-board — great option for anything with a lifecycle status/state.

### Where fleeting notes surface
- The `system` folder is for system files that can't be in `.memoria`. If the user needs to access a file, it can't be there.
- I created a fleeting note and it is not in the fleeting base.
- Having to navigate folders to find dashboards is not the best solution.

### Library workspace
- Can we use icons for the options on the left pane?
- One dataview per pane seems a waste of real estate. They can all be together.
- The pane is not a place for explanation. It should have information. It can have a help link that opens a relevant help page.
- The workspace can open with multiple pages. Frequently-used / navigation info in the left pane; details / deep dives / less frequent updates on pages. Both can have buttons for frequent actions. Bases can be embedded in pages.

### Tutorials
- T03 Step 3 (Judge the candidate card): No Inbox tab or "Needs me" view in Desk, nor a card in the inbox for the added URL.
- T03 Step 4 (Read the paper): Expecting the user to find `.memoria/data/extracts/<citekey>.md` is unreasonable; the user should never access `.memoria`. It is not even in the folder view.
- T03 Step 5 (Write the source note): Does the librarian create the proposed source note?
- T04 Step 1 (Ask the co-PI for a batch): **Asking the co-PI to perform a task is never the ONLY way to do it. Every task should be able to be performed by the co-PI, but it is always on top of the standard process. Things that go only through the co-PI are only things that require LLM–human two-way conversation.** The capture from Zotero doesn't work.
- T05 (Synthesize toward a writing project): The source note should have a button to create a claim note linked to it.

### home.md
- Homepage plugin isn't working.
- Buttons can be in a line to take up less space.
- The Status glance is a good idea. Can we make the status the link? If not, then status-link pairs. Are there additional important statuses?
- The Resolve card button seems broken.
- The Delegate a task button is great. The task list should include a phrase, not just a verb. No need to write `memoria-` in front of the agent's name.
- The dashboard callout opens, but there is just a list of links.
- Review all the homepage plugin's settings and ensure full use.

### reference/system-actions
- Each action should include how it can be invoked.

### explanation/engines/
- Engines are Memoria's deterministic app. **Rule of thumb: anywhere there are two names or parentheses, there is probably a naming issue.** If there are apps, then why do we call them engines?
- What is CI invocation? Never explained; not obvious for a non-developer.
- Ingest is a complex process with its own page → `reference/ingest`. Why is it a standalone page? Which category?
- `engines/ingest/pipeline.py` is too generic. The name should have the same form: ingest, search, cluster, verify, lint…
- Processing/maintenance engines vs bookkeeping/housekeeping apps?
- `/reference/ingest` includes info about other engines too. There should be an engine reference page (procedural) and an explanation page (rationale).

### Site-wide
- References like (D41) likely refer to annotations in purged work documents.
- Links in engine/ingest are broken and use a different format — probably site-wide. We need to decide how to refer to a system file. Does `engines/ingest/pipeline.py` need to be a link at all? How formatted?
- Why are all the links broken?
- Do the ADR links add useful information or a distraction? Some subheadings include the ADR in parentheses followed by the link.

### General
- Do we need cli-rest-mcp?
- What are the files in the eval folder?
- What is `system/vocabulary.md`?
- Where are the catalog bases?
- Error: no Python installed.
- Do we need to show all properties in all note types?
- co-PI should be **Co-PI**.
- **Two ways to navigate: bases and dashboards/reports.** No reason for the user to navigate via the files view. Think about how to provide navigation and cluster it sensibly.
- Which views are needed for each base? Which dashboard pairs with each base? Which kanban view (base-board) presents that info? Cluster by job-to-be-done. Divide between quick nav (left pane), task-oriented dashboards, and deep-work dashboards. Make the next action frictionless. Frequently-used dashboards: highly functional + help link. Infrequent diagnostic dashboards: step-by-step guidance.

### Client Agent
- Export → dedicated folder in the system folder. Auto-export on. Open note after export off. Display name: **Memoria Co-PI**.

### Workspaces (alpha.3)
- Workspace design is lacking; doesn't take advantage of the plugin (obsidian workspaces). Both use home.md as the only open tab (pointless — always open). They don't open the co-PI in the right pane (should be relevant at least for the library).
- **home workspace:** name isn't self-describing/thematic. Enigmatic description, unhelpful link.
- **library:** reading pipeline looks the same as board state, same design failures. Why is each on a different side? Right pane empty (no data), enigmatic.
- **home.md** is the system's starting point / control panel — always on the page the PI uses for the most frequent action + most-needed info. Discard and redesign from scratch.
- Guidelines: all 3 workspaces share the same layout; present only relevant info + drill-down; easy access to all relevant actions; home.md provides what's always needed (else discard the common card). Consider buttons-panel / synaptic-view / buttons. **Left pane = navigation. Co-PI = right pane.**
- **Workspaces are gates to the system.**
  - **Gate 1 — system/maintenance/housekeeping:** where the user goes when a system issue needs attention. Status bar indicates it.
  - **Gate 2 — sources/library gate:** navigate the catalog + related notes/reports (source notes, gap reports, candidate cards) using bases and network views. See catalog/source-note health issues needing attention. Find new sources via gap analysis (cards, reports).
  - **Gate 3 — knowledge base/ZK gate:** resolve issues with the links network incl. hubs and indexes. (Maybe a separate bookkeeping gate for network health of entities+notes, and a separate knowledge gate that manages notes.)
- **Project artifacts (out of scope for the build, but must be understood):**
  - **Research question** — informs the next stages.
  - **Knowledge map** — the system scans notes+entities and presents the part of the knowledge network relevant to the project + open network issues.
  - **Knowledge gap** — gaps in the notes that can be closed using existing entities (new hubs, indexes, claim-notes from the existing catalog). Informs the next artifact.
  - **Sources gap** — new relevant items to add to the catalog.
  - **Outline** — derived from the knowledge map.
  - Iterative: closing a gap changes the knowledge map; gaps and map may inform changes in the research question. **This gate is the driver for all catalog/library/source work, and the basis for writing and coding.**

## doer-tiers / cognitive model

- "doer-tiers" — find a more common term. Actors?
- The Vault: there is also `.obsidian/`.
- **4.1 Two activities, six phases:** Is activity and workspace the same thing? Are those really phases from the human POV? Two workspaces: read and write. Six tasks a human can delegate: **catalog, extract, link, map, draft, verify.** Should the human delegate all six from both workspaces, or should the workspace limit them? Tasks delegated via command palette or slash command in the client-agent pane? Pros/cons of catalog+extract+link+map+verify under a single profile.
- **4.2 The six agents:** agents.md and /personality? The pane provides access to 4 agents — needed, or does task delegation make it redundant? Humans always talk to the same agent and delegate tasks to others. This way the pane's native agent fully uses Hermes' self-improving learning loop (memory, /goals, skills) and evolves into a true Co-PI.
- **4.3 engines + 5 Housekeeping (linter):** linter belongs to both — confusing. Maybe drop housekeeping and just have engines.
- **6 Workspaces:** difference between read and write? Pros/cons of two vs one?
- **Should we have a single model that works as an architecture AND a cognitive model?** They are very close; a single model may be a better cognitive model than a perfect separate one.
- I am still not sure how the **inbox gap and candidate** are different from the project's **gap-report and corpus-map**.
- Merge linter into engines; Section 5 is redundant.
- Adopt Obsidian terminology for the UI.
- Explain Diversity reserve.
- All skills should use the same naming convention.

### Installation (doer-tiers)
- Replace the in-repo vault folder (unnecessary, error-prone) with a `src/` folder containing all necessary files; the install script creates the folder structure with `.gitkeep` and populates from the repo. Alternatively copy all to `.memoria/` and populate from there, so the linter has a copy of every system file to restore. Script: create folders → download files → populate → install Hermes → install profiles → install Obsidian? → explain how to finish setup. Remove Zotero (covered in tutorial).

## System Architecture (7 layers)

**Guiding principle: Decisions flow top-down, while information flows bottom-up.**
- L1 — The human (maybe call it the PI? more descriptive; "human" aligns with human-centered design — research needed).
- L2 — The workspace: all Obsidian UI (homepage, dashboards, inbox, workspace, command palette).
- L3 — The Co-PI: permanent AI agent in the ACP pane. Inherits the Socratic agent + complete system knowledge (can explain how to do things — a memoria skill). No write privilege, but can use the same tasks the human can; maybe give it all read-only skills. Most similar to a standard AI chatbot. Uses full Hermes capabilities: built-in self-improving learning loop, memory, /goals, skills.
- L4 — The tasks layer: ephemeral profiles, kanban board, task cards. Given tasks from Co-PI and human, performed under a structured process.
- L5 — The MCP server(s): agents fully sandboxed. MCP server is lightweight, fetches data / executes tools. (Are we / should we use MCP apps?)
- L6 — The engines layer: all engines. Better name — applications/apps? Invoked by human, agents, or cron for bookkeeping and maintenance.
- L7 — The vault/data/knowledge/library layer: all files and folders.

### Guardrails
- **"Honesty is the best policy." The biggest pitfall is creating a synthetic index with a threshold.** Every recommendation (all inbox items) should include: **Impact level** (high/med/low — any scale with >3 levels collapses to 2–3; research best practice); **Certainty level** (same); the impact (what happens if accepted); what happens if rejected; the reasoning behind the impact level; reasons for accepting; reasons for rejecting; the verdict justification. Consider how to formulate each part and their order. Is anything missing?

### The analyst/librarian merger
- Review the project phase and its requirements to ensure nothing is missed. (Maybe call the two workspaces the **library** and the **project** workspaces.) Before writing/coding (which have their own agents), the human needs:
  - Help formulating the **research question** — a note/document guiding later stages; getting it wrong affects everything. Includes scope, problem. Done with Co-PI or writer.
  - **Checking the catalog for relevant items** — the agent scans all sources, decides relevance, groups into categories, presents a report by category with rationale, and for each item: what it is about, why relevant, adopt/borrow/reject with rationale. (Related sources can be grouped: paper+repo, review+source, paper+counter-paper.)
  - Once sources are linked, the system runs a **literature search** and recommends new resources to add + link. Similar report structure.
  - Sidenote: reports are inbox-like, project-specific items. Merge, or per-workspace inbox? Research best practice.
  - Next: the **canvas/mind-map/project sketch** — connecting notes into a thread (a ZK-like phase).
  - The **outline** — derived from the canvas. One-time export or stay synced (one/two-way)?
  - Writing and coding; Verification.
- Iterative, not linear, but a natural progression. Decide which agent suits each task by posture; then assess whether analyst and librarian can merge. Writing/coding/verification not fully developed — can be v0.3.
- **Deep vs task-oriented work:** the workspaces should clearly separate deep work (e.g., the project document) from task-oriented work (e.g., reviewing links). Distinct mindsets; don't mix.

## Design refinements (naming, states, structure)

- **Rule of thumb: two names or parentheses = a naming issue.** Desk → workspace(s). Store → files/folders/file-system/Obsidian vault. catalog/ → library/librarian. 
- Board states are Hermes' native board state. A card gets a `review_status` once its native state is done. Should inbox/review_status use the same states as other categories?
  - `Review_status: proposed → provisional → current / archived` (instead of unreviewed → requested → approved / rejected).
  - Aren't all inbox items done cards waiting for human approval? If so, keep the card name and give it a lifecycle state like any other item.
  - Maturity `agent_recommendation`: `inconclusive → issues-found → clean` vs `seedling → budding → evergreen`. Both are judgment calls, not objective states.
- Bases as the Store's view layer: the housekeeping/integrity explanation is too general, lacks detail.
- **Either read/write or compile/compose — no two terminologies for the same thing.** read/write is easy to grasp. Ideally the **human verb, agent activity, agent name, and inbox item share the same name.**
- Does the librarian carry the whole reading process alone? Split into 3 profiles? Do the lanes share skills? Skills can be assigned per lane, so the librarian might have 3 modes.
- "colleagues" → "team".
- Is the linter zero-LLM?
- **6.1 Three workspaces:** No "mode" (double-naming). Read workspace / write workspace work great.
- Now that we have the structure, rethink the profile division. A profile = **skills + posture.** Skills can be per-lane. Every time there's an agent, consider: which skills (can differ across agents), what posture (constant per profile), and whether this skills+posture combo is optimal.
- Where/how does the user ask for active assistance? Undefined.
- **Pattern library:** Does using a pattern require a skill? Same skill for all? Which agent uses each? Which pattern per action type? Read vs write patterns? How does the user find the right pattern at the right time?
- **Design guardrails:** **A fully automated process is better than one requiring a human to click OK without reading.** Are the score-emitting skills deterministic? **Propose, not dispose + anti-anchoring: assume the system approved everything promoted for human approval. The best guardrail is giving the human the reasoning — pros, cons, verdict — so the human judges the process, not just the result.**
- Appendix A topic ontology: study design and methodology sound the same.
- Skill naming scheme: `agent-lane/workspace-action-result`? Don't write just "book" or "house" (confusing).
- Some parts are hard to follow — write clearly, organize logically.
- Graded warning loudness: each level should have a defined outcome.
- **Homepage** is a good intuitive name; functionality makes sense. Should all dashboards integrate into the homepage? "What's needed" on top above the fold; click/scroll or collapsing view for details. Compare options.
- Workspace names keep returning to think/write, compile/compose. Apply the **phone-call test**: define conceptually, name properly, apply consistently for a simple mental model.
- Active assistance per workspace: design solid, naming not. Need a consistent, self-explanatory naming scheme across the whole system so complexity hides behind a simple cognitive model.
- Do patterns belong in `system/` or `.memoria/`? Is `system/` the right name?
- **Merge the two parts into a single comprehensive design doc** including existing skills, kanban cards, etc.

## Three layers (bookkeeping / upkeep / work)

- **We got something basic wrong.** This isn't the research/production layer — **it's the bookkeeping layer**: the autonomous agent actions BETWEEN human actions. A human acts in the workspace (out of scope); the agent handles all bookkeeping (this layer) and resurfaces results in the workspace (dashboards).
- **The upkeep layer** is also bookkeeping but a different type, triggered by human actions, agent actions, and cron. It's its own layer. Names: integrity layer, linter, upkeep, housekeeping.
- **The third layer** is where the human does their work: workspaces/work layer.
- **Folders** are another layer (currently "vault layer" — not self-explanatory).
  - Keep numbers in folder names? Numbers denote direction — does a direction exist or is it a network?
  - Names: `notes/` works (basic concept the user must know). Adopt ZK note names? May offer an easier path in + honor ZK tradition. Rethink each note type from its description; compare new vs current vs ZK.
  - `entities/` is technical, uninspiring — library/index/catalog. `artifacts/` also technical. Which bases are needed?
  - `projects/` was good and self-explanatory. Unlike notes, it's first divided into projects, then artifacts. First subdivision = projects.
  - Project/control artifacts not fully defined. Is an artifact a type (like a note, an entity)? Are they all the same type? corpus-map, gap-report, framing, outline, canvas, draft, verification-report, code-note, deliverable(🔒); project-scoped candidate-card, gap-card. One type is **reports**: gap-report, verification-report, candidates-report. Is gap-report = gap-card? candidate-card vs gap-card?
- **State framework:** universal state scheme for a simpler mental model: `proposed → provisional → current → retracted → archived`. Only ONE state. `seedling → budding → evergreen` can be a **property** of a claim-note. Do other notes have properties? Artifacts?
- **5.1 user's view:** should feel like someone I trust working in the background to help me achieve my goals. If this is the housekeeping layer, each phase describes what the agent is doing — maybe defined by the card type on the kanban board (e.g., cataloging phase: librarian assigned a cataloging card).
- **5.3 gate triad** — rethink. Sequence: human action/trigger → agents' lanes → notification/signal.
- **7 Upkeep layer (no gate):** same sequence.
- **Entity storage decision:** options — SQLite, Obsidian bases, JSON/XML schemas in files, NoSQL. Pros/cons of each.

## What Memoria is

**Memoria is an opinionated, phase-gated, bounded, personal tool for thinking and writing — a durable research vault that compounds across months and years of work.**
- **personal** — thinking is private and separate from communication; notes stay private so thoughts remain unfiltered, preserving raw reasoning before audience-aware editing distorts/sanitizes them.
- **Phases ①–⑤ are pipeline-driven** — each fires on the single output of the one before it. Does phase 1 fire on the single output of 6? If so, make it explicit.
- **Why CURATE is last, not first:** Maybe it should be first. CURATE as phase 1 doesn't fire on a single output; it may be triggered by any other phase and by the human.
- **4.2 gate triad:** current structure: agent sets → human judges → agent carries. Terminology: the human doesn't only judge — maybe "human thinks and writes." Conceptual: each phase ends with agent-carries triggering the next agent-sets. Is there a clear structural divide, or one process arbitrarily split in two?
- **4. knowledge cycle (production layer):** dual name is carryover. Use `new-new (previously: old-name)`. → "knowledge production layer"?
- **4.4 Maintenance band — under all phases, no gate:** same layer or separate?
- **Workspaces:** align design to the new phases? Maybe a workspace per space, with home giving cues which phase/workspace needs attention. What active assistance per phase/workspace? (See Open Notebook chat-assistant / ai-notes / transformations / search; Fabric + patterns; learnprompting thought-generation; arxiv 2502.18600. Both have REST APIs.)

### Entities vs Notes (flagged as a source of tension)
- There is an **implicit distinction between entities and notes**; making it explicit may simplify the design.
- **Entities have properties**, currently in `20-sources/`. **Notes are units of data inherited from ZK.**
- The **item-note and paper-note are a mixture of a note and an entity** — a source of tension.
- Implications:
  - Cataloging a source triggers TWO types of action, stored separately: (1) **mechanical** — creating entities (paper, people, orgs), gathering metadata, extracting content, linking to existing entities; (2) **creating a source note** and linking it to other notes (agent-doable, human-gated if needed).
  - Clear distinction between an entity's objective properties and the source note's vault-specific properties (topic, project).
  - Clear distinction between entity links and note links.
  - **We can have a single type of source-note.** item-note vs paper-note differ in metadata and connections, not essence/usage.
  - Enables granular source types (book chapter, journal article, preprint, repository, dataset) each with relevant properties, **without convoluting the vault** — source type becomes a single property of the source-note.
  - Re-examine whether other note types are entities forced to be notes.
  - Re-examine whether an Obsidian note is the best way to store entities (source notes mix structured + unstructured; entities have only structured data).
  - Clear distinction between candidate-note and source-note (distinct phases of the lifecycle).

### Note types
- fleeting-note, reference-note, project-note, code-note don't appear in the design. Framing, corpus-map, gap-card, gap-report, outlines, report are not currently defined notes.
- **ZK core note types:** Fleeting (temporary captures, discarded/processed within a day or two); Literature/Source (brief summaries with a reference, in your own words); Permanent/Evergreen/Main (single atomic idea, full clear sentences, understandable without context, connected to others). **Supporting:** Structure Notes/Hubs (tables of contents / narrative threads organizing permanent notes to outline a topic or prep writing); Project Notes (temporary, task-specific, archived when done); Index Notes (high-level overview pointing to structure notes / key themes, for navigation).

### 5. State model & non-monotonic knowledge
- Do the new states apply to all note types? How do they differ from current lifecycle states? Replacing or adding? How per type?
- Are fleeting, answer, and claim notes different types, or one type in different states?

### Beyond this point (new components)
- Everything up to the **Validation status** improves the EXISTING (already-approved) design goal — only implementation needs agreement. Everything from Validation onward introduces NEW components with no parallel; mark them explicitly, state the problem each solves, agree the problem+approach BEFORE implementation. Finalize the first part first (ripple effects).

## Clean-slate reasoning (the "six weeks old, reconsider from first principles" note)

- Memoria began: integrate rigorous research practices into the **Karpathy Wiki LLM.** Chose Obsidian (popularity), Hermes (built-in learning loop), Zotero (bibliography) — **as defaults, without evaluating fit.**
- Karpathy's ingest/query/lint was too limited. We needed background + user-triggered, deterministic + LLM-driven. Adopted Hermes without checking fit. Unasked questions: Is the Hermes **kanban board** suitable (rigid, predefined; we need multiple workflows/actors)? Are Hermes **profiles** the right mechanism for granular LLM control (should all librarian tasks use the same LLM)?
- Adopted **ZK** for the knowledge layer. Linking source notes to Zotero records was insufficient (couldn't manage knowledge-graph sources or creator forms) → introduced **entity notes → the catalog.** Kept using existing tools without assessing suitability. **Obsidian is not clearly the best option for a structured knowledge graph.**
- Adapting Obsidian as the UI forced changes signaling issues: an **inbox** to mediate Hermes background processes ↔ user; layers to restrict direct file access and enforce rules Obsidian wasn't built for.
- Seven-layer architecture: deliberately chose Hermes (Co-PI) + Obsidian (vault), but later choices lacked requirements analysis. **L7 became a mix of notes + data repositories → lack of clarity.** We didn't conceptualize Memoria as an **application** or implement an appropriate **agentic application stack.**
- **Six weeks old, pre-beta, no working installations. Ideal time to reconsider the application stack from first principles — clean-slate design from requirements and best practices, not the current implementation.** See ards-project/ard-spec and GoogleCloudPlatform/knowledge-catalog OKF SPEC.

### Round 1
- **Memoria is an opinionated, personal tool for thinking and writing — a durable research vault that compounds across months and years.**
- **Personal** — thinking is private/separate from communication; unfiltered notes preserve raw reasoning before audience-aware editing sanitizes it. **One human who owns judgment** (review, synthesis, scope). **Not a team tool.**
- **Opinionated** — enforces specific workflows, eliminates setup paralysis. Vault structure, document types, review gates are **not configurable surfaces — they are the design.**
- **Knowledge production, not just storage:** the vault grows more useful over time (new sources connect to existing claims; synthesis sharpens as evidence accumulates; structural maintenance keeps the graph coherent). **That is the difference between a research vault and a notes pile.**
- **Local-first is a current implementation constraint, not a goal.** A solution usable by a single user on several computers is an advantage. **The storage local + exportable-ownership requirement was derived from the local-first assumption rather than from first principles/actual requirements.**
- Recommended file-based DB + markdown+frontmatter makes sense. **SQLite was chosen as a default without considering alternatives based on requirements.**
- (At least) two UI surfaces: markdown+frontmatter, and the rest. **Obsidian chosen as a default without considering alternatives.** The "rest" should integrate into the chosen editor for a unified experience.
- **Safety** — limit the blast radius of (human/agent/system) errors and of poisoned input; keep it traceable and reversible.
- Memoria doesn't aim to replace Zotero but can do most of what it does. Study Zotero and JabRef design.
- **The source-capturing process is based on academic papers but should apply to any digital source.** When capturing: (1) keep an **immutable raw copy** (PDF, web page, audio); (2) extract content into markdown; (3) extract metadata (rich for academic; min bibliographic per ACM); (4) add source + immediate entities to the **catalog graph** (source, authors, orgs, venue, cited-by, references); (5) create a (candidate?) source note.
- **The catalog graph is a deterministic, objective representation of sources. The source note connects the catalog graph to the knowledge/notes SUBJECTIVE graph based on ZK and the Toulmin model.**

### Round 2
- What's the difference between the two types of projects from the system's POV? Does having two types outweigh the added cognitive-model complexity?
- What happens if I start a project without any seed bibliography?
- **Gap analysis should analyze BOTH the sources and the notes graphs, and the gaps between them:** Dense knowledge+resources = desired state; thin = new topic; **a mismatch between the graphs is the really interesting case.**
- Should a project be an **independent knowledge bundle** inside the vault?
- Is Razlogova's annotation note a type of permanent note?
- Terminology: Adopt ZK terms? Why is source-note the only one with `-note`? If we use `-note`, we can't have `note` as a type.
- Do we need the ZK index?
- Should non-source notes link directly to a source, or should all other notes link to the source note?
- **"In your own words" distinguishes source vs permanent/annotation notes.** Adding a source assumes the user knows what it's about; an LLM writing a source note in its own words is task delegation (user may rewrite). A permanent/annotation note is two tasks: deciding whether to have a note (needs context) and writing it. The system can help by talking about sources and suggesting notes (guided reading, like Open Notebook); a project provides context.
- **The Toulmin model is relevant only to creating a graph for a project.** Optional; **don't force the Toulmin overlay on every note.**
- Pros/cons of SQLite FTS5 + sqlite-vec vs QMD?
- On-disk layout: self-explanatory, industry-standard terminology.
- Why do projects have a slug, not an ID?
- Catalog Concepts have creators[], venue and Links: authored_by, published_in.
- What are the plugin's two panels?
- **Separation of duties: the operation that generates is never the one that checks.** Examples? For each agent/human operation, an additional agent QA operation; repeat until approved; then the system checks graph/system integrity; repeat until approved; then human approval if needed + log for traceability.
- **Milestones:** many milestones look disciplined but the current design hit a wall; we can't proceed without beta.1. Ideal: test everything checkable before implementing; implement the **basic knowledge cycle** + plugin; test; more milestones if needed. **Any milestone that doesn't enable at least the basic knowledge cycle (which also requires the plugin) is meaningless.** First milestone = **0.1.0-beta.1.**
  - **Basic knowledge cycle:** Open a project (question/thesis) → seed it → gap analysis surfaces what's missing → source to fill gaps → capture any digital source (immutable raw copy + content + metadata) → extract atomic annotations → develop notes/claims toward the thesis → re-run gap analysis.
- **ADRs should be written to enable retirement of as many ADRs as possible.** History can provide context but also confusion. Prune stale ADRs, reduce count to the necessary minimum.

### Round 3
- How does each concept type map to the OKF? How do we use tags? How do the Toulmin elements map to it?
- Terminology: Source vs digest; Note vs idea vs thought vs insight; Hub vs topic vs index; Catalog vs library.
- **Since two modules are still missing (writing and coding), the version will be alpha.11, not beta.1.**

## Alpha.15 (TRUNCATED — owner to re-paste from here)

- Is the **journal-as-forensic-truth** the right model? **Basic assumption: knowledge integrity is not asserted by semantic evaluation of a single node or edge validity, but by the STRUCTURAL INTEGRITY OF THE KNOWLEDGE GRAPH.** A validity incident can occur in response to 3 types of events:
  1. Any change to the graph, by a human or a machine, triggers a verification response that may trigger an integrity incident.
  2. The user decides there is an error in the graph.
  3. Periodic.
- *[message truncated here — remainder not captured]*
