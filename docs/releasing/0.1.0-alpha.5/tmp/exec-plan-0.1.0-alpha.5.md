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
- **Issues:** WS-0 #576, WS-A #577, WS-B #578, WS-C #579, WS-D #580, WS-E #581, WS-H #582,
  WS-G #583; folds #154 #337 #381 #374 #372 #344 #370 #415.
- **Started:** 2026-06-15 · **Last updated:** 2026-06-15

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

- **Vault / runtime split.** The Python runtime lives in `src/.memoria/` and is rsynced into a vault's
  `.memoria/` by `scripts/install.sh`. Vault data is the Obsidian vault (`~/Memoria` runtime;
  `~/Memoria-test` sandbox — **never test against `~/Memoria`**).
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

- [ ] 2026-06-15 — ExecPlan + release-plan authored; milestone #6 + parent #584 + workstream issues
      #576–583 created; in-scope issues assigned. Execution can start at WS-0.
- [ ] WS-0 spikes (#576) — §D3 / §13.1 / §13.4 resolved
- [ ] WS-A ADR pass (#577)
- [ ] WS-B schema + templates (#578)
- [ ] WS-C structural-impact Operation (#579)
- [ ] WS-D gap taxonomy + saturation (#580)
- [ ] WS-E PI surface (#581, #154, #381)
- [ ] WS-F instrumentation (#337)
- [ ] WS-G cheap slices (#374, #372, #344, #370, #415, #583)
- [ ] WS-H thin test-env slice (#582)

## 8. Execution log

- 2026-06-15 — Scope set with the PI: the **expanded v1 cut** (5 gap kinds, optional `warrant`, survey
  mode, CEBM enum, writing loop, start-now logs), cutting on the inference/structural fault line, not on
  a labor budget. Architectural calls go to the WS-A ADRs, not here. Test-env harness held out of scope
  (ADR-77/78, separate); only the deny-assertion slice rides alpha.5.
- 2026-06-15 — Three open decisions carried as in-plan gates (WS-0): §D3 spike first; §13.1 conservative
  default in the gate ADR; §13.4 index-note default pending §D3.

## 9. Surprises & discoveries

- (fill as workstreams land — e.g. the §D3 spike outcome, since the whole dashboard surface depends on it.)

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

- (per-workstream transcripts pasted here as each lands — the §D3 spike result, the Operation pytest, the
  Obsidian attended-check for start-a-project, the deny-assertion transcript.)

## 12. Outcomes & retrospective

- **Shipped:** (fill as workstreams close — each maps to a merged PR.)
- **Still open:** (remaining gaps → keep their GitHub issues open; roll to the next checkpoint.)
- **Routed to:** decisions → the WS-A ADRs; readiness/scope → milestone #6 + #584; this plan holds no
  durable record of its own.
- **Lessons:** (fill at checkpoint close, before deleting this `tmp/` note.)
