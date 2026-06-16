# Deferred-ADR cadence review — implementable-now findings

Status: design scratch (alpha.6 `tmp/`), pre-scoping. Delete before the alpha.6
checkpoint closes; promote anything durable into ADRs / issues first.
Date: 2026-06-16.

## What this is

A skeptical pass over all 14 `deferred` ADRs at `main` (post-alpha.5), asking
**which can be implemented now vs. which still have a real blocker** — verifying
each ADR's stated trigger against the actual code, *not* trusting the ADR's own
`assumes:`/triggers (alpha.5 silently invalidated several). Tier C (genuinely
blocked) is summarised at the bottom; the implementable work is Tiers A and B.

The standing caveat: this checkout is a clean scaffold (`src/` has 0 claims, 0
papers, 0 projects). Every trigger that gates on **corpus size or usage**
(`50+ claims`, `≥300 triage decisions`, `2 machines`, `3 projects`) cannot be
judged here — it depends on the live `~/Memoria` vault and actual usage. Those
are Tier C.

Stale ADR trigger text corrected alongside this note: **ADR-38, ADR-41, ADR-35,
ADR-59, ADR-76** (see the cadence-review PR).

## Tier A — implementable now (no real technical blocker)

| ADR | Buildable now | Verified evidence | Notes |
|---|---|---|---|
| **41** Configurable review-gate mode | the `advisory` gate-mode behavior (a config flag + the gate honoring it) | `policy_mcp.py:96-97` already stamps `AUDIT_SCHEMA_VERSION=2` + `REVIEW_MODE="blocking"` — the non-backfillable attribution sliver shipped in alpha.5 | Only gate left is *wanting* the Path 2/3 comparison study; no missing mechanism. |
| **74** Plugin provenance manifest | the static lock manifest (plugin ID, repo, pinned tag, SHA-256, license, owned/patched flag) + a CI doctor | 12 vendored plugins under `src/.obsidian/plugins/`, **zero** SHA/license manifest today | Mechanical, no external dependency. The downloader/updater is a later add. |
| **76** (step 2) Packaging | the `[project]` table + `src/`-layout un-hiding + console scripts + deleting the 11 `__file__` bootstraps | step-1 tooling `pyproject.toml` already landed (alpha.4); `src/.memoria` still dotted, no `[project]` table | Pure import-hygiene; independent of the deferred reconciling-installer spine (step 3). |
| **58** (2 of 5) Adjacent tools | **read-only Obsidian Inspector** (board counts / WIP / audit tail / Linter band) and **static-HTML admin reports** (weekly snapshot) | both read existing dashboards/logs, no new write path | The other three (Todoist mirror, open-design renderer, literate code-note) are external-dep / design-incomplete. |

## Tier B — a cheap deterministic slice is ready now; the rest is gated

- **ADR-35 (skill insights).** Buildable now: a recurrence sweep over the
  alpha.5 `classify`-miss log → an Inbox card → `skill-insights/`. The detection
  prerequisite now exists; only the *volume* of recurrences is usage-gated.
- **ADR-39 (acceptance checklists).** Buildable now: the **mechanical** half
  (citekey present, `<250` words, title = claim sentence) as a Linter flag —
  template-derivable; `detectors.py` doesn't have it yet. The **soft** rubric
  half needs ≥30 real exemplars (corpus-gated).
- **ADR-59 (classical displacements).** Buildable now: (1) **keyphrase (YAKE)**
  candidate tags alongside the classifier; (2) the **no-ID dedup proposer** — the
  ID-first pass already ships in `link.py`, and `recorded_by_name` now logs the
  by-name collisions that would trigger it; (3) **classical prose metrics** before
  the export gate. Blocked: learning-to-rank triage (needs ≥300 decisions),
  claim-sentence classifier (needs a pilot + FP data), discovery scorer (depends
  on ADR-61).
- **ADR-65 (schema/retrieval).** Buildable now: add the `similar` relation value
  and the `_aspects.{key_idea,method,outcome}` paper fields (neither exists in the
  schemas today); shadow-extract `_aspects` over `_papers/`; wire the
  `vision_analyze` figure-reading path. Confident *adoption* of the thresholds is
  corpus-gated (≥30-50 confirmable pairs/papers).
- **ADR-38 (pre-file similarity gate).** Trigger (a) "live qmd index in
  retrieval" is **now met** (qmd is wired into the Librarian/Writer/Peer-reviewer
  skills). Buildable now in **shadow mode** (log neighbours, never block); the
  retrospective `find-duplicates` sweep must be built first, and confident gating
  (the 0.8 threshold) is corpus-gated.

## Tier C — genuinely blocked (real, verified prerequisite) — not for alpha.6

- **ADR-66** triage/ranking — confidence score exists; thresholds need a measured
  error rate over ≥2 months (real-vault data).
- **ADR-61** nightly discovery loop — operator preconditions (`research-focus.md`
  maintained ≥4 weeks, written `screening-plan.md`, an always-on machine).
- **ADR-60 / ADR-63** cross-vault / multi-machine — need a real 2nd vault / 2nd
  device / ≥3 projects; dormant by design under single-researcher scope.
- **ADR-80** ephemeral test-env harness — **only Phase 2 is blocked now** (the
  live-model L5 + visual golden-diffs + chaos/perf tail). Gate 2 is **resolved**
  (Gemma 4 12B is GA — multimodal-input/text-output, official GGUF, served by
  `llama-server --jinja` over `/v1`) and gate 3 is a ~5-min smoke test, so
  **Phase 1 (L0–L4 + cross-cutting) is model-free and implementable now** — built on
  `scripts/e2e-smoke.sh` + record/replay cassettes + the g9 zero-LLM spine + a
  seeded L4 golden path (the model is needed at record time, not run time). See
  ADR-80's phased-adoption section.
