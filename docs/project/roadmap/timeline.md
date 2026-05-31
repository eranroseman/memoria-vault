---
topic: roadmap
---

# Timeline and phases

The week-by-week ramp from the [minimum viable system](README.md#minimum-viable-system) to production, plus the six implementation phases that structure the work. As in the [roadmap overview](README.md), the phases are ordered so each produces a working, useful slice.

## Implementation timeline

A concrete week-by-week ramp from MVS to production.

### Weeks 1–2 — Infrastructure

- Set up Zotero + BBT with the citekey format `auth.lower + year + shorttitle(1,0)` (see [ADR-4](../decisions/04-citekey-naming-convention.md)).
- Create the MVS folder structure.
- Install Hermes and configure terminal access.
- Drop in two templates: `paper-note.md`, `claim-note.md`.
- **Ingest 5 pilot papers.** Verify ingest works end-to-end.
- **Classify all 5.** Verify `_proposed_classification` proposals look reasonable.

Exit: a new note from ingest lands in the right folder with the right frontmatter.

### Weeks 3–4 — Seed the corpus

- Ingest your **30–50 most important papers**.
- Classify them all — this builds your corpus's classification baseline and validates the vocabulary.
- Write **5–10 claim notes** from the most synthesis-ready literature.
- Run the weekly ritual twice (even if minimal) to confirm 30-minute target.

Exit: classification feels routine; claim notes have started to form a graph.

### Month 2 — Deepen synthesis

- Complete classification on the full initial corpus.
- Write claim notes consistently — target **2–3 per week**.
- Run `hermes run find-duplicates` for the first time — establish the merge routine.
- Expand schema beyond MVS where you feel the absence (`pub_status`, `full_text_reviewed`, etc.).

Exit: the claim note layer is dense enough that you start linking across papers.

### Months 3–4 — Activate advanced features

- Create the **first MOC** when a topic crosses the topic-MOC threshold (≥ 15–20 papers + claim notes combined; see [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds)).
- Activate lag metrics in the weekly dashboard (once `triage_completed` is populated).
- Begin Canvas sessions for chapter planning.
- Start systematic `hermes run find` for whatever scoping work you have active.
- Add items / entities folders if you're consistently citing tools and people.

Exit: the vault stops being a place you build and starts being a place you write from.

### Month 5+ — Production use

- Migrate to a multi-device setup if the Chromebook becomes a regular working device or batch ingest needs to run overnight — see the [Deployment options](deployment-options.md) matrix.
- Build child MOCs as topic clusters become dense (a branch with `>20` claim notes and `>10` paper notes; see [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds)).
- Begin drafting from the reference layer.
- Promote from mode-based to four-profile (or the full seven) when the bottleneck appears.

The migration path always points the same direction: **start narrow, expand when the corpus demands it.** Avoid adding structure pre-emptively.

## Implementation phases

### Phase 1 — Naming and schema (rename + contract)

**Goal.** Establish Memoria as the official name and lock down the [schema contract](../../reference/glossary.md#system-and-architecture) that Hermes and the board will share.

**Steps.**

1. Rename the system in the vault documentation and any AGENTS-style schema files. Keep `research-wiki` as an alias for migration.
2. Define the card states, the worker lanes (one per profile), and the review gate rules in one schema document so Hermes and the board share the same contract.
3. Confirm note-type names match the defined set in [vault/README.md](../../explanation/vault/README.md): `fleeting-note`, `answer-note`, `paper-note`, `item-note`, `person-note`, `organization-note`, `venue-note`, `claim-note`, `moc`, `reference-note`, `project-note`, `code-note`, `canvas`, `draft`, `deliverable` (15 in total — the three entity types are separate, not a single `entity-*`). Keep any older names as deprecated aliases during transition.
4. Commit the design document set (`docs/`) as the shared source of truth.

**Exit criteria.** The schema is the single source of truth. Anyone (including the agent) can read it and know what the states, types, and folders mean.

### Phase 2 — Vault structure (folders + templates)

**Goal.** Ensure the vault is structurally ready for the workflows.

**Steps.**

1. Confirm the folder structure matches [vault/README.md](../../explanation/vault/README.md). Create any missing folders.
2. Drop the 15 templates into `00-meta/03-templates/` (see [vault/note-types.md](../../reference/note-types.md) for the full list).
3. Migrate any existing notes whose folder no longer matches their type.
4. Set up `00-meta/index.md` and `00-meta/weekly-review.md` with the queries from [obsidian-ui/README.md](../../explanation/obsidian-ui/README.md).
5. Confirm Zotero + Better BibTeX exports to `.memoria/library.bib`.

**Exit criteria.** A new note created from a template lands in the right folder with the right frontmatter. Dashboards open and show real data.

### Phase 3 — Hermes profiles (seven contracts)

**Goal.** Configure the seven Hermes profiles with their permissions, commands, skills, and MCPs — on the **primary** machine. The full seven only need to live on the [primary dispatcher](../../reference/glossary.md#system-and-architecture); secondary devices install a narrower set (see [Per-device install sets](#per-device-install-sets) below).

**Steps (primary machine).**

1. Create Hermes profiles for Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter.
2. For each profile, drop its `SOUL.md` (plus `config.yaml`, `mcp.json`, optional `cron/` and `skills/`) into `.memoria/profiles/memoria-<name>/`. The design summaries in [profiles/](../../explanation/profiles/) describe the contract each SOUL.md must satisfy; the SOUL.md files themselves live in the starter vault under `.memoria/profiles/memoria-<name>/`.
3. Attach only the commands, skills, and MCPs the profile needs (see [profiles/README.md](../../explanation/profiles/README.md)).
4. Test each profile in isolation with a small task that exercises its lane.
5. Confirm that permission boundaries hold: the Librarian cannot write to `30-synthesis/01-claims/`; the Socratic profile cannot write anywhere; the Mapper can only write to project-scratch corpus-map paths; the Linter cannot silently move files; etc.

#### Per-device install sets

For multi-device deployments (local-mesh and always-on), not every machine compiles all seven profiles; the right install set depends on the device's role. The **primary** (single workstation under local-only; desktop under local-mesh; VPS under always-on) compiles all seven and owns dispatch — all cron, all queue dispatch, all discovery loops run there. A secondary device installs only what its role can safely run: `memoria-socratic` as the baseline (architecturally write-denied, so safe regardless of human behavior), Mapper / Writer / Verifier added only per justified use case, and never Librarian / Coder / Linter. A developer's secondary install is the one exception — all seven, but only with **mandatory** `HERMES_HOME` isolation pointed at a *test vault*, never the production vault.

The principle: **install only what the device's role can safely run** (structural over behavioral enforcement). The canonical per-device install table — install tiers, per-profile risk, and the developer-isolation rule — lives in [Deployment options → Secondary-device patterns](deployment-options.md#secondary-device-patterns-local-mesh-and-always-on); it is not duplicated here.

**Exit criteria.** Each profile can do its job end-to-end on a small example on the primary. Permission violations fail loudly, not silently. Secondary devices have the right per-role install set; running a profile that wasn't installed returns a clean "profile not found" rather than a silent run.

### Phase 4 — Kanban board (state machine)

**Goal.** Stand up the board as the orchestration layer.

**Steps.**

1. Stand up the **Hermes built-in Kanban** (see [kanban-board/README.md](../../explanation/kanban-board/README.md) for the mandated choice and the alternatives that were considered).
2. Adopt the Hermes Kanban's fixed `status` enum — `triage`, `todo`, `ready`, `running`, `blocked`, `done`, `archived`. These are not configurable; map Memoria's lifecycle onto them (see [kanban-board/states.md](../../explanation/kanban-board/states.md)).
3. Define the review overlay in card `metadata`: `review_status`, `agent_verdict`, `review_owner`, `review_requested_at`, `reviewed_at`, `promote_target`, `supersedes`. (The execution fields — `status`, `assignee`, `reason`, `max_retries` — are Hermes built-ins, not Memoria's to define.)
4. Configure dispatch logic so cards in `triage`, `done` (awaiting review), or `blocked` are not claimable by non-review workers.
5. Configure retry behavior so recoverable failures reuse the same card (returned to `ready`) within `max_retries`.
6. Configure the Kanban dispatch rules to advance cards (no Orchestrator profile); configure Verifier and Linter to write `agent_verdict` recommendations the human promotes to `review_status: approved`.
7. **Stand up a mock REST API for board-layer testing.** A small in-memory or fixture-backed server that implements the same HTTP endpoints as the live Obsidian Local REST API (see [architecture/control-plane.md](../../explanation/architecture/control-plane.md)) but writes to a scratch directory instead of the live vault. The board's dispatch logic, retry rules, and state transitions are exercised end-to-end against the mock without Obsidian running — this is also what CI runs against. The thin-layers principle (one job per layer, no business logic in the glue) is what makes the mock cheap to build and maintain.

**Exit criteria.** A card can flow from `ready` through review and back to a worker. Retries reuse the same card. The review gate blocks dispatch. The state machine has a regression test suite that runs without live Obsidian.

### Phase 5 — Pilot corpus (small end-to-end run)

**Goal.** Run a small corpus through the full pipeline and refine the lane rules, review overlay, and handoff summaries before scaling.

**Steps.**

1. Pick 5–10 sources representative of your active research.
2. Run them through ingest → classify → distill → promote.
3. For each card, exercise the review gate explicitly. Watch for any state that "leaks" past review.
4. Note handoff friction: where did the next worker have to re-derive context? Improve handoff summaries.
5. Note routing friction: where did the dispatch rules misfire? Improve lane-override rules.
6. Refine the `metadata` overlay if a field is missing or unused (the Hermes `status`/built-in fields are fixed).

**Exit criteria.** A new source can move through the pipeline without surprises. The weekly dashboard meaningfully reflects state.

### Phase 6 — Scale and automate

**Goal.** Apply Memoria to the full research corpus and add automation at the edges.

**Steps.**

1. Migrate the existing corpus into the new structure (one folder at a time, with Linter dry-runs at each stage).
2. Add scheduled tasks: nightly enrichment refresh, weekly lint, monthly stale-note check.
3. Add a board summary dashboard if the board is dense enough to warrant it.
4. Set up Pandoc export pipeline for `40-workbench/*/04-drafts/`.
5. Configure session logging to write to `00-meta/02-logs/` and commit weekly.

**Exit criteria.** The system runs without daily babysitting. The human shows up for review and synthesis; everything else flows.
