---
title: Decision records
parent: Developers
has_children: true
topic: decisions
nav_order: 3
permalink: /adr/
---

# Decision records

Architecture Decision Records for Memoria. Each file records one choice: what was
decided, why, which alternatives were weighed, and the consequences. ADRs are the
**single home for decisions at every stage of their lifecycle** — there is no separate
proposals folder.

Files are named `NN-title.md` and are **browsable in this directory** — numbered in
creation order. To add one, copy `docs/adr/_template.md` and take the next
number.

## Status lifecycle

`proposed` → `accepted` → `superseded` (or `rejected`). ADR status records decision
state only. Scheduling and readiness live in the GitHub issue tracker: an accepted
decision can still have an implementation issue with Readiness `Later`, `Blocked`,
or `Needs shaping`. See `docs/adr/_template.md` for the required fields per
status.

## Index

<!-- ADR-INDEX:START -->

| # | Decision | Status |
|---|---|---|
| [06](06-citekey-naming-convention.md) | Citekey naming convention | superseded → ADR-124 |
| [11](11-vault-eval-maintenance.md) | vault-eval as a maintenance capability | accepted |
| [12](12-obsidian-linter-reference-only.md) | obsidian-linter is reference-only, not a control-plane formatter | accepted |
| [14](14-advisor-review-vs-frozen-deliverable.md) | Advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract | superseded → ADR-126 |
| [16](16-systematic-review-adopt-on-demand.md) | Adopt-on-demand — systematic-review tooling | proposed |
| [20](20-publication-path.md) | Publication path — vault-eval benchmark first, capture-now | accepted |
| [24](24-single-researcher-scope.md) | Single-researcher scope — multi-user semantics are out of scope | accepted |
| [29](29-testing-framework.md) | A layered testing framework, not a pile of plans | accepted |
| [44](44-tests-in-pytest-tree.md) | L1 component tests live in a repo-side pytest tree, not inline in shipped modules | accepted |
| [62](62-measurement-and-verification-harnesses.md) | Measurement and verification harnesses | accepted |
| [64](64-native-windows-support.md) | Native Windows support | accepted |
| [73](73-docs-reference-conventions.md) | Documentation references — source links, ADR links, and per-operation Diátaxis split | accepted |
| [75](75-github-project-fields-and-release-sub-issues.md) | Use GitHub Project fields and release sub-issues for live work state | accepted |
| [88](88-literate-code-note.md) | Literate code-note | proposed |
| [90](90-claim-sentence-classification.md) | Claim-sentence classification | proposed |
| [91](91-classical-prose-metrics-export-gate.md) | Classical prose metrics for the export gate | proposed |
| [92](92-discovery-relevance-scoring.md) | Discovery relevance scoring | accepted |
| [93](93-keyphrase-extraction-tag-candidates.md) | Keyphrase extraction for tag candidates | accepted |
| [94](94-record-linkage-entity-deduplication.md) | Record linkage for entity deduplication | accepted |
| [95](95-nightly-proactive-discovery-loop.md) | Nightly proactive discovery loop | rejected |
| [96](96-code-lane-keep-revert-experiment-loop.md) | Code-lane keep/revert experiment loop | proposed |
| [97](97-writer-proposed-candidate-claim-notes.md) | Writer-proposed candidate claim notes | rejected |
| [98](98-relation-vocabulary-expansion.md) | Relation-vocabulary expansion | proposed |
| [99](99-massw-aligned-paper-aspects.md) | MASSW-aligned paper aspects | accepted |
| [101](101-navigation-spaces-gate-reserved-for-approval.md) | Navigation surfaces are "spaces"; "gate" is reserved for the approval gate | accepted |
| [103](103-projected-canvas-spatial-axis.md) | Projected Canvas spatial axis | rejected |
| [105](105-diagnostic-plane.md) | Content-light diagnostic plane — out of the vault, ephemeral, opt-in detail | accepted |
| [106](106-cost-and-disposition-capture.md) | Cost and disposition capture — Hermes session store and the review action | rejected |
| [107](107-okf-interchange-bundle-format.md) | OKF as Memoria's import/export bundle format | proposed |
| [108](108-liteparse-local-document-parsing.md) | LiteParse as the local document-parsing engine | proposed |
| [110](110-ruff-format-python-layout.md) | Ruff: formatter owns layout (line-length 100), curated lint ruleset | accepted |
| [122](122-sqlite-working-state-boundary.md) | SQLite working state and catalog records sit behind the checked Concept boundary | accepted |
| [123](123-doi-catalog-enrichment-gate.md) | DOI catalog enrichment gates checked source promotion | accepted |
| [124](124-standalone-catalog-citation-authority.md) | Standalone catalog is the citation authority | accepted |
| [125](125-standalone-cli-engine-architecture.md) | Memoria is a standalone local CLI + engine | accepted |
| [126](126-four-type-knowledge-model.md) | Four concept types, meaning-only frontmatter, hub-owns-tag, project layer | accepted |
| [127](127-quarantine-and-verify-integrity.md) | Quarantine-and-verify integrity engine (recoverability, git/journal, recovery classes) | accepted |
| [128](128-no-write-time-correctness-oracle.md) | No write-time correctness oracle — checked ≠ approved | accepted |
| [129](129-layered-machine-judgment.md) | Layered machine judgment — proposers, deterministic extraction, shadow-first calibration | accepted |
| [130](130-read-api-surfaces-and-copi.md) | Read-API-only surfaces and the agent contract | accepted |

