# Timeline and phases

The week-by-week ramp from [Memoria v0.1](README.md) to production corpus use, plus the six implementation phases that structure the work. Memoria v0.1 is the full system — all folders, templates, profiles, dashboards, and the Kanban board are stood up in weeks 1–2; subsequent weeks are about corpus density, not system assembly.

## Phases

Three phases from initial setup to production corpus use. Phase 1 installs every Memoria v0.1 component; Phase 2 seeds and validates the corpus; Phase 3 activates density-gated features and automates the edges. The direction throughout: **the system is complete from day 1; corpus density drives what you activate, not what you install.**

### Phase 1 — Full system setup · Weeks 1–2

**Goal.** Install every Memoria v0.1 component on a single machine (`local-only` deployment): schema contract, complete vault structure, all profiles, all skills, and the Kanban board. Everything in v0.1 lands here on one device. Later phases use these components — they do not install new ones. Multi-device is a Phase 3 concern.

**Steps.**

**Schema and naming**

1. Establish Memoria as the official name in vault documentation and any AGENTS-style schema files. Keep `research-wiki` as an alias for migration.
2. Define the card states, the worker lanes (one per profile), and the review gate rules in one schema document so Hermes and the board share the same contract.
3. Confirm note-type names match the defined set in [vault/README.md](../../docs/explanation/architecture/vault.md): `fleeting-note`, `answer-note`, `paper-note`, `item-note`, `person-note`, `organization-note`, `venue-note`, `claim-note`, `moc`, `reference-note`, `project-note`, `code-note`, `canvas`, `draft`, `deliverable` (15 in total). Keep any older names as deprecated aliases during transition.
4. Commit the design document set (`docs/`) as the shared source of truth.

**Vault structure**

1. Create the **complete folder structure** (`00-meta/` through `95-archive/`, including items, entities, workbench, and deliverables) — confirm it matches [vault/README.md](../../docs/explanation/architecture/vault.md).
2. Drop all **15 templates** into `00-meta/03-templates/` (answer, canvas, claim, code, deliverable, draft, fleeting, item, moc, organization, paper, person, project, reference, venue — see [vault/note-types.md](../../docs/reference/note-types.md)).
3. Migrate any existing notes whose folder no longer matches their type.
4. Set up the **full dashboard suite** — `00-meta/01-dashboards/index.md` as the entry point plus all 10 dashboards (see [obsidian/README.md](../../docs/explanation/obsidian/README.md)).
5. Confirm Zotero + Better BibTeX (citekey format `auth.lower + year + shorttitle(1,0)` per [ADR-6](../decisions/06-citekey-naming-convention.md)) auto-exports to `.memoria/library.bib`.
6. Resolve the callout-manager configuration: copy `.obsidian/plugins/callout-manager/data.json.TODO` → `data.json` and fill in callout styling. Until resolved, `[!brief]`, `[!suggestions]`, and `[!verification]` callouts do not render correctly.

**Profiles, skills, and plugins**

1. **Run the installer** — the bootstrap `install.sh` (Ubuntu/Debian + WSL2; `install.ps1` is the thin Windows launcher). Its profile-install step (also runnable alone via `--profiles-only`) stages all seven profiles, substitutes `{{VAULT_PATH}}` in every `mcp.json` and `config.yaml`, pip-installs MCP requirements (`mcp>=1.2.0`, `PyYAML>=6.0`), and registers profiles via `hermes profile install`. Do not drop files manually — the path substitution is what makes the policy gate and MCP wiring functional. The design contracts each `SOUL.md` must satisfy are in [profiles/](../../docs/explanation/profiles/).
2. **Version every profile prompt in git from this first commit.** Prompt history cannot be reconstructed after the fact — it is the prerequisite for any retrospective analysis of suggestion quality, Chain-of-Evidence typing, or regression harness work. A profile whose prompt history has gaps cannot be audited.
3. **Install the five pending Obsidian plugins** as post-clone steps via Community Plugins — see [reference/plugins.md](../../docs/reference/plugins.md) for exact names and required configuration. The five are: `dataview` (every dashboard query depends on it), a template runner (template insertion), a quick-capture plugin (fleeting-note intake), `obsidian-git` (vault commits and prompt versioning), and `obsidian-homepage` (auto-opens `Home.md` on startup). None ship in `.obsidian/plugins/`; no dashboard, template, or capture workflow functions without them.
4. Install all **ACP plugins** and the **K-Dense scientific-agent-skills** set (`hermes skills install`). K-Dense skills ship as empty `.keep` placeholders in each profile's `skills/` directory — `hermes skills install` must run before any profile can invoke them.
5. **Verify the policy gate:** run `python .memoria/mcp/policy_mcp.py --self-test` (34 checks) and `python .memoria/mcp/policy_hook.py --self-test` (18 checks, including pre→post roundtrip). Both must pass before any profile is allowed to run against the production vault.
6. Test each profile in isolation with a small task that exercises its lane.
7. Confirm permission boundaries hold: Librarian cannot write to `30-synthesis/01-claims/`; Socratic cannot write anywhere; Mapper can only write to project-scratch corpus-map paths; Linter cannot silently move files.

