---
topic: roadmap
---

# Timeline and phases

The week-by-week ramp from [Memoria v0.1](README.md#memoria-v01) to production corpus use, plus the six implementation phases that structure the work. Memoria v0.1 is the full system — all folders, templates, profiles, dashboards, and the Kanban board are stood up in weeks 1–2; subsequent weeks are about corpus density, not system assembly. A third, parallel track — [Publication instrumentation](#publication-instrumentation-parallel-track-from-day-1) — runs from day 1 for anyone keeping the publication paths open.

## Phases

Three phases from initial setup to production corpus use. Phase 1 installs every Memoria v0.1 component; Phase 2 seeds and validates the corpus; Phase 3 activates density-gated features and automates the edges. The direction throughout: **the system is complete from day 1; corpus density drives what you activate, not what you install.**

### Phase 1 — Full system setup · Weeks 1–2

**Goal.** Install every Memoria v0.1 component on a single machine (`local-only` deployment): schema contract, complete vault structure, all profiles, all skills, and the Kanban board. Everything in v0.1 lands here on one device. Later phases use these components — they do not install new ones. Multi-device is a Phase 3 concern.

**Steps.**

**Schema and naming**

1. Establish Memoria as the official name in vault documentation and any AGENTS-style schema files. Keep `research-wiki` as an alias for migration.
2. Define the card states, the worker lanes (one per profile), and the review gate rules in one schema document so Hermes and the board share the same contract.
3. Confirm note-type names match the defined set in [vault/README.md](../../explanation/vault/README.md): `fleeting-note`, `answer-note`, `paper-note`, `item-note`, `person-note`, `organization-note`, `venue-note`, `claim-note`, `moc`, `reference-note`, `project-note`, `code-note`, `canvas`, `draft`, `deliverable` (15 in total). Keep any older names as deprecated aliases during transition.
4. Commit the design document set (`docs/`) as the shared source of truth.

**Vault structure**

1. Create the **complete folder structure** (`00-meta/` through `95-archive/`, including items, entities, workbench, and deliverables) — confirm it matches [vault/README.md](../../explanation/vault/README.md).
2. Drop all **15 templates** into `00-meta/03-templates/` (answer, canvas, claim, code, deliverable, draft, fleeting, item, moc, organization, paper, person, project, reference, venue — see [vault/note-types.md](../../reference/note-types.md)).
3. Migrate any existing notes whose folder no longer matches their type.
4. Set up the **full dashboard suite** — `00-meta/01-dashboards/index.md` as the entry point plus all 10 dashboards (see [obsidian-ui/README.md](../../explanation/obsidian-ui/README.md)).
5. Confirm Zotero + Better BibTeX (citekey format `auth.lower + year + shorttitle(1,0)` per [ADR-4](../decisions/04-citekey-naming-convention.md)) auto-exports to `.memoria/library.bib`.

**Profiles, skills, and plugins**

1. For each of the seven profiles (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter), drop its `SOUL.md` (plus `config.yaml`, `mcp.json`, optional `cron/` and `skills/`) into `.memoria/profiles/memoria-<name>/`. The design summaries in [profiles/](../../explanation/profiles/) describe the contract each SOUL.md must satisfy.
2. Attach the commands, skills, and MCPs each profile needs (see [profiles/README.md](../../explanation/profiles/README.md)).
3. Install all **ACP plugins** and the **K-Dense scientific-agent-skills** set.
4. Test each profile in isolation with a small task that exercises its lane.
5. Confirm permission boundaries hold: Librarian cannot write to `30-synthesis/01-claims/`; Socratic cannot write anywhere; Mapper can only write to project-scratch corpus-map paths; Linter cannot silently move files.

**Kanban board**

1. Stand up the **Hermes built-in Kanban** (see [kanban-board/README.md](../../explanation/kanban-board/README.md) for the mandated choice and the alternatives considered).
2. Adopt the Hermes Kanban's fixed `status` enum — `triage`, `todo`, `ready`, `running`, `blocked`, `done`, `archived` — and map Memoria's lifecycle onto them (see [kanban-board/states.md](../../explanation/kanban-board/states.md)).
3. Define the review overlay in card `metadata`: `review_status`, `agent_verdict`, `review_owner`, `review_requested_at`, `reviewed_at`, `promote_target`, `supersedes`. (The execution fields — `status`, `assignee`, `reason`, `max_retries` — are Hermes built-ins.)
4. Configure dispatch logic so cards in `triage`, `done` (awaiting review), or `blocked` are not claimable by non-review workers.
5. Configure retry behavior so recoverable failures reuse the same card (returned to `ready`) within `max_retries`.
6. Configure Kanban dispatch rules to advance cards (no Orchestrator profile); configure Verifier and Linter to write `agent_verdict` recommendations the human promotes to `review_status: approved`.
7. *If pursuing publication optionality:* turn on the [five-signal log](#publication-instrumentation-parallel-track-from-day-1) from the first ingest — the disposition and decision-time signals cannot be backfilled.

**Exit criteria.** Schema is the single source of truth. A new note from any template lands in the right folder. All dashboards open and show real data. All seven profiles run end-to-end on a small task; permission violations fail loudly. A card flows `ready → running → done (awaiting review) → approved`; the review gate blocks dispatch.

### Phase 2 — Seed and synthesize · Weeks 3–8

**Goal.** Ingest the initial corpus, establish classification and claim-note rhythms, and validate the full pipeline against real data.

**Steps.**

1. **Ingest 5 pilot papers.** Verify end-to-end: note lands in `20-sources/01-papers/`, audit log fires, `_proposed_classification` proposals look reasonable, `[!brief]` callout populates.
2. **Ingest your 30–50 most important papers.** Classify them all — this builds the corpus's classification baseline and validates the vocabulary.
3. Write **5–10 claim notes** from the most synthesis-ready literature. Run the weekly ritual twice (even if minimal) to confirm 30-minute target.
4. Complete classification on the full initial corpus.
5. Write claim notes consistently — target **2–3 per week**.
6. Run `find-duplicates` (`hermes -p memoria-verifier chat -s find-duplicates`) for the first time — establish the merge routine.
7. Confirm all schema fields are populated consistently (`pub_status`, `full_text_reviewed`, `_proposed_classification`, `_enrichment`).
8. For each card during the pilot run, exercise the review gate explicitly. Watch for any state that "leaks" past review.
9. Note handoff friction (where did the next worker re-derive context?) and routing friction (where did dispatch rules misfire?). Improve summaries and lane-override rules accordingly.
10. Refine the `metadata` overlay if a field is missing or unused (the Hermes `status`/built-in fields are fixed).

**Exit criteria.** A new source moves through the pipeline without surprises. Classification feels routine. The claim note layer is dense enough to start linking across papers. The weekly dashboard meaningfully reflects state.

### Phase 3 — Activate, scale, and automate · Month 3+

**Goal.** Activate corpus-density-gated features, migrate the full corpus, add automation at the edges, and expand to multi-device if needed.

**Steps.**

1. **Create the first MOC** when a topic crosses the topic-MOC threshold (≥ 15–20 papers + claim notes combined; see [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds)).
2. Activate lag metrics in the weekly dashboard (once `triage_completed` is populated).
3. Begin Canvas sessions for chapter planning.
4. Start systematic discovery (`hermes -p memoria-librarian chat -s find`) for active scoping work.
5. Build child MOCs as clusters densify (> 20 claim notes + > 10 paper notes on a branch; see [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds)).
6. Begin drafting from the reference layer.
7. Migrate the existing corpus into the new structure (one folder at a time, with Linter dry-runs at each stage).
8. Add scheduled tasks: nightly enrichment refresh, weekly lint, monthly stale-note check.
9. Set up Pandoc export pipeline for `40-workbench/*/04-drafts/`.
10. Configure session logging to write to `00-meta/02-logs/` and commit weekly.
11. **Migrate to multi-device** when a second device enters regular use or batch ingest needs to run overnight. See [Deployment options](deployment-options.md) for the `local-mesh` and `always-on` patterns. When adding a secondary device: install only what that device's role can safely run (`memoria-socratic` as the baseline; Mapper / Writer / Verifier per justified use case; never Librarian / Coder / Linter); the primary retains all seven and owns all dispatch. Developer secondaries are the one exception — all seven, but only with `HERMES_HOME` isolation pointed at a test vault.

**Exit criteria.** The vault stops being a place you build and becomes a place you write from. The system runs without daily babysitting. The human shows up for review and synthesis; everything else flows.

## Publication instrumentation (parallel track, from day 1)

> **Scope.** This track applies only if keeping the [publication paths](evaluation.md) open is a goal. Since Memoria v0.1 is the full system, this is not an exception to a lean default — it is an additional logging discipline layered on top of the standard setup. The five signals below are **non-backfillable**: they must be captured live from the first ingest or the data is lost. If publication is not a goal, ignore this section.

**Why day 1.** Every publication path routes through a running system producing operator *time-series* — and the load-bearing signals (suggestion disposition, per-review decision time, policy deny-reasons) cannot be reconstructed after the fact. Everything backfillable from git (link density, FAMA exposure, classification debt) can wait; these cannot.

**The instrument — minimal, but running from the first ingest.** The Memoria v0.1 vault + the seven profiles + the Policy MCP + a minimal *timed* board ([Phase 1](#phase-1--full-system-setup--weeks-12)) + the supersession wiring ([ADR-22](../decisions/22-claim-supersession.md)). "Minimal" is load-bearing: manual card advancement is fine, and auto-dispatch / retry automation still defer — what matters is that the mechanisms *emit events*, not that they run at production scale.

**The five-signal log** (the actual day-1 deliverable; small — defined in [success-metrics.md](success-metrics.md) and [evaluation.md](evaluation.md)):

1. Suggestion disposition — accept : edit : reject, **per profile** *(non-backfillable)*.
2. Operator decision time per `awaiting-review` card *(non-backfillable)*.
3. Per-card state-transition timestamps.
4. API cost per card.
5. Policy deny-reasons.

**Retention / versioning disciplines** (cheap to keep, impossible to recover if skipped):

- **Version every profile prompt in git** — the only way the [CiteME-style Verifier harness](future-directions.md#citeme-style-verifier-regression-harness) and Chain-of-Evidence typing can be rebuilt retroactively.
- **Retain the raw audit log + board history** indefinitely — [Fleet observability](future-directions.md#fleet-observability) and static reports then become pure backfill.
- **Keep approved drafts** through the [ADR-3](../decisions/03-answer-draft-retention.md) 90-day sweep — they seed the vault-CiteME fixture; do not discard them.
- **Do not prune session `state.db`** — cheap, and it preserves reasoning-trace analysis for later.

**Paths 2/3 — the comparison arm.** The thesis "structurally blocking review is correct" is unfalsifiable without an advisory baseline. Run the comparison via the configurable review-gate mode ([ADR-31](../decisions/31-configurable-review-gate-mode.md)): `blocking` (default) vs `advisory`, **the same logger in both arms**, with `review_mode` stamped per card. Prefer a within-subject design (same operator, comparable projects) to blunt n=1 skepticism, and add a promotion-reversal event so false-promotion rate is measurable.

**Single-user / single-machine.** Nothing in Paths 1–3 needs a second machine or always-on infrastructure — those are Path-4 and [future-directions](future-directions.md) concerns. The only structural limit is single-*user* → n=1, mitigated by the logging above and the within-subject comparison.

**Exit** (ongoing — a discipline, not a one-time gate). From the first ingest: every card emits the five signals, every profile prompt is versioned in git, and approved drafts plus the audit log are retained. The binding constraint is calendar time, not capability — three months of this data is worth more than three months of further design.
