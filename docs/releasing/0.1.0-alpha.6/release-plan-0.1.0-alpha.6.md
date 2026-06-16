---
release: v0.1.0-alpha.6
status: draft        # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan — v0.1.0-alpha.6
parent: Releasing
nav_order: 2
---

# Release plan — v0.1.0-alpha.6

**Current status: pre-release (draft).** alpha.6 turns the alpha.6 ADR audit's
findings into a checkpoint: make the **accepted** decisions that silently don't hold
actually hold, finish alpha.5's Project-gate navigation surface, and deliver the
roadmap's committed-next **ephemeral test-env harness (ADR-80, Phase 1)**. The single
biggest thing between here and cut is the harness build (the long pole); the
conformance fixes are small and mostly independent. `released:` in the frontmatter
flips to `true` only for a tagged GitHub Release — this internal checkpoint closes at
`status: complete`, `released: false`.

## 1. Scope — what this release is

alpha.6 is a **conformance-and-verification checkpoint** built on two pillars. **Pillar
one (Track A — re-implement approved goals):** the alpha.6 audit
([`tmp/adr-implementation-gap-analysis.md`](tmp/adr-implementation-gap-analysis.md))
read all 56 accepted ADRs against the built artifacts and found eight where the
accepted decision does not actually hold. alpha.6 closes the material ones — a runtime
security regression (the Obsidian-MCP bearer token rides plain-HTTP loopback,
contradicting ADR-31), two unenforced schema/query invariants (ADR-78 born-`current`
thesis, ADR-10 superseded-claim exclusion), the missing Project-gate **navigation
surface** that finishes alpha.5's headline (ADR-70/77), and the cheap docs/template/
supply-chain cleanups (ADR-07, ADR-73, ADR-74). **Pillar two (Track B — net-new):** the
model-free **Phase 1 test-env harness** (ADR-80) — the L0–L4 golden path via
seed→cassette that makes every future release re-runnable from a fresh clone. It
explicitly does **not** build the harness's live-model Phase 2, the deferred shadow/
instrument telemetry harvest (rolled to alpha.7, where the harness can seed a corpus to
measure), or anything gated on real-corpus calibration or always-on infrastructure
(§5).

## 2. Definition of done — gates

v0.1.0-alpha.6 ships when **every gate sub-issue under
[Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635)
is closed.** Definitions (state lives in the sub-issues, never in this table):

