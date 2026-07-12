# Deferred-ADR implementability — independent re-verification

_Generated 2026-06-16 during alpha.6 and carried forward to alpha.8. Working
artifact (`tmp/`) — route durable actions to issues/ADRs before the next checkpoint
closes._

## What this is

A skeptical, code-level re-check of all 14 `deferred` ADRs at `main`, asking
**which can be implemented now vs. which still have a real blocker**. Every claim
was verified against the actual artifacts in `src/` — **not** against the ADR's own
`assumes:`/trigger text, and **not** trusting the now-pruned alpha.6 cadence-review
scratch note, which this pass both confirmed and corrected. Four independent agents
each owned a slice of the ADR set and read full files.

Headline corrections vs. the cadence-review scratch note:

- **Tier C is over-stated.** Three ADRs filed as "genuinely blocked" (66, 61, 80)
  each have a defensible buildable-now slice — in two cases the slice is the very
  prerequisite that makes the stated blocker measurable.
- **Several ADRs cite "reuse existing X" where X does not exist** (ADR-59's
  deterministic scorer, ADR-65's `vision_analyze` path). Those slices are blocked,
  not merely deferred. Tracked as ADR-status correction issues (see bottom).

## Implementable now (no real technical blocker)

| ADR | Buildable slice | Verified evidence |
|---|---|---|
| **74** plugin provenance | full slice: SHA-256/license lock manifest + CI doctor | 12 plugins under `src/.obsidian/plugins/`, clean 1:1 with `community-plugins.json`; no lock exists; `.github/workflows/lint-config.yml:63` only *excludes* plugins. Purely mechanical, zero external dep. |
| **41** advisory gate-mode | config flag + mode-conditional gate + promotion-reversal event | `REVIEW_MODE` is a hardcoded constant (`policy_mcp.py:97`); gate is `is_review_gated→dry_run` (308-310) + loudness deny (437-452). Small deterministic change. Study-gated, not blocker-gated. |
| **76** step 2 packaging | `[project]` table, `src/` un-hiding, console scripts, delete bootstraps | step-1 tooling landed; no `[project]` table; `src/.memoria` still dotted. Independent of deferred step-3 spine. |
| **35** misfire sweep | recurrence sweep over `classify.jsonl` → Inbox card → `skill-insights/` | `classify_miss`/`miss_kind` stamped live (`classify.py:168-173`), wired into `runner.py:158`. Substrate genuinely populated. General meta-memory remains usage-gated. |
| **39** mechanical Linter flag | citekey-present / `<250`-word / title=claim-sentence checks | no such detector in `detectors.py`; template-derivable. Low payoff today (0 claim notes). Soft rubric half stays corpus-gated. |
| **65** schema adds | `similar` relation value + `_aspects.{key_idea,method,outcome}` fields + shadow extract + exploration-traces | relation vocab is documentary-only (no enforcement in `detectors.py:396`); `_aspects` absent from `paper.yaml`. All additive. Threshold adoption corpus-gated. |
| **38** shadow ratchet | log qmd neighbours at file-time, never block | qmd-in-retrieval trigger **genuinely met** — runtime `{{QMD}}` MCP wired into librarian/writer/peer-reviewer `config.yaml`. (Runtime qmd, not dev `./.qmd/` — verified.) `find-duplicates` sweep and 0.8 gating remain blocked. |
| **58** (1 of 5) | read-only Obsidian Inspector | data sources present (`board-state.md`, `audit-log.md`, linter verdict). Other 4 surfaces need Todoist API / Quartz / unspecified handoff / net-new logic. |

## Tier C over-stated — these have a buildable-now slice

- **ADR-66** — premise is **false**: scores are not on `_proposed_classification`
  (empty stub, `ingest_paper.py:201`); they live only in `classify.jsonl`, never
  joined to operator accept/reject. The "wait 2 months for error data" clock cannot
  start because the data isn't logged. **Buildable now:** instrument the measurement
  substrate (write scores onto the proposal + a decisions log). Reframe from
  *blocked* → *instrument-now, calibrate-later*.
- **ADR-61** — every code dependency exists (find skill wired; a 5-job cron scaffold
  with heartbeat already runs; task routing). A `discovery-cron.sh` orchestrator is
  buildable now, dormant until the operator files exist. Blocker is
  precondition-for-*running*, not for-*building*.
- **ADR-80** — deny-slice shipped (verified, `tests/test_policy_gate_plugin.py:41`).
  Phase 1 is model-free by the ADR's own words; the remaining blocker is engineering
  effort, not an external prerequisite. Only Phase 2 (live GPU model) is genuinely
  cost-gated.

## Genuinely blocked (confirmed)

- **ADR-60 / ADR-63** — correctly dormant-by-design under single-researcher scope
  (ADR-24). Vault has only `_template/`, zero real projects, zero claim notes — even
  the single-vault "cross-project reading" cap has nothing to read. Both ADRs carry
  anti-premature-build guards, independently confirmed by absent infra. Unblock = a
  real second vault/device/≥3 projects.
- The remaining Tier-B gated slices stay gated for the stated reasons:
  ADR-59 learning-to-rank (≥300 decisions), claim-sentence classifier (pilot+FP),
  prose metrics (the LLM-judge export gate is not live); ADR-38 confident gating
  (corpus); ADR-65 figure-informed aspects (no vision path exists).

## Stale-assumption items → ADR-status correction issues

These are ADR-text accuracy defects found during verification (not implementation
gaps). Each gets a durable tracker issue:

1. **ADR-59** claims "the existing `[!suggestions]` weighted scorer (embedding-sim +
   citation-graph overlap + topic-tag overlap)" and "No new subsystems are mandated —
   most items reuse machinery already present (the `[!suggestions]` scorer …)". **No
   such deterministic scorer exists** — ranking is an LLM skill
   (`catalog-rank-candidate/SKILL.md`). The discovery-scorer displacement is itself
   unbuilt, not reusable machinery. (link.py ID-first pass + `recorded_by_name`
   logging claims *are* accurate.)
2. **ADR-65** treats Hermes `vision_analyze` as an "available-but-unwired" path ready
   to adopt — **no such path exists in this repo's ingest code** (grep = ADR/scratch
   only). Also: the ADR's `supports`/`contradicts` baseline is behind the deployed
   skills — `extends` already ships in `link-suggest-claim/SKILL.md`.
3. **ADR-76** "delete the **11** `__file__` bootstraps" is stale — ~17 `sys.path`
   sites across 13 files at HEAD. And load-bearing decision 2 frames "extract a
   genuine, tiny, standalone policy core" as future work, but it **already exists**
   (`src/.memoria/memoria_runtime/policy/`, imported by `policy_mcp.py:51`). What
   remains is the gate shim vendoring it instead of `sys.path`-reaching.
4. **ADR-39** re-entry trigger path `30-synthesis/01-claims/` is stale — the real
   claim-note home is `notes/claims/` (`detectors.py:51` TYPE_HOME).

## Method note

Standing caveat carried from the cadence review: this checkout is a clean scaffold
(0 claims, 0 papers, 0 real projects). Every trigger gating on corpus size or usage
(`50+ claims`, `≥300 decisions`, `2 machines`, `3 projects`) cannot be exercised
here — those remain usage-gated against the live vault by definition.
