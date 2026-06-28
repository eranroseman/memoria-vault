---
release: v0.1.0-alpha.8
status: complete     # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan — v0.1.0-alpha.8
parent: Releasing
nav_order: 2
---

# Release plan — v0.1.0-alpha.8

**Current status: complete internal checkpoint.** alpha.8 is the **runtime-foundations &
observability** checkpoint: it implemented every issue marked
`Readiness: Ready` in the Memoria Issue Tracker project.
`released:` in the frontmatter is the formal-release machine flag: it flips to
`true` only for a tagged GitHub Release. Like alpha.5-alpha.7, alpha.8 is an
**internal untagged checkpoint**: `status: complete`, `released: false`, no
release-please PR, no tag, and no GitHub Release.

## 1. Scope — what this release is

alpha.8 delivers the **runtime foundation and observability layer** that the
clean-slate logging/telemetry design (ADRs 104–106) and the ADR-76 packaging
decision require before any feature work builds on them. It lands, as a sequence of
small behavior-preserving PRs, the ADR-76 package spine and shared runtime helpers,
the security-sensitive policy/structural/ingest/installer module splits, the
content-light diagnostic plane and cost/disposition analytics, the read-only
Inspector and exploration-trace capture, the shadow-only similarity/calibration
telemetry, the day-1 empty-state polish, the Zotero→catalog capture fix, and the CI
provenance + opt-in live-Hermes test hardening. The boundary: this checkpoint is
**refactor + observability + telemetry-shadow plus two already-accepted read-only
surfaces**, not new autonomous behavior. No calibrated enforcement, no
auto-merge/auto-block, no relation-vocabulary expansion, and no
installer-distribution (tarball/signing) work — those stay deliberately later.

The in-work ExecPlan was deleted at closeout after its durable decisions and
evidence were routed to ADRs, reference docs, validation issue comments, and
[`validation-log.md`](validation-log.md).

## 2. Definition of done — gates

