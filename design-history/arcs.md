# Part IV — Synthesis: evolution arcs (alpha.1 → alpha.15)

## Evolution arcs (alpha.1 → alpha.15)

Memoria's alpha series is not a feature-accretion history; it is a sequence of **re-derivations**, three of which (alpha.7, alpha.11, alpha.14) discarded a standing architecture and rebuilt from requirements. The through-line is a steady transfer of authority away from autonomous agents and configurable runtime toward a **deterministic, gated, single-writer engine** whose safety rests on traceability rather than approval. The dates below are the release-folder/design-doc authoring dates in git; the "biggest change" is the one decision that reframed the product at that step.

### Timeline

| Version | Date | One-line theme | Single biggest design change |
|---|---|---|---|
| alpha.1 | 2026-06-14 | First v0.1 cut of the Hermes + Obsidian + Zotero stack | Establishes the release-gate discipline and the three-layer (board · workers · vault) product on the Hermes runtime (ADR-01, ADR-22) |
| alpha.2 | 2026-06-14 | Consolidation checkpoint | Folds scattered v0.1 build work into one coherent checkpoint |
| alpha.3 | 2026-06-14/15 | UI build milestone | First dedicated Obsidian UI research/build pass (`tmp/ui-design-research-report.md`) |
| alpha.4 | 2026-06-15 | Build/defect closure + engine vocabulary | Names the deterministic layer **"operations"** (ADR-69) and pins **engines-write / agents-judge** (ADR-57) |
| alpha.5 | 2026-06-15 | The Project gate | Adds the fourth navigation gate plus the **thesis note, argument graph + warrant** (ADR-77/78/79) and the ephemeral test-env (ADR-80) |
| alpha.6 | 2026-06-16 | Conformance + test-env harness | Makes accepted ADRs actually true and ships containerized-test-env Phase 1 (ADR-80) |
| alpha.7 | 2026-06-18 | Clean-slate Obsidian UI & navigation | **Persistent-shell four-space model** (Inbox/Library/Knowledge/Project nav row) + Bases view layer + capture forms; retires the workspace-swap (ADR-68 → ADR-81) |
| alpha.8 | 2026-06-18/19 | Runtime foundations & observability | Splits the omnibus ADR-58/59/61/65 into the granular ADR-84…100 (classical-method displacements, retrieval/schema extensions) |
| alpha.9 | 2026-06-21 | UI/workflow + runtime-gate hardening | The literature-review **"qwen2.5:7b is the test fixture, not the runtime — the live engine is an API"** correction, plus a Hermes-version decision |
| alpha.10 | 2026-06-22 | Hermes/runtime governance + onboarding | **Promotion-gated verification** process; ADR-116/117/118/119 schema & dashboard work; tutorials + sample vault |
| alpha.11 | 2026-06-27 | Clean-slate re-derivation from requirements | The **integrity spine** (attributable/reversible/detected + read-barrier) over an **OKF workspace** (catalog/knowledge/capabilities); one knowledge graph (digest/note/hub); direction-not-authorship |
| alpha.12 | 2026-06-28 | The keep-test / storage boundary | **SQLite as SSOT for catalog + ops**, markdown only for the keep-set; **CLI-first**, Obsidian demoted to optional adapter; typed pydantic-ai operations (ADR-122) |
| alpha.13 | 2026-06-30 | Multi-source catalog enrichment | **capture→enrich split** pulling OpenAlex/Semantic Scholar/PubMed/Unpaywall/Crossref/arXiv with per-field provenance + retraction gate (ADR-123/124) |
| alpha.14 | 2026-06-30 | Standalone CLI + engine consolidation | **Removes Obsidian, Zotero, Hermes, MCP, and installed profiles from the required baseline**; OpenAlex graph import; universal concept frontmatter (#1157) |
| alpha.15 | 2026-07-01/02 | Engine + integrity hardening | The **four-type knowledge model** (note/work/hub/project) with **meaning-only frontmatter** — every verdict moved out of files into SQLite; quarantine-and-verify; uv/Typer/stdlib-sqlite; ADR consolidation 125–130 |

The shape of the series: alpha.1–6 build out the Hermes-era product; alpha.7 resets the *UI*; alpha.8–10 harden the *runtime*; alpha.11 resets the *architecture*; alpha.12–14 progressively strip the runtime down to a standalone engine; alpha.15 hardens and consolidates it.

---

### (a) Seven specialist profiles → five → no agent autonomy at all

**Lineage:** [01-alpha.1-baseline](01-alpha.1-baseline.md), [07-alpha.7](07-alpha.7.md), [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** The agent model collapsed in three moves. It began as **seven specialist Hermes profiles over one generalist** (ADR-02, `_notes/docs-exports/adr-full.md`: "Seven specialist profiles over one generalist agent"). At the **alpha.7-era clean-slate (ADR-48)** it flipped to **"one Co-PI fronts everything; specialists consolidate to posture-defined agents"** — five profiles, the retriever/scout profile (ADR-37) and profile-compilation (ADR-42) both folded in (`adr-full.md`: 37 and 42 "superseded → ADR-48"). By **alpha.14/15 the profile system was deleted from the product entirely** (ADR-125 supersedes 26, 48, 120; "Dropped from the product, not deferred: … installed profiles and lane/fleet (26, 48, 120)"). What survives is a single **read-only Co-PI posture plus capability-backed operation postures**, where "the dividing line is posture and write-permission, not capability or tool" (`docs/design/why-specialist-postures.md`).

**Why:** A generalist agent has "unclear responsibility … ambiguous permissions … no separation of stances" (`why-specialist-postures.md`), which is why roles were split in the first place. But finer role-splitting fragments the system: "more routing, more permission matrices, and — decisively — a fragmented learning loop" (same doc), so seven collapsed to postures-per-family. The deeper flip — removing *autonomy* — is forced by the autonomous-loop analysis: Karpathy's keep/revert loop is only safe when "the metric is monotonic … changes are reversible … experiments are independent," and knowledge work fails all three because "synthesis quality is not scalar," "synthesis errors compound," and "later sources reinterpret earlier ones" (`docs/design/why-not-autonomous.md`). Confidence-routing (SmartPause) was refused because "confident-wrong is the failure mode" (same doc; `why-review-gate-is-structural.md`). The literature review corroborated the *mechanics* but stripped the autonomy: the ~47-system survey found the useful patterns are "structural: stage gates, explicit roles, typed handoffs, persistent graphs" while the refused ones are "scalar-optimization loops: autonomous keep/revert, tournament evolution, confidence-routed gate bypass" (`docs/design/why-pattern-provenance.md`). Net effect: "from agent-assisted to bounded, phase-gated knowledge production" (same). The alpha.11 design states the destination bluntly — "the PI is a director + spot-corrector, not an approval queue … Trust shifts from 'a human approved this' to 'the system guarantees this trace'" (`scratch/releases/0.1.0-alpha.11/…-design.md` §4). ADR-125 keeps only the posture invariant with the runtime gone: "Memoria never grants an agent file, terminal, code-execution, or send tools."


**Current (as of alpha.15):** No agent autonomy is part of the alpha.15 product baseline; agents can propose, but the engine owns writes and checks.

**Pending (unreleased):** Beta.1 must prove the user-facing read/write loop without reintroducing autonomous writes.

### (b) Numbered folders (10-inbox / 02-answers) → type-first folders → state-not-folders

**Lineage:** [00-origins](00-origins.md), [01-alpha.1-baseline](01-alpha.1-baseline.md), [07-alpha.7](07-alpha.7.md), [15-alpha.15](15-alpha.15.md).


**What:** The original scheme was **lifecycle-numbered folders** — ADR-04, "Folders encode lifecycle stage, not subject area" (`adr-full.md`). At the alpha.7-era reset it flipped to **type-first category folders** (ADR-47, "Type-first category folders — catalog · notes · projects · inbox · system"), superseding ADR-04. Alpha.15 completed the move by taking read-state *out of folders entirely*: "a Concept's position in the system is its type, never its topic, and read state is record state, not a folder" (`docs/design/lifecycle-over-topic.md`), consolidated into the four-type homes of ADR-126.

**Why:** Numbered lifecycle folders forced a **file move on every state change**, which breaks the one property the system exists to protect. The current doc makes the argument: "Topics are many-to-many; a folder is one location," so folders are reserved "for the one fact that is one-to-one: what kind of checked bundle this is" (`lifecycle-over-topic.md`). Moving state into a record instead of a path is "strictly better" because "a state change does not move a file, so it cannot break wikilinks, lose Git history continuity, or invalidate saved queries," and "a claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking" (same doc). This is the same provenance-first logic (design principle 5, `design-principles.md`) that later drove `check_status` out of frontmatter (arc d).


**Current (as of alpha.15):** Type homes and database state, not lifecycle folders, carry system state.

**Pending (unreleased):** No pending folder-state decision is released.

### (c) Emergence of the four-type knowledge model (work / note / project / hub)

**Lineage:** [11-alpha.11](11-alpha.11.md), [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** There was no clean type model early — types accreted. ADR-126 records the damage: "The type roster grew by accretion (47, 50, 78, 117, 119): claim, question, excerpt, synthesis, thesis, steering, vocabulary, asset, digest, fleeting — each with folder homes, lifecycle fields, and per-type rules … 12+ types across three bundles." Alpha.11 already tried to tame this to a **three-node knowledge graph — digest (machine) / note (human) / hub (both)** (`0.1.0-alpha.11-design.md` §5). The **flip to exactly four types happened at alpha.15**: ADR-126 "Four concept types … replaces the accreted type zoo … with four types" — **note** (with optional `mode: claim | question`), **work** (a source's subjective digest, 1:1 with the SQLite catalog record), **hub** (owns exactly one controlled-vocabulary tag; membership is mechanical, salience is curated), and **project** (the compose-flow frame with one-way project→corpus references). It landed in code as PR-B2 (#1164), "the largest single change in 15": schema/templates/runtime cut to "the four knowledge Concept types (`note`, `work`, `hub`, `project`); Concept ids are ULIDs … `digest` materialization moved to `work`" (alpha.15 exec-plan §3).

**Why:** "The multiplicity itself caused drift and confusion" (ADR-126 Context). The discriminator was tightened to "a fundamentally different artifact" — a flippable check regime is a *mode*, not a type, and a layer-difference is not a knowledge type. That test dissolved most of the zoo into relocations ("excerpt → a `anchor` on a note/work; index → generated views; fleeting → an unchecked note; steering → the `instructions` config; thesis → a role, not a type"). The four earn their place by *creating distinct obligations the gap engine feeds on*: a `claim` mode without evidence is an `under-warranted` gap; an open `question` is a compose-flow lead — "field-derived typing could not tell a plain thought from a claim missing its evidence" (ADR-126). The model is genealogically Luhmann's: catalog work ≈ literature note, note = permanent note, hub = structure note/Map-of-Content (`docs/design/intellectual-foundations.md`, `hubs-and-navigation.md`), with the net-new machine-digest role borrowed from Karpathy's compiler.


**Current (as of alpha.15):** The released alpha.15 knowledge model has four Concept types: work, note, project, hub.

**Pending (unreleased):** Beta.1 must validate whether those four types cover the MVP read/write workflow.

### (d) Frontmatter: optional → universal enforcement (alpha.14) → meaning-only (alpha.15)

**Lineage:** [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** Early frontmatter was per-type and optional, and it *carried verdict state* — `check_status` lived in the file. **Alpha.14 forced universal frontmatter**: PR #1157 (`88b7f0f5`), "universal-concept-frontmatter enforcement … `id`/`standing`/`check_status` frontmatter enforcement across templates and operation manifests" (alpha.15 exec-plan §0). **Alpha.15 then inverted it**: PR-L (#1179) and the §S5 principle made frontmatter **meaning-only** — "`check_status` (and all verdict/derived state) is *not written to frontmatter at all*, and a gate asserts frontmatter carries no verdict fields" (exec-plan §1). Verdicts moved to SQLite (PR-B, #1163: "frontmatter `check_status` no longer trusted as verdict authority"). PR-AC (#1197) then closed the field set: the validator "rejects undeclared Concept frontmatter fields."

**Why:** The alpha.14 universal enforcement was the natural endpoint of read-barrier logic — a consumer must be able to trust every file's status, so every file must declare it. But that created the exact hazard ADR-126 names: "`check_status` lived in frontmatter, so checking a note rewrote it, hand-edits forged status, and every consumer had to distrust the file it was reading." The fix is the split-authority rule of ADR-125: "files own meaning, the DB owns verdicts and records." This is enforced structurally, not by convention, because the value only holds if it *can't* be forged — `checked_terminology_gate.py` even "blocks checked = approved/verified/trusted drift" (exec-plan PR-L). Fail-closed follows: "rebuild-from-files starts fully `unchecked` and ignores frontmatter status" (PR-B). The move is the same provenance-integrity principle as arc (b), applied to state instead of location.


**Current (as of alpha.15):** Frontmatter is meaning-only; verdict and derived state live in SQLite.

**Pending (unreleased):** No pending decision may put check/verdict state back in authored files without a new release decision.

### (e) The OKF interchange bundle (alpha.11 / alpha.15)

**Lineage:** [11-alpha.11](11-alpha.11.md), [15-alpha.15](15-alpha.15.md).


**What:** Memoria discovered its own substrate was a near-match for Google Cloud's **Open Knowledge Format**. ADR-107 (proposed 2026-06-19, the alpha.9 era) records the convergence: "OKF's *Concept* is a typed markdown document, its *Concept ID* is the file path minus `.md`, relationships are markdown links … That an external, vendor-backed spec landed on the same shape is validation." **Alpha.11 adopted OKF nouns for the whole workspace**: "A Memoria workspace contains three OKF-compatible bundle roots — `catalog/`, `knowledge/`, and `capabilities/`," with Memoria as a "strict producer, permissive consumer" (`0.1.0-alpha.11-design.md` §6.1). **By alpha.15 OKF was narrowed to the boundary only** — export/interchange, not the internal representation. ADR-107 states the reason it can only be a boundary: "OKF mandates permissive consumption … and holds that 'the specific kind of relationship is conveyed by the surrounding prose, not by the link itself.' Memoria deliberately rejected prose-typed relationships in favor of typed edges (ADR-126) … OKF is therefore a fit for the boundary, not the core."

**Why:** OKF solved Memoria's "least-defined layer … its outbound layer" — it "supplies exactly that missing unit: the Knowledge Bundle … consumable without Memoria's gates, MCPs, or Hermes runtime" (ADR-107). But OKF's permissive-consumer thesis is "the inverse of Memoria's thesis," which needs the relationship type *on the edge* for graph queries and enforces "strict schemas, controlled vocabularies, and category-error rejection." So the interchange format could not become the internal contract without discarding the integrity model. The retreat from workspace-wide OKF (alpha.11) to export-only (alpha.15) tracks the broader alpha.12 keep-test: only the keep-set must be portable markdown; working state is SQLite (arc g).


**Current (as of alpha.15):** OKF is an interchange boundary, not the internal representation.

**Pending (unreleased):** Beta.1 still needs an export/import acceptance test if interchange is in MVP scope.

### (f) The Hermes runtime's rise (alpha.9/10) and its role by alpha.15

**Lineage:** [01-alpha.1-baseline](01-alpha.1-baseline.md), [09-alpha.9](09-alpha.9.md), [10-alpha.10](10-alpha.10.md), [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** Hermes was the *foundation* of the product from alpha.1: ADR-22 "Build on the Hermes Agent runtime rather than a bespoke one," ADR-26 "The repo is the install unit; profiles are hand-authored," ADR-27/28 the write-gate as a Hermes plugin, ADR-32 external access over MCP, ADR-46 the seven-layer architecture on Hermes. Its **peak was alpha.9/10**, whose themes are literally "Hermes-version decision" (alpha.9 README) and "Hermes/runtime governance" (alpha.10 README), with cost/session accounting read straight from the Hermes session store (ADR-106: "hermes kanban show … `~/.hermes/profiles/<lane>/state.db`"). Then it was demoted, then removed. **Alpha.11** kept Hermes only "as a specialized adapter … where a specific Hermes feature pays for itself," with a **direct OpenAI-compatible API as the default runner** (`0.1.0-alpha.11-design.md` §8). **Alpha.12** made the engine standalone and CLI-first. **Alpha.14** put Hermes explicitly "Outside the baseline" (`0.1.0-alpha.14-design.md` §0). **Alpha.15/ADR-125 dropped it from the product**: "Dropped from the product, not deferred: Hermes (22, 35, 43, 80's Hermes-flavored harness)." By alpha.15 the runtime is Python 3.12 + uv + Typer + stdlib sqlite3 + pydantic-ai + git CLI (ADR-125); "Hermes is not part of the runtime" (exec-plan PR-AG). Hermes plays **no role** in shipped alpha.15.

**Why:** The rise was pragmatic reuse — "a durable state machine across sessions and retries — the runtime Memoria builds on" (`_notes/ai-research-systems-survey.md`). The fall was driven by the same alpha.9 literature correction that reset the model tier: the review "was run assuming `qwen2.5:7b` (local) is Memoria's production engine. It is not: `qwen2.5:7b` is the local test fixture; the live … engines call an LLM API" (`_notes/REVIEW-SUMMARY.md`, `REVIEW-REFUTATIONS.md`). Once the live engine is an API, the Hermes control-plane DB, profiles, Kanban, and MCP-as-required-API become weight the single-user local tool doesn't need — the alpha.11 design lists them among what to "deliberately shed": "per-write approval … profiles/fleet as the primary runtime model, the Hermes control-plane DB, the seven-layer ceremony" (`_notes/0.1.0-alpha.11-design.md`). ADR-125 turns the reuse argument back on itself: "The engineering ADR-22 warned against (durable state, retries, crash recovery) is now owned in-house — ADR-127 is where that obligation is paid." The consequence is the design goal all along: "One install command, no external runtime, no always-on process."


**Current (as of alpha.15):** Hermes is not part of the released alpha.15 runtime.

**Pending (unreleased):** Any future adapter must be optional and must not become the product runtime by accident.

### (g) The SQLite / derived-store state boundary (alpha.12)

**Lineage:** [11-alpha.11](11-alpha.11.md), [12-alpha.12](12-alpha.12.md), [15-alpha.15](15-alpha.15.md).


**What:** Alpha.11 held a **files-are-SSOT-everywhere** rule with "a passive rebuilt index over files" — the query index (`qmd`), embeddings, DAG, and queues were all "disposable projections (gitignored, rebuilt)" (`0.1.0-alpha.11-design.md` §6). **Alpha.12 flipped this with the keep-test** (ADR-122): "The thing you keep if Memoria dies must be markdown files in OKF, plus a portable bibliography export. Everything else is free to be SQLite" (`0.1.0-alpha.12-design.md` §1). SQLite became **SSOT for the catalog, source/entity/link graph, journal, queue, flags, check status, and rollback graph**, with markdown reserved for the keep-set (knowledge + capabilities + a materialized `references.bib`). Alpha.15/ADR-125 hardened it into a **split-authority rule**: "SQLite is the authority for records, operations, queue, journal, and verdicts; markdown files are the human corpus; content-addressed blobs hold raw payloads," explicitly "overturning ADR-49's rejected alternative ('SQLite as the store: never the source of truth')."

**Why:** The alpha.11 all-files rule was honest about ownership but wrong about *relational* state: a passive file-index cannot give "records, queues, and verdicts a transactional home markdown cannot provide" (ADR-125). The keep-test replaced "the fuzzy 'ownership feels important'" with an objective question — "does the user need this to keep thinking and writing outside Memoria" (`0.1.0-alpha.12-design.md` §1) — so ownership is preserved exactly where it matters and SQLite is used everywhere it doesn't. Two enabling constraints were relaxed to make this affordable: "no multi-device sync (single machine)" and "ownership/portability scoped to the keep-set + bibliography export, not the whole workspace" (same doc §0). Alpha.15 then paid the durability bill this boundary implies: WAL + `synchronous=FULL`, write-ahead fsync ordering, crash-at-each-boundary recovery, and fail-closed-to-`unchecked` on DB loss (exec-plan PR-D2, §1; ADR-127).


**Current (as of alpha.15):** SQLite owns records, operations, queue, journal, and verdicts; markdown owns the human keep-set.

**Pending (unreleased):** Beta.1 must exercise crash/rebuild behavior on the real read/write path.

### (h) Enrichment / graph (DOI, OpenAlex, Crossref — alpha.13/14)

**Lineage:** [13-alpha.13](13-alpha.13.md), [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** Early catalog metadata rode **Zotero + Better BibTeX** as the bibliographic backbone (ADR-05/06). **Alpha.13 built a dedicated multi-source enrichment subsystem** on the alpha.12 SQLite catalog: a "capture/enrich split … `capture-source` durably stages raw content … then `enrich-source` resolves identifiers → fetches required providers → merges one canonical record with per-field provenance → validates/checks (incl. retraction) → promotes the source to consumable `checked`" over "OpenAlex, Semantic Scholar, PubMed, Unpaywall, Crossref, arXiv" (`0.1.0-alpha.13-design.md` §0), gated by ADR-123 (DOI catalog enrichment) and ADR-124 (standalone catalog citation authority, which absorbed the old Zotero-authority ADR-06). **Alpha.14 imported the citation graph itself**: OpenAlex authorship/primary-topic/keyword edges, Crossref relations and full-text links, OpenAlex OA full-text URLs, and OpenAlex concepts/MeSH/SDG as graph topics (commits `cf9f23ef`, `c3538d47`, `dedccea8`, `62011e1c`, `a618b1ed`, etc. in the `0e9ed9dd..5b1ea8bc` log). **Alpha.15** hardened the merge (PR-F, #1173: "static field-authority table … deterministic blob replay … `provider_coverage = full|partial|degraded`") and added record-linkage attention on exact/blocked duplicate IDs (PR-V…PR-Z, ADR-94) plus MASSW-aligned work aspects (PR-AB, ADR-99).

**Why:** Zotero-as-authority conflicted with the standalone direction — ADR-124 made the catalog its own citation authority so the product no longer *requires* an external reference manager (Zotero survives only "as importers, not authority," `0.1.0-alpha.11-design.md` §8). Multi-provider enrichment is forced by the requirement "every catalog item is enriched from multiple scholarly APIs" (`0.1.0-alpha.13-design.md` method), and per-field provenance follows directly from design principle 5, "provenance everywhere" (`design-principles.md`): "Each provider call is a journal `api_call` event … so every field is traceable to who supplied it." The capture→enrich split exists to keep the checked boundary narrow — a DOI source cannot be promoted to `checked` until enrichment and the retraction check pass (`0.1.0-alpha.13-design.md` capture-boundary table). Importantly, merge stays **deterministic** and **never auto-merges identities**: record-linkage collisions "emit one stable `inbox/` work prompt … and do not merge records" (exec-plan PR-V), because the ingest engine must "never merge identities silently" (ADR-56) and the enrichment path is worker-only ("agents never get network or code-execution").


**Current (as of alpha.15):** Catalog enrichment is deterministic, provider-provenanced, and does not silently merge identities.

**Pending (unreleased):** Beta.1 must decide the minimum provider set needed for an actual useful MVP.

### (i) UI / navigation — the alpha.7 clean-slate

**Lineage:** [07-alpha.7](07-alpha.7.md), [14-alpha.14](14-alpha.14.md), [15-alpha.15](15-alpha.15.md).


**What:** The UI was rebuilt from scratch at **alpha.7**, "Clean-slate Obsidian UI & navigation." It landed "the Bases view layer, capture forms, the persistent-shell gate model (Inbox/Library/Knowledge/Project, switched by a nav row — retiring the ADR-68 workspace-swap), Portals folder navigation … and the Memoria-tuned Obsidian config + CSS" (alpha.7 README), formalized in ADR-81 (which superseded the ADR-68 Desk/Library/Studio workspaces). The general projector engine, projected telemetry, and the Canvas/argument-graph spatial axis were **deferred** into ADR-102/103. Later refinements: ADR-101 fixed the vocabulary ("navigation surfaces are 'spaces'; 'gate' is reserved for the approval gate"). By **alpha.14/15 the entire Obsidian UI was removed from the required product** — ADR-125 drops "the Obsidian-hosted policy plugin (28, 31)," and alpha.15 is explicitly "an engine and integrity checkpoint, not an Obsidian plugin release … No alpha.15 slice adds … an Obsidian plugin, plugin manifest, command-palette command, Inspector panel" (`0.1.0-alpha.15-design.md` Scope Boundary); the shipped surfaces are "CLI, scoped MCP, and loopback HTTP" (exec-plan PR-AG).

**Why:** The pre-alpha.7 workspace-swap model (ADR-68) treated navigation as *mode switching* between whole workspaces, which fought the way a researcher actually moves between activities; the persistent-shell "nav row" made the four spaces (which map onto the four jobs — Library/Knowledge/Project + the Inbox queue, `docs/design/what-memoria-is.md`: "you bring sources into the Library, build them into connected claims in Knowledge, and drive an inquiry to output in a Project") always-present instead of exclusive. The UI stayed deliberately thin — "thin in code, but load-bearing" — with the hard rule that the plugin "is a control panel, not a writer": it "never writes canonical Concepts … it enqueues; the worker commits" (`0.1.0-alpha.11-design.md` §8.1), and surfaces "show raw evidence/derivation first, any suggestion second — never an 'agent verdict' (Jacobs)." That write-boundary discipline is exactly what let the whole Obsidian surface be *removed* by alpha.14 without touching the integrity core: because the UI never owned truth, dropping it cost the engine nothing, and the read/view/action contracts could be re-expressed over CLI/HTTP/MCP. Any future editor adapter now "require[s] their own ADR instead of inheriting an alpha.15 commitment" (exec-plan PR-AG).


**Current (as of alpha.15):** The required surface is engine-first: CLI/read API, not an Obsidian plugin.

**Pending (unreleased):** Beta.1 must choose the smallest direct user surface that makes reading and writing usable.

---

**The single sentence that ties all nine arcs together:** every flip moves a guarantee from something a human or agent *does* (approve a write, choose a folder, set a status field, run a profile, host a UI, trust a reference manager) to something the system *structurally enforces* (a trace, a type-home, a DB verdict, a deterministic operation, a scoped read API, an in-house enriched catalog) — because the design's founding thesis is that when "the human directs but does not author or approve each change," integrity "rests on a tamper-evident derivation graph + continuous structural checks + cascade rollback, with a human gate only where an action is irreversible" (`0.1.0-alpha.11-design.md` §0, §2).

Key source files: `/home/eranr/memoria-vault/scratch/releases/0.1.0-alpha.{11,12,13,14,15}/*-design.md`; `/home/eranr/memoria-vault/scratch/releases/0.1.0-alpha.15/0.1.0-alpha.15-exec-plan.md`; `/home/eranr/memoria-vault/main/docs/adr/{107,122,123,124,125,126}-*.md`; `/home/eranr/memoria-vault/main/docs/design/{why-not-autonomous,why-specialist-postures,why-review-gate-is-structural,lifecycle-over-topic,hubs-and-navigation,why-pattern-provenance,intellectual-foundations,design-principles,what-memoria-is}.md`; `/home/eranr/memoria-vault/main/_notes/{REVIEW-SUMMARY,REVIEW-REFUTATIONS,ai-research-systems-survey,docs-exports/adr-full}.md`; and the historical release READMEs under `docs/releasing/0.1.0-alpha.{1..10}/` (recoverable via git; deletion commit `846d8439`).

### (j) Decision-record mechanism — ADRs -> living design history

**Lineage:** [00-origins](00-origins.md) through [15-alpha.15](15-alpha.15.md), plus this living synthesis.

**What:** Historical ADRs are evidence, not authority. Durable decisions now belong in release decision ledgers while they are being made, then close into the frozen design-history chapter and this synthesis when the release closes.

**Why:** The alpha history shows repeated architectural reversals. A live ADR set made older opinions look authoritative after the implementation and product thesis had moved on. The safer mechanism is a dated release decision with typed pointers to implementation, tests, and evidence, followed by a frozen release chapter.

**Current (as of alpha.15):** Alpha.15 remains the last released technical baseline. This mechanism change is a workflow migration, not a retroactive product change.

**Pending (unreleased):** The beta.1 release workspace must carry open Y-statement decisions until they are implemented, rejected, or folded into the next frozen chapter.
