---
title: Decisions
parent: Explanation
nav_order: 90
has_children: true
topic: decisions
---

# Decisions

Architecture Decision Records for Memoria. Each file records one choice: what was
decided, why, which alternatives were weighed, and the consequences. ADRs are the
**single home for decisions at every stage of their lifecycle** — there is no separate
proposals folder.

Files are named `NN-title.md` and are **browsable in this directory** — numbered in
creation order. To add one, copy [the ADR template](_template.md) and take the next
number.

## Status lifecycle

`proposed` → `accepted` → `superseded` (or `rejected`), plus `deferred` for a decision
whose shape is settled but whose scheduling waits. A `deferred` or `proposed` ADR is
not a to-do item; it is revisited each release cycle rather than parked on a fired
condition. See [the template](_template.md) for the required fields per status.

## Index

<!-- ADR-INDEX:START -->

| # | Decision | Status |
|---|---|---|
| [01](01-three-layer-architecture.md) | Three-layer architecture — board, workers, vault | superseded → ADR-46 |
| [02](02-seven-specialist-profiles.md) | Seven specialist profiles over one generalist agent | superseded → ADR-48 |
| [03](03-structural-review-gate.md) | Review gate is structural, enforced by the policy MCP | accepted |
| [04](04-lifecycle-over-topic-folders.md) | Folders encode lifecycle stage, not subject area | superseded → ADR-47 |
| [05](05-zotero-as-bibliographic-backbone.md) | Zotero + Better BibTeX as the bibliographic backbone | accepted |
| [06](06-citekey-naming-convention.md) | Citekey naming convention | accepted |
| [07](07-delegate-coding-to-external-agents.md) | Code agent attachment | accepted |
| [08](08-typed-relations-frontmatter.md) | Typed relations frontmatter | superseded → ADR-52 |
| [09](09-contradictions-dashboard.md) | Contradictions / tensions dashboard | accepted |
| [10](10-claim-supersession.md) | Claim supersession relation | accepted |
| [11](11-vault-eval-maintenance.md) | vault-eval as a maintenance capability | accepted |
| [12](12-obsidian-linter-reference-only.md) | obsidian-linter is reference-only, not a control-plane formatter | accepted |
| [13](13-homepage-front-door.md) | Homepage front-door note, auto-opened by obsidian-homepage | accepted |
| [14](14-advisor-review-vs-frozen-deliverable.md) | Advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract | accepted |
| [15](15-project-membership-from-topic-hint.md) | Project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed | accepted |
| [16](16-systematic-review-adopt-on-demand.md) | Adopt-on-demand — systematic-review tooling | accepted |
| [17](17-shared-candidate-frontmatter.md) | Shared candidate frontmatter format | superseded → ADR-50, ADR-51 |
| [18](18-rename-agent-verdict.md) | Rename `agent_verdict` → `agent_recommendation` | accepted |
| [19](19-moc-threshold-alert.md) | Agent-proposed hubs (threshold alert and Mapper handoff) | accepted |
| [20](20-publication-path.md) | Publication path — vault-eval benchmark first, capture-now | accepted |
| [21](21-l3-autonomy-ceiling.md) | L3 autonomy ceiling, structurally enforced (the Coder-lane exception is retired) | accepted |
| [22](22-build-on-hermes-runtime.md) | Build on the Hermes Agent runtime rather than a bespoke one | accepted |
| [23](23-scoped-memory-substrates.md) | Memory is seven scoped substrates, not one store | accepted |
| [24](24-single-researcher-scope.md) | Single-researcher scope — multi-user semantics are out of scope | accepted |
| [25](25-session-logging-two-logs.md) | Two separate session logs — hash-paired audit vs. per-session digests | accepted |
| [26](26-repo-as-install-unit.md) | The repo is the install unit; profiles are hand-authored and idempotently deployed | accepted |
| [27](27-hermes-native-config-and-gate-enforcement.md) | Configure Hermes the way Hermes reads config; the review gate enforces via a toolset allowlist with obsidian as the only write path | accepted → ADR-28 |
| [28](28-write-gate-as-plugin.md) | The vault write gate is a Hermes Python plugin, not a shell hook | accepted |
| [29](29-testing-framework.md) | A layered testing framework, not a pile of plans | accepted |
| [30](30-deterministic-ingest-pipeline.md) | Tiered ingest pipeline (capture → fallback-chained enrichment → gated write) | accepted |
| [31](31-native-obsidian-mcp.md) | Vault access via the Local REST API plugin's native MCP (HTTPS), not uvx mcp-obsidian | accepted |
| [32](32-external-access-over-mcp.md) | Profile capabilities and external access reach the agent only over MCP; deterministic tools are self-hosted | accepted |
| [33](33-cluster-mcp-bertopic.md) | The Mapper's clustering runs over a Memoria-authored BERTopic MCP, not in-agent ML skills | accepted |
| [34](34-code-artifact-autopilot.md) | Code-artifact autopilot | rejected |
| [35](35-cross-run-skill-insights.md) | Cross-run skill-insights memory | deferred |
| [36](36-dedicated-review-note-type.md) | Dedicated review-note type | superseded → ADR-51 |
| [37](37-retriever-scout-profile.md) | Retriever / Scout as a separate profile | superseded → ADR-48 |
| [38](38-pre-file-similarity-gate.md) | Ratchet — a qmd similarity gate before filing a synthesis note | deferred |
| [39](39-note-acceptance-checklists.md) | Per-note-type acceptance checklists ("frozen evaluator") — deferred | deferred |
| [40](40-admin-gui-surface.md) | Admin/forensic GUI surface (hermes-workspace) | rejected |
| [41](41-configurable-review-gate-mode.md) | Configurable review-gate mode (blocking / advisory) for comparison studies | deferred |
| [42](42-profile-compilation.md) | Profile compilation from a shared base | superseded → ADR-48 |
| [43](43-skill-governance.md) | Skill governance and lifecycle | accepted |
| [44](44-tests-in-pytest-tree.md) | L1 component tests live in a repo-side pytest tree, not inline in shipped modules | accepted |
| [45](45-release-management-model.md) | Release management — gates as a tracking-issue checklist, release-please for versioning | accepted |
| [46](46-seven-layer-architecture.md) | Seven-layer architecture — PI · Interface · Co-PI · Tasks · MCP · Engines · Vault | accepted |
| [47](47-type-first-category-folders.md) | Type-first category folders — catalog · notes · projects · inbox · system | accepted |
| [48](48-copi-and-agent-consolidation.md) | One Co-PI fronts everything; specialists consolidate to posture-defined agents | accepted |
| [49](49-catalog-in-bases-linter-monitor.md) | Catalog entities live in Obsidian Bases; the Linter is the integrity monitor and commit gate | accepted |
| [50](50-universal-lifecycle-and-maturity.md) | One lifecycle chain for everything; maturity is a claim property; reference dropped; MOC renamed hub | accepted |
| [51](51-inbox-category-and-honesty-card.md) | The Inbox category and the honesty card — argument for/against, what tipped it, certainty; no verdict on proposals | accepted |
| [52](52-links-vs-relationships.md) | Notes carry authored links:, entities carry given relationships — two kinds of connection | accepted |
| [53](53-pattern-library.md) | The pattern library — curated prompt-transformations as data in system/patterns/, one runner | accepted |
| [54](54-two-decision-kinds-batch-worklists.md) | Two kinds of human decision — approval gates and work prompts; classify automated; batch worklists for high cardinality | accepted |
| [55](55-src-scaffold-populate-golden-copy.md) | The repo ships src/, the installer scaffolds and populates, and a golden copy makes the vault restorable | accepted |
| [56](56-extraction-uncertainty-flag.md) | Low-confidence extraction routes to a flag — the ingest engine never merges identities silently | accepted |
| [57](57-engines-write-agents-judge.md) | Engines write, agents judge — no LLM agent as a mechanical writer | accepted |
| [58](58-adjacent-tool-integrations.md) | Adjacent tool integrations and added surfaces | deferred |
| [59](59-classical-method-displacements.md) | Classical method displacements over LLM calls | deferred |
| [60](60-cross-vault-knowledge-sharing.md) | Cross-vault and cross-project knowledge sharing | deferred |
| [61](61-nightly-discovery-loop.md) | Nightly discovery loop, code-experiment loop, and Writer-proposed claims | deferred |
| [62](62-measurement-and-verification-harnesses.md) | Measurement and verification harnesses | accepted |
| [63](63-multi-machine-deployment.md) | Multi-machine deployment topologies and secondary-device patterns | deferred |
| [64](64-native-windows-support.md) | Native Windows support: production on Windows, testing on Linux | accepted |
| [65](65-retrieval-and-schema-extensions.md) | Retrieval and schema extensions | deferred |
| [66](66-triage-ranking-improvements.md) | Semi-automatic triage, agent-consensus pre-filter, and tournament ranking | deferred |
| [67](67-drift-procedures-keep-or-retire.md) | Drift procedures under the golden-copy model — keep or retire | accepted |
| [68](68-workspaces-desk-library-studio.md) | Workspaces v2 — Desk / Library / Studio, home.md as control panel | accepted |
| [69](69-operations-layer-naming.md) | Operations — name the deterministic layer and its four categories | accepted |
| [70](70-navigation-gates-dashboards.md) | Navigation — intent-named gates, ambient maintenance, JTBD dashboards | accepted |
| [71](71-structured-capture-forms.md) | Structured capture — forms at entry, the Linter as authority, one schema per type | accepted |
| [72](72-command-surfacing.md) | Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive | accepted |
| [73](73-docs-reference-conventions.md) | Documentation references — source links, ADR links, and per-operation Diátaxis split | accepted |
| [74](74-pinned-obsidian-plugin-supply-chain.md) | Manage bundled Obsidian plugins with a pinned provenance manifest | deferred |
| [75](75-github-project-fields-and-release-sub-issues.md) | Use GitHub Project fields and release sub-issues for live work state | accepted |
| [76](76-versioned-vault-release-reconciling-installer.md) | Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer | deferred |
| [77](77-project-gate.md) | Project gate | accepted |
| [78](78-thesis-note-type.md) | Thesis note type | accepted |
| [79](79-argument-graph-and-warrant.md) | Argument graph and warrant | accepted |
| [80](80-ephemeral-containerized-test-env.md) | Ephemeral containerized Linux test-env harness | deferred |

<!-- ADR-INDEX:END -->

This table is generated from each ADR's frontmatter by
[`scripts/gen_adr_index.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/gen_adr_index.py) — run it after adding or
editing an ADR; CI fails if it is stale. Do not edit the table by hand.

Rules:

- **Every decision lives here, at any status.** Open proposals (`proposed`/`deferred`), accepted decisions, and superseded ones all share this folder and the one number sequence.
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Retired decisions are removed.** If the question a decision answered no longer applies, delete it — git history is the record.
- **Deferred is revisited, not gated.** A `deferred` ADR records `assumes:` (the decisions/mechanisms it rests on) so a change that invalidates it is detectable; it is re-judged each release cycle, never held on a static trigger.
- **Sequencing is not decided here.** *When* a decision ships lives in the current milestone, the current "Release vX.Y" parent issue plus sub-issues, and the release plan under [`docs/releasing/`](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md), which change independently of these decisions. Link to that release surface rather than restating phase order, so a re-plan does not strand stale dates here.

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
cut** — see [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md).
