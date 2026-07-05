# Part II — The full alpha.1 design (baseline)

*Reconstructed from the tree at the alpha.1 release commit `0e9ed9dd` ("split 0.1.0 → 0.1.0-alpha.1", 2026-06-14). Four facets: the vault & knowledge model; profiles, SOUL & the Hermes runtime; the write gate, policy engine & provenance; and the pipeline, discovery, evaluation, distribution & ADR landscape.*
### Vault structure & knowledge model

> **A note on what "alpha.1 as of `0e9ed9dd`" contains.** Commit `0e9ed9dd` ("docs(releasing): split 0.1.0 → 0.1.0-alpha.1; add alpha.2 checkpoint plan", #452) is the alpha.1 release commit *after* the large design update (the D-series, ADRs 46–68) had already been applied to the shipped scaffold and reference docs. The tree at this commit therefore ships a **type-first category-folder** vault (`catalog/ · notes/ · projects/ · inbox/ · system/`), not the **lifecycle-numbered** folders (`00-meta/ … 95-archive/`, including `10-inbox/02-answers/`) that the *originally-built* alpha.1 used. The numbered scheme survives at `0e9ed9dd` only in the point-in-time release/test records (`docs/releasing/0.1.0-alpha.1/manual-testing.md` opens: *"paths here (numbered folders such as `00-meta/01-dashboards/` and `30-synthesis/`)… are **not current**"*) and in the superseded `ADR-04`. This section reconstructs the **authoritative shipped design at `0e9ed9dd`** (type-first) in full, then documents **the numbered-folder taxonomy it superseded** with the reasoning for the change — because that transition *is* the central design decision of the alpha.1 vault model.

---

#### 1. Top-level taxonomy — type-first category folders

The vault root is organized by **category — one content kind per folder, no lifecycle numbers** (`docs/explanation/architecture/vault.md`; `src/.memoria/schemas/folders.yaml` declares `categories: [catalog, notes, projects, inbox, system]`):

```text
<vault-root>/
├── home.md         ← front door (absorbs the daily-health glance)
├── research-focus.md  program memory — the PI's standing steering
├── AGENTS.md          ground rules for any agent in the vault
├── troubleshooting.md vault-root nav page
├── catalog/        CATALOG: structured entity records (Obsidian Bases)
│   papers · people · organizations · venues · datasets · repositories
├── notes/          NOTES: prose (Zettelkasten)
│   fleeting/ · source/ · claims/ 🔒 · hubs/ 🔒 · index/
├── projects/       PROJECTS: work artifacts (ships empty in v0.1.0-alpha.2)
├── inbox/          INBOX: agent→human message cards (candidate · gap · flag · alert · work-prompt)
├── system/         SYSTEM: visible infrastructure — logs · templates · patterns · dashboards · board · eval · metrics
├── .obsidian/      hidden Obsidian app config (Bases defs, layouts, graph groups)
└── .memoria/       hidden runtime (MCP, profiles, schemas, golden copy)
```

**What:** Five type-first vault-root categories, one content kind per folder, "one folder never mixes two categories," folders named for their *content* not for a doer.
**Why:** `ADR-47` supersedes `ADR-04`. The design update (D2/D24) found that *"the knowledge is a **network**, not a pipeline: direction belongs in a **state property**, and the real structural distinction is the entity/note/artifact/signal split"* (`docs/adr/47-type-first-category-folders.md`). Naming folders for content rather than doer keeps them stable: *"both the ingest engine and the Librarian agent operate on `catalog/`"* (`vault.md`). The rejected alternative — topic folders — fails because *"topics are many-to-many"* and a topic folder forces you to *"pick one folder and lose the connections… or create duplicates that immediately diverge"* (`docs/explanation/knowledge/lifecycle-over-topic.md`); this half of `ADR-04` **survives unchanged** and is itself a Zettelkasten inheritance ("Luhmann's slip-box had no subject folders").

**What:** The type→folder map is machine-read from one file (`src/.memoria/schemas/folders.yaml`).
**Why:** It is *"the single source for the Linter, the policy gate, the installer skeleton, and the tests"* (`vault.md`) — a schema change is a one-file edit, never a hunt across hardcoded lists (`frontmatter.md`). `folders.yaml` declares `homes:` (type→path), `gated_prefixes: [notes/claims/, notes/hubs/]`, `transient_prefixes: [inbox/]`, and the full installer `skeleton:`.

**What:** `.memoria/` (runtime) and `.obsidian/` (app config) are hidden peers of the vault; `.memoria/schemas/` is *"THE single schema source"* holding per-type schemas, `folders.yaml`, and `calibration.yaml` (drift-bound thresholds) (`docs/reference/on-disk-layout.md`).
**Why:** Separates the human-facing knowledge surface from machinery; the installer scaffolds the skeleton and *populates it from `src/`* as a restorable golden copy (`ADR-55`).

---

#### 2. Note & concept types — the 18-type roster

There are **18 typed notes in four categories**: 6 catalog entities, 5 notes, 5 inbox cards, 2 system types (`docs/reference/note-types.md`). The schemas under `src/.memoria/schemas/types/` are authoritative; the reference page is the human view and *"the schemas win on any disagreement."*

**Catalog entities (6)** — `paper`, `person`, `organization`, `venue`, `dataset`, `repository`. All in `catalog/`, engine-built, Base-backed, keyed on stable IDs (DOI/ORCID/ISSN), carrying **given** `relationships`. None is review-gated.

**Notes (5)** — `fleeting`, `source`, `claim` 🔒, `hub` 🔒, `index`. Carry **authored** `links:`. Two live in gated zones.

**Inbox cards (5)** — `candidate`, `gap`, `flag`, `alert`, `work-prompt` (all flat in `inbox/`, start `proposed`, converge to `archived`).

**System types (2)** — `pattern` (`system/patterns/`), `eval-task` (`system/eval/`).

| Category | Type | Folder | Lifecycle subset | Gated | Required fields |
|---|---|---|---|---|---|
| Catalog | `paper` | `catalog/papers/` | `current → retracted → archived` | no | `citekey`, `title` |
| Catalog | `person` | `catalog/people/` | `current → archived` | no | `name` |
| Catalog | `organization` | `catalog/organizations/` | `current → archived` | no | `name` |
| Catalog | `venue` | `catalog/venues/` | `current → archived` | no | `name` |
| Catalog | `dataset` | `catalog/datasets/` | `current → retracted → archived` | no | `name` |
| Catalog | `repository` | `catalog/repositories/` | `current → archived` | no | `name` |
| Notes | `fleeting` | `notes/fleeting/` | `proposed → archived` | no | `origin` |
| Notes | `source` | `notes/source/` | full chain | no | `title`, `entity` |
| Notes | `claim` | `notes/claims/` | `current → retracted → archived` | **yes** | `title`, `maturity`, `sources` |
| Notes | `hub` | `notes/hubs/` | `current → archived` | **yes** | `title`, `topic` |
| Notes | `index` | `notes/index/` | `current → archived` | no | `title` |
| Inbox | `candidate` | `inbox/` | `proposed → current → archived` | no | honesty body (below) |
| Inbox | `gap` | `inbox/` | same | no | honesty body |
| Inbox | `flag` | `inbox/` | same | no | `finding`, `agent_recommendation`, `target`/`citekey` |
| Inbox | `alert` | `inbox/` | same | no | `title`, `finding` |
| Inbox | `work-prompt` | `inbox/` | same | no | `action`, `what_happened`, `target`/`task_id` |
| System | `pattern` | `system/patterns/` | `proposed → current → archived` | no | `title`, `posture`, `mode`, `action`, `input`, `output_target` |
| System | `eval-task` | `system/eval/` | same | no | `title`, `workflow`, `lane` |

**What:** The deepest split is **Catalog (given facts, ungated) vs Notes (judgment)**.
**Why:** This *"revives Luhmann's two-box system: he kept a **bibliographic index** physically separate from the **main slip-box**"* (`docs/explanation/knowledge/note-types.md`). Catalog frontmatter is *"given facts built by ingest and not gated"* while *"the claim and hub are the PI's judgment"* (`vault.md`). Keeping the boxes separate is *"what lets the mechanical half run ungated while the judgment half stays human."* The same paper is therefore two files — the `paper` entity (bibliographic fact) and, if read, a `source` note pointing back at it.

**What:** The prose note types map to Luhmann's three-way distinction under software names: `fleeting` (raw capture), `source` (= literature note, "what the source says"), `claim` (= permanent note, "what the PI thinks").
**Why:** *"The rename reflects a software context; the distinction is unchanged"* (`docs/explanation/overview/intellectual-foundations.md`). The `claim` is *"the synthesis atom"* and enforces atomicity — *"one claim per note… if the title contains an 'and' doing real conceptual work, it is two notes"* (`note-types.md`), because *"wikilinks citing a multi-claim note are ambiguous, and a multi-claim note cannot be cleanly superseded."*

**What:** `hub` is the renamed MOC; the `reference` type was **dropped**.
**Why (both in `ADR-50`):** MOC→hub keeps the threshold-alert mechanism (`ADR-19`) under a plainer name. `reference` was retired because it *"double-encoded maturity"* (an `evergreen` claim *is* the settled unit) and *"collided with Zettelkasten vocabulary,"* where "reference note" already means a literature note (our `source`).

**What:** The old alpha.1 `paper-note`/`item-note` prose split collapsed into one `source` type.
**Why:** *"identification now lives on the entity — paper vs repository vs dataset — and the prose is one `source` note type regardless"* (`note-types.md`).

---

#### 3. Frontmatter schema — the field-kind grammar

The contract lives in `src/.memoria/schemas/types/<type>.yaml`, loaded/validated by `src/.memoria/engines/lib/schema.py`. Each schema declares `required:` and `optional:` maps of `field: kind`, an `enums:` block, and optional `required_any:` (`docs/reference/frontmatter.md`). Field kinds: `str`, `int`, `bool`, `date`, `list`, `map`, `literal:<value>` (pins a field, e.g. `type: literal:claim`), `enum:<name>`. **Unknown extra fields are allowed** — *"the schema constrains, it does not enumerate."* Verbatim `claim.yaml`:

```yaml
type: claim
category: notes
gated: true # review-gated zone (ADR-03/ADR-47)
enums:
  lifecycle: [current, retracted, archived]
  maturity: [seedling, budding, evergreen] # a property, never a gate (ADR-50)
required:
  type: literal:claim
  lifecycle: enum:lifecycle
  title: str
  maturity: enum:maturity
  sources: list # every claim → a citekey (provenance guardrail)
optional:
  links: map # supports / contradicts / … (ADR-52)
  topics: list
  superseded_by: str
  created: date
```

**What:** A **single universal lifecycle chain** with per-type subsets: `proposed → provisional → current → retracted → archived`.
**Why (`ADR-50`):** alpha.1 originally *"carried several state vocabularies side by side (note lifecycle values, board states, a settled-claim note type)"*; the update unified them so there is *"one state vocabulary to learn."* The rejected alternative (per-type vocabularies) *"multiplies the mental model for one user; subsets of one chain capture the same constraints."* Subsets encode epistemic shape: entities are born `current` (facts don't await approval), `source` starts `proposed` (awaiting reading), `claim` exists only once the PI makes it `current`. The subset ⊆ chain constraint is test-enforced (`frontmatter.md`).

**What:** `maturity` (`seedling → budding → evergreen`) is a **claim property, never a gate**, riding alongside lifecycle; and `agent_recommendation` (`inconclusive → issues-found → clean`) is a soft agent verdict.
**Why (`ADR-50`, `promotion-model.md`):** the two axes — *"how trusted?" (lifecycle) and "how developed?" (maturity)* — are deliberately different value sets so *"neither can impersonate the other."* Nothing auto-promotes at `evergreen`; a `clean` recommendation *"never substitutes for human approval."* Rejected alternative: maturity as a lifecycle axis — *"it gates nothing and varies only on claims — a property, not a state."*

**What:** The PI-facing `lifecycle` is separate from the board's hidden `status` execution enum.
**Why:** the Hermes-native `status` *"stays a hidden mechanic, never shown to the PI"* (`ADR-50`) — the human sees one state vocabulary, the runtime keeps its own.

**Enforcement.** A pre-commit `schema-check` gate (`src/.memoria/engines/linter/precommit_check.py`) blocks git-tracked writes that fail their schema; the daily Linter cron monitors between commits. `system/` infrastructure (except `system/patterns/`) and the three vault-root nav pages (`home.md`, `research-focus.md`, `troubleshooting.md`) are untyped and exempt.

---

#### 4. Links vs relationships — two kinds of connection

**What:** Notes carry **authored `links:`** (a `map` of typed edges — `supports`, `contradicts`, `extends` — whose values are wikilinks); catalog entities carry **given `relationships`** (`cited_by`, `authored_by`, `published_in`). Two related fields: a `source` note's required `entity` (wikilink to the catalog entity it is about) and a `claim`'s required `sources` list (citekeys = bibliographic provenance).
**Why (`ADR-52`, supersedes `ADR-08`):** `ADR-08`'s single `relations:` field *"conflated two different things"* — objective facts about sources vs connections the PI draws — which *"differ in nature, owner, and gating,"* and `relations`/`relationships` were *"a near-synonym clash waiting to happen (D17)."* The split means *"the link-confirmation gate applies only where judgment lives; mechanical facts flow ungated"* (with the low-confidence→`flag` escape valve, `ADR-56`). It also yields *"two typed layers — a citation/identity graph over entities and an argument graph over notes,"* enabling the contradictions dashboard (`ADR-09`) and claim supersession (`ADR-10`). The Linter's `frontmatter-link` detector checks every `links:`/`entity` wikilink resolves; citekeys are checked by sweeps. Rejected: one field for both (forces one gating rule onto two trust models); `references`/`connections` naming ("reference" was already retired and is citation-narrow).

**What:** *"`archived` is a state, not a folder"*; a state change is a frontmatter edit, never a file move.
**Why (`ADR-47`/`ADR-50`, `lifecycle-over-topic.md`):** under the old numbered-folder model *"every state change moved a file — and every move risked breaking wikilinks, losing Git history continuity, and invalidating saved queries."* Now *"a note is born in its type-home and dies in its type-home"*; *"a claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking."* This protects provenance — the property *"the whole system is built to protect"* — and keeps the agent's write-permission paths stable (*"the answer never shifts under it mid-task"*).

---

#### 5. The Inbox and the honesty card

**What:** `inbox/` is the agent→human message category; the kanban board and queue dashboards are *views* of it (one Base grouped by type). Five card types in three shapes:
- **Proposals** (`candidate`, `gap`) carry an **honest argument, no verdict**: `action` · `argument_for` · `argument_against` (the agent's strongest self-rebuttal) · `what_tipped_it` · `certainty` (3-level: `confident`/`likely`/`unsure`).
- **Verification cards** (`flag`, `alert`) **lead with the finding** and keep a verdict (`agent_recommendation`).
- **Work-prompts** carry `action`/`what_happened`/pointer, never a verdict.
All share optional `raised_by` and `loudness` (`quiet`/`notice`/`alert`/`block`) and route through one shared writer, `src/.memoria/engines/lib/inbox.py`.

**Why (`ADR-51`):** agent→human signals were *"scattered (candidate notes in a folder, board cards, dashboard rows)"* and a confident verdict on a card *"begged the automation-bias question: research shows handing a human a confident verdict **reduces** scrutiny."* For a proposal the verdict is *"a given — the agent surfaced the item because it recommends it,"* so a verdict line is vacuous; *"an Inbox item the PI can clear without reading is a design smell,"* and the against-case + certainty are *"the information-bearing fields."* High-cardinality screening becomes *"one aggregate work-prompt"* over a Bases worklist, never N cards, which *"would flood a queue meant to converge to zero and invite select-all-accept"* (`ADR-54`). Rejected: ship the verdict on every card (induces automation bias); blind-first (nothing to hide on a proposal).

---

#### 6. Controlled vocabulary

**What:** `src/system/vocabulary.md` (itself an `index`-typed note, `lifecycle: current`) is the single source for three classification facets: `research_area` and `methodology` (on `paper` and `source`) and `topics` (on `claim`). It ships ~27 curated `research_area` terms (health-informatics domain), a two-group `methodology` list (research architecture + specific technique), each term with a one-line definition.
**Why (`docs/explanation/knowledge/vocabulary-discipline.md`):** separate facets because they *"answer categorically different questions"* — `methodology` is *how* a study was structured, `research_area` is *what* it is about; *"routing both to the same field makes both queries unreliable."* `research_area` is *seeded mechanically from OpenAlex topics* by `classify.py` so *"the vocabulary is free and consistent across sources"* — removing *"one whole class of drift at intake."* Consolidation is **deferred to ~50 papers** because *"premature consolidation locks in the wrong vocabulary… the cost of false consolidation is higher than the cost of deferring."* The failure this guards against — drift like `receptivity-detection` vs `opportune-moments` — *"produces no error… queries return incomplete results; the PI infers thin coverage when coverage is adequate."* Reference taxonomies (MeSH, ACM CCS) are deliberately kept out of the queryable facet, living in each note's `_enrichment` namespace *"for browsing, not querying."*

---

#### 7. Note body structure

**What:** The three prose types have prescribed section bodies (templates in `src/system/templates/`). `source`: **In my words** / **Worth distilling** / **Tensions**. `claim`: **Claim** (one sentence) / **Evidence** (every line traces to a `sources` citekey) / **Connections** (typed links). `hub`: what the area is about / what belongs now / what needs review.
**Why (`docs/explanation/knowledge/note-body-structure.md`):** a source note's Summary is *"what the PI reads six months later to cite the paper without re-reading it"*; a source note without a Critique is *"storage, not synthesis."* A claim's required Links section is *"the most structurally significant"* — *"a claim with no `links:` has not made it into the knowledge graph… it cannot compound"* (the Zettelkasten principle that *"a note's value comes from its links, not its contents"*). A source note may never contain the PI's own claims, because otherwise *"the boundary between 'what the source says' and 'what I think' would collapse, and provenance would become unverifiable"* — the same epistemic separation that lets `notes/claims/`/`notes/hubs/` be gated while source-note authoring is delegable bookkeeping.

---

#### 8. Templates, Bases views, dashboards, homepage

**Templates (16).** `src/system/templates/` ships starter notes for **16 of the 18 types** — all except `pattern` and `eval-task` (authored directly in their folders): `alert, candidate, claim, dataset, flag, fleeting, gap, hub, index, organization, paper, person, repository, source, venue, work-prompt`. **What/Why:** *"Templates are scaffolding — the schemas, not the templates, are what validation runs against,"* and the Linter's golden-copy check keeps deployed templates byte-identical to the shipped ones (`note-types.md`).

**Bases views (6).** `.base` files sit alongside their data: `catalog/catalog.base`, `inbox/inbox.base`, `system/dashboards/{claims,sources,fleeting}.base`, `system/patterns/patterns.base`. **Why (`ADR-49`):** entities and queues surface through Obsidian Bases (*saved DB views over frontmatter*), but *"every row is a file; the records are the source of truth; nothing reads a Base as data."* Because *"Bases has no integrity guarantees — no schema, no constraints,"* that gap is the Linter's job (a monitor + commit gate that can restore from the golden copy).

**Dashboards (12 files → 11 dashboards).** `src/system/dashboards/` ships `board-state, reading-pipeline, discuss-queue, open-questions, contradictions, drift-watch, loose-ends, weekly-review, audit-log, fleet-health, eval-trend, skill-lifecycle` plus the three `.base` files. **What/Why (`docs/reference/dashboards.md`):** *"Two changes from v0.1.0-alpha.1: **daily-health was absorbed into the homepage**… and **board-state is now the Inbox board**."* Dashboards are read-only health views (*"empty is success"*, *"one decision per dashboard"*, *"graceful degradation"*); the Inbox is the action queue. The explanation site groups them into four attention-kinds: Daily glance, Synthesis agenda (Library), Structural health (Maintenance), Operational health (Agent-ops).

**Homepage / cockpit.** `src/home.md` (`cssclasses: [dashboard]`) is the front door (`ADR-13`), opened on startup by the optional `obsidian-homepage` plugin. It carries an above-fold **Status glance** (a `dataviewjs` block over `board-state.jsonl`/`lint-findings.jsonl` — *"N review(s) pending · N blocked · N HIGH/CRITICAL"*), an **Act** button row (QuickAdd capture/delegate/resolve, ACP chat), a **Workspaces** row (Desk/Library/Studio — `ADR-68`), and a grouped **Dashboards** index. `research-focus.md` is separate **program memory** the Librarian reads at session start to *weight discovery*.

---

#### 9. Gated zones and the Linter

**What:** `notes/claims/` and `notes/hubs/` are 🔒 gated (`gated_prefixes` in `folders.yaml`); the policy MCP degrades every agent write there to `dry_run`. The Catalog is deliberately **ungated**.
**Why (`vault.md`, `promotion-model.md`, `ADR-03`):** *"Agents propose (cards, staging artifacts); the PI disposes."* Gating claims/hubs protects the trust posture — *"when the Peer-reviewer traces a draft's citations, it assumes the claims represent positions the PI actually holds."* The Catalog is left open because *"its content is given facts, not judgment,"* and gating it *"would be a rubber stamp"* — with the single escape valve that low-confidence extraction routes to a `flag` (`ADR-56`) rather than merging silently. Classify is *"neither an approval nor a work prompt — it is automated,"* because a human gate on high-volume verifiable metadata *"is a guaranteed rubber stamp"* (`ADR-54`). The gate is the deliberate bottleneck: *"a system that could populate `notes/claims/` without the PI's attention would be a system where the PI no longer owns their own knowledge base"* (`promotion-model.md`).

---

#### 10. The numbered-folder taxonomy this superseded (original alpha.1)

The alpha.1 build that shipped 2026-06-09 (`release-plan-0.1.0-alpha.1.md`: *"Frozen record… numbered folders reflect that point in time and is not current"*) used **lifecycle-numbered top-level folders**, per the then-current `ADR-04`:

```text
00-meta/       (01-dashboards/, 04-reference/, vocabulary.md, skill-insights/)
10-inbox/      (01-fleeting/, 02-answers/)
20-sources/    (01-papers/, 02-items/, entities)
30-synthesis/  (01-claims/, 02-reference/, 03-moc/)
40-workbench/  (per-project: 01-map/, 02-framing/, 04-drafts/, 06-code/)
50-deliverables/   (terminal, frozen)
90-assets/  ·  95-archive/  ·  99-system/ (templates/, board/, logs/)
```

The original type set was **16 note-type names** — `fleeting-note, answer-note, paper-note, item-note, person-note, organization-note, venue-note, claim-note, moc, reference-note, project-note, code-note, canvas, draft, deliverable, candidate-note` — with **16 templates** in `99-system/templates/` and a **10-dashboard suite** whose entry point / cockpit was `00-meta/01-dashboards/daily-health.md` (`release-plan-0.1.0-alpha.1-appendix.md`, steps under "Vault structure"). Promotion meant physically *moving the file forward* through the numbered stages; `50-deliverables/` was terminal-and-frozen (`ADR-14`); `95-archive/` was a real archive folder.

**What changed, and why:**

- **What:** Numbered lifecycle folders → type-first category folders (`ADR-04` → `ADR-47`). **Why:** *"numbered folders imply a **pipeline**, and the knowledge is a **network**. A claim doesn't travel anywhere when the PI retracts it… What changes is its standing — and standing is a property, not a location"* (`lifecycle-over-topic.md`). The stated defect of the old model: *"every state change moved a file — and every move risked breaking wikilinks, losing Git history continuity, and invalidating saved queries."*
- **What:** `95-archive/` and `90-assets/` folders removed. **Why:** *"derived artifacts are hidden runtime data; archived notes stay put"* (`ADR-47`); `archived` became a state (`ADR-50`), costing *"zero file churn."*
- **What:** `paper-note`+`item-note` → one `source`; `reference-note` dropped; `moc` → `hub`; `answer-note` (the `10-inbox/02-answers/` drafts) retired. **Why:** identification moved to the entity, `reference` double-encoded maturity, and MOC/hub was a naming fix (`ADR-50`).
- **What:** Candidate notes-in-a-folder, board cards, and dashboard rows → the unified `inbox/` message category with the honesty card. **Why:** the signal end of the loop became first-class and honesty its guardrail (`ADR-51`).
- **What:** Multiple state vocabularies + settled-claim type → one universal lifecycle chain + `maturity` property. **Why:** *"one state vocabulary to learn"* for a single user (`ADR-50`).

The half of `ADR-04` that **survived**: topic never lives in folders — *"what a folder can uniquely encode is what a note **is**,"* while topics stay in frontmatter facets (`research_area`, `methodology`, `topics`) and links, and topical navigation is built by hubs (`lifecycle-over-topic.md`).

---

#### 11. Intellectual grounding (the "why" beneath the model)

The whole model is an explicit integration of four traditions plus a ~47-system field survey (`docs/explanation/overview/intellectual-foundations.md`): **Karpathy's LLM-wiki** ("the vault is the compiled artifact… the agent is a compiler, not just a retriever" — but *"the human decides what enters the canonical graph"*); **Luhmann's Zettelkasten** (atomicity, explicit linking, the fleeting/literature/permanent type distinction, and the two-box catalog/notes split); **Bush's Memex** (the associative wikilink/hub/relationship graph as primary, folders secondary — *"a claim note with no incoming links… may as well not exist"*); and the survey's adopted patterns (stage-gated pipelines, thin control over thick state = *"agents fail when state lives in chat and succeed when state lives in files"*, explicit agent roles, structured handoff outputs, persistent knowledge graphs). What the survey made Memoria *decline* directly shapes the vault's gating: **advisory-only LLM review** (Memoria makes the gate structural instead), **scalar-metric keep/revert**, and **tree-search over synthesis** — because *"none of those numbers is plausible for 'is this synthesis a faithful, well-cited, non-redundant addition.'"*

**Key files for this section:** `docs/explanation/architecture/vault.md`, `docs/reference/{on-disk-layout,note-types,frontmatter,dashboards,linking}.md`, `docs/explanation/knowledge/{lifecycle-over-topic,note-types,promotion-model,note-body-structure,knowledge-cycle,vocabulary-discipline}.md`, `docs/explanation/overview/intellectual-foundations.md`, `src/.memoria/schemas/folders.yaml` + `schemas/types/*.yaml`, `src/system/{vocabulary.md,templates/*,dashboards/*}`, `src/home.md`, `src/research-focus.md`; ADRs 47, 50, 51, 52, 54, 49, 03, 56, 04 (superseded); release records under `docs/releasing/0.1.0-alpha.1/`.

### Profiles, SOUL model & the Hermes runtime

> **Reconciliation up front — the premise's "seven" does not match what ships at `0e9ed9dd`.** The task frames this as *seven specialist profiles* and lists *co-pi, engineer, librarian, peer-reviewer, writer, retriever-scout, and a 7th*. That list conflates two different rosters, and neither is what is on disk at this commit. The live source of truth — `src/.memoria/profiles/` — contains exactly **five** profile directories: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`. The "seven specialists" is the **superseded** ADR-02 roster (*Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter* — the 7th the premise couldn't name is the **Linter**), and **retriever-scout** (ADR-37) was a *proposed* split of the Librarian that **never shipped** and was killed by the same decision that produced the five. As of `0e9ed9dd` the design is unambiguously **"one co-PI + four background lanes = five profiles"** ([ADR-48](docs/adr/48-copi-and-agent-consolidation.md)); the seven-profile model is history. I reconstruct the *shipped five* as the design, then account for the *superseded seven* (and retriever-scout, and the profile-compiler) as the decisions that governed how the set got to five. Per the ground rules I flag this rather than silently reconstruct a seven-profile system that does not exist here.

> **Version note.** Commit `0e9ed9dd` is the docs commit that *split 0.1.0 → 0.1.0-alpha.1 and added the alpha.2 checkpoint plan* (`docs(releasing): split 0.1.0 → 0.1.0-alpha.1`). The shipped profile manifests already carry `version: 0.1.0-alpha.2` and the docs already describe the consolidated (post-ADR-48) model. So "the alpha.1 design as of `0e9ed9dd`" *is* the five-profile consolidation; the earlier seven-profile shape is visible here only as superseded ADRs and as install-time pruning of "the v0.1.0-alpha.1 seven-profile set" (`docs/explanation/deployment/distribution-model.md`).

---

#### 1. The runtime: build *on* Hermes, don't build a runtime

**What:** Memoria's entire execution layer — the Kanban board (`kanban.db`), the worker profiles, the dispatcher, the memory tiers, the MCP host, and the API server (port 8642) — is the external **Hermes Agent** runtime (Nous Research). Memoria supplies only *conventions on top*: the review-gate overlay in card `metadata`, the policy MCP that gates writes, the five profile `SOUL.md`s, and the vault schema. The governing rule is *"Hermes moves work; Memoria decides what work means and what may become canonical."*

**Why:** The hardest runtime problems — *"durable state across crashes, atomic card claiming, retry semantics, MCP hosting"* — *"are not Memoria's to solve"* and *"a reimplementation would be a worse copy plus a permanent maintenance burden, for no gain in the knowledge layer"* (`docs/adr/22-build-on-hermes-runtime.md`, Consequences / Alternatives). The decision explicitly rejects three named alternatives, each because it *"routes durable state or permissions through the wrong layer"*: **AutoGen-style chat-as-substrate** (*"Memoria's state must survive `/clear` and cross-profile handoffs in thick stores"*), **OpenHands-style sandbox-vs-host permissions** (*"Memoria needs permissions enforced per-profile at the write layer"*), and **rendering the board with the Obsidian Kanban plugin** (*"couples two state machines for no gain"*). This is a deliberate *"borrow"* in the pattern-provenance sense (`docs/explanation/rationale/why-hermes.md`). The load-bearing consequence: *"anything that would require modifying Hermes internals … is a signal the design has drifted"* — the boundary is enforced by keeping the overlay in `metadata` Hermes treats as opaque, so Memoria stays compatible with a stock Hermes install.

**What:** The API server (port 8642) is a *separate* surface from the human channels (Obsidian, CLI, Telegram). **Why:** *"Programmatic integration needs a different interface than human operation"* — a filesystem watcher on a PDF drop *"cannot use the command palette."* But it *"grants no extra power … A program calling the API has exactly the permissions of the profile it acts as — no elevation. The API is a different door, not a different key"* (`docs/explanation/rationale/why-hermes.md`). Every API write still passes the policy MCP.

---

#### 2. Hermes-native config and the write gate (the mechanism the profiles depend on)

The profile model is only coherent given *how Hermes reads config*, which was fixed by a Tier-4 live investigation recorded in **ADR-27** and corrected by **ADR-28**.

**What:** Each profile is its own `HERMES_HOME` (`~/.hermes/profiles/<name>/`), and Hermes reads `model`, `mcp_servers`, `agent.disabled_toolsets`, `terminal`, `checkpoints`, and `plugins` from **one per-profile `config.yaml`**. A standalone `mcp.json` is *dead* at runtime.

**Why:** The gate *failed* a live test — an agent wrote a note to an arbitrary host path (`…/OneDrive/Documents/Memoria/…`) *"entirely outside any gate."* The root cause: *"Hermes loads MCP servers only from `mcp_servers` in `config.yaml`… Memoria shipped its policy + obsidian servers in `mcp.json`, so neither ever loaded"* (`docs/adr/27-…`, Finding 1). *"Profiles do not sandbox the agent"* (Finding 2), so with no obsidian MCP write tool loaded, the agent fell back to raw filesystem writes.

**What:** Enforcement is **default-deny by toolset allowlist plus a single gated write path**. Each `config.yaml` sets `agent.disabled_toolsets = all_hermes_toolsets − lane_allowlist`, and the **obsidian MCP** (the Local REST API plugin's native MCP over loopback HTTP, ADR-31) is the *only* write path a lane has. **Why:** A denylist of `[terminal, file]` was *"insufficient … leaving code_execution, delegation, cronjob, messaging, browser, computer_use live … code_execution alone re-opens the hole"* (Finding 5). With no filesystem write tool, *"the agent's only way to write the vault is the obsidian MCP path — which the gate gates."*

**What:** The gate itself is a **Python plugin** (`memoria-policy-gate`), fail-closed, in-process, in every run mode (`-z`/CLI, gateway, cron, ACP) — not a shell hook. **Why:** ADR-28 supersedes *only ADR-27's enforcement mechanism*: the `obsidian.*` shell-hook *"never fired on live writes"* because Hermes registers the tool as `mcp_obsidian_obsidian_append_content` and *"the shell-hook `re.fullmatch` against `obsidian.*` never matches it (shell hooks are also consent-gated and fail-open)."* The plugin *"runs in-process in every mode, matches in Python, gets the task_id, and is fail-CLOSED,"* and *"hard-denies the native vault_delete/vault_move and command_execute"* (`config.yaml` comments, `memoria-librarian`/`memoria-engineer`). ADR-27's *config-model* decisions (`mcp_servers` in `config.yaml`, the allowlist, obsidian-as-sole-write-path) all **stand**.

**What:** Two more Hermes-native safety features are adopted: `checkpoints: {enabled: true}` (shadow-git snapshot before destructive writes) and `terminal.cwd: {{VAULT_PATH}}`. **Why:** *"Reversibility no longer depends on the hook firing"* — checkpoints cover even writes the gate can't see — and `cwd` *"anchors stray file ops inside the vault"* (`docs/adr/27-…`, Decision §6; every profile `config.yaml`). The investigation also corrected a doc error: *"Tirith is a command-string security scanner, not the tool-permission/capability layer"* (Finding 8).

---

#### 3. The five profiles

The design's dividing line is **posture and write-permission, not capability or tool** — *"faithful vs skeptical, read-only vs scratch-write vs review-gated"* (`docs/explanation/rationale/why-specialist-profiles.md`). Model routing is tiered by posture-load (verified from the five `config.yaml` `default:` keys):

| Profile | Posture | Lane(s) | Write scope | Model (`kilocode` gateway) | Skills |
|---|---|---|---|---|---|
| **co-PI** (`memoria-copi`) | reflective thinking-partner | *(none — the ACP pane)* | **`[]` — read-only** | `~anthropic/claude-opus-latest` | 5 |
| **Librarian** (`memoria-librarian`) | faithful | catalog · extract · link · map | `inbox/`, `catalog/`, `notes/fleeting/`, `notes/source/` | `~anthropic/claude-haiku-latest` | 12 |
| **Writer** (`memoria-writer`) | generative, draft-only | draft | `projects/` scratch | `~anthropic/claude-sonnet-latest` | 4 |
| **Peer-reviewer** (`memoria-peer-reviewer`) | skeptical, independent | verify | `inbox/` only | `~anthropic/claude-opus-latest` | 4 |
| **Engineer** (`memoria-engineer`) | delegating | code | `projects/<project>/code/` | `~anthropic/claude-haiku-latest` | 0 |

(25 skills total — the exact count ADR-43 cites as the trigger for the skill-lifecycle dashboard.)

**Why the model tiering:** the two judgment-heavy postures — holding the conversation (co-PI) and the skeptical red-team (Peer-reviewer) — get **opus**; generative prose gets **sonnet**; the *"fill only the judgment holes"* mechanical lanes (Librarian, Engineer scaffolding) get **haiku**. This follows directly from the design principle that the mechanical half of the work is engines, and the agent supplies only the narrow judgment the engine can't (`memoria-librarian/SOUL.md`: *"The mechanical half of cataloging … is the ingest engine — you fill only the judgment holes"*).

**The co-PI — the one you talk to.** **What:** *"the one agent the PI converses with … Everything else in Memoria is delegated through you or run as an engine."* Three jobs, one posture: **question** (the folded-in Socratic role — `ask:question-source`, `ask:read-lens`, `explore:branch-framings`), **explain** (`explain-the-system`), **delegate** (`delegate:route-task` → tasks MCP). It is *"read-only over the entire vault — `policy.allow.write: []`"* and is the **sole carrier** of Hermes' self-improving loop (memory · /goals · skills) and the only profile with `/personality` (`src/.memoria/profiles/memoria-copi/SOUL.md`; `docs/explanation/profiles/co-pi.md`). **Why the hard wall:** *"A conversation drifts, accumulates context, and gets persuaded; a card does not. By the time delegated work touches the vault it has passed through a lane's scoped permissions, the propose-not-dispose process, and the PI's gate — none of which a chat message can shortcut"* (`co-pi.md`). **Why the co-PI alone carries memory:** *"Hermes' self-improving loop … only compounds in an agent that has every conversation. Split across seven, each got a sliver of context and none grew"* (`why-specialist-profiles.md`). Note its `config.yaml` keeps `memory` enabled while every specialist disables it — the allowlist encodes "sole memory carrier" mechanically.

**The Librarian — faithful.** **What:** runs *four* lanes — catalog · extract · link · map — because *"a research librarian does both intake and the literature work; so do you."* *Faithful posture*: *"include generously and report state; the gate filters. You propose, never decide."* It writes only intake/staging zones and is barred from `notes/claims/`, `notes/hubs/`, `notes/index/`, `projects/`, `system/` (`memoria-librarian/SOUL.md`, ADR-47). **Why merged, not split:** the old Librarian and Mapper *"were both faithful — intake and corpus mapping are one research-librarian stance pointed in two directions"* (`why-specialist-profiles.md`). Classification is *"audited metadata, not a gate; flag only genuine ambiguity"* (D16/D21). Discovery reads run through the `paper_search` MCP with `web` **disabled** (ADR-32) — *"the Librarian now makes no direct API calls"* (`config.yaml`) — because the deterministic ingest pipeline (ADR-30) owns the mechanical half and the agent can't `code_execution`.

**The Writer — generative, draft-only.** **What:** one lane, `draft`; drafts land in `projects/` scratch, *"never directly in `notes/claims/` or any deliverable zone"*; every factual sentence binds to a citekey (*"If you cannot cite it, you cannot write it"*); **no self-verification** and **no new claims** (`memoria-writer/SOUL.md`). **Why draft-only + no self-check:** *"A draft is raw material, never a deliverable"* and fact-checking its own output is *"the Peer-reviewer's lane, kept independent on purpose (separation of duties)."*

**The Peer-reviewer — skeptical, deliberately independent.** **What:** one lane, `verify`; judgment checks (citekey resolution, claim→source tracing, near-tie prep) plus the conceptual red-team; *"flag, don't fix"*; writes only `inbox/`; its `clean` *"never substitutes for the PI's approval"* (ADR-50) (`memoria-peer-reviewer/SOUL.md`). **Why never merged into the Librarian** (the one consolidation refused *on principle*): *"The agent that gathers and synthesizes must not also grade the result — separation of duties is the anti-rubber-stamp principle. A checker that inherits the proposer's faithful stance waves through exactly what the gate exists to catch"* (`why-specialist-profiles.md`). **Why judgment only:** *"The deterministic sweeps (retraction, dedup, broken-citation) are engines, not you — you bring judgment where determinism ends."*

**The Engineer — delegating.** **What:** one lane, `code`; a *"documentary front for an external coding agent"* — it *"does not write code yourself"*, scaffolds the handoff into `projects/<project>/code/` through the gated obsidian MCP, records provenance, and owns per-task commit/revert (`memoria-engineer/SOUL.md`; `docs/explanation/profiles/engineer.md`). Like every profile it is **MCP-only** — no terminal, file, or code_execution. **Why:** *"Memoria doesn't compete with coding agents — it connects to them … reimplementing them inside Memoria would produce a worse copy"* (same thin-front logic as ADR-22). ADR-21 *"retired the old Coder-lane execution exception"* — the `config.yaml` comment records the history verbatim: *"The v0.1.0-alpha.1 Coder kept terminal+file (ADR-27 §4); the Engineer does not."* **Why per-task commits:** *"one card, one commit, one diff to review … keeps revert scope small."*

**Delegation posture (the ranked axis).** **What:** agents differ in how much *support* work they may hand to a child/external agent — *"never the role's defining judgment."* Ranked widest→narrowest: **Engineer** (widest — the substantive coding *is* an external handoff by design), **Writer** (facts/cleanup; synthesis stays local), **Librarian** (narrow enrichment/lookups), **Peer-reviewer** (very low — *"delegation weakens independence"*), **co-PI** (none — read-only) (`docs/explanation/profiles/delegation-posture.md`). **Why the co-PI is at the bottom despite delegating *everything*:** *"routing a write to a board lane is the system's front door, not a subtask spawn — the card lands under another lane's ceiling and the PI's gate, never under the co-PI's own authority."* The invariant across all five: *"propose-not-dispose … Delegation can move work around; it can never move a decision past the gate."*

**The bounded rule.** All five agents **propose**; the **PI disposes**. Promotions, the `retracted` decision, and gated-zone writes are PI-only, enforced by the policy MCP (`README.md`). No Orchestrator (*"routing lives in `delegate:route-task` and the board's dispatch rules — auditable mechanism, not a reasoning agent"*) and no LLM Reviewer (*"an LLM reviewer … converts a structural gate into a probabilistic one"*) (`why-specialist-profiles.md`).

---

#### 4. The SOUL.md model — shared layer + unique layer

**What:** each agent = a **shared layer** (`AGENTS.md`, one copy in the vault root — *"the one 'how we work in this vault' instruction set every agent reads"*) plus a **unique layer** (`SOUL.md` posture, `skills/`, `config.yaml`, MCP wiring, packaged by `distribution.yaml`) (D46; `docs/explanation/deployment/distribution-model.md`; every `SOUL.md` closes with *"Shared house rules: the vault-root `AGENTS.md`."*). `SOUL.md` files are short and posture-first — mission, posture, boundaries, write-zones, discipline — not policy dumps.

**Why the shared/unique split:** it structurally kills the old failure mode — *"seven near-identical SOUL files duplicating common policy by hand"* — by giving *"common content one home (`AGENTS.md`), and what remains per-profile is genuinely per-profile"* (`distribution-model.md`). This is precisely why the **profile compiler was rejected**: **ADR-42** proposed a build step to generate shared SOUL sections from a common base to reduce *inter-profile drift*, but it is `superseded_by: [48]` because *"the shared AGENTS.md layer + unique SOUL/skills/config removes the drift problem the compiler addressed."* **What/Why (compiler deferred, then obviated):** the standing answer was *"at seven-profile scale the shared content is small enough to keep in lockstep by hand"*, held *"until inter-profile drift is a felt, recurring bug"* (ADR-42 Alternatives) — then ADR-46/48 moved shared content into `AGENTS.md` so there was nothing left to compile. `distribution-model.md` confirms: *"At five profiles, hand-authoring the unique layers stays cheap, and a profile compiler remains unnecessary."*

---

#### 5. config.yaml / distribution.yaml

**config.yaml — Hermes reads it, per profile.** **What:** holds `model` (provider `kilocode`, gateway `https://api.kilo.ai/api/gateway`), `mcp_servers` (policy + obsidian always; plus lane-specific ingest/cluster/patterns/paper_search/pyzotero/qmd/tasks), `agent.disabled_toolsets`, `terminal.cwd`, `checkpoints`, and `plugins.enabled: [memoria-policy-gate]`. The installer substitutes `{{PYTHON}}`, `{{VAULT_PATH}}`, `{{QMD}}` at deploy. **Why each MCP server is present rather than a direct capability:** *"agents reach the vault, engines, and APIs ONLY through MCP — no exceptions"* (D40; `memoria-engineer/config.yaml`). Concretely: the Librarian gets `paper_search` (discovery) + `ingest` (the deterministic pipeline it *"can't exec scripts"* to run) + `pyzotero` (read-only Zotero) + `qmd` (local hybrid BM25+vector search) + `cluster` + `patterns`; the co-PI gets `tasks` (its sole write path) and read/compute facades (`ingest`, `cluster`) but *"its lane-override has write_scope: [] so any write attempt is denied by the gate."* The obsidian MCP runs over **plain HTTP on loopback** because *"Hermes can't skip TLS verify for the self-signed HTTPS port"*, and the port lives in `OBSIDIAN_MCP_PORT` so *"a sandbox + a production vault can serve different ports and coexist"* (ADR-31).

**distribution.yaml — the Hermes profile manifest.** **What:** read by `hermes profile install`; declares `name`, `version: 0.1.0-alpha.2`, `hermes_requires: ">=0.12.0"`, and `env_requires` (which Hermes writes out as `.env.EXAMPLE`). **Why the env split matters:** the shipped provider is `kilocode` (`KILOCODE_API_KEY` required), so `ANTHROPIC_API_KEY` is `required: false` — *"unused by the shipped kilocode config."* The co-PI's `OBSIDIAN_API_KEY` note is explicit that it is *"read tools only; the copi lane denies all writes"* — the manifest itself documents the read-only wall. The Librarian's manifest carries the full scholarly-API key set (OpenAlex now *required* — *"As of 2026-02 OpenAlex requires a key"* — S2, NCBI) because *its* engines make the enrichment calls. **Why keys are seeded per-profile:** *"Hermes reads per-profile `.env` only — there is no global inheritance … The installer must seed shared keys into each profile `.env`"* (ADR-27 Finding 6).

---

#### 6. Skills (SKILL.md) and skill governance

**What:** a skill is a `SKILL.md` with YAML frontmatter — `name`, `description`, `version`, `platforms`, and a `metadata.memoria` block declaring `skill_id` (colon form, e.g. `catalog:find-source`), `profile`, `lane`, `mcp_tools`, `write_scope`, and `outputs`. The body is procedure. Example: `catalog:find-source` declares `lane: catalog`, `write_scope: ["inbox/", "notes/fleeting/"]`, `outputs: [candidate, fleeting]`, and `mcp_tools` limited to the `paper_search.search_*` tools + gated obsidian + `policy.check_permission/complete_write`. The co-PI's `delegate:route-task` declares `write_scope: []` and its only write tool is `tasks.delegate_route_task` — *"The co-PI's only write path — and it writes a board card, never the vault."*

**Why skills attach per-lane, not per-agent:** the design axiom is *"a profile is a posture; skills attach per lane"* — postures are stable, skills are the swappable capability layer, and the same technique can recur across agents (embedding similarity drives the Librarian's mapping, the Peer-reviewer's dedup, and the intake brief). Memoria *"takes the duplication on purpose — a shared capability-agent would need the union of every caller's access, dissolving the per-lane write boundaries"*; the reconciliation is *"capability lives in engines and shared MCP servers … the agents stay posture-pure"* (`why-specialist-profiles.md`). The `delegate:route-task` header even carries a legacy-name shim (*"legacy name: `delegate-task`; load on disk as `delegate-route-task`"*), evidence of the rename churn from the consolidation.

**Skill governance — dashboard, not lifecycle (ADR-43).** **What:** at 25 skills across five profiles (threshold >15) Memoria shipped a **read-only `skill-lifecycle` dashboard** (`system/dashboards/skill-lifecycle.md`) that renders lane policy vs. shipped skills, and **rejected** the full lifecycle state machine, `system/skills/` governance notes, and onboarding checklist. **Why:** *"The signal that fired was skill count, and what count breaks is visibility, which the dashboard restores. The lifecycle machinery answers a different problem — coordinating graduations and approvals — that has not occurred (zero passthrough-to-dedicated graduations to date) and that the single-researcher scope (ADR-24) makes structurally unlikely: with one human approver there is no hand-off an `intake → … → approved` pipeline would mediate."* The **runtime mechanism is the system of record**: lane-override files (`policy.allow.skills`/`deny.skills`) + the per-profile `skills/` folders *are* skill governance; the dashboard *"reads the live files, not a generated snapshot,"* so it *"cannot drift."* Skill *history* lives only in git — *"acceptable at n=1 operator."* A related idea, **cross-run skill-insights memory** (ADR-35, the MetaClaw/CORAL pattern), is **deferred** because *"low payoff until the corpus is dense enough that cross-project patterns actually recur"* — *"too much architecture for a single-user vault at current density."*

---

#### 7. The agent-client pane / ACP

**What:** the `agent-client` Obsidian plugin implements **ACP (Agent Client Protocol)** as a chat pane hosting **exactly one agent — the co-PI**. There is *no profile picker to manage*; the specialists are board lanes, not conversation partners. The pane is pinned in the right sidebar of all three shipped workspaces (Desk/Library/Studio, ADR-68) and keeps its session across workspace switches. Sessions auto-export on close to `notes/fleeting/chats/` (`chat_*`), where the sweeps cron stamps them as `type: fleeting, origin: chat` within 15 minutes (`docs/explanation/obsidian/agent-client-picker.md`; `docs/how-to-guides/using-obsidian/use-the-acp-pane.md`).

**Why a conversational pane exists at all** (alongside the board): *"the board is for work that produces a reviewable artifact; the pane is for thinking that produces a clearer human."* Exploratory work — *"thinking a paper through … sketching a counter-outline"* — *"would produce cards that never cleanly close, because the 'output' lives in the human's understanding, not in a file."*

**Why one agent, not a picker** (the design change from the seven-profile era): *"An earlier design put four ACP-suitable profiles behind a picker (Socratic, Mapper, Writer, Verifier) and cleared the conversation on every switch, so that one specialist's context couldn't bleed into another's permission contract. ADR-48 retired that design."* The consolidation *"dissolves the problem the picker existed to manage"* on two fronts: (1) *"With one agent in the pane there is no contract boundary to police mid-conversation — the co-PI holds a single, hard contract (read-only …), so no exchange can talk it into a write it isn't allowed"*; and (2) *"because there is no switch, the conversation persists — and a persisting conversation is exactly what the co-PI's memory loop needs to compound."* What the picker's separation protected *"now lives where it belongs — on the board … The boundary between specialists is physical (separate dispatched processes with separate permissions), not a UI affordance the human must operate correctly."* The pane writes nothing canonical because the co-PI is structurally read-only; anything durable is *"written through the normal gated path afterward."* An "assist surface" of verb-shaped quick entry points (Find/Search/Patterns/Ask/Draft/Explore) is **designed but deferred** ([#380](https://github.com/eranroseman/memoria-vault/issues/380)).

---

#### 8. The superseded seven-specialist model (accounting for the premise)

The five-profile design is best understood as the *resolution* of the earlier seven, so the governing decisions are worth stating with their rationale.

**ADR-02 — seven specialists over one generalist** (`status: superseded, superseded_by: [48]`). **What:** the original roster was *"Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter — each with a focused mission, narrow folder permissions, the skills it actually needs, and a clear exit condition. There is no Orchestrator profile and no Reviewer profile."* **Why seven, not one generalist** (the part that *survives* into the five): *"Quality responsibility is traceable"* (a bad paper note is a Librarian problem, a bad trace a Verifier problem); *"Permission enforcement is practical"* (a generalist's write scope is *"the superset of all tasks"*); and *"Optimistic and conservative stances must be structurally separated"* (Librarian proposes generously, Verifier checks conservatively — *"an agent that does both must switch internally; there is no structural guarantee it does"*). **Why no Orchestrator / no Reviewer:** *"routing encoded in rules is auditable; routing decided by a reasoning agent is not"*, and *"LLM-based reviewers are confidently wrong on exactly the outputs the gate needs to catch — hallucinated citations are emitted with high fluency and high confidence."* These two exclusions carried *unchanged* into the five-profile design.

**ADR-48 — the consolidation to five** (`supersedes: [2, 37, 42]`). **What:** *"The PI converses with one agent — the co-PI — and delegates everything else,"* and the seven collapse by posture. **Why the seven were over-divided:** *"Under 'profile = posture, skills attach per lane' several profiles shared one stance."* The exact mapping (`why-specialist-profiles.md`):
- **Librarian + Mapper → Librarian** — *"both faithful … one research-librarian stance pointed in two directions."*
- **Socratic → co-PI** — *"the conversational stance with the write-wall … so it folded in."*
- **Verifier → Peer-reviewer + engines** — *"its judgment checks became the Peer-reviewer; its deterministic sweeps became engines."*
- **Linter → engine** (the "7th" the premise couldn't name) — *"never an agent at all — zero-LLM, reproducible, cron-run: an engine by definition."*
- **Coder → Engineer** — *"kept its boundary and became the Engineer."*

The two forcing pressures were a **UX failure** (*"Seven specialists created a real UX failure: who do I talk to? Every profile was a possible conversation, so no conversation compounded"*) and a **fragmented learning loop** (*"the self-improving loop … only compounds in an agent that has every conversation. Split across seven, each got a sliver of context and none grew"*). ADR-48 also records that scope was expanded mid-build: *"the original plan shipped only co-PI + Librarian … the PI expanded the scope mid-build — 2026-06-09 — so Writer, Peer-reviewer, and Engineer landed in v0.1.0-alpha.2 as well."*

**ADR-37 — retriever-scout** (`status: superseded, superseded_by: [48]`). **What:** a *proposed* split of the Librarian into **Retriever** (broad discovery/candidate generation) and **Librarian** (ingest/enrichment/classification). **Why proposed:** *"At high discovery volume, one profile doing both `find` and `ingest` may have its classifier and its discovery scorer competing for the same compute and context."* **Why rejected/never shipped:** *"one more profile with no current bottleneck to motivate it"* — and ADR-48's note makes the disposition explicit: *"one Librarian posture spans catalog·extract·link·map, find included."* It was to be revisited only if *"discovery volume genuinely overwhelms the unified Librarian"* (e.g. the nightly discovery loop at scale). So retriever-scout is neither one of the ADR-02 seven nor one of the shipped five — it is a *would-be eighth* that the consolidation folded back into the Librarian's `catalog` lane.

**Install-time consequence.** The idempotent profile installer *"prunes stale `memoria-*` profiles that are no longer shipped (the v0.1.0-alpha.1 seven-profile set)"* on every `git pull` (`distribution-model.md`) — the design deliberately garbage-collects the old seven from any machine that once had them, so the five-profile roster is the enforced runtime state, not just the documented one.

---

**Key evidence files (all at `0e9ed9dd`):** `src/.memoria/profiles/{memoria-copi,memoria-librarian,memoria-writer,memoria-peer-reviewer,memoria-engineer}/{SOUL.md,config.yaml,distribution.yaml,skills/*/SKILL.md}`; `AGENTS.md` (vault root, shared layer); `docs/adr/{02,22,27,28-ref,35,37,42,43,48}-*.md`; `docs/explanation/profiles/{README,co-pi,engineer,delegation-posture,librarian,peer-reviewer,writer}.md`; `docs/explanation/rationale/{why-hermes,why-specialist-profiles}.md`; `docs/explanation/obsidian/agent-client-picker.md`; `docs/how-to-guides/using-obsidian/use-the-acp-pane.md`; `docs/explanation/deployment/distribution-model.md`.

### Write gate, policy engine, provenance & audit

At alpha.1 (commit `0e9ed9dd`) this subsystem is Memoria's trust spine: the one place where "a human approved this" and "an agent wrote that" become structural facts on disk rather than conventions in a prompt. It has five moving parts — a **pure decision engine** (`policy_mcp.py`), a **fail-closed enforcement bridge** (the `memoria-policy-gate` Hermes plugin reusing `policy_hook.py`), a **structural human review gate** (ADR-03), an **append-only hash-paired audit log** plus per-session digests (ADR-25), and a **zero-LLM structural linter** that closes the loop by detecting drift (`detectors.py`). The readiness review's own scorecard lists "Write gate + policy engine (deny / dry_run / fail-closed)" as **self-tested + live-validated** and the obsidian MCP write-bridge as **approved (live write confirmed)** (`docs/releasing/0.1.0-alpha.1/release-readiness-review-2026-06-03.md`, rows 30–31).

#### The policy engine — a pure decision core with four decisions

**What:** `src/.memoria/mcp/policy_mcp.py` is the runtime write-gate. Every vault action is one of eight guarded verbs — `read`, `write`, `append`, `move`, `delete`, `mkdir`, `auto_fix`, `report` (`ACTIONS`), of which six are `MUTATING_ACTIONS`. Each request resolves to exactly one of four decisions: `allow`, `allow_with_log`, `deny`, `dry_run` (the `Decision` dataclass; contract in `docs/reference/policy-mcp.md`). The design deliberately splits a **dependency-light, unit-testable core** (the `decide()` pure function, the glob→regex matcher, SHA-256 hashing, the JSONL audit append) from a **thin MCP-server wrapper** — the docstring states the core "runs and self-tests without the MCP SDK or even PyYAML installed, so the enforcement logic is verifiable in isolation." A one-shot `--decide '<json>'` CLI form is the documented debugging entry point.

**Why:** The gate is the load-bearing safety property, so its logic must be verifiable without a running agent, an MCP transport, or even YAML. `policy_mcp.py`'s header states this mirrors `detectors.py`'s deliberate "pure core + thin wrapper" shape; the alternative — logic entangled with the MCP SDK — would make the single most security-critical component the hardest to test. The four-decision vocabulary exists because a binary allow/deny cannot express the two things Memoria needs beyond blocking: *"proceed but you must be audited"* (`allow_with_log`) and *"I will not perform this, but tell the human"* (`dry_run`, the structural review gate's mechanism).

**What (precedence):** `decide()` evaluates a fixed precedence ladder (documented verbatim in its docstring): (1) invalid action → deny; (2) a loaded skill's `deny.write` → deny (one-way narrowing, checked before everything but action validity); (3) `report` → allow within lane; (4) `read` → default-allow, `allow_with_log` in review-gated zones, explicit `deny.read` wins; (5) `auto_fix` → Linter class-gating; (6) `delete` → deny unless `flags.explicit_authorization` and within write scope; (7) `mkdir` → allow within `routing.write_scope`; (8) `write`/`append`/`move` → `deny.write` wins, else `allow.write` → `allow_with_log`, else **default-deny**.

**Why default-deny + audit-every-mutating-allow:** The bottom of the ladder is default-deny ("no rule matched at all") because a permission system that defaults open is not a boundary. A code comment records a real correction: a bare `allow` "used to skip the audit for lanes without `require:audit_log`, leaving writes with no `before_hash` to pair against `write_complete` — so the audit chain had holes. `allow_with_log` closes them." That is: every mutating allow is forced to be audited, otherwise the reversibility guarantee (below) has silent gaps.

#### Lane-overrides — versioned, per-profile policy manifests

**What:** Each profile's ceiling lives in a versioned YAML file under `.memoria/lane-overrides/` (`writer.yaml`, `copi.yaml`, `librarian.yaml`, `peer-reviewer.yaml`, `engineer.yaml`). `parse_lane()`/`LanePolicy` model `policy.allow.{skills,write,read,auto_fix.classes}`, `policy.deny.*`, `policy.require` (every shipped lane sets `audit_log`), and `routing.{invocation,external_api_policy,write_scope}`. `policy.deny` wins over `policy.allow`; unmatched paths are default-denied. Globs use doublestar semantics implemented by `glob_to_regex()` (`**` crosses `/`, `*` stays within a segment, `?` one non-`/` char). The Writer's lane, e.g., allows `write: ["projects/**"]` and explicitly denies `notes/claims/**`, `notes/hubs/**`, `catalog/**`, `inbox/**`, `system/**`. The **co-PI is the limiting case**: `allow.write: []` plus `deny.write: "**"` — "the hard write-denial is the structural guarantee behind 'read directly, delegate writes'" (`copi.yaml`).

**Why:** The reference doc names what the gate is *not*: "not a substitute for the review gate, not a content checker, and not a hidden controller. Every rule lives in a versioned lane-override file." Keeping policy in versioned files (not code, not prompts) makes the ceiling auditable, diffable, and debuggable — the doc's stance is that "an unexpected deny is a Memoria-side question — check the lane-override YAML for what the rule says, then the policy MCP's audit log for the actual decision." One consequence the doc calls out: every shipped lane denies `system/**`, so no profile can mutate `system/templates/` through the gate for any action — the boundary is uniform, not per-verb.

#### Two structural overrides that no lane can relax

**What (review-gated zones → dry_run):** `REVIEW_GATED_PREFIXES = ("notes/claims/", "notes/hubs/")` (loaded canonically from `.memoria/schemas/folders.yaml` `gated_prefixes` via `load_gated_prefixes()`, with the hardcoded tuple as a test-enforced dependency-free fallback). Any otherwise-allowed *mutating* action targeting these prefixes degrades to `dry_run` with `policy_rule: review_gated.dry_run` — "review-gated zone write requires approval — surface as board comment." This applies to `write`/`append`/`move`, and to `delete`/`mkdir`/`auto_fix` in those zones, **regardless of the lane's `policy.allow`**.

**Why:** This is ADR-03 made concrete. Canonical zones "must only receive content that a human has reviewed and approved… A profile that 'decides' to canonize directly cannot, because the file-system call returns before content reaches disk" (ADR-03). The rationale is the specific failure mode in `why-human-gate.md`: "hallucinated citations and fabricated claims are emitted with high fluency and high confidence. An advisory gate that fires on low-confidence outputs would wave through exactly the outputs the gate exists to catch. The gate must be unconditional — it cannot be confidence-routed." ADR-03 rejects three alternatives explicitly: prompt-based rules ("mean time to failure… degrade at long context"), an advisory LLM reviewer ("confidently wrong on exactly the inputs the gate needs to catch"), and confidence-routed gating (SmartPause). The dry_run/board-comment path preserves the agent's work product without letting it reach canonical.

**What (auto_fix class gate):** `auto_fix` is gated on `flags.class`. Only `{safe-and-unambiguous, authorized-targeted}` may proceed (as `allow_with_log`, and only within the lane's write scope); `schema-content` is pinned to `dry_run` always; `review-gated-edit` to `deny` always — "regardless of who asks" (`AUTO_FIX_*_CLASSES` constants, `docs/reference/policy-mcp.md#auto-fix-policy`).

**Why:** Auto-fix is the one path where an engine mutates notes without a fresh human decision, so it needs a categorical ceiling independent of lane config: mechanical fixes (whitespace) are safe; a field rename is a schema migration that needs its own tool (`lint:migrate-schema`) → `dry_run`; any write to a gated zone is a canonical edit → `deny`. At alpha.1/alpha.2 the shipped Linter engine is report-only, so the class gate is "the gate exists for any future fixer, including `golden.py restore --apply`" (`docs/reference/linter.md`).

#### Fail-closed enforcement: from shell hook (ADR-27) to Python plugin (ADR-28)

**What:** `check_permission` only *decides*; the component that actually *stops* a write is the **`memoria-policy-gate` Hermes Python plugin** (`src/.memoria/plugins/memoria-policy-gate/__init__.py`), deployed per profile by the installer with `{{PROFILE}}`/`{{VAULT_PATH}}` substituted. It registers `pre_tool_call` (`_gate`) and `post_tool_call` (`_complete`) and reuses the tested core verbatim via `policy_hook.evaluate_pre`/`evaluate_post` → `policy_mcp.PolicyEngine` — "no policy logic lives here." `_gate` returns `{"action":"block", …}` on `deny`/`dry_run`, and **any exception inside the gate also returns block** (fail-closed).

**Why (the whole ADR-27 → ADR-28 arc):** This is the most important reasoning in the subsystem, and it was forced by a live failure. ADR-27 originally concluded the gate would enforce via a `pre_tool_call` **shell hook** with `matcher: "obsidian.*"` once MCP servers moved into `config.yaml` and a toolset allowlist made obsidian the only write path. But a real live re-run (Hermes v0.14.0, `hermes -z`, against `Memoria-test`) found "the gate **never fires**: a write to a review-gated zone succeeded, ungated and unaudited" (ADR-28 Context). Three converging causes:
1. **Tool-name/matcher mismatch** — Hermes registers MCP tools as `mcp_<server>_<tool>`, so the obsidian write is `mcp_obsidian_obsidian_append_content`; the shell-hook's `re.fullmatch("obsidian.*", …)` returns `None`. The earlier "passing" test used a fabricated name.
2. **Shell hooks are consent-gated** — skipped on non-TTY runs (cron, headless `-z`) unless allowlisted.
3. **Shell hooks are fail-OPEN by construction** — "A gate that proceeds on its own failure is not a gate."

ADR-28's decision table shows the Python plugin is "the only option that is both fail-closed *and* solves `task_id` provenance for free" — it runs in-process in every mode (no consent), matches in Python (so the real `mcp_obsidian_*` name is caught), and receives the `task_id` the MCP-wrapper alternative could not. ADR-28 is a **partial supersession**: it replaces only ADR-27's *enforcement mechanism*; ADR-27's config-model decisions (`mcp_servers` in `config.yaml`, the `agent.disabled_toolsets` allowlist computed as `all_toolsets − lane_allowlist`, obsidian as the only write path) all stand, "because they are what make a single gated path sufficient." The plugin's one residual weakness — "if the plugin fails to load there is no gate" — is bounded by `plugins.enabled` and backstopped by the capability layer. ADR-28's validation section records a deliberately adversarial test: with `policy_mcp.py` moved aside, an otherwise-allowed write is **blocked** (fail-closed), "where the shell hook would have failed open."

#### The obsidian MCP write-bridge and the MCP-only sandbox

**What:** `policy_hook.py` maps obsidian MCP tool names to policy actions via **substring** matching on `WRITE_KEYWORDS` (`append`→append, `patch/put/create/write`→write, `delete`→delete, `rename/move`→move) so it survives Hermes' server prefixing. Read tools (get/list/search) contain none of those keywords → not gated (`classify()` returns `None`). Beyond path-gating obsidian writes, the hook **hard-denies** two families for *every* lane: `DENY_OBSIDIAN = (command_execute, vault_delete, vault_move)` and `DENY_DIRECT_TOOLS` (the `file`/`terminal`/`code_execution` families — `write_file`, `patch`, `terminal`, `run_command`, `code_execution`, …). `to_vault_relative()` normalizes tool-supplied paths, returning `None` (proceed, ungated) for absolute paths outside the vault since "the gate governs vault zones only."

**Why:** The sandbox model is "policy-via-MCP, MCP-only (D40/ADR-46): agents reach the vault, engines, and external APIs ONLY through MCP servers" (`policy_hook.py` docstring). No Memoria profile ships the `file`/`terminal` toolsets (`agent.disabled_toolsets`), so a call reaching the hook from those families "means config drift (e.g. a Hermes update adding a toolset the denylist doesn't know), so the gate fails closed rather than trusting the capability layer. The capability layer is the first wall; this hook is the second, in-process one." `command_execute` is hard-denied because it "runs an arbitrary Obsidian command and has no single path to gate"; `vault_delete`/`vault_move` are denied as least-privilege (the workflows don't need them). The path-`None`-outside-vault choice is scoped intent: the Engineer committing to a repo outside the vault "is not this hook's concern."

**What (fail-open limitation, documented):** `policy_hook.py`'s docstring is candid that **Hermes fails open on hook errors** at the Hermes layer — "this gate cannot be truly fail-closed at the Hermes layer. It fails closed on its own decisions… which is the strongest guarantee a hook can give." An unresolvable write (missing profile/path/task_id, or a policy import failure) is blocked. **Why:** honesty about the residual — ADR-25 restates it: "Enforcement is best-effort, not fail-closed… the pairing catches tampering after the fact rather than preventing it." This is why the audit trail's *detective* guarantees (below) matter: they backstop a preventive layer that cannot be perfect.

#### SHA-256 hashing and reversibility (`before_hash` / `after_hash`)

**What:** On an allowed mutating action, `PolicyEngine.check()` computes `before_hash = sha256_file(path)` and returns it; the pre-decision audit entry carries `before_hash` with `after_hash: null`. After the write lands, `complete_write()` computes `after_hash` and appends a **separate `write_complete` record** matched to the decision by `task_id` + `path`. A missing file hashes as the empty-byte SHA-256 (`EMPTY_SHA256`), never null; a **hash read-error denies the request** ("no hash, no allow"). `complete_write()` also re-derives the expected `before_hash` from the prior audit record and, if the caller's supplied value disagrees, records `hash_mismatch: true` + `expected_before_hash` — "the caller-supplied hash is not trusted silently."

**Why:** The design chose **per-write hash pairing, not a cross-entry hash chain** (`docs/reference/policy-mcp.md`, ADR-25). ADR-25 explains: pairing "pins one write's before/after state and nothing more — it does not hash-link successive entries," which keeps the log a set of independent, reversible records that a single forward walk can verify. `write_complete` is deliberately "a record kind, not a value of the `decision` enum" — the four decisions stay exactly `allow`/`allow_with_log`/`deny`/`dry_run`. The MCP computes hashes (workers never supply them) so the trail cannot be spoofed by the actor it audits. A code comment flags the open question of whether the MCP should *front* the write to make hashing atomic — at alpha.1 `check_permission` is advisory, so `complete_write` captures the after-state post-hoc.

#### The human review gate as first-class state

**What:** The board card's `review_status` is a state machine — `unreviewed` → `requested` (worker done, human's turn) → `approved` / `rejected` — and is "the authoritative state of human approval — not comments, tags, or conversations" (ADR-03, `why-human-gate.md`). `board_export.py` projects these transitions into `system/logs/board-transitions.jsonl` and `disposition.jsonl` (accept | edit | reject, marked **un-backfillable**), and writes one review prompt per card reaching `done`. A WIP cap on `done-awaiting-review` creates back-pressure that slows new card creation when the queue fills (ADR-03 Consequences). Crucially, the **agent verdict is separated from the review**: engines/Peer-reviewer attach `metadata.agent_recommendation`, which "informs; it never replaces" the human decision (`why-human-gate.md`).

**Why:** Review is modeled as structured data, not conversation, so it is queryable — "which cards are awaiting review?" — and enforceable via WIP caps: "'The human reviewed this' must be a field, not a convention" (`why-human-gate.md`). The agent-verdict separation exists because "a clean Peer-reviewer report doesn't mean the draft is good; it means the citations trace and the schema is valid" — collapsing the two would reintroduce the correlated-error failure the structural gate was built to defeat. The bottleneck is intentional: "A system that can autonomously populate the synthesis zone without human attention has removed the epistemic guarantee that makes the vault trustworthy" (ADR-03). The disposition log is un-backfillable because accept/edit/reject can only be observed at the moment of the human decision — ADR-25 makes the same point that "the audit and session record cannot be reconstructed retroactively."

#### Session logging & audit — two logs, one writer each (ADR-25)

**What:** Two distinct logs live in `system/logs/`:
- **`audit.jsonl`** — written by the policy gate, **append-only forever, never rotated**, hash-paired per write. Fields: `timestamp`, `profile`, `action`, `path`, `task_id`, `decision`, `policy_rule`, optional `reason`, `before_hash`/`after_hash` (`docs/reference/policy-mcp.md`). Every `deny`/`dry_run`/`allow_with_log` is always logged; path-traversal attempts are audited with the *raw* path via `_audit_traversal()` because "a traversal attempt is the request most worth logging."
- **`sessions/YYYY-MM-DD-HHMM.jsonl`** — written by the Linter's `session_summary.py` on the daily cron: a **deterministic digest** (header of task/profiles/counts + one record per touched path), idempotent, only digesting sessions quiet ≥24h.

**Why (never rotated):** ADR-25 rejects weekly rotation ("[#393]"): at single-researcher write volume (ADR-24) rotation "would force every full-history consumer — the `write_complete` pairing reads, the `vault-hash-drift` walk, the session digests — to stitch across rotated files, for no benefit. Append-only forever keeps one walk = the whole history"; growth is surfaced, not silenced, by the Linter's 50 MB `audit-log-size` advisory. **Why two logs:** they answer opposite questions for opposite readers — audit is forensic ("did this write happen and was it authorized?"), digests are narrative ("what did the session accomplish?"). ADR-25 rejects one combined log: "A single log is either too verbose to verify (audit polluted with narrative) or too noisy to read." **Why a deterministic digest, not an LLM narrative:** "the Linter is a zero-LLM engine (ADR-49), and a digest derived deterministically from the audit trail is reproducible, auditable, and free." Per-session file naming by minute makes the digests multi-machine-safe without collision (ADR-24). The audit-log dashboard adds a security reading: "a sudden rise in policy MCP denials can indicate an injection attempt coaxing an agent toward unauthorized writes" — Memoria ingests untrusted PDFs, an indirect-prompt-injection surface (`docs/explanation/dashboards/operational-health/audit-log.md`).

#### Provenance — at three grains

**What (write provenance):** Every audited write pins *who* (`profile`), *under what authority* (`policy_rule`), *for which unit of work* (`task_id`, required on every request — "delegated children share summaries, not live state, so identity must travel with every request"), and *what changed* (`before_hash`/`after_hash`). A missing `task_id` is itself denied (`request.no-task-id`) — though, unlike a path-traversal deny, it is not audited (the check returns before any audit append).

**What (content provenance):** Lane `policy.require` carries `source_tracking` (e.g. `librarian.yaml`), and the design's borrowed pattern is a **claim-to-evidence chain by construction** — "every claim traces through a recorded evidence chain to a grounding source" (`why-pattern-provenance.md`, citing ScientistOne's 0/337 hallucinated references vs. baselines up to 21%). Typed relations `supports`/`contradicts` are active for claim-tracing; `sources` citekeys are bibliographic (checked by the sweeps, not the frontmatter-link detector).

**What (pattern provenance):** `why-pattern-provenance.md` is the design-lineage ledger for the ~47 surveyed AI-research systems, sorted into **Borrow / Adapt / Reference / Ignore**. Its governing discipline: "the mechanic is borrowed but the autonomy posture is narrowed: Memoria refuses the scalar-metric keep/revert loop that most of these systems layer on top." **Why this matters to the gate:** the Ignore column is the intellectual justification for the structural gate — it explicitly refuses "Confidence-routed bypass of the human gate" (AutoResearchClaw SmartPause), the "Co-trained generator + reviewer loop" (CycleResearcher — "metric and objective collapse"), "Preference internalization into model weights" (NanoResearch — "once preferences live in weights they are no longer inspectable, auditable, or revertible"), and the tournament/evolution loop. The FAMA-exposure detector (below) operationalizes a borrow recorded in **ADR-10** (Memora's FAMA metric, which penalizes "reuse of obsolete memory") as a deterministic check — it is not an entry in this pattern-provenance ledger, whose Borrow column does not list it. Memoria's own differentiator over the surveyed MCP-native ecosystems is named as "MCP as a *permission / policy boundary*, not merely interoperability" — precisely the policy gate.

#### The structural linter & drift detection (`detectors.py`)

**What:** `src/.memoria/engines/linter/detectors.py` (782 lines) is the deterministic, zero-LLM, **report-only** detector suite — "gates at commit, monitors between" (`docs/reference/linter.md`). Its constants are schema-driven from `.memoria/schemas/` with hardcoded fallbacks. The audit/provenance-relevant detectors:
- **`vault-hash-drift` (CRITICAL)** — walks `audit.jsonl`, keeps the latest `write_complete` per path (append-only-forever means "one walk covers the full history"), compares each recorded `after_hash` to the current on-disk SHA-256. A mismatch means "the file was edited outside the audited write path… A legitimate human edit in Obsidian surfaces here too, by design." Deletes fall out naturally (empty-hash convention); a zero-byte file is a documented blind spot.
- **`audit-unpaired-writes` (MEDIUM)** — a mutating allow with no paired `write_complete` after 1h → "the reversibility chain has a hole."
- **`audit-log-size` (LOW)** — the 50 MB advisory for the never-rotated log.
- **`skeleton-drift` (MEDIUM)** — a folder from `folders.yaml` `skeleton` missing from an installed vault (keyed on the golden manifest's presence).
- **`fama-exposure` (HIGH)** — a downstream note wikilinking a *superseded* claim (`lifecycle: archived` or `superseded_by` set): "reuse of obsolete memory."

**What (pre-commit gate + golden copy):** The installer wires `precommit_check.py` into `.git/hooks/pre-commit` — schema-invalid typed notes **block the commit** (exit 1); `golden.py` stages a SHA-256-manifested canonical copy of every system file at `.memoria/golden/`, with `restore` propose-only by default (`--apply` writes bytes back).

**Why:** ADR-49 makes the Linter an *engine, not an agent* — deterministic and zero-LLM, so its findings are reproducible and free of the confident-hallucination risk the whole subsystem guards against. The detectors are the **detective backstop** to the gate's imperfect prevention: because Hermes fails open on hook errors (ADR-25), `vault-hash-drift` and `audit-unpaired-writes` catch tampering (or a legitimate out-of-band Obsidian edit) *after the fact* — "the finding means the trail no longer pins that file's state." The golden copy is "the human-facing half of template protection (#179): agents are already blocked by the lane ceilings… so the golden copy exists to catch and repair an *accidental human* edit or deletion of a system file" (`docs/reference/linter.md`). ADR-12 reinforces the single-authority principle from the other side: obsidian-linter is ruled **incompatible — do not install**, because "a deterministic tool still fails the architecture if it writes outside the Policy MCP / audit trail" — a second frontmatter authority would collide with the agent-written `_proposed_classification`/`_enrichment` namespaces and, worse, write to audited zones ungated.

#### Deferred: the pre-file similarity ratchet (ADR-38)

**What/Why:** A `qmd` similarity gate at the moment a synthesis note is filed — surfacing near-duplicate neighbours for the human to confirm/merge/override — is **deferred**. It is not refused: "nothing to dedup against on an early vault, and the threshold can't be tuned without real false-positive data." Notably it explicitly rejects an auto-merge-above-threshold design ("similarity is not identity… merging is a human judgement; the gate only *surfaces* candidates") and rejects a `--force` bypass ("the human's confirm/merge/override *is* the escape valve") — the same human-decides posture as the structural gate, applied to duplication.

---

**Source files (all at `0e9ed9dd`):** `src/.memoria/mcp/policy_mcp.py`, `policy_hook.py`, `board_export.py`, `metrics_aggregate.py`; `src/.memoria/plugins/memoria-policy-gate/{__init__.py,plugin.yaml}`; `src/.memoria/lane-overrides/{writer,copi}.yaml`; `src/.memoria/engines/linter/detectors.py`; `docs/reference/{policy-mcp,linter}.md`; `docs/adr/{03,12,25,27,28,38}-*.md`; `docs/explanation/rationale/{why-human-gate,why-pattern-provenance}.md`; `docs/explanation/architecture/session-logging.md`; `docs/explanation/dashboards/{operational-health/audit-log,structural-health/drift-watch}.md`; `docs/releasing/0.1.0-alpha.1/release-readiness-review-2026-06-03.md`.

### Pipeline, discovery, evaluation, distribution & the ADR landscape

> **Reading note — the commit is a terminology seam.** `0e9ed9dd` is the commit *"docs(releasing): split 0.1.0 → 0.1.0-alpha.1; add alpha.2 checkpoint plan (#452)"*. It is the exact point where the **frozen alpha.1 release record** (`docs/releasing/0.1.0-alpha.1/*`) still speaks of **seven profiles** (`librarian, mapper, socratic, writer, verifier, coder, linter`) and **numbered lifecycle folders** (`10-inbox/`, `20-sources/`, `99-system/`), while the surrounding `docs/adr/` and `docs/explanation/` trees have already been rewritten forward to the alpha.2 consolidation (five profiles, type-first `catalog/ notes/ projects/ inbox/ system/`, the engines-vs-agents split). Both release docs carry the banner *"Frozen record… terminology reflects that point in time and is not current"* (`docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1.md`). This section reconstructs the **alpha.1 design as those frozen release docs recorded it**, using the ADRs present at the commit as corroboration of the *why* — and flags each place where the ADR that would supersede it already exists in-tree.

The alpha.1 release bar itself was deliberately narrow. Both the release plan and the readiness review define "shippable" as **one loop, not seven agents**: *"a technical early-adopter can install Memoria and run ONE agent workflow end-to-end — through a real trigger, gated and audited, queued for human review — and watch it work"* (`release-readiness-review-2026-06-03.md`). Everything below is scoped by that bar: the pipeline is the *one valuable loop*; discovery, most evaluation, cross-vault, and multi-machine are consciously `deferred`-status ADRs that ship no code in alpha.1.

---

#### 1. Ingest / capture pipeline — the deterministic tiered spine (ADR-30)

**What.** Ingest is *one pipeline in three tiers* with two ordering invariants — **capture commits first** and **scriptable-before-LLM** — and **gated writes only** (`docs/adr/30-deterministic-ingest-pipeline.md`, "Decision"). The tiers:

- **Tier 0 — Guaranteed (local, must succeed).** No network, no PDF, no ML. A `capture-intake.jsonl` append-only log is written by QuickAdd *before* ingest is even invoked ("the true 'nothing lost' anchor"), then identity is resolved from the local `.memoria/memoria.bib`, the entry is **type-routed** (`paper-note` / `item-note` / book-chapter — because ~17% of the user's 867-entry corpus is non-paper), frontmatter is built, and a gated write lands the stub at `lifecycle: captured`.
- **Tier 1 — Standard (network, fallback-chained → *reliable*).** Each subsystem is a chain that degrades to Tier 0 only if *all* sources miss. Resolve/merge is **S2 + OpenAlex co-primary, Crossref for non-arXiv DOIs**, merged **per-field best-source-wins with provenance** (authors/ORCID/affiliations ← OpenAlex; intents/tldr/embedding ← S2; references = **union deduped by DOI**). Then conditional-by-ID enrichment (PMCID→PMC+MeSH, arXiv→full text, DOI→Crossref), a full-text chain (`S2ORC → CORE → PMC → arXiv → Unpaywall → local Zotero PDF → pymupdf4llm → OCR`, pre-extracted preferred), embedding-based tag suggestion over the user's own defined vocabulary, then **LLM call #1** — a **hard-schema-constrained classification proposal** that promotes `captured → proposed`, plus **ID-keyed idempotent linking** (find-or-create venue/person/org on ISSN/ORCID/ROR; no-ID entities recorded by name, never node-created).
- **Tier 2 — Optional (best-effort, absent-able).** The `[!brief]` comparative narrative (**LLM call #2**), an advisory NLI contradiction signal, and arXiv→code-repo cross-linking.

**Why.** The pre-existing `obsidian-paper-note` skill was *"fully LLM-orchestrated — costly, non-reproducible, and fragile"* for work that is *"overwhelmingly mechanical"*, and its PDF dependency `ocr-and-documents` literally *"currently fails to install"* (ADR-30 Context; the readiness review lists this same fragility as Risk 3). The three-tier shape is the direct answer to a hard requirement — *"nothing captured is ever lost; robustness by redundancy"* — arrived at through **two adversarial red-team rounds and an empirical spike on the user's 867-entry library**. The spike is load-bearing evidence, not decoration: it found the three metadata sources **disagree and are each incomplete** (reference counts of 151/129/146 for the same paper across S2/OpenAlex/Crossref; ORCID present in OpenAlex but ~0 in S2), which is *why* the merge is per-field-best-source rather than single-source-precedence. The single-source (S2-only) alternative was **rejected** precisely because "the spike showed each source is incomplete" (ADR-30 "Alternatives considered"). Splitting into two ADRs (spine + spike-gated enrichment) was rejected in favour of one three-tier ADR so "approving the whole [is] safe without a multi-step project."

Two design choices carry their own rationale:
- **What:** the deterministic spine is reached by the agent as an **MCP tool** (`ingest_pipeline`, `mcp/ingest_mcp.py`), not run as a script. **Why:** the Librarian's capability allowlist (ADR-27) *disables* `code_execution`/`terminal`/`file`, so a worker literally cannot run a script — the correction is recorded verbatim in ADR-30's header banner and "Correction" note. The agent fills only "the two judgment holes" (classify + brief) and writes through the gated obsidian MCP.
- **What:** re-ingest (even a manual command) is **enqueued as a board card**, never an ad-hoc `hermes` session. **Why:** find-or-create is idempotent only under **serialized writes**, and the WIP=1 invariant serializes only *board-dispatched* work — so routing through the board is the chosen per-citekey lock that stops a manual re-ingest racing the retry sweep (ADR-30 "Reliability, re-ingest, serialization").

**Status at the commit.** ADR-30 is `accepted` and marked *"Implemented and validated live (#100–#116)"*; the release plan's G10 gate records a real paper ingested end-to-end (`dispatch → ingest_pipeline MCP → S2+OpenAlex+Crossref merge → classify + [!brief] → gated multi-writes → review_status: requested`). Notably, the readiness review had listed the multi-source merge as **cut to "single-source-with-fallback"** for the first slice — but the release plan §5 records it was *"not cut after all… the S2 + OpenAlex + Crossref per-field best-source merge shipped, grounded by the 867-paper spike."* The alpha.2-era `docs/reference/ingest.md` present at this commit shows how the design was already being refined forward (a four-stage `pipeline.py`, a `calibration.yaml` **entity-resolution confidence floor of 0.85** that routes low-confidence merges to an Inbox `flag` card per ADR-56, and automated-not-gated classification per ADR-54).

---

#### 2. Retrieval, schema & the derived store

**What (shipped in alpha.1).** Retrieval is **deterministic search over the vault** — a Search engine (`qmd` embedding stack + the obsidian MCP), never a learned reranker (`docs/explanation/engines/README.md`). The schema contract is the 16 note-types and their frontmatter (release-plan appendix step: `fleeting/answer/paper/item/person/organization/venue/claim/moc/reference/project/code/canvas/draft/deliverable/candidate`), with **typed relations** `supports`/`contradicts` as first-class frontmatter (ADR-08) feeding the contradictions dashboard (ADR-09), and **claim supersession** as a relation (ADR-10). A **derived/extract store** lives *outside* the agent's write lane: `.memoria/data/extracts/<citekey>.md` with the paper note's `extract_path` pointing at it (`docs/reference/ingest.md`, "Derived artifacts").

**What (deferred — ADR-65).** Three retrieval/schema extensions are shape-settled but adopt-nothing-yet: **relation-vocabulary expansion** (`similar` first, then `cross-domain`/`uses-method`), **MASSW-aligned `_aspects`** (`key_idea`/`method`/`outcome`, agent-populated at ingest, figure-informed via Hermes `vision_analyze`), and **exploration-trace capture** (rejected directions recorded at project level).

**Why.** The extensions are deferred on an explicit cost/benefit argument: *"a half-populated typed field returns incomplete answers and erodes trust, and aspect extraction adds an LLM call per paper"* (ADR-65 Context). The full PARNESS four-value relation taxonomy is **rejected from day one** because *"it was designed for ML/science workflows and may be wrong-shaped for knowledge work"* — so one value is earned at a time (`similar` only after ≥200 claim notes with ≥500 inter-claim links *and* the human feels the "find similar" friction). This is the "simplest design that meets the requirement" principle applied to schema: type a field only when the query pressure is real.

---

#### 3. Discovery loop (ADR-61, ADR-37, ADR-66)

**What (deferred — nothing runs in alpha.1).** ADR-61 defines a **nightly proactive discovery loop**: Hermes on a nightly cron reads `research-focus.md`, picks top-N priorities (default 3), runs `find` per priority (≤10 candidates each), ingests the prior day's confirmed candidates, enriches stale notes, commits, and posts a morning summary. ADR-37 reserves a **separate Retriever/Scout profile** to split discovery scoring from ingest classification. ADR-66 reserves three inbox-triage improvements — **semi-autonomous batch triage** (batch classifications above a calibrated confidence, e.g. >0.92, into one approval card), an **agent-consensus pre-filter** (a second independent-provider profile pass sets `consensus:`), and **tournament pairwise ranking** for large (>50) inboxes as a cold-start fallback for a future learning-to-rank model.

The **live analogue** that *does* ship is structural, not automated: the knowledge cycle's *map* and *verify* tasks raise Inbox `gap` cards that re-trigger *catalog* — *"the output end of the cycle feeds the intake end"* (`docs/explanation/knowledge/knowledge-cycle.md`). Discovery in alpha.1 is operator-triggered `find`, not a cron.

**Why.** All three are deferred on the same discipline: *"autonomy expands within the lane, the structural review gate stays put"* and *"none is gated on a static trigger"* (ADR-61 Context). The nightly loop's dominant named risk is **silent cron failure** ("the loop fails loud, never silent") and **inbox flooding** if inclusion criteria aren't written down first — hence its adoption condition requires `screening-plan.md` to exist and a maintained `research-focus.md` for ≥4 weeks. It is also gated on **always-on infrastructure** (Syncthing + VPS), which ties it to ADR-63. The Scout split (ADR-37) is rejected *now* because *"one more profile with no current bottleneck to motivate it"* — a unified Librarian is simpler; the split earns its keep only when *"discovery volume genuinely overwhelms the unified Librarian… where discovery scoring and classification visibly contend."* ADR-66's consensus pre-filter carries a specific literature-driven caution: two profiles must use **different providers or fine-tuning regimes** to avoid *"correlated errors (the Bisht et al. 2026 hivemind finding)."*

---

#### 4. Evaluation / measurement & verification (ADR-20, ADR-11, ADR-62; ADR-29/44)

This is the sharpest **capture-now / analyze-later** split in the system.

**What ships in alpha.1 — the six-signal capture.** The publication-path ADR (ADR-20) commits to *"start the six-signal instrumented capture now — the single highest-leverage action."* The six signals (all emitting + self-tested per the release-plan appendix): (1) suggestion disposition accept:edit:reject → `disposition.jsonl`; (2) operator decision time per review card (derived); (3) per-card state-transition timestamps → `board-transitions.jsonl`; (4) API cost per card → `cost.jsonl`; (5) policy deny-reasons → `audit.jsonl`; (6) **FAMA exposure** (drafts citing a superseded claim) → the `fama-exposure` detector. Schemas are pinned in `docs/reference/telemetry.md`.

**What is deferred — the analysis harnesses (ADR-62).** The **CiteME-style Peer-reviewer regression harness** (~50 excerpt→claim pairs, gates prompt changes at the 90th-percentile baseline), the **Chain-of-Evidence claim taxonomy** (typed evidence chains, adapted from ScientistOne / Meng et al. 2026, *gated by* the CiteME harness), a **fleet-observability aggregator** (materializes the fleet-health dashboard), a **propagation-debts re-eval queue**, an **LLM-judge `prose-check` export gate** (never auto-edits, never blocks), and **execution-trace reflection on retry**. ADR-11 defines the umbrella capability: `vault-eval` is a **diagnostic maintenance capability built from existing machinery** — dispatched as a board `eval` card, executed with non-committing scratch-path writes, scored deterministically by the Linter (recall@k, support-rate, FAMA) — and its verdicts are **diagnostic, never gating**.

**Why.** The whole split rests on one irreversible fact: **"capture cannot be back-filled, so it ships first; the analysis harnesses that read it are deferred"** (ADR-62 Context; ADR-20 §2). Choosing the **vault-eval benchmark paper** (Path 1) over a system/position/artifact paper is justified because it is *"the only path tractable in months rather than years, has the lowest coupling to a finished system… and forces the measurement layer every downstream path depends on into existence"* (ADR-20 "Decision"). The deferred harnesses **gate one another** (the CiteME fixture gates the claim taxonomy; fleet observability surfaces the retry rate that gates reflection-on-retry), so ordering is encoded in their adoption conditions. And *"partial adoption can be worse than none — a claim taxonomy with most claims untyped makes type-aware checks unreliable"* (ADR-62 Consequences) — the reason each waits for a concrete volume trigger (e.g. CiteME only after a project has ≥20 approved drafts citing ≥20 approved claim notes). Verdicts stay non-gating to preserve the human-gate invariant (ADR-11 / ADR-03): *"an eval or prose-check dip informs the human and never auto-halts scheduled work."*

**Testing harnesses (ADR-29, ADR-44).** Evaluation of the *code*, as opposed to the vault, is a **layered testing framework** (ADR-29) with **L1 component tests in a repo-side pytest tree, not inline in shipped modules** (ADR-44). The release plan's S1 stage records five `--self-test` suites green: `policy_mcp`, `policy_hook`, `board_export`, `metrics_aggregate`, `detectors`.

---

#### 5. Distribution / install — repo-as-unit, `src/` + golden copy, bootstrap installer (ADR-26, ADR-55, ADR-64)

**What.** **The repo is the install unit** (ADR-26): clone it (or run the one-line bootstrap that clones it) and the installer at the repo root deploys everything. The repo has three parts — `scripts/install.{sh,ps1}` (bootstrap), `src/` (**source files only, never a live vault**), `docs/` (developer-facing, not deployed) (`docs/explanation/deployment/distribution-model.md`). The install *flow* (ADR-55) is **scaffold → populate → stage golden copy**: create the folder tree (checked against the machine-read `.memoria/schemas/folders.yaml`), populate system files from `src/`, then stage a hash-manifested **golden copy** at `<vault>/.memoria/golden/` that turns the Linter *"from a detector into a repairer"* via `lint:restore`. Then it wires the pre-commit gate, installs Hermes + the profiles (**pruning** stale `memoria-*` profiles), offers the optional cluster stack, installs Obsidian if absent, and wires the crons.

**Architecture — one bash implementation, a thin PowerShell launcher.** `scripts/install.sh` (~981 lines, per ADR-64) is the *single real script*; `scripts/install.ps1` is a **thin WSL2 launcher** that gates on WSL2, ensures Obsidian on the Windows side, then hands the whole flow to `bash scripts/install.sh` inside WSL2 (`docs/explanation/deployment/bootstrap-installer.md`). Windows runtime rule: **Hermes runs only on Linux/WSL2; Windows is the editing surface**, and WSL2 is a *hard prerequisite* — "No WSL2 → the installer does nothing" (explains, links Microsoft's guide, exits).

**Why.**
- **What:** ship `src/` not a live `vault/` template. **Why:** a live-vault template *"blurs 'source of truth' with 'a running instance,' invites accidental edits to the template, and offers no recovery path"* (distribution-model.md; ADR-55). Authoring (repo) and restoring (runtime golden copy) stay cleanly separate, and user content is structurally distinct from system files "from the first minute."
- **What:** the golden copy. **Why:** it makes the deployed vault *self-healing for system files without re-running the installer* — the daily Linter pass compares live files to the manifest and can restore a mangled one (`lint:restore`, propose-only).
- **What:** profile install is **idempotent + prunes**, releases are **fresh-install, never in-place migration**. **Why:** idempotency *"is the mechanism that keeps deployed profiles synchronized with their source"*; in-place migration's *"half-migrated states are the failure mode D52 rejected"* (distribution-model.md; bootstrap-installer.md non-goals).
- **What:** two files but *one* implementation, real logic in bash. **Why:** *"correctness, not just simplification: Hermes is WSL2-only on Windows, so profiles must be installed inside WSL — a native PowerShell `hermes profile install` could never work end-to-end"* (bootstrap-installer.md).
- **What:** guide-don't-automate app installs, presence-checks-not-version-gates, don't install language runtimes, default the vault *off* OneDrive. **Why:** each *"trades a little breadth for much less shell to build and maintain"*; OneDrive specifically *"fights Hermes's WSL writes across `/mnt/c`, and Git is the backup"* (bootstrap-installer.md "Simplifying decisions").
- **`curl | bash` safety model.** Inspect-first is the documented primary; the one-liner is wrapped in a `main`-guard "so a truncated download cannot execute a half-command," with a printed numbered plan + consent, `--dry-run`, and never-silently-elevate.

**Native Windows (ADR-64, `deferred`).** The WSL2-only rule's two rationales *"have since weakened"* — Hermes now runs natively on Windows and the analysis-stack wheels exist. The decision, if pursued, is *"a port that collapses the two-OS topology into one — not a runtime flag,"* and *"a meaningful share of the work is deletion"* (removing the `networkingMode=mirrored` bridge requirement, `/mnt/c` file-lock fights, the OneDrive hazard). **Why deferred anyway:** *"still too large to swap into the v0.1.x workspace releases, which are written and tested for WSL2"* — revisit after alpha.3. The bootstrap-installer doc carries the matching *"Reevaluation (2026-06)"* banner: *"This rule remains in force for the v0.1.x releases."*

---

#### 6. Cross-vault / multi-machine (ADR-60, ADR-63)

**What (both `deferred`; alpha.1 ships `local-only` only).** The adopted default is **`local-only`** — one workstation, Git for history, Zotero on localhost, $0 infra (`docs/explanation/deployment/deployment-options.md`). ADR-63 settles the *shapes* past it without building them: three sync topologies (`local-mesh` = Syncthing P2P/$0; `obsidian-sync` = cloud/~$10-mo/`.bib`-only Zotero; `always-on` = Syncthing+VPS/~$12–25-mo), a set of secondary-device operating patterns (vault-only, Telegram dispatch, HTTP API client, Hermes ACP-only, SSH-spawned ACP), and the invariants that keep them safe. ADR-60 defines four additive cross-boundary *capabilities* riding those substrates: cross-vault **read-only** retrieval, cross-project reading (a personal AgentRxiv), scripted `state.db` session-history sync, and a Hermes shared-memory server.

**Why.** The core risk the whole secondary-device design exists to make *structurally impossible* is **write coordination**: *"two machines race on card writes and corrupt the audit log"* (ADR-63 Context). Hence the load-bearing invariant **"exactly one Hermes dispatcher per vault"**, enforced by `HERMES_HOME` + test-vault isolation (mandatory, not optional, under `always-on`). Secondary-device install is **structural-over-behavioral**: a device compiles *only* profiles architecturally safe on it — `memoria-copi` is the always-safe baseline because `policy.allow.write: []` and `routing.invocation: interactive_only` mean it *cannot* write or be queue-dispatched *"regardless of human behavior"* — because *"structural enforcement ('profile not found') beats the behavioral convention 'don't enable cron.'"* Both ADRs are deferred with an explicit **anti-premature-optimization guard**: *"do not stand up a VPS or Syncthing mesh as a preparatory measure… Syncthing is additive later and restructures nothing, so there is no first-mover cost to pay early."* Sequencing is justified by coverage: *"scripted sync covers ~90% of the need at zero infrastructure, which is why it is sequenced first,"* and the memory server is explicitly guarded — *"do not adopt the memory server before scripted sync has been tried."* ADR-60 adds the trust boundary: a foreign vault's claim notes are *"treated as sources, not as your own synthesis"* and *"must never be promoted to local canon without re-synthesis."* The two ADRs are *"designed to move together."*

---

#### 7. Cost / metrics

**What.** Per-ingest cost is deliberately engineered *down*: Tier 0 is free (local); Tier 1 is *"a handful of HTTP calls… one local embedding pass, an optional per-tag zero-shot pass, and one schema-constrained classify call"*; Tier 2 adds *"at most one larger `[!brief]` call"* — *"the cost moves off the old 8-step LLM loop into cheap HTTP + a reused embedding model"* (ADR-30 "Cost / latency"). Model routing is a Hermes concern, not a deployment one — *"synthesis to Claude, embed/classify/quick-summary to cheaper models via OpenRouter"* (deployment-options.md). API cost per card is captured as telemetry signal #4 (`cost.jsonl`), and `metrics_aggregate.py` computes trust-score bands but is deferred to Phase 3 because *"it needs real run volume before trust-score bands are meaningful."*

**Why.** The system has **no scalar quality payoff to optimize against** (L3 ceiling forecloses it), so *"budget discipline replaces metric discipline. Because there is no scalar payoff to optimize against, the nightly loop is bounded by a cost ceiling (~$1–3/day) rather than by a quality target"* (ADR-21 Consequences). This is why the deferred nightly loop (ADR-61) and code-experiment loop carry `budget_iterations:`/`budget_cost_usd:` fields rather than accuracy targets — a cost ceiling is the only meaningful bound when there is nothing to maximize.

**Known cost/telemetry limitation at the cut.** Two of the six signals — `disposition` and `cost` — *"cannot emit on the current Hermes"*: `board_export.py` reads them from the card `metadata` overlay (`review_status`/`cost`/`tokens`) which this Hermes version does not surface in serialized card JSON. The exporter is *"correct and ready to consume both the instant Hermes exposes the overlay"* (release-plan G5 + §6 Known limitations). Four signals work live.

---

#### 8. The ADR landscape at `0e9ed9dd`

**Count.** `git ls-tree -r 0e9ed9dd -- docs/adr/` returns **70 markdown files**: **68 numbered ADRs (01–68)**, plus `README.md` (the index) and `_template.md`. By status in the README index: **46 accepted**, **15 deferred** (ADRs 34, 35, 38, 39, 40, 41, 58, 59, 60, 61, 62, 63, 64, 65, 66 — note some marked deferred), and **7 superseded** (01→46, 02→48, 04→47, 08→52, 27→28, 36→51, 37→48, 42→48). Numbers 60–68 are the alpha.1→alpha.2 wave that converted retired design pages into deferred/accepted decision records; ADR-68 (workspaces) is the most recent, added in the commit immediately prior.

**The ~15 most design-defining ADRs** (number · title · one-line decision):

| # | Title | Decision (one line) |
|---|---|---|
| **03** | Structural review gate | Writes to review-gated zones are degraded to `dry_run` by the **policy MCP** at the filesystem level — approval on the board card is the only path to canonical; not a prompt rule. |
| **21** | L3 autonomy ceiling | Target L3 (multi-step execution under human strategy, per-batch review), **structurally enforced**; agents propose/classify/draft/verify but never canonize; no autonomy exception anywhere (Coder-lane exception retired). |
| **22** | Build on Hermes | Build *on* the Hermes runtime (Kanban `kanban.db`, profiles, dispatcher, MCP host); Memoria supplies only conventions on top — *"Hermes moves work; Memoria decides what work means."* |
| **46** | Seven-layer architecture | PI · Interface · co-PI · Tasks · MCP · Engines · Vault — supersedes the original three-layer model (ADR-01). |
| **48** | co-PI + agent consolidation | One permanent co-PI fronts everything; the seven specialists consolidate to posture-defined agents (supersedes ADR-02/37/42). |
| **47** | Type-first category folders | Top level is `catalog/ notes/ projects/ inbox/ system/` — organized by content kind, no lifecycle numbers (supersedes lifecycle-folders ADR-04). |
| **50** | Universal lifecycle + maturity | One chain `proposed → provisional → current → retracted → archived`; maturity is a claim property; `archived` is a state not a folder; MOC → hub. |
| **57** | Engines write, agents judge | Any write whose content is rule-derivable is done by a deterministic **engine**, never an LLM agent; agents contribute only the judgment holes. |
| **30** | Tiered ingest pipeline | Capture → fallback-chained enrichment → gated write, in three tiers (Tier-0 local floor, Tier-1 reliable multi-source merge, Tier-2 optional) — *the alpha.1 value loop*. |
| **55** | src/ + scaffold + golden copy | Repo ships `src/` (never a live vault); installer scaffolds/populates; a hash-manifested golden copy makes system files restorable. |
| **26** | Repo is the install unit | Clone-and-bootstrap deploys everything; profiles hand-authored + idempotently deployed; `vault/` not independently installable. |
| **27 + 28** | Gate config + gate-as-plugin | Configure Hermes as Hermes reads config with **obsidian MCP as the only write path** per lane (27); implement the gate as a fail-closed **Python plugin**, not a never-firing shell hook (28). |
| **20** | Publication path | Vault-eval benchmark paper first (tractable, forces the measurement layer); **start six-signal capture now** because capture cannot be back-filled. |
| **11** | vault-eval as maintenance | Run eval as a diagnostic capability from existing machinery (board dispatch, scratch-path writes, Linter scoring) — **verdicts inform, never gate**. |
| **49** | Catalog in Bases; Linter as monitor | Catalog entities are markdown with Bases-queryable frontmatter; the **Linter** is both integrity monitor (cron/CI) and commit gate. |
| **54** | Two kinds of human decision | Approval gates vs. work prompts; **classification is automated + audited** (not gated), with batch worklists for high-cardinality decisions. |

**How the landscape frames the four subsystems above:** the *accepted* spine (03, 21, 22, 46–50, 55–57) is what alpha.1 actually builds — the structural gate, the layered architecture, the engines/agents split, the deterministic ingest loop, and the golden-copy install model. The *deferred* cluster (60–66) is exactly the pipeline-adjacent growth this document reconstructs — cross-vault (60), nightly discovery (61), M&V harnesses (62), multi-machine (63), native Windows (64), retrieval/schema extensions (65), triage/ranking (66) — each shape-settled, scheduling-gated, and adopting no code. ADR-67 (drift procedures) is the one late *accepted* decision that closes a design category rather than opening one: it retires the weekly-agent-run drift model entirely in favour of *"engine (daily cron) / installer (idempotent re-run) / repo CI,"* on the principle that *"nothing here needs a weekly agent run."*


---
