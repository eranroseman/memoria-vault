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
| [03](03-structural-review-gate.md) | Review gate is structural, enforced by the policy MCP | accepted |
| [05](05-zotero-as-bibliographic-backbone.md) | Superseded Zotero bibliography authority | superseded → ADR-124 |
| [06](06-citekey-naming-convention.md) | Citekey naming convention | accepted |
| [07](07-delegate-coding-to-external-agents.md) | Code agent attachment | accepted |
| [09](09-contradictions-dashboard.md) | Contradictions / tensions dashboard | accepted |
| [10](10-claim-supersession.md) | Claim supersession relation | accepted |
| [11](11-vault-eval-maintenance.md) | vault-eval as a maintenance capability | accepted |
| [12](12-obsidian-linter-reference-only.md) | obsidian-linter is reference-only, not a control-plane formatter | accepted |
| [14](14-advisor-review-vs-frozen-deliverable.md) | Advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract | accepted |
| [15](15-project-membership-from-topic-hint.md) | Project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed | accepted |
| [16](16-systematic-review-adopt-on-demand.md) | Adopt-on-demand — systematic-review tooling | accepted |
| [19](19-moc-threshold-alert.md) | Agent-proposed hubs (threshold alert and Mapper handoff) | accepted |
| [20](20-publication-path.md) | Publication path — vault-eval benchmark first, capture-now | accepted |
| [21](21-l3-autonomy-ceiling.md) | L3 autonomy ceiling, structurally enforced (the Coder-lane exception is retired) | accepted |
| [22](22-build-on-hermes-runtime.md) | Build on the Hermes Agent runtime rather than a bespoke one | superseded → ADR-64 |
| [23](23-scoped-memory-substrates.md) | Memory is seven scoped substrates, not one store | accepted |
| [24](24-single-researcher-scope.md) | Single-researcher scope — multi-user semantics are out of scope | accepted |
| [25](25-session-logging-two-logs.md) | Two separate session logs — hash-paired audit vs. per-session digests | accepted |
| [26](26-repo-as-install-unit.md) | The repo is the install unit; profiles are hand-authored and idempotently deployed | accepted |
| [28](28-write-gate-as-plugin.md) | The vault write gate is a Hermes Python plugin, not a shell hook | accepted |
| [29](29-testing-framework.md) | A layered testing framework, not a pile of plans | accepted |
| [30](30-deterministic-ingest-pipeline.md) | Tiered ingest pipeline (capture → fallback-chained enrichment → gated write) | accepted |
| [31](31-native-obsidian-mcp.md) | Vault access via the Local REST API plugin's native MCP (HTTPS), not uvx mcp-obsidian | accepted |
| [32](32-external-access-over-mcp.md) | Profile capabilities and external access reach the agent only over MCP; deterministic tools are self-hosted | accepted |
| [33](33-cluster-mcp-bertopic.md) | The Mapper's clustering runs over a Memoria-authored BERTopic MCP, not in-agent ML skills | accepted |
| [35](35-cross-run-skill-insights.md) | Cross-run skill-insights memory | accepted |
| [38](38-pre-file-similarity-gate.md) | Ratchet — a qmd similarity gate before filing a synthesis note | accepted |
| [41](41-configurable-review-gate-mode.md) | Configurable review-gate mode (blocking / advisory) for comparison studies | accepted |
| [43](43-skill-governance.md) | Skill governance and lifecycle | accepted |
| [44](44-tests-in-pytest-tree.md) | L1 component tests live in a repo-side pytest tree, not inline in shipped modules | accepted |
| [46](46-seven-layer-architecture.md) | Seven-layer architecture — PI · Interface · Co-PI · Tasks · MCP · Engines · Vault | accepted |
| [48](48-copi-and-agent-consolidation.md) | One Co-PI fronts everything; specialists consolidate to posture-defined agents | accepted |
| [49](49-catalog-in-bases-linter-monitor.md) | Catalog entities live in Obsidian Bases; the Linter is the integrity monitor and commit gate | superseded → ADR-122 |
| [52](52-links-vs-relationships.md) | Notes carry authored links:, entities carry given relationships — two kinds of connection | accepted |
| [53](53-pattern-library.md) | The pattern library — curated prompt-transformations as data in system/patterns/, one runner | accepted |
| [54](54-two-decision-kinds-batch-worklists.md) | Two kinds of human decision — approval gates and work prompts; classify automated; batch worklists for high cardinality | accepted |
| [55](55-src-scaffold-populate-golden-copy.md) | The repo ships a vault template, the installer scaffolds and populates, and a golden copy makes the vault restorable | accepted |
| [56](56-extraction-uncertainty-flag.md) | Low-confidence extraction routes to a flag — the ingest engine never merges identities silently | accepted |
| [57](57-engines-write-agents-judge.md) | Engines write, agents judge — no LLM agent as a mechanical writer | accepted |
| [62](62-measurement-and-verification-harnesses.md) | Measurement and verification harnesses | accepted |
| [64](64-native-windows-support.md) | Native Windows support | accepted |
| [66](66-triage-ranking-improvements.md) | Semi-automatic triage, agent-consensus pre-filter, and tournament ranking | accepted |
| [69](69-operations-layer-naming.md) | Operations — name the deterministic layer and its four categories | accepted |
| [72](72-command-surfacing.md) | Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive | accepted |
| [73](73-docs-reference-conventions.md) | Documentation references — source links, ADR links, and per-operation Diátaxis split | accepted |
| [74](74-pinned-obsidian-plugin-supply-chain.md) | Manage bundled Obsidian plugins with a pinned provenance manifest | accepted |
| [75](75-github-project-fields-and-release-sub-issues.md) | Use GitHub Project fields and release sub-issues for live work state | accepted |
| [77](77-project-gate.md) | Project gate | accepted |
| [79](79-argument-graph-and-warrant.md) | Argument graph and warrant | accepted |
| [80](80-ephemeral-containerized-test-env.md) | Ephemeral containerized Linux test-env harness | accepted |
| [83](83-direct-pi-relate-control.md) | Direct PI relate control | accepted |
| [88](88-literate-code-note.md) | Literate code-note | proposed |
| [90](90-claim-sentence-classification.md) | Claim-sentence classification | proposed |
| [91](91-classical-prose-metrics-export-gate.md) | Classical prose metrics for the export gate | proposed |
| [92](92-discovery-relevance-scoring.md) | Discovery relevance scoring | proposed |
| [93](93-keyphrase-extraction-tag-candidates.md) | Keyphrase extraction for tag candidates | proposed |
| [94](94-record-linkage-entity-deduplication.md) | Record linkage for entity deduplication | proposed |
| [95](95-nightly-proactive-discovery-loop.md) | Nightly proactive discovery loop | proposed |
| [96](96-code-lane-keep-revert-experiment-loop.md) | Code-lane keep/revert experiment loop | proposed |
| [97](97-writer-proposed-candidate-claim-notes.md) | Writer-proposed candidate claim notes | proposed |
| [98](98-relation-vocabulary-expansion.md) | Relation-vocabulary expansion | proposed |
| [99](99-massw-aligned-paper-aspects.md) | MASSW-aligned paper aspects | proposed |
| [100](100-exploration-trace-capture.md) | Exploration-trace capture | accepted |
| [101](101-navigation-spaces-gate-reserved-for-approval.md) | Navigation surfaces are "spaces"; "gate" is reserved for the approval gate | accepted |
| [102](102-disposable-projection-engine.md) | Disposable projection engine | proposed |
| [103](103-projected-canvas-spatial-axis.md) | Projected Canvas spatial axis | proposed |
| [104](104-telemetry-three-planes.md) | Telemetry as three planes — audit, analytics, diagnostic | accepted |
| [105](105-diagnostic-plane.md) | Content-light diagnostic plane — out of the vault, ephemeral, opt-in detail | accepted |
| [106](106-cost-and-disposition-capture.md) | Cost and disposition capture — Hermes session store and the review action | accepted |
| [107](107-okf-interchange-bundle-format.md) | OKF as Memoria's import/export bundle format | proposed |
| [108](108-liteparse-local-document-parsing.md) | LiteParse as the local document-parsing engine | proposed |
| [109](109-project-management-native-views.md) | Project management uses native views over project notes | accepted |
| [110](110-ruff-format-python-layout.md) | Ruff: formatter owns layout (line-length 100), curated lint ruleset | accepted |
| [112](112-tutorial-destination-first-arc.md) | Onboarding is one destination-first project arc | accepted |
| [114](114-left-pane-navigator.md) | Left pane is a navigation rail: Now over Places | accepted |
| [115](115-inbox-queue-and-retired-homepage.md) | Inbox is the queue, not a space; retire the homepage front door for a startup shell + welcome seed | accepted |
| [116](116-obsidian-surface-architecture.md) | Obsidian surface architecture: three primitives (View, Collection, Rail) + two edges | accepted |
| [118](118-dashboard-consolidation.md) | Dashboard consolidation: fold redundant pages into spaces; keep system dashboards read-only; make the Inspector the read-only index | accepted |
| [119](119-schema-driven-document-creation.md) | Concept schemas own field, home, read-state, and form contracts | accepted |
| [120](120-profile-config-materialization.md) | Profile config capability blocks are materialized from the tool registry | accepted |
| [121](121-enqueue-only-obsidian-control-panel.md) | Obsidian control panel mutates only by enqueueing worker jobs | superseded → ADR-122 |
| [122](122-sqlite-working-state-boundary.md) | SQLite working state and catalog records sit behind the checked Concept boundary | accepted |
| [123](123-doi-catalog-enrichment-gate.md) | DOI catalog enrichment gates checked source promotion | accepted |
| [124](124-standalone-catalog-citation-authority.md) | Standalone catalog is the citation authority | accepted |

<!-- ADR-INDEX:END -->

This table is generated from each ADR's frontmatter by
[`scripts/gen_adr_index.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/gen_adr_index.py) — run it after adding or
editing an ADR; CI fails if it is stale. Do not edit the table by hand.

Rules:

- **Every decision lives here, at any status.** Open proposals (`proposed`), accepted decisions, rejected alternatives, and superseded ones all share this folder and the one number sequence.
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
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