| Gate | Proves | Verified by | Issues |
| --- | --- | --- | --- |
| G1 | **Correctness & security conformance.** The three `bug`-labeled accepted-ADR gaps no longer hold: ADR-31 — the runtime serves the Obsidian MCP over verified HTTPS, the bearer token no longer travels plain loopback; ADR-78 — the schema rejects a born-`current` thesis and the promotion to `current` is review-gated; ADR-10 — `query`/`write` exclude superseded claims by default, with the claim `schema_version` bump. | S1 + S4 | Gate [#636](https://github.com/eranroseman/memoria-vault/issues/636); impl [#620](https://github.com/eranroseman/memoria-vault/issues/620), [#621](https://github.com/eranroseman/memoria-vault/issues/621), [#624](https://github.com/eranroseman/memoria-vault/issues/624) |
| G2 | **Project-gate navigation surface.** ADR-70/77 — Project is registered as the fourth switchable top-level workspace and is reachable as a gate from Obsidian (not link-only), finishing alpha.5's headline. The `registerBasesView` pilot stays deferred (ADR-77). | S3 + S5 | Gate [#637](https://github.com/eranroseman/memoria-vault/issues/637); impl [#622](https://github.com/eranroseman/memoria-vault/issues/622) |
| G3 | **Docs, template & supply-chain conformance.** ADR-07 — `system/templates/code-note.md` exists (or the stale reference is dropped); ADR-73 — the bare-`(ADR-NN)` rule is enforced in `docs-doctor` or the offending reference pages are fixed; ADR-74 — a static plugin provenance lock manifest (pinned version/commit/SHA-256 + license for the 12 vendored plugins) lands. | S0 | Gate [#638](https://github.com/eranroseman/memoria-vault/issues/638); impl [#627](https://github.com/eranroseman/memoria-vault/issues/627), [#626](https://github.com/eranroseman/memoria-vault/issues/626), [#585](https://github.com/eranroseman/memoria-vault/issues/585) |
| G4 | **Ephemeral test-env harness — Phase 1 (ADR-80).** The model-free L0–L4 golden path runs from seed→cassette (record/replay cassettes + the g9 zero-LLM spine + a seeded L4 path on `e2e-smoke.sh`); ADR-80's model-availability smoke check passes. The model is needed at record time, not run time. | S3 + S5 | Gate [#639](https://github.com/eranroseman/memoria-vault/issues/639); impl [#586](https://github.com/eranroseman/memoria-vault/issues/586) |

[#625](https://github.com/eranroseman/memoria-vault/issues/625) (ADR-20 capture
signals) is **documented as an upstream-Hermes known-limitation** (§6) and is **not** a
gate — the exporter is already wired and emits the moment the Hermes card-metadata
overlay appears.

## 3. Validation — stages

The staged plan that turns `shipped` into `approved`; a release candidate re-runs **all
stages green from a fresh clone on a disposable vault** (`~/Memoria-test`, never
`~/Memoria`). Stage state lives in the stage sub-issues (S0–S5 =
[#640](https://github.com/eranroseman/memoria-vault/issues/640)–[#645](https://github.com/eranroseman/memoria-vault/issues/645))
under [Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635).

| Stage | Proves |
| --- | --- |
| S0 | static: the new `code-note.md` template parses; the provenance lock manifest validates; `docs-doctor` green (including the new bare-code rule if added); `gen_adr_index` + adr-index hook fresh |
| S1 | component pytest: born-`current` thesis rejection + gated promotion; superseded-claim default filter in `query`/`write`; harness spine units (cassette record/replay, the g9 zero-LLM path) |
| S2 | dry-run: installer substitution incl. the new template + the Project workspace registration; cassette replay on a disposable vault |
| S3 | integration: Project workspace switches in Obsidian and Bases render; the harness L0–L4 cassette replay runs green |
| S4 | live/enforcement: the runtime serves the Obsidian MCP over HTTPS with `ssl_verify` (sandbox `~/.hermes` / memoria-test only) so the bearer token no longer rides plain loopback (#620). The born-`current` thesis rule is **content-aware** — enforced at schema/Linter time (S1), not via the path-based policy plugin |
| S5 | E2E: the harness golden path L0–L4 from a fresh clone; the Project gate driven end-to-end from Obsidian |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers are** any
open gate/stage sub-issue under [Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635), plus any open
High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1). Two hard facts
this release: **[#620](https://github.com/eranroseman/memoria-vault/issues/620) is the
one security regression** (a bearer token on plain loopback) and carries High priority;
and **[#586](https://github.com/eranroseman/memoria-vault/issues/586) (the harness) is
the long pole** — start it first, in parallel with the conformance work.

## 5. Out of scope (deferred)

Deliberately later, each for a named reason (per-artifact deferred set lives in the
deferred-status ADRs):

- **Harness Phase 2** — live-model L5, visual golden-diffs, chaos/perf. ADR-80 is
  phased; Phase 2 is GPU/model-cost-gated.
- **The shadow/instrument harvest → alpha.7** — [#370](https://github.com/eranroseman/memoria-vault/issues/370)
  (ADR-38 ratchet), [#611](https://github.com/eranroseman/memoria-vault/issues/611)
  (ADR-65 shadow proposers), [#416](https://github.com/eranroseman/memoria-vault/issues/416)
  (ADR-66 instrument), [#371](https://github.com/eranroseman/memoria-vault/issues/371)
  (ADR-35 misfire sweep). These are net-new dark-launch telemetry whose payoff is
  back-loaded: two of them run over claim/paper notes that don't exist on a clean
  scaffold, so they measure nothing until the Phase-1 harness can seed a corpus.
  Deferring them to alpha.7 is the cheapest value-per-hour cut.
- **Packaging (ADR-76)** — [#521](https://github.com/eranroseman/memoria-vault/issues/521).
  Its own issue guards against adding a `[project]` table early, and the audit found the
  "step 2" scope partly stale; revisit at cadence, not alpha.6.
- **Cross-vault / multi-machine** — [#410](https://github.com/eranroseman/memoria-vault/issues/410)
  (ADR-60), [#413](https://github.com/eranroseman/memoria-vault/issues/413) (ADR-63);
  dormant by design under single-researcher scope.
- **Calibration/corpus-blocked** — [#379](https://github.com/eranroseman/memoria-vault/issues/379),
  [#559](https://github.com/eranroseman/memoria-vault/issues/559),
  [#560](https://github.com/eranroseman/memoria-vault/issues/560),
  [#561](https://github.com/eranroseman/memoria-vault/issues/561),
  [#562](https://github.com/eranroseman/memoria-vault/issues/562).
- **Always-on / transport** — [#382](https://github.com/eranroseman/memoria-vault/issues/382),
  [#383](https://github.com/eranroseman/memoria-vault/issues/383),
  [#181](https://github.com/eranroseman/memoria-vault/issues/181).
- **Research / no act-now driver** — [#188](https://github.com/eranroseman/memoria-vault/issues/188),
  [#192](https://github.com/eranroseman/memoria-vault/issues/192),
  [#193](https://github.com/eranroseman/memoria-vault/issues/193),
  [#220](https://github.com/eranroseman/memoria-vault/issues/220),
  [#187](https://github.com/eranroseman/memoria-vault/issues/187).

## 6. Known limitations (state in the release notes)

- The harness validates **L0–L4 model-free via recorded cassettes**; L5 quality
  behavior is not yet exercised (Phase 2). A cassette can drift from live model
  behavior, and record-time refresh is manual.
- The superseded-claim filter is **default-on at `query`/`write`**; this changes default
  read behavior, and notes authored before the claim `schema_version` bump are read
  under the new default.
- The plugin provenance manifest is a **static lock** — there is no updater or CI
  provenance-doctor yet (deferred), so drift between the manifest and the vendored
  plugins is caught only by manual re-audit.
- **ADR-20 `disposition.jsonl` / `cost.jsonl` stay empty** pending the Hermes
  card-`metadata` overlay (upstream limitation, `docs/reference/telemetry.md`); the
  exporter emits the moment it appears.
- The Project gate is now a switchable workspace, but its custom `registerBasesView`
  pilot remains deferred (ADR-77) — it renders through the standard surface.

## 7. Cut procedure

1. **Every gate + stage sub-issue closed** under [Release v0.1.0-alpha.6 (#635)](https://github.com/eranroseman/memoria-vault/issues/635);
   required CI green on `main`; no open High-priority blocker (notably
   [#620](https://github.com/eranroseman/memoria-vault/issues/620)).
2. **Re-run all stages from a fresh clone** on a disposable vault (`~/Memoria-test`) →
   all green; record evidence in the sub-issues / Actions artifacts.
3. **ADR status maintenance.** The accepted-ADR gaps move PARTIAL→implemented (ADR-31,
   -78, -10, -70, -77, -07, -73); ADR-80 (Phase 1) and ADR-74 (static-manifest slice)
   move `deferred`→`accepted` with their remaining phases/slices noted. **Retire-sweep:**
   no question is dissolved by alpha.6, so the sweep is expected to be a no-op — confirm
   before cut.
4. **Merge the release-please PR** (folding §6 known-limitations into the notes) — or,
   for this internal checkpoint, skip the tag.
5. **Set frontmatter** — internal checkpoint: `status: complete`, `released: false`.
6. **Delete `tmp/`** design notes (the exec plan and the three audit scratch files) —
   promote anything durable into ADRs first.
7. **Close the milestone and [#635](https://github.com/eranroseman/memoria-vault/issues/635)**, rolling unfinished issues to
   the next checkpoint.

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Shadow & instrument harvest | alpha.7 | [#370](https://github.com/eranroseman/memoria-vault/issues/370) / [#611](https://github.com/eranroseman/memoria-vault/issues/611) / [#416](https://github.com/eranroseman/memoria-vault/issues/416) / [#371](https://github.com/eranroseman/memoria-vault/issues/371) dark-launch telemetry, now exercisable against a harness-seeded corpus; starts the calibration clocks |
| Harness Phase 2 | when GPU/model budget allows | live-model L5 + visual golden-diffs + chaos/perf (ADR-80) |
| Gate expansion | after one real project under PI-touch budget | authored gap kinds, tier-3 impact, PICO/FINER + CRAAP lenses |
| Packaging | trigger-gated | ADR-76 ([#521](https://github.com/eranroseman/memoria-vault/issues/521)) versioned-release + reconciling installer |

Full phase steps and investigation detail belong in
`release-plan-v0.1.0-alpha.6-appendix.md` if it becomes worth preserving.

## 9. Appendix — what does NOT belong in this file

The living build plan (workstreams, sequencing, per-issue steps) is
[`tmp/exec-plan-0.1.0-alpha.6.md`](tmp/exec-plan-0.1.0-alpha.6.md); the audit research
that produced this scope is the three `tmp/` scratch notes. Durable decisions live in
the ADRs; issue/PR evidence remains on GitHub. Long-tail phase/migration detail would go
in `release-plan-v0.1.0-alpha.6-appendix.md` if it becomes worth preserving.
