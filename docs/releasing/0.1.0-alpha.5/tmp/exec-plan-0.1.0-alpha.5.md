# ExecPlan — v0.1.0-alpha.5 (the Project gate)

This is an ExecPlan: a single, self-contained, living document carrying the alpha.5 build from its
current state to a validated, observable result. It follows `.agents/templates/exec-plan.md`; see
`.agents/playbooks/exec-plan.md` for how to run it. Tracked release scratch — lives under the
alpha.5 `tmp/`, deleted before the checkpoint closes (durable decisions route into ADRs first).

## 0. Metadata

- **Task:** build the **Project gate** (fourth navigation gate, ADR-70's deferred slot) as the
  *expanded v1 cut*, plus the cheap unblocked backlog slices and one coordinated ADR pass.
- **Execution model:** one worktree → branch → PR per workstream (`AGENTS.md` §1/§2). Structural
  and load-bearing changes land before the broad UI surface.
- **Milestone:** `0.1.0-alpha.5` (#6) — internal checkpoint. Readiness:
  [Release v0.1.0-alpha.5 (#584)](https://github.com/eranroseman/memoria-vault/issues/584).
- **Design of record:** `docs/releasing/0.1.0-alpha.5/tmp/project-starter.md` (gate);
  `…/tmp/adr-update.md` (ADR housekeeping); `…/tmp/test-env.md` §3 (the deny-assertion).
- **Related ADRs:** new — Project gate / thesis-type / argument-graph+`warrant`; amends
  ADR-68/70/61/23/62; retires ADR-17/34/40; reuses ADR-8/52 (relations), ADR-9 (contradictions),
  ADR-10 (supersession), ADR-48 (Librarian find), ADR-49 (Bases), ADR-50 (lifecycle), ADR-51 (gap
  card), ADR-25 (audit), ADR-28 (write gate), ADR-62 (measurement).
- **Issues:** WS-0 #576, WS-A #577, WS-B #578, WS-C #579, WS-D #580, WS-E #581, WS-F #337,
  WS-H #582, WS-G #583; folds #154 #381 #374 #372 #344 #370 #415.
- **Started:** 2026-06-15 · **Last updated:** 2026-06-16

## 1. Purpose / big picture

After this build a researcher can, from Obsidian: start a **project** (a bounded inquiry), author a
**thesis** (a provisional position that lives through `proposed → provisional → current → retracted`),
and watch a deterministic **structural-impact Operation** tell them which gaps actually move the
thesis and **when the argument is saturated enough to stop** — inverting the open-ended "keep finding
more" treadmill into a signal that argues for stopping when warranted. Falsifying a thesis (`retracted`
+ the subgraph that refuted it) is a *finished* result, not a dead end. Everything the gate decides is
a computation over the argument graph (auditable, replayable); everything it *asserts as true* still
goes through PI review. The cost the gate relocates onto the PI is **measured** from day one
(attention instrumentation), so expansion past v1 is earned, not assumed.

## 2. Context and orientation

For a reader new to this repo:

- **Vault / runtime split.** The Python runtime lives in `src/.memoria/` and is copied into a vault's
  `.memoria/` by the platform installer. Windows production uses native `scripts/install.ps1` with a
  native Hermes home and vault; Linux/WSL testing uses `scripts/install.sh`. Vault tests run on a
  disposable sandbox (`~/Memoria-test` or `%USERPROFILE%\Memoria-test`), **never the production vault**.
- **PI** = the human owner. **PI direct-access rule:** every feature is reachable from the Obsidian UI
  directly, not only via CLI.
- **Lanes / gate.** Agents act only through MCP servers; the policy-gate plugin
  (`src/.memoria/plugins/memoria-policy-gate/`) hard-denies disallowed tool calls (MCP-only sandbox).
  Agents propose; the PI promotes; nothing auto-infers (ADR-10/48/51).
- **The two graphs (the central insight, project-starter §2).** (1) the **descriptive knowledge map**
  — topology of what exists; (2) the **argument graph** — the `supports`/`contradicts` subgraph
  (ADR-8/52) rooted at the thesis. The **outline derives from the argument graph, not the topology** —
  that is what moves the gate from "organizes knowledge" to "produces an argument."
- **Derived vs authored / Operation vs agent vs human** (project-starter §3). The map, structural
  impact, and saturation are **derived Operations**; the thesis is an **authored note** with a gated
  lifecycle; gaps are **agent-proposed, PI-promoted** cards (ADR-51).
- **Current state.** `projects/` ships empty (ADR-68); `src/projects/` exists. No `thesis`/`project`
  note type exists (`claim.yaml` lifecycle is `[current, retracted, archived]` — born canonical, which
  is *why* the thesis must be its own type). `map-scope-project` skill, `project-hints.yaml.example`,
  and the `frame-a-project` / `start-a-writing-project` how-tos already exist. `registerBasesView`
  reality is **unverified** (§D3) and gates the dashboard surface.

The **expanded v1 line** (the cut, decided with the PI): build everything *deterministic* or
*optional-and-free*; defer only the *inference tier* (tier-3) and *structural breaks* (multi-thesis,
auto-promote). `warrant` ships as an **optional attribute** with the unstated-warrant gap **off**.

## 3. Plan of work

Sequenced structural-first; each workstream is its own worktree → branch → PR.

- **WS-0 — pre-work spikes (#576), gating.** §D3 `registerBasesView` spike (native view vs generated
  fallback); §13.1 conservative maturity-threshold default; §13.4 materialization shape (index-note if
  the custom view is built, else per-note stamps). The data model proceeds regardless; only the
  *rendering* (WS-E) waits on §D3.
- **WS-A — ADR pass (#577).** One coordinated `docs/adr/` PR: the gate-trio ADRs + adr-update §1/§5
  (retirements, doc-integrity, amendments). `gen_adr_index` green.
- **WS-B — schema + templates (#578).** `thesis.yaml`/`project.yaml` + templates + `projects/<slug>/`
  scaffold; derived-property fields; optional `warrant`; `gap_type`; CEBM enum; PICO/FINER + output_mode.
- **WS-C — two graphs + structural-impact Operation (#579).** Traversal, impact/on_path/saturation,
  maturity gate + scope-overlap cold-start floor, **write-only-on-change** materialization + `computed_at`.
- **WS-D — gap taxonomy + saturation (#580).** Five gap kinds (three shown, two advisory-above-maturity),
  thesis-relative ranking; saturation 1–2 + one-click refutation stamp; survey-mode coverage saturation.
- **WS-E — PI surface (#581).** start-a-project on-ramp (#154); dashboards (WS-0 outcome);
  writing-as-gap-generator; thesis supersession (mark-don't-invalidate). map:graph-claims/canvas-hub (#381).
- **WS-F — instrumentation (#337).** Attention metrics → fleet-health (the instrument-as-gate budget).
- **WS-G — cheap slices, parallel small PRs.** #374 `review_mode` stamp, #372 mechanical checklist,
  #344 diversity reserve, #370 shadow ratchet, #415 ADR-65 doc-fix, #583 start-now logs.
- **WS-H — thin test-env slice (#582).** The negative deny-assertion + new-command coverage.

Dependency edges: WS-A → WS-B → WS-C → WS-D → WS-E; WS-0 spike → WS-E rendering; WS-F and WS-G run in
parallel from the start; WS-H last (needs the new commands).

## 4. Concrete steps

1. **Isolate each workstream** (`AGENTS.md` §1) — a fresh worktree + branch per workstream, off latest
   `origin/main` (do **not** switch `~/memoria-vault`'s own checkout):

   ```bash
   git fetch origin
   git worktree add ~/mv-<ws> -b feat/alpha5-<ws> origin/main
   cd ~/mv-<ws>
   ```

2. **Pick the next workstream in §3 order.** Read its issue body + the cited `project-starter.md`/
   `adr-update.md` sections. WS-0 and WS-A land first; WS-B–E are the spine; WS-F/WS-G parallel; WS-H last.

3. **Implement against the design of record**, verify per §5 with focused tests (`scripts/test.sh`) and
   an Obsidian-UI check where the PI direct-access rule applies (WS-E especially).

4. **Update this plan** (§7 Progress, §8 Execution log, §9 Surprises) at every stop, then open the PR.

## 5. Validation and acceptance

Per `.agents/playbooks/verify-change.md` — observable claims, lowest-cost evidence, real transcripts.
All vault tests run on `~/Memoria-test`, never `~/Memoria`.

- **WS-0 / §D3:** Given the spike, when complete, then there is a recorded verdict that
  `registerBasesView` is usable (build a trivial view) **or** the generated-render fallback is chosen.
  *Prove with:* the spike note + a rendered minimal view or fallback artifact.
- **WS-A:** Given the ADR PR, when `python scripts/gen_adr_index.py` runs, then the index is fresh,
  every retired ADR (17/34/40) has `date_resolved`, ADR-17 has `superseded_by: [50,51]`, and no
  `assumes`/prose references 17/34/40 or superseded-37. *Prove with:* `gen_adr_index.py` + a grep.
- **WS-B:** Given the new schemas, when a `thesis`/`project` note is created and validated, then the
  lifecycle gate rejects a born-`current` thesis and accepts `proposed`. *Prove with:* schema
  self-test + a focused pytest.
- **WS-C:** Given a seeded argument graph, when the Operation runs, then `impact`/`on_path`/
  `saturation_state`/`graph_maturity`/`computed_at` are materialized **only on changed notes**, and
  off-path gaps read impact 0. *Prove with:* an Operation pytest asserting write-only-on-change + the
  off-path cut.
- **WS-D:** Given a mature thesis with no `addressed` `contradicts`, when gaps compute, then a
  **refutation** advisory fires; given a sparse graph, advisory kinds are hidden. *Prove with:* gap
  detector pytest at two maturity levels.
- **WS-E:** Given the start-a-project form **in Obsidian**, when submitted, then `projects/<slug>/`
  scaffolds with thesis + question artifacts and the result lands as a proposal. *Prove with:* an
  attended Obsidian check on `~/Memoria-test` + a scaffold pytest.
- **WS-F:** Given a resolved gate card, when it resolves, then time-on-gate / accept-rate land in
  fleet-health (no placeholder metric). *Prove with:* a metrics pytest + the rendered dashboard.
- **WS-H (the safety test):** Given a **known-deny** write, when driven through the ADR-28 plugin,
  then it is **blocked** with a deny audit row — the gate-fires property is proven, not inferred.
  *Prove with:* the negative-assertion harness on `~/Memoria-test`.
- **E2E (S5):** Given a fresh project, when driven question → thesis → argument graph → gaps →
  saturation → outline from Obsidian, then each transition produces its artifact and the saturation
  signal fires only when conditions 1–2 + the stamp are met. *Prove with:* the WS-H E2E run.

## 6. Idempotence and recovery

- **Safe to re-run:** each workstream is its own branch/PR; re-running an unstarted one is a no-op.
  The plan is regenerable from milestone `0.1.0-alpha.5` + #584.
- **Rollback:** `git worktree remove` a per-workstream worktree; revert the PR commit. WS-B (schemas)
  and WS-C (the Operation + materialization) are the load-bearing changes — land them behind their
  tests, and a bad materialization run is recoverable because it is write-only-on-change with
  `computed_at` (re-run recomputes; nothing is destroyed).

## 7. Progress

- [x] 2026-06-15 — ExecPlan + release-plan authored; milestone #6 + parent #584 + workstream issues
      #576–583 created; in-scope issues assigned. Execution started at WS-0.
- [x] WS-0 spikes (#576) — §D3 / §13.1 / §13.4 resolved in `tmp/ws-0-spikes.md`
- [x] WS-A ADR pass (#577)
- [x] WS-B schema + templates (#578)
- [x] WS-C structural-impact Operation (#579)
- [x] WS-D gap taxonomy + saturation (#580)
- [x] WS-E PI surface (#581) — core surface merged; #154 and #381 remain open/deferred follow-ups
- [x] WS-F instrumentation (#337)
- [x] WS-G cheap slices (#374, #372, #344, #370, #415, #583) — trigger-log slice complete;
      remaining deferred-behavior slices rolled forward out of the alpha.5 milestone
- [x] WS-H thin test-env slice (#582)

## 8. Execution log

- 2026-06-15 — Scope set with the PI: the **expanded v1 cut** (5 gap kinds, optional `warrant`, survey
  mode, CEBM enum, writing loop, start-now logs), cutting on the inference/structural fault line, not on
  a labor budget. Architectural calls go to the WS-A ADRs, not here. Test-env harness held out of scope
  (ADR-77/78, separate); only the deny-assertion slice rides alpha.5.
- 2026-06-15 — Three open decisions carried as in-plan gates (WS-0): §D3 spike first; §13.1 conservative
  default in the gate ADR; §13.4 index-note default was pending §D3.
- 2026-06-16 — WS-0 resolved. `obsidian@1.13.1` exposes `Plugin#registerBasesView`, so WS-E can
  build the dashboard as a custom Bases view. Set the conservative maturity default to a connected
  thesis-rooted component with at least 5 addressed relations, including at least 1 `supports` and
  1 `contradicts` edge. Choose the single generated index-note as the default materialization shape.
- 2026-06-16 — WS-A resolved in the ADR layer: added ADR-77/78/79 for the Project gate, thesis note
  type, and argument graph + optional `warrant`; retired ADR-17/34/40; amended the stale
  dependencies and doc-integrity notes called out in `adr-update.md`; regenerated the ADR index.
- 2026-06-16 — WS-B resolved the schema/template spine: added `project` and `thesis` schemas and
  templates, Project scaffold directories, Project-derived cache fields, `gap_type`, optional
  evidence level on sources, `ingest_status` on papers, and schema-shaped Modal Forms project-start
  fields with parity tests.
- 2026-06-16 — WS-C added the deterministic Project structural-impact Operation. It traverses the
  thesis-rooted `supports`/`contradicts` graph, computes impact/on-path/maturity/saturation values,
  applies the conservative maturity threshold plus the scope-overlap cold-start floor, and writes a
  single generated Project gate index note only when derived values change.
- 2026-06-16 — WS-D extended the Project cache with gap taxonomy and saturation semantics: shown
  additive/conflict/fragility findings, maturity-gated structural/refutation advisories, the
  one-click PI `refutation_sufficiency` stamp for saturation condition 3, and survey-mode
  coverage-relative saturation.
- 2026-06-16 — WS-E added the PI-facing Project surface: QuickAdd/Modal Forms project scaffolding,
  Project gate cache refresh, thesis supersession with a lazy re-confirmation alert, a Project gate
  Bases dashboard, and Writer draft verification that stages visible knowledge-gap cards for
  ungrounded assertions.
- 2026-06-16 — WS-F made the review gate measurable: board export now emits deterministic blind
  re-review samples, the Obsidian resolve command appends `attention.jsonl` timing rows, the metrics
  aggregator writes time-on-gate / expand-to-accept / card-open-to-resolve / blind-sample fields into
  lane metric notes, and fleet-health renders those fields from `system/metrics/`.
- 2026-06-16 — WS-G trigger-log slice landed the cheap self-detecting signals without starting the deferred
  behavior: policy audit rows stamp `schema_version: 2` and `review_mode: blocking`, Inbox resolves
  append `triage.jsonl`, ambiguous classify rows mark `classify_miss`, ID-missing linker names append
  `linkage.jsonl`, and cron wrappers append `cron-heartbeat.jsonl` only after successful runs.
- 2026-06-16 — WS-H added the alpha.5 test-env safety slice: a component test loads the live
  `memoria-policy-gate` plugin, drives a known-deny `mcp_obsidian_vault_write` into
  `notes/claims/`, and asserts both a plugin block and a deny audit row; the new Project-gate
  QuickAdd/Modal Forms commands remain covered by the existing palette/form tests.
- 2026-06-16 — Merged the remaining alpha.5 validation slices on main (`b3a5474`): WS-F PR #608,
  WS-G trigger-log slice PR #609, and WS-H PR #610. Closed the S0/S1/S2/S4 validation stages and
  the G1/G2/G3/G5 gates; the then-open G4/G6/S3/S5 work was resolved in the later live-validation
  and backlog-split entries below.
- 2026-06-16 — S3 live Obsidian integration passed on `~/Memoria-test`: `Memoria: start project`
  scaffolded `projects/slug-bug/`, `Memoria: refresh project gate` refreshed
  `project-gate-index.md`, and `system/dashboards/project-gate.md` rendered Bases rows for the
  Project note and active thesis. S3 (#597) closed; G4 then waited only on S5 E2E (#599), which the
  next entry resolves.
- 2026-06-16 — S5 live Obsidian E2E passed on `~/Memoria-test`: a seeded `slug-bug` project moved
  from question/thesis through an argument graph with shown gap findings, closed its open
  high-impact gap, stamped `refutation_sufficiency: true`, recomputed `saturation_state: saturated`,
  and produced `projects/slug-bug/drafts/saturated-outline.md`. S5 (#599) and G4 (#591) are closed.
- 2026-06-16 — G6 closed after splitting the backlog honestly. The shipped alpha.5 scope is the
  trigger-log slice from #583/#609. Deferred/superseded behavior work was removed from the milestone:
  #154, #381, #344, #370, #372, #374, and #415. The remaining ADR-65 shadow-proposer row was split to
  #611 for a later checkpoint. No gate/stage blocker remains under #584.

## 9. Surprises & discoveries

- WS-0: the custom Bases view path is viable in the published Obsidian API, but it must be treated as
  a version-pinned pilot in WS-E rather than an untyped QuickAdd script surface.
- WS-A: ADR-62 was partly stale rather than wholly deferred. Fleet observability is already built via
  `metrics_aggregate.py` and `memoria-metrics`, so the ADR now records the harness family as accepted
  with only the remaining harnesses still waiting on cadence-review context.
- WS-B: the live ingest code already writes `ingest_status: enriched` and existing docs/tests reference
  `complete`, so the paper schema enum uses the shipped values (`tier0`, `enriched`, `complete`,
  `needs-human`) rather than the earlier tier1/tier2 wording.

## 10. Interfaces & dependencies

- **Schemas:** `src/.memoria/schemas/types/{thesis,project}.yaml` (new); optional `warrant` on the
  relations contract (ADR-8/52); `gap_type` on `gap.yaml`; CEBM enum on `source.yaml`; derived-property
  fields. Templates under `src/system/templates/`.
- **Operation:** new module under `src/.memoria/operations/` (twin of the contradictions/knowledge-map
  views) traversing frontmatter relations; materializes derived props **write-only-on-change** (ADR-25
  audit is append-only — a naïve per-component re-stamp is write amplification).
- **Dashboards:** `registerBasesView` (WS-0 verdict) or a generated read-only Canvas/markdown render.
- **PI surface:** QuickAdd/Modal Forms start-a-project (supersedes the old `40-workbench` path, #154);
  Writer lane + FAMA cite-check feed writing-as-gap-generator; ADR-28 plugin is the deny path (WS-H).
- **Find:** on-demand gap-pull via the existing Librarian `catalog-find-source` (ADR-48); **not** ADR-61.
- **Instrumentation:** `metrics_aggregate.py` + fleet-health (ADR-62) for PI-touch metrics (#337).

## 11. Artifacts & notes

- WS-0 spike result: `docs/releasing/0.1.0-alpha.5/tmp/ws-0-spikes.md`.
- WS-A decision records: `docs/adr/77-project-gate.md`,
  `docs/adr/78-thesis-note-type.md`, `docs/adr/79-argument-graph-and-warrant.md`.
- WS-B schema/template artifacts: `src/.memoria/schemas/types/project.yaml`,
  `src/.memoria/schemas/types/thesis.yaml`, `src/system/templates/project.md`,
  `src/system/templates/thesis.md`, `src/projects/_template/`.
- WS-C operation artifact: `src/.memoria/operations/processing/project/structural_impact.py`;
  focused coverage in `tests/test_project_structural_impact.py`.

## 12. Outcomes & retrospective

- **Shipped:** WS-0, WS-A, WS-B, WS-C, WS-D, WS-E core surface, WS-F, WS-H, and the WS-G trigger-log
  slice. Merged PRs: #603, #604, #605, #606, #607, #608, #609, #610.
- **Still open:** no alpha.5 gate/stage blockers. Deferred/superseded follow-ups intentionally left
  out of the checkpoint remain open outside the milestone (#154, #381, #344, #370, #372, #374, #415,
  #611).
- **Routed to:** decisions → the WS-A ADRs; readiness/scope → milestone #6 + #584; this plan holds no
  durable record of its own.
- **Lessons:** the Project gate works best as a deterministic Obsidian-visible cache: the tricky
  runtime failures were deployment/config drift (Modal Forms field shape, missing copied operations),
  not the structural-impact algorithm itself. Future checkpoint plans should include an explicit
  disposable-vault refresh step before live UI validation.