<!-- ADR-INDEX:END -->

This table is generated from each ADR's frontmatter by
[`scripts/gen_adr_index.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/gen_adr_index.py) — run it after adding or
editing an ADR; CI fails if it is stale. Do not edit the table by hand.

Rules:

- **Every decision lives here, at any status.** Open proposals (`proposed`), accepted decisions, rejected alternatives, and superseded ones all share this folder and the one number sequence.
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Subsystem ADRs are the default home.** ADRs 125–130 consolidate the alpha.15
  architecture into broad subsystem decisions; amend one of them unless a genuinely
  new subsystem appears.
- **Retired decisions are removed.** If the question a decision answered no longer applies, delete it — git history is the record.
- **Scheduling is issue state, not ADR state.** Use ADR `status` for whether a decision is proposed, accepted, rejected, or superseded. Use the linked GitHub issue's Readiness for whether implementation is ready, blocked, needs shaping, or belongs later.
- **Sequencing is not decided here.** *When* a decision ships lives in the current milestone and the current "Release <version>" parent issue plus sub-issues, which change independently of these decisions. Link to that release surface rather than restating phase order, so a re-plan does not strand stale dates here.

## When to retire an ADR

ADRs are immutable in **content** — you supersede a decision, never rewrite it — but the
*set* is pruned, so it doesn't accrue stale v0.x cruft. "Immutable" means the decision
text doesn't change; it does **not** mean every file is kept forever. Three fates:

- **Accepted + load-bearing** — keep; it's the live rule the code follows.
- **Superseded** — keep as a thin tombstone *while the supersession chain still has value*
  (a reader following `superseded_by` must not hit a dead end). Once the replacement is
  long-settled and nothing links to it, it is eligible to retire.
- **Retired** — the question it answered no longer applies: **delete it**; git history is
  the record.

**Never prune the rejected-alternatives memory.** An ADR's *Alternatives considered* — why
we did *not* do X — is the highest-value, lowest-cost part: it stops the same idea being
re-litigated. Retire decisions whose *question dissolved*, not ones that record a
still-relevant rejection.

**Mechanics.** Delete the file, **leave the number gap** (numbers are permanent — never
renumber), remove or repoint inbound `supersedes` / `superseded_by` / `assumes` references
and any doc links (the `lint` job's link checks catch a dangling reference), then
regenerate the index (`scripts/gen_adr_index.py`). The retire sweep runs **per release
cut** — see `.agents/playbooks/release.md`.
