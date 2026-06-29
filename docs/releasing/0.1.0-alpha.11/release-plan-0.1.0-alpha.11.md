---
release: 0.1.0-alpha.11
status: candidate    # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- 0.1.0-alpha.11
parent: Releasing
nav_order: 2
---

# Release plan -- 0.1.0-alpha.11

**Current status: candidate internal checkpoint.** alpha.11 is the fresh-sandbox
reset that implements the basic knowledge cycle and tests the integrity thesis.
It is not a formal release: no release-please PR, tag, GitHub Release, migration,
upgrade path, or backwards-compatibility work is expected. Candidate evidence is
preserved in the
[0.1.0-alpha.11 validation log](validation-log.md); remaining limits are
sandbox/product-evidence limits, not migration or compatibility work.

## 1. Scope -- what this release is

alpha.11 delivers the basic knowledge cycle end to end in Obsidian on a fresh
test workspace: open a project, seed it, run gap analysis, capture a real source,
hold the Co-PI conversation, compile a machine-owned digest plus hub suggestions,
construct anchored notes/claims, re-run gap analysis, and exercise trace,
structural checks, flag routing, and cascade rollback. The implementation uses a
workspace with `catalog/`, `knowledge/`, and `capabilities/` roots; a trusted
worker; a derivation journal; checked-only consumption; qmd-backed disposable
indexing; and a thin Obsidian control-panel plugin.

The boundary is explicit: alpha.11 starts from a fresh sandbox workspace. It does
not migrate existing data, preserve legacy draft/export affordances, ship the
writing module, add the coding/autonomy lane, introduce multi-user/sync-primary
infrastructure, or make automatic Link/contradiction promotion authoritative.

## 2. Definition of done -- gates

0.1.0-alpha.11 is complete when every gate below is closed in the release parent
issue or its successor, with evidence attached there. This file defines the gates;
issue state is the source of truth.

| Gate | Proves | Verified by |
| --- | --- | --- |
| G1 Source contract | The alpha.11 schema/folder model, operation policy, worker boundary, projection generators, release docs, and system docs agree with the design source of truth. | `scripts/verify pr`, `docs_doctor`, `status_doctor`, `agents_doctor`, focused schema/policy tests. |
| G2 Fresh sandbox package | A fresh alpha.11 workspace initializes with `catalog/`, `knowledge/`, `capabilities/`, `steering.md`, journal, queue, projections, and disposable qmd index; no migration input is required. | Package/skeleton tests, projection drift check, checked-only qmd BM25 rebuild. |
| G3 Basic knowledge cycle | One real source goes through capture, metadata, conversation, digest/hub compounding, anchored notes/claims, Ask/gap analysis, and re-run in Obsidian. | End-to-end run in `Memoria-test` plus evidence file. |
| G4 Integrity spine | Trusted writes, PI-edit backfill, foreign quarantine, read barrier, structural checks, act/ask/drop routing, and cascade rollback all fire with traced events. | Writer/journal tests, `tests/test_integrity.py`, boundary-deny tests, seeded structural fixture. |
| G5 Seeded-error verdict | The frozen seeded-error bundle measures recall, false positives, rollback completeness, residual error versus baseline, and human-checkpoint value per error class. | `system/eval/alpha11-seeded-errors.json`, `tests/test_seeded_errors.py`, batch runner results; bar met or targeted gating added and retested. |
| G6 Documentation and release readiness | System documentation, ADRs, release plan, and tracked `tmp/` disposition agree with the built alpha.11 behavior. | Documentation sweep, release close-out sweep, checker summary. |

## 3. Validation -- stages

The automated release-candidate prefix is:

```bash
scripts/verify rc
```

If runtime prerequisites are unavailable, record the skip reason and run the
Runtime/Product checks manually on the test host.

| Stage | Proves |
| --- | --- |
| Source | Static docs, agent guidance, schemas, policy boundaries, generated references, and focused tests are green on the candidate commit. |
| Package | A fresh alpha.11 sandbox assembles without legacy input and regenerates projections without drift. |
| Runtime | Worker, Local REST bridge, qmd, Zotero Local API import path, and Obsidian plugin control panel work against `Memoria-test`. |
| Product | The basic knowledge cycle is usable in Obsidian, with evidence-first flags and trace-to-rollback available to the PI. |
| Release | Release plan, system docs, ADRs/issues, and `tmp/` scratch disposition are current; no hidden release state remains in local notes. |

## 4. Blockers

Not enumerated here. By definition the blockers are any open gate/stage issue
under the alpha.11 release parent, any open issue assigned to the
`0.1.0-alpha.11` milestone, and any open High-priority blocker in the Memoria
Issue Tracker project.

## 5. Out of scope (later)

- Migration, upgrade path, backwards compatibility, production-vault conversion,
  or data-preservation checks for an existing install.
- Draft, verify, paper export, and any compatibility affordance for older
  draft/export behavior.
- Coding/autonomy lane, multi-user support, sync-authoritative DB, hosted control
  plane, message broker, workflow engine, graph database, or heavy agent
  framework.