**Kanban board**

1. Stand up the **Hermes built-in Kanban** (see [kanban-board/README.md](../../docs/explanation/kanban-board/README.md) for the mandated choice and the alternatives considered).
2. Adopt the Hermes Kanban's fixed `status` enum — `triage`, `todo`, `ready`, `running`, `blocked`, `done`, `archived` — and map Memoria's lifecycle onto them (see [kanban-board/states.md](../../docs/explanation/kanban-board/states.md)).
3. Define the review overlay in card `metadata`: `review_status`, `agent_verdict`, `review_owner`, `review_requested_at`, `reviewed_at`, `promote_target`, `supersedes`. (The execution fields — `status`, `assignee`, `reason`, `max_retries` — are Hermes built-ins.)
4. Configure dispatch logic so cards in `triage`, `done` (awaiting review), or `blocked` are not claimable by non-review workers.
5. Configure retry behavior so recoverable failures reuse the same card (returned to `ready`) within `max_retries`.
6. Configure Kanban dispatch rules to advance cards (no Orchestrator profile); configure Verifier and Linter to write `agent_verdict` recommendations the human promotes to `review_status: approved`.
7. **Wire the board exporter on a ~60s cadence.** `board_export.py` must run continuously to project the live Hermes board into `00-meta/board/<task_id>.md` and `00-meta/02-logs/board-state.jsonl` — this is what the board-state and fleet-health dashboards read. Without it, dashboards show no board data even though the board itself is running.
8. **Enable the five-signal log from the first ingest.** Suggestion disposition and operator decision time cannot be reconstructed after the fact. The five signals are: (1) suggestion disposition (accept : edit : reject) per profile; (2) operator decision time per `awaiting-review` card; (3) per-card state-transition timestamps; (4) API cost per card; (5) policy deny-reasons. Defined in [measurement-and-verification.md](../proposals/measurement-and-verification.md).
9. Configure the review-gate mode per [proposal-31](../proposals/31-configurable-review-gate-mode.md): `blocking` (default) vs `advisory`. Stamp `review_mode` on every card. This makes the comparison arm available later without retrofitting — a within-subject baseline (same operator, comparable projects) requires that both arms log identically from the start.
10. Do not prune session `state.db`. It is small, and it preserves the reasoning-trace data needed for any retrospective analysis.

**Exit criteria.** Schema is the single source of truth. A new note from any template lands in the right folder. All five pending Obsidian plugins are installed and dashboard queries return real data. Policy gate self-tests pass (34 + 18 checks). `board_export.py` is running and `00-meta/board/` is populating. All seven profiles run end-to-end on a small task; permission violations fail loudly. A card flows `ready → running → done (awaiting review) → approved`; the review gate blocks dispatch. **The five-signal log is running and emitting all five signals. Every profile prompt is committed to git.**

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
9. **Check suggestion disposition ratios per profile** (accept : edit : reject) after the first 10–20 cards per lane. A high rejection rate signals the profile's proposals are poorly calibrated; a near-zero rejection rate signals rubber-stamping. Both warrant a prompt revision.
10. **Track operator decision time on `awaiting-review` cards.** Outliers reveal where the review ritual stalls — either the card's context summary is insufficient or the review criteria are unclear. Improve the relevant `SOUL.md` summary section accordingly.
11. Note handoff friction (where did the next worker re-derive context?) and routing friction (where did dispatch rules misfire?). Improve summaries and lane-override rules accordingly.
12. Refine the `metadata` overlay if a field is missing or unused (the Hermes `status`/built-in fields are fixed).