v0.1.0-alpha.8 ships when **every gate sub-issue under [Release v0.1.0-alpha.8](https://github.com/eranroseman/memoria-vault/issues/740) is closed.**
Each gate is a yes/no verdict over a cluster of the Ready issues. Definitions:

| Gate | Proves | Verified by | Gate issue · Work issues |
| --- | --- | --- | --- |
| G1 | **Package spine.** A fresh checkout runs an editable install through a `memoria.*` import root; pytest and e2e-smoke pass; every retained `sys.path.insert` is documented. | S0 + S1 + S3 | #741 · #727 |
| G2 | **Shared runtime helpers.** Frontmatter/JSONL/timestamp/vault-IO helpers are centralized; duplicate implementations are removed from ≥3 production modules; helper edge-case unit tests pass. | S1 | #742 · #728 |
| G3 | **Security-sensitive splits, behavior-preserving.** policy MCP is split into decision/audit/engine/server with every security invariant intact; structural-impact/ingest/installer hotspots are split with no semantic change. | S1 + S3 + S4 | #743 · #729, #730 |
| G4 | **Test harness & CI doctors.** e2e assertions move into importable Python helpers behind the unchanged shell entrypoint; the bundled-plugin provenance doctor runs in the required path; the opt-in live-Hermes test-l2 smoke ships documented and non-blocking. | S0 + S1 + S2 + S5 | #744 · #731, #686, #688 |
| G5 | **Observability planes.** The content-light diagnostic plane writes redacted, rotated, out-of-vault diagnostics with a redaction self-test; cost/disposition analytics emit with a fail-closed cost doctor and a joined-cost fixture. | S1 + S4 | #745 · #736, #737 |
| G6 | **Shadow telemetry & calibration (no enforcement).** Pre-file similarity runs report-only with shadow telemetry; the hybrid-score calibration threshold spec is filled and `calibration.yaml` extended; no auto block/merge and no ungrounded threshold ship. | S1 + S4 | #746 · #370, #379 |
| G7 | **Inspector & exploration capture.** The read-only Obsidian Inspector (ADR-84) and exploration-trace capture (ADR-100) are implemented per their accepted ADRs. | S1 + S3 + S5 | #747 · #697, #713 |
| G8 | **Day-1 UX & capture correctness.** All four gate dashboards read as intentional when empty with agreed first-run guidance; `capture zotero` adds to the catalog. | S2 + S5 | #748 · #690, #660 |
| G9 | **Research input routed.** The Obsidian project-management survey is delivered as adopt/borrow/reject findings and routed to issues/ADR, not left in scratch. | S0 (doc review) | #749 · #329 |

`#611` (ADR-65 shadow proposers) was `Ready` but **already closed** (2026-06-19);
its work is folded into the G6 telemetry baseline and is not re-scoped here.

## 3. Validation — stages

The staged test plan that turns `shipped` into `approved`. A release candidate must
re-run **all stages green from a fresh clone** on a clean target box (track the runs
in the stage sub-issues under the release parent issue).

| Stage | Proves | Stage issue |
| --- | --- | --- |
| S0 | `static-contract`: editable-install metadata parses; `docs_doctor`, `status_doctor`, `agents_doctor`, `check_test_refs`, adr-index, cspell clean; plugin-provenance lock validates. | #756 |
| S1 | `component`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/` green, including new helper, policy-split, diagnostic-redaction, and cost-join tests; bare-import smoke imports pure decision modules without the MCP SDK. | #757 |
| S2 | `vault-assembly`: `bash scripts/e2e-smoke.sh` green (stage names unchanged); disposable-vault build carries gates, empty-state copy, plugin lock, and CSS snippets. | #758 |
| S3 | `workflow-replay`: model-free ADR-80 Phase 1 replay asserts expected artifacts, deny audit row, and forbidden-file absence after the splits. | #759 |
| S4 | `runtime-integration`: live policy-gate audit row, diagnostic/cost capture, and shadow telemetry observed against a disposable vault (opt-in `scripts/test-l2.sh`). | #760 |
| S5 | `release-acceptance`: fresh-vault GUI pass — empty states, Inspector, Zotero capture, and exploration-trace surfaces behave in the runtime vault. | #761 |

## 4. Blockers

None at closeout. All alpha.8 gate and stage sub-issues under
[Release v0.1.0-alpha.8](https://github.com/eranroseman/memoria-vault/issues/740)
were closed, and no open issue remained assigned to the `v0.1.0-alpha.8` milestone.

## 5. Out of scope (later)

- **Calibrated enforcement / tuning** of pre-file similarity — stays report-only;
  enforcement is #562 (`Readiness: Later`).
- **Score-* map skills and the diversity reserve** (#381, #344) — gated on the #379
  threshold spec shipping first.
- **Installer distribution** (tarball publishing, signing, copy-install) — ADR-76
  schedules it separately; alpha.8 only does the import/package spine.
- **Updater/download automation** for bundled plugins — gated behind the #686
  provenance doctor being stable.
- **Relation-vocabulary expansion, automatic `_aspects` writes, auto-merge/auto-block**
  — telemetry-shadow only this checkpoint (ADR-65).
- **The projector engine, spatial/Canvas axis, and edge-authoring "relate" control** —
  deferred in [ADR-81](../../adr/81-persistent-gate-dashboards.md).

## 6. Known limitations (state in the release notes)

- Limitation: Pre-file similarity is **report-only**. Impact: humans see neighbour
  suggestions but nothing is auto-merged or blocked. Workaround: none needed.
  Tracking: #370 / #562.
- Limitation: Hybrid scores ship **only where their thresholds are filled**. Impact:
  score-* skills (#381) and the diversity reserve (#344) stay out until #379 lands.
  Workaround: none. Tracking: #379.
- Limitation: Diagnostics are **local, disposable, and content-light**. Impact: no
  raw payloads are retained; deep debugging needs a user-triggered redacted bundle.
  Workaround: generate a redacted bundle on demand. Tracking: #736 / ADR-105.
- Limitation: The live-Hermes `test-l2` smoke is **opt-in and non-PR**. Impact: live
  agent-wiring regressions are not caught by required CI. Workaround: run
  `scripts/test-l2.sh` manually. Tracking: #688 / ADR-29.

## 7. Documentation integrity

Before the release candidate is approved, complete a fresh documentation sweep per
the template's seven checks (coverage, single-source-of-truth, Diataxis placement,
Related links, terminology/glossary drift, third-party/example freshness, ADR
capture). For alpha.8 specifically: ADR-76, ADR-29, ADR-65, ADR-84, ADR-100, and
ADRs 104–106 must match the shipped implementation, and `docs/reference/policy-mcp.md`,
`docs/reference/installer.md`, `docs/reference/operations.md`, `docs/testing/README.md`,
and `docs/testing/verification-matrix.md` must reflect the moved module paths and new
commands. Group findings Critical / Major / Minor with `file:line` citations and the
checker summary.

## 8. Runtime readiness

Record runtime evidence for each target environment per the template's seven checks
(fresh clone, installer target, sandbox refresh, WSL/Linux host, Hermes profiles,
local services, GUI acceptance). alpha.8 specifically must prove: an editable install
from a fresh checkout (#727); the `~/Memoria-test` sandbox refreshed after the
installer split (#730); a live policy-gate audit row plus diagnostic/cost capture
against a disposable vault (#736/#737/#688); and a fresh-vault GUI pass for empty
states, Inspector, Zotero capture, and exploration trace. Production
(`memoria-private`) stays hands-off.

## 9. Release close-out sweep

Before closing this internal checkpoint, run the template's close-out sweep: review
every tracked `tmp/` file (including this release's ExecPlan), move durable content
into ADRs/system/reference/how-to/explanation docs, move any unfinished scratch to
the next folder, delete `tmp/` only after disposition, retire-sweep any ADR this
release dissolves, close/roll-forward issues and the release parent issue, and
fast-forward the dedicated main checkout with a clean status.

## 10. Cut procedure

This checkpoint follows the untagged internal path:

1. **Every gate + stage sub-issue closed** under the release parent issue; required
   CI green on `main`; no open High-priority blocker.
2. **Re-run all stages from a fresh clone** on a clean target → all green; record
   evidence in the sub-issues or Actions artifacts.
3. **Complete §7 documentation integrity, §8 runtime readiness, and §9 close-out sweep.**
4. **Internal checkpoint path:** do not cut a tag or GitHub Release. Preserve closeout
   evidence in a `validation-log.md`, keep the durable decisions in their ADRs, and
   set this file's frontmatter to `status: complete`, `released: false` after the
   release parent issue is closed.
5. **Close the milestone and the release parent issue**, rolling any unfinished issues
   to the next checkpoint.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Calibrated enforcement | After #379 threshold spec ships | Promote pre-file similarity from shadow to enforced (#562); ship score-* skills (#381) + diversity reserve (#344) |
| Installer distribution | ADR-76 next slice | Tarball publishing, signing, copy-install delivery |
| Bundled-plugin updater | After #686 doctor is stable | Updater/download automation on top of the provenance doctor |
| Projector engine & spatial axis | Trigger-gated (ADR-81) | Extend board mirror; projected telemetry bases; argument-graph canvas |

## 12. Appendix — closeout disposition

The tracked `tmp/` ExecPlan was removed at closeout. Durable outcomes are preserved
in the merged PRs, ADRs, issue comments, and [`validation-log.md`](validation-log.md);
unfinished follow-on work remains in GitHub issues with post-alpha.8 readiness.