- Automatic Link/contradiction promotion, nightly discovery at scale, advanced
  graph visualization beyond Canvas, and external MCP exposure of Memoria
  operations.

## 6. Known limitations

- Limitation: alpha.11 is an internal checkpoint, not a tagged release. Impact:
  users should not look for a GitHub Release or release-please changelog entry.
  Workaround: use this plan, merged PRs, and the release issue trail as the
  checkpoint record.
- Limitation: alpha.11 runs on a fresh test workspace until the seeded-error bar
  passes. Impact: no non-sandbox workspace is supported during the checkpoint.
  Workaround: use `Memoria-test` or disposable workspaces only.
- Limitation: model-quality wiki synthesis and visual Obsidian panel activation
  require live/tool-specific evidence. Impact: CI can prove structure, but these
  gates need attended/runtime proof. Workaround: record the live evidence in the
  gate issue or release evidence file. Zotero is in scope only as an item/source
  import path for alpha.11; Zotero annotation import is not a release gate. The
  local parser-backed PDF page/span/bbox fixture has passed in the Memoria-test
  venv; broader real-corpus parser quality remains a follow-up measurement.

## 7. Documentation integrity

Before alpha.11 closes, update system documentation and complete a fresh docs
sweep over the reset:

1. **Coverage:** workspace layout, Concept types, `source_id`, trusted writer,
   journal events, read barrier, operation policy, qmd indexing, capture,
   conversation, notes, gap analysis, checks, rollback, plugin boundary, and
   seeded-error verdict have current how-to/reference/explanation coverage.
2. **Single source of truth:** schema/folder YAMLs, operation policies, release
   plan, ADRs, and public docs do not restate conflicting contracts; generated
   projections are covered by drift checks.
3. **Diataxis placement and indexing:** new or changed pages land in the right
   section and section README/index pages link them.
4. **Terminology:** Bundle, workspace, Concept, Link, Citation, `digest`, `note`,
   `hub`, operation, checked/unchecked/quarantined, and non-sandbox gate wording
   are used consistently.
5. **External/runtime claims:** Hermes, Obsidian, Zotero, qmd, parser, and model
   runner claims are backed by current on-box or explicitly marked evidence.
6. **ADR capture:** durable decisions from `tmp/` scratch land in `docs/adr/`;
   unfinished scratch moves forward or becomes issues before `tmp/` is deleted.

Required checker summary: `python scripts/docs_doctor.py docs`, `python
scripts/status_doctor.py`, `python scripts/agents_doctor.py`, docs link checks,
cspell, and any focused schema/policy tests touched by the implementation.

## 8. Runtime readiness

Runtime evidence is required because alpha.11 changes the storage shape, write
boundary, worker, plugin surface, capture path, index, and integrity loop.

Record:

1. Fresh sandbox initialization from the alpha.11 skeleton.
2. Worker write, PI-edit backfill, foreign quarantine, projection regeneration,
   and checked-only qmd rebuild.
3. Obsidian Local REST bridge and plugin panel activation in `Memoria-test`.
4. Zotero Local API item import and selected-PDF-parser page/span/bbox evidence.
5. One full source-to-gap-analysis cycle, including trace-to-rollback.
6. Seeded-error verdict bundle and per-class results.

No runtime check may mutate any non-sandbox workspace.

## 9. Release close-out sweep

Before closing this checkpoint:

1. Review every tracked file in `docs/releasing/0.1.0-alpha.11/tmp/`.
2. Fold implemented decisions into ADRs, system documentation, reference/how-to
   docs, tests, or issue comments.
3. Move unfinished scratch forward to the next release `tmp/` or a GitHub issue.
4. Delete only scratch whose durable content has landed elsewhere.
5. Close or roll forward alpha.11 issues and milestone items.
6. Confirm branch/worktree hygiene after merge.

Current disposition: the tracked alpha.11 `tmp/` scratch was reviewed and
removed after its durable evidence was summarized in
the [0.1.0-alpha.11 validation log](validation-log.md). Future alpha.11 release
state belongs in the release plan, validation log, issues, tests, ADRs, or
system docs, not a tracked `tmp/` folder.

## 10. Cut procedure

This checkpoint follows the untagged internal path:

1. Every gate and stage issue is closed; required CI is green on `main`; no open
   High-priority blocker remains.
2. Re-run the Source/Package/Runtime/Product/Release stages or record explicit
   runtime skip/manual replacement evidence.
3. Complete documentation integrity, runtime readiness, and close-out sweeps.
4. Do not cut a tag or GitHub Release. Set this plan to `status: complete`,
   `released: false` after the release parent issue is closed.
5. Close the milestone, rolling unfinished issues to the next checkpoint.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Seeded-error follow-up | After alpha.11 verdict | Add targeted gates for any weak error class and retest. |
| Writing module | After integrity gate holds | Design draft/verify/export on top of the checked graph. |
| Discovery scale | After basic loop is usable | Expand source discovery and retrieval quality beyond the first cycle. |
