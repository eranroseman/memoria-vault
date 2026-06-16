---
release: v0.1.0-alpha.5
status: complete     # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan — v0.1.0-alpha.5
parent: Releasing
nav_order: 2
---

# Release plan — v0.1.0-alpha.5

**Current status: alpha.5 is complete as an internal checkpoint.** This is not a tagged GitHub
Release. The headline deliverable is the **Project gate** — the
fourth navigation gate (ADR-70's deferred slot), shipped as the *expanded v1 cut* now captured in
ADR-77, ADR-78, and ADR-79. The dashboard-risk spike, deterministic Project-gate spine, PI surface,
instrumentation, thin deny-assertion slice, and live Obsidian E2E validation are complete. The
deferred backlog behavior slices were removed from the alpha.5 milestone rather than treated as
blockers. `released:` flips to `true` only for a tagged release; this checkpoint closes at `status:
complete`, `released: false`.

As of 2026-06-16, every alpha.5 gate/stage issue under
[Release v0.1.0-alpha.5 (#584)](https://github.com/eranroseman/memoria-vault/issues/584) is closed:
G1-G6 and S0-S5. The remaining open issues that were once considered for alpha.5 are explicitly
rolled forward as deferred/superseded follow-ups, including
[#154](https://github.com/eranroseman/memoria-vault/issues/154),
[#381](https://github.com/eranroseman/memoria-vault/issues/381),
[#344](https://github.com/eranroseman/memoria-vault/issues/344),
[#370](https://github.com/eranroseman/memoria-vault/issues/370),
[#372](https://github.com/eranroseman/memoria-vault/issues/372),
[#374](https://github.com/eranroseman/memoria-vault/issues/374),
[#415](https://github.com/eranroseman/memoria-vault/issues/415), and
[#611](https://github.com/eranroseman/memoria-vault/issues/611).

## 1. Scope — what this release is

alpha.5 builds the **Project gate**: a project is a bounded research inquiry that drives an
argument toward a defended (or falsified) thesis, and the gate's job is to know **when to stop**
(saturation) — not to generate endless work. The gate's *logic* is deterministic and auditable
(every load-bearing mechanism is an Operation over the argument graph, in the same trust class as
the contradictions and knowledge-map views); its *inputs* are PI-authored or agent-proposed, gated
by review. This release ships the **expanded v1 cut** — everything that is deterministic or
optional-and-free, drawing the line on the architecture's real fault line (inference and structural
assumptions), not on a labor budget. It also clears a set of cheap, unblocked backlog slices and
folds one coordinated ADR housekeeping pass. It explicitly does **not** build the full ephemeral
test-env harness (its own effort, ADR-77/78), the inference tier, or anything gated on real-corpus
calibration or always-on infrastructure (§5).

## 2. Definition of done — gates

v0.1.0-alpha.5 ships when **every gate sub-issue under
[Release v0.1.0-alpha.5 (#584)](https://github.com/eranroseman/memoria-vault/issues/584) is met.**
Definitions:

| Gate | Proves | Verified by | Issues |
| --- | --- | --- | --- |
| G1 | Decisions are recorded: gate-trio ADRs + adr-update housekeeping/retirements; the §13.1 conservative maturity default is set; the §D3 spike is resolved (native view or fallback). | S0 + ADR index | Gate [#588](https://github.com/eranroseman/memoria-vault/issues/588); implementation [#577](https://github.com/eranroseman/memoria-vault/issues/577), [#576](https://github.com/eranroseman/memoria-vault/issues/576) |
| G2 | Spine artifacts exist: `thesis` + `project` note types, templates, `projects/<slug>/` scaffold, gated lifecycle. | S1/S2 | Gate [#589](https://github.com/eranroseman/memoria-vault/issues/589); implementation [#578](https://github.com/eranroseman/memoria-vault/issues/578) |
| G3 | The deterministic engine works and is safe: structural-impact Operation with write-only-on-change materialization + maturity gate; five gap kinds; saturation conditions 1–2 + refutation stamp; survey mode. | S1 | Gate [#590](https://github.com/eranroseman/memoria-vault/issues/590); implementation [#579](https://github.com/eranroseman/memoria-vault/issues/579), [#580](https://github.com/eranroseman/memoria-vault/issues/580) |
| G4 | A PI can drive a project end-to-end from Obsidian: start-a-project on-ramp, dashboards rendered, writing-emits-gaps, thesis supersession. | S3/S5 | Gate [#591](https://github.com/eranroseman/memoria-vault/issues/591); implementation [#581](https://github.com/eranroseman/memoria-vault/issues/581). Older broad follow-ups [#154](https://github.com/eranroseman/memoria-vault/issues/154) and [#381](https://github.com/eranroseman/memoria-vault/issues/381) are not alpha.5 blockers. |
| G5 | The gate is measurable: attention instrumentation emits PI-touch metrics into fleet-health (instrument-as-gate, the safety valve for the expanded cut). | S4 | Gate [#592](https://github.com/eranroseman/memoria-vault/issues/592); implementation [#337](https://github.com/eranroseman/memoria-vault/issues/337) |
| G6 | The cheap unblocked trigger-log slice lands; deferred behavior slices stay out of alpha.5. | S0/S1 | Gate [#593](https://github.com/eranroseman/memoria-vault/issues/593); implementation [#583](https://github.com/eranroseman/memoria-vault/issues/583), [#609](https://github.com/eranroseman/memoria-vault/pull/609). Deferred follow-ups [#344](https://github.com/eranroseman/memoria-vault/issues/344), [#370](https://github.com/eranroseman/memoria-vault/issues/370), [#372](https://github.com/eranroseman/memoria-vault/issues/372), [#374](https://github.com/eranroseman/memoria-vault/issues/374), [#415](https://github.com/eranroseman/memoria-vault/issues/415), and [#611](https://github.com/eranroseman/memoria-vault/issues/611) are later-checkpoint work. |

## 3. Validation — stages

The staged plan that turns `shipped` into `approved`; a release candidate re-runs **all stages green
from a fresh clone on a disposable vault** (`~/Memoria-test`, never `~/Memoria`). Stage state lives in
the sub-issues under [#584](https://github.com/eranroseman/memoria-vault/issues/584).

| Stage | Proves |
| --- | --- |
| S0 | static: new schemas parse + validate; `docs-doctor` green; `gen_adr_index` + adr-index hook fresh |
| S1 | component pytest: structural-impact Operation, gap detectors, saturation, write-only-on-change materialization, lifecycle gating |
| S2 | dry-run: installer substitution + `projects/<slug>/` scaffold on a disposable vault |
| S3 | integration: dashboards render (native `registerBasesView` or fallback), Bases reads materialized props, start-a-project scaffolds from the Obsidian form |
| S4 | live/enforcement: the **negative deny-assertion** (a gated thesis→current routes through review, not a column drag) via the ADR-28 plugin; PI-touch metrics land in fleet-health |
| S5 | E2E: a project from question → thesis → argument graph → gaps → saturation → outline, driven from Obsidian (the thin test-env slice, [#582](https://github.com/eranroseman/memoria-vault/issues/582)) |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers are** any open gate/stage
sub-issue under [#584](https://github.com/eranroseman/memoria-vault/issues/584), plus any open
High-priority blocker in the [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).
The one hard sequencing fact: **[#576](https://github.com/eranroseman/memoria-vault/issues/576)
(the §D3 spike) gates the dashboard surface** — resolve it first; the data model proceeds regardless.

## 5. Out of scope (deferred)

Deliberately later, each for a named reason (per-artifact deferred set lives in the deferred-status ADRs):

- **The full ephemeral test-env harness** (ADR-77 / ADR-78) — its own effort, carrying the external
  local-model spike (G2/G3 there). alpha.5 ships only the thin validation slice
  ([#582](https://github.com/eranroseman/memoria-vault/issues/582)).
- **The inference tier** — tier-3 semantic impact; any LLM judging the gate. Breaks the auditability the
  gate rests on.
- **Authoring-burden surface** — a `warrant` *mandate* and the unstated-warrant gap (the attribute ships
  optional); tier-3 quality lenses as computed gates (CRAAP filter, PICO-coverage check).
- **Structural breaks** — multi-thesis projects; auto-promotion of gated transitions.
- **ADR-61 nightly automation** — adoption conditions unmet; the gate uses on-demand find instead.
- **Calibration/corpus-blocked** — [#379](https://github.com/eranroseman/memoria-vault/issues/379),
  [#559](https://github.com/eranroseman/memoria-vault/issues/559),
  [#562](https://github.com/eranroseman/memoria-vault/issues/562),
  [#560](https://github.com/eranroseman/memoria-vault/issues/560),
  [#561](https://github.com/eranroseman/memoria-vault/issues/561).
- **Always-on / transport** — [#382](https://github.com/eranroseman/memoria-vault/issues/382),
  [#181](https://github.com/eranroseman/memoria-vault/issues/181),
  [#383](https://github.com/eranroseman/memoria-vault/issues/383).
- **Research / no act-now driver** — [#188](https://github.com/eranroseman/memoria-vault/issues/188),
  [#192](https://github.com/eranroseman/memoria-vault/issues/192),
  [#193](https://github.com/eranroseman/memoria-vault/issues/193),
  [#220](https://github.com/eranroseman/memoria-vault/issues/220),
  [#187](https://github.com/eranroseman/memoria-vault/issues/187).

**Completed precondition:** alpha.4 closeout is done — [#296](https://github.com/eranroseman/memoria-vault/issues/296),
[#414](https://github.com/eranroseman/memoria-vault/issues/414), and
[#527](https://github.com/eranroseman/memoria-vault/issues/527) are closed, so they do not block alpha.5.

## 6. Known limitations (state in the release notes)

- The gate's logic is auditable; its **conclusions are only as good as the argument graph it runs over**
  — a mis-typed `supports` or missing `contradicts` yields precise nonsense. The gate cannot verify its
  own inputs.
- **Impact/saturation are dark below the maturity threshold** (most of a small project's life). The
  dashboard displays low confidence there by design; orientation falls back to scope-overlap.
- **Materialized derived props are a cache, not live** — Bases has no auto-refresh; the dashboard shows
  `computed_at` and stale values read as stale.
- The dashboard rendering tech depends on `registerBasesView`; if the spike fails, the surface ships as a
  generated read-only render (the data model is unaffected).
- `warrant` ships as an optional attribute only; the gate does not yet judge or require warrants.

## 7. Cut procedure

1. **Every gate + stage sub-issue closed** under [#584](https://github.com/eranroseman/memoria-vault/issues/584); required CI green on `main`; no open High-priority blocker.
2. **Re-run all stages from a fresh clone** on a disposable vault (`~/Memoria-test`) → all green; record evidence in the sub-issues / Actions artifacts.
3. **Retire-sweep the ADRs** — already completed in WS-A; no follow-up ADR-retirement PR remains for alpha.5.
4. **Merge the release-please "Release v0.1.0" PR** (folding §6 known-limitations into the notes) — or, for this internal checkpoint, skip the tag.
5. **Set frontmatter** — internal checkpoint: `status: complete`, `released: false`.
6. **Delete `tmp/`** design notes (`project-starter.md`, `install-a-real-package.md`, `adr-update.md`, `test-env.md`, `exec-plan-0.1.0-alpha.5.md`) — promote anything durable into ADRs first.
7. **Close the milestone and [#584](https://github.com/eranroseman/memoria-vault/issues/584)**, rolling unfinished issues to the next checkpoint.

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Test-env harness | next | The ephemeral containerized harness (ADR-77/78) + local-model spike; automates L3/recovery/security/perf |
| Gate expansion | after one real project under PI-touch budget | Unlock authored gap kinds, tier-3 impact, PICO/FINER + CRAAP lenses |
| Packaging | trigger-gated | ADR-76 versioned-release + reconciling installer (deferred) |

Full phase steps and investigation detail belong in `release-plan-v0.1.0-alpha.5-appendix.md` if needed.

## 9. Appendix — what does NOT belong in this file

Detailed build steps and scratch design notes are retained under `tmp/` for closeout audit. Durable
decisions live in the ADRs; issue/PR evidence remains on GitHub. Long-tail phase/migration detail
would go in `release-plan-v0.1.0-alpha.5-appendix.md` if it becomes worth preserving.