**Exit criteria.** A new source moves through the pipeline without surprises. Classification feels routine. The claim note layer is dense enough to start linking across papers. The weekly dashboard meaningfully reflects state. Suggestion disposition ratios per lane are in a reasonable range (not near 0% or 100% rejection).

### Phase 3 — Activate, scale, and automate · Month 3+

**Goal.** Activate corpus-density-gated features, migrate the full corpus, add automation at the edges, and expand to multi-device if needed.

**Steps.**

1. **Create the first MOC** when a topic crosses the topic-MOC threshold (≥ 15–20 papers + claim notes combined; see [linking.md](../../docs/reference/linking.md#moc-thresholds)).
2. Activate lag metrics in the weekly dashboard (once `triage_completed` is populated).
3. Begin Canvas sessions for chapter planning.
4. Start systematic discovery (`hermes -p memoria-librarian chat -s find`) for active scoping work.
5. Build child MOCs as clusters densify (> 20 claim notes + > 10 paper notes on a branch; see [linking.md](../../docs/reference/linking.md#moc-thresholds)).
6. Begin drafting from the reference layer.
7. Migrate the existing corpus into the new structure (one folder at a time, with Linter dry-runs at each stage).
8. Add scheduled tasks: nightly enrichment refresh, weekly lint, monthly stale-note check. Also wire `metrics_aggregate.py` on a weekly cadence — it needs real run volume before trust-score bands are meaningful, so Phase 3 is the right trigger for this one (unlike `board_export.py`, which runs from Phase 1).
9. Activate the **skill-lifecycle dashboard** once skill-governance is stood up (`00-meta/07-skills/` is a placeholder until this phase).
10. Set up Pandoc export pipeline for `40-workbench/*/04-drafts/`.
11. Configure session logging to write to `00-meta/02-logs/` and commit weekly.
12. **Retain the raw audit log and board history indefinitely.** Do not rotate or prune `00-meta/02-logs/audit.jsonl` or session `state.db`. Fleet observability and static reports are pure backfill from these logs — they have no value if the logs are gone.
13. **Keep approved drafts** through the Linter's answer-draft retention sweep (the `stale-answer-drafts` detector flags `10-inbox/02-answers/` notes older than 90 days for keep/promote/discard; no auto-archive). They seed the vault-CiteME fixture and cannot be reconstructed.
14. **Run the comparison arm** if you have accumulated enough review data: switch the review-gate mode to `advisory` on a comparable project (same operator), keep the same logger, and compare false-promotion rate and decision time against the `blocking` baseline. Add a promotion-reversal event so false-promotion is measurable. See [proposal-31](../proposals/31-configurable-review-gate-mode.md).

**Exit criteria.** The vault stops being a place you build and becomes a place you write from. The system runs without daily babysitting. The human shows up for review and synthesis; everything else flows. Three months of five-signal log data is available for retrospective analysis.

### Phase 4 — Multi-device · When a second device enters regular use

**Goal.** Extend Memoria to a second machine without fragmenting dispatch ownership or violating profile permission boundaries. This phase is triggered by need — a second device entering regular use, or batch ingest needing to run overnight — not by a calendar milestone.

**Steps.**

1. **Choose a deployment pattern.** See [Deployment options](deployment.md) for the full comparison. `local-mesh` (Syncthing, peer-to-peer) suits most setups; `always-on` (Syncthing + VPS) is for unattended overnight ingest. Pick based on whether the secondary device is always reachable.
2. **Determine the secondary device's role.** Install only the profiles that device's role justifies. `memoria-socratic` is the safe baseline for any secondary. Add Mapper, Writer, or Verifier only for explicit, justified use cases. Never install Librarian, Coder, or Linter on a secondary — these profiles own state that must not be duplicated across devices.
3. **Keep all seven profiles and dispatch ownership on the primary.** The primary is the single source of truth for card dispatch. A secondary that runs Librarian or issues dispatch commands creates split ownership and audit gaps.
4. **For developer secondaries only:** install all seven profiles, but isolate with `HERMES_HOME` pointed at a test vault — never the production vault. This is the one exception to the rule above, and the isolation is what makes it safe.
5. **Verify sync before running any profile on the secondary.** Confirm vault files are in sync (Syncthing status: up-to-date), audit log is intact, and board state matches the primary before the first card is claimed on the secondary device.

**Exit criteria.** The secondary device runs its assigned profiles without touching dispatch. Vault state stays in sync across devices. The audit log shows no gaps or duplicate card claims. The primary remains the sole dispatch owner.
