<!-- source: adr/README.md -->

# Decisions

Architecture Decision Records for Memoria. Each file records one choice: what was
decided, why, which alternatives were weighed, and the consequences. ADRs are the
**single home for decisions at every stage of their lifecycle** — there is no separate
proposals folder.

Files are named `NN-title.md` and are **browsable in this directory** — numbered in
creation order. To add one, copy [the ADR template](_template.md) and take the next
number.

## Status lifecycle

`proposed` → `accepted` → `superseded` (or `rejected`). ADR status records decision
state only. Scheduling and readiness live in the GitHub issue tracker: an accepted
decision can still have an implementation issue with Readiness `Later`, `Blocked`,
or `Needs shaping`. See [the template](_template.md) for the required fields per
status.

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
| [13](13-homepage-front-door.md) | Homepage front-door note, auto-opened by obsidian-homepage | superseded → ADR-115 |
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
| [35](35-cross-run-skill-insights.md) | Cross-run skill-insights memory | accepted |
| [36](36-dedicated-review-note-type.md) | Dedicated review-note type | superseded → ADR-51 |
| [37](37-retriever-scout-profile.md) | Retriever / Scout as a separate profile | superseded → ADR-48 |
| [38](38-pre-file-similarity-gate.md) | Ratchet — a qmd similarity gate before filing a synthesis note | accepted |
| [39](39-note-acceptance-checklists.md) | Per-note-type acceptance checklists ("frozen evaluator") | accepted |
| [40](40-admin-gui-surface.md) | Admin/forensic GUI surface (hermes-workspace) | rejected |
| [41](41-configurable-review-gate-mode.md) | Configurable review-gate mode (blocking / advisory) for comparison studies | accepted |
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
| [58](58-adjacent-tool-integrations.md) | Adjacent tool integrations and added surfaces | superseded → ADR-84, ADR-85, ADR-86, ADR-87, ADR-88 |
| [59](59-classical-method-displacements.md) | Classical method displacements over LLM calls | superseded → ADR-89, ADR-90, ADR-91, ADR-92, ADR-93, ADR-94 |
| [60](60-cross-vault-knowledge-sharing.md) | Cross-vault and cross-project knowledge sharing | accepted |
| [61](61-nightly-discovery-loop.md) | Nightly discovery loop, code-experiment loop, and Writer-proposed claims | superseded → ADR-95, ADR-96, ADR-97 |
| [62](62-measurement-and-verification-harnesses.md) | Measurement and verification harnesses | accepted |
| [63](63-multi-machine-deployment.md) | Multi-machine deployment topologies and secondary-device patterns | accepted |
| [64](64-native-windows-support.md) | Native Windows support: production on Windows, testing on Linux | accepted |
| [65](65-retrieval-and-schema-extensions.md) | Retrieval and schema extensions | superseded → ADR-98, ADR-99, ADR-100 |
| [66](66-triage-ranking-improvements.md) | Semi-automatic triage, agent-consensus pre-filter, and tournament ranking | accepted |
| [67](67-drift-procedures-keep-or-retire.md) | Drift procedures under the golden-copy model — keep or retire | accepted |
| [68](68-workspaces-desk-library-studio.md) | Workspaces v2 — Desk / Library / Studio, home.md as control panel | superseded → ADR-81 |
| [69](69-operations-layer-naming.md) | Operations — name the deterministic layer and its four categories | accepted |
| [70](70-navigation-gates-dashboards.md) | Navigation — intent-named gates, ambient maintenance, JTBD dashboards | accepted |
| [71](71-structured-capture-forms.md) | Structured capture — forms at entry, the Linter as authority, one schema per type | accepted |
| [72](72-command-surfacing.md) | Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive | accepted |
| [73](73-docs-reference-conventions.md) | Documentation references — source links, ADR links, and per-operation Diátaxis split | accepted |
| [74](74-pinned-obsidian-plugin-supply-chain.md) | Manage bundled Obsidian plugins with a pinned provenance manifest | accepted |
| [75](75-github-project-fields-and-release-sub-issues.md) | Use GitHub Project fields and release sub-issues for live work state | accepted |
| [76](76-versioned-vault-release-reconciling-installer.md) | Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer | accepted |
| [77](77-project-gate.md) | Project gate | accepted |
| [78](78-thesis-note-type.md) | Thesis note type | accepted |
| [79](79-argument-graph-and-warrant.md) | Argument graph and warrant | accepted |
| [80](80-ephemeral-containerized-test-env.md) | Ephemeral containerized Linux test-env harness | accepted |
| [81](81-persistent-gate-dashboards.md) | Persistent gate dashboards | accepted |
| [82](82-four-gates-canonical-vocabulary.md) | The four gates are the single user-facing vocabulary; retire the Compile/Compose cycle naming | superseded → ADR-101 |
| [83](83-direct-pi-relate-control.md) | Direct PI relate control | accepted |
| [84](84-read-only-obsidian-inspector.md) | Read-only Obsidian Inspector | accepted |
| [85](85-todoist-gap-card-mirroring.md) | Todoist gap-card mirroring | proposed |
| [86](86-open-design-deliverable-rendering-agent.md) | Open-design deliverable-rendering agent | proposed |
| [87](87-static-html-admin-reports.md) | Static-HTML admin reports | proposed |
| [88](88-literate-code-note.md) | Literate code-note | proposed |
| [89](89-learning-to-rank-triage.md) | Learning-to-rank triage | proposed |
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
| [111](111-two-mode-tutorial-spine.md) | Two-mode tutorial spine, seeded by a half-built corpus | superseded → ADR-112 |
| [112](112-tutorial-destination-first-arc.md) | Onboarding is one destination-first project arc | accepted |
| [113](113-copi-guided-onboarding.md) | Co-PI-guided onboarding (deferred) | proposed |
| [114](114-left-pane-navigator.md) | Left pane is a navigation rail: Now over Places | accepted |
| [115](115-inbox-queue-and-retired-homepage.md) | Inbox is the queue, not a space; retire the homepage front door for a startup shell + welcome seed | accepted |
| [115](115-profile-config-materialization.md) | Profile config capability blocks are materialized from the tool registry | accepted |
| [116](116-obsidian-surface-architecture.md) | Obsidian surface architecture: three primitives (View, Collection, Rail) + two edges | accepted |
| [117](117-type-naming-scheme.md) | Document types: kind-scoped names with a fleeting exception; folder names never collide with spaces | accepted |
| [118](118-dashboard-consolidation.md) | Dashboard consolidation: fold redundant pages into spaces; keep system dashboards read-only; make the Inspector the read-only index | accepted |
| [119](119-schema-driven-document-creation.md) | Schema-driven documents: the type schema is the complete declarative contract that validates, generates, and is the single source | accepted |

<!-- ADR-INDEX:END -->

This table is generated from each ADR's frontmatter by
[`scripts/gen_adr_index.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/gen_adr_index.py) — run it after adding or
editing an ADR; CI fails if it is stale. Do not edit the table by hand.

Rules:

- **Every decision lives here, at any status.** Open proposals (`proposed`), accepted decisions, rejected alternatives, and superseded ones all share this folder and the one number sequence.
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Retired decisions are removed.** If the question a decision answered no longer applies, delete it — git history is the record.
- **Scheduling is issue state, not ADR state.** Use ADR `status` for whether a decision is proposed, accepted, rejected, or superseded. Use the linked GitHub issue's Readiness for whether implementation is ready, blocked, needs shaping, or belongs later.
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


---

<!-- source: adr/01-three-layer-architecture.md -->

# ADR-01: Three-layer architecture — board, workers, vault

## Context

Any agent-assisted knowledge system has to manage three concerns simultaneously: what work is in progress, who is executing it, and what stable knowledge has accumulated. The naive approach is to let a single agent manage all three from its own context. This works for short sessions but fails across sessions, across retries, and across handoffs — because none of that state survives when the conversation ends.

## Decision

Memoria separates these three concerns into three distinct layers with explicit boundaries between them:

- **Board layer (Kanban)** — owns active work state. Every task lives as a card until a human approves it. The board persists across sessions; workers re-ground on it rather than relying on conversational memory.
- **Worker layer (Hermes profiles)** — owns execution context. Seven specialist profiles, each with narrow permissions and a clear exit condition. Workers are stateless between cards; all continuity comes from the board or the vault.
- **Vault layer (Obsidian)** — owns settled knowledge. Durable, lifecycle-organized, human-reviewed before promotion to canonical zones.

The policy MCP enforces the boundary between workers and vault at runtime — it is not a naming convention.

## Why

Three independent research systems (Chen et al. 2026, AgentRxiv 2025, PARNESS 2026) reach the same empirical conclusion from different starting points: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. Chen's ablation shows removing the durable-artifact layer costs 6.41 points on PaperBench and 31.82 on MLE-Bench Lite. The three-layer split is the structural form of this finding.

Collapsing any two layers breaks specific guarantees:
- Board + workers collapsed → work state lost at session end; retries duplicate effort
- Workers + vault collapsed → agents write canonical knowledge without review; errors compound
- Board + vault collapsed → task history pollutes the knowledge graph; in-flight and settled notes become indistinguishable

## Consequences

- The board is the shared state machine. Every long-lived task must have a card.
- Workers carry no persistent state between cards. They read from the board and vault; they write to the vault's working zones.
- The vault's canonical zones are structurally protected — no worker can write to them without a human review approval.
- Retries are safe: the card persists, the vault is unchanged, the worker can be re-dispatched from the last known state.

## Alternatives considered

**Single agent with rich prompt context** — loses all state at session end; no structural separation between discovery and synthesis; permissions become the superset of all tasks.

**Chat-as-substrate (AutoGen style)** — state lives in conversation history, which is ephemeral, hard to query, and unsuitable for long-horizon work.


---

<!-- source: adr/02-seven-specialist-profiles.md -->

# ADR-02: Seven specialist profiles over one generalist agent

## Context

The worker layer needs to be structured. The choice is between one generalist agent that does everything and several specialist agents, each with a narrow mission. A generalist is simpler to configure but creates permission ambiguity, unclear quality responsibility, and no structural separation between optimistic (discovery) and conservative (verification) stances.

## Decision

Memoria uses seven specialist profiles — Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter — each with a focused mission, narrow folder permissions, the skills it actually needs, and a clear exit condition. There is no Orchestrator profile and no Reviewer profile. Routing is static (encoded in lane-override files); review is always human-driven.

## Why

**Quality responsibility is traceable.** When a paper note has an error, it's a Librarian problem. When a citation doesn't trace, it's a Verifier problem. With one agent, debugging requires replaying the conversation to reconstruct which decision caused what.

**Permission enforcement is practical.** A specialist profile's write scope is narrow and checkable by the policy MCP. A generalist profile's write scope is the superset of all tasks — the MCP can't distinguish "this agent is in discovery mode" from "this agent is in synthesis mode."

**Optimistic and conservative stances must be structurally separated.** Librarian proposes optimistically (include candidates, classify tentatively). Verifier checks conservatively (trace every citation, flag every near-duplicate). An agent that does both must switch internally; there is no structural guarantee it does, and no way to audit whether it did.

No Orchestrator because routing encoded in rules is auditable; routing decided by a reasoning agent is not. No Reviewer profile because LLM-based reviewers are confidently wrong on exactly the outputs the gate needs to catch — hallucinated citations are emitted with high fluency and high confidence.

## Consequences

- Each profile's permissions are declared in a lane-override YAML file that the policy MCP reads at startup.
- Routing is deterministic: a card's `assignee` field determines which profile can claim it; no reasoning agent makes routing decisions.
- The review gate is a human action on `review_status`; agents recommend via `agent_recommendation` but never approve.
- Profile count is fixed at seven for Memoria v0.1. Adding an eighth profile requires a new lane-override file, SOUL.md, and policy MCP registration.

## Alternatives considered

**One generalist agent** — ambiguous permissions, no quality traceability, no structural separation between discovery and verification.

**Orchestrator profile for routing** — routing becomes a reasoning step that's hard to audit; if the orchestrator makes a wrong assignment, the failure is invisible until the wrong profile runs.

**LLM-as-Reviewer** — confidently wrong on hallucinated citations; converts a structural gate into a probabilistic one that fails on exactly the inputs it needs to catch.


---

<!-- source: adr/03-structural-review-gate.md -->

# ADR-03: Review gate is structural, enforced by the policy MCP

## Context

Canonical zones (*v0.1.0-alpha.2: `notes/claims/` and `notes/hubs/`, per [ADR-47](47-type-first-category-folders.md); Project gate thesis promotion adds a project-scoped review path; the deliverable zone remains later work. Originally `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`*) must only receive content that a human has reviewed and approved. The question is whether this guarantee lives in prompt instructions, agent conventions, or infrastructure.

## Decision

The review gate is enforced by the **policy MCP** at the filesystem level. Any write targeting a review-gated zone is degraded to `dry_run` — the write does not reach disk — regardless of which profile requests it and regardless of what the profile's prompt says. The human's `review_status: approved` on the board card is the only path to canonical.

This is not a naming convention or a prompt instruction. A profile that "decides" to canonize directly cannot, because the file-system call returns before content reaches disk.

## Why

Prompt-based rules have a mean time to failure: they degrade at long context, can be overridden by later instructions, and don't survive session restarts. Structural enforcement doesn't degrade.

The specific failure mode that matters: hallucinated citations and fabricated claims are emitted with high fluency and high confidence. An advisory gate that fires on low-confidence outputs would wave through exactly the outputs the gate exists to catch. The gate must be unconditional — it cannot be confidence-routed.

The cost is that the human is a bottleneck. This is the point: the human must stay in contact with what the system produces. A system that can autonomously populate the synthesis zone without human attention has removed the epistemic guarantee that makes the vault trustworthy.

## Consequences

- Review-gated zones are hardcoded in the policy MCP configuration; they cannot be bypassed by profile prompt or lane-override.
- Every write to the vault is intercepted, logged with a SHA-256 hash, and auditable.
- The board's `review_status` field is the authoritative state of human approval — not comments, tags, or conversations.
- A WIP cap on done-awaiting-review cards creates back-pressure: when the human's review queue is full, the dispatcher slows new card creation on that lane.

## Promotion within synthesis is also manual

The same principle governs promotion, not just writes: maturity moves only by a human setting it (*v0.1.0-alpha.2 update: the `reference` type/layer is retired by [ADR-50](50-universal-lifecycle-and-maturity.md) — an `evergreen` claim is itself the settled unit; the human-only rule on `maturity` is unchanged*). Originally: a `claim-note` graduated to the `reference` layer only by a human setting `maturity: evergreen` in the weekly review — never by an automatic maturity threshold or a link-density heuristic. (Inlink count signals "well-cited," not "stable enough for reference"; contested claims accumulate inlinks too.) *Folded in from the former ADR-2 (a renumbered draft on auto-promotion, unrelated to the current [ADR-02](02-seven-specialist-profiles.md)), which was only ever `proposed`.*

## Alternatives considered

**Prompt-based rule ("always wait for review")** — degrades at long context; overrideable; doesn't survive session restart.

**Advisory LLM reviewer** — confidently wrong on exactly the inputs the gate needs to catch. Converts a structural guarantee into a probabilistic one.

**Confidence-routed gate (SmartPause)** — routes to human only when agent confidence is low. Fails because hallucinated citations are emitted with high confidence. See [Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md).


---

<!-- source: adr/04-lifecycle-over-topic-folders.md -->

# ADR-04: Folders encode lifecycle stage, not subject area

> **Verified on-box 2026-06-21 (mechanism note).** "`Librarian` writes to `20-sources/`,
> never to `30-synthesis/`" (Why, below) is enforced by the **policy gate** — lane-override
> `allow.write`/`deny.write` globs + the gate's default-deny (`src/.memoria/mcp/policy_hook.py`,
> `decision.py`) — not by the folder. Folders are inert: they route and document ("what kind
> of note is this"), they do not stop a write. The lifecycle-folder decision stands; only the
> enforcement attribution is corrected. Per AGENTS.md "Enforcement is a mechanism, not a label."

## Context

The vault needs an organizing principle for its folder structure. The obvious choice is subject area — put all cognitive science notes in `cognitive-science/`. The alternative is lifecycle stage — put all sources in `20-sources/`, all synthesis in `30-synthesis/`, regardless of topic.

## Decision

Top-level vault folders encode **lifecycle stage**, not subject area. A paper about attention lives in `20-sources/01-papers/`, not `cognitive-science/`. Topics live in frontmatter (`topic:`, `methods:`, `domain:`). The folder says "what this note is"; frontmatter says "what it's about."

The one exception is `40-workbench/`: its unit is the **project** (a bounded transient effort), not the lifecycle stage. Within a project folder, artifacts are organized by sub-stage (`01-map/`, `02-framing/`, etc.).

## Why

Topic folders fail because topics are many-to-many: a paper on attention and working memory belongs in `cognitive-science/` and `neuroscience/` and `HCI/`. Either you duplicate the note (it immediately diverges), pick one folder arbitrarily (you lose the other connections), or accept that the folder adds no information (so why have it?).

Lifecycle stage is one-to-one: a note is at exactly one stage. This makes the folder load-bearing — it tells the agent and the human what kind of thing a note is, not what it's about. Agent permissions align with stages (`Librarian` writes to `20-sources/`, never to `30-synthesis/`). Queries separate cleanly: "what notes are in the inbox?" uses the folder; "what notes are about attention?" uses frontmatter.

## Consequences

- Six numbered top-level folders: `00-meta/`, `10-inbox/`, `20-sources/`, `30-synthesis/`, `40-workbench/`, `50-deliverables/`.
- Topics, methods, domains belong in YAML frontmatter, not folder paths.
- The Linter validates that notes are in their correct lifecycle folder; a `claim-note` in the inbox or a `paper-note` in synthesis is a structural error.
- Navigation by topic is via Maps of Content (MOCs) in `30-synthesis/03-moc/`, not folder hierarchy.

## Alternatives considered

**Topic folders** — many-to-many problem produces duplication or meaningless catch-alls; agent permissions become ambiguous (the agent's permission must span all topic folders, which is the same as "all paths").

**Hybrid (topic + stage)** — adds complexity with no benefit; the topic dimension belongs in frontmatter where it can be queried correctly.


---

<!-- source: adr/05-zotero-as-bibliographic-backbone.md -->

# ADR-05: Zotero + Better BibTeX as the bibliographic backbone

## Context

Memoria needs a canonical source for bibliographic metadata — author, title, year, venue, DOI, PDF location — that is authoritative, human-maintained, and accessible to agents. Several options exist: manage metadata directly in Obsidian frontmatter, use a dedicated reference manager, or pull from external APIs on demand.

## Decision

**Zotero** is the bibliographic backbone. Every citable source has a Zotero entry with a pinned **Better BibTeX (BBT)** citekey before the paper note is created. The vault's `memoria.bib` (auto-exported by Zotero on changes) is the source of truth for citation metadata. The Librarian reads from it; it never writes to it.

Citekeys follow the convention defined in [ADR-06](06-citekey-naming-convention.md).

## Why

Zotero is battle-tested, has broad metadata ingestion (DOI, ISBN, URL, PDF drag-and-drop), and Zotero's storage keeps the canonical PDF. Better BibTeX provides stable, pinnable citekeys — without pinning, a metadata change regenerates the key and silently breaks every wikilink in the vault.

The alternative of managing metadata in Obsidian frontmatter puts Memoria in the business of building a reference manager, with none of the ingestion support, deduplication, or field-normalization that Zotero provides. External-API-on-demand has no offline guarantee and no single source of truth.

## Consequences

- A source must be in Zotero with a pinned BBT citekey before ingestion. The Librarian's ingest workflow fails if a citekey is missing.
- The `memoria.bib` file lives at `.memoria/memoria.bib`. The starter ships an **empty tracked stub** so the citation plugin loads on first launch; the **populated** bib is **gitignored** (`vault/.gitignore`) because it is large and user-specific — each setup's Zotero auto-export overwrites the stub locally and is never committed.
- PDFs live in Zotero's storage; paper notes reference them via `pdf_uri`, not by copying the file into the vault.
- Obsidian-native Zotero connectors (ZotLit, zotero-integration) are evaluated but not adopted — see the [connector comparison](../reference/zotero-plugins.md); the reasoning is in *Alternatives considered* below.

## Alternatives considered

**Frontmatter-only metadata** — requires Memoria to implement deduplication, field normalization, and PDF management; Zotero already does all of this better.

**ZotLit** (Obsidian plugin, reads Zotero's SQLite directly) — held as a *future migration target*, not adopted now. It is genuinely faster for bulk imports, but the daily one-paper-at-a-time flow doesn't justify the migration cost (re-aligning the paper-note template, re-validating the schema), and its Zotero 7 compatibility is unresolved. Adopt only when bulk-import volume — e.g. a scoping or systematic review ingesting dozens of papers at once — justifies it **and** Zotero 7 stability is confirmed. On migration the load-bearing settings are `databaseDir`, a `citationLibrary` matching the same Better BibTeX export so citekey vocabulary stays stable, and a `noteTemplate` reproducing the `_proposed_classification` / `_enrichment` blocks.

**zotero-integration** (Obsidian plugin, Better BibTeX HTTP API) — evaluated, not in use. More capable than the BibTeX-file connector (color-coded annotation import, Nunjucks templates), but it only wins if PDF annotation moves *out* of Obsidian and *into* Zotero. Memoria's design keeps annotation in Obsidian via pdf-plus, so flipping that direction is a change to the human's daily rhythm, not a plugin swap.

**External APIs on demand** — no offline guarantee; no single source of truth; metadata fetched differently on different runs produces drift.


---

<!-- source: adr/06-citekey-naming-convention.md -->

# ADR-06: Citekey naming convention

## Context

Citekeys are the load-bearing identifier for every paper-note (`@mamykina2010sense`). The Better BibTeX (BBT) format determines what gets generated; the convention determines whether the keys remain stable and readable across thousands of papers.

## Decision

Adopt **`authoryearword`** as the standard citekey format. Exact BBT format string (paste into Better BibTeX → Citation key formula):

```text
[auth.lower][year][shorttitle1_0]
```

This produces `mamykina2010sense` from a Mamykina 2010 paper titled "Sense and sensibility..." — surname lowercase, four-digit year, and the first significant title word via `shorttitle(1,0)` (one whole word, no fixed character count — do **not** substitute `condense:N`). **Pin the key in Zotero immediately after import** so subsequent metadata edits don't regenerate it.

## Consequences

- Keys are short, human-readable, and stable.
- Collisions are rare (different authors + same year + same title-word is uncommon); when they occur, BBT appends a disambiguator.
- The pin-immediately discipline is non-negotiable — without it, edits to Zotero metadata regenerate keys and break every wikilink pointing to the old key.

## Alternatives considered

**Stricter conventions** (e.g., full first-author surname + year + DOI suffix) were rejected because they sacrifice readability for marginal collision-resistance. The corpus's actual collision rate is well below the threshold that would justify the noise.

**Looser conventions** (e.g., year + arbitrary slug) were rejected because they lose the author-as-mnemonic property that makes citekeys readable in prose.

## Related

- **Workflows affected:** [Zotero capture](../how-to-guides/library/capture-and-ingest.md), [Ingest](../reference/ingest.md)
- **Files affected:** [The vault](../explanation/architecture/vault.md), `system/templates/paper.md` (in the starter vault)


---

<!-- source: adr/07-delegate-coding-to-external-agents.md -->

# ADR-07: Code agent attachment

## Context

> *Note (v0.1.0-alpha.2): "Coder" below is the profile's original name — [ADR-48](48-copi-and-agent-consolidation.md) renamed it the **Engineer** (`memoria-engineer`, lane-override `engineer.yaml`). The delegate-don't-implement decision is unchanged.*

Does the Coder profile delegate substantive coding work to an external coding agent (Kilocode, Aider, Claude Code, Codex), or implement coding capabilities itself?

## Decision

**Delegate.** The Coder profile scaffolds `code-note` handoffs with vault context (motivating sources, project links, purpose) and coordinates the review gate. The actual code editing happens in a specialized external agent running as a peer with a shared filesystem. The full setup pattern lives in [create a code artifact](../how-to-guides/project/create-a-code-artifact.md).

> **Current vs. planned agents.** The shipped Engineer lane wires **`codex` and `claude-code`** as the current external coding agents — the agent IDs referenced in `memoria-engineer/distribution.yaml` (env keys per agent), with the lane scoped by `lane-overrides/engineer.yaml`. **Kilo Code and Aider are planned future additions**, not yet wired. (`kilocode` today is the Engineer's *model provider* in `config.yaml`, distinct from a coding-agent skill.)

## Consequences

- The Coder profile stays narrow (scaffold + document); doesn't accumulate coding complexity it wasn't designed for.
- Human can use whichever coding agent fits the project (Claude Code for unfamiliar codebases, Aider for fast diffs, etc.).
- Adds a tool dependency — the human must install and configure one of the external agents.
- The same parallel-agents-with-shared-filesystem pattern generalizes to rendering agents ([open-design](../how-to-guides/project/create-a-code-artifact.md)).

## Alternatives considered

**Coder runs code itself** (in-profile execution): rejected because it conflates research-side Hermes (curating provenance) with code-side tools (editing files, running tests). Mixing the two would either bloat the Hermes side with redundant coding capabilities or leave the code-side underdeveloped relative to specialized tools.

## Related

- **Workflows affected:** [Code](../how-to-guides/project/create-a-code-artifact.md)
- **Files affected:** [The Coder](../explanation/profiles/engineer.md), [create a code artifact](../how-to-guides/project/create-a-code-artifact.md), `99-system/templates/code-note.md` (in the starter vault)


---

<!-- source: adr/08-typed-relations-frontmatter.md -->

# ADR-08: Typed `relations:` frontmatter

## Context

Plain wikilinks record *that* two claims relate, not *how*. Graph queries and argument-construction operations — "what contradicts X", "what supports X", "what methods feed this lineage" — can't be answered from untyped links. [ADR-10](10-claim-supersession.md) — ratified together with this ADR on 2026-05-29 — carves out the one correctness-critical typed relation (`superseded_by`, top-level) as a slice of this namespace, and [ADR-9](09-contradictions-dashboard.md)'s contradictions dashboard needs `contradicts` to have data to read. The original deferral assumed typed links would be a per-link maintenance burden; the question is whether that cost is real once the relation is *opt-in*.

## Decision

Adopt a **`relations:` frontmatter block** on claim-notes for *associative* typed links, **human-set and opt-in**. The v1 vocabulary is deliberately small — `supports` (directional: this claim supports the target) and `contradicts` (symmetric: the two claims disagree). The block is **nested** (matching the `relations: { … }` notation [ADR-9](09-contradictions-dashboard.md) assumes); new relation types are added to the [schema reference](../reference/frontmatter.md) on felt need, not coined ad hoc. The temporal relations `supersedes` / `superseded_by` stay **top-level** as [ADR-10](10-claim-supersession.md) shipped them — they govern a claim's *currency* (a value property), distinct from the *associative* links in `relations:`. Typed links are opt-in: untyped wikilinks remain first-class and coexist; the agent may *propose* a relation into `_proposed_classification`, but never writes one onto a canonical note.

## Consequences

- Unblocks [ADR-9](09-contradictions-dashboard.md): the contradictions dashboard now has `relations.contradicts` to query.
- Adopting the *namespace* costs nothing when unused — opt-in means that below the density where typed links pay off they simply stay sparse; there is no "populate every link" burden. This is what made the earlier deferral unnecessary: the cost had been modeled as mandatory.
- Adds a small schema obligation: a `relations` controlled vocabulary in the [schema reference](../reference/frontmatter.md), a `schema_version` bump on the claim-note template, and a Linter check that flags `relations:` keys outside the vocabulary.
- Richer link semantics (a `relation_type:`-per-link list, an expanded PARNESS-style vocabulary — PARNESS: a typed-relation scheme covering supports, refutes, extends, uses, and similar rhetorical moves between claims) and an **NLI candidate-proposer** for `contradicts` remain future work — see [Retrieval and schema extensions](65-retrieval-and-schema-extensions.md) and [Classical method displacements](59-classical-method-displacements.md). v1 is human-noticed, human-typed.

## Alternatives considered

**Keep deferring** (plain wikilinks only): rejected — the maintenance cost that justified the deferral assumed *every* link must be typed; an opt-in namespace removes that, and ADR-9 plus the supersession work ([ADR-10](10-claim-supersession.md)) make the felt need concrete.

**Flat top-level keys** (`supports:`, `contradicts:` at the top level): rejected — pollutes the top-level namespace and diverges from ADR-9's `relations: { … }` notation; the nested block groups associative links under one key.

**Fold supersession into `relations:`**: rejected — `superseded_by` derives a claim's *currency* and the Linter FAMA check keys on its top-level presence ([ADR-10](10-claim-supersession.md)); moving it would re-open an accepted decision and force a field-relocation migration for no semantic gain. Temporal currency and associative relation stay distinct.

**Agent-assigned relations**: rejected — typing a link is a canonical-surface judgment; the agent proposes, the human sets (the autonomy boundary, consistent with ADR-10).

## Related

- **Workflows affected:** [Distill](../how-to-guides/knowledge/write-a-claim-note.md) (where `contradicts` / `supports` are set), [Promote](../how-to-guides/knowledge/promote-a-claim.md), [Query](../how-to-guides/knowledge/query-the-vault.md) (relation-aware retrieval).
- **Files affected:** [Frontmatter fields](../reference/frontmatter.md) (the `relations:` namespace + vocabulary), [Document types](../reference/document-types.md) + `99-system/templates/claim-note.md`, the Linter's `structural-detectors.md` (vocabulary check), [contradictions dashboard](../explanation/dashboards/synthesis-agenda/contradictions.md) (consumer).
- **Required by:** [ADR-9 (Contradictions dashboard)](09-contradictions-dashboard.md) — now unblocked.
- **Related decisions:** [ADR-10 claim supersession](10-claim-supersession.md) (the temporal relation kept top-level; this generalizes the associative rest).


---

<!-- source: adr/09-contradictions-dashboard.md -->

# ADR-09: Contradictions / tensions dashboard

## Context

At low claim-note density the human holds conflicts in their head; as claims accumulate across projects and MOCs, contradictions hide in the long tail — two papers years apart, in different MOCs, never read side by side. A dashboard that surfaces "claims I've filed that disagree with each other" is a high-value synthesis starting point. With [ADR-8](08-typed-relations-frontmatter.md) now adopting the `relations:` namespace (including `contradicts`), the data the dashboard needs exists.

## Decision

Adopt a **`contradictions` dashboard** (ships at `system/dashboards/contradictions.md`, Dataview over the vault). v1 reads **human-set** `links.contradicts` links (ADR-52 renamed the old `relations:` namespace to `links:`) and lists the conflicting claim pairs for review — **no LLM judgment in the rollup**, consistent with the deterministic discipline of the other dashboards. The dashboard frames pairs as "worth resolving," never as defects (a paper refuting an earlier one is a wanted finding, not an error). An **NLI-based candidate proposer** — which would *suggest* contradictions for the human to confirm — is explicitly **out of v1 scope**; it remains future work ([Classical method displacements](59-classical-method-displacements.md)), to be added when claim density makes manual noticing insufficient.

## Consequences

- Contradictions become queryable instead of held in memory — the synthesis value the dashboard exists for.
- v1 is only as complete as the human's `contradicts` links; until those are filed the dashboard is sparse. That day-one emptiness is the signal that tells you whether the NLI proposer is worth building — expansion-threshold discipline.
- Adds one dashboard design summary plus a runtime Dataview page; consumes the `links.contradicts` edges (ADR-8's `relations.contradicts`, renamed by [ADR-52](52-links-vs-relationships.md)). No new judgment surface and no LLM in the rollup.

## Alternatives considered

**LLM-judged contradictions** (let an LLM read the corpus and flag tensions): rejected — LLM-as-similarity-judge has the calibration problem named in [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md); different runs surface different tensions with no stable ground truth. The memory-benchmark review ([Measurement and verification harnesses](62-measurement-and-verification-harnesses.md)) independently confirms LLM memory/similarity judgments are unreliable.

**Ship the NLI proposer in v1**: deferred, not rejected — NLI is deterministic and the right eventual proposer ([Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md)), but building it before the manual dashboard proves demand inverts the expansion-threshold rule. v1 ships the surface; the proposer graduates later.

## Related

- **Depends on:** [ADR-8 typed relations](08-typed-relations-frontmatter.md) (supplies the contradicts edges — now `links.contradicts` after [ADR-52](52-links-vs-relationships.md)).
- **Files affected:** [contradictions dashboard](../explanation/dashboards/synthesis-agenda/contradictions.md) (new), [Dashboards](../explanation/dashboards/README.md) (index).
- **Future proposer:** [Classical method displacements](59-classical-method-displacements.md) — the deterministic NLI candidate-generation engine that populates v2.
- **Related decisions:** [ADR-10 claim supersession](10-claim-supersession.md) (supersession is the temporal complement to contradiction).


---

<!-- source: adr/10-claim-supersession.md -->

# ADR-10: Claim supersession relation

> *Terminology note (v0.1.0-alpha.2): the lifecycle chain is now `proposed → provisional → current → retracted → archived` ([ADR-50](50-universal-lifecycle-and-maturity.md)); the `dormant` value referenced below is retired. The supersession decision (a `superseded_by` pointer, distinct from lifecycle) is unchanged — and `retracted` now carries the invalidated-claim case this ADR motivates.*

> **Verified on-box 2026-06-21.** The default query path now runs through
> `src/.memoria/mcp/qmd_filter_mcp.py`, which preserves qmd's tool surface while
> excluding claim notes with `superseded_by` unless the caller passes
> `include_superseded: true` for historical lookup. The FAMA-style draft linter
> remains a separate follow-up.

## Context

The claim-note schema records how *developed* a claim is (`maturity`: seedling → budding → evergreen) and how *durable* a note is (`lifecycle`: proposed → current → dormant → archived), but nothing records that a claim has been **overturned by a newer one**. An `evergreen` claim that a later finding invalidated is structurally indistinguishable from one that still holds, so `query`/`write` can resurface a stale belief as current. This is precisely the failure the long-term-memory literature isolates: **Memora**'s FAMA metric exists to penalize reuse of obsolete/invalidated memory, and **ClawArena**'s finding is "revise, don't accumulate." That same literature shows supersession is the *least reliably automatable* memory capability — which argues it must be carried by **structure** (human-set, agent-maintained), the "bookkeeping, not intelligence" principle Memoria is founded on. Existing pieces don't cover it: `contradicts` ([ADR-8](08-typed-relations-frontmatter.md)) is symmetric disagreement between coexisting claims, not directional replacement over time; the contradictions dashboard ([ADR-9](09-contradictions-dashboard.md)) surfaces coexisting contradictions, not directional replacement over time; and `drift-watch` tracks structural/config drift, not claim staleness.

## Decision

A claim note records that it has been overturned with a single typed relation,
`superseded_by: [[newer-claim]]` (optional inverse `supersedes:` on the newer note
for navigation). A claim's currency — **current vs. superseded** — is *derived from
the presence of `superseded_by`*, not stored as a separate field, so there is one
source of truth and no new controlled vocabulary. The link is **human-set**: the
agent may propose a supersession candidate (e.g., ingest surfaces a paper that
updates an existing claim) into the proposal namespace for review, but never writes
the link itself. Downstream, `query` and `write` exclude superseded claims by
default, and a later Linter slice should add a FAMA-style detector that flags any
draft or answer citing a superseded claim. This one relation is adopted as a
**correctness-critical slice** of the [ADR-8](08-typed-relations-frontmatter.md)
typed-relations namespace, which shipped on the same date.

## Consequences

- Drift becomes reliable **bookkeeping** (a human-set link at the moment of replacement) instead of unreliable inference — the one way the literature says this capability can be made dependable.
- Enables filtering superseded claims out of `query`/`write` and leaves a clear
  hook for a later FAMA-style Linter check — closing the current query-currency
  gap without pretending the draft-citation detector has shipped.
- Advances the supersession slice without committing to full typed relations (ADR-8) or the contradictions dashboard (ADR-9); it is a deliberate partial adoption of ADR-8's namespace.
- Adds a small schema obligation to the claim-note template (a `schema_version` bump) and one maintenance step when a claim is replaced.
- v1 treats supersession as whole-claim and binary; *partial* supersession (a claim overturned only in part) is not modeled and is left to a future refinement.

## Alternatives considered

**Defer alongside ADR-8** (treat supersession as just another typed relation, gated on corpus density): rejected. Generic relations had been deferred (ADR-8 was ratified together with this ADR on 2026-05-29) because their *omission only blocks queries*; supersession's omission causes a *correctness failure* (surfacing a stale claim as current — the FAMA failure mode). Its cost/benefit is inverted from generic relations — low marginal cost (one human-set link at a natural moment), high cost-of-omission — so it warrants carving out.

**Reuse `lifecycle: dormant`/`archived`** to mark superseded claims: rejected. Lifecycle is about durability/activity, not validity, and carries no pointer to the replacement, so you can neither reliably filter "current belief" nor trace what replaced what. A lifecycle transition may *accompany* supersession but is not sufficient.

**Reuse `contradicts`**: rejected. Contradiction is symmetric disagreement between claims that coexist; supersession is directional replacement over time. Conflating them loses the "which one is current" signal that the whole mechanism exists to provide.

**LLM-detected supersession** (let a model flag overturned claims): rejected for the same reason [ADR-9](09-contradictions-dashboard.md) rejected LLM-judged contradictions — non-deterministic, no stable ground truth — and reinforced by the memory-benchmark evidence (Memora, MemoryAgentBench) that LLM memory judgments are unreliable. The agent proposes candidates; the human sets the link.

## Related

- **Workflows affected:** [Distill](../how-to-guides/knowledge/write-a-claim-note.md), [Promote](../how-to-guides/knowledge/promote-a-claim.md) (where the link is set), [Query](../how-to-guides/knowledge/query-the-vault.md) / [Write](../how-to-guides/project/draft-with-writer.md) (filter superseded claims), and later [Verify](../how-to-guides/project/verify-and-revise.md) once the FAMA-style draft detector ships.
- **Files affected:** [Frontmatter fields](../reference/frontmatter.md) (add the relation), [Document types](../reference/document-types.md), the claim template, and `src/.memoria/mcp/qmd_filter_mcp.py`.
- **Related decisions / Depends on:** [ADR-8 typed relations](08-typed-relations-frontmatter.md) (adopts one relation from its namespace ahead of the rest); [ADR-9 contradictions dashboard](09-contradictions-dashboard.md) (supersession is the temporal complement to contradiction).
- **Source discussion:** benchmark review — [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (Change 1, and the benchmark detail); evidence from Memora/FAMA and ClawArena.


---

<!-- source: adr/11-vault-eval-maintenance.md -->

# ADR-11: vault-eval as a maintenance capability

> **Implementation status: shipped.** The gold set, the lane dispatcher (`operations/telemetry/eval/eval_dispatch.py`), the non-committing scratch contract, and the quarterly cron shipped first (0.1.0-alpha.1). The **scoring + observability** half landed with [#424](https://github.com/eranroseman/memoria-vault/issues/424): a deterministic scorer (`operations/telemetry/eval/eval_score.py` — the Linter's zero-LLM, report-only discipline, hosted with the sweeps engines beside the dispatcher) reads each card's machine-readable result block off the board, computes recall@k / support-rate / FAMA, appends per-run scores to `system/metrics/eval/runs.jsonl`, and the `eval-trend` dashboard renders the trend. The lane's rubric self-score on the card is recorded for comparison, never aggregated. The shipped source tree uses type-first homes (`src/system/eval/` and `src/system/metrics/eval/`) and now includes an `eval-task` note type; the older `99-system/eval/` path below is historical design prose.

## Context

`vault-eval` (an eval-harness scaffold) is Memoria's system-level evaluation — a small hand-curated gold set per workflow that measures whether the *deployed system* finds, verifies, answers, and remembers correctly *on this vault*, as opposed to off-the-shelf benchmarks that score a model on a foreign corpus (see [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md)). To be useful it must run against the live profiles and live with the vault, not persist as an external script. The question is how to host it without standing up a parallel subsystem; it splits into three sub-decisions — who owns it, whether it gates, and where the gold set lives.

## Decision

Memoria runs `vault-eval` as a **diagnostic maintenance capability built from existing machinery**, not a new subsystem:

- **Dispatch (board).** A scheduled `eval` card (quarterly + on-demand) fans each gold task out through the workflow's real profile command — `find` → Librarian, `verify` → the Verifier's `cite-check`, and so on — so the run exercises *deployed* profiles, not mocks.
- **Execution (Policy MCP).** Eval-context profile writes are non-committing: scoped to a scratch path and discarded after scoring, so a run never mutates the vault.
- **Scoring + verdict (Linter).** The Linter scores each run (deterministic metrics — recall@k, support-rate, FAMA — reusing the Verifier's entailment for `verify`), records a per-workflow score, and guards gold-set integrity (a gold item whose target path no longer resolves is a broken-reference finding, like any other).
- **Surfacing (observability).** Results append to `system/metrics/eval/` and trend on a dashboard. The verdict is **diagnostic, not gating** — unlike `drift-watch`'s structural FAIL, an eval dip informs the human; it does not pause scheduled work.
- **Gold set (vault).** Gold tasks live in `system/eval/` as `eval-task` notes.

## Consequences

- Reuses board dispatch, the Linter's health-reporting + broken-link detector, the Policy MCP, and the metrics log — no parallel system, and the harness tests the *deployed* profiles on the *real* vault.
- Gold-set rot (renamed/deleted target notes) is caught by machinery already running.
- Requires profiles to support a non-committing eval/dry-run mode — a real implementation cost — and adds one scheduled task, a scratch namespace, and gold-set upkeep.
- Diagnostic-only means a capability regression won't auto-halt work; the human must notice it on the dashboard. This is intentional, per [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) ("diagnostic, not contract").

## Alternatives considered

**Keep `vault-eval` as an external script outside the runtime** (don't integrate): rejected — it would drift from the deployed profiles, couldn't reuse the health/metrics machinery, and in practice wouldn't be run on a cadence.

**Gate scheduled work on the eval verdict** (like `drift-watch`'s FAIL): rejected — capability scores are noisy and, per `success-metrics.md`, diagnostic not contract; gating on them invites Goodharting and false halts.

**A dedicated eval-runner profile** (not the Linter): rejected for now — eval is a health-reporting concern the Linter already covers, and a new profile violates the expansion-threshold (add a profile only when an existing one is consistently overloaded). Revisit if eval orchestration outgrows the Linter.

**Gold tasks as a note type immediately**: originally rejected as premature; later
implementation crossed the threshold and added the `eval-task` type in `system/eval/`.

## Related

- **Workflows affected:** [Verify](../how-to-guides/project/verify-and-revise.md) (the eval reuses `cite-check`); the maintenance/`lint` surface (the Linter scores + reports).
- **Files affected:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md), [On-disk layout](../reference/on-disk-layout.md) (`system/eval/`, `system/metrics/eval/`), the Linter's `structural-detectors.md` and a dashboard (in the starter vault).
- **Related decisions / Depends on:** [ADR-10 claim supersession](10-claim-supersession.md) (the drift gold tasks exercise its FAMA check); [ADR-9 contradictions dashboard](09-contradictions-dashboard.md) and [ADR-8 typed relations](08-typed-relations-frontmatter.md) (shared observability lineage).
- **Source discussion:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (Observability + Integration); the `vault-eval` scaffold.


---

<!-- source: adr/12-obsidian-linter-reference-only.md -->

# ADR-12: obsidian-linter is reference-only, not a control-plane formatter

> **Update (2026-05-31): hardened to incompatible — do not install.** The original decision held obsidian-linter at "reference-only," documenting a de-fanged config for anyone who chose to run it anyway. The current verdict is stronger: **obsidian-linter cannot be used together with Memoria.** Two reinforcing reasons: (1) the [classification-storage decision](../reference/frontmatter.md) confirmed `_proposed_classification` / `_enrichment` are **YAML frontmatter namespaces the agent writes constantly** — so obsidian-linter's frontmatter rules (key-sort, timestamp, attribute insert/remove) are no longer a corner-case footgun but a guaranteed, continuous collision with a second frontmatter authority; and (2) whole-folder exclusion can't protect `40-workbench/` drafts, which are *both* human-edited and agent-written. The "run it carefully" path is withdrawn. The Decision/Consequences below are retained as the record of the original, milder ruling; where they say "not installed and not recommended," read "not compatible — do not install." The held config is preserved under *Held configuration (historical)* below — kept as the record of what was once proposed, not as a how-to.

## Context

The Obsidian Linter (platers/obsidian-linter) is a deterministic, on-save Markdown formatter — superficially aligned with Memoria's "bookkeeping, not intelligence" thesis, and previously carried in the `recommended/` plugin set with a carefully de-fanged config (agent/canonical folders excluded, frontmatter timestamp/insert/remove rules off, schema-aligned key sort, no HTML-comment rules). The question is whether a vault that already runs the **Memoria Linter** (deterministic structural validation under the Policy MCP, with an audit trail) and **markdownlint** (Markdown hygiene) should also ship a third formatter. Two prior commitments frame it: the Policy MCP makes every canonical write audited and hash-paired (a `before_hash`/`after_hash` per write), and frontmatter has a single declared authority ([Frontmatter fields](../reference/frontmatter.md)).

## Decision

Memoria treats obsidian-linter as **incompatible — do not install**: documented for the record only. (This is the hardened ruling per the Update banner above; it strengthens the original "reference-only … not installed and not recommended" verdict — no config makes the plugin safe to run alongside Memoria.) It must never act as a **control-plane formatter** — it never writes to Policy-MCP-audited zones, and it is never the authority for frontmatter or schema. The formatting concerns it would cover are owned elsewhere: the **Memoria Linter** owns frontmatter/schema validation and structural drift; **markdownlint** owns Markdown hygiene. The plugin's safe-config knowledge (folder exclusion, frontmatter rules off, the HTML-comment footgun) is preserved under *Held configuration (historical)* below in case a human chooses to run it anyway or the decision is revisited.

## Consequences

- One fewer formatter to install, configure, keep in sync with the schema, and re-audit on every upgrade (the HTML-comment-strip risk that would silently delete `_proposed_classification` / `_enrichment` blocks).
- No second frontmatter authority — the single-source-of-truth invariant for frontmatter is preserved by construction.
- The human loses on-save whitespace / key-sort tidiness on hand-written draft folders. This is the cost; it is judged marginal against markdownlint + the Memoria Linter already covering hygiene and structure.
- Moves obsidian-linter from `recommended/` (11 → 10) to `reference/` (3 → 4); the prior config doc is reframed as held knowledge.
- Reversible: the reference doc records the exact constraints under which it *could* be re-adopted (human-surface folders only, frontmatter rules off, never the control plane).

## Alternatives considered

**Keep it recommended, de-fanged (the prior state).** Rejected: even correctly scoped to human-only folders with frontmatter rules off, it duplicates work the Memoria Linter and markdownlint already own, and adds a standing upgrade-audit burden (diff the rule registry for HTML-comment rules every release) for marginal whitespace / key-sort value. The risk/benefit doesn't justify a place in the install set.

**Have the Memoria Linter profile *use* obsidian-linter.** Rejected on runtime grounds: obsidian-linter is TypeScript-in-Obsidian with no standalone CLI; the headless Linter profile can't call it as a library, and the deterministic formatting it needs it already performs directly (regex / markdownlint-class checks) under the audit trail.

**Remove it entirely (no doc).** Rejected: the de-fanged-config and HTML-comment-footgun knowledge is hard-won and worth keeping; `reference/` is exactly the "held, not installed" shelf for it.

## Held configuration (historical, not a how-to)

This records what was once proposed under the milder "reference-only" ruling, and why even a careful config does not rescue the plugin. The current verdict (the Update banner above) is that **no config makes it compatible** — this section is the evaluation record, not an enable path.

The constraints once proposed were: exclude every agent-managed folder via `foldersToIgnore`; `yaml-timestamp` / `insert-yaml-attributes` / `remove-yaml-keys` **off** (they fight the Librarian for the `_proposed_classification` / `_enrichment` frontmatter namespaces it writes on every ingest); `auto-correct-common-misspellings` **off** (it mangles domain terms, e.g. `JITAI`); and never enable any rule that rewrites or strips note content the agent owns.

**Why "just exclude the folders" doesn't rescue it.** The plugin has no per-folder rules — whole-folder `foldersToIgnore` exclusion is the only knob. But `40-workbench/` drafts are *both* human-edited (so you'd want on-save tidiness) *and* agent-written (so formatting corrupts state); no single exclusion list satisfies both. Whole-folder exclusion can keep the plugin off canonical zones but cannot make it safe on the one folder where on-save tidiness would actually help.

## Related

- **Files affected:** the `recommended/`→`reference/` reframing of the prior plugin doc (recommended 11→10, reference 3→4) is recorded in [Obsidian plugins](../reference/obsidian-plugins.md); the held config it carried is folded into this ADR (above).
- **Profiles affected:** the [Linter](../explanation/operations/README.md) — owns the formatting/validation concern obsidian-linter would otherwise touch.
- **Related decisions:** the frontmatter namespace discipline this protects ([Frontmatter fields](../reference/frontmatter.md)).
- **Source discussion:** the control-plane-authority analysis — a deterministic tool still fails the architecture if it writes outside the Policy MCP / audit trail.


---

<!-- source: adr/13-homepage-front-door.md -->

# ADR-13: Homepage front-door note, auto-opened by obsidian-homepage

## Context

Obsidian's default is to reopen the last-open notes, so a Memoria session lands wherever it left off. Memoria already designates [Daily Health](../explanation/dashboards/daily-glance/daily-health.md) as the dashboards' entry point, but there is no *vault* front door and no deterministic landing. The community offers two shapes: plugins that render their own start-page UI (e.g., obsidian-startpage), and plugins that simply open a chosen note on launch (obsidian-homepage). The choice is constrained by two Memoria invariants — every canonical write flows through the Policy MCP / audit trail ([ADR-12](12-obsidian-linter-reference-only.md)), and UI surfaces are **Dataview notes**, not plugin-rendered views ([obsidian](../explanation/obsidian/README.md)).

## Decision

Memoria ships a **plain Markdown front door** and opens it on startup with **[obsidian-homepage](../reference/obsidian-plugins.md)** (`recommended/`, not required). `home.md` began as the front-door note at the vault root: a thin **Dataview note** that led with the Daily Health glance, then linked the board, knowledge dashboards, and command-palette quick actions. *(Status note 2026-06-12: as written this said "ten shipped dashboards (incl. Daily Health, `daily-health.md`)" — since the design update, Daily Health is no longer a separate dashboard file; see [Dashboards](../reference/dashboards.md).)* *(Status note 2026-06-12, amended 2026-06-16: `home.md` was redesigned as a four-block control panel per [ADR-68](68-workspaces-desk-library-studio.md).)* *(Status note 2026-06-18, corrected 2026-06-21: [ADR-81](81-persistent-gate-dashboards.md) superseded the workspace-control-panel model. The Homepage plugin now opens `spaces/inbox`; `home.md` remains as a plain fallback note linking to the Inbox space. The decision preserved here is the view-management principle: obsidian-homepage opens a git-tracked note and writes nothing.)* obsidian-homepage is adopted because it is **view-management only — it opens a note and writes nothing**, so it never touches the Policy-MCP / audit invariants; it can run a "refresh Dataview" command on open. The launch view stays a git-tracked, lintable note.

## Consequences

- Deterministic landing: every session opens on the front door, not wherever the last one ended; a "home" command/ribbon jumps back.
- The home view is a Dataview note — version-controlled, lintable, embeddable — consistent with notes-as-dashboards. No plugin-rendered surface escapes the system's grain.
- One new `recommended/` plugin (UI-only, dependency-free, per-device) and one new vault note to keep *thin* (it must surface dashboards, not duplicate them).
- obsidian-homepage is QoL, not load-bearing: without it the human pins `home.md` manually; Memoria still works.
- Additive and reversible: `Daily Health` keeps its role as the dashboards' entry point; `Home` simply leads with it.

## Alternatives considered

**obsidian-startpage (plugin-rendered start page).** Rejected: its home view is a custom plugin UI, not a note — it can't embed Memoria's Dataview dashboards, isn't in git, isn't lintable, and exits the notes-as-dashboards discipline. That it writes nothing isn't sufficient; the *home view itself* must be a note.

**Heavy "home base" templates** (TaskNotes + Meta Bind + Buttons + Banners + …). Rejected: ~5–6 extra plugins for a productivity-app-shaped dashboard (pomodoro, daily tracker) — plugin sprawl against Memoria's minimalism. Their layouts are kept as design inspiration (reference), not installs.

**No plugin — rely on "reopen last session" + a pinned note.** Rejected as the default: it gives no deterministic landing, which is the whole value. It remains the zero-dependency fallback if the human declines the plugin.

## Related

- **Files affected:** [Home — the vault front door](../explanation/obsidian/home.md) (the front-door design + runtime scaffold), [Obsidian plugins](../reference/obsidian-plugins.md) (the obsidian-homepage plugin; recommended 10→11).
- **Related decisions:** [ADR-12 obsidian-linter reference-only](12-obsidian-linter-reference-only.md) — same control-plane test, opposite verdict (homepage opens a view and writes nothing; the linter wrote on save).
- **Surfaces:** [The Daily Health dashboard](../explanation/dashboards/daily-glance/daily-health.md) (Home leads with it), [Obsidian](../explanation/obsidian/README.md).


---

<!-- source: adr/14-advisor-review-vs-frozen-deliverable.md -->

# ADR-14: advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract

## Context

Memoria models a `deliverable` (`50-deliverables/`) as **terminal and frozen** — produced by
re-running Pandoc, never edited in place; if it needs changes you supersede it with a new
draft → export cycle ([Export routes and formats](../reference/export.md),
[Document types](../reference/document-types.md)). The current export path emits one thing: a
static citeproc `.docx` whose citations are frozen text.

This is correct for **final journal submission**. It has no answer for the **advisor-feedback
loop** that dominates the months *before* submission: a PhD student sends drafts to an advisor
who comments and tracks changes in Word/LibreOffice, and that round needs **live, editable
citation fields** (so the advisor can move, add, or restyle references) — exactly what a
frozen static export cannot provide. The predecessor (v1.5) design documented three live-citation
routes (`zotero.lua` Word fields, LibreOffice ODF Scan, Google Docs) and the hybrid
"draft in Obsidian, finish in Word." Memoria carried the static route and dropped the live one,
leaving the frozen-deliverable model implicitly responsible for a job it cannot do.

## Decision

A **deliverable is frozen and is produced by static Pandoc citeproc at submission time only.**
An **advisor-review export** — a live-citation `.docx`/`.odt` carrying editable Zotero fields —
is a **separate, explicitly non-deliverable working artifact.** It does **not** live in
`50-deliverables/`, is not subject to the "never edit in place" rule, and is regenerated from
the same draft whenever a new round is needed. The routes and their failure modes are
documented in [export a draft](../how-to-guides/project/export-a-draft.md); the
human chooses the target editor **before drafting**.

## Consequences

- The frozen-deliverable invariant is preserved by construction — live, hand-edited Word files
  never masquerade as deliverables, so `50-deliverables/` stays a clean record of what shipped.
- The real PhD workflow (advisor track-changes rounds) is supported instead of silently
  unsupported.
- One more documented export route to maintain (`zotero.lua` / ODF Scan) with real,
  named failure modes (`lpeg` on Windows; first-open `.docx` corruption) — mitigated by the
  "test on a single-citation doc first" guidance in export-targets.
- The human carries a new up-front decision — pick the final editor before drafting — because
  switching Obsidian → Google Docs late forces manual re-insertion of every citation.

## Alternatives considered

**Stretch the frozen-deliverable model to allow in-place edits for advisor rounds.** Rejected:
it destroys the invariant that `50-deliverables/` is terminal and auditable, and conflates a
mutable working file with a shipped artifact.

**Only ever ship static citeproc; tell advisors to comment on frozen text.** Rejected: frozen
citations can't be restyled or moved, and it fights the advisor's native Word/Zotero workflow —
the friction the live route exists to remove.

**Build a Memoria-native live-citation exporter.** Rejected as over-engineering: Zotero +
Better BibTeX + Pandoc already provide the routes; Memoria's job is to document and run them,
not reimplement citation-field injection.

## Related

- **Workflows affected:** [export a draft](../how-to-guides/project/export-a-draft.md) (companion how-to, added with this ADR), [Export routes and formats](../reference/export.md) (the existing static path)
- **Files affected:** the `deliverable` note type — [Document types](../reference/document-types.md)
- **Profiles:** [Coder](../explanation/profiles/engineer.md) runs the Pandoc mechanics


---

<!-- source: adr/15-project-membership-from-topic-hint.md -->

# ADR-15: project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed

> **Implementation status: built** ([#425](https://github.com/eranroseman/memoria-vault/issues/425)). The classify stage (`classify.py`, wired in `runner.py`) loads the optional `.memoria/project-hints.yaml` and scores each project's `primary_topics` against the paper's OpenAlex topic signals (topic names + subfields, kebab-case normalized; a hint matches a signal when equal or when all the hint's tokens appear in it). The ADR left the proposal rule open, so the implementation picked a conservative one: **every project with ≥ 1 overlapping hint topic is proposed, ranked by overlap count** — safe because it is a proposal the human confirms at triage, never an auto-apply. The proposal lands in `_proposed_classification.projects`; each decision (proposed or no-match) appends one `stage: project_hints` line to `system/logs/classify.jsonl` with the candidates and overlap counts (ADR-51 honesty — counts, not confidence). An absent hints file is a silent no-op (fully manual); a malformed one warns once on stderr and degrades to manual.

## Context

The predecessor vault defined **corpus profiles** — one per research project, each declaring
`expected_study_designs`, `expected_methods`, and `primary_topics`. At ingest the Librarian
scored a paper's abstract against every profile and proposed a `projects` value inside the
classification block, which the human corrected at triage.

In the current design the classification block survives (renamed `_proposed_classification`),
**but its project-scoring input is gone**: the starter vault ships no corpus profiles and no
`expected_*` matrices. So the Librarian can propose `study_design` / `methods` / `topic`, but
the structured signal that let it propose **project membership** specifically was dropped in the
redesign — leaving project assignment either fully manual or driven by an undocumented heuristic.
This ADR resolves which.

Two design forces pull against each other:

- The corpus-profile *scoring matrix* (`expected_study_designs` + `expected_methods` per project)
  is exactly the kind of human-maintained config that **drifts** — the redesign shed similar
  weight elsewhere, and [Frontmatter fields](../reference/frontmatter.md#the-field-kind-grammar)
  deliberately leaves `study_design` / `methods` / `topic` open rather than controlled.
- But "which of my projects does this paper belong to?" is a real, repetitive judgment the agent
  *can* usefully **propose** — losing it entirely pushes pure manual tagging onto the human.

## Decision

**Restore the minimal version, not the matrix.** Add an optional, lightweight per-project hint —
just `primary_topics` (and a free-text `description`) per project — that the Librarian scores by
**topic overlap** to **propose** a `projects` value in `_proposed_classification`. The human
confirms or corrects project membership at triage, exactly as for the other proposed fields.

Explicitly **do not** restore `expected_study_designs` / `expected_methods` scoring — design and
method are already proposed independently, and a per-project expectation matrix is drift-prone
config for marginal gain. A project hint is a *hint*, not a controlled vocabulary, so it does not
reopen the open-by-design choice for `study_design` / `methods` / `topic`.

```yaml
# .memoria/project-hints.yaml  (optional; absent = project membership is fully manual)
# The starter vault ships project-hints.yaml.example — copy to project-hints.yaml and edit.
projects:
  - id: phd-dissertation
    description: HCI + digital health — JITAI, receptivity, health coaching, equity, LLM mHealth.
    primary_topics: [jitai, receptivity-detection, health-coaching, mhealth, sensemaking, health-equity]
  - id: scoping-review
    description: Scoping review (replace with actual topic).
    primary_topics: [jitai, mhealth]
```

## Consequences

- The one capability genuinely lost in the redesign (agent-proposed project membership) is back,
  at minimal config cost — a short topic list per project, not a scoring matrix.
- "Agent proposes, human decides" holds: the `projects` proposal lands in
  `_proposed_classification` and is human-confirmed at triage like every other field.
- No new controlled vocabulary and no drift-prone expectation matrix — `primary_topics` is a hint
  the human edits freely; an absent `project-hints.yaml` simply means manual project tagging.
- The Librarian's classify step needs a small addition: score candidate `topic` values against
  each project's `primary_topics`, propose the best-overlap project(s). This lands with the
  Librarian's classify implementation, not before.

## Alternatives considered

**Restore the full corpus-profile matrix** (`expected_study_designs` + `expected_methods` +
`primary_topics`). Rejected: drift-prone human-maintained config for marginal benefit over topic
overlap; design/method are already proposed separately.

**Declare project assignment human-only; document the gap.** Defensible and zero-config, but
discards a genuinely useful, low-risk proposal the agent can make — it pushes repetitive tagging
fully onto the human for no architectural gain.

**Infer projects implicitly from topic without any hint file.** Rejected: an undocumented
heuristic is exactly the ambiguity this ADR exists to remove; the hint file makes the signal
explicit and auditable.

## Related

- **Source:** the predecessor vault's corpus-profiles mechanism (internal salvage analysis).
- **Profile:** [Librarian](../explanation/profiles/librarian.md) — owns classify / `_proposed_classification`.
- **Schema:** [Frontmatter fields](../reference/frontmatter.md) (`projects`, `_proposed_classification`).
- **Respects:** the open-by-design choice for `study_design` / `methods` / `topic` — see [frontmatter.md controlled vocabularies](../reference/frontmatter.md#the-field-kind-grammar); a project hint is not a controlled vocabulary.


---

<!-- source: adr/16-systematic-review-adopt-on-demand.md -->

# ADR-16: Adopt-on-demand — systematic-review tooling

Four feature clusters — **systematic-review mode**, **evidence-quality fields**, **pre-ingest screening**, and the **dual-rater workflow** — all add schema, fields, or workflow whose only purpose is to serve **formal scoping reviews and systematic reviews**. They share one rationale and are consolidated into this single decision; the table below records what is unique to each. (In an earlier draft these were four separate ADRs, now folded together here — the original draft numbers are not used, to avoid collision with the accepted ADR set.)

## The shared decision

Memoria does not carry systematic-review machinery in the baseline. Every field, flag, and pipeline in this cluster is **adopt-on-demand**: it activates per project, only while a formal review is actually running. Day-to-day reading, synthesis, and `find` stay free of it.

The reasoning is identical across all four:

- **Most notes would carry empty values.** Outside a systematic review, PRISMA fields, evidence-quality fields, and rater fields have nothing meaningful to hold; dashboards would spend their effort filtering blanks.
- **Premature schema is harder to remove than to add.** Additive fields introduced when a real protocol demands them cost less than schema that has to be deprecated once it proves unused.
- **The trigger is a felt need, not a threshold.** Adoption fires when a concrete review starts — a chapter, a paper, a protocol — not at a corpus-size count.

## The members

| Member | Unique contribution | Activation trigger |
|---|---|---|
| **Systematic-review mode** | `review_mode: systematic-review` flag + PRISMA fields (inclusion/exclusion, vote traces, multi-reviewer agreement) | A systematic review is actively running |
| **Evidence-quality fields** | Evidence-quality fields (`funding`, `coi`, `risk_of_bias`, `population`, `intervention_type`) on empirical papers | A project protocol or target journal requires them |
| **Pre-ingest screening** | A separate pre-ingest PRISMA + ASReview screening pipeline (200–5000 candidates) | Starting a formal scoping or systematic review |
| **Dual-rater workflow** | Dual-rater fields (`rater_1`, `rater_2`, `rater_agreement`) for inter-rater reliability | The chapter or paper requires reported agreement *and* a second human rater exists |

## Relationship to the candidate-note baseline

The candidate-note baseline is adjacent but **not** part of this deferred cluster — it was
adopted into baseline v0.1 independent of any formal review, because the shared
candidate schema pays off for everyday `find` on its own. The later
[ADR-51](51-inbox-category-and-honesty-card.md) Inbox contract supersedes the old
candidate-note routing shape. This cluster's pre-ingest screening pipeline consumes
the current Inbox/candidate schema once *it* activates.

## See also

- Glossary: **Review** — the systematic-review sense versus the board review gate and the weekly-review ritual ([Glossary](../reference/glossary.md)).


---

<!-- source: adr/17-shared-candidate-frontmatter.md -->

# ADR-17: Shared candidate frontmatter format

> **Accepted / implemented in v0.1 (2026-06-01).** The `candidate-note` (16th) type ships: template `99-system/templates/candidate-note.md`, registered in `document-types.md` / `frontmatter.md`, the `weekly-review` query wired, and Verifier gap-cards unified under `source: gap`.
>
> **Superseded 2026-06-16 on two axes — read both.**
> [ADR-50: One lifecycle chain for everything; maturity is a claim property; reference
> dropped; MOC renamed hub](50-universal-lifecycle-and-maturity.md) replaces the
> **lifecycle vocabulary** (it now owns the universal lifecycle chain), and
> [ADR-51: The Inbox category and the honesty card](51-inbox-category-and-honesty-card.md)
> replaces the **candidate-note routing** (Inbox categories and gap-card honesty). This
> record remains as the historical candidate-note design.

## Context

Candidate notes can arrive from four pipelines: `find` (forward/backward citation search), database-search (PRISMA-style bulk screening — see [ADR-16](16-systematic-review-adopt-on-demand.md) (pre-ingest screening, in the systematic-review cluster)), manual (human-typed lead), or **capture-timeout** (a Zotero capture whose ingestion gave up — see *Ingestion dead-letter* below). Without a shared schema, each pipeline produces its own slightly different frontmatter and dashboards must run separate queries.

### Two roles, one type: discovery inbox + ingestion dead-letter

The candidate-note earns its place by filling **two** gaps with one type, not by being an alternate front door for routine capture (deliberate single captures should still go straight to a `paper-note`/`item-note` — adding a candidate gate there is redundant friction).

1. **Discovery inbox.** Un-screened leads from `find` / database-search await a human include/exclude decision before any enrichment cost is paid.
2. **Ingestion dead-letter.** The normal path is `capture → ingest (≤60s) → paper-note`. When ingestion *fails* — API down, no PDF, stalled queue — the card today exhausts `max_retries` and sits at `blocked`, invisible in the vault. Instead, on `kanban_block` (give-up signal, not a wall-clock timer) the capture **materializes as a candidate-note** so nothing captured is ever lost; the human can retry the pipeline or discard it from a triage-able note rather than a parked board card. (Before the 16th type shipped, this degraded gracefully — a stalled capture simply stayed a `blocked` card.)

These two roles carry **different** `candidate_status` meanings (see below): a dead-letter candidate is *pending ingest-retry*; a discovery candidate is *pending include/exclude*. They trigger different next actions, so the status field must distinguish them.

## Decision

Adopt the unified frontmatter schema for candidate notes:

```yaml
type: candidate-note
source: find                     # find | database-search | manual | capture-timeout | gap
candidate_status: pending-screen # pending-screen | pending-ingest | included | excluded
exclusion_reason: ""
projects: []                     # plural list, matches other templates
```

`candidate_status` distinguishes the two roles:

- `pending-screen` — discovery lead awaiting a human include/exclude decision (`find` / database-search / manual / `gap` — a Verifier gap-card unified into this type at adoption).
- `pending-ingest` — a `capture-timeout` note whose ingestion gave up; awaiting a pipeline retry or discard.
- `included` / `excluded` — terminal screening outcomes; an `included` discovery candidate proceeds to ingestion, a successfully re-ingested `pending-ingest` note becomes a `paper-note`/`item-note` and the candidate is archived.

These are the candidate-specific fields; every note also carries the global required fields (`schema_version`, `created`, `updated`, `lifecycle`) — see [Frontmatter fields](../reference/frontmatter.md).

`candidate-note` is not in the 15 note types in [Document types](../reference/document-types.md#document-types); adopting this ADR means adding it as the 16th type with its own template (`99-system/templates/candidate-note.md`) and updating the list.

## Consequences

- A single Dataview query in [The weekly-review dashboard](../explanation/dashboards/structural-health/weekly-review.md) covers all candidate sources.
- Triage dashboards work uniformly regardless of where a candidate came from.
- **No captured source is silently lost.** Ingestion failures surface as triage-able dead-letter notes instead of `blocked` board cards, decoupling capture reliability from ingest reliability.
- Tiny schema cost; high payoff for any later screening work.
- Before the 16th note type was added in templates, both roles degraded gracefully: discovery queries returned no results, and a stalled capture stayed a `blocked` card. The type has since shipped (see the status note above), so both are now live.

## Alternatives considered

**Per-pipeline schemas**: rejected — duplicates effort and forces three parallel queries in every candidate dashboard.

**Hold off until [ADR-16](16-systematic-review-adopt-on-demand.md) is adopted**: rejected — the shared format pays off for `find` alone (the current primary candidate source), and adopting it later wouldn't be cheaper.

**Candidate-gate every capture** (route all Zotero captures through `candidate-note` first): rejected — a deliberate single capture *is* the screening decision, so a mandatory candidate stage adds redundant friction to the common path. The candidate-note earns its place at the *edges* (un-screened discovery leads, failed-ingest dead letters), not as the default front door.

## Related

- **Consumed by:** [ADR-16 pre-ingest screening](16-systematic-review-adopt-on-demand.md) — reads this schema for bulk screening.
- **Files affected:** [The vault](../explanation/architecture/vault.md), `99-system/templates/candidate-note.md` (to be created), [The weekly-review dashboard](../explanation/dashboards/structural-health/weekly-review.md)


---

<!-- source: adr/18-rename-agent-verdict.md -->

# ADR-18: Rename `agent_verdict` → `agent_recommendation`

> **Accepted / implemented in v0.1 (2026-06-01).** Renamed across the card schema,
> dashboards, the Linter SOUL.md, and the docs in one coordinated pass. The old
> name remains only in historical references.
>
> **Compatibility note (2026-06-21).** Runtime readers intentionally do **not**
> fall back to `agent_verdict`; the migration is one-way and tests pin that legacy
> fields are ignored. New writes and public schema/docs use `agent_recommendation`.

## What

The card-metadata field that holds the Verifier's or Linter's assessment of a `done` card is renamed from `agent_verdict` to `agent_recommendation`. Its value set is unchanged (`clean` / `issues-found` / `inconclusive`); only the field name changes, across the schema, `board_export.py`, dashboards, and the docs that reference it.

## Why

The field's name is in tension with its documented role. Every gloss describes it as a *recommendation* the human may override — "what does the checking agent advise? — separate from the human's decision" ([The board as a state machine (the control plane)](../explanation/workflows/board-as-state-machine.md)). But "verdict" connotes a *ruling*: final, authoritative, decided.

This matters more than ordinary word-choice because the board's central design move is keeping three dimensions distinct precisely so the agent's view cannot masquerade as the human's judgment ([Kanban board](../explanation/kanban-board/README.md)). "verdict" is the one word that quietly competes with `review_status` for "who decided" — eroding, in the field name itself, the very separation the three-dimension split exists to protect. `agent_recommendation` makes the name self-correcting: it reads as an input, not a decision, reinforcing "agents propose, humans dispose" without relying on the reader catching the gloss.

## Trade-offs

- **Migration cost.** The field is wired through the card schema, `board_export.py`, the board-state and fleet-health dashboards, and ~4 docs. A rename that misses a Dataview query fails *silently* — the `dashboard-field-drift` class — so it must be a single coordinated pass.
- **Ergonomics.** `agent_recommendation: clean` is wordier than `agent_verdict: clean` in frontmatter and dashboard tables.
- **Cheaper alternative exists.** A one-line clarification at the schema definition ("a recommendation, not a decision — the human overrides via `review_status`") captures most of the benefit at near-zero cost and is the recommended fallback if this rename isn't scheduled.



## Dependencies

- A complete inventory of consumers: card schema, `board_export.py`, `metrics_aggregate.py`, board-state + fleet-health dashboards, review-as-state / board-as-state-machine / kanban-board docs, and any Linter/Verifier output that writes the field.
- Best sequenced alongside any other v0.1 frontmatter/metadata migration so the consumer sweep runs once.


---

<!-- source: adr/19-moc-threshold-alert.md -->

# ADR-19: Agent-proposed hubs (threshold alert and Mapper handoff)

> **Tier 1 ships (status note, 2026-06-12).** The report-only check is implemented as the Linter's `hub-threshold` detector ([#426](https://github.com/eranroseman/memoria-vault/issues/426)). The chosen rule, where this ADR left the reading open: a "topic" is a term in a claim's `topics` list or a paper's `research_area` list (the paper-side topic facet the classify stage fills — papers carry no `topics` field); the threshold is **15 notes** (papers + claims combined, the lower edge of the ≥15–20 band in [Wikilink and link conventions](../reference/linking.md#hub-thresholds)); matching is case-insensitive; a topic already covered by a `hub` (or legacy `moc`) note — its `topic` or `title` matches the term — is suppressed. The finding is a LOW advisory ("consider creating a hub"), never auto-creation. **Tier 2 ships (status note, 2026-06-16).** The deterministic `hub_handoff.py` operation reads current `hub-threshold` findings and delegates a `map` lane card to the Librarian. The handoff is ceiling-validated by `tasks_mcp.py`, allows only `notes/fleeting/maps/` and `inbox/`, and explicitly forbids writes under `notes/hubs/`; the PI still creates or promotes the final hub.

> *Terminology note (v0.1.0-alpha.2): "MOC" is now the `hub` type ([ADR-50](50-universal-lifecycle-and-maturity.md)); "the Mapper" is the **Librarian's `map` lane** ([ADR-48](48-copi-and-agent-consolidation.md)); the `reference` type referenced below is retired ([ADR-50](50-universal-lifecycle-and-maturity.md)) — an `evergreen` claim is the settled unit. The threshold-alert decision is unchanged.*

## What

The system surfaces when a topic cluster has crossed the hub-creation threshold but has no hub yet, so the human is prompted to create one instead of having to notice the count by hand. Two tiers:

- **Tier 1 — threshold alert (report-only).** A Linter/dashboard signal: "topic `X` has 18 notes (papers + claim notes) and no hub — consider creating one." No agent-written content; it just makes the threshold crossing visible. Mirrors the existing report-only Linter idiom.
- **Tier 2 — Mapper hub proposal.** A `hub_handoff.py` operation reads fired `hub-threshold` findings and raises an idempotent `map` lane card. The Mapper drafts a **bare** hub proposal (schema-shaped frontmatter template + candidate member-note list + threshold evidence) under `notes/fleeting/maps/` and raises one Inbox candidate card for PI review. The stub is a member list only — never annotations or "why these belong" — and `notes/hubs/` remains review-gated.

## Why

There is an asymmetry in how human-owned synthesis types get agent help. A `reference-note` gets an agent-drafted starting point: the Writer's `promote` command proposes a claim→reference promotion the human finalizes ([Obsidian command palette](../reference/obsidian-command-palette.md)). A `hub` formerly got none — it is human-authored start to finish ([Build a Map of Content](../how-to-guides/knowledge/build-a-moc.md)), and the Mapper now receives the request as a `map` lane card rather than as a profile command.

Yet the Mapper already computes the exact signal a hub proposal needs: `cluster-map` finds dense topic clusters, and [Wikilink and link conventions](../reference/linking.md#hub-thresholds) defines the ≥15–20-note threshold that says "time for a hub." The capability is present; it is simply not wired to a proposal. Today the human must manually track note counts per topic to know when a hub is due — a bookkeeping task the system is otherwise built to absorb.

## Trade-offs

- **Tier 1** is nearly free and nearly risk-free: it reads counts the Linter already has access to and writes a report line. No new content, nothing to rubber-stamp.
- **Tier 2** adds a Mapper handoff, and carries a real hazard: an agent-listed membership *looks* curated but isn't, nudging the human toward rubber-stamping the indiscriminate "hub-as-folder-dump" the design explicitly warns against ([Common pitfalls](../explanation/knowledge/common-pitfalls.md)). The mitigation — stub is a member list + threshold note only, never annotations — must be enforced, because the annotation *is* the curation that defines the type, and that is the human's.



## Dependencies

- Linter running end-to-end (for the Tier 1 alert).
- Mapper `cluster-map` + the hub thresholds in [Wikilink and link conventions](../reference/linking.md#hub-thresholds) (already defined).
- Tier 2 is implemented by `operations/integrity/linter/hub_handoff.py` delegating through `tasks_mcp.py` to staging paths outside the review-gated zone.


---

<!-- source: adr/20-publication-path.md -->

# ADR-20: Publication path — vault-eval benchmark first, capture-now

## Context

When this was decided (pre-v0.1 ship), Memoria was a design artifact — rigorous and internally consistent, but it had not yet run a system, produced a benchmark, or surveyed the field. (v0.1 has since shipped and run end-to-end, but it has still produced no benchmark or published contribution, so the strategy below stands.) A 20-paper system survey plus a ~51-paper capability-mapped benchmark review established that no surveyed paper published on design alone; every one ran a system and measured something, shipped a benchmark, or organized the field. The strategic question — which publication shape to aim at, and what to do *first* — was open and blocking: it determines what gets built, what gets instrumented, and in what order. It is live now (not later) because the binding constraint is calendar time on data collection: publications need time series, and the un-backfillable signals (suggestion disposition, operator decision time) are lost forever if capture does not start at first ingest. The full analysis behind this decision — four candidate paths, evidence requirements, and the honest negative space — lives in the source report linked below.

## Decision

Memoria commits to a **two-part publication strategy**:

1. **Target Path 1 first: a vault-eval benchmark paper** (NeurIPS Datasets & Benchmarks track), instantiated via the tractable vault-CiteME within-corpus citation-attribution cell and grounded in the broader "does the vault compound?" framing of [ADR-11 vault-eval](11-vault-eval-maintenance.md). This is chosen over a system paper (Path 2), a position paper (Path 3), or an open-artifact release (Path 4) because it is the only path tractable in months rather than years, has the lowest coupling to a finished system (it needs the Verifier profile and a public fixture, not the whole stack), and forces the measurement layer every downstream path depends on into existence. The system/position papers are explicitly **deferred** until Path 1 has produced data; *which* of them follows is decided by the data, not now.

2. **Start the six-signal instrumented capture now** — the single highest-leverage action, independent of when paper-writing begins. The capture is minimal and adopted in v0.1 (the *analysis* harnesses in [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) stay deferred): state-transition timestamps, operator decision time, per-card cost, policy deny-reasons, suggestion disposition (accept : edit : reject), and FAMA exposure. Schemas are pinned in [Telemetry & logs](../reference/telemetry.md). Capture precedes analysis because capture cannot be back-filled.

## Consequences

- **Build order is now ordered by the paper, not by feature appeal.** The Verifier profile and a public vault-CiteME fixture are the critical path; everything else is downstream. The board-export cron (Phase 1 in the [timeline](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md)) becomes a publication prerequisite, not just an observability nicety — without it the board-state and cost logs never populate. The former cost/disposition gap is closed by [ADR-106](106-cost-and-disposition-capture.md): cost joins completed cards to the Hermes session store, and suggestion disposition is captured at the review action.
- **The de-risking is deliberate.** If within-vault citation-attribution numbers come out *worse* than public CiteME, the Verifier-as-gate thesis weakens — and we learn that before staking a system paper on it.
- **n=1 operator data is accepted as a known weakness** of the later system-paper path, to be mitigated by detailed logging and a within-subject comparison arm (blocking vs. advisory review, see [ADR-41](41-configurable-review-gate-mode.md)) rather than by more operators.
- **The novelty surface is fixed to a triad** — policy-MCP-enforced zone permissions, structurally blocking review state, and structural human-set claim supersession ([ADR-10](10-claim-supersession.md)) as the answer to the FAMA failure mode — plus the measurable knowledge-work consequences that only data can supply. We explicitly will **not** anchor a paper on the seven-profile design, the LLM-Wiki/Zettelkasten/Memex synthesis, or Obsidian-as-substrate; each is prior art or operational, not contributory.
- A higher-novelty framing (Path 1′, vault-eval as the contribution rather than vault-CiteME as an instance) remains available and costs more fixture work; the choice between the two framings is left to paper-drafting time and does not change this decision.

## Alternatives considered

**Lead with a system paper (Path 2).** Rejected as the *first* move: 6–9 months, requires the full MVS + Librarian + Verifier + Linter stack and a comparison study, and needs a defensible "operator hours saved per unit of vault growth" metric that does not yet exist in the field. It is the natural *second* paper once Path 1 has produced data.

**Lead with a position paper (Path 3).** Rejected as first: position papers without empirical work get rejected, and with strong empirical work they compete with full system papers — a narrow sweet spot. Its field-survey prerequisite is largely satisfied by the ~51-paper taxonomy, but it still needs the same empirical evidence as Path 2.

**Open-artifact release (Path 4).** Rejected as first: longest horizon — needs a real implementation, adopter-facing docs, and external adoption stories that take time to accumulate.

**Defer instrumentation until the system is "finished."** Rejected outright: disposition and decision-time signals cannot be reconstructed after the fact, so waiting discards the most valuable data permanently. Capture is decoupled from paper-writing and starts at first ingest.

## Related

- **Files affected:** [Telemetry & logs](../reference/telemetry.md) (the six-signal schemas), [Release plan — v0.1.0-alpha.1 — appendix](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md) (step 8, six-signal capture; board-export cron is the prerequisite).
- **Related decisions / Depends on:** [ADR-11 vault-eval](11-vault-eval-maintenance.md) (the eval program this paper instantiates); [ADR-10 claim supersession](10-claim-supersession.md) (the FAMA-exposure signal and a novelty-triad pillar); [ADR-03 structural review gate](03-structural-review-gate.md) (the blocking-review thesis the later system/position paper would test).
- **Proposals:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (analysis harnesses, deferred); [ADR-41](41-configurable-review-gate-mode.md) (the comparison arm); [ADR-106](106-cost-and-disposition-capture.md) (the cost/disposition capture path).
- **Supporting rationale:** [Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md), [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md), [Why the review gate is structural](../explanation/rationale/why-human-gate.md), [Intellectual foundations](../explanation/overview/intellectual-foundations.md).
- **Source discussion:** originally distilled from the working report `notes/publication-path-report.md` (retained outside the repo for provenance).


---

<!-- source: adr/21-l3-autonomy-ceiling.md -->

# ADR-21: L3 autonomy ceiling, structurally enforced (the Coder-lane exception is retired)

## Context

How far agent autonomy may extend is the single most consequential constraint in Memoria — it governs every future automation proposal — yet it was only ever argued in prose ([Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md), [What Memoria is](../explanation/overview/what-memoria-is.md)) and never recorded as a decision with a fixed anchor. The live question is concrete: [Karpathy](../reference/bibliography.md#karpathy-llm-wiki)'s autonomous keep/revert loop is safe only when three preconditions hold simultaneously — the metric is monotonic, changes are reversible, and experiments are independent. Knowledge synthesis fails all three: synthesis quality is not a scalar, synthesis errors persist and compound across everything that later cites them, and later sources reinterpret earlier ones. Without a recorded ceiling, each new "let the agent just do X overnight" proposal re-litigates this from scratch, and the boundary erodes by increments.

## Decision

Memoria targets **L3 on the [Chen et al. 2026](../reference/bibliography.md#chen2026autonomous) taxonomy** — multi-step autonomous execution under human-set strategy with per-batch review — and enforces that ceiling **structurally, through the policy MCP, not through prompt instructions**. Agents propose, classify, draft, and verify; they never canonize. Every promotion into `30-synthesis/` and `50-deliverables/` routes through the human review gate ([ADR-03](03-structural-review-gate.md)). Scheduled and overnight operations write to `10-inbox/` only. The single exception was the **Coder lane**: code artifacts satisfy all three preconditions (tests are a monotonic scalar, `git reset` makes changes reversible, experiments are independent), so an internal keep/revert experiment loop was admissible there, with outputs landing in the project code scratch and still requiring human review to promote. *(v0.1.0-alpha.2 update — **the exception is retired**: the Coder profile is gone ([ADR-48](48-copi-and-agent-consolidation.md)) and its successor, the Engineer, is MCP-only with no execution capability. **No autonomy exception exists anywhere.** The decision will be revisited only if the code lane / external-coding-agent path grows beyond the current Project gate handoff.)* L4 (self-directed synthesis) and L5 (self-directed agenda-setting) are out of scope by construction.

## Consequences

- Confidence-based autonomy refinements are foreclosed for the synthesis lanes: a future "only escalate low-confidence outputs" proposal is answered by this ADR, not re-argued.
- Budget discipline replaces metric discipline. Because there is no scalar payoff to optimize against, the nightly loop is bounded by a cost ceiling (~$1–3/day) rather than by a quality target.
- The human stays on the critical path for every canonical write. The mitigation for the resulting review load is "make each review cheaper, not fewer reviews" — a better Verifier, pre-verified material, structured evidence chains — never removing the gate.
- *(v0.1.0-alpha.2)* No lane carries an autonomous keep/revert loop. Introducing one anywhere — including a future code lane — requires revisiting this ADR explicitly.
- The discovery loop may run unattended because it only *finds and ingests* candidates into `10-inbox/`; the human reviews candidates before they enter canonical zones, so autonomous discovery does not breach the ceiling.

## Alternatives considered

**Full autonomy (L4/L5) on synthesis.** Rejected: this is what every autonomous research system (AI Scientist, AI co-scientist, CORAL, SciMON, Karpathy Autoresearch) does, and all of them rely on a single keep/revert scalar. No such scalar faithfully measures "is this a well-cited, non-redundant addition to the vault," and in durable knowledge work a wrong-but-kept claim compounds rather than wasting one run.

**Confidence-routing (SmartPause / AutoResearchClaw, [Liu et al. 2026](../reference/bibliography.md#liu2026autoresearchclaw)).** Rejected even though its ablation shows targeted gating beats both full autonomy and dense oversight. Hallucinated citations and fabricated numbers are emitted with high fluency and high confidence — confident-wrong is the failure mode the gate exists to catch, and a confidence signal is gameable by exactly that mode. The real insight (gate well, not everywhere) is kept, but spent on cheaper reviews rather than fewer.

## Related

- **Supporting rationale:** [Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md) (the preconditions argument and the Coder exception), [Why the review gate is structural](../explanation/rationale/why-human-gate.md), [What Memoria is](../explanation/overview/what-memoria-is.md) (autonomy-spectrum positioning, "vibe researching").
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the mechanism that enforces this ceiling); [ADR-07 external coding agent boundary](07-delegate-coding-to-external-agents.md) (the Coder lane this ADR carves the exception for).
- **Proposals bounded by this ADR:** the code-lane keep/revert experiment loop
  tracked in [ADR-61](61-nightly-discovery-loop.md); [Configurable review-gate mode
  (blocking | advisory) for comparison studies](41-configurable-review-gate-mode.md)
  (advisory-mode comparison arm).
- **Source discussion:** retroactively records a decision long embedded in `why-not-autonomous.md` and `what-memoria-is.md`. The reasoning lives in those `why-*` docs and may evolve; the ceiling recorded here does not move without a superseding ADR.


---

<!-- source: adr/22-build-on-hermes-runtime.md -->

# ADR-22: Build on the Hermes Agent runtime rather than a bespoke one

## Context

> *Note (v0.1.0-alpha.2): the "seven specialist `SOUL.md`s" below predates [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the fleet to **five** profiles; likewise the ADR-01 three-layer framing in Related was superseded by the seven-layer model ([ADR-46](46-seven-layer-architecture.md)). The build-on-Hermes decision itself is unchanged.*

Memoria's entire execution layer — the Kanban board, the worker profiles, the dispatcher, the programmatic API — is supplied by an external runtime, [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research). This is a foundational, hard-to-reverse dependency: it determines what the board *is*, how profiles claim work, and where integrations connect. The choice was explained at length in [Why Hermes](../explanation/rationale/why-hermes.md) but never recorded as a decision, so the alternatives that were weighed — and the precise Memoria/Hermes boundary — had no fixed anchor. An ADR matters here specifically to preserve *what was rejected and why*, which is the part most likely to be re-litigated when a shinier runtime appears.

## Decision

Memoria builds **on** Hermes rather than implementing its own runtime. Hermes owns the execution substrate: the persistent Kanban board (`kanban.db`) as a durable cross-session state machine, the profile mechanism (`SOUL.md` identity, `config.yaml` model routing, lane permissions), the dispatcher that claims `ready` cards and advances state with retries, and the native memory tiers, MCP host, and API server (port 8642). Memoria supplies only the *conventions on top* — the review-gate overlay in card `metadata`, the policy MCP that gates writes, the seven specialist `SOUL.md`s, and the vault schema — all riding Hermes's extension points without modifying it. The governing rule of thumb: **Hermes moves work; Memoria decides what work means and what may become canonical.**

## Consequences

- Memoria's design effort goes entirely into the knowledge layer, which is where its actual contribution lies; the hardest runtime problems (durable state across crashes, atomic card claiming, retry semantics, MCP hosting) are not Memoria's to solve.
- Memoria stays compatible with a stock Hermes install: the overlay lives in card `metadata` that Hermes treats as opaque, so the board works with standard Hermes tooling.
- The cost is a standing dependency on an external runtime's release cadence and conventions. This is accepted deliberately, and it is why [Hermes conventions are reused verbatim](../explanation/rationale/why-hermes.md) rather than renamed.
- The boundary is load-bearing: anything that would require *modifying* Hermes internals (rather than riding its MCP/metadata/lane extension points) is a signal the design has drifted and should be reconsidered against this ADR.
- The same "thin front over a mature external engine" logic recurs in [ADR-07](07-delegate-coding-to-external-agents.md) (Coder delegates to external coding agents); the two decisions share a rationale and should move together if that rationale is ever revisited.

## Alternatives considered

**Build a bespoke runtime.** Rejected: its hardest parts are exactly what Hermes already solves, so a reimplementation would be a worse copy plus a permanent maintenance burden, for no gain in the knowledge layer.

**AutoGen-style chat-as-substrate.** Rejected: routing durable work state through a conversation transcript puts state in the wrong layer. Memoria's state must survive `/clear` and cross-profile handoffs in thick stores (board, vault), not in chat history ([the memory model](../explanation/architecture/memory-model.md)).

**OpenHands-style sandbox-vs-host permission model.** Rejected: it routes permissions through a sandbox boundary, whereas Memoria needs permissions enforced per-profile at the write layer (the policy MCP), independent of where execution runs.

**Render the board with the Obsidian Kanban plugin.** Rejected: the authoritative board is Hermes's `kanban.db`, surfaced via the Dataview-backed [`board-state`](../explanation/dashboards/daily-glance/board-state.md) dashboard. The plugin reads only its own single-file Kanban-format markdown (`kanban-plugin: board` frontmatter), of which there is none. Bridging them — the `hermes-kanban` translation layer — works but couples two state machines for no gain; the Hermes Workspace board view and the `board-state` dashboard already cover visualization. (Obsidian Kanban remains fine for standalone personal boards unrelated to the Hermes board.)

## Related

- **Supporting rationale:** [Why Hermes](../explanation/rationale/why-hermes.md) (what Hermes provides, the boundary table, the API surface), [Why the architecture is layered](../explanation/rationale/why-three-layers.md) (thin-control-over-thick-state), [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md) (this as a deliberate "borrow").
- **Related decisions:** [ADR-01 three-layer architecture](01-three-layer-architecture.md) (the layers Hermes coordinates); [ADR-02 seven specialist profiles](02-seven-specialist-profiles.md) (the profiles *are* Hermes profiles, and there is no Orchestrator); [ADR-07 external coding agent boundary](07-delegate-coding-to-external-agents.md) (same thin-front rationale).
- **Source discussion:** retroactively records the runtime choice already embedded in `why-hermes.md`. The evolving detail of the boundary lives in that doc; the decision to build on Hermes rather than reimplement it is what this ADR fixes.


---

<!-- source: adr/23-scoped-memory-substrates.md -->

# ADR-23: Memory is seven scoped substrates, not one store

> **Revised 2026-06-02.** Originally six substrates. Substrate 5 ("vault project memory") was split into **project memory** and **program memory**, and the set was renamed for self-explanatory, scope-faithful names. Updated in place rather than superseded — this extends the same decision a day after it was recorded, it does not reverse it. (The count is authoritative at **seven**; the file was renamed from `six-memory-substrates` to `scoped-memory-substrates` so the name no longer states a stale count.)
>
> **Clarified 2026-06-16.** `research-focus.md` is program memory: standing,
> cross-project steering. A Project gate question, thesis, map, and gaps are
> project memory: bounded to one inquiry and archived with it.

> **Verified on-box 2026-06-21 (rationale correction — the decision stands, its
> justification is re-founded).** The Context/Why below say the substrate
> *boundaries* "keep one lane's in-flight reasoning from leaking into another's."
> The split does not *enforce* that — it **describes** it. Enforcement lives in three
> mechanisms, none of them the taxonomy: (1) cross-profile isolation = per-profile
> directories (own session store + `MEMORY.md`) **plus** every profile denying
> `session_search`/`moa`/`delegation` (`src/.memoria/profiles/memoria-*/config.yaml`)
> **plus** the kanban card as the only shared channel; (2) durable-write access = the
> policy gate's **per-lane path globs** (`src/.memoria/mcp/policy_hook.py:13`); (3) the
> card as the structured cross-profile unit. Two consequences: the "keep durable out of
> capped stores" clause is **placement correctness, not access control** (better served
> by a write-time lint than a category); and substrate **#3 (Session history) is
> currently disabled in all five profiles** (`session_search` denied), so the table
> lists a dead entry — re-enable deliberately or drop it from the live set. Test that
> proves isolation: "profile B cannot read profile A's session" (separate dirs +
> denylist), runnable independent of this taxonomy. Keep the seven as a **reference /
> routing table** for "where does X live?"; do not cite it as the access-control
> mechanism. Per AGENTS.md "Enforcement is a mechanism, not a label."

## Context

"Memory" in Memoria is not one thing, and treating it as one is the source of most "the agent forgot" and "the agent remembered something it shouldn't" failures. Every profile's read/write boundary depends on which substrate holds a given fact, yet the split was only described in [the memory model](../explanation/architecture/memory-model.md) and never recorded as a decision. Because the substrate boundaries are what keep one lane's in-flight reasoning from leaking into another's — and what keep durable knowledge out of size-capped, session-frozen stores — the split deserves a fixed anchor rather than living only in mutable prose.

## Decision

Memoria's memory is **seven distinct substrates**, each with its own scope, lifespan, backing store, and owner — **three** provided by Hermes natively (Working memory, Agent memory, Session history), **four** added by Memoria:

1. **Working memory** (Hermes) — one session, cleared on `/clear`; active reasoning state.
2. **Agent memory** `MEMORY.md` + `USER.md` (Hermes) — one agent (profile), durable, injected as a *frozen snapshot* into the system prompt under hard token caps (~800 / ~500); stable facts only.
3. **Session history** (Hermes) — one agent across all past sessions; searchable recall that carries **no authority** and never gates promotion.
4. **Handoff memory** (Memoria — Kanban) — one card, travels across profiles; the structured unit of cross-profile communication.
5. **Project memory** (Memoria — vault files) — one sub-project across lanes; open questions, decisions, framing; archives with the project.
6. **Program memory** (Memoria — vault files) — the whole research program; the human's standing steering (`research-focus`, `screening-protocol`); persistent.
7. **Audit memory** (Memoria — vault files) — whole vault, append-only; audit trail, snapshots, metrics.

A **substrate** is one of these seven categories; its **backing** is the store behind it (Hermes / Kanban / vault files). The governing test: **memory is read back as recall; configuration is read as rules** — config (e.g. `project-hints.yaml`) is not an eighth substrate. `SOUL.md` is identity, not memory.

## Why

- Substrate boundaries exist to keep each profile's read/write/retention rules clean; lumping facts of different scope or lifespan into one store is what produces the "forgot / shouldn't-have-remembered" failures.
- Program steering (persistent, program-wide — `research-focus`) and project working state (bounded, per-project) differ on scope, lifespan, and cardinality, so they are separate substrates, not one "project memory."
- Each name states its scope/role, so "where does X live?" is answerable from the name alone.

## Consequences

- "Where does X live?" becomes answerable by lifespan and scope, which is what makes cross-profile handoffs reliable: the Writer inherits the Librarian's *handoff payload* (handoff memory), never its session context.
- Agent memory's token caps are load-bearing, not advisory — in-flight task state must use handoff memory; cross-project standing steering uses program memory; one project's working state uses project memory.
- The vault is ground truth: a session-history result that contradicts a vault note loses.
- Audit memory's append-only constraint is enforced — every write is hash-paired (`before_hash`/`after_hash`), and the Linter's `audit-unpaired-writes` detector flags a write whose pairing never completed ([ADR-25](25-session-logging-two-logs.md)); audit capture must start from day one because cost and human-loop trends cannot be reconstructed retroactively.
- Adding an eighth place to "remember" something must map onto one of these seven (or be reclassified as configuration); an eighth substrate is a schema change that would supersede this ADR.

## Alternatives considered

**One unified memory store.** Rejected: it collapses every cross-session question into "store it and hope," and forces profiles to share too much (one lane's reasoning leaks into another) or too little (re-deriving the project goal every session). The scoped split is thin-control-over-thick-state applied to memory.

**Keep program and project as one "vault project memory" substrate.** Rejected (2026-06-02): a program-wide, persistent steering file and per-project, bounded scratch are different memory on every axis but "human-owned vault file" — merging them mislabels the substrate and buries `research-focus` as one example among others.

**Store durable facts in agent memory.** Rejected as a general approach: agent memory is per-profile, size-capped, and frozen at session start, so it cannot hold cross-lane or in-flight state without truncation or staleness — those belong in program/project memory and handoff memory respectively.

## Related

- **Supporting rationale:** [the memory model](../explanation/architecture/memory-model.md) (the substrate table, per-scope reasoning, and the memory-vs-configuration test).
- **Related decisions:** [ADR-01 three-layer architecture](01-three-layer-architecture.md) and [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (substrates 1–3 are Hermes-native); [ADR-25 session logging](25-session-logging-two-logs.md) (the append-only audit substrate's enforcement).
- **Reference:** [Memory substrates](../reference/memory.md) (the substrate table as lookup).


---

<!-- source: adr/24-single-researcher-scope.md -->

# ADR-24: Single-researcher scope — multi-user semantics are out of scope

## Context

Memoria assumes one human who owns judgment: review decisions, synthesis choices, and scope priorities all belong to that single researcher. This assumption is stated in [What Memoria is](../explanation/overview/what-memoria-is.md) but was never recorded as a decision — and unrecorded scope *constraints* are the ones that erode silently, because each individual "could we also support two reviewers / a shared queue / per-user permissions?" looks harmless in isolation. Recording the boundary makes the cumulative cost of crossing it explicit: multi-user review is not a feature increment, it is a different system.

## Decision

Memoria is a knowledge-production system for a **single researcher**. The design assumes exactly one human reviewer who owns all judgment about what enters the canonical vault. **Multi-user review semantics — concurrent reviewers, per-user permissions, shared review queues, attribution/merge of competing judgments — are explicitly out of scope.** Features that assume a single owner of judgment (the blocking review gate of [ADR-03](03-structural-review-gate.md), agent-proposed/human-confirmed classification of [ADR-15](15-project-membership-from-topic-hint.md), the single declared authority for frontmatter) are correct as designed and are not to be generalized to teams. This is a scope boundary, not a capability claim.

## Consequences

- The review gate stays simple: one reviewer, one verdict, no reconciliation of competing human judgments. This is a feature, not a limitation, at the target scale.
- *Multi-machine* is not *multi-user*: one researcher operating Memoria across several machines is in scope (session files are named to avoid sync collisions — [ADR-25](25-session-logging-two-logs.md)); several humans sharing one vault is not. The distinction is owner-of-judgment count, not device count.
- Any proposal that introduces a second judgment-owner must be treated as superseding this ADR, not extending the current design — it would touch the gate, the audit model, classification confirmation, and permissions at once.
- Team-tool framing is off the table for v0.x, which keeps the novelty surface and the publication path ([ADR-20](20-publication-path.md)) honestly scoped to n=1 operator data.

## Alternatives considered

**Design for teams from the start.** Rejected: multi-user review semantics (concurrency, per-user permissions, merge of competing verdicts) are a different and substantially larger system, and building for them now would complicate the single-owner gate that is central to the design — paying a large cost for a use case the project does not target.

**Leave scope implicit.** Rejected: an unstated boundary gets crossed incrementally. Recording it gives reviewers a single place to point when a feature quietly assumes a second human.

## Related

- **Supporting rationale:** [What Memoria is](../explanation/overview/what-memoria-is.md) ("single researcher" and "not a team tool in its current form").
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (assumes one reviewer); [ADR-15 project auto-classification](15-project-membership-from-topic-hint.md) (one human confirms); [ADR-20 publication path](20-publication-path.md) (n=1 operator data accepted as a known weakness).
- **Proposals bounded by this ADR:** [Cross-vault knowledge sharing](60-cross-vault-knowledge-sharing.md) (cross-machine for one researcher is in scope; a shared multi-user memory server is not, absent a superseding decision).
- **Source discussion:** retroactively records the scope boundary already stated in `what-memoria-is.md`.


---

<!-- source: adr/25-session-logging-two-logs.md -->

# ADR-25: Two separate session logs — hash-paired audit vs. per-session digests

> **Status: accepted — fully implemented (2026-06-12).** Both halves now ship: the **audit log** (hash-paired per write, guarded by the Linter's `audit-unpaired-writes` and `vault-hash-drift` detectors) and the **per-session digests** under `system/logs/sessions/`, written by the Linter's `session_summary` engine on the daily cron ([#391](https://github.com/eranroseman/memoria-vault/issues/391), [#392](https://github.com/eranroseman/memoria-vault/issues/392)). Two amendments from the original draft: the audit log is **append-only forever — never rotated** (the "weekly rotation" of early drafts is rejected, [#393](https://github.com/eranroseman/memoria-vault/issues/393); growth is surfaced by the Linter's `audit-log-size` advisory at 50 MB), and the second log is a **deterministic digest, not an LLM narrative** — the Linter is zero-LLM, so "narrative" below reads as "per-session digest."

## Context

Memoria's review gate ([ADR-03](03-structural-review-gate.md)) is only trustworthy if the record of what happened is tamper-evident. Two different questions need answering from session activity — *"did this write happen and was it authorized?"* (forensic) and *"what did this session accomplish?"* (narrative) — and they have different readers, lifecycles, and integrity requirements. The mechanism that answers both was described in [Session logging](../explanation/architecture/session-logging.md) but never recorded as a decision. Because the audit log is the substrate dashboards and tamper-detection depend on, its design (who writes it, whether it is append-only, how its integrity is guaranteed) deserves a fixed record rather than living only in prose.

## Decision

Memoria keeps **two separate logs in `99-system/logs/`**, written by different components:

- **Policy MCP audit log** (`audit.jsonl`) — written by the **policy MCP**, **append-only forever** and **hash-paired per write**: every mutating entry records a `before_hash` / `after_hash` (SHA-256, computed by the MCP) and is matched by a `write_complete` record, so a write can be reversed and an edit made outside the trail is detectable. This is per-write pairing, not a cross-entry chain. It answers the forensic question and feeds the audit-log and fleet-health dashboards. The log is **never rotated**: at single-researcher write volume ([ADR-24](24-single-researcher-scope.md)) rotation would complicate every consumer that walks the full history — the pairing reads, the `vault-hash-drift` verifier, the session digests — for no benefit, and it would match neither the session files' accumulate-indefinitely posture. Unbounded growth is surfaced, not silent: the Linter's `audit-log-size` detector raises a LOW advisory once the log exceeds **50 MB**.
- **Per-session summaries** (`sessions/YYYY-MM-DD-HHMM.jsonl`) — a **Linter**-written *deterministic digest* of the audit trail (the Linter is zero-LLM, so this is a digest, not an LLM narrative): one file per session (`task_id`), named from the session's first timestamp (a deterministic `-2` suffix disambiguates a shared start minute), carrying a header record (task, profiles, start/end, counts by action and decision) and one record per touched path (actions, final decision, final `after_hash`). Files are never rotated and accumulate indefinitely, answering the what-happened question for the researcher. The writer (`operations/integrity/linter/session_summary.py`) runs on the daily lint cron, is idempotent (an already-digested `task_id` is never rewritten), and only digests sessions quiet for **24 h**, so an in-flight session is never summarized early.

The two are never combined. The `sessions/` directory is intentionally **not** pre-created in the starter vault (an empty tracked folder would add git noise); the installer creates it on first setup, and the Linter is the sole writer of session memory.

## Consequences

- The audit log stays terse, append-only, and queryable for tamper detection; mixing narrative into it would make it verbose and harder to verify, while mixing per-write events into summaries would make them harder to read.
- Tamper-evidence is structural but **detective, not preventive**: because every write is hash-paired and the log is append-only, modification is *detectable* — the Linter's `audit-unpaired-writes` detector flags a mutating allow with no paired `write_complete`, and its `vault-hash-drift` detector flags (CRITICAL) any path whose latest recorded `after_hash` no longer matches the on-disk file ([ADR-23](23-scoped-memory-substrates.md), audit memory) — a legitimate human edit in Obsidian surfaces there too, by design: the finding means the trail no longer pins that file's state, not that the edit was malicious. Enforcement is best-effort, not fail-closed: Hermes fails open on hook errors, so the pairing catches tampering after the fact rather than preventing it.
- Per-session file naming by `YYYY-MM-DD-HHMM` makes the narrative log multi-machine-safe: one researcher's machines each write their own session files and the vault accumulates them without collision (consistent with the single-researcher scope of [ADR-24](24-single-researcher-scope.md)).
- A missing `sessions/` directory would cause the digest writer to silently fail, so vault setup must create it — the installer's folder skeleton includes `system/logs/sessions/` (declared in `.memoria/schemas/folders.yaml` and guarded by the Linter's `skeleton-drift` detector), and the writer itself creates the directory on demand as a backstop.
- Capture must start from first run: the audit and session record cannot be reconstructed retroactively, which is also why the publication telemetry of [ADR-20](20-publication-path.md) depends on logging existing early.

## Alternatives considered

**Weekly rotation of `audit.jsonl`.** Rejected ([#393](https://github.com/eranroseman/memoria-vault/issues/393)): rotation would force every full-history consumer — the `write_complete` pairing reads, the `vault-hash-drift` walk, the session digests — to stitch across rotated files, for no benefit at single-researcher write volume. Append-only forever keeps one walk = the whole history; the `audit-log-size` advisory keeps growth visible.

**An LLM-written narrative summary.** Rejected: the Linter is a zero-LLM engine ([ADR-49](49-catalog-in-bases-linter-monitor.md)), and a digest derived deterministically from the audit trail is reproducible, auditable, and free — the narrative reading stays with the researcher.

**One combined log.** Rejected: the two readers want opposite shapes. A single log is either too verbose to verify (audit polluted with narrative) or too noisy to read (summaries polluted with per-write events). Separation lets each serve its reader.

**Pre-create the `sessions/` directory in the repo.** Rejected: a tracked empty folder accumulates churn in git history as session files land. Creating it at install time keeps the repo clean at the cost of one documented setup step.

## Related

- **Tracking issues (resolved):** [#391](https://github.com/eranroseman/memoria-vault/issues/391) (per-session digests), [#392](https://github.com/eranroseman/memoria-vault/issues/392) (`vault-hash-drift`), [#393](https://github.com/eranroseman/memoria-vault/issues/393) (append-only-forever).
- **Supporting rationale:** [Session logging](../explanation/architecture/session-logging.md) (the two-log table and the not-pre-created rationale).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the audit trail makes the gate's writes accountable); [ADR-23 memory substrates](23-scoped-memory-substrates.md) (audit memory is the append-only substrate); [ADR-24 single-researcher scope](24-single-researcher-scope.md) (multi-machine, single-user safety).
- **Profiles affected:** the [Linter](../explanation/operations/README.md) (reads `99-system/logs/`; runs the `audit-unpaired-writes`, `vault-hash-drift`, and `audit-log-size` integrity checks; writes the per-session digests).
- **Reference:** [Policy MCP](../reference/policy-mcp.md) (audit log format and enforcement).
- **Source discussion:** retroactively records the two-log separation already embedded in `session-logging.md`.


---

<!-- source: adr/26-repo-as-install-unit.md -->

# ADR-26: The repo is the install unit; profiles are hand-authored and idempotently deployed

> **Amended (2026-06-10; 2026-06-23).** Three specifics below are now stale:
> (1) the repo ships **`src/`**, not `vault/`, as the source-of-truth tree the installer
> scaffolds and populates — see [ADR-55](55-src-scaffold-populate-golden-copy.md);
> read "`vault/`" throughout as "`src/`". (2) The profile compiler this ADR calls
> "deferred ([ADR-42](42-profile-compilation.md))" is superseded by the Co-PI/agent
> consolidation in [ADR-48](48-copi-and-agent-consolidation.md); the seven-profile
> premise no longer holds. (3) Profile configs are no longer entirely hand-authored:
> [ADR-115](115-profile-config-materialization.md) materializes only the mechanical
> capability blocks from `tool-registry.yaml`. The core decision (the repo is the
> install unit; idempotent profile deploy) stands.

## Context

> *Note (v0.1.0-alpha.2): "seven" profile directories below predates [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the fleet to **five** (`.memoria/profiles/memoria-{copi,librarian,writer,peer-reviewer,engineer}`). The decision is unchanged — profiles remain hand-authored and idempotently deployed; the deferred-compiler trade-off now reads "five-profile scale".*

How Memoria is packaged, installed, and kept up to date has direct upgrade-path consequences — yet the model was only described in [Distribution model](../explanation/deployment/distribution-model.md) and never recorded as a decision. Two coupled questions need a fixed answer: what is the unit a user installs (the whole repo, or just the vault?), and how do the seven Hermes profile directories stay synchronized with their vault source over time without a build step? Recording this matters because the deferral of a profile compiler and the "repo is the install unit" choice both shape every future install and upgrade.

## Decision

**The repo (`memoria-vault`) is the install unit.** A user clones it (or runs the one-line bootstrap that clones it), and the bootstrap installers at the repo root deploy everything: `scripts/install.ps1` for native Windows production and `scripts/install.sh` for Linux/WSL testing. The repo has three parts with distinct audiences: `scripts/install.sh`/`scripts/install.ps1` (bootstrap), `src/` (the runtime artifact source deployed to a working vault), and `docs/` (developer-facing, not deployed). Consequences that follow as rules:

- **`vault/` is not independently installable** — installing requires the whole repo, and any reference from a vault-resident file to `docs/` is a **GitHub URL, never a relative path**, because the deployed vault does not carry them.
- **Profiles are hand-authored**, not compiled. The seven profile directories under `.memoria/profiles/` are maintained by hand; a profile compiler is **deferred** ([Profile compilation from a shared base](42-profile-compilation.md)) because seven-profile scale does not yet justify the complexity.
- **Profile install is idempotent.** The profile-install step (re-runnable on its own via `--profiles-only`) refreshes every author-owned file on each `git pull` and leaves human-owned secrets (`.env`, local overrides) untouched.

## Consequences

- Upgrades are "`git pull` then re-run the idempotent profile install" — that re-run is the mechanism that keeps deployed profiles synchronized with the vault source.
- A `profile-install-drift` detector was once planned to *catch* deployed copies diverging from source; it is **retired** ([ADR-67](67-drift-procedures-keep-or-retire.md)) — the vault-side Linter cannot see `~/.hermes`, and the idempotent re-run is both the detection and the fix.
- Hand-authoring accepts a known cost: common content (audit behavior, policy invariants, MCP connections) is duplicated across seven `SOUL.md` files kept in lockstep by human review. When that lockstep becomes painful, the deferred compiler proposal is the planned response — and adopting it would supersede the hand-authored clause here.
- The deployed-vault-carries-no-`docs/` rule is load-bearing: a relative cross-reference from a vault file silently breaks after deployment, so vault→docs links must be GitHub URLs.
- Windows installs must deploy off OneDrive, which the bootstrap handles by copying `src/` to a working production vault location.

## Alternatives considered

**Ship `vault/` as the independently installable unit (the earlier vault-centric framing).** Superseded by the bootstrap model: the installers live at the repo root because the clone is the entry point, which makes the repo — not the vault alone — the install unit. The vault-as-carrier framing is retained only as history.

**Generate profiles from a shared base via a compiler.** Deferred, not rejected: it would eliminate the seven-way duplication, but at seven-profile scale the duplication is not yet painful enough to justify a build step. Held as [Profile compilation from a shared base](42-profile-compilation.md) with hand-authoring as the current state.

## Related

- **Supporting rationale:** [Distribution model](../explanation/deployment/distribution-model.md) (the three-part repo, idempotent install, hand-authored profiles).
- **Related decisions:** [ADR-02 seven specialist profiles](02-seven-specialist-profiles.md) (the profiles being deployed); [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (profiles deploy to `~/.hermes/profiles/`).
- **Installer design:** [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) (rationale) + [Installer (bootstrap)](../reference/installer.md) (inventories).
- **Proposals:** [Profile compilation from a shared base](42-profile-compilation.md) (the deferred compiler).
- **How-to:** [Redeploy profiles](../how-to-guides/operate/redeploy-profiles.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
- **Source discussion:** retroactively records the distribution model in `distribution-model.md`; note this ADR follows the *current* repo-as-install-unit model, which has moved past the earlier vault-as-carrier framing.


---

<!-- source: adr/27-hermes-native-config-and-gate-enforcement.md -->

# ADR-27: Configure Hermes the way Hermes reads config; the review gate enforces via a toolset allowlist with obsidian as the only write path

> **Partial supersession (2026-06-02, [ADR-28](28-write-gate-as-plugin.md)).** ADR-28
> supersedes **only this ADR's *enforcement mechanism*** (shell hook → Python plugin);
> the `superseded_by: [28]` frontmatter scopes to that mechanism, **not** to the ADR
> as a whole. ADR-27's config-model decisions — `mcp_servers` in `config.yaml`,
> a profile-scoped toolset allowlist, obsidian as the only write path — **all stand**.
> Concretely, this ADR's
> *enforcement mechanism* — the `pre_tool_call` **shell hook** with
> `matcher: "obsidian.*"` — does **not** fire on live agent writes: Hermes registers
> the obsidian tool as `mcp_obsidian_obsidian_append_content`, and the shell-hook
> `re.fullmatch` against `obsidian.*` never matches it (shell hooks are also
> consent-gated and fail-open). ADR-27's validation rows were synthetic
> (hand-set `task_id`s), not a live run. **ADR-28 replaces the shell hook with a
> Python plugin** (the gate now enforces live). The rest of ADR-27 — `mcp_servers`
> in `config.yaml`, the profile-scoped toolset allowlist, obsidian as the only
> write path — **stands**; it is what makes one gated path sufficient.
>
> **Hermes 0.17 correction (2026-06-22).** The current allowlist is expressed with
> positive `platform_toolsets` for every Memoria runtime platform. The old
> computed `agent.disabled_toolsets = all − allowlist` model remains only as a
> backstop for known direct-world toolsets if a Hermes path falls back to defaults.

## Context

A Tier-4 live investigation (Hermes Agent v0.14.0, WSL2, against the `Memoria-test`
vault with Obsidian open on Windows) set out to verify that the structural review
gate ([ADR-03](03-structural-review-gate.md)) actually blocks an agent's writes to
review-gated zones. It did not — and chasing *why* uncovered that several Memoria
profile artifacts were placed where Hermes does not read them. The gate, the
capability layer ([#51](https://github.com/eranroseman/memoria-vault/issues/51)),
and the obsidian bridge ([#39](https://github.com/eranroseman/memoria-vault/issues/39))
all depend on Hermes loading config from specific files; Memoria had guessed the
locations.

The investigation produced a sequence of wrong intermediate conclusions ("hooks
don't fire in oneshot", "…not in the gateway either", "build a custom obsidian
bridge"). Each was an artifact of the misplacement, not a real Hermes limitation.
This ADR records the corrected model and the resulting plan so the dead ends are
not re-walked. It refines — does not supersede — ADR-03 (the gate is still
structural) and [ADR-22](22-build-on-hermes-runtime.md) (we still build on the
Hermes runtime); it sharpens *how* we configure that runtime.

This decision rests on the authoritative Hermes sources read during the
investigation: `cli-config.yaml.example`, and the `user-guide/{configuration,
profiles,multi-profile-gateways,checkpoints-and-rollback,docker}` +
`developer-guide/{tools-runtime,cron-internals,acp-internals}` docs shipped in the
local install (`~/.hermes/hermes-agent/website/docs/`), plus reads of
`agent/shell_hooks.py`, `tools/mcp_tool.py`, `hermes_cli/config.py`,
`hermes_cli/main.py`, and `agent/tool_executor.py`.

## Findings (the evidence this decision is built on)

1. **Hermes loads MCP servers only from `mcp_servers` in `config.yaml`.**
   `tools/mcp_tool.py::_load_mcp_config()` reads `mcp_servers` via `load_config()`.
   Nothing reads a per-profile `mcp.json` at runtime — `hermes profile install`
   treats `mcp.json` as a distribution-owned file to *copy*, never to load.
   Memoria shipped its `policy` + `obsidian` servers in `mcp.json`, so **neither
   ever loaded** (`hermes -p memoria-writer mcp list` → "No MCP servers
   configured"). This is the single root cause of the gate failure.

2. **With no obsidian tool, the agent writes via the filesystem.** Profiles do
   **not** sandbox (`user-guide/profiles.md`: "Profiles do not sandbox the
   agent… the agent still has the same filesystem access as your user account").
   Lacking the obsidian MCP tool, the agent wrote a note via `code_execution` /
   `file` to an arbitrary host path (`…/OneDrive/Documents/Memoria/…`), entirely
   outside any gate.

3. **`config.yaml` is the home for per-profile settings, and `load_config()` is
   profile-scoped.** Each profile is its own `HERMES_HOME`
   (`~/.hermes/profiles/<name>/`); `load_config()` reads
   `get_hermes_home()/config.yaml`. So `model`, `mcp_servers`, `hooks`,
   `platform_toolsets`, `agent.disabled_toolsets`, `terminal`, and plugins all
   belong in **one** per-profile `config.yaml`. A separate `mcp.json` is dead.

4. **The shell-hook gate *does* fire in every run mode — the matcher was the
   problem, not the mode.** All run modes (CLI/`-z`, gateway, cron, ACP) wrap the
   same `run_agent.AIAgent`; every tool call routes through
   `model_tools.handle_function_call → invoke_hook("pre_tool_call")`
   (`developer-guide/tools-runtime.md`), including MCP tools. Hooks register at
   CLI and gateway startup (`register_from_config`), and cron runs inside the
   gateway ticker (`cron-internals.md`), ACP wraps `AIAgent` with
   `enabled_toolsets=["hermes-acp"]` (`acp-internals.md`). The gate didn't fire
   only because (a) `matches_tool` uses `re.fullmatch` (`agent/shell_hooks.py`),
   so `matcher: "obsidian"` matched *nothing* — fixed to `"obsidian.*"` — and
   (b) the agent never called an obsidian tool (finding 1), so even the correct
   matcher had nothing to match. **The earlier "hooks don't fire / need a custom
   bridge" conclusions are withdrawn.**

5. **The capability denylist `[terminal, file]` is insufficient.** The lane's
   `tool-registry.yaml` intends a default-deny *allowlist*
   (writer = `[web, vault_read, vault_write, skills, todo, policy]`), but the
   profile inherited the global `platform_toolsets.cli` (≈17 toolsets). Disabling
   only `terminal`+`file` left `code_execution`, `delegation`, `cronjob`,
   `messaging`, `browser`, `computer_use` live — several of which write to disk or
   act outside the gate. `code_execution` alone re-opens the hole.

6. **Hermes reads per-profile `.env` only — there is no global `~/.hermes/.env`
   inheritance for a profile run.** Shared keys placed only in the global `.env`
   never reach a profile run (model init fails; `${OBSIDIAN_API_KEY}` resolves
   empty → the original 401). The installer must seed shared keys into each
   profile `.env`.

7. **`hermes config set` stores a scalar string, not a list** — it cannot emit a
   YAML list, so `disabled_toolsets` must be written by editing the file
   (PyYAML), preserving the `model`/`hooks` blocks.

8. **Hermes ships native mechanisms Memoria was reinventing or mis-naming:**
   the terminal `DANGEROUS_PATTERNS` + `command_allowlist` is a real
   command-approval layer; and **"Tirith" is a command-string security scanner
   (`security.tirith_*`), *not* the tool-permission/capability layer** —
   `policy-mcp.md` misnamed it. The capability layer is `platform_toolsets` /
   `agent.disabled_toolsets`. Hermes `checkpoints` are real for native
   `write_file`/`patch`/terminal writes, but Memoria's normal vault writes go
   through the Obsidian MCP path, so profile `checkpoints.enabled` is inert for
   Memoria and no longer ships.

## Decision

**Configure Hermes through the files and keys Hermes actually reads, and enforce
the review gate by making the obsidian MCP server the *only* write path each
non-terminal lane has.** Concretely:

1. **MCP servers live in each profile's `config.yaml` under `mcp_servers`.** The
   installer merges the (now-vestigial) `mcp.json` content into `config.yaml` at
   deploy time and stops relying on `mcp.json`. `policy` + `obsidian` therefore
   load, and obsidian becomes the agent's vault-write tool.

2. **Each lane is locked to a positive toolset allowlist.** The source
   `config.yaml` for every profile lists the permitted toolsets in
   `platform_toolsets` for each runtime platform (`cli`, gateway platforms,
   `cron`, and `api_server`), derived from `tool-registry.yaml`. The
   `agent.disabled_toolsets` list is retained as a backstop for known
   direct-world families only. For the five current lanes this removes
   `code_execution`, `file`, `terminal`, `delegation`, `browser`, etc. **With no
   filesystem write tool, the agent's only way to write the vault is the
   obsidian MCP path — which the policy plugin gates.**

3. **Keep the shell-hook gate as the enforcement mechanism (ADR-03 stands).** It
   fires in CLI, gateway, cron, and ACP via the shared `AIAgent` dispatch. The
   matcher is `obsidian.*` (fullmatch). The custom-bridge alternative is
   **rejected** — it was only ever needed under the withdrawn "hooks don't fire"
   premise. *(Enforcement mechanism superseded by [ADR-28](28-write-gate-as-plugin.md):
   the shell hook never fired on live writes — it is replaced by the
   `memoria-policy-gate` Python plugin. The config-model decisions 1, 2, 4–6 below
   are unaffected.)*

4. **Coder and Linter keep `terminal`+`file` (they need git / `detectors.py`).**
   Their file writes are gated by the hook (`write_file|patch` matcher) and
   scoped by lane `write_scope`; their shell writes are bounded by `write_scope`
   plus, optionally, a Docker terminal backend (see Consequences).
   *(v0.1.0-alpha.2 update — this exception is retired by D40/[ADR-46](46-seven-layer-architecture.md):
   the Linter became a cron/CI engine (no agent), and the Engineer — the Coder's
   successor — is MCP-only like every lane. No Memoria profile ships `terminal`,
   `file`, or `code_execution`; the policy-gate plugin additionally hard-denies
   those tool families fail-closed for every lane. The external coding agent the
   Engineer hands off to is third-party code and gets execution isolation when
   introduced, per D40.)*

5. **Shared keys are seeded into each profile `.env`** by the installer
   (`seed_profile_env`, idempotent; re-run `--profiles-only` after adding keys).
   Already landed in PR #57.

6. **Adopt only the Hermes-native safety features that affect Memoria's path:**
   `terminal.cwd` stays set to the vault to anchor stray ops, and the "Tirith =
   capability layer" docs error is corrected. Do **not** ship
   `checkpoints.enabled` unless Memoria gains a native file/terminal write path or
   a test proves checkpoints fire for the actual Obsidian MCP write path.

## Consequences

- **`mcp.json` is retired** as a runtime artifact (kept, if at all, only as the
  source the installer merges from). The ledger row, `profiles.md`, and the
  bootstrap docs update accordingly.
- **`tool-registry.yaml` becomes load-bearing**: it is the source for each lane's
  positive `platform_toolsets` and MCP tool filters, not just a drift-check reference.
- **The gate enforces in all run modes** once (1)+(2) land — no per-mode special
  casing, no custom bridge.
- **Reversibility comes from Memoria's own audit/golden mechanisms, not Hermes
  checkpoints.** Policy writes record before/after hashes; shipped system files are
  restorable from the golden copy. Hermes checkpoints are not claimed for MCP
  writes.
- **Optional defense-in-depth for Coder/Linter**: `terminal.backend: docker`
  sandboxes their `terminal`+`code_execution` in a container, with a vault
  bind-mount scoped to just their write zone (`40-workbench/*/06-code/` for Coder,
  `99-system/logs/` for Linter). Full-Hermes-in-Docker is **not** adopted: in the
  WSL2 + Windows-Obsidian topology it adds container→host REST-bridge networking
  fragility for no gate benefit (the gated path lives on the Windows host).
- **Records to correct** (the investigation invalidated earlier claims):
  - `#39` "resolved via the obsidian bridge" — the observed write was a filesystem
    write, not obsidian; reopen until obsidian MCP actually loads and a gated write
    is confirmed.
  - `#58` "gate is a no-op in oneshot/gateway" — wrong premise; the gate fires, the
    obsidian tool was simply never loaded. Correct and likely close.
  - `policy-mcp.md` Caveat 2 + the ledger "custom bridge" recommendation — replace
    with the `mcp_servers`-placement + allowlist model above.
  - `#51` capability layer — the `[terminal, file]` denylist is superseded by the
    `all − allowlist` computation.

## Implementation plan

Installer (`scripts/install.sh`) and profile sources (`vault/.memoria/profiles/*`):

1. Emit `mcp_servers` into each deployed `config.yaml` (merge from the profile's
   `mcp.json`; substitute `{{VAULT_PATH}}` and the venv interpreter; keep
   `${OBSIDIAN_API_KEY}` for env interpolation).
2. Emit positive `platform_toolsets` per lane from `tool-registry.yaml`, with
   `agent.disabled_toolsets` retained only as the known direct-world backstop.
3. Set `terminal.cwd: {{VAULT_PATH}}` per profile; do not emit `checkpoints` for
   MCP-only lanes.
4. Keep `seed_profile_env` (#57) and the `obsidian.*` matcher (#57).
5. Re-run Tier-4 on `Memoria-test`: confirm `hermes -p <lane> mcp list` shows
   `obsidian`+`policy`; a write to an allowed zone produces an audit row; a write
   to a review-gated zone is **blocked** with no file on disk; the five
   non-terminal lanes have no `code_execution`/`file`/`terminal`.
6. Then correct `#39`/`#58`, `policy-mcp.md`, and the ledger.

Sequencing lives in [Release plan — v0.1.0-alpha.1](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1.md); this ADR records the
choices, not the schedule.

## Alternatives considered

- **Custom obsidian bridge (MCP wrapper that calls `check_permission` internally).**
  Rejected: only attractive under the withdrawn "hooks never fire" premise. The
  native hook fires in all modes once obsidian is the write path; a bridge is more
  to build and maintain and still wouldn't cover `code_execution`/`terminal`.
- **Run automation through the gateway to "make hooks fire".** Moot — hooks fire
  in `-z`/cron/ACP too; the gateway is not required for enforcement (though it
  remains how Hermes-native cron executes).
- **Denylist-only capability (`disabled_toolsets: [terminal, file]`).** Rejected:
  leaves `code_execution` and other write/act paths live. The allowlist
  (`all − allowed`) is the correct default-deny realization of `tool-registry.yaml`.
- **`platform_toolsets` per platform instead of global `disabled_toolsets`.**
  Accepted in Hermes 0.17. It is slightly more verbose, but it fails closed for
  new toolsets on configured platforms; `disabled_toolsets` remains a backstop.
- **Full Hermes-in-Docker for sandboxing.** Rejected as the primary fix: it
  contains blast radius but doesn't load obsidian or remove `code_execution`, and
  the vault bind-mount it requires re-opens ungated writes to the vault. Retained
  only as optional `terminal.backend: docker` scoped to Coder/Linter.
- **SOUL.md / prompt rules as the boundary.** Rejected per ADR-03 and confirmed by
  `profiles.md`: prompts do not enforce a filesystem boundary.


---

<!-- source: adr/28-write-gate-as-plugin.md -->

# ADR-28: The vault write gate is a Hermes Python plugin, not a shell hook

> **Partial (mechanism-only) supersession.** The `supersedes: [27]` frontmatter is
> scoped: this ADR supersedes **only [ADR-27](27-hermes-native-config-and-gate-enforcement.md)'s
> shell-hook enforcement mechanism**, replacing it with the `memoria-policy-gate`
> Python plugin. **ADR-27's config-model decisions are retained** — `mcp_servers` in
> `config.yaml`, the profile-scoped toolset allowlist, and obsidian as each lane's
> only write path all still stand (they are what make a single gated path
> sufficient). ADR-27 is **not** fully superseded.

> **Verified on-box 2026-06-21 (mechanism correction).** The sentence above
> over-credits the capability layer: on the installed Hermes (v0.14.0),
> `agent.disabled_toolsets` is a **schema subtraction only** — it strips a tool from
> what the model *sees* (`model_tools.py:370`) — and `registry.dispatch(name, args)`
> runs **any** registered tool by name with **no enablement check** at dispatch
> (`tools/registry.py:390`). So a disabled tool is hidden from the model, not removed
> from the runtime; against the injection threat ([ADR-32](32-external-access-over-mcp.md),
> the dominant one) the denylist is not a capability boundary. What actually makes the
> single gated path sufficient is the **plugin's own behaviour**, which the code
> already gets right: `policy_hook` **independently hard-denies** `file`/`terminal`/
> `code_execution` and **defaults to block** for any unknown tool
> (`src/.memoria/mcp/policy_hook.py:82-96, 204, 264`), explicitly "rather than trusting
> the capability layer." Read the Decision below with that correction: `disabled_toolsets`
> is UX (keeps the model from seeing the tool); the plugin's hard-deny + default-deny is
> the enforcement. Per AGENTS.md "Enforcement is a mechanism, not a label."
>
> **Hermes 0.17 correction (2026-06-22).** The primary UX/capability shaping layer
> is now positive `platform_toolsets` per runtime platform, with
> `agent.disabled_toolsets` retained only as a known direct-world backstop. The
> enforcement statement above is unchanged: the plugin hard-deny is the boundary.

## Context

[ADR-27](27-hermes-native-config-and-gate-enforcement.md) concluded that the
structural review gate ([ADR-03](03-structural-review-gate.md)) enforces via a
`pre_tool_call` **shell hook** (`matcher: "obsidian.*"`, running `policy_hook.py`)
once `mcp_servers` live in `config.yaml` and a toolset allowlist makes obsidian the
only write path. Its validation rows, however, carried hand-set `task_id`s
(`adr27-write-01`) — they came from synthetic hook-test payloads, not a live agent
run.

A real live re-run (Hermes v0.14.0, `hermes -z`, against `Memoria-test`) found the
gate **never fires**: a write to a review-gated zone succeeded, ungated and
unaudited. Three independent investigations plus a first-hand `hermes hooks test`
converged on the cause:

1. **Tool-name / matcher mismatch.** Hermes registers MCP tools as
   `mcp_<server>_<tool>` (`tools/mcp_tool.py`), so the obsidian write is
   `mcp_obsidian_obsidian_append_content` (the `mcp_` prefix + mcp-obsidian's own
   `obsidian_` names, doubled). The shell-hook matcher uses `re.fullmatch`
   (`agent/shell_hooks.py`), and `re.fullmatch("obsidian.*", "mcp_obsidian_…")` is
   `None`. The hook process is never spawned — no block, no audit. (The earlier
   "in-process test passed" used the fabricated name `obsidian_append_content`,
   which *does* fullmatch — hence the false positive.)
2. **Shell hooks are consent-gated.** On non-TTY runs (cron, headless `-z`) they
   register only with `--accept-hooks` / `HERMES_ACCEPT_HOOKS=1` /
   `hooks_auto_accept: true`; otherwise *"not allowlisted — skipped."*
3. **Shell hooks are fail-OPEN by construction.** The hook dispatcher swallows
   callback exceptions; shell hooks return "no block" on error/timeout/bad-JSON
   (`agent/shell_hooks.py`, `hermes_cli/plugins.py`). A gate that proceeds on its
   own failure is not a gate.

Earlier conclusions ("hooks don't fire in oneshot"; "…not in the gateway either")
were partly right about the symptom and wrong about the cause: the firing site
*is* reached in every mode; the matcher silently rejected the tool.

## Decision

**Implement the write gate as a Hermes Python plugin (`memoria-policy-gate`),** not
a shell hook. The plugin registers two lifecycle hooks on the plugin manager:

- `pre_tool_call` → classify the tool, evaluate the lane policy, and return
  `{"action": "block", "message": …}` for `deny`/`dry_run`. **Fail-closed:** any
  error inside the gate returns a block.
- `post_tool_call` → complete the audit record (paired `after_hash`).

It **reuses the tested decision core verbatim** — `policy_hook.evaluate_pre` /
`evaluate_post` and `memoria.runtime.policy.PolicyEngine` — so no policy logic is
duplicated.
The `hooks:` block is removed from every profile `config.yaml`; the plugin is
turned on per lane via `plugins.enabled` and deployed (with `{{PROFILE}}` /
`{{VAULT_PATH}}` substituted) by the installer's `deploy_policy_plugin`.

The capability layer from ADR-27 (`platform_toolsets`, obsidian = the only write
path for the five current lanes, with `agent.disabled_toolsets` as a backstop)
**stands** — it is what makes a single gated path sufficient. ADR-28 replaces only
ADR-27's *enforcement mechanism* (shell hook → plugin); the config-model decisions
in ADR-27 are unchanged.

## Why a plugin (over the alternatives)

| Approach | All modes | task_id | Fail-closed | Notes |
| --- | --- | --- | --- | --- |
| **Python plugin `pre_tool_call`** (chosen) | yes (in-process, no consent) | **yes — passed to the callback** | yes (block on any internal error) | matches in Python, so the real `mcp_obsidian_*` name is caught |
| Fix the shell-hook matcher (`mcp_obsidian.*`) | yes | yes | **no** — fail-open by design | one-line stopgap only |
| Wrapper `obsidian` MCP server | yes | **no — MCP tools get only model args** | yes | new process + replicate REST calls; task_id is the hard part |

The plugin is the only option that is both fail-closed *and* solves `task_id`
provenance for free. Its one residual weakness — if the plugin fails to load there
is no gate — is bounded by `plugins.enabled` (installer-managed) and backstopped by
the capability layer (no other write path exists).

## Consequences

- The gate now enforces live in `-z`/gateway/cron/ACP (all share the same agent
  loop and plugin dispatch). This resolves
  [#58](https://github.com/eranroseman/memoria-vault/issues/58) for real, not by
  artifact.
- `policy_hook.py` stays as the shared decision/audit core (its `--self-test`
  remains valid); only its use as a *shell-hook entrypoint* is retired.
- Defense in depth: the plugin gates both the obsidian MCP writes (all lanes) and
  the `file` toolset writes (`write_file`/`patch`) on Coder/Linter, via the same
  `classify`, so it replaces both former shell-hook matchers.
- New residual risk: "plugin not loaded → ungated." Mitigated by `plugins.enabled`
  per lane and the capability allowlist; a startup assertion is a possible
  follow-up.

## Validation

Live on `Memoria-test` (Hermes v0.14.0, `hermes -z`), against lanes deployed
through the productionized installer (`memoria-librarian` and `memoria-writer`):

- **Allowed-zone write** (`10-inbox/…`) → succeeds; audit logs `allow` +
  `write_complete` with the real session-UUID `task_id`.
- **Review-gated/denied write** (`30-synthesis/…`) → **blocked** (`policy deny`);
  no file on disk; audit reason shows the real `mcp_obsidian_obsidian_append_content`
  name (proving the plugin matched what the shell hook missed).
- **Simulated policy outage** (`policy_mcp.py` moved aside) → an otherwise-allowed
  write is **blocked** (fail-closed), where the shell hook would have failed open.

The gate was then re-validated in the other non-interactive run modes (same agent
loop; the gateway calls `discover_plugins()` at startup, `gateway/run.py`):

- **Gateway** (driven headless via the built-in `api_server` platform,
  `POST /v1/chat/completions`) → denied write blocked (audit `deny`); allowed write
  succeeds (audit `allow` + `write_complete`).
- **Cron** (`hermes -p <lane> cron run … && cron tick`) → denied write blocked
  (audit `deny`), no file on disk.

## Alternatives considered

- **Keep the shell hook, fix the matcher to `mcp_obsidian.*`.** Makes it fire, but
  it stays consent-gated and fail-open — unacceptable for the primary gate. Viable
  only as a transition stopgap; not adopted.
- **Custom wrapper `obsidian` MCP server.** Fail-closed and mode-independent, but an
  MCP tool receives only model-supplied args, so `task_id` provenance is unsolved
  (the model would have to be trusted to pass it). More moving parts than a plugin
  for no enforcement gain. Held as a fallback if the "plugin must load" assumption
  ever proves insufficient.


---

<!-- source: adr/29-testing-framework.md -->

# ADR-29: A layered testing framework

> **Amended by [ADR-44](44-tests-in-pytest-tree.md):** L1 component tests now live in a
> repo-side `pytest` tree (`tests/`), not inline `--self-test` blocks. The pyramid,
> coverage matrix, and disciplines below are unchanged; only L1's hosting moved.
>
> **Amended 2026-06-23:** the release process is now described as five promotion
> gates. The historical L0-L5 labels remain coverage aliases; humans and scripts
> use Source, Package, Runtime, Product, and Release gates.

## Context

Memoria has three good test plans — [headless](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/headless-test-plan.md) (static + schema), [hermes-cli](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/hermes-cli-test-plan.md) (agent wiring + the policy gate), and [GUI](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/gui-test-plan.md) (Obsidian/Zotero/dashboards) — but no framework binding them. Three problems follow: coverage is **implicit** (nobody can answer "is component X tested?"), gaps are **invisible** until hit, and the plans **drift** from the design (e.g. the CLI plan still cited the dissolved `00-meta/04-reference/`, the GUI plan still listed a deleted root `README`). An assessment also surfaced uncovered surface: the installer end-to-end, recovery/failure-modes, security/adversarial, performance/scale, deployment modes, a cross-layer golden path, and — by design — agent *output quality*.

## Decision

Adopt a **promotion-gated test framework**: cheap checks run first and often,
expensive checks run only when their evidence matters, and every release promotes
from source to package to runtime to product acceptance to cut readiness. The
coverage matrix still owns the component-to-plan index; the gate vocabulary is
the process people and scripts use.

**Promotion gates**

| Gate | Proves | Primary command / evidence | Trigger |
| --- | --- | --- | --- |
| **Source** | the repo is internally coherent: format, lint, schema, docs, generated-file drift, secrets/provenance, and changed-code tests | `scripts/verify pr` | every PR |
| **Package** | the repo can assemble a valid disposable Memoria vault and replay the model-free lifecycle | `scripts/verify package` | vault/package-related PRs, nightly, release candidate |
| **Runtime** | Hermes, MCP, policy gates, and local service boundaries work with a disposable runtime | `scripts/verify runtime` | nightly, runtime-related PRs when available, release candidate |
| **Product** | Memoria's user workflows produce the expected artifacts and human-visible surfaces render | release-candidate runbook evidence | release candidate |
| **Release** | the candidate is ready to cut: fresh-clone evidence, docs, blockers, versioning, close-out, and notes are ready | release issue + release-please evidence | formal release / checkpoint close |

**Coverage aliases**

| Layer | Covers | Plan / owner | Trigger |
| --- | --- | --- | --- |
| **L0 Static & schema** | the 5 CI checks + dashboard/telemetry schema-drift | headless | every commit (CI) |
| **L1 Component** | `pytest tests/` (gate, hook, board, metrics, ingest/verify MCP, detectors, ingest spine, repo tooling) — ADR-44 | headless §A | every commit (CI) |
| **L2 Wiring / contract** | policy gate + every agent command + board/profile/skills/cron + architecture invariants | hermes-cli | per release (cheap model, disposable vault) |
| **L3 System integration** | plugins, REST bridge, dashboards render, Zotero→bib, ACP | GUI | per release (Windows) |
| **L4 Golden-path E2E** | one full-lifecycle trace across all layers | [e2e-golden-path](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/e2e-golden-path-plan.md) | per release |
| **L5 Quality / eval** | agent *output* quality (gold tasks, scored) | [ADR-11](11-vault-eval-maintenance.md) vault-eval | per release / model swap |
| **Cross-cutting** | Installer clean-install · Recovery · Security · Performance · Deployment | [installer](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/installer-test-plan.md) (+ others as built) | on relevant change |

**Disciplines**

1. **Coverage matrix is the keystone.** [`coverage-matrix.md`](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/coverage-matrix.md) maps every design component → its layer/plan → automated? → release gate. Gaps are tracked, not discovered by accident.
2. **Determinism.** Below L5, assert *artifact shape and gate decision*, never prose quality. Output quality is L5's job alone.
3. **Drift control.** A check (`scripts/check_test_refs.py`) verifies every path/link a plan references resolves, so plans can't rot silently; runs in CI alongside docs-doctor.
4. **Explicit gate mapping.** Each gate names the layer/plan that satisfies it
   and writes evidence for the run, so "is the release tested?" is answerable
   from the matrix plus the release issue.

All plans live in [Testing](https://github.com/eranroseman/memoria-vault/tree/main/docs/testing), built from `test-plan-template.md`.

## Why

- The substrate of testing is *which behaviour is asserted where* — the same reason the memory model is scoped substrates ([ADR-23](23-scoped-memory-substrates.md)). Without an index, coverage erodes and nobody notices; the matrix makes erosion visible.
- The pyramid pushes coverage to the cheapest layer that can assert it: a `--self-test` on every commit beats a manual GUI step per release.
- Separating wiring (L0–L4) from quality (L5) keeps fast deterministic checks honest and quarantines the slow, judgement-heavy eval where it belongs.

## Consequences

- New artifacts: the coverage matrix, the installer and golden-path plans, and the drift check. The eval layer (L5) is owned by ADR-11 and ships its gold tasks separately under `system/eval/`.
- The release plan's gates reference the matrix; a release is "tested" when its required layers are green per the matrix.
- Adding a test surface means adding a row to the matrix and pointing it at a layer — not inventing an unindexed plan.

## Current implementation mapping

The historical L0-L5 names remain coverage aliases, but the reader-facing testing
model now names the behavior each gate proves:

| Promotion gate | Behavior aliases / historical layer |
| --- | --- |
| Source | `static-contract` L0 + `component` L1 |
| Package | `vault-assembly` + `workflow-replay` |
| Runtime | `runtime-integration` L2b/L3 live Hermes, MCP, local services |
| Product | golden path, quality evals, GUI/Bases/dashboard acceptance, G9-G11 |
| Release | S0-S5 + G-gate release evidence, blocker/doc/version close-out |

This is an aliasing migration, not a required-check rename. CI status-check names stay
stable until branch protection and `ruleset-doctor` are updated deliberately.

## L2 implementation note

L2 ("wiring / contract") splits at the **model boundary**, and the two halves belong at different costs:

- **L2a — policy-gate contract (hermetic).** The gate is pure Python (stable entrypoint `policy_mcp.py`, split core `memoria.runtime.policy`), so every lane's allow / deny / dry_run contract is assertable with **no model, Hermes, or Obsidian**. It is already an L1 `--self-test`; folding the hermes-cli §5 write-walls for **all seven lanes** into it (Phase 1, [#73](https://github.com/eranroseman/memoria-vault/pull/73)) pushes the policy-gate half of L2 down to per-commit CI — the cheapest layer that can assert it (Discipline 2 + the pyramid).
- **L2b — agent wiring (runtime-bound).** Whether `hermes -p <profile> chat -q -s <cmd>` actually dispatches, routes through the *live* gate, and lands the right artifact needs the runtime + a cheap model + the Obsidian write path. Assert artifact **shape / placement / audit row**, never prose.

**Driver (resolved).** Hermes ships a scripted one-shot: `hermes -z "<prompt>"` (final text only, clean stdout/stderr) and `hermes chat -q` (same, but tool calls in the transcript — what L2b wants, to observe the write + the gate call). ACP is interactive/editor-only — **not** the automation path.

**Backend (resolved).** L2b does **not** need Obsidian. In production the 5 non-code lanes write only through the `obsidian` MCP → Local REST API (`file` is absent from their positive `platform_toolsets`), but the gate is **transport-agnostic**: `policy_hook.classify` keys on the base tool-name + path at the `pre_tool_call` plugin layer ([ADR-28](28-write-gate-as-plugin.md)), gating `obsidian_*` and `file` `write_file`/`patch` identically — the REST transport itself is L3's contract (matrix #15), not L2's. So:
- **Option B (chosen for unattended).** A filesystem-backed `obsidian` MCP shim with the same tool names (`obsidian_append_content`/`patch_content`/`put_content`). Skills call the same tools, the gate fires unchanged, writes land on disk — no GUI, runs anywhere. The ADR-28 task_id objection to a wrapper MCP doesn't apply: the gate plugin still supplies task_id; the shim only executes the write.
- **Option A (production-faithful variant).** Headless Obsidian (`xvfb-run`) on a self-hosted runner — exercises the real REST path, but heavy/flaky and overlaps L3 #15, so it doesn't gate L2b.
- *(Rejected: re-enabling the `file` toolset — Memoria skills emit `obsidian_*`, so they'd break without an obsidian server.)*

**Attended vs unattended — split by slice, not all-or-nothing.** L2a is unattended already (#73). ADR-80's `workflow-replay` now covers the model-free cassette slice of the deterministic L2-L4 path, but it does **not** replace L2b's live Hermes dispatch signal. For L2b, `scripts/test-l2.sh` implements the unattended Option-B smoke core: a disposable vault, temporary `HERMES_HOME`, filesystem-backed `obsidian` MCP shim, the real policy-gate plugin, a `hermes chat -q` dispatch through a local OpenAI-compatible endpoint, and artifact/audit assertions. By default it starts a deterministic local smoke endpoint so the wiring proof is stable; set `MEMORIA_L2_USE_SMOKE_MODEL=0` to exercise a real cheap/local model endpoint. It remains opt-in/manual or nightly rather than required PR CI. **Keep the full §4 matrix + the GUI/Zotero/dashboard tail attended, per release** — automating the marginal cases (Zotero state, dashboard rendering, prose-adjacent judgment) costs the most and benefits the least, and a watching human catches the un-asserted (loops, near-miss shapes, the silent-pass class).

**Phasing.** (1) gate-contract into `--self-test` — **done** (#73); (2) backend + driver — **resolved** (Option B; `hermes -z`/`chat -q`); (3) opt-in live smoke — **shipped as `scripts/test-l2.sh`** ([#688](https://github.com/eranroseman/memoria-vault/issues/688)), nightly/manual, not PR-blocking. `workflow-replay` remains the automated model-free evidence, while `scripts/test-l2.sh` supplies the live model/Hermes dispatch signal when runtime prerequisites are available. The full hermes-cli §4 matrix stays the attended plan of record.

## Alternatives considered

**Keep ad-hoc plans (status quo).** Rejected: it's how the gaps and drift accrued — coverage is implicit and unmonitored.

**One exhaustive suite.** Rejected: a single mega-plan is unmaintainable and ignores that different surfaces need different cadences (per-commit vs per-release vs per-model-swap). The pyramid matches cadence to cost.


---

<!-- source: adr/30-deterministic-ingest-pipeline.md -->

# ADR-30: Tiered ingest pipeline

> *Terminology note (v0.1.0-alpha.2): `captured` is now the `ingest_status: tier0` floor, **not** a lifecycle value — paper entities are `lifecycle: current` from creation ([ADR-50](50-universal-lifecycle-and-maturity.md); `paper` enum `current → retracted → archived`), and the retry sweep keys on `ingest_status`. The lifecycle chain is `proposed → provisional → current → retracted → archived` (`dormant` retired). Numbered folders (`20-sources/`, `99-system/`) are now type-first ([ADR-47](47-type-first-category-folders.md)): `catalog/`, `system/`. The pipeline decision below is unchanged.*
>
> **Schema note (2026-06-16).** `ingest_status` is a paper-scoped enum, not an
> implicit pipeline scratch field. The schema owns the legal values
> (`tier0`, `enriched`, `complete`, `needs-human`) and Operations must write only those
> values.

> **Implemented and validated live (#100–#116).** The deterministic spine ships as
> six scripts (`ingest_paper` / `resolve_merge` / `extract` / `link` / `pipeline` /
> `sweeps`) plus the seeded `00-meta/vocabulary.md`, the `captured` + `ingest_status`
> schema, and the two re-ingest sweeps on cron. One correction to the design below:
> the Librarian's capability allowlist (ADR-27) disables `code_execution`, so the
> pipeline is reached as an **MCP tool** (`ingest_pipeline`, `mcp/ingest_mcp.py`), not
> a script the worker runs — the agent still makes only the two judgments and writes
> through the gated obsidian MCP. A real paper ingested end-to-end on installer-deployed
> lanes (vocabulary-constrained classify + `[!brief]` + ID-keyed entity links + gated
> writes → `review_status: requested`); the Tier-1 merge is grounded by the 867-paper
> spike. Tracked in the v0.1 release plan as G10.

> **Verified on-box 2026-06-21 (partial — the tag-suggestion layer is absent).** The
> deterministic spine above is real, but the embedding/zero-shot **tag-suggestion layer**
> that this ADR frames as Tier-1's value is **not built**: `classify` intentionally runs a
> deterministic OpenAlex-topic mapping, and the full-text chain ships only Unpaywall → PMC →
> local PDF. The "Implemented and validated live" callout applies to the spine, not to the
> full Tier-1 value layer. Treat tag suggestion, S2ORC/CORE/arXiv/OCR extraction, and Tier-2
> NLI/code-repo enrichment as deferred follow-up work unless a later ADR or issue implements
> them.

## Context

Capture-from-Zotero → ingest is the system's primary intake path but the least-built part of it: the command-palette reference marks the API-POST capture commands as **designed, not shipped**, and the only operable path is a manual Librarian CLI session ([Capture and ingest a source](../how-to-guides/library/capture-and-ingest.md)). The existing `obsidian-paper-note` skill is **fully LLM-orchestrated** — costly, non-reproducible, and fragile (its PDF dependency `ocr-and-documents` currently fails to install) for work that is overwhelmingly mechanical.

Two things make a redesign tractable: a **free, programmatic scholarly-API layer** (Semantic Scholar, OpenAlex, Crossref, PubMed/PMC, arXiv, Unpaywall, CORE) lets enrichment be built as **fallback chains** rather than a single dependency; and **lightweight tooling** (`pymupdf4llm`, embedding retrieval over the user's own tag list) covers the rest without heavy local ML. The hard requirements: every write **gated and audited**; **nothing captured is ever lost**; robustness **by redundancy**.

This ADR was hardened across **two adversarial red-team rounds** and grounded by an **empirical spike on the user's 867-entry library**. The corpus is genuinely heterogeneous — 436 articles, 166 conference papers, 111 preprints, 53 chapters, 49 software, 48 books; 737 DOIs (641 Crossref-registered, 96 arXiv), 283 arXiv/eprint, 117 PMCID, 228 ISBN; mostly CS/ML/HCI with a real biomedical slice. That heterogeneity, and what the spike found about multi-source disagreement, drive the design below. The result is **one pipeline in three tiers** — a guaranteed local floor, a reliable fallback-chained standard layer, and optional extras — so a failing extra cannot break the core, because the core never depends on it.

## Decision

Memoria ingests a source through **one pipeline, three tiers**, with two ordering invariants — **capture commits first** and **scriptable-before-LLM** — and **gated writes only**. The Zotero path is a fast-path branch, not a separate pipeline. The deterministic spine is a script, `ingest_paper.py`, run **by the Librarian worker**; the worker performs the two LLM judgments and **all** vault writes through the `obsidian`/`memoria-policy-gate` ([Policy MCP](../reference/policy-mcp.md)) — no raw filesystem writes. The Zotero selection is read with `curl`, never a browser-style fetch (Better BibTeX's local server returns HTTP 000 to any request carrying an `Origin` header).

> The "scriptable" tiers are **stable-ish, not bit-deterministic** — API, embedding, and OCR outputs drift across versions and over time; pin model/API versions.

### Tier 0 — Guaranteed (local, must succeed → `lifecycle: captured`)

The floor: no network, no PDF, no ML; always succeeds when the citekey is in the local `.bib`.

1. **Durability anchor first.** QuickAdd appends the raw selection (citekey + minimal `.bib` fields) to a local **append-only capture-intake log** (`99-system/logs/capture-intake.jsonl`) **before invoking ingest**. This write depends on neither Hermes, the worker, nor the gate — it is the true "nothing lost" anchor. If the Zotero read itself fails, QuickAdd falls back to a manual-citekey prompt.
2. **Resolve identity + route by type** from `.memoria/memoria.bib` (local): citekey, title, all author names, year, DOI/arXiv/PMCID/ISBN, venue, abstract, and the **entry type** → `paper-note` (article/conf/preprint), `item-note` (software), or book/chapter handling. ~17% of the corpus is non-paper; the pipeline never forces a repo or a book into the paper-note shape.
3. **Build frontmatter** from the type's template — stable IDs, all authors recorded, classification fields empty.
4. **Gated write** to the type's folder (`20-sources/01-papers/` or `02-items/`), `lifecycle: captured`.

### Tier 1 — Standard (network, fallback-chained → *reliable*, not best-effort)

Each subsystem is a chain; the note gets the data if *any* source has it, degrading to Tier 0 only when all miss. **All sources are open access / free** — no subscription publisher APIs. Tier 1 carries the system's *value* (a Tier-0-only note is a near-empty stub); it is not safety-critical but it **is** correctness-critical, and the merge below is its hard problem — validate it on a real sample before relying on it (see Consequences).

**Resolve + merge — `S2 + OpenAlex` co-primary, `Crossref` for non-arXiv DOIs.** The spike showed these sources **disagree and are each incomplete** (reference counts for the same paper: 151/129/146, 107/32/95, 68/82/68 across S2/OpenAlex/Crossref; ORCID present in OpenAlex up to 14/paper but ~0 in S2). Therefore the merge is **per-field, best-source-wins, with provenance**, not whole-record precedence:

- authors + **ORCID** + affiliations ← **OpenAlex**; `intents` / `isInfluential` / `contexts` / `tldr` / `embedding` ← **S2**; canonical scalar metadata ← Crossref/OpenAlex.
- **references = the union across sources, deduped by DOI** (the keyspace the vault stores), since no single source is complete. The graph requires the **paginated `/paper/{id}/references` and `/citations`** endpoints — the **batch endpoint does not reliably return nested references** (empirically 7/21 papers), so this costs extra calls against the ~1 req/s budget; cache by DOI/CorpusId.
- Do **not** pair author sub-fields by index across sources (name forms and ordering differ); merge within a source, then reconcile by name+position+ORCID.
- These are **model/aggregator outputs, not ground truth** — only the ID matching is exact; intent/influence/contradiction signals are advisory.

**Conditional-by-ID enrichment** (each well-populated in the corpus): **PMCID** → PMC open-access full text (pre-extracted) + MeSH (PMCID→PMID via the NCBI ID converter); **arXiv ID** → arXiv full text + categories; **non-arXiv DOI** → Crossref references/metadata.

**Full text — pre-extracted first, parse last:** `S2ORC → CORE (by DOI) → PMC (PMCID) → arXiv (arXiv ID) → Unpaywall→OA-PDF → local Zotero PDF → pymupdf4llm → OCR`. Sources returning text already-extracted (S2ORC/CORE/PMC) are preferred — no local parsing, no untrusted-PDF surface. A Zotero capture always has the local PDF as a floor. The OCR decision is the script's (a deterministic text-layer + coherence check; the coherence heuristic is **English-biased** — non-English papers must not be auto-misrouted). Empty/garbled extract is **flagged degraded**, not silently dropped; it does not abort the ingest.

**Tag suggestion — the kept NLP, domain-agnostic, over the user's tag set.** Tags are a **setup input**: the user seeds an initial vocabulary (tied to `research-focus`) that the system develops over time. Each tag should carry a **short definition/description** — a 1–3-word label embeds weakly; the definition is what makes similarity meaningful. Produce a ranked shortlist per dimension (**topic / methodology / research-type**) by combining: (a) **embedding similarity** between the paper text and each tag's *definition* (domain-agnostic — works across the biomedical + CS corpus; reuses the `qmd` stack); (b) optional **zero-shot classification** (one inference *per tag* — a real cost); (c) the API taxonomies (OpenAlex topics, MeSH for the PMCID slice, arXiv categories) as *additional* signal. The model ranks existing tags; it never invents one.

**Classification proposal (LLM call #1) — promotes `captured → proposed`.** Map the shortlist to `_proposed_classification`, **hard-schema-constrained** to the vocabulary. Extracted document text is **untrusted input** (delimited, instructions stripped, schema-constrained) — see Security.

**Linking (ID-keyed, idempotent).** Find-or-create `venue-note` (ISSN), `person-note` (ORCID), `organization-note` (ROR), keyed on stable IDs. **No-ID entities are recorded by name in the paper-note, never node-created, never name-merged** (venues/orgs as well as authors). Cites/cited-by via local **DOI-match** of the merged reference union against the vault; annotate edges with `isInfluential` / `intents` / `contexts` where S2 supplied them.

### Tier 2 — Optional (best-effort; absent-able)

- **`[!brief]` comparative narrative** (LLM call #2) over deterministically-selected neighbours.
- **NLI contradiction signal** — *advisory, low-precision only*; a hint for the brief, never a fact.
- **arXiv → code-repo** (Papers-with-Code / confidence-thresholded) → `item-note` + cross-link; proposed when uncertain.

### Lifecycle

Adds one value, **`captured`** (today `lifecycle` is `proposed · current · dormant · archived`). The classification proposal is the only thing separating `captured` from `proposed`; everything else is enrichment present in either state.

- **paper-note:** `captured` (Tier 0) → `proposed` (classification proposal) → `current` (human).
- **entity notes:** created at `proposed` during Tier-1 linking → `current` (human, lazily) — the existing entity lifecycle, no new track.
- **terminal floor:** after bounded failed re-ingest attempts, `captured` + `ingest_status: needs-human` so the retry-sweep stops and the human is surfaced.

### Reliability, re-ingest, serialization

The capture-intake log + the `captured` stub mean a failure anywhere in Tiers 1–2 **leaves the note at `captured`** — recoverable, nothing lost. This supersedes the old "materialise a `capture-timeout` candidate" idea for the *deliberate-capture* path. There are **two distinct backstops, with distinct owners**:

- **(a) log-reconciliation** — a pass that reconciles `capture-intake.jsonl` against created notes and re-drives any entry whose **Tier-0 stub never landed** (the durability anchor for a failed first write).
- **(b) captured retry-sweep** — re-runs **Tier 1** on `captured` notes whose enrichment failed, with backoff and the `needs-human` floor.

Re-ingest is **idempotent in writes** (ID-keyed find-or-create makes no duplicates) but **not stable in output** (refreshed APIs/vault → refreshed enrichment). Find-or-create safety requires **serialized writes** — and the single-lane WIP=1 invariant only serializes **board-dispatched** work. Therefore **all re-ingest (manual command included) is enqueued as a board card**, never run as an ad-hoc `hermes -p memoria-librarian` session, so a manual re-ingest cannot run concurrently with sweep (b) and race find-or-create. (Equivalently, a per-citekey/per-entity lock; routing through the board is the chosen mechanism.)

### Security (untrusted ingest surface)

The gate bounds *where* writes land, not their *content*. So: local PDF/OCR parsing runs in a **subprocess with CPU/memory/time `rlimit`s and a temp working dir** — not in the worker's main process (MuPDF has a CVE history); pre-extracted API text (S2ORC/CORE/PMC) is preferred precisely because it avoids local parsing, leaving only the local-PDF floor as the residual untrusted-parse surface. For prompt injection: **classify (LLM #1) is hard-schema-constrained**, so a crafted PDF/abstract cannot steer the typed field. The **`[!brief]` (LLM #2) is free-text and *not* schema-constrained** — instruction-stripping is unreliable, so a crafted abstract/neighbour can steer its prose; this is a **lower-stakes, human-reviewed, acknowledged residual** injection surface, not one the schema defense covers.

### Cost / latency (per ingest)

Tier 0 is effectively free (local). Tier 1 is a handful of HTTP calls — the merge chain **plus** the paginated `/references` fetch (the graph is not free in the batch) — one local embedding pass, an optional **per-tag** zero-shot pass, and **one** schema-constrained classify call. Tier 2 adds at most **one** larger `[!brief]` call. The cost moves off the old 8-step LLM loop into cheap HTTP + a reused embedding model; the additions the first estimate omitted are the `/references` calls and per-tag zero-shot.

### Future options

Subscription publisher APIs are deliberately out of scope (open-access full text via S2ORC/CORE/PMC/arXiv/Unpaywall covers the OA slice). Deferred: heavier domain NLP (scispaCy, an RCT/PICO classifier) only if the embedding/zero-shot tag layer proves insufficient; the S2 Recommendations API and `/snippet/search` for discovery; an API-POST capture transport ([The control plane](../explanation/architecture/control-plane.md) ideal) once the Hermes API is stood up — the script front-end ships first.

## Consequences

- **Robust by redundancy.** No single API is load-bearing for *safety*; the Tier-0 floor guarantees a valid note offline / for an unindexed paper / with no PDF.
- **But Tier-1 correctness is owed.** The fallback chains traded a single-API risk for a **multi-source merge** risk — the spike confirmed the sources disagree, so the merge (per-field best-source; reference union deduped by DOI) is the now-load-bearing piece and **must be validated on a real sample** of the vault's papers before the system is trusted to enrich correctly. The merge is grounded by an n≈22 spike here; a fuller pass is a build-time gate.
- **The "no extra call" linking claim is retracted** — the citation graph requires the paginated `/references` endpoint, costed above.
- **Heterogeneity handled.** Type-routing (paper/item/software/book) + by-ID conditionals (PMCID/arXiv/Crossref) match the real corpus; books/software degrade to metadata-only rather than breaking.
- **Domain-agnostic tagging.** Embedding/zero-shot over the user's defined tag set works across biomedical + CS, where a MeSH-only crosswalk would be empty for most papers.
- **Nothing lost, everything gated** (un-gated capture-intake log as the anchor; every note write audited); honest determinism (idempotent writes + board-serialized re-ingest, not identical output).
- **Cost — a real rewrite.** `obsidian-paper-note` slims to "run the script, judge, write"; `ingest_paper.py` must be built and tested, with the merge logic, structured-output contracts, and explicit edge-case branches (type routing, no-DOI/PDF, OCR fallback, no-ID entities, non-English text).
- **Constraint — lifecycle.** Adds `captured` (+ `ingest_status: needs-human`) and changes the deliberate-capture dead-letter to "stays `captured`"; docs describing the LLM-orchestrated ingest must be updated.

## Alternatives considered

- **Single-source (S2-only) enrichment.** Rejected: rests on one API's coverage and ML outputs; the spike showed each source is incomplete, so fallback chains + a union graph are required.
- **Split into two ADRs (spine + spike-gated enrichment).** Rejected for **three tiers in one ADR**: defining enrichment as reliable-but-non-load-bearing-for-safety makes approving the whole safe without a multi-step project — but the Tier-1 *validation* the split would have forced is preserved as a build-time gate.
- **A separate Zotero capture+ingest pipeline.** Rejected: the standard ingest is already Zotero-native; a Zotero-specific one duplicates ~90% and drifts.
- **Deterministic work at capture (in QuickAdd glue).** Rejected: thickens glue the control plane keeps thin, bypasses the gate, and blocks the capture UX on slow PDF tooling. The spine runs in the worker.
- **`candidate-note` as the universal capture record.** Rejected: "awaiting decision" mismatches a deliberate capture, plus happy-path churn. The capture-intake log + card commit the capture; the candidate stays for leads/dead-letters.
- **A `derived` lifecycle track for entities.** Rejected: entity notes already use `proposed → current`.
- **GROBID / Marker as the default extractor.** Rejected: heavy and (Marker) currently failing to install; pre-extracted API text + `pymupdf4llm` cover the common case, OCR/Marker only for scanned/equation-heavy PDFs.
- **Keep the LLM-orchestrated ingest.** Rejected: non-reproducible, costly, fragile for mechanical work.

## Related

- **Workflows affected:** [Capture and ingest a source](../how-to-guides/library/capture-and-ingest.md), [Obsidian command palette](../reference/obsidian-command-palette.md).
- **Files affected:** `obsidian-paper-note/SKILL.md` (slims to *call the ingest tool* + judgments + gated write), a new `ingest_paper.py` (source of truth for API field lists, chain order, and merge rules — kept out of the ADR so it can change without re-deciding), [Ingest routing](../reference/ingest.md) (type routing, fallback chains, extraction tiers, S2-not-GROBID), [Frontmatter fields](../reference/frontmatter.md) / [Document types](../reference/document-types.md) (`captured` + `ingest_status`), `capture-from-zotero.js` (`curl` not `requestUrl`; the capture-intake log), the seed-tag vocabulary format (tags carry definitions).
- **Correction (delivery mechanism):** the worker **cannot run the pipeline as a script** — the Librarian's capability allowlist (ADR-27) disables `code_execution`/`terminal`/`file`. The deterministic spine is therefore delivered as an **MCP tool** (`ingest_pipeline` on the `memoria-ingest` server, `mcp/ingest_mcp.py`, wrapping `runner.run()`), reached the same way vault access and the policy gate are. The tool reads + computes only; the agent still fills the two holes and writes through the gated obsidian MCP. (The CLI entry points remain for cron/sweeps and offline use.)
- **Related decisions / Depends on:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md) (the write gate), [ADR-16](16-systematic-review-adopt-on-demand.md).
- **Supersession note:** deliberate-capture dead-letters stay `captured` rather than materialising a `capture-timeout` candidate.
- **Source discussion:** design conversation + two red-team rounds + an 867-paper API merge spike, 2026-06-03.


---

<!-- source: adr/31-native-obsidian-mcp.md -->

# ADR-31: Native obsidian MCP over HTTPS

## Context

Every lane's vault-write path is the `obsidian` MCP ([ADR-27](27-hermes-native-config-and-gate-enforcement.md)/[ADR-28](28-write-gate-as-plugin.md)). v0.1 used the **uvx `mcp-obsidian`** package (stdio), which **hardwires port 27124** and reads only `OBSIDIAN_API_KEY` — `OBSIDIAN_HOST`/`OBSIDIAN_PORT` are ignored. Because only one Obsidian vault can serve a given port, a sandbox and a production vault couldn't both expose the REST API at once, forcing a "keep production closed during runs" rule and manual port juggling.

The **Local REST API plugin (v4.1.2, "with MCP")** now ships its **own native MCP server** at `/<host>/mcp` (Streamable HTTP) — a viable replacement whose port lives in the URL.

## Decision

Point every profile's `obsidian` `mcp_servers` entry at the plugin's **native MCP over verified HTTPS on loopback**, dropping uvx `mcp-obsidian`:

```yaml
obsidian:
  url: "https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp"
  ssl_verify: "${OBSIDIAN_MCP_SSL_VERIFY}"
  headers:
    Authorization: "Bearer ${OBSIDIAN_API_KEY}"
```

- **Verified HTTPS, not plain HTTP** — Hermes supports `mcp_servers.<name>.ssl_verify` as either a bool or a path to a PEM CA bundle for HTTP/SSE MCP servers. `OBSIDIAN_MCP_SSL_VERIFY` points at the Local REST API plugin's exported certificate/CA bundle, so the bearer key no longer travels over unencrypted loopback and verification remains on.
- **Port via `OBSIDIAN_MCP_PORT`** (`~/.hermes/.env`) so sandbox + production coexist on different ports — no more "keep production closed."
- **Explicit `Authorization: Bearer`** header — `hermes mcp add --auth header` sent a form the plugin 401'd; the exact bearer header works.

## Security — the gate still holds

The native server exposes 16 tools with **different names** (`vault_write`/`append`/`patch`/`delete`/`move`, `command_execute`, …). The write gate matches on `obsidian` + a write keyword, and `WRITE_KEYWORDS` already covers `write`/`append`/`patch`/`delete`/`move` — so the native write tools are gated **with no matcher change** (verified: `mcp_obsidian_vault_write` to a denied zone is blocked). The path arg is `path` (first `PATH_KEYS` match), so the gate evaluates the right file.

`policy_hook` adds a **hard-deny** (`DENY_OBSIDIAN`) for `command_execute` (arbitrary Obsidian command — no path to gate), `vault_delete`, and `vault_move` (destructive, unused by the workflows; the old uvx tools were read/write/append/patch only). These are blocked for every lane even inside an allowed zone — least privilege, defense-in-depth beyond tool-selection.

## Consequences

- **Sandbox + production coexist** on different ports; the uvx dependency is gone.
- **Validated live:** read + a full ingest end-to-end through the native MCP (note written via `vault_write`/`append`, gated); pytest coverage now pins native tool names and the hard-denies.
- **Setup cost:** enable the plugin's HTTPS endpoint on `OBSIDIAN_MCP_PORT` and set `OBSIDIAN_MCP_SSL_VERIFY` to the exported PEM certificate/CA bundle path. **All profiles** *(v0.1.0-alpha.2: the fleet is the five profiles of [ADR-48](48-copi-and-agent-consolidation.md); originally seven)* are switched — leaving any lane on uvx (27124) would re-introduce the port collision the moment it ran, so the coexistence benefit only holds with every lane native. The shared `policy_hook` (with `DENY_OBSIDIAN`) gates them all identically.
- **Residual:** the certificate file is per-machine plugin state, so it stays in `.env` / gitignored plugin state rather than repository source.

- **Related:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md) (the write gate this preserves).


---

<!-- source: adr/32-external-access-over-mcp.md -->

# ADR-32: External access over MCP

## Context

> *Note (v0.1.0-alpha.2): the profile names below predate [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the seven specialists to five — Mapper → Librarian (`map` lane), Socratic → Co-PI, Verifier → Peer-reviewer, Coder → Engineer, Linter → an engine. The MCP-only decision (no direct `web`; deterministic tools self-hosted) is unchanged and applies to the current fleet — **with one tightening: the Decision's two `terminal` exceptions below (Coder, Linter) are retired.** The Linter is now a no-agent engine ([ADR-48](48-copi-and-agent-consolidation.md)), and the Engineer (the Coder's successor) is MCP-only like every other lane: **no profile ships `terminal`, `file`, or `code_execution`**, enforced fail-closed by the policy plugin's denylist ([ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md)). The self-hosted retraction MCP described below (`verify_mcp.py` / `retraction_check(doi)`) was never shipped: [ADR-46](46-seven-layer-architecture.md)/D41 delivers retraction as the cron-only sweep engine `operations/integrity/retraction/retraction.py` instead — same three-source design and data provenance, no MCP facade.*

A fleet-wide audit of the seven profiles found the capability surface inconsistent. Some profiles ran deterministic engines as loose scripts via the `terminal` toolset (the Linter's `detectors.py`); some made scholarly-API calls directly via the `web` toolset (the Librarian's `paper-lookup`/`enrich`, the Verifier's retraction lookups); capabilities were a mix of authored skills, K-Dense web-fetch skills, and raw HTTP. This matters because the policy gate ([ADR-28](28-write-gate-as-plugin.md)) and Hermes' determinism guarantees only apply to **MCP tools** (`mcp_<server>_<tool>`): a call made through `web` or `terminal` is neither gated nor audited, and when the *model* constructs an HTTP call or runs a check each turn, the result is no longer deterministic or reproducible in CI. The audit also surfaced a stale claim — that the Librarian wrote back to Zotero — when Memoria uses Zotero's read-only local API, so the "direct API access is required" assumption was partly false.

## Decision

Profile capabilities — both deterministic engines and external service access — reach the agent **only over MCP servers**, registered in each profile's `config.yaml` `mcp_servers` and gated by the policy plugin. The agent's `code_execution` and `web` toolsets are **disabled on every profile**; `terminal` is disabled except for two deliberate exceptions: the **Coder** (delegates to external coding agents that execute code outside the gated runtime) and the **Linter** (runs its own zero-LLM `detectors.py`). *(Both exceptions were later retired — see the note under Context; no current profile ships `terminal`.)* Where no suitable off-the-shelf MCP exists, Memoria **self-hosts a thin, pure-stdlib MCP over authoritative open data** rather than granting a raw toolset or vendoring an unproven dependency.

## Consequences

- **Every profile's external access is gated, audited, and deterministic.** Discovery is the `paper_search` MCP (openags/paper-search-mcp); Zotero reads are the read-only `pyzotero` MCP; citation context is the pyzotero MCP's Semantic Scholar tools; vault access is the `obsidian` MCP; the deterministic ingest pipeline is the `ingest` MCP ([ADR-30](30-deterministic-ingest-pipeline.md)); the Linter's detectors are the `structural-detectors` skill's bundled engine.
- **Retraction is self-hosted on authoritative open data.** No mature retraction MCP exists; the planned `verify_mcp.py` facade was not shipped. The current implementation is the cron-only sweep engine `operations/integrity/retraction/retraction.py`, using three sources, most-authoritative first: the Retraction Watch dataset (Crossref-owned, CC, refreshed from `gitlab.com/crossref/retraction-watch-data`), CrossRef `update-to`/`is-retracted-by` (real-time delta), and Open Retractions (fallback). Read-only, deterministic, offline-capable, with an offline self-test.
- **Least privilege.** Five of seven profiles (Librarian, Verifier, Mapper, Socratic, Writer) make **no direct API calls and run no code** — their only outward path is gated MCP. The remaining direct-execution surface is the Coder's and Linter's `terminal`, both by design; the Coder's hand-off to external coding agents is the largest trust surface in the fleet and is acknowledged as such. *(Retired — see the Context note: the Engineer/Linter `terminal` was removed; only the external coding agent the Engineer delegates to runs outside the gate.)*
- **Cost.** More MCP servers to install and keep running. Two require a one-time host install (`paper-search-mcp` in the vault venv, `zotero-mcp` on PATH); the self-hosted servers (`policy`, `ingest`) run from the vault venv. The Retraction Watch CSV needs a periodic cron refresh through the retraction Operations engine.
- **Residual.** The obsidian MCP now uses verified loopback HTTPS ([ADR-31](31-native-obsidian-mcp.md)); external-agent execution remains outside the gate by construction.

## Alternatives considered

- **Keep `web`/`terminal` enabled with `external_api_policy` as the guardrail.** Rejected: those calls bypass the policy gate's audit trail, let the model improvise non-deterministic HTTP/logic, and grant a far larger blast radius than a typed MCP tool — the opposite of the determinism the Linter and ingest pipeline are built on.
- **Vendor `retraction-watch-mcp` (the only purpose-built retraction MCP).** Rejected as the primary: it is a 0-star, single-author repo with a package/name mismatch, and bundles a ~360 MB SQLite snapshot. We instead pull the **same authoritative dataset** straight from Crossref's official distribution into a thin server we control; the vendored RW server remains an upgrade path if its provenance hardens.
- **Adopt a paper-search MCP that downloads full text (openags' `download_*` tools include a Sci-Hub fallback).** Rejected for those tools: the Librarian uses only the `search_*` tools; PDF retrieval and extraction stay with the ingest pipeline (Marker), so the Sci-Hub path is never invoked.

## Related

- **Related decisions / Depends on:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md) (native config + gate enforcement), [ADR-28](28-write-gate-as-plugin.md) (the policy gate this rule rides on), [ADR-30](30-deterministic-ingest-pipeline.md) (the pipeline-as-MCP precedent), [ADR-31](31-native-obsidian-mcp.md) (the obsidian MCP).
- **Files affected:** `vault/.memoria/operations/integrity/retraction/retraction.py` (was planned as `mcp/verify_mcp.py` — see the alpha.2 note above), `vault/.memoria/scripts/retraction-refresh-cron.sh`, every `vault/.memoria/profiles/memoria-*/config.yaml` and `vault/.memoria/lane-overrides/*.yaml`, the Linter's `structural-detectors` skill, the Verifier's `retraction-check` + `claim-checks` skills.


---

<!-- source: adr/33-cluster-mcp-bertopic.md -->

# ADR-33: BERTopic cluster MCP for the Mapper

## Context

> *Note (v0.1.0-alpha.2): "the Mapper" is now the **Librarian's `map` lane** ([ADR-48](48-copi-and-agent-consolidation.md)); the cluster-MCP decision below applies to that lane unchanged.*

The Mapper's three commands — `scope-project`, `gap-report`, `cluster-map` — are corpus *clustering* over note embeddings (HDBSCAN density clusters, UMAP projection, BERTopic/TF-IDF topics). They are wired as the K-Dense `scikit-learn` and `umap-learn` **skills** granted in `mapper.yaml`. But a Hermes skill whose work is running Python executes in the `code_execution`/`terminal` sandbox and declares `requires_toolsets`; a skill is unavailable when its required toolset is off. The Mapper disables **both** `code_execution` and `terminal` (it is read-mostly, [ADR-32](32-external-access-over-mcp.md)), and has no compute MCP — so those skills **cannot actually run**. The clustering is granted and described but non-functional. (`qmd` is unaffected: it is an index-backed search skill, not a per-invocation Python run, which is why it works on the same execution-disabled lanes.)

No mature, typed, gated clustering/topic MCP exists to adopt — a survey of the ecosystem found only an abandoned `k_means`-only scikit-learn server, a 0-star UMAP-only pruning tool, a graph-substrate server (Neo4j), and generic "run arbitrary Python" servers (which would re-introduce the very code-execution surface the Mapper removed). Granting the Mapper `terminal` would close the gap but re-open arbitrary execution **and network** (a shell can `curl`), undoing the MCP-only / no-direct-external property [ADR-32](32-external-access-over-mcp.md) established.

## Decision

Add a Memoria-authored **cluster MCP** (`vault/.memoria/mcp/cluster_mcp.py`) and ship it in v0.1. The MCP owns both the lightweight typed-graph clustering path and the optional heavy topic-modeling path: graph/community maps run with NetworkX over authored `links:` and `relationships`, while **BERTopic** remains the opt-in topic-modeling backend for the standard sentence-transformers → UMAP → HDBSCAN → c-TF-IDF pipeline. The Mapper invokes typed MCP tools such as `cluster_build_graph`, `cluster_emit_canvas`, and `cluster_model_topics` over MCP. The Mapper stays **fully sandboxed** (`code_execution` / `terminal` / `web` all disabled); the non-runnable `scikit-learn` and `umap-learn` skill grants are retired in favour of the MCP. This follows the [ADR-30](30-deterministic-ingest-pipeline.md) precedent (Memoria-authored deterministic compute reaches the agent over MCP) and the [ADR-32](32-external-access-over-mcp.md) rule (shared capability at the MCP layer, posture isolation at the agent layer).

## Consequences

- **The Mapper's graph clustering and Canvas proposal path actually run** — gated and audited through the policy plugin — while the lane keeps `code_execution`/`terminal`/`web` off. The "no direct external access" property holds.
- **The heavy ML dependencies stay optional and isolated.** BERTopic pulls `sentence-transformers` (→ `torch`), `umap-learn`, and `hdbscan`. That install-footprint cost is accepted for topic modeling, but it is not part of the lean policy-core requirements and not required for the default graph/community path.
- **Self-contained and deterministic.** The graph path uses authored vault edges plus fixed seeds and echoes parameters; the BERTopic path computes embeddings itself when the optional dependencies are installed (or, later, may read `qmd`'s vector index to avoid recompute). The offline self-test proves deterministic graph behavior and clean BERTopic degradation when optional dependencies are absent.
- **Retires two dead skill grants** (`scikit-learn`, `umap-learn`) and tidies the installer's skill inventory.
- **Implementation is a tracked follow-up.** This ADR records the decision and the shape; the server, the Mapper `config.yaml` `mcp_servers` wiring, the `cluster-mapping` skill update (call the MCP, not the skills), and the docs land next.

## Current implementation mapping

`src/.memoria/mcp/cluster_mcp.py` is the shipped cluster MCP. Its default,
PR-safe surface is lightweight and deterministic: `cluster_build_graph` builds a
typed NetworkX graph from authored note `links:` and entity `relationships`,
computes communities/centrality/layout, and `cluster_emit_canvas` writes a staged
claim-debate Canvas under the allowed maps home. `cluster_model_topics` is the
optional BERTopic surface. If BERTopic or its heavy dependencies are absent, it
returns a structured `bertopic-not-installed` error instead of requiring the default
vault install to carry the ML stack. `tests/test_cluster_mcp.py` locks that split:
graph/canvas behavior must run deterministically, and the topic-modeling path must
either run with enough data and dependencies or degrade cleanly.

## Alternatives considered

- **Grant the Mapper `terminal`** (the Linter's pattern). Rejected: the Linter's `terminal` is justified because `detectors.py` is a CLI build tool (CI / pre-commit / cron) and the lane is trusted/local; the Mapper's clustering is agent-runtime-only, and a shell would re-open arbitrary execution + network on a read-mostly lane — a direct regression of ADR-32.
- **Adopt an off-the-shelf clustering/topic MCP.** Rejected: none is mature, typed, and gated. The candidates are abandoned (`k_means`-only), 0-star and UMAP-only, wrong-substrate (graph DB), or arbitrary-code executors (a security regression).
- **Wire `sentence-transformers` + `umap-learn` + `hdbscan` + c-TF-IDF by hand.** Rejected in favour of **BERTopic**, which bundles the identical pipeline in one dependency and one call — a smaller, better-tested surface.
- **Defer clustering for v0.1** (a `qmd`-similarity-only Mapper). Rejected: corpus density/topic mapping *is* the Mapper's reason to exist ("map the corpus"); shipping it without clustering guts the profile.

## Related

- **Depends on / extends:** [ADR-32](32-external-access-over-mcp.md) (compute over MCP; posture isolation at the agent layer), [ADR-30](30-deterministic-ingest-pipeline.md) (the deterministic-pipeline-as-MCP precedent).
- **Files affected (on implementation):** `vault/.memoria/mcp/cluster_mcp.py` (new), `vault/.memoria/profiles/memoria-mapper/config.yaml` (`mcp_servers`), `vault/.memoria/lane-overrides/mapper.yaml` (drop `scikit-learn`/`umap-learn`), `vault/.memoria/profiles/memoria-mapper/skills/cluster-mapping/` (call the MCP), `docs/reference/installer.md` + `docs/reference/profiles.md`.
- **Source discussion:** the profile audit (PR #210) — the clustering gap surfaced while minimizing the capability duplication ADR-32 names.


---

<!-- source: adr/34-code-artifact-autopilot.md -->

# ADR-34: Code-artifact autopilot

> **Rejected 2026-06-16.** The proposed scheduled-script autopilot is
> structurally precluded by [ADR-21](21-l3-autonomy-ceiling.md)'s L3 autonomy
> ceiling. Code-lane execution remains human-bounded; future work belongs to the
> explicit keep/revert experiment loop tracked in #369, not a per-note unattended
> script flag.

## What

An opt-in `autopilot: true` flag on a `code-note` that lets Hermes run a scripted analysis on a schedule — e.g. a weekly metric-refresh script that regenerates dashboards without a human kickoff. Per-`code-note`, never global.

## Why

Recurring analyses currently need a manual trigger every time. For a genuinely repetitive script with a fixed, scalar output, that kickoff is pure friction the system could absorb.

## Trade-offs

- Scheduled execution means compute spend without a human in the loop — bounded only if a per-run budget and a tight opt-in scope are enforced.
- A failed scheduled run can leave stale metric data downstream; autopilot needs a fail-loud path, not silent staleness.
- Adds a card/note field and dispatch wiring for scheduled code runs.

## Rejection rationale

Memoria will not adopt this shape. A per-`code-note` `autopilot: true` flag creates
unattended code execution from vault content, adds a second execution trigger, and
weakens the L3 ceiling. If repeated code experimentation becomes valuable, it must
use the lane-bounded keep/revert experiment loop: explicit metric, budget, output
path, audit trail, and human promotion.

## Alternatives considered

**Adopt now with a global flag.** Rejected: no current use case warrants the safety overhead.

**Adopt only via the Coder profile's cron, not a per-`code-note` flag.** A possible future shape; defer the choice between the two until a concrete first use case exists.

## Related

- **Tracking issue:** [#369](https://github.com/eranroseman/memoria-vault/issues/369)
  tracks the replacement code-experiment loop shape.
- **Workflows:** [Code](../how-to-guides/project/create-a-code-artifact.md)
- **Files:** [The Coder](../explanation/profiles/engineer.md), `99-system/templates/code-note.md`
- **Related proposal:** [Nightly discovery loop](61-nightly-discovery-loop.md) §2 (Coder experiment loop) — the keep/revert variant of the same Coder-lane autonomy; this proposal is the *scheduled-script* variant.
- **Bounded by:** [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the Coder exception).


---

<!-- source: adr/35-cross-run-skill-insights.md -->

# ADR-35: Cross-run skill-insights memory

## What

A `00-meta/skill-insights/` log where Hermes records patterns learned across projects — e.g. "X classifier underperforms when Y" — and surfaces them in future planning sessions. The MetaClaw / CORAL pattern from autonomous-research systems (MetaClaw: multi-round claim extraction that iteratively refines what counts as a learnable signal; CORAL: cross-run aggregation that pools those signals across separate project runs into a queryable log).

## Why

Today Hermes treats every project as fresh — there is no compounding learning across projects. Patterns the human notices stay in their head or in ad-hoc notes, never in a queryable log the agent can reuse.

## Trade-offs

- A real meta-claims schema, a write discipline, and a review surface — all non-trivial to design and maintain.
- Low payoff until the corpus is dense enough that cross-project patterns actually recur and become visible.

## When this matters

A concrete cross-project pattern recurs often enough to be worth capturing — ideally scoped narrowly first (e.g. classifier mis-firings only) rather than a general meta-memory. The detection prerequisite **now exists**: alpha.5 added the classify-miss instrumentation, so a recurrence sweep over the logs can surface "trigger ready" instead of relying on the operator noticing — the narrow slice (sweep → Inbox card → `skill-insights/`) is buildable now; only the *volume* of recurrences is usage-gated.


## Alternatives considered

**Adopt now (general).** Rejected: too much architecture for a single-user vault at current density.

**Adopt scoped to a single domain** (e.g. classifier mis-firings). Accepted as the prudent first implementation shape once the linked issue is ready.

## Related

- **Tracking issue:** [#371](https://github.com/eranroseman/memoria-vault/issues/371) — implementation readiness lives on the issue.
- **Files:** none currently.


---

<!-- source: adr/36-dedicated-review-note-type.md -->

# ADR-36: Dedicated review-note type

## What

A `review-note` type that stores reviewer judgments with provenance, separate from the note being reviewed — giving every review decision a durable, queryable home.

## Why

Review provenance today lives on the board card (`review_status`, `reviewed_at`, handoff `summary`) and in the audit log. Once a card closes, its review history is not directly browsable as notes.

## Trade-offs

- Adds another note type to the schema for a benefit not currently felt.
- A parallel review-note tree to maintain alongside the card/audit record.

## When this matters

An audit requirement emerges that needs persistent, browsable review records outliving the board card.


## Alternatives considered

**Adopt now.** Rejected: adds a note type for an unfelt benefit.

**Query the audit-log JSONL directly** (no new type). The current approach; works for now.

## Related

- **See also:** [Kanban board](../explanation/kanban-board/README.md) (existing `review_status` semantics).
- **Files:** none currently.


---

<!-- source: adr/37-retriever-scout-profile.md -->

# ADR-37: Retriever / Scout as a separate profile

## What

Split the Librarian into **Retriever** (broad discovery, candidate generation) and **Librarian** (ingest, enrichment, classification), so discovery can scale across more candidates without taxing the classification model with discovery-shape work.

## Why

At high discovery volume, one profile doing both `find` and `ingest` may have its classifier and its discovery scorer competing for the same compute and context.

## Trade-offs

- One more profile to configure (lane policy, command catalog, SOUL.md) with no current bottleneck to justify it.
- A unified Librarian is simpler: single lane, single command set.

## When this matters

Discovery volume genuinely overwhelms the unified Librarian — e.g. the [nightly discovery loop](61-nightly-discovery-loop.md) running at scale, where discovery scoring and classification visibly contend.


## Alternatives considered

**Split now.** Rejected: one more profile with no current bottleneck to motivate it.

**Stay unified forever.** Rejected as a long-term answer: at enough scale the two concerns diverge.

## Related

- **Workflows:** [Find](../how-to-guides/library/find-new-sources.md), [Ingest](../how-to-guides/library/capture-and-ingest.md)
- **Files:** [Profiles](../explanation/profiles/README.md), [The Librarian](../explanation/profiles/librarian.md)


---

<!-- source: adr/38-pre-file-similarity-gate.md -->

# ADR-38: Ratchet — a qmd similarity gate before filing a synthesis note

> *Terminology note (v0.1.0-alpha.2): the `reference` type is retired ([ADR-50](50-universal-lifecycle-and-maturity.md)) — read "`claim-note` or `reference-note`" below as just claim and hub notes — and `30-synthesis/` is now `notes/claims/` + `notes/hubs/` ([ADR-47](47-type-first-category-folders.md)). The decision is unchanged.*

## What

A similarity check at the *moment a synthesis note is created*: before a `claim-note` or `reference-note` is filed into `30-synthesis/`, run a `qmd` hybrid search against existing synthesis notes and, if the top match exceeds a threshold, flag the note and present the neighbours to the human to confirm / merge / override. Borrowed from Karpathy's overnight-loop pattern (gate every addition against existing state), adapted from "revert if loss didn't improve" to "don't file if it duplicates."

## Why

Memoria catches duplicates **retrospectively**: `find-duplicates` runs on a cadence and surfaces near-duplicates *after* they exist and have been wikilinked, at which point merging is painful (every inbound link must be repointed). The most common synthesis failure — paraphrasing something already in `30-synthesis/` — slips through until the next sweep.

## Trade-offs

- Depends on a current `qmd` index; a stale index silently misses recent notes, so the gate must trigger an incremental index or warn when the index is old.
- Expect a noisy first ~6 months: keyword-near, claim-distinct pairs the human must still read.
- No `--force` bypass — the human's confirm/merge/override *is* the escape valve.

## When this matters

**(a) is now satisfied** — `qmd` is live in the agent retrieval path (wired into the Librarian/Writer/Peer-reviewer skills as of alpha.5). What remains is **(b)** a synthesis corpus dense enough that filing a duplicate is a real risk — the point at which the 0.8 threshold and false-positive rate can be tuned against real notes — plus building the retrospective `find-duplicates` sweep, which does not yet exist. The gate primitive can ship in **shadow mode** first (log neighbours, never block) and harden once the corpus is dense.

## Current implementation

alpha.8 ships the shadow primitive, not enforcement. The active PI-side filing
surfaces (`Memoria: create linked claim note` and `Memoria: structured source
capture`) run `qmd search --format json --full-path` before writing the note,
filter to claim/source neighbours, attach up to three neighbours in a
`[!similarity]` callout, and append one content-light
`system/logs/pre-file-similarity.jsonl` row. A missing/stale qmd index is a warning
in the callout and telemetry, not a block. There is still no hard threshold,
auto-merge, or bypass prompt; calibration/enforcement remains #562.

## Proposed mechanism (for when the trigger fires)

Before filing, run a `qmd` similarity check against existing synthesis notes. If the top match exceeds a threshold (start at cosine **0.8**, tune), flag the note and present the candidate neighbours; the human confirms new / merges / overrides — never an automatic block or merge. The gate is owned by the **Linter** (validation discipline) or **Mapper** (it already surfaces neighbouring notes); the decision stays at the human review gate.

```bash
# Ratchet: check the proposed note against existing synthesis notes before filing.
qmd search "{proposed note title or claim}" --scope 30-synthesis --top 3
# If top score > 0.8 -> present neighbours; human confirms new / merges / overrides.
# Requires a current qmd index; run `qmd index --incremental` if stale.
```

## Alternatives considered

**Adopt now.** Rejected: nothing to dedup against on an early vault, and the threshold can't be tuned without real false-positive data.

**Keep only retrospective `find-duplicates` forever.** Rejected: the two are complementary (ratchet at creation, sweep for what slipped through), not redundant; the sweep's painful post-link merges are exactly what the ratchet removes.

**Auto-merge above the threshold.** Rejected: similarity is not identity (two JITAI-receptivity notes can be near-duplicate by keyword, distinct by claim). Merging is a human judgement; the gate only *surfaces* candidates.

## Related

- **Tracking issue:** [#370](https://github.com/eranroseman/memoria-vault/issues/370) — implementation readiness lives on the issue.
- **Pairs with:** [ADR-39 — note-acceptance checklists](39-note-acceptance-checklists.md)
- **Retrospective counterpart:** `find-duplicates` (maintenance cadence)
- **Profiles:** [Linter](../explanation/operations/README.md), [Mapper](../explanation/profiles/librarian.md)
- **Document types gated:** [claim-note, reference-note](../reference/document-types.md)


---

<!-- source: adr/39-note-acceptance-checklists.md -->

# ADR-39: Per-note-type acceptance checklists ("frozen evaluator")

## What

Explicit, per-note-type acceptance criteria the agent checks before filing — the structural definition of a *good* note of each type. For a claim-note, e.g.: "makes a falsifiable claim, supported by >= 1 citekey, title is the claim itself, under 250 words." By analogy to Karpathy's overnight loop, where the unchanging `train.py` evaluator is the constant every experiment is judged against.

## Why

Quality standards are currently implicit and human-judged. Making them explicit and uniform would catch under-supported or mis-shaped notes before they are filed, and pairs naturally with the ratchet gate ([ADR-38](38-pre-file-similarity-gate.md)), which could use the checklist to decide what to flag.

## Trade-offs

- Typing every claim against criteria adds an extraction step.
- Partial adoption (some claims checked, most not) is worse than none — it makes type-aware checks unreliable.
- "Falsifiable claim" is not machine-checkable, so the "evaluator" is partly a prompt for the human, not a hard guard.

## When this matters

The vault holds **50+ `claim-note`s**, so the criteria can be grounded in real examples rather than guessed.


## Alternatives considered

**Adopt now as a mechanical pre-file gate.** Rejected: premature (criteria ungrounded) and partly unenforceable — mechanical enforcement of soft criteria creates friction; non-enforcement makes the checklist decorative.

**Drop the idea entirely.** Rejected: it is a cheap, high-optionality enhancement once grounded, and it composes with the ratchet. Worth accepting as future direction rather than forgetting.

## Related

- **Tracking issue:** [#372](https://github.com/eranroseman/memoria-vault/issues/372) — implementation readiness lives on the issue.
- **Pairs with:** [ADR-38 — ratchet duplicate gate](38-pre-file-similarity-gate.md)
- **Note type concerned:** [claim-note](../reference/document-types.md)
- **Re-entry trigger:** 50+ claim-notes in `notes/claims/`


---

<!-- source: adr/40-admin-gui-surface.md -->

# ADR-40: Admin/forensic GUI surface (`hermes-workspace`)

> **Rejected 2026-06-16.** The forensic need is covered by the CLI and
> dashboards now, with a possible read-only Obsidian Inspector recorded in
> [ADR-58](58-adjacent-tool-integrations.md). An external admin GUI would add a
> second, immature surface with too much write capability for too little benefit.

## What

A web GUI for *administration and forensics* — "what skills are loaded," "what's in this profile's memory," "show the audit log filtered to deny events this week" — to fill the one gap among Memoria's operator surfaces (Obsidian, in-vault dashboards, CLI, Telegram, API). `hermes-workspace` (a Nous Research project; web UI on the Hermes API at `:8642`; chat with SSE, file browser, terminal, memory editor, skills browser, session inspector; PWA, Tailscale-accessible, MIT) addresses exactly that gap.

## Why

The admin/forensic views above are CLI-only today — fine for command-line natives, slow for browsing. There is no GUI for the "what's loaded / in memory / in the audit log" questions.

## Trade-offs

- `hermes-workspace` is v0.1.0, ~9 stars, single contributor — a hackathon project, not a mature product. Documenting it in canonical docs is a stale-doc liability for near-zero benefit while the CLI fills the gap.
- Any such surface risks becoming a second, un-gated place to act on content if scoped wrong.

## Rejection rationale

Memoria will not adopt `hermes-workspace`. It is a broad administrative GUI over
profile memory, files, terminal access, and sessions; even local-only, it expands
the action surface outside the vault's existing policy-gated flows. The durable
need is forensic visibility, not another write-capable workspace.


## Alternatives considered

**Adopt `hermes-workspace` now as an optional documented surface.** Rejected: documenting a v0.1.0 single-contributor tool is a maintenance liability that outweighs the convenience; the CLI already covers the need.

**Adopt it as a primary surface.** Rejected outright: it overlaps Obsidian (file browser, chat) and would create a second, un-gated place to act on content — against the "Obsidian is the content surface; the board holds state; the policy MCP gates writes" architecture.

**Build a Memoria-native admin GUI.** Rejected as scope creep: the forensic need is real but narrow; the CLI + dashboards cover the daily path.

## Related

- **Tracking issue:** [#373](https://github.com/eranroseman/memoria-vault/issues/373) — revisit each release cadence.
- **Existing surfaces:** CLI (forensic), dashboards (state), Telegram (push) — see [Interaction channels](../explanation/architecture/human-channels.md)
- **Invariant protected:** the human review gate (`review_status`) and the [policy MCP](../reference/policy-mcp.md)
- **Adjacent future idea:** the read-only Memoria Inspector Obsidian plugin from
  [Adjacent tool integrations](58-adjacent-tool-integrations.md) covers part of
  the same forensic need from inside Obsidian.


---

<!-- source: adr/41-configurable-review-gate-mode.md -->

# ADR-41: Configurable review-gate mode (blocking / advisory) for comparison studies

> **Naming.** This is **not** [ADR-14](14-advisor-review-vs-frozen-deliverable.md)'s "advisor-review export" (a live-citation `.docx` for a *human academic advisor* in Word). That concerns deliverables. This proposal concerns the *agent review gate* and exists purely as measurement infrastructure.

> **Verified on-box 2026-06-21.** The hard stop is at the write, not the card
> column. There is no on-box code that refuses a board column advance based on
> `review_status`; the guarantee that matters is enforced by the policy decision
> core, where a review-gated path resolves to `dry_run`/block
> (`memoria/runtime/policy/decision.py`). The same wording in ADR-03/77/78 should be
> read this way. The decision stands; only the locus of enforcement is corrected.
> Per AGENTS.md, enforcement is a mechanism, not a label.

## What

A single configurable `review_mode` setting with two values:

- **`blocking`** (default, the only recommended operating mode). Current behavior,
  unchanged: writes into review-gated canonical paths resolve to `dry_run`/block
  until the human approval path performs the promotion.
- **`advisory`** (study-only). The `agent_recommendation` is still written and surfaced but does **not** structurally block — a card may advance/promote without approval. This deliberately removes the safety property.

Three invariants make the mode evidence rather than just a weaker system: (1) the same six-signal instrumentation fires identically in both modes (commensurability is the point); (2) every logged event is stamped with its arm (`review_mode`), set live because the attribution is non-backfillable; (3) the default is `blocking` and advisory must be explicitly, narrowly enabled — per study, time-boxed, ideally within-subject.

## Why

Memoria is designed **blocking-only**, and that is correct as the operating posture ([ADR-03](03-structural-review-gate.md)). But the system's publication thesis — "for knowledge work, structurally blocking human review is the correct commitment" — is a claim of the form "*blocking* beats *advisory*," which is **unfalsifiable without an advisory baseline** measured by the same instrument. No current decision provides a non-gating mode, so the system can measure itself but not against the alternative it claims to beat — the one decision-layer gap between today's design and a completable Path 2/3 study.

## Trade-offs

- **Deliberately downgrades the safety property in the advisory arm** — mitigated structurally by default `blocking`, explicit per-study opt-in, time-boxing, and a clear study scope so advisory can never silently become the standing config.
- **Confound risk:** the operator may behave differently knowing an arm is the "weak" one — mitigated by within-subject design and, where feasible, allocating tasks without foreknowledge.
- **Small implementation cost:** the review-gated write decision becomes
  mode-conditional; one `review_mode` field is added (a `schema_version` bump).
- **Companion metric:** a clean false-promotion-rate measurement also needs a **promotion-reversal event** (distinct from supersession), logged in both arms — small, rides on the same instrumentation.

## When this matters

Committing to the Path 2/3 comparison study. The non-backfillable **attribution sliver already shipped** (alpha.5): the policy audit stamps `review_mode: blocking` and `schema_version: 2` (`policy_mcp.py`). What remains is the `advisory` *behavior* itself — a configurable gate mode — which is not part of the day-1 instrument and is not exercised in ordinary use. Building it is a small deterministic change gated only on wanting the study, not on any missing mechanism.


## Alternatives considered

**Use a generic-LLM-assistant baseline instead of an advisory Memoria variant.** Rejected as the primary baseline: it confounds the gating variable with a different tool, retrieval stack, and UI, so any difference is uninterpretable. Useful only as an optional secondary comparison.

**Build a separate advisory fork / profile set.** Rejected: it duplicates the system, drifts from the blocking config, and — fatally — breaks logger commensurability, the whole reason the comparison is worth running.

**Run Path 2/3 single-arm (blocking only).** Rejected: "blocking beats advisory" cannot be supported by observing the blocking arm alone.

**Stay blocking-only and leave the comparison arm undecided.** Rejected as the standing answer because it leaves the system unable to ever produce the comparative evidence; recorded here so the study-only exception is explicit rather than implicit.

## Related

- **Tracking issue:** [#374](https://github.com/eranroseman/memoria-vault/issues/374) — implementation readiness lives on the issue.
- **Workflows:** [Verify](../how-to-guides/project/verify-and-revise.md), [Promote](../how-to-guides/knowledge/promote-a-claim.md); board dispatch rules ([timeline](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md)).
- **Files:** the card/log schema (`review_mode` field, `schema_version` bump); [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md); the publication-instrumentation track in [Release plan — v0.1.0-alpha.1 — appendix](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md), [ADR-11 vault-eval](11-vault-eval-maintenance.md), [ADR-14](14-advisor-review-vs-frozen-deliverable.md) (distinct "advisor-review").
- **Source discussion:** publication-path analysis — the Path-2/3 advisory-baseline gap.


---

<!-- source: adr/42-profile-compilation.md -->

# ADR-42: Profile compilation from a shared base

The seven SOUL.md files are hand-authored and hand-maintained. This proposal describes a build step that would generate the shared sections from a common base, reducing inter-profile drift.

## What

A compile step that generates each profile's SOUL.md by combining:
- A shared base (common audit-log behavior, common policy invariants, common MCP connections)
- A per-profile override block (unique mission, commands, permissions)

The compiler outputs the seven SOUL.md files into the starter vault; no hand-authoring of shared sections.

## Why

The current approach copies shared content (e.g., the audit-log behavior specification) into seven separate SOUL.md files that must be kept in lockstep by hand. When shared behavior changes, seven files need updating — and the retired `profile-install-drift` idea ([ADR-67](67-drift-procedures-keep-or-retire.md)) only ever addressed the *deployment* copy drifting from the *source* copy, not the seven *sources* drifting from each other.

## Trade-offs

A compiler adds a build step and a source-to-output relationship that must be maintained. Debugging requires understanding which sections are compiled vs. hand-authored. The gains are proportional to how much content is actually shared across profiles — if profiles diverge significantly, the compiler buys little.

## When this matters

Inter-profile drift (the seven SOUL.md files disagreeing on shared behavior) becomes a recurring maintenance problem — not a theoretical one. The trigger is at least two instances of a shared-behavior change being applied to some profiles but not others, causing a real bug.


## Alternatives considered

**Keep hand-authoring (the current state).** The standing answer: at seven-profile scale the shared content is small enough to keep in lockstep by hand, and the idempotent installer re-run keeps the source→deployment copy synchronized (the `profile-install-drift` check is retired, [ADR-67](67-drift-procedures-keep-or-retire.md)). Held until inter-profile drift is a felt, recurring bug.

**A lighter include/partial mechanism instead of a full compiler.** A possible middle path (shared blocks pulled in by reference rather than generated). Defer the build-step-vs-include choice until a concrete first drift incident shows which shape the shared content actually wants.

## Related

- **Decision:** [ADR-26 repo-as-install-unit](26-repo-as-install-unit.md) — records hand-authored profiles as the current state and this proposal as the deferred compiler.
- **Linter detector:** `profile-install-drift` — retired ([ADR-67](67-drift-procedures-keep-or-retire.md)); the idempotent installer re-run owns source-vs-deployed sync (and never addressed source-vs-source).
- **Files:** the seven `.memoria/profiles/memoria-<name>/SOUL.md`.


---

<!-- source: adr/43-skill-governance.md -->

# ADR-43: Skill governance and lifecycle

## Context

Adding a skill is a runtime operation: edit `policy.allow.skills` in a lane-override
file and drop the `SKILL.md` into the right profile's `skills/` folder. At low skill
count that is sufficient — the bookkeeping fits in the human's head. This ADR was
deferred until the count stopped fitting; at v0.1.0-alpha.2 the vault shipped **25
skills across five profiles** (threshold: > 15), and the open question became which of
two shapes to stand up:

- **Dashboard-only** — a `skill-state` dashboard giving visibility into which
  skills are active in which lane, with no new process.
- **Full lifecycle** — a state machine (`intake → proposed → scaffolded → testing →
  needs-review → approved → active → archived`), per-skill governance notes in
  `system/skills/`, and a 7-step onboarding checklist for new skills.

The deferral itself named the discriminator: confusion about *what's active* wants the
dashboard; uncontrolled *graduations* want the state machine.

## Decision

**Dashboard-only.** The `skill-state` dashboard ships in
`system/dashboards/skill-state.md`: a Dataview view that reads the runtime
governance layer directly (`.memoria/lane-overrides/*.yaml` and
`.memoria/profiles/*/skills/*/SKILL.md`) and renders, per lane, the allowed and denied
runtime skills, the shipped `SKILL.md` folders, and a consistency-check table that
surfaces any disagreement between lane policy and shipped skills.

**The lifecycle half is not adopted.** No state machine, no per-skill governance notes
in `system/skills/` (the folder is not created — the placeholder is retired), no
onboarding checklist. The signal that fired was skill *count*, and what count breaks is
*visibility*, which the dashboard restores. The lifecycle machinery answers a different
problem — coordinating graduations and approvals — that has not occurred (zero
passthrough-to-dedicated graduations to date) and that the single-researcher scope
([ADR-24](24-single-researcher-scope.md)) makes structurally unlikely: with one human
approver there is no hand-off an `intake → … → approved` pipeline would mediate, and
retroactive governance notes for 25 skills plus a checklist per new skill is pure
process overhead. Should graduation churn actually materialize, this half can be
revisited as a new proposal.

**The runtime mechanism is the system of record.** Lane-override files
(`policy.allow.skills` / `policy.deny.skills`) plus the per-profile `skills/` folders
*are* skill governance; the dashboard renders them at view time and therefore cannot
drift from them. Adding a skill remains a runtime operation, exactly as before.

## Consequences

- "Which skills are active in which lane?" has a one-glance answer that is always
  current — the dashboard reads the live files, not a generated snapshot.
- Mismatches (a skill relying on a runtime gate its lane denies, frontmatter
  contradicting the shipping profile, duplicate `skill_id`s) surface as dashboard rows
  instead of being discovered mid-run.
- Adding a skill stays friction-free: no checklist, no governance note, no state to
  advance. The cost is that skill *history* (why a skill was added or retired) lives
  only in git, which is acceptable at n=1 operator.
- `system/skills/` is never created; the on-disk layout is unchanged.
- The shape of the two file formats the dashboard parses is pinned by tests
  (`tests/test_skill_state_dashboard.py`), so a lane-override or `SKILL.md`
  restructuring fails CI rather than silently blanking the dashboard.

## Alternatives considered

**Full lifecycle (state machine + `system/skills/` notes + onboarding checklist).**
Rejected for now, per above: it solves a coordination problem a single-researcher
system doesn't have, at the cost of retroactive authoring for every existing skill and
standing friction on every new one. Not silently dropped — explicitly not adopted;
re-proposable if graduation churn appears.

**Keep the runtime mechanism alone (do nothing).** The pre-trigger state. Rejected:
at 25 skills the "what's active where?" question genuinely stopped being answerable
from memory, and answering it by opening ten YAML files is exactly the bookkeeping
failure the deferral predicted.

**A generated report instead of a live dashboard.** A cron script writing a markdown
snapshot would add a generator, a cadence, and a staleness window for no benefit — the
source files are small and local, so the view layer can read them directly
([ADR-49](49-catalog-in-bases-linter-monitor.md): dashboards are views, never a second
store).

## Related

- **Tracking issue:** [#368](https://github.com/eranroseman/memoria-vault/issues/368) — the trigger firing and the shape decision.
- **System of record:** lane-override files (`policy.allow.skills`) + per-profile `skills/` folders.
- **The dashboard:** `system/dashboards/skill-state.md`; rationale in [skill-state dashboard](../explanation/dashboards/operational-health/skill-state.md).
- **Scope premise:** [ADR-24](24-single-researcher-scope.md) — single researcher; one judgment owner.


---

<!-- source: adr/44-tests-in-pytest-tree.md -->

# ADR-44: L1 component tests live in a repo-side pytest tree

## Context

[ADR-29](29-testing-framework.md) chose to host L1 component tests as inline
`python <module> --self-test` blocks inside each module. The stated rationale was
that the `vault/.memoria/` modules are a *distributed* artifact (the installer copies
them to user machines), so inline tests could **self-verify in situ**.

On review, that justification does not hold: nothing runs `--self-test` on a deployed
vault — not the installer, not any runtime or troubleshooting path. The tests ship to
user machines purely as a side effect of being inline, and are never exercised there.
The two things a post-install check would actually want are better served otherwise —
**corruption** by a checksum (the golden copy already carries a SHA-256 manifest, and
`golden_restore.py check` flags any drifted system file), and **environment** (wrong Python, missing deps) by the
installer's existing `pip install` plus a one-line import check. Neither needs the unit
tests to ship. Meanwhile the inline blocks bloat the modules, ship dead code to users,
and reinvent a test runner (`scripts/test.sh`'s hand-rolled `check()`).

## Decision

L1 component tests move to a conventional **repo-side `tests/` pytest tree** and are
**removed from the modules**. Each former `_self_test()` becomes `tests/test_<name>.py`;
the repo-root `pyproject.toml` declares pytest `pythonpath` for the loose runtime
module directories and repo tooling scripts. `python-selftest.yml`,
`scripts/test.sh`, and the pre-commit hook run `pytest`. The deployed vault carries **zero test code**.

This **amends ADR-29's L1 implementation only** — the pyramid (L0–L5), the coverage
matrix, drift control, and gate mapping are unchanged. The installer-side **checksum +
import smoke check** is the right home for in-situ verification and is **deferred to
alpha.2**, when the installer is being reworked anyway.

## Consequences

- Test code stops shipping in `vault/.memoria/`; modules shrink to production code.
- `pytest` becomes a dev/CI dependency (it is **not** added to the vault runtime
  `requirements.txt` — the shipped runtime stays dependency-light).
- Standard tooling is available: `pytest -k`, assertion introspection, and
  `coverage.py` can now measure the matrix instead of asserting it by hand.
- The current loose-module import roots live in `pyproject.toml`; the full ADR-76
  wheel migration later replaces those `pythonpath` entries with one installed
  package root.
- Until the alpha.2 installer work lands, a deployed install has **no** post-install
  self-check. This is the status quo (it never had one) — not a regression.

## Alternatives considered

**Keep inline self-tests (ADR-29 as written).** Rejected: the in-situ justification is
unrealized, and the cost (shipped dead code, bloated modules, a bespoke runner) is real.

**Thin pytest wrapper that subprocess-invokes the existing `--self-test`.** Rejected:
the test code would still live in — and ship with — the modules; it only adds a runner.

**Split by ship-boundary (pytest for `scripts/`, inline for `vault/`).** Rejected as the
end state: it keeps two mechanisms. A single tree is simpler, and the in-situ need is
met by the deferred installer checksum/import check instead.


---

<!-- source: adr/45-release-management-model.md -->

# ADR-45: Release management — gates as a tracking-issue checklist, release-please for versioning

## Context

Releases were managed with a **self-contained plan file** per version: one
`release-plan-vX.Y.md` carrying a frontmatter `released:` flag, hand-maintained §2
Gate (`G1–G11`) and §3 Stage (`S0–S5`) state tables, scope, cut procedure, and roadmap,
plus sibling run records — scope in the GitHub milestone, notes in `CHANGELOG.md`, and a
`v*` tag triggering `release.yml`. It was git-tracked, reviewable in PRs, self-contained,
and offline-capable. But it hurt in three observed ways: the hand-maintained markdown
state tables **drifted** (the template itself wished for a future `status-doctor` check;
the release scaffolding guidance and the v0.1 plan accumulated stale path/term references); there was
**no live status surface** (you read a file to know where a release stood); and it took
~8 files per release with two places to keep aligned (plan gates ↔ milestone/issues).

## Decision

Adopt a **tiered, additive** model — stop anywhere, escalate later without rework. **Tier
1 (fix the drift + add `status-doctor`) and Tier 2 are adopted; Tier 3 is deferred.**

- **Readiness state** lives in the **"Release vX.Y" tracking issue** — a gate checklist
  GitHub renders as a progress bar — retiring the hand-maintained §2/§3 markdown tables
  (the main drift source). *(Tracking shape amended by
  [ADR-75: Use GitHub Project fields and release sub-issues for live work
  state](75-github-project-fields-and-release-sub-issues.md): the single-checklist
  tracking issue is replaced by a parent issue plus one sub-issue per gate; the
  milestone-for-scope and release-please-for-versioning decisions here stand.)*
- **Scope** is the GitHub **milestone** (`vX.Y`).
- **Version + CHANGELOG + GitHub Release** are owned by **release-please** (manifest mode)
  from Conventional Commits, replacing the tag-only `release.yml`. Don't hand-edit
  `CHANGELOG.md` or tag by hand.
- **Prose** (scope summary, cut procedure, known-limitations) stays in
  `docs/releasing/<version>/`, guarded by `status-doctor` against link/path/flag drift.
- The in-flight **alpha.1** plan keeps its §2/§3 tables as the at-cut record (with a pointer
  to its tracking issue); **alpha.2+** uses the checklist model from the start.

The live process this produced is documented in [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md) and
scaffolded by the release playbook at `.agents/playbooks/release.md`.

> **Status note (2026-06-21).** release-please is configured in manifest mode but
> intentionally paused for pre-alpha: `.github/workflows/release-please.yml` is
> `workflow_dispatch`-only and the manifest remains `0.0.0`. Until the first formal
> tagged release, internal checkpoints use the release plan plus GitHub gate/stage
> issues; release-please does not yet auto-open version PRs.

## Consequences

- Live status for free (progress bar + milestone %); the hand-table drift source is gone.
- The record **splits**: prose in git, gate/stage state in GitHub — offline gate-state
  visibility is lost (an accepted trade at solo cadence).
- release-please is opinionated and now owns versioning/notes; merging its "Release vX.Y"
  PR cuts the tag. (Operational caveat: its PR needs Actions PR-review permission / a
  scoped `RELEASE_PLEASE_TOKEN` — tracked separately.)
- The release **cut** now includes an ADR retire-sweep (see [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md)).

## Alternatives considered

The gate/stage *vocabulary* comes from the layered testing framework ([ADR-29](29-testing-framework.md));
this decision is only about *where release state and versioning live*.

- **Stay file-folders + add `status-doctor`** (Tier 1 alone). Lowest effort, kills the
  drift, stays in git — but adds no live surface and the gate state stays hand-edited
  markdown. Kept as the floor; Tier 2 is layered on top.
- **GitHub-native gates** (chosen, Tier 2). Gates as a tracking-issue checklist + milestone
  for scope: live status for free, no markdown state tables. Cost: state leaves git
  (GitHub-only), offline visibility lost — acceptable for one operator.
- **VS Code GitHub extension.** Rejected as the system of record — it's a viewer/UI over
  whichever model you pick, never the model itself.
- **release-please** (chosen for the notes/versioning half). Automates version + CHANGELOG +
  Release PR once unpaused for formal releases; opinionated, replaces `release.yml`. It automates only versioning/notes, **not
  readiness** — which is why it pairs with the tracking-issue gates rather than replacing them.
- **Tier 3 — Projects "Release" view + `scripts/release.sh` cut script.** Deferred: richest
  dashboard and a one-command cut, but the Projects field/view config isn't in git, it's the
  most moving parts, and the dashboard is marginal at solo cadence. Revisit if cadence rises;
  the cut **script** (the higher-value half) can be pulled in standalone.

## Related

- **Live process:** [Releasing](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/README.md); `.agents/playbooks/release.md` scaffolds it.
- **Gate/stage model:** [ADR-29](29-testing-framework.md) (the layers/matrix the gates map to).
- **Amended by:** [ADR-75: Use GitHub Project fields and release sub-issues for live
  work state](75-github-project-fields-and-release-sub-issues.md) — replaces the
  single-checklist tracking shape with a parent issue plus one sub-issue per gate.


---

<!-- source: adr/46-seven-layer-architecture.md -->

# ADR-46: Seven-layer architecture — PI · Interface · Co-PI · Tasks · MCP · Engines · Vault

> **Vocabulary amended (2026-06-14, [ADR-69: Operations — name the deterministic
> layer and its four categories](69-operations-layer-naming.md)).** The layer this ADR
> calls **Engines** is now named **Operations** (the synonym "app" is retired too).
> ADR-69 governs the vocabulary; this ADR keeps the architecture.

> **Verified on-box 2026-06-21 (mechanism note).** "agents reach engines and the Vault
> only through [MCP]" (Decision, below) is bound by the **gate's deny rules** —
> `policy_hook.DENY_DIRECT_TOOLS` hard-denies `file`/`terminal`/`code_execution` and the
> decision core default-denies unknown tools at dispatch (the [ADR-28](28-write-gate-as-plugin.md)
> mechanism; profile toolsets are schema/capability shaping only). The strict
> layer-dependency contract *describes* the agent write-path; the gate is what stops a
> direct write. Per AGENTS.md "Enforcement is a mechanism, not a label."

## Context

ADR-01's three layers (board, workers, vault) described the v0.1.0-alpha.1 infrastructure but
conflated two distinctions the design update pulled apart: *where* things live
(structure) and *who* acts (actor-kind). The design work
converged on a single model that serves as both the cognitive and the build view, with
the MCP trust boundary made explicit. An adversarial review then scoped its layering claim
honestly.

## Decision

Memoria is **seven layers** — **PI** (the human; the only actor who promotes to
canonical) · **Interface** (the Obsidian UI: Home, dashboards, Inbox, the
Library/Project Workspaces, command palette) · **Co-PI** (the permanent conversational
agent in the ACP pane) · **Tasks** (ephemeral profiles + the kanban board + cards) ·
**MCP** (the policy/sandbox boundary) · **Engines** (the deterministic apps: ingest,
search, clustering, verification sweeps, Linter) · **Vault** (the files and folders).

Three **actor-kinds** act across the structural layers: the PI (human judgment),
**agents** (posture + LLM — the Co-PI and the Task lanes), and **engines**
(deterministic, no posture). One flow rule: **decisions flow down, information flows
up.** The strict each-layer-depends-only-on-the-one-below contract binds the **agent
write-path** (Co-PI → Tasks → MCP → Engines/Vault); the PI and trusted automation
(cron, CI) are *direct edges* — the PI edits the Vault in Obsidian, and cron/CI/the PI
invoke engines directly. **MCP is a policy gate, not an execution sandbox**: agents
reach engines and the Vault only through it; first-party agents get no process
isolation (sufficient under the solo/local premise).

## Consequences

- The "is it an agent or an engine?" question is decided by posture + LLM judgment,
  not by invocation style; deterministic work never occupies a board lane.
- The MCP boundary is where allow-listing, write-scoping, and audit live; adding an
  engine means deciding whether it needs an MCP facade (agent-reachable) or not
  (cron/CI-only).
- "Completely sandboxed" is over-claiming: the honest phrase is *policy-sandboxed via
  MCP*; execution isolation is deferred until untrusted third-party code is run.
- Docs and diagrams describe one model at two zoom levels (three actors over the
  substrate; seven layers in the build view), never two competing models.

## Alternatives considered

**Keep the three-layer model.** It hid the Co-PI/Tasks split and the MCP boundary —
the two things v0.1.0-alpha.2 builds against. **Two separate models (cognitive + build) with a
mapping table.** A 1:1 mapping was the smell that they were redundant; one
good-enough model beats two perfect ones (D42). **Strict layering for every actor.**
False in practice — the PI edits the Vault directly; claiming otherwise misleads
(red-team contradiction 3).

## Related

- **Resolves / supersedes:** [ADR-01](01-three-layer-architecture.md)
- **Related decisions / Depends on:** [ADR-22](22-build-on-hermes-runtime.md),
  [ADR-48](48-copi-and-agent-consolidation.md)


---

<!-- source: adr/47-type-first-category-folders.md -->

# ADR-47: Type-first category folders — catalog · notes · projects · inbox · system

## Context

ADR-04 encoded lifecycle stage in numbered folders (`10-inbox/ … 50-deliverables/`),
which implied a pipeline. The design update (D2/D24) found the knowledge is a
**network**, not a pipeline: direction belongs in a *state property*, and the real
structural distinction is the entity/note/artifact/signal split.

## Decision

The vault's top level is organized by **category**, one content kind per folder, no
lifecycle numbers:

```text
catalog/    structured entity records (Obsidian Bases) — papers, people,
            organizations, venues, datasets, repositories
notes/      prose (Zettelkasten) — fleeting/ · source/ · claims/ 🔒 · hubs/ 🔒 · index/
projects/   work artifacts, project-scoped — Project gate notes, drafts, code, exports
inbox/      agent→human messages (the kanban board and queue dashboards are views of it)
system/     visible infrastructure — logs · templates · patterns · dashboards
.memoria/   hidden runtime (MCP, profiles, schemas, golden copy)
.obsidian/  hidden Obsidian app config (Bases definitions, layouts, graph groups)
```

**One folder never mixes two categories.** Folders are named for their *content*, not
for a doer. Lifecycle direction lives in the `lifecycle` state property
([ADR-50](50-universal-lifecycle-and-maturity.md)); `archived` is a state, not a
folder — notes stay in their type-home and drop from active views.

## Consequences

- Moving a note between folders is no longer a state transition; state changes are
  frontmatter edits, preserving links and provenance.
- The type → folder-home map is machine-read (`.memoria/schemas/folders.yaml`) and is
  the single source for the Linter, the policy gate, the installer skeleton, and tests.
- The old `90-assets/` and `95-archive/` folders disappear (derived artifacts are
  hidden runtime data; archived notes stay put).
- ZK-faithfulness improves: Zettelkasten has no folder ordering; topic stays out of
  folders (in frontmatter facets).

## Alternatives considered

**Keep lifecycle-numbered folders.** Implies a pipeline and makes every promotion a
file move that breaks links. **Topic folders.** Rejected since ADR-04 for the same
reasons it was rejected there — topics are facets, not locations.

## Related

- **Resolves / supersedes:** [ADR-04](04-lifecycle-over-topic-folders.md)
- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-49](49-catalog-in-bases-linter-monitor.md)


---

<!-- source: adr/48-copi-and-agent-consolidation.md -->

# ADR-48: One Co-PI fronts everything; specialists consolidate to posture-defined agents

## Context

ADR-02's seven specialist profiles created a real UX failure — "who do I talk to?" —
and fragmented the learning loop across agents that never conversed. Under
"profile = posture, skills attach per lane" several profiles shared one stance. The
design update (D26/D27/D34/D38/D46) consolidated by posture and concentrated
conversation in a single front.

## Decision

The PI converses with **one agent — the Co-PI** — and **delegates** everything else.
The Co-PI is the permanent agent in the ACP pane: reflective thinking-partner posture
(it subsumes the old Socratic role), **read-only** (it runs read-only skills directly;
every write goes out as a delegated task card), and the sole carrier of Hermes'
self-improving loop (**memory · /goals · skills**); **`/personality` is a Co-PI-only
affordance** — specialist postures are fixed by design.

The background agents are role-named, posture-defined lanes: **Librarian** (*faithful*;
the four processing lanes catalog · extract · link · map — the old Librarian + Analyst),
**Writer** (*generative, draft-only*), **Peer-reviewer** (*skeptical, deliberately
independent* — never merged with the Librarian; separation of duties), **Engineer**
(*delegating*). Deterministic work is **engines, not agents**
([ADR-46](46-seven-layer-architecture.md)): the Linter and the verification sweeps left
the profile set. Each agent = a shared layer (the vault `AGENTS.md`) + a unique layer
(`SOUL.md`, `skills/`, `config.yaml`, MCP wiring).

**v0.1.0-alpha.2 ships all five profiles** (the original plan shipped only Co-PI + Librarian,
with the rest deferred to v0.1.0-alpha.3; the PI expanded the scope mid-build — 2026-06-09 — so
Writer, Peer-reviewer, and Engineer landed in v0.1.0-alpha.2 as well; their *Project-workspace
workflows* still arrive with v0.1.0-alpha.3).

## Consequences

- One conversational context compounds (memory/goals/skills) instead of seven that
  reset; background lanes stay stateless propose-then-dispose executors.
- The board's lanes shrink to the background agents; there is no Co-PI lane and no
  engine lane.
- Drafting and verification interrogation are conversational but currently routed
  through one-shot cards — the open "conversational specialist work" question
  (red-team theme C) is deliberately unresolved; a routing agent is rejected.
- The old profile names (Mapper, Socratic, Verifier, Coder) disappear from the
  installed set; their useful skills migrate into the consolidated lanes.

## Alternatives considered

**Keep seven specialists.** Artificial handoffs between profiles sharing one posture,
and the "who do I talk to?" confusion. **Co-PI plus directly-conversable specialists.**
Reintroduces the confusion and splits the learning loop; revisit only if a specialist
conversation proves necessary. **Merging verification into the Librarian.** Breaks
separation of duties — the agent that synthesizes must not grade its own work.

## Related

- **Resolves / supersedes:** [ADR-02](02-seven-specialist-profiles.md)
- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md),
  [ADR-21](21-l3-autonomy-ceiling.md), [ADR-23](23-scoped-memory-substrates.md)


---

<!-- source: adr/49-catalog-in-bases-linter-monitor.md -->

# ADR-49: Catalog entities live in Obsidian Bases; the Linter is the integrity monitor and commit gate

## Context

The old `paper-note`/`item-note` types were entity-note hybrids — a standing tension
between structured bibliographic facts and interpretive prose. The design update (D3)
split them: **entities** are structured records, **source notes** are prose. Bases —
Obsidian's native database views over frontmatter — fit the plain-text/git/lintable
discipline, but provide **no integrity guarantees** (no schema, no constraints). The
red-team pass and D50 settled how integrity is actually supplied.

## Decision

Catalog entities (paper, person, organization, venue, dataset, repository) are
markdown records under `catalog/` with **flat, Bases-queryable frontmatter**, surfaced
through **Obsidian Bases** views. Bases are the *view layer*; the records are the
source of truth; nothing reads a Base as data.

The **Linter engine is the integrity monitor and the commit gate**: a **pre-commit
`schema-check`** gates git-tracked writes at commit (D50), and the cron/CI sweep
monitors between commits — it validates every record against its type schema
(required fields, value types, enum vocabularies, `links:`/`relationships` resolve to
real targets, keyed off the `type:` discriminator) and flags drift as Inbox `flag`s.
The Linter is honestly a *monitor* for live in-app edits (it detects, it does not
block); a file-watcher daemon is deliberately not built. Type schemas live in one
canonical home — **`.memoria/schemas/`** — read by the Linter, the policy gate, the
installer, and the tests.

## Consequences

- Entity data stays git-diffable plain text; a broken Base view loses nothing.
- Every schema change is one YAML edit in `.memoria/schemas/`, picked up by all
  consumers — no scattered hardcoded field lists.
- Between a bad live edit and the next sweep, a Base can briefly serve a malformed
  record; this window is accepted (solo premise) and bounded by the commit gate.
- Bases is a young format: `.base` views are tested against the schemas in CI so our
  side cannot silently drift.

## Alternatives considered

**SQLite / JSON / a graph DB as the store.** Opaque, not git-diffable, outside the
plain-text discipline; a derived index is fine at scale but never the source of truth.
**Keeping the hybrid paper-note.** The tension this splits was a recurring source of
schema drift. **A file-watcher write gate.** A daemon the engine model avoids; the
commit gate + sweep bound the risk acceptably.

## Related

- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md), [ADR-12](12-obsidian-linter-reference-only.md)


---

<!-- source: adr/50-universal-lifecycle-and-maturity.md -->

# ADR-50: One lifecycle chain for everything; maturity is a claim property; reference dropped; MOC renamed hub

## Context

v0.1.0-alpha.1 carried several state vocabularies side by side (note lifecycle values, board
states, a settled-claim note type), and "reference note" collided with the
Zettelkasten term for a literature note. The design update (D4/D5/D19/D24) unified
them.

## Decision

Everything the PI sees uses **one lifecycle chain**:

```text
proposed → provisional → current → retracted → archived
```

Each type uses a *subset* (the per-type subsets live in `.memoria/schemas/types/`).
`archived` is a **state, not a folder**. Inbox cards use this same chain (a card
awaiting you is `proposed`); the Hermes-native execution `status` stays a hidden
mechanic, never shown to the PI.

Two **soft 3-tier judgment signals** ride alongside, neither a gate nor a state:
**maturity** (`seedling → budding → evergreen`) — how *developed* a claim is, PI-set —
and **agent-recommendation** (`inconclusive → issues-found → clean`) — a verdict on a
check, agent-set. A `seedling` claim is fully `current`; a `clean` recommendation never
substitutes for human approval, and nothing auto-promotes at `evergreen`.

The **`reference` note type is dropped** (an `evergreen` claim is the settled unit;
"reference note" double-encoded maturity and collided with ZK vocabulary). **MOC is
renamed `hub`** (amends [ADR-19](19-moc-threshold-alert.md) — the threshold-alert
mechanism survives under the new name).

## Consequences

- One state vocabulary to learn; "how trusted?" (lifecycle) and "how developed?"
  (maturity) are visibly different axes with distinct value sets.
- State transitions are frontmatter edits — no file moves, links survive.
- Queries that filter on `lifecycle` must scope by category (card-state vs note-state
  share the vocabulary; folder scope keeps them disjoint).
- Existing `reference`-type material becomes evergreen claims or source notes.

## Alternatives considered

**Per-type state vocabularies.** More precise, but multiplies the mental model for one
user; subsets of one chain capture the same constraints. **Maturity as a lifecycle
axis.** It gates nothing and varies only on claims — a property, not a state.
**Keeping `reference`.** Collides with ZK's reference note (= our `source`) and adds a
type where a property suffices.

## Related

- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-18](18-rename-agent-verdict.md), [ADR-10](10-claim-supersession.md); amends
  [ADR-19](19-moc-threshold-alert.md)


---

<!-- source: adr/51-inbox-category-and-honesty-card.md -->

# ADR-51: The Inbox category and the honesty card — argument for/against, what tipped it, certainty; no verdict on proposals

## Context

Agent→human signals were scattered (candidate notes in a folder, board cards, dashboard
rows), and the card format begged the automation-bias question: research shows handing
a human a confident verdict *reduces* scrutiny, and for a proposal the verdict is a
**given** — the agent surfaced the item because it recommends it. The design update
(D6/D18/D35/D37/D49) made the signal end of the loop first-class and made honesty the
card's guardrail.

## Decision

**`inbox/` is the agent→human message category.** Four message card types — **candidate** (a
*found* source proposed for intake), **gap** (a *missing*-source need), **flag** (a
verification/integrity issue), **alert** (drift/retraction) — plus the aggregate
**work-prompt** (below), for **five** Inbox card types in all — on the universal
lifecycle chain (`proposed` = awaiting you; there is no `review-request` type). The
kanban board and the queue dashboards are *views* of the Inbox (one Base grouped by
type).

**Proposal cards carry an honest argument, not a verdict**: **Action** (what you'd be
accepting) · **Argument for** · **Argument against** (the agent's strongest
self-rebuttal) · **What tipped it** (the deciding reason) · **Certainty** (3-level,
action-labelled). No verdict line — it is implied by the card existing.
**Verification/adjudication items keep their verdict** (`clean` / `issues-found` /
`inconclusive`; near-tie same/different/unsure) and lead with the finding.

**High-cardinality decisions never become N cards** — a report that needs dozens of
keep/reject calls is a Bases-backed **batch worklist** and surfaces **one aggregate
work-prompt** in the Inbox.

## Consequences

- "An Inbox item the PI can clear without reading is a design smell" gets structural
  backing: the against-case and certainty are the information-bearing fields.
- Card templates render the honesty body; the schema for each card type lives in
  `.memoria/schemas/types/` like any other type.
- Engines and lanes share one card-writer so every `flag`/`alert`/`candidate` is
  shaped identically.
- Supersedes the candidate-note routing from
  [ADR-17](17-shared-candidate-frontmatter.md): `candidate` becomes an Inbox
  type; the shared-frontmatter intent survives inside the card schema.

## Alternatives considered

**Ship the verdict on every card.** Vacuous for proposals and induces automation bias.
**Blind-first (hide the verdict until the PI leans).** There is no verdict to hide on
a proposal; for verification items the finding *is* the payload. **One card per item in
batch screening.** Floods a queue meant to converge to zero and invites
select-all-accept.

## Related

- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-03](03-structural-review-gate.md); supersedes
  [ADR-17](17-shared-candidate-frontmatter.md) and
  [ADR-36](36-dedicated-review-note-type.md) (a card in `proposed` is the review
  surface, so a dedicated review note type is no longer needed)


---

<!-- source: adr/52-links-vs-relationships.md -->

# ADR-52: Notes carry authored links:, entities carry given relationships — two kinds of connection

## Context

ADR-08's single `relations:` field conflated two different things: *objective facts
about sources* (paper cited-by paper, authored-by person, published-in venue) and
*connections the PI draws* (claim supports/contradicts claim). They differ in nature,
owner, and gating — and `relations`/`relationships` were a near-synonym clash waiting
to happen (D17).

## Decision

Two distinct connection kinds, two distinct fields:

| | **`relationships`** (Catalog entities) | **`links:`** (Notes) |
|---|---|---|
| nature | **given** — objective facts | **authored** — connections the PI draws |
| examples | cited-by, authored-by, published-in, DOI→ORCID | supports, contradicts, hub membership |
| built by | the **ingest engine**, mechanically | agent **proposes**, **PI confirms** |
| gated? | no — facts (low-confidence extraction → `flag`, [ADR-56](56-extraction-uncertainty-flag.md)) | yes — the *link* gate |

"Relationships are given; links are authored." `links:` replaces the old `relations:`
field; typed edges (`supports`, `contradicts`) keep ADR-08's typed-relations intent and
keep feeding the contradictions dashboard ([ADR-09](09-contradictions-dashboard.md))
and claim supersession ([ADR-10](10-claim-supersession.md)).

## Consequences

- The link-confirmation gate applies only where judgment lives; mechanical facts flow
  ungated (with the uncertainty escape valve).
- The graph has two typed layers — a citation/identity graph over entities and an
  argument graph over notes — which is what makes typed graph projections possible.
- A connection between two *entities* is always a relationship; `links:` endpoints are
  notes. The schema files encode this so the Linter can reject category errors.
- One-time field rename `relations:` → `links:` in templates, schemas, and dashboards.

## Alternatives considered

**One field for both.** Conflates given and authored, and forces one gating rule onto
two different trust models. **`references`/`connections` naming.** "Reference" was
already retired as a note type and is citation-narrow; links/relationships matched the
words the PI would say.

## Related

- **Resolves / supersedes:** [ADR-08](08-typed-relations-frontmatter.md)
- **Related decisions / Depends on:** [ADR-09](09-contradictions-dashboard.md),
  [ADR-10](10-claim-supersession.md), [ADR-49](49-catalog-in-bases-linter-monitor.md)


---

<!-- source: adr/53-pattern-library.md -->

# ADR-53: The pattern library — curated prompt-transformations as data in system/patterns/, one runner

## Context

fabric "patterns" and open-notebook "transformations" showed that reusable,
single-purpose prompt-transformations are most of what assist skills do — but
importing those tools wholesale would put ungated LLM calls outside the policy MCP and
adopt a chat-with-docs epistemic model Memoria exists to prevent (D11; folds
[ADR-43](43-skill-governance.md)'s governance intent).

## Decision

Memoria ships a **pattern library**: curated prompt-transformations stored **as
markdown in `system/patterns/`** (visible, git-tracked, lintable — *not* `.memoria/`).
**Patterns are data; one runner executes them all** — "using a pattern" = the runner +
a pattern id; patterns are never individual skills. Each pattern's frontmatter declares
its **posture/agent, mode (Library/Project), action type, input, and `output_target`**;
a shared `_preamble.md` enforces the Memoria voice (your-words, concise,
propose-never-assert, cite-don't-fabricate).

Enforced constraints: a pattern **never writes a gated zone** (output goes to staging,
else the run degrades to dry-run and lint fails); propose-not-dispose; the Linter
validates pattern files against the pattern schema; runs are versioned and
reproducible with per-run provenance. Patterns are themselves gated assets
(human-authored, or agent-proposed → human-approved). The library is seeded by
*adapting* fabric patterns, retargeted to staging. Runner: an in-vault MCP; invocation
via palette · pane · selection; model: per-pattern hint with a global fallback.

## Consequences

- New assist behavior is usually a new markdown file, not new code.
- The runner is one audited chokepoint for every pattern execution (provenance,
  output-target enforcement).
- The pattern-picker is a Base over the library, filtered by current mode/task.
- Curation is a real ongoing duty — a bad pattern is a gated asset to fix, not a prompt
  buried in code.

## Alternatives considered

**Adopt fabric as a dependency.** Its value is the pattern *idea*, not the pipe-CLI;
as a dependency it bypasses the policy MCP. **One skill per pattern.** Explodes the
skill registry and makes governance per-skill instead of per-data-file.
**Chat-with-docs transformations.** The "synthesis without rigor" failure mode; rejected
on epistemics.

## Related

- **Related decisions / Depends on:** [ADR-03](03-structural-review-gate.md),
  [ADR-43](43-skill-governance.md), [ADR-51](51-inbox-category-and-honesty-card.md)


---

<!-- source: adr/54-two-decision-kinds-batch-worklists.md -->

# ADR-54: Two kinds of human decision — approval gates and work prompts; classify automated; batch worklists for high cardinality

## Context

Reviewing every human touchpoint with one question — *could the PI clear this without
reading it?* — exposed that the gates were not one kind of thing: some review agent
output, some prompt the PI's own thinking, and one (classify) was a rubber-stamp
pretending to be a gate (D21/D37; reinforces [ADR-03](03-structural-review-gate.md)
and the no-auto-accept rule).

## Decision

Every place the PI acts is one of **two kinds**, and each gets a different Inbox item:

The worklist shape is aggregate-first: a fleeting note plus one batch card that
summarizes the work, not one toggle or one Bases row per candidate item.

- **Approval gate** — the PI reviews *agent-produced output* and accepts/rejects. The
  item must carry the honesty card ([ADR-51](51-inbox-category-and-honesty-card.md)) —
  never a bare "OK?".
- **Work prompt** — the agent signals it is *time for the PI's own thinking/writing*;
  a rich nudge with the material to start, not an approval.

**The rule:** *an Inbox item a human can clear without reading is a design smell* —
give it real decision material, or automate it. **classify fails this test and is
automated** (audited, correctable; a `flag` fires only on genuine ambiguity) — the real
Read-side gates are candidate triage (keep/skip) and link confirmation.
**High-cardinality per-item decisions live in a batch worklist** — a Bases-backed
screening surface where each file-backed `worklist-item` row carries a `decision`
field the PI toggles at group or item granularity — surfaced as **one aggregate
work-prompt**, never N cards.
No confidence-tiered auto-accept anywhere: confident-wrong is the failure mode the
gate exists to catch.

## Consequences

- Each decision point in the workflow is classified (gate vs prompt) and its Inbox
  item designed accordingly; new features must declare which kind they add.
- Classification ships as audited metadata the PI can correct, not as a card.
- Batch screening borrows the systematic-review model (include/exclude with reasons),
  and its worklists converge — the Inbox stays an action queue that empties.
- The strongest gates (certify, link-confirm, re-adjudicate) always ship their
  reasoning.

## Alternatives considered

**A gate on classify.** Low-stakes metadata + high volume = guaranteed rubber-stamp;
automation with audit beats a fake decision. **One card per screened item.** Floods
the queue and trains select-all-accept. **Confidence-tiered auto-accept.** Waves
through exactly the confident-wrong outputs the gate exists to catch.

## Related

- **Related decisions / Depends on:** [ADR-03](03-structural-review-gate.md),
  [ADR-51](51-inbox-category-and-honesty-card.md), [ADR-15](15-project-membership-from-topic-hint.md)


---

<!-- source: adr/55-src-scaffold-populate-golden-copy.md -->

# ADR-55: The repo ships src/, the installer scaffolds and populates, and a golden copy makes the vault restorable

> **Verified on-box 2026-06-21.** The shipped mechanism is the SHA-256 golden
> manifest plus `check` and `restore`; `restore` is propose-only unless the caller
> passes `--apply`, and the absence of any release-upgrade reconcile command is
> test-pinned by `tests/test_golden_restore.py::test_upgrade_command_is_not_shipped`.

## Context

The repo carried a top-level `vault/` — effectively a live-vault template — which
blurred "source of truth" with "a running instance" and offered no recovery path when
a deployed system file drifted or was corrupted: the Linter could *detect* but not
*restore* (this ADR chooses
fresh-installed releases over in-place migration).

## Decision

The repo ships **`src/`** — source files only (templates, profiles, skills, schemas,
dashboards, patterns, `.obsidian` config), never a live vault. The installer
**scaffolds, then populates**: it creates the vault folder tree (the skeleton is
checked against `.memoria/schemas/folders.yaml`; empty content dirs get `.gitkeep`),
copies the system files from `src/`, and **stages a golden copy** of every system file
at `<vault>/.memoria/golden/` with a hash manifest. The **Linter restores from the
golden copy** on detected drift (`lint:restore` — propose-only by default; the PI or
cron applies). Installer flow: create → download → populate (+ golden copy) → install
Hermes → install profiles (pruning stale `memoria-*`) → install Obsidian → print the
finish-setup steps. **Zotero setup leaves the installer** and moves to the tutorial.
Releases are delivered **fresh-install** — build the complete system from `src/` and
replace the prototype, never migrate user content in place. Refreshing the test or
development vault is limited to overwriting shipped system files from `src/` and then
restaging `.memoria/golden/manifest.json` so later drift checks compare against the
installed source snapshot. There is no shipped in-place release-upgrade reconcile:
that broader layer-aware upgrade path belongs to the later versioned-release spine in
[ADR-76](76-versioned-vault-release-reconciling-installer.md).

This amends [ADR-26](26-repo-as-install-unit.md): the repo remains the install unit
and profiles remain hand-authored and idempotently deployed; what changes is the
shipped shape (`src/`, not a live vault) and the new restore capability.

## Consequences

- User content and system files are structurally separate from the first minute;
  current refresh/install paths repopulate shipped system files from `src/` and leave
  user content outside that scope.
- The Linter becomes a repairer, not just a detector — drift is fixable from a
  known-good baseline without re-running the installer.
- Cross-release, layer-aware upgrade reconciliation is not part of this ADR's shipped
  mechanism. ADR-76 owns that future versioned-release installer path.
- The installer gets simpler to reason about: scaffold and populate are idempotent,
  separately testable steps.
- Together with the lane ceilings this closes the template-protection question
  (#179) as **both**: agents cannot overwrite `system/templates/` because every
  shipped lane-override denies `system/**` (the Co-PI denies `**`) and no lane's
  `allow.write` / `write_scope` / auto-fix scope reaches into `system/`, enforced
  by the write gate ([ADR-28](28-write-gate-as-plugin.md)); an accidental *human*
  overwrite (or deletion) is detected as golden-copy drift and restored via
  `lint:restore`. Both halves are test-pinned (`tests/test_policy_mcp.py`,
  `tests/test_golden_restore.py`).

## Alternatives considered

**Keep shipping a live `vault/` template.** The drift and blurred-source-of-truth
problems this exists to fix. **In-place migration between releases.** Rejected by D52 —
half-migrated states are the failure mode; fresh-install sidesteps it.
**Populate the vault from `.memoria/golden/` instead of `src/`.** Equivalent at
install; `src/` populate + golden staging keeps authoring (repo) and restoring
(runtime) cleanly separate.

## Related

- **Related decisions / Depends on:** amends [ADR-26](26-repo-as-install-unit.md);
  [ADR-49](49-catalog-in-bases-linter-monitor.md), [ADR-47](47-type-first-category-folders.md)
- **Extended by (proposed):** [ADR-76: Distribute Memoria as a versioned vault release;
  deploy via a source-agnostic reconciling
  installer](76-versioned-vault-release-reconciling-installer.md) proposes extending this
  ADR's golden manifest to cover the code and authored-content layers; if accepted, its
  manifest supersedes this one.


---

<!-- source: adr/56-extraction-uncertainty-flag.md -->

# ADR-56: Low-confidence extraction routes to a flag — the ingest engine never merges identities silently

## Context

The Catalog is ungated because relationships are *given facts* — but the red-team pass
showed the "mechanical" ingest engine quietly makes fuzzy judgment calls at its seams:
entity resolution ("is this the same author?"), near-duplicate merging, license and
venue typing. A confidently-wrong merge would enter canon with no gate, and the
Linter's schema check validates *shape*, not *identity-correctness* (red-team theme B;
D51-decision).

## Decision

The ingest engine gates on **extraction uncertainty, not on the given/authored
distinction**: clean, unambiguous extractions write to the Catalog ungated as before
([ADR-30](30-deterministic-ingest-pipeline.md) unchanged for the mechanical pipeline) — but
**below a confidence floor, entity-resolution, dedup, and license/venue calls emit an
Inbox `flag`** (a near-tie card: the two candidates side by side, honesty-card body)
**instead of merging or writing silently**. The PI adjudicates same/different/unsure.
The confidence floor lives in `.memoria/schemas/calibration.yaml` alongside the other
calibrated thresholds (drift-bound; recalibrated on model/source changes).

> **Implementation status (2026-06-21).** The current entity-resolution guard is
> stricter than this ADR's flag route: ingest refuses fuzzy entity merges and
> creates/links entities only by stable IDs; no-ID entities remain recorded by name
> instead of being node-created or merged. The `entity_resolution.confidence_floor`
> entry is reserved configuration and is not consumed by a model. The shipped
> near-tie flag pattern exists for classification uncertainty, not yet for dedup or
> license/venue typing.

## Consequences

- Wrong-merge corruption — the one ungated path into canonical data — gets a human
  gate exactly where the fuzziness is, with near-zero friction on clean facts.
- The ingest engine needs a confidence signal per fuzzy call; heuristics that cannot
  produce one are treated as below-floor.
- Some false-positive flags are accepted as the price; the floor is tunable in one
  place.
- The same pattern (gate the uncertainty, not the category) is available to any future
  engine that makes fuzzy calls.

## Alternatives considered

**Keep all extraction ungated.** Silent wrong-merges into the source-of-truth Catalog.
**Gate all extraction.** Re-creates the rubber-stamp problem
([ADR-54](54-two-decision-kinds-batch-worklists.md)) on thousands of clean facts.
**Auto-accept above a confidence tier.** That is confidence-routing, rejected
repeatedly — the floor here routes *to* a human, never around one.

## Related

- **Related decisions / Depends on:** amends [ADR-30](30-deterministic-ingest-pipeline.md);
  [ADR-51](51-inbox-category-and-honesty-card.md), [ADR-49](49-catalog-in-bases-linter-monitor.md)


---

<!-- source: adr/57-engines-write-agents-judge.md -->

# ADR-57: Engines write, agents judge — no LLM agent as a mechanical writer

> **Vocabulary amended (2026-06-14, [ADR-69: Operations — name the deterministic
> layer and its four categories](69-operations-layer-naming.md)).** The deterministic
> layer this ADR calls **engines** is now named **Operations**. ADR-69 governs the
> vocabulary; this ADR keeps the decision — "Operations write, agents judge."

## Context

Memoria's split between deterministic **engines** and judgment-bearing **agents**
(ADR-46, ADR-48; the [task classification](../explanation/rationale/why-computational-methods.md))
has always carried an implicit corollary: an LLM agent is **never used as the
mechanical writer** of an artifact whose content is derivable by rule — catalog
records, logs, file moves, schema-shaped transformations, exports. ADR-30 applies it
to ingest ("scriptable-before-LLM"), ADR-32 applies it to external access, and
ADRs 9/10 invoke it when rejecting LLM-judged dashboards and supersession — but the
general decision and its reasons were never recorded in one place. This ADR records it.

(*Naming note:* this is unrelated to the **Writer** agent, whose drafting is a
*generative* task — open-ended composition the PI reviews behind the gate. The rule
governs **mechanical** writes: outputs with a single right answer.)

## Decision

**Any write whose correct content is derivable by rule is performed by an engine
(deterministic code), never by an LLM agent following an instruction.** Agents
contribute only the judgment holes (a brief, a classification proposal, prose) and
every agent write is a gated proposal. If a task's output can be specified — same
input, same bytes — it is engine work by definition.

## Why

Two properties a knowledge substrate cannot do without, and an LLM-as-scribe provides
neither:

1. **Consistency.** The same action must yield the same result. LLM output varies
   run-to-run even at `temperature 0`: production inference is not batch-invariant —
   floating-point non-associativity under varying server batch sizes makes identical
   prompts diverge (an experiment sampling one prompt 1,000 times at temperature 0
   produced **80 distinct outputs**; bitwise-identical completions required replacing
   the inference kernels themselves). Empirically, multi-step tool-calling agents show
   the same pattern at the behavioral level: stable tool *choice*, varying *arguments* —
   exactly the part that becomes file content. A mechanical writer that paraphrases a
   field name, reorders keys, or "helpfully" reformats once per hundred runs corrupts a
   substrate that schemas, links, and diffs depend on.

2. **Traceability.** When an engine writes, the *why* of every byte is reconstructable:
   a code path, inputs, a log line, a diff, a test that pins the behavior. When an
   agent writes from an instruction, the derivation lives in opaque sampling — the same
   action can yield a different result **without leaving a trace that lets you find out
   what happened**. The audit chain records *that* a write occurred and its hashes, but
   only deterministic code lets you replay and explain it. Observability research on
   agents reaches the same conclusion from the other side: making agent behavior
   auditable requires pinning and logging every model/prompt/tool version precisely
   *because* the step itself is irreproducible — machinery Memoria does not need to
   build for writes an engine can simply perform.

The cost asymmetry seals it: an engine write is cheap, testable, and idempotent; an
LLM write costs tokens and latency and can fail in ways no test can enumerate.

## How the rule lands in v0.1.0-alpha.2

- The ingest engine assembles records, builds relationships, appends the intake
  anchor; the Librarian fills only the two judgment holes (ADR-30, ADR-56).
- `board_export`, `metrics_aggregate`, `golden`, the sweeps, and the Linter write
  their artifacts directly as trusted engine code — never via an agent.
- The reconcile sweep stamps chat exports mechanically; no agent rewrites files.
- Agent writes that remain are judgment products (briefs, proposals, drafts, cards)
  and go through the policy gate as proposals (ADR-03, ADR-28).

## Trade-offs

- Every new mechanical write needs engine code (and a test) instead of a sentence in
  a SKILL.md — slower to add, which is the point: the sentence version is the failure.
- Some tasks sit on the boundary (e.g. summarize-then-file); the
  [task classification](../explanation/rationale/why-computational-methods.md) default
  test applies — if a rule would produce the right answer most of the time, the write
  is engine work and the LLM contributes at most a bounded judgment hole.

## Alternatives weighed

- **Let agents perform mechanical writes under tight prompts.** Rejected: prompt
  discipline degrades (ADR-03's argument), and no prompt restores batch-invariance or
  a derivation trace.
- **Accept variance and lint it away afterwards.** Rejected: the Linter is a monitor
  and commit gate, not a substitute for writes being right; silent near-misses inside
  schema-valid values are exactly what detectors cannot see.
- **Pin providers/kernels for deterministic inference.** Rejected as the general
  answer: batch-invariant inference exists but trades throughput, binds Memoria to
  specific serving stacks, and still leaves the derivation opaque — determinism
  without explainability.

## Evidence

- Thinking Machines Lab, *Defeating Nondeterminism in LLM Inference* (2025) — batch
  non-invariance as the root cause; 1,000 temp-0 samples → 80 distinct outputs;
  bitwise reproducibility only via batch-invariant kernels.
  <https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/>
- LMSYS, *Towards Deterministic Inference in SGLang* (2025) — what it takes to make
  serving deterministic, and the cost. <https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/>
- *How Consistent Are LLM Agents? Measuring Behavioral Reproducibility in Multi-Step
  Tool-Calling Pipelines* (2026) — "structural consistency, parametric variance"
  across 1,140 agent traces. <https://arxiv.org/abs/2605.28840>
- *AgentTrace: A Structured Logging Framework for Agent System Observability* (2026) —
  the logging burden required to make nondeterministic agent steps auditable.
  <https://arxiv.org/pdf/2602.10133>
- *Beyond Reproducibility: Token Probabilities Expose Large Language Model
  Nondeterminism* (2026). <https://arxiv.org/pdf/2601.06118>

## Related

- **Reinforces:** [ADR-30](30-deterministic-ingest-pipeline.md) (scriptable-before-LLM),
  [ADR-32](32-external-access-over-mcp.md), [ADR-46](46-seven-layer-architecture.md)
  (engines as an actor-kind), [ADR-03](03-structural-review-gate.md) (structure over
  prompt discipline).
- **Rationale page:** [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).


---

<!-- source: adr/58-adjacent-tool-integrations.md -->

# ADR-58: Adjacent tool integrations and added surfaces

## Superseded

This proposal bundle is split into one ADR per surface:

- [ADR-84](84-read-only-obsidian-inspector.md): Read-only Obsidian Inspector.
- [ADR-85](85-todoist-gap-card-mirroring.md): Todoist gap-card mirroring.
- [ADR-86](86-open-design-deliverable-rendering-agent.md): Open-design deliverable-rendering agent.
- [ADR-87](87-static-html-admin-reports.md): Static-HTML admin reports.
- [ADR-88](88-literate-code-note.md): Literate code-note.

## Related

- **Related decisions / Depends on:** [ADR-32 (external access over MCP)](32-external-access-over-mcp.md) (the gated path any external integration takes)
- **Original tracking issue:** [#408](https://github.com/eranroseman/memoria-vault/issues/408).


---

<!-- source: adr/59-classical-method-displacements.md -->

# ADR-59: Classical method displacements over LLM calls

## Superseded

This proposal bundle is split into one ADR per candidate displacement:

- [ADR-89](89-learning-to-rank-triage.md): Learning-to-rank for triage.
- [ADR-90](90-claim-sentence-classification.md): Claim-sentence classification.
- [ADR-91](91-classical-prose-metrics-export-gate.md): Classical prose metrics for the export gate.
- [ADR-92](92-discovery-relevance-scoring.md): Discovery relevance scoring.
- [ADR-93](93-keyphrase-extraction-tag-candidates.md): Keyphrase extraction for tag candidates.
- [ADR-94](94-record-linkage-entity-deduplication.md): Record linkage for entity deduplication.

## Related

- **Related decisions / Depends on:** [ADR-09 contradictions dashboard](09-contradictions-dashboard.md) (owns the NLI contradiction proposer); [ADR-30 deterministic ingest pipeline](30-deterministic-ingest-pipeline.md) (the deterministic discipline these displacements extend).
- **Source discussion:** [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).
- **Original tracking issue:** [#409](https://github.com/eranroseman/memoria-vault/issues/409).


---

<!-- source: adr/60-cross-vault-knowledge-sharing.md -->

# ADR-60: Cross-vault and cross-project knowledge sharing

> **Verified on-box 2026-06-21 (named enforcer not yet implemented).** Decision item 1
> says cross-vault read-only access works "with the policy MCP enforcing the boundary."
> On the installed gate that mechanism **does not exist**: `policy_hook.vault_root()`
> governs a single local vault and the decision core has no foreign-vault scope
> (`src/.memoria/mcp/policy_hook.py:155`). This ADR is `accepted`-shape but unscheduled
> ("the scheduling waits on the trigger"), so it is a *deferred* design, not shipped — it
> must not be read as a live guarantee. When built, cross-vault read-only requires a real
> foreign-vault scope **and** a deny-write test proving the foreign vault rejects writes.
> Per AGENTS.md "Enforcement is a mechanism, not a label."

## Context

The v0.1 scope is one researcher working one vault on one machine ([ADR-24](24-single-researcher-scope.md)). But a researcher accumulates more than one vault (a collaborator's, a separate domain vault) and more than one project inside a vault, and recall does not currently cross either boundary: a claim settled in vault A is invisible from vault B, and work approved on one project never primes another. Each gap is a felt friction only once the second vault or third project is real — so the shapes are settled here while the scheduling waits on the trigger.

## Decision

Memoria defines four additive cross-boundary capabilities, each scoped to a memory substrate ([ADR-23](23-scoped-memory-substrates.md)) and each gated behind its own trust guard:

1. **Cross-vault read-only retrieval.** MCP-mediated read access to a second Memoria vault, strictly read-only — no writes, no card creation — with the policy MCP enforcing the boundary. The foreign vault's canon is someone else's: its claim notes are treated as *sources*, not as your own synthesis. Requires both vaults reachable by the same Hermes instance.
2. **Cross-project reading as personal AgentRxiv.** Profiles scan approved outputs from other projects in the same vault at session start — the within-vault analogue of AgentRxiv's ~11% gain from agents reading prior agent reports — implemented as a step in the Librarian's session-start routine.
3. **Scripted session-history sync.** `hermes profile export` / `import` snapshots carry `state.db` chat history between machines for session continuity without a shared server, extending the `memories/` junction sync pattern. Manual or cron-triggered; snapshots must exclude credentials.
4. **Hermes shared-memory server.** A remote shared memory provider giving real-time, concurrency-capable cross-machine recall — the live-service replacement for scripted snapshots — adopted only for the specific failure mode where the scripted approach breaks.

## Consequences

- Cross-vault retrieval introduces a trust boundary: foreign claim notes must never be promoted to local canon without re-synthesis.
- Cross-project reading earns its keep only on a vault with real overlap; on a sparse vault it adds noise and latency.
- The Hermes memory server adds standing infrastructure cost and a hosting dependency — scripted sync covers ~90% of the need at zero infrastructure, which is why it is sequenced first.

## When this matters

Per capability, a concrete signal — not "might be useful" — as context for the cadence review:

- **Cross-vault retrieval:** two active research vaults are in use and you regularly switch between them to check whether a claim from vault A is addressed in vault B.
- **Cross-project reading:** the vault has ≥ 3 active projects with ≥ 50 approved claim notes each, *and* cross-project insights are being missed until manual review.
- **Scripted session-history sync:** you regularly start a session on a second machine and want prior session context from the primary.
- **Hermes memory server:** the scripted snapshot approach is *already* failing because you switch devices frequently *within* a single work session, not just between sessions. **Guard: do not adopt the memory server before scripted sync has been tried** — it is the right fix for one specific failure mode, and adopting it pre-emptively buys infrastructure cost without clear benefit.

## Related

- **Related decisions / Depends on:** [ADR-23](23-scoped-memory-substrates.md) (the scoped memory substrates each capability rides on); [ADR-24](24-single-researcher-scope.md) (single-researcher scope) — this ADR extends ADR-24's bounds outward to the multi-vault, multi-project case while keeping the single-operator invariant.
- **Deployment substrate:** [ADR-63 multi-machine deployment](63-multi-machine-deployment.md) — the sync topologies these cross-machine capabilities run on; the two are designed to move together.
- **Tracking issue:** [#410](https://github.com/eranroseman/memoria-vault/issues/410) — implementation readiness lives on the issue.


---

<!-- source: adr/61-nightly-discovery-loop.md -->

# ADR-61: Nightly discovery loop, code-experiment loop, and Writer-proposed claims

## Superseded

This proposal bundle is split into one ADR per lane-bounded automation expansion:

- [ADR-95](95-nightly-proactive-discovery-loop.md): Nightly proactive discovery loop.
- [ADR-96](96-code-lane-keep-revert-experiment-loop.md): Code-lane keep/revert experiment loop.
- [ADR-97](97-writer-proposed-candidate-claim-notes.md): Writer-proposed candidate claim notes.

## Related

- **Related decisions / Depends on:** [ADR-48 Co-PI and agent consolidation](48-copi-and-agent-consolidation.md) (the Librarian `find` capability the nightly loop drives); [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the boundary all three respect); [ADR-51](51-inbox-category-and-honesty-card.md) (candidate and gap proposals land as Inbox cards).
- **Original tracking issue:** [#411](https://github.com/eranroseman/memoria-vault/issues/411).


---

<!-- source: adr/62-measurement-and-verification-harnesses.md -->

# ADR-62: Measurement and verification harnesses

## Context

A set of analysis capabilities would make the Peer-reviewer measurable, the claim layer richer, and the system's health visible over time. The **minimal capture** they all read — the six-signal operational log (state-transition timestamps + decision time, cost per card, deny reasons, suggestion disposition, FAMA exposure) — is the single highest-leverage action from the publication-path report, with schemas pinned in [Telemetry & logs](../reference/telemetry.md) (see [ADR-20 publication path](20-publication-path.md)). Capture cannot be back-filled, so the schema and available emitters ship first. ADR-106 closed the former card-overlay gap by joining cost to Hermes session rows and writing disposition at the human review action. This ADR records the harness family: the fleet observability aggregator has shipped, while the remaining harnesses stay deferred until their per-item conditions raise priority.

## Decision

Memoria treats the following analysis harnesses as the approved direction:

- **CiteME-style Peer-reviewer regression harness.** A private fixture of ~50 (excerpt → target-claim-note) pairs built from approved vault drafts, scored against the Peer-reviewer nightly, with accuracy recorded in a metric note. A Peer-reviewer prompt change ships only when fixture accuracy is at or above the running 90th-percentile baseline — preventing silent regression from model updates, context-length changes, or template edits.
- **Chain-of-Evidence claim taxonomy.** Type each substantive claim and require a type-appropriate evidence chain — `citation` (resolved citekey + claim note), `numerical` (the passage containing the figure), `methodological` (protocol summary), `conclusion` (the claim notes it rests on). Adapted from ScientistOne (Meng et al. 2026). The CiteME harness is the gate: adopt typing only if the harness shows it measurably reduces false-clean verdicts. Score verification and method–code alignment are out of scope for knowledge work (code lane only).
- **Fleet observability aggregator.** A scheduled aggregator reads the audit log and board history to materialize the [fleet-health dashboard](../explanation/dashboards/operational-health/fleet-health.md) — per-lane and per-skill cost, success rate, retry rate, and latency on daily/weekly/monthly cadence. This slice is built as `metrics_aggregate.py` and the `memoria-metrics` cron wrapper.
- **Propagation debts re-eval queue.** When a high-traffic note changes (claim promoted to `evergreen`, reference updated, paper retracted), enumerate the dependents needing re-evaluation and record them as a readable queue in the Linter's report. The human works the queue; the agent never rewrites dependents.
- **LLM-judge `prose-check` export gate.** At export time only, a `prose-check` command scores the manuscript on a small fixed rubric (argument coherence, voice consistency, citation grounding) and attaches a report to the export card. It never auto-edits, never blocks export, and never runs against synthesis — the human reads it and decides whether to revise.
- **Execution-trace reflection on retry.** On a retry, a reflection skill reads the failure trace (tool called, arguments, error) and produces a *modified* handoff payload for the next attempt — not an identical redispatch. The reflection layer rewrites the handoff payload for one card only; it never rewrites prompts, skills, or system contracts. A `reflection_count` field (distinct from retry count) shows when reflection itself is exhausted.

## Consequences

- Each remaining deferred harness reads the six-signal capture model. Cost and disposition now have first-class emitters through the [ADR-106](106-cost-and-disposition-capture.md) path; `cost-misses.jsonl` rows are data-quality misses, not zero-cost activity.
- Several harnesses gate one another (the CiteME fixture gates the claim taxonomy; fleet observability surfaces the retry rate that gates reflection-on-retry), so order matters and the conditions encode it.
- Partial adoption can be worse than none — a claim taxonomy with most claims untyped makes type-aware checks unreliable; a too-small or too-easy CiteME fixture gives false confidence — so each waits for its condition.
- Verdicts stay diagnostic, not gating, consistent with [ADR-11](11-vault-eval-maintenance.md): an eval or prose-check dip informs the human and never auto-halts scheduled work.
- New machinery is still required where noted (structured failure traces in the Kanban dispatcher, fixture-construction effort, export-time prose check) — real implementation costs that the conditions defer until justified.

## When this matters

Per-item conditions that raise priority at the cadence review:

- **CiteME regression harness** — the Peer-reviewer is live against real drafts *and* at least one project has produced ≥ 20 approved drafts citing ≥ 20 approved claim notes. (Building before the Peer-reviewer's behavior settles pins the fixture to a transient prompt.)
- **Chain-of-Evidence taxonomy** — the CiteME harness is live with a measured untyped baseline *and* false-clean Peer-reviewer verdicts are a recurring issue; adopt only if the harness shows typing measurably reduces them.
- **Fleet observability aggregator** — built in v0.1.0-alpha.4 as `metrics_aggregate.py` plus the `memoria-metrics` cron wrapper.
- **Propagation debts queue** — the corpus passes ~500 claim notes *and* the human notices, while reading a draft, that a cited claim has shifted.
- **LLM-judge `prose-check` gate** — a deliverable has been re-exported more than twice for issues a model could have caught on the first read.
- **Reflection-on-retry** — sustained retry rate > 0.10 across a lane visible in fleet observability, *or* a specific skill's retry rate crosses 0.20.

## Current implementation mapping

The telemetry schema and downstream aggregation contract are current system behavior.
`audit.jsonl`, `board-state.jsonl`, `board-transitions.jsonl`,
`lint-findings.jsonl`, `disposition.jsonl`, and `cost.jsonl` emit through their
documented writers. ADR-106 deliberately keeps cost and disposition off the card
metadata overlay: cost/tokens join a completed card to the Hermes session store via
`hermes kanban show <id> --json` and
`runs[].metadata.worker_session_id`, while disposition is written by the
`Memoria: resolve inbox card` QuickAdd action. Consumers must treat
`cost-misses.jsonl` rows as join-quality misses, never as valid zero-cost runs.

## Related

- **Related decisions / Depends on:** [ADR-11 vault-eval as a maintenance capability](11-vault-eval-maintenance.md) (the diagnostic-not-gating discipline and the eval surface these harnesses report through); [ADR-20 publication path](20-publication-path.md) (the six-signal capture these harnesses read, already adopted); [ADR-41 configurable review-gate mode](41-configurable-review-gate-mode.md) (the export/review gate the `prose-check` capability attaches to).
- **Source discussion:** [Telemetry & logs](../reference/telemetry.md).
- **Tracking issues:** [#412](https://github.com/eranroseman/memoria-vault/issues/412)
  — cadence review for the harness family;
  [#737](https://github.com/eranroseman/memoria-vault/issues/737) — implemented
  session-store/review-action path for `disposition.jsonl` and `cost.jsonl`.


---

<!-- source: adr/63-multi-machine-deployment.md -->

# ADR-63: Multi-machine deployment topologies and secondary-device patterns

## Context

The v0.1 default is `local-only` — one workstation, Git for history, Zotero on localhost ([deployment options](../explanation/deployment/deployment-options.md)). That default requires the workstation to be on and offers neither auto-sync nor unattended automation. Two felt needs push past it: working the vault from a second device (laptop, phone, tablet), and running discovery/ingest overnight without a human kickoff. Both require a sync topology *and* a safe answer to "what may a non-primary device do against a vault the primary is also dispatching against?" — without one, two machines race on card writes and corrupt the audit log. The topologies are additive and cost nothing to defer, so they are settled here and scheduled later. `deployment-options.md` currently defers the past-`local-only` substrate *to* this decision, which is its authoritative target.

## Decision

Memoria defines three sync topologies beyond `local-only`, a set of secondary-device operating patterns, and the invariants that keep them safe:

- **Three topologies:** `local-mesh` (Syncthing P2P, no VPS, $0 infra — desktop + laptop); `obsidian-sync` (Obsidian cloud sync, ~$10/mo, `.bib`-only Zotero on the VPS — when iOS access is needed); `always-on` (Syncthing + VPS, ~$12–25/mo — multi-device with an always-on agent, recommended for the discovery loop). Migration is monotonic: start `local-only`, move to `local-mesh` when a second device enters the workflow, graduate to `always-on` when unattended automation is wanted. `local-mesh` is structurally `always-on` minus the VPS.
- **Secondary-device patterns**, ordered by setup complexity: *vault-only* (Obsidian + Git, read/write notes, ~80% of daily work, no Hermes); *Telegram dispatch* (dispatch via the primary's bot, nothing installed locally); *HTTP API client* (POST to the primary's loopback/Tailscale API); *Hermes ACP-only* (local Hermes binary, the only pattern enabling the `agent-client` plugin); and *SSH-spawned ACP* (no local Hermes — spawn the primary's Hermes over SSH). Pattern selection follows topology: under `local-mesh` the desktop primary sleeps, so a local ACP install is preferred; under `always-on` the VPS is always reachable, so SSH-spawn is the default and removes install drift.
- **Structural-over-behavioral install policy.** A secondary device compiles only profiles architecturally safe on it, not the primary's full set. `memoria-copi` is the always-safe baseline — `policy.allow.write: []` and `routing.invocation: interactive_only` mean it *cannot* write or be queue-dispatched regardless of human behavior. The background lanes — Librarian, Writer, Peer-reviewer, and Engineer — are add-as-needed/dispatched, each carrying obligations the human must remember (API cost, queue conflicts, or background-only) before being installed on a secondary. Structural enforcement ("profile not found") beats the behavioral convention "don't enable cron, don't claim cards."
- **One dispatcher per vault, enforced by isolation.** Exactly one Hermes dispatcher touches a given vault. A developer's full install may coexist with the primary *only* by pointing at a different vault: under `always-on`, `HERMES_HOME` isolation **and** a *test vault* (clone, fixture, Docker volume) are mandatory, never optional — a dev Hermes on the production vault while the VPS also dispatches is the failure mode this rule exists to prevent.

## Consequences

- **Write coordination is the core risk** the whole secondary-device design exists to make structurally impossible, not merely discouraged.
- `always-on` adds standing cost and ops surface — a rented VPS, a Syncthing mesh to keep healthy, and a cron whose silent failure is the dominant operational risk.
- `obsidian-sync` degrades Zotero to `.bib`-only on the VPS, constraining Librarian discovery on that node.
- SSH-spawned ACP removes local install drift but adds a reachability dependency (primary awake, ~100–500ms/message latency).
- Install drift across devices is a standing maintenance cost once more than one machine compiles profiles — the Co-PI-only baseline is what keeps it bounded.

## When this matters

Per topology, a concrete signal — context for the cadence review, not a gate:

- **`local-mesh`:** a *second device* genuinely enters daily use and manual Git pull/push between machines is the felt friction.
- **`always-on`:** unattended overnight work is wanted — most concretely the discovery loop — and a sleep-prone workstation keeps missing the cron.
- **`obsidian-sync`:** iOS/mobile vault access is required and Syncthing-on-mobile isn't viable.

**Guard: do not stand up a VPS or Syncthing mesh as a preparatory measure.** `local-only` is the correct posture until a second device or unattended automation is real; Syncthing is additive later and restructures nothing, so there is no first-mover cost to pay early. The invariant that must never relax on adoption: **exactly one Hermes dispatcher per vault**.

## Related

- **Authoritative target / adopted baseline:** [deployment options](../explanation/deployment/deployment-options.md) — defers the past-`local-only` substrate to this decision; documents the `local-only` default and the common conventions (Git history, `memoria.bib` in-vault, one dispatcher per vault, `.env` per-machine) these patterns presuppose.
- **Related decisions / Depends on:** [ADR-24](24-single-researcher-scope.md) (single-researcher scope); [ADR-26](26-repo-as-install-unit.md) (repo as install unit); [ADR-55](55-src-scaffold-populate-golden-copy.md) (src scaffold).
- **Cross-machine capabilities:** [ADR-60 cross-vault knowledge sharing](60-cross-vault-knowledge-sharing.md) — the capabilities that ride this substrate; the two are designed to move together.
- **Tracking issue:** [#413](https://github.com/eranroseman/memoria-vault/issues/413) — implementation readiness lives on the issue.


---

<!-- source: adr/64-native-windows-support.md -->

# ADR-64: Native Windows support: production on Windows, testing on Linux

## Context

Memoria's first shipped Windows path was **WSL2-only**: Hermes and the Python operations ran inside WSL2, while Windows hosted only the editing surface (Obsidian, Zotero, the vault files), reached across `/mnt/c` and a loopback bridge. `install.ps1` was a thin WSL2 launcher; `install.sh` was the real, apt-based bash installer.

That rule rested on two rationales that have since weakened:

1. **"Hermes is WSL2-only on Windows"** — no longer true. Nous's current official docs state Hermes runs natively on Windows 10/11 (no WSL, no Cygwin, no Docker), with a dedicated native installer that auto-provisions Python 3.11 / Node 22 / PortableGit. The feature matrix shows native CLI, TUI, gateway, cron scheduler, MCP stdio/HTTP, browser tool, dashboard, and login auto-start. The only called-out missing feature is the dashboard `/chat` embedded terminal pane, which needs a POSIX PTY; Memoria's Obsidian ACP pane does not depend on that pane.
2. **Windows build-pain for the analysis stack** — largely gone. Current pip wheels cover `umap-learn` (+ `numba`/`llvmlite`), `hdbscan`, `bertopic`, `torch` (CPU), and `faiss-cpu` on native Windows. That stack is also not shipped yet (it is the [ADR-33](33-cluster-mcp-bertopic.md) cluster MCP follow-up), so it is a non-blocker today.

The alpha.4 decision is to stop treating WSL2 as the production Windows runtime.
Production installs run natively on Windows; Linux/WSL remains the test harness
and developer validation path.

> **Cadence review (2026-06-16, v0.1.0-alpha.4): accepted.** The live Hermes
> Windows Native guide documents native Windows support for the runtime surfaces
> Memoria uses. This supersedes the WSL2-only rule and folds the broader
> migration tracked in [#296](https://github.com/eranroseman/memoria-vault/issues/296)
> into the native production installer.

## Decision

**Native Windows is the production runtime. Linux/WSL is the testing runtime.**
Do the port as a two-script split, not as a runtime flag:

- **Production provisioning** — `scripts/install.ps1` is a native Windows installer. It wraps Hermes's native Windows installer, lays down the vault from `src/`, creates the vault-local MCP venv, deploys the five profiles with Windows paths, propagates `.env` values, deploys the policy-gate plugin, and wires Hermes cron wrappers.
- **Testing provisioning** — `scripts/install.sh` remains the Linux/WSL test installer. It is the path CI and disposable Linux/WSL validation use.
- **Scheduling and always-on** — use Hermes's native Windows gateway and cron support. The deterministic wrappers remain shared for now and execute through Hermes's Windows shell strategy.
- **Bridge removal** — the production path has no `/mnt/c` translation, no WSL2 gate, and no `windowsWslMode` requirement for ACP. The WSL bridge remains only in WSL-specific test docs.

This **supersedes the WSL2-only rule** ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md), the [installer platform matrix](../reference/installer.md)), **amends [ADR-26](26-repo-as-install-unit.md)** (`install.ps1` is a real installer), and **reinforces [ADR-22](22-build-on-hermes-runtime.md)** (Memoria builds on Hermes rather than reimplementing a runtime).

## Consequences

- Native Windows removes the WSL2↔Windows boundary problems — the `networkingMode=mirrored` production requirement for the Obsidian REST bridge ([ADR-31](31-native-obsidian-mcp.md)), `/mnt/c` cross-boundary file-lock fights, OneDrive/WSL lock interactions, `/mnt/c` path translation, and `windowsWslMode` in the ACP pane.
- The Linux/WSL path remains valuable, but as a test environment rather than the production Windows recommendation.
- Live Windows verification is still required before declaring a release candidate green; the architectural blocker is gone.

## Follow-up verification

- Run `scripts/install.ps1 -DryRun` and a full attended native Windows install against a disposable vault before release-candidate signoff.
- Confirm ACP launches `hermes` natively with `windowsWslMode: false`.
- Confirm the verified HTTPS Obsidian MCP works with `OBSIDIAN_MCP_SSL_VERIFY`.
- If [ADR-33](33-cluster-mcp-bertopic.md)'s stack ships, avoid base `hnswlib` on Windows: its sdist-only package needs MSVC to build. Swap to FAISS / `chroma-hnswlib` and pin Python 3.10-3.13.

## Related

- **Reinforced / assumed:** [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (Hermes is now native), [ADR-26 repo is the install unit](26-repo-as-install-unit.md) (`install.ps1` becomes a real installer).
- **Affected decisions:** [ADR-31 native Obsidian MCP](31-native-obsidian-mcp.md) (bridge simplifies on one OS), [ADR-33 cluster MCP](33-cluster-mcp-bertopic.md) (the Windows wheel edge).
- **Installer shape:** [Installer (bootstrap)](../reference/installer.md), [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) (the WSL2-only rule this would supersede).
- **Tracking issue:** [#414](https://github.com/eranroseman/memoria-vault/issues/414) — revisit at each release cadence.


---

<!-- source: adr/65-retrieval-and-schema-extensions.md -->

# ADR-65: Retrieval and schema extensions

## Superseded

This proposal bundle is split into one ADR per retrieval/schema extension:

- [ADR-98](98-relation-vocabulary-expansion.md): Relation-vocabulary expansion.
- [ADR-99](99-massw-aligned-paper-aspects.md): MASSW-aligned paper aspects.
- [ADR-100](100-exploration-trace-capture.md): Exploration-trace capture.

## Related

- **Related decisions / Depends on:** [ADR-52 (links vs relationships)](52-links-vs-relationships.md) (the typed-relationship base this extends and the split this respects), [ADR-30 (ingest pipeline)](30-deterministic-ingest-pipeline.md) (where `_aspects` are populated)
- **Original tracking issues:** [#415](https://github.com/eranroseman/memoria-vault/issues/415)
  and [#611](https://github.com/eranroseman/memoria-vault/issues/611).


---

<!-- source: adr/66-triage-ranking-improvements.md -->

# ADR-66: Semi-automatic triage, agent-consensus pre-filter, and tournament ranking

## Context

Three capabilities reduce the operator's per-candidate judgment cost without moving the autonomy boundary: batching high-confidence classifications into one approval, routing a consensus pre-filter ahead of the review queue, and ranking a large inbox by pairwise comparison. None bypasses the structural review gate — they change what reaches it and in what order. They are grouped because they share that constraint and because each carries a calibration risk that makes premature adoption worse than waiting; the thresholds below are cadence-review context, not gates.

## Decision

Memoria will, when scheduled, add:

1. **Semi-autonomous batch triage.** The classifier already emits a confidence score with `_proposed_classification`. When confidence is above a threshold (e.g. > 0.92), proposals are batched into a single "approve these classifications?" card rather than reviewed individually; low-confidence proposals remain individual reviews. The threshold is calibrated against the operator's measured error rate, and the batch card surfaces the full list readably. Applies only to classification dimensions where calibrated confidence exists — never to new note types the classifier hasn't seen.

2. **Agent-consensus pre-filter.** Before a candidate reaches the review queue, a second independent profile pass reviews the output; agreement sets `consensus: true`, disagreement `consensus: false`, and the operator processes disagreement cards first. It does not bypass the gate — the gate stays structural; the pre-filter only routes. To avoid correlated errors (the Bisht et al. 2026 hivemind finding), the two profiles use models from different providers or fine-tuning regimes.

3. **Tournament pairwise ranking.** When the discovery inbox is large (> 50 candidates), candidates are ranked by pairwise LLM comparison against `research-focus.md` to surface the top-N first; lower-ranked candidates can be deferred. This is an explicit cold-start fallback for the learning-to-rank model — once that model has enough training data, Memoria switches to it (cheaper, faster, personalized).

## Consequences

- A too-permissive confidence threshold promotes wrong classifications silently; calibration against the actual error rate is load-bearing.
- The consensus pre-filter adds latency and per-card cost, and two profiles with correlated errors can agree and be confidently wrong together — it has diminishing value on shared-model failure modes.
- Pairwise comparison cost scales quadratically with queue size, and ranking is personalized only while `research-focus.md` is current.

## Current implementation mapping

#379 adds the threshold contract in
[`calibration.yaml`](../reference/calibration.md): `hybrid_scores.candidate_rank`
and `hybrid_scores.outline_score` are present but `production_enabled: false` with
null thresholds until real PI decisions/outcomes fill the grounding dataset and
error budget. The clustering quality thresholds live under
`clustering.quality_thresholds` with the same shadow-first rule. No score from this
ADR may change routing or review visibility until those fields are filled.

## When this matters

*(Cadence-review context, not a gate.)*

- **Semi-autonomous triage** — classification backlog exceeds a week's review capacity *and* the classifier has run for ≥ 2 months with a measured accuracy baseline.
- **Agent-consensus pre-filter** — review-queue depth consistently exceeds 2 weeks' backlog *and* a spot-check shows agreed cards are approved at > 90% rate. If the two profiles share an underlying model or training, the correlated-error risk is real — use different providers or regimes.
- **Tournament ranking** — the inbox regularly exceeds 50 candidates *and* the learning-to-rank model is not yet trained. It is the expensive cold-start alternative; retire it once learning-to-rank has data.

## Related

- **Related decisions / Depends on:** [ADR-50 lifecycle](50-universal-lifecycle-and-maturity.md) (the card states triage moves between); [ADR-51 inbox honesty card](51-inbox-category-and-honesty-card.md) (the inbox surface these improvements feed); [ADR-54 batch worklists](54-two-decision-kinds-batch-worklists.md) (the batch-approval mechanism semi-auto triage builds on).
- **Tracking issue:** [#416](https://github.com/eranroseman/memoria-vault/issues/416) — implementation readiness lives on the issue.


---

<!-- source: adr/67-drift-procedures-keep-or-retire.md -->

# ADR-67: Drift procedures under the golden-copy model — keep or retire

## Context

The original structural-linter design (v0.1.0) specified five **weekly agent-run drift
procedures**: golden-copy, skeleton-drift, profile-install-drift, command-vocab-drift,
and plugin-config-drift. The as-built rewrite (PR #390) shipped only the golden-copy
baseline and marked the rest deferred; the design pages themselves were later retired
into ADRs (PR #406). Each procedure needed a keep-or-retire decision under the
golden-copy model ([ADR-55](55-src-scaffold-populate-golden-copy.md)), tracked in
[#394](https://github.com/eranroseman/memoria-vault/issues/394). A sibling decision —
the audit-chain checks (`vault-hash-drift`) — is recorded in
[ADR-25](25-session-logging-two-logs.md).

A structural observation drives the outcome: nothing here needs a *weekly agent run*.
What is deterministic belongs in the zero-LLM Linter engine on the daily cron
([ADR-49](49-catalog-in-bases-linter-monitor.md)); what needs deploy-host state the
vault cannot see belongs to the idempotent installer; what is repo-consistency belongs
to the repo's CI tests.

## Decision

| Procedure | Decision | Where it lives |
| --- | --- | --- |
| **golden-copy** | **Keep — built** | `operations/integrity/linter/golden_restore.py` (stage / check / restore) on the daily lint cron ([ADR-55](55-src-scaffold-populate-golden-copy.md)). |
| **skeleton-drift** | **Keep — built** | The Linter's `skeleton-drift` detector: every directory in the `skeleton` list of `.memoria/schemas/folders.yaml` must exist in the vault; a missing one is a MEDIUM finding (fix: re-run the idempotent installer or `mkdir`). Checked only in installed vaults — keyed on the golden manifest — because the repo's `src/` deliberately ships no empty dirs ([ADR-55](55-src-scaffold-populate-golden-copy.md)). Needs only the vault tree, so it is a vault-side detector, not an agent run. |
| **plugin-config-drift** | **Keep — via the golden copy** | The installer ships Obsidian plugin config from `src/.obsidian/` into the runtime vault, so the golden manifest now covers the **Memoria-shipped** config files: each shipped plugin's `data.json` plus `community-plugins.json`, `core-plugins.json`, and the `memoria-link-colors.css` and `memoria-property-badges.css` snippets. Per-machine / runtime-generated state never enters the manifest — `agent-client/data.json` is seeded per machine from its `.example`, `obsidian-local-rest-api` regenerates its `data.json` (apiKey + TLS) on first launch, and workspace/appearance/graph state is the user's to mutate. |
| **profile-install-drift** | **Retire** | It needs `~/.hermes` deploy state the vault-side Linter doesn't have. Deploy drift is *fixed*, not just detected, by re-running the idempotent installer (`--profiles-only`), and the vault-side sources of the deployed profiles are golden-copy-covered. A detector that can see only one side of the comparison adds nothing over the fix. |
| **command-vocab-drift** | **Retire** | Config/vocabulary consistency is a repo CI concern, single-sourced and tested there: `tests/test_profiles.py` checks every profile's lane-override exists, lane write-scopes avoid the gated zones, and configs reference real MCP servers; `tests/test_schemas.py` pins the gated-prefix fallbacks in `policy_mcp`/`patterns_mcp` to `folders.yaml`; `tests/test_policy_hook.py` covers the gate plugin's tool matching and hard-denies. A weekly vault-side re-check would re-derive what CI already gates per commit. |

The detectors built here and in ADR-25 (`skeleton-drift`, `vault-hash-drift`,
`audit-log-size`, `hub-threshold`) run with the rest of `detectors.py` on the **daily**
lint cron — strictly more often than the designed weekly cadence.

## Consequences

- No weekly agent-run drift procedure exists or is planned; the category is closed.
  Drift work is split engine (daily cron) / installer (idempotent re-run) / repo CI.
- Retiring profile-install-drift leaves source→deployment drift detectable only by
  re-running the installer; that is accepted because the re-run *is* the repair, and
  [ADR-26](26-repo-as-install-unit.md)'s detector/installer "matched pair" framing is
  amended accordingly.
- The golden manifest now includes shipped Obsidian config, so a PI who deliberately
  tunes a shipped plugin setting will see a `golden check` drift report until the
  golden copy is re-staged — the same propose-only discipline as every system file.

## Alternatives considered

**Implement all five as designed (weekly agent runs).** Rejected: every procedure is
either deterministic (engine), host-side (installer), or repo-side (CI); an LLM agent
adds cost and nondeterminism to checks that need neither.

**Retire plugin-config-drift too.** Rejected: the installer demonstrably ships plugin
config (`rsync src/ → vault`, with `agent-client/data.json` seeded from its example),
so shipped-config corruption is real and the golden copy already has the machinery to
catch and restore it.

## Related

- **Tracking issue:** [#394](https://github.com/eranroseman/memoria-vault/issues/394).
- **Related decisions:** [ADR-55](55-src-scaffold-populate-golden-copy.md) (golden copy), [ADR-25](25-session-logging-two-logs.md) (audit-chain checks), [ADR-26](26-repo-as-install-unit.md) (idempotent installer), [ADR-49](49-catalog-in-bases-linter-monitor.md) (Linter as engine).
- **Reference:** [Linter: detectors and auto-fix](../reference/linter.md).


---

<!-- source: adr/68-workspaces-desk-library-studio.md -->

# ADR-68: Workspaces v2 — Desk / Library / Studio, home.md as control panel

## Context

The shipped workspace set was two layouts (**Home**, **Library**) with a promised
third ("Project", slated for v0.1.0-alpha.3) that never shipped. The two layouts had
no shared contract: Home put the board in the *right* pane and the homepage in the
main pane, Library opened on an empty tab, the Co-PI chat pane appeared in neither,
and the catalog base was serialized as a `markdown` leaf. Meanwhile `home.md` had
grown prose (explanatory header, "Start here", a web link-dump) around its working
parts, and every quick action still required a palette round-trip.

## Decision

**Three workspaces — Desk, Library, Studio — under one shared layout contract**, and
`home.md` rewritten as a four-block control panel.

The shared contract, in every workspace:

- **Main pane** is the mode's work surface — a real file, never `home.md`, never an
  empty leaf.
- **Left sidebar** (~320) is navigation: 2–4 pinned tabs of that mode's drill-down
  views, with the file explorer always the **last** tab.
- **Right sidebar** (~360) is the Co-PI: the agent-client chat view
  (`agent-client-chat-view`) pinned in every workspace — the conversation partner
  travels with the mode.
- `home.md` is pinned in **no** workspace; the obsidian-homepage plugin opens it on
  launch ([ADR-13](13-homepage-front-door.md)).

| Workspace | Mode | Main pane | Left tabs (then file explorer) |
| --- | --- | --- | --- |
| **Desk** | "What needs me?" | `system/dashboards/board-state.md` | `inbox/inbox.base`, `drift-watch.md`, `weekly-review.md` |
| **Library** | Reading & synthesis | `system/dashboards/reading-pipeline.md` | `catalog/catalog.base`, `discuss-queue.md`, `open-questions.md`, `contradictions.md` |
| **Studio** | Drafting | `research-focus.md` (projects/ ships empty — the priorities note is the drafting anchor) | `system/dashboards/claims.base`, `system/patterns/patterns.base` |

Studio's right sidebar carries a second tab — the core backlink view — behind the
Co-PI tab: backlinks finally live where there is an active note. **Studio replaced
the original empty "Project" workspace promise for alpha.3; the later
[Project gate](77-project-gate.md) uses the same workspace machinery for bounded
inquiry rather than reviving that empty workspace.** `.base` leaves serialize as view type `bases`
(the core Bases view registered for the `base` extension), fixing the previous
`markdown` mis-serialization.

`home.md` becomes a **four-block control panel** (still a consumer-only Dataview
note per ADR-13): (1) a one-line **status strip** (reviews pending · blocked ·
HIGH/CRITICAL findings, linking board and drift-watch); (2) an **action row** of
command buttons (capture fleeting / Zotero / URL, delegate, resolve card, talk to
Co-PI); (3) a **navigation row** (Desk · Library · Studio · Project gate, with
Project opening inside Studio rather than adding a fourth saved workspace); (4) the **drill-down
index** — the collapsed dashboard callouts plus research-focus and
troubleshooting. Everything else (prose, link-dumps, docs-site links beyond
troubleshooting) is dropped.

Two mechanisms support the panel:

- **Buttons** (shabegom/buttons) is adopted as a **bundled (required) plugin** —
  vendored under `src/.obsidian/plugins/buttons/`, listed in
  `community-plugins.json`, golden-copy-covered. Standing rule: **command-type
  buttons only.** The plugin's `template` / `text` / `calculate` button types write
  to notes outside the policy gate and are banned.
- The core Workspaces plugin has no per-workspace load commands, so a QuickAdd user
  script (`system/scripts/load-workspace.js`) loads a named workspace via the
  internal-plugin API, and three macro choices ("Memoria: open Desk workspace / Library /
  Studio") pass the target name via QuickAdd's per-command settings — giving one
  one-click palette command (and button) per workspace.

## Consequences

- Switching workspaces is one click or one palette command; the Co-PI pane is
  present in every mode, so "talk to the agent" never requires layout surgery.
- `home.md` is glance-and-go: status, actions, navigation — no duplicated dashboard
  queries, no prose to rot. It remains git-tracked, lintable, consumer-only.
- One new required plugin (Buttons). Its write-capable button types are banned by
  rule; the linter's golden manifest covers its shipped files, and it needs no
  `data.json` (defaults suffice).
- The three QuickAdd workspace choices and the loader script are shipped config —
  covered by the existing QuickAdd consistency tests plus new workspace-layout
  tests.
- Docs that described the Home/Library pair or the promised alpha.3 Project
  workspace are rewritten; Studio supersedes that workspace promise, while
  [ADR-77](77-project-gate.md) owns the later Project gate.

## Alternatives considered

**Names.** *Inbox* (for Desk) rejected: collides with the `inbox/` folder,
`inbox.base`, and the inbox card category — "open the Inbox" would be ambiguous
three ways. *Triage* rejected: mixes a medical metaphor into the rooms metaphor.
*Office* rejected: not mode-specific (everything happens in an office). *Lab*
rejected for now: reserved for a future code-experiment surface
([#369](https://github.com/eranroseman/memoria-vault/issues/369)). Desk / Library /
Studio are consistent rooms, each self-describing of its cognitive mode.

**Keep home.md in a workspace's main pane.** Rejected: the homepage plugin already
opens it on launch; pinning it in a layout makes the work surface a launchpad and
double-opens it on every load.

**Per-workspace hotkeys instead of commands/buttons.** Rejected as the only path:
hotkeys are per-device, unshippable config; commands ship in the vault and feed
both the palette and the buttons. Hotkeys remain available on top.

**Meta Bind (or raw HTML) instead of Buttons.** Rejected: Meta Bind is a much
larger surface for the same command-dispatch need; raw HTML buttons can't dispatch
Obsidian commands without custom JS. Buttons restricted to `type command` is the
minimal writing-free mechanism.

## Related

- **Files affected:** `src/.obsidian/workspaces.json`, `src/home.md`,
  `src/system/scripts/load-workspace.js`, `src/.obsidian/plugins/buttons/`,
  `src/.obsidian/plugins/quickadd/data.json`, `src/.obsidian/community-plugins.json`.
- **Related decisions:** [ADR-13](13-homepage-front-door.md) (the front door —
  unchanged; its note is now the control panel), [ADR-48](48-copi-and-agent-consolidation.md)
  (the Co-PI the right pane pins), [ADR-49](49-catalog-in-bases-linter-monitor.md)
  (catalog in Bases), [ADR-55](55-src-scaffold-populate-golden-copy.md) (golden copy
  covers the shipped plugin files), [ADR-77](77-project-gate.md) (bounded inquiry
  surface).
- **Reference:** [Obsidian workspaces](../reference/obsidian-workspaces.md),
  [Obsidian plugins](../reference/obsidian-plugins.md).


---

<!-- source: adr/69-operations-layer-naming.md -->

# ADR-69: Operations — name the deterministic layer and its four categories

## Context

The deterministic, non-LLM layer ([ADR-46](46-seven-layer-architecture.md)) is named
inconsistently. The docs call it both **"engines"** and **"Memoria's deterministic
apps"** — one concept, two words, the textbook ubiquitous-language anti-pattern (DDD).
"engine" is also not plainly self-descriptive (game/search/rules engines abound). The
five components have no shared structure: `engines/ingest/` exists, but the Cluster
engine logic lives inside `mcp/cluster_mcp.py` with no `engines/cluster/`, Search has
no directory at all, and `engines/sweeps/` mixes three different kinds of work. The
ingest entry point is the shape-named `pipeline.py`, and `engines/lib/` is a generic
catch-all. The original alpha.3 design note asked whether the work splits into
"processing/maintenance vs bookkeeping/housekeeping" — four near-overlapping words
that mis-cut the space (maintenance ≈ housekeeping; bookkeeping is a metaphor for
recording). Deriving names from what each component *does*, rather than from the
existing folder, gives a cleaner, self-descriptive vocabulary.

## Decision

Memoria's deterministic, non-LLM layer is named **Operations** (the term "engine" and
the synonym "app" are retired). The contrast with the agent layer is: **you _run_ an
operation; you _delegate_ to an agent.**

Operations group into **four categories, named by what the PI does with each one's
output**:

- **Processing** — builds and serves the knowledge base; the PI **uses** the result.
  (`ingest`, `search`, `cluster`.) Agent-reachable via an MCP facade.
- **Integrity** — detects and repairs correctness/consistency problems; the PI **acts
  on** the findings (cards/alerts). (`verify`/lint detectors, `retraction`, `golden`.)
  Cron/CI-only.
- **Cleanup** — routine, silent tidying/normalizing/archiving; the PI **never sees**
  it. (`reconcile`, `archive_inbox`, retry/stamp.) Cron-only.
- **Telemetry** — records activity and emits metrics; the PI **consults** it on demand.
  (board/telemetry export, `metrics`, session digests, `eval`.) Cron-only.

Each **leaf operation** has **one bare-verb token** (`ingest`, `search`, `cluster`,
`verify`, `lint`) used identically as its proper name, directory, module stem, and CLI
verb. The code tree is restructured by category:
`src/.memoria/operations/{processing,integrity,cleanup,telemetry}/`. Generic
shape-names are retired in the move — `ingest/pipeline.py` → a responsibility name
(`runner.py` or `catalog.py`), `lib/` dissolved, `golden.py` → `golden_restore.py`.

The rename is **decided now but executed as one atomic refactor** (see *When this
matters*), not piecemeal.

## Consequences

- Each term is self-descriptive and non-overlapping; "maintenance"/"housekeeping"
  synonyms collapse and "bookkeeping" becomes the distinct **Telemetry**.
- The four categories line up with two things already true: the **MCP-facade boundary**
  (Processing is agent-reachable; the other three are cron/CI-only) and the
  **navigation model** ([ADR-68](68-workspaces-desk-library-studio.md) / report §3) —
  Integrity → status bar + Action cards, Telemetry → pull dashboards, Cleanup →
  invisible, Processing → the knowledge itself.
- The restructure fixes the structural inconsistencies: it gives **Cluster** a real
  home (logic out of `mcp/cluster_mcp.py`, a thin façade left behind, mirroring
  `ingest_mcp.py`), gives **Search** a directory, and splits the three-category
  `sweeps/` folder.
- **High blast radius.** `engines/` is hardcoded in `tests/conftest.py`,
  `scripts/test.sh`, `scripts/e2e-smoke.sh`, `scripts/install.sh`,
  `tests/test_precommit_schema.py`, and across docs/ADRs — all must move in the same
  change, with `docs-doctor` and the test suite re-run after.
- **Excluded from any find/replace** (false positives): the `memoria-engineer` agent
  profile (a persona, not the layer), qmd's "search engine" (third-party), and the
  `PolicyEngine` class name (decide separately).
- [ADR-46](46-seven-layer-architecture.md) and every doc using "engine"/"deterministic
  apps" must be amended to the new term; this ADR governs the vocabulary, ADR-46 keeps
  the architecture.

## When this matters

The **vocabulary decision** is accepted for alpha.3 so UI work builds on settled terms
(the navigation, dashboards, and docs all reference these categories). The **code/tree
rename** serves engineering clarity, not the alpha.3 "UI build", and carries real risk
— so it is scheduled as a **dedicated refactor pass, sequenced _after_ the docs→source
link convention lands** (the alpha.3 research notes, `open-issues-research` Issue 3c)
so links aren't pinned to paths about to move. Re-judge priority each release cycle.
Cheap, non-structural parts (delete "app" from prose; define "CI invocation") can land
in alpha.3 ahead of the rename.

## Alternatives considered

- **Keep "engine," delete "app."** Cheapest (the folder and ADR-46 already use it), but
  "engine" is not plainly self-descriptive and keeps a mildly overloaded term. Retained
  only as a fallback if the rename churn proves unacceptable.
- **Two buckets — Processing vs Maintenance.** Matches the MCP-facade boundary exactly,
  but lumps "findings you act on" with "records you consult" and "silent tidying",
  losing the distinctions that drive the dashboards.
- **The note's pairing — {Processing+Maintenance} vs {Bookkeeping+Housekeeping}.** Splits
  the two synonyms (maintenance/housekeeping) into different buckets and pairs the two
  genuinely-different ops concepts (recording vs tidying); "bookkeeping" is a metaphor.
- **"service" or "tool" as the umbrella.** "service" implies an always-on RPC daemon
  (wrong for the on-demand + cron mix); "tool" collides with "MCP tool" — a new dual
  vocabulary.
- **Three categories** (fold Cleanup into Integrity). The merge was tempting only because
  "maintenance"/"housekeeping" overlap; with the self-descriptive names "Integrity" and
  "Cleanup" are obviously different work, so four crisp categories read clearer.

## Related

- **Files affected:** `src/.memoria/engines/` (→ `operations/`), `tests/conftest.py`,
  `scripts/test.sh`, `scripts/e2e-smoke.sh`, `scripts/install.sh`,
  `tests/test_precommit_schema.py`, `docs/explanation/engines/` (→ renamed),
  `docs/reference/system-actions.md`
- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md) (defines
  the layer; its "engine" term is amended here), [ADR-68](68-workspaces-desk-library-studio.md)
  (the navigation model the categories map onto)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 2, `naming-and-diataxis-audit`)


---

<!-- source: adr/70-navigation-gates-dashboards.md -->

# ADR-70: Navigation — intent-named gates, ambient maintenance, JTBD dashboards

## Context

[ADR-68](68-workspaces-desk-library-studio.md) shipped the Desk/Library/Studio
workspace *shells* under one layout contract, but the navigation *model* is
unsettled: what each workspace is for, where "the system needs you" surfaces, and
how the dashboards inside each are organized. alpha.3 is the UI build, so this needs
deciding now.

## Decision

Navigation is a set of **intent-named gates** implemented on the existing workspace
machinery. Switching a gate changes only the left-nav, the main dashboard, and where
the Co-PI is pointed — **never what an action does** (these are views/spaces, not
modes). There are **three core gates now** (an Action/"what needs me" gate, a
Sources/Library gate, a Knowledge gate), plus the **Project gate accepted in
[ADR-77](77-project-gate.md)**; the top level never exceeds five.

**System health is ambient, not a gate.** A status-bar indicator carries the ambient
signal; anything *actionable* surfaces as a card in the Action queue (point-of-action,
not a separate destination); a pull-based health detail view is reachable on demand
for deliberate housekeeping.

**Dashboards are organized by Jobs-To-Be-Done.** Each gate's dashboard answers that
gate's question: the Action dashboard is strictly action-first (every card carries its
next action; non-actionable items don't appear), while Library and Knowledge lean
object-first for browsing.

## Consequences

- Caps cognitive load (3 gates now, progressive disclosure for depth) and keeps
  maintenance from ever being a forced "wall of yellow."
- Maps onto [ADR-69](69-operations-layer-naming.md): **Integrity** findings → status
  bar + Action cards; **Telemetry** → pull dashboards; **Cleanup** → invisible;
  **Processing** → the knowledge itself.
- Base Board (kanban over Bases) is adopted only as a **version-pinned sandbox pilot**,
  not a committed dependency — native Bases has no board view yet.
- Extends ADR-68 rather than replacing it; Studio remains the drafting shell, and
  [ADR-77](77-project-gate.md) owns the Project gate's bounded-inquiry surface.

## When this matters

alpha.3 (the UI build). The Project gate is now accepted by
[ADR-77](77-project-gate.md); revisit the gate count only if a fifth top-level
intent earns a concrete job.

## Alternatives considered

- **A dedicated Maintenance gate.** Rejected — every authority (Google SRE, NN/g, Calm
  Technology) treats unconditional "everything not-green" surfacing as the cause of
  alert fatigue; VS Code/GitHub/Datadog all decline to promote "problems" to a forced
  destination.
- **Five gates now.** Rejected — sits at the upper bound after the Project gate;
  spend the remaining cognitive budget on depth within the four gates.
- **A single unified home dashboard across gates.** Rejected — violates "show only what
  this job needs" and tends to overcrowd.

## Related

- **Related decisions / Depends on:** [ADR-68](68-workspaces-desk-library-studio.md)
  (the shells), [ADR-69](69-operations-layer-naming.md) (the categories the dashboards
  map onto), [ADR-77](77-project-gate.md) (the fourth gate)
- **Implementing issues:** #467 (JTBD dashboards + intent-named gates), #375 (status-bar
  ambient indicator), #380 (assist surface), #145 (property display)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 1,
  `ui-design-research-report` §3–§4)


---

<!-- source: adr/71-structured-capture-forms.md -->

# ADR-71: Structured capture — forms at entry, the Linter as authority, one schema per type

## Context

Note creation is template-based free text: there is no form abstraction, so
instructional text leaks into the saved note; there is no per-type required-field
enforcement; and controlled vocabularies (e.g. the lifecycle state) are typed as free
text with no constraint. The deterministic Linter already validates the vault
([ADR-49](49-catalog-in-bases-linter-monitor.md)).

## Decision

Human capture goes through a **form** (the Modal Forms plugin) with typed fields and
**controlled-vocabulary controls** — for a small fixed set such as the lifecycle state
(`proposed`/`current`/`archived`), radio buttons rather than a dropdown — and with help
text living **in the form, not the saved note**.

The **deterministic Linter remains the single enforcement authority**: agents, the API,
and bulk edits all create notes outside any form, so the Linter (not the form) is what
guarantees correctness. Both the form's controlled vocabularies and the Linter's
allowed-value checks **derive from one per-type schema** in `.memoria/schemas/`, so the
two layers cannot diverge. Memoria is **strict, not liberal**: an unknown value for a
fixed-set field is rejected, not coerced.

## Consequences

- Prevention at entry (the form) plus detection everywhere (the Linter) — defense in
  depth, with one schema as the single source of truth.
- Adds Modal Forms as a bundled plugin; capture commands route through it.
- Help text and field labels stop polluting note bodies.
- Enforcement stays where it already lives (the Linter), so no second system of record.

## When this matters

alpha.3 (capture is the core UI loop).

## Alternatives considered

- **Lint-only (status quo).** Detection, not prevention; bad data exists transiently and
  help text leaks into notes.
- **Form-only.** Client-side, therefore bypassable by agents/API/bulk; doesn't cover
  non-form creation paths.
- **In-panel enum widget (e.g. Better Properties).** Gives a native dropdown in the
  Properties panel but is off-store and leans on undocumented Obsidian internals — a
  version-pinned sandbox pilot at most, not a baseline dependency.

## Related

- **Related decisions / Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md)
  (the Linter is the integrity authority), [ADR-30](30-deterministic-ingest-pipeline.md)
  (the non-form ingest write path)
- **Implementing issues:** #183 (Obsidian forms for structured capture), #145 (property
  display / lifecycle visibility)
- **Source discussion:** the alpha.3 research notes (`ui-design-research-report` §2,
  `open-issues-research` Issue 4b)


---

<!-- source: adr/72-command-surfacing.md -->

# ADR-72: Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive

## Context

Some Memoria actions were historically reachable only by asking the Co-PI, and
Obsidian core has no native way to place an arbitrary command in the ribbon. The
product principle is that every feature is directly PI-accessible from the Obsidian
UI; the Co-PI is an escalation for genuine two-way conversation, never the only path
to a routine action.

## Decision

**Every routine Memoria action is reachable directly from the Obsidian UI without the
Co-PI.** Native hotkeys and native command-palette pinning cover most surfaces;
**Commander** is adopted to place commands in the ribbon / page-header / status-bar
(the one genuine gap in core); **Slash Commander** is optional for an in-editor `/`
menu.

The Co-PI remains additive. An action may be Co-PI-only only when the interaction
itself is the product: synchronous, read-only dialogue that depends on back-and-forth
judgment, the Co-PI's memory loop, or interactive persona tuning. If the outcome is a
card, note, draft, report, capture, resolved Inbox item, or any other durable artifact,
there must be a direct command/palette/terminal route, and user-facing docs must name
that route beside any Co-PI phrasing.

## Consequences

- Reaffirms and operationalizes the PI-direct-access rule; the Co-PI is never a
  single point of access for a deterministic or durable action.
- Requires docs to explain any Co-PI-only exception as conversation-bound rather than
  action-bound.
- Adds Commander as a bundled plugin (pairs with the existing QuickAdd commands).
- Explicitly rejects Shell Commands (arbitrary local execution — violates the MCP-only
  sandbox) and Better Command Palette (unmaintained) for this role.

## When this matters

alpha.3 (the daily interaction surface).

## Alternatives considered

- **Co-PI-only invocation.** Rejected — violates direct access and makes routine actions
  depend on an LLM round-trip.
- **Native-only (no plugin).** Covers hotkeys and palette pinning but cannot place a
  command in the ribbon — the surfacing gap Commander fills.

## Related

- **Related decisions / Depends on:** [ADR-48](48-copi-and-agent-consolidation.md)
  (one Co-PI fronts everything)
- **Implementing issues:** #461 (adopt Commander), #380 (assist surface from
  palette/pane/selection)
- **Source discussion:** the alpha.3 research notes (`ui-design-research-report` §1,
  Category 10 plugin matrix)


---

<!-- source: adr/73-docs-reference-conventions.md -->

# ADR-73: Documentation references — source links, ADR links, and per-operation Diátaxis split

## Context

The docs site is Jekyll + just-the-docs on GitHub Pages, organized by Diátaxis. Three
recurring defects: relative links from docs into `src/` break on the published site
(`src/` is outside the Jekyll source root, so they 404 at any path depth); stale
`(D41)`-style references point at deleted design docs; and complex subsystems mix
procedural reference with rationale on one page (and even document more than one
subject).

## Decision

1. **Never link into `src/` from a published page.** Reference a source file as an
   **inline-code path** (`` `src/.memoria/…` ``) by default; use an **absolute,
   tag-pinned** `https://github.com/eranroseman/memoria-vault/blob/<tag>/…` URL only
   when a click genuinely adds value. `docs-doctor` blocks published→`src/` relative
   links via `check_site_local_links`.
2. **ADR references stay out of tutorial / how-to / reference body text and
   subheadings.** They are allowed inline within **explanation** pages and in an
   optional per-page footer **"Decisions"** section, always as **title-text links** —
   never bare `(ADR-NN)` codes. `docs-doctor` enforces the bare `(ADR-NN)` ban;
   the Diátaxis placement rule remains a manual documentation convention.
   Bare `(D##)` references are purged from published user-facing prose, but may
   remain in ADR history where they are part of the decision record.
3. **Complex operations get a procedural reference page and a separate rationale
   explanation page** (Diátaxis "work vs study"), cross-linked with Django's
   "link, don't repeat" discipline so each fact has one home. Simple operations may keep
   a one-paragraph "Why" inline.

## Consequences

- Source references survive the engines→operations rename ([ADR-69](69-operations-layer-naming.md)),
  because inline-code paths and tag-pinned URLs don't depend on the live relative tree.
- Cleaner prose; ADR traceability preserved without clutter.
- Builds on [ADR-12](12-obsidian-linter-reference-only.md) (docs tooling is advisory);
  the new structural rule is enforced by docs-doctor, not obsidian-linter.

## When this matters

alpha.3 (docs hygiene), sequenced **before** the engines→operations code rename so links
aren't pinned to paths about to move.

## Alternatives considered

- **`blob/main` links.** Always current but silently break on rename/delete and drift on
  line anchors; reserved only for "browse this directory" links.
- **Keep relative `src/` links.** They resolve on disk and on github.com but are dead on
  the published site — the defect this ADR removes.

## Related

- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md),
  [ADR-12](12-obsidian-linter-reference-only.md), [ADR-69](69-operations-layer-naming.md)
- **Implementing issues:** #464 (docs hygiene sweep), #443 (explanation pages describe
  unbuilt behavior)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 3,
  `naming-and-diataxis-audit` Part 2)


---

<!-- source: adr/74-pinned-obsidian-plugin-supply-chain.md -->

# ADR-74: Manage bundled Obsidian plugins with a pinned provenance manifest

## Context

Memoria commits the built files for its required Obsidian plugins under
`src/.obsidian/plugins/` so a fresh vault works without downloading plugins at
install time. This supports the repo-as-install-unit and offline, reproducible
vault image chosen in [ADR-26](26-repo-as-install-unit.md) and
[ADR-55](55-src-scaffold-populate-golden-copy.md). The repository now records a
static, machine-readable provenance lock for those bundled artifacts in
`src/.obsidian/plugin-provenance-lock.json`: plugin identity, upstream repository,
pinned local version, artifact SHA-256 digests, license assertion, and local-patch
status. That lock makes manual review auditable, but update automation is still
future work: CI validates the static lock against committed artifacts, while a
repository updater that fetches and replaces upstream-owned artifacts remains a
later increment.

## Decision

Memoria keeps bundled Obsidian plugin build artifacts committed in
`src/.obsidian/plugins/`; installation remains network-independent and does not
download executable plugin code. The accepted supply-chain model is incremental:

- A versioned lock manifest beside the plugin inventory. For each bundled
  plugin it records the plugin ID, upstream repository, pinned release tag or
  commit, source/release URL, artifact SHA-256 digests, license, and whether the
  checked-in files are unmodified, patched, or Memoria-authored.
- A CI provenance doctor. It proves the lock matches committed
  artifacts, every enabled bundled plugin is represented exactly once, declared
  files exist, and no undeclared executable artifact has entered a plugin directory.
- A strict ownership split: `main.js`, upstream `manifest.json`, and upstream
  `styles.css` are vendored artifacts unless the lock says otherwise;
  Memoria-authored `data.json`, `.example` files, and configuration overlays are
  maintained separately and are never overwritten by the updater.
- A repository updater as a later increment, after the CI doctor is stable. It
  downloads into a temporary directory, verifies the declared upstream identity and
  pinned version, computes the locked digests, and replaces only upstream-owned
  build artifacts after explicit review.
- Explicit patch provenance. A locally modified plugin must use a maintained
  fork or a reviewable patch recorded by the lock; editing minified build output
  without reproducible source or patch history is not allowed.

The lock manifest and CI doctor are current behavior. Updater automation remains
sequenced implementation work, after the doctor is stable, so drift is detectable
before any automation can rewrite artifacts.

## Consequences

- Fresh installs remain batteries-included and deterministic even without
  network access.
- Plugin updates become reviewable supply-chain changes rather than opaque
  binary replacements.
- CI can detect partial upgrades, accidental local edits, missing provenance,
  and drift between the enabled-plugin list and shipped artifacts.
- The lock and updater add maintenance work, particularly for plugins whose
  upstream releases do not publish stable assets or checksums.
- A checksum proves that the repository contains the reviewed pinned artifact;
  by itself it does not establish that the upstream publisher or release was
  trustworthy. Version selection and upstream review remain human decisions.
- Memoria must define migration behavior for renamed plugin IDs and upstream
  manifests before automation can safely prune old plugin directories.

## Current implementation mapping

The lock is implemented in `src/.obsidian/plugin-provenance-lock.json` and
validated by `scripts/plugin_provenance_doctor.py` in the required lint and local
L0 gates. `tests/test_plugin_provenance.py` shares the doctor core so test
fixtures and CI enforce the same contract: enabled-plugin coverage, exactly one
lock entry per bundled plugin directory, manifest-version parity, declared
upstream fields, SHA-256 digests for committed artifact files, and rejection of
undeclared executable artifacts. This is enough for manual audit and review of
vendored plugin changes, but it is not yet updater automation. Only after that
doctor is stable should Memoria add an updater that downloads and stages new
upstream artifacts for review.

## When this matters

Revisit the remaining increments at each release cadence, with higher priority when
bundled plugin artifacts change regularly, a plugin update cannot be traced
confidently to an upstream release, a security advisory affects a bundled plugin,
local patches become necessary, or another maintainer needs to reproduce an update
without private context. These are scheduling signals, not automatic adoption gates.

## Alternatives considered

**Download plugins during installation.** This reduces repository size and
always fetches from a declared source, but makes installation network-dependent,
allows upstream disappearance or mutable releases to break old Memoria
versions, and moves executable supply-chain risk into the user installation
path. It conflicts with the repo-as-install-unit model, so committed pinned
artifacts remain the recommendation.

**Use Obsidian's community-plugin installer after first launch.** This delegates
updates to the standard UI and avoids vendoring code, but removes the
batteries-included first run and makes the runtime state depend on manual steps
and whatever version is current at installation time. It is appropriate for
recommended plugins, not Memoria's required set.

**Track plugin repositories as Git submodules.** Submodules provide commit
provenance, but Obsidian loads built release artifacts rather than arbitrary
source trees; many plugin repositories require a Node build with version-specific
tooling. Submodules would add contributor friction without eliminating the need
to build, verify, and commit the exact runtime files.

**Continue manual vendoring without a manifest.** This had the lowest immediate
implementation cost before ADR-74, but would leave updates non-reproducible and
weaken review of executable third-party changes. It is not the recommended
long-term model.

## Related

- **Files affected:** [`src/.obsidian/plugins/`](https://github.com/eranroseman/memoria-vault/tree/main/src/.obsidian/plugins),
  [`scripts/plugin_provenance_doctor.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/plugin_provenance_doctor.py),
  [Obsidian plugin reference](../reference/obsidian-plugins.md)
- **Related decisions / Depends on:** [ADR-26](26-repo-as-install-unit.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-67](67-drift-procedures-keep-or-retire.md)
- **Tracking issue:** [#686](https://github.com/eranroseman/memoria-vault/issues/686)
  — CI provenance doctor before updater automation.


---

<!-- source: adr/75-github-project-fields-and-release-sub-issues.md -->

# ADR-75: Use GitHub Project fields and release sub-issues for live work state

## Context

[ADR-45](45-release-management-model.md) moved release readiness out of
hand-maintained markdown tables and into GitHub. The first shape used a single
"Release vX.Y" tracking issue as a gate checklist. That removed file drift, but it
made each gate a checkbox rather than a work item with its own owner, comments,
evidence, blocking discussion, and Project metadata. In parallel, labels had started
to carry too many meanings: type, area, priority, triage state, and bot automation.
That made issue search noisy and made release planning depend on conventions that
GitHub Projects models more directly.

## Decision

Memoria uses GitHub issues as the atomic unit of work, the **Memoria Issue Tracker**
Project as the live planning surface, milestones as release scope, and ADRs as the
decision record. Project fields carry `Status`, `Area`, `Type`, and `Priority`;
labels stay minimal and are reserved for repo-wide search chips or bot automation.
Release readiness lives in a **"Release vX.Y" parent issue** with one sub-issue per
gate or validation stage, instead of a single checklist embedded in the release
plan or parent issue body.

> **Current field set (see [Issue tracking](../contributing/issue-tracking.md)):**
> the live Project carries `Status` and `Readiness` only. The original `Area`, `Type`,
> and `Priority` fields were retired as unused planning overhead, and `Readiness` was
> added to separate "is it decided" from "is it ready to build." The decision to model
> planning state in Project fields — not labels or markdown — is unchanged.

## Consequences

- Each release gate/stage can have its own evidence trail, assignee, comments, and
  close condition.
- The Project table becomes the source for triage, priority, and release views;
  process docs point to it instead of copying its state.
- Labels are simpler and less likely to conflict with Project fields or automation.
- Some live state remains GitHub-only. That is acceptable for planning metadata, while
  durable rationale still belongs in ADRs and durable process prose remains in `docs/`.
- GitHub Project field configuration is not versioned in this repository, so
  `docs/contributing/issue-tracking.md` documents the expected field vocabulary and
  colors for human repair.

## Alternatives considered

**Keep the single release tracking issue checklist.** Rejected as too flat: it shows
progress, but it does not give each gate a first-class place for evidence, ownership,
or blocked discussion.

**Use labels for Type, Area, Status, and Priority.** Rejected because labels are global
repo search metadata and bot hooks, not a planning schema. Project fields model this
more directly and avoid a large label taxonomy.

**Track planning state in markdown under `docs/`.** Rejected for live state because it
reintroduces the drift class ADR-45 removed. Markdown remains the home for durable
process and decision prose, not the live board.

## Related

- **Workflows affected:** [Issue tracking](../contributing/issue-tracking.md),
  [Releasing](../releasing/README.md)
- **Related decisions / Depends on:** [ADR-45](45-release-management-model.md)


---

<!-- source: adr/76-versioned-vault-release-reconciling-installer.md -->

# ADR-76: Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer

## Context

The thing Memoria deploys is **a configured vault, not a Python package**. The
seven subtrees the installer lays down today are several things wearing one rsync:
importable Python (`operations/`, `mcp/`, `memoria_runtime/`, `lib/`), authored
boundary content that must track the release (the policy-gate shim, baseline
schemas, cron wrappers, shipped lane policy), PI-customizable authored content
(`SOUL.md`/`SKILL.md`, PI-added schema types, per-vault lane tuning), host-side
Hermes config rendered into `~/.hermes/profiles/<profile>/`, and per-vault state
(`logs/`, `.env`, the golden store, notes).

The obvious framing — "make the runtime an installable wheel; the vault holds data, not source" — optimizes only the first of those three and lets that artifact define the whole deployment story. It does not hold up: a wheel cannot carry `SOUL.md`/`SKILL.md`, the `plugin.yaml` gate shim (loaded **by the MCP host in its own interpreter**, not the venv), or the cron wrappers, so "vault holds data, not source" is unreachable — much of what stays in the vault is authored source by necessity. It also imports costs the audience does not yet justify (a prebuilt-wheel supply-chain trust surface, non-transactional `pip --upgrade` rollback) and turns the policy-gate reachability question into an open execution blocker. (The `engines → operations` rename that earlier framings sequenced *before* packaging has since landed in [#536](https://github.com/eranroseman/memoria-vault/issues/494), so that sequencing concern is already spent.)

Designing from scratch, the spine inverts: the unit is a **versioned vault release**, and the installer is a **pure function of `(release_root, vault_path)`** that reconciles each layer idempotently. The Python-package work the wheel framing wanted is still right — it is just *how the code layer lands inside the release*, not the spine itself.

This decision does **not** change integrity *protection*. A common misconception — that [ADR-55](55-src-scaffold-populate-golden-copy.md)'s golden copy protects the runtime code — is false: `golden_restore.py`'s manifest covers `system/{templates,dashboards,patterns,eval,scripts}/`, three system files, and three `.obsidian` config files, with **no `.memoria/` prefix**. Code-integrity protection is the MCP-only sandbox (agents cannot write files; [ADR-46](46-seven-layer-architecture.md)) plus Git as source of truth. This design *extends* ADR-55's manifest idea to cover the code and authored layers for **verification**, but leaves the protection mechanism untouched.

## Decision

Memoria moves from repo-subtree deployment to a single versioned vault release
deployed by a source-agnostic reconciling installer. Two decisions are
load-bearing; everything else follows from them.

**Accepted scope.** This records the deployment *spine* as decided; the work is
staged (see *Migration* and *Guard* below) and scheduling lives in the tracking
issue. The import-hygiene package half (step 2 — package-root install,
console scripts, deleting the `sys.path`/`__file__` bootstraps) and the in-process
policy core (decision 2) are cleared to proceed on their own merits. The
tarball/signing/copy-install distribution half (decision 1's no-checkout path)
stays deferred — readiness `Later` — until a no-checkout audience is real; git-tag
remains the delivery posture until then.

### Load-bearing decision 1 — one versioned release, laid down by a reconciling installer that is layered by lifecycle

The installer is `install(release_root, vault_path)`: an idempotent function that does not care whether `release_root` is a checked-out Git tag or an unpacked tarball. It reconciles each layer by its own lifecycle:

| Layer | Examples | Lifecycle | How the installer handles it |
|---|---|---|---|
| **Code** | runtime (`operations`, `mcp`, `runtime`, `lib`), the extracted policy core | versioned; never hand-edited; recovery = reinstall | installed into `<vault>/.memoria/.venv` as the `memoria` package |
| **Authored boundary / contract** | gate shim, shipped `lane-overrides/<lane>.yaml`, baseline schemas, cron wrappers | release-owned; a security or schema fix must land | release-wins: apply the release, back up/report prior drift, never preserve-live |
| **PI configuration** | `SOUL.md`/`SKILL.md`, PI-added schema types, per-vault lane overlay | human-owned preference inside release ceilings | customize-preserve: preserve live changes, surface conflicts, never auto-merge over the PI |
| **Host-side config** | rendered `~/.hermes/profiles/<profile>/config.yaml` | managed at install; lives outside the vault | render from profile templates with `{{PYTHON}}`, `{{VAULT_PATH}}`, `{{QMD}}`, and model/Obsidian env refs |
| **Per-vault state** | notes, `logs/`, `.env`, golden store | never touched by an upgrade | excluded from the release manifest |

The shipped lane policy is boundary/contract, not state: release policy tightening must
land. PI lane tuning therefore moves to a separate preserved overlay merged at
load time with **tighten-only** semantics: an overlay may add denies or remove
allows, but it may not widen past the shipped baseline. The exact overlay path and
merge code are part of this proposal's implementation work.

The release carries **one version** (`memoria.__version__`) and a
**content-addressable manifest** (SHA per file) over code plus release-owned
authored files. The manifest is one mechanism with per-layer verdicts: code
mismatch is tamper/reinstall, boundary mismatch is restore/apply-release, and PI
configuration mismatch is expected customization or conflict. It generalizes
[ADR-55](55-src-scaffold-populate-golden-copy.md) without pretending all files have
the same lifecycle.

The runtime is a real, single-rooted `memoria` package (`pyproject.toml` as the one source of truth for build, dependency tiers, pytest, ruff, and `[project.scripts]` console entry points; the three `requirements*.txt` collapse into named groups). Deployed installs use `pip install <release_root>` into the vault venv, not editable mode: the one-line installer may clone to a staging directory and delete it after the vault is populated, so an editable install would leave a dangling import root. Contributor dev setup may still use `pip install -e .` for editor/type-checker convenience. No prebuilt `.whl` is shipped; the wheel is built in CI solely as a packaging-correctness check (it exercises `package_data` and `__init__.py` gaps that editable installs do not).

### Load-bearing decision 2 — extract a genuine, tiny, standalone policy core

The policy-gate runs in the MCP host's process, whose interpreter the installer
does not pin. The small, dependency-free **policy core** (the mutating-action set,
path matching, lane loading, and review-gated decision logic) now lives under the
installed package path `memoria/runtime/policy/`, imported by both the MCP servers
and the gate hook. What remains for the full versioned-release spine is tightening
the host import story so the gate shim imports the installed core directly and
fails closed if that import is unavailable.

The preferred implementation is for the gate to import the **single installed
policy core** from the vault venv's package install, not a committed duplicate. The
import chain from `memoria` to `memoria.runtime.policy` must stay stdlib-only and
is guarded by a bare-interpreter CI test. If the host cannot import the installed
core, the gate fails closed. A generated vendored fallback is allowed only if
in-process import proves infeasible; a hand-maintained vendored copy is rejected
because it can drift at authoring time.

This makes the hard-deny security boundary small and auditable while avoiding a
second policy copy. The failure mode is explicit: a boundary that cannot load its
policy denies rather than waves calls through.

### Delivery

Git tag now (`git checkout vX && ./install.sh <vault>`): versioned, reproducible, transparent, zero build pipeline. When an audience that cannot run a checkout appears, the *same* installer consumes a hash-verified (eventually signed) release tarball — the spine does not change, only the source of `release_root`. Rollback is `git checkout <prev-tag> && ./install.sh`; no wheel retention or `--force-reinstall` dance. Vault resolution stays a parameter (`resolve_vault()` is already arg→env, never `__file__`).

**Migration is staged and ordered:**

1. **Landed (alpha.4) ✅:** a repo-root `pyproject.toml` carried pytest and ruff
   tooling, and the `conftest.py` `sys.path` block was removed.
2. **Package spine (alpha.8, #727):** add the `[project]` table, introduce the
   `memoria.*` import root, install the release root into the vault venv, and migrate the
   dependency-free policy path first. Legacy loose-module `pythonpath` entries remain
   until their modules move behind the package root in later slices.
3. **Shared runtime helpers (alpha.8, #728):** centralize dependency-light
   frontmatter, JSONL, timestamp, and vault path primitives under
   `memoria.runtime.{vaultio,jsonl,time,paths}`; keep MCP `_shared.py` as a
   compatibility facade while operations migrate to the package root.
4. **Packaging continuation:** delete the remaining runtime `__file__`/`sys.path`
   bootstraps as modules move, then wire console scripts where they replace existing
   file entrypoints. This half stands on its own import-hygiene merits, independent of
   the delivery change.
5. **Then (the spine):** flip deployment to the reconciling installer over a versioned release; have the gate shim import the installed policy core (decision 2) and drop its `sys.path` reach-through; introduce the release manifest and the tighten-only lane overlay.

## Consequences

- **The full deployable is modeled, not just the Python third.** Boundary authored content, PI configuration, host config, and state have different homes and upgrade paths instead of being smuggled through "data."
- **The headline invariant becomes true and honest:** *the runtime code* installs into the venv; profiles, the host-loaded gate shim, schemas, and cron wrappers remain vault-side authored content by design — no contradiction to chase.
- **The gate-reachability question becomes settled architecture, not an open blocker.** The policy-core extraction is a one-time refactor that removes version skew rather than parking it; the gate stays in-process (no hot-path IPC hop, no fail-closed availability dependency on a running server).
- **One manifest replaces scattered worries** with a content-addressable source of truth for "what should be on disk," while still reporting different verdicts for code, boundary files, and PI configuration.
- **The shipped-wheel's premature costs are dropped:** no shipped-artifact supply-chain trust surface, no non-transactional `pip --upgrade` rollback problem, no `site-packages` transparency regression on the primary machine.
- **Multi-machine falls out for free** ([ADR-63](63-multi-machine-deployment.md)): one versioned release, N vaults, state per-machine; more multi-machine-friendly than either rsync-from-checkout or a bare wheel.
- **Entry-point audit (carried forward):** several console scripts are notional — `memoria-lint` and `memoria-eval` are each "pick one canonical entry" decisions (the linter `main()` is in `detectors.py`; eval spans `eval_dispatch.py`/`eval_score.py`); the rest need `main()` signature/return confirmation (`reconcile.main()` returns an `int` exit code, which `[project.scripts]` handles correctly).
- **Costs:** the reconciling installer is more logic than `cp -R`/rsync; the boundary-vs-PI-config classification, tighten-only lane overlay, import-purity guard, and release manifest must be designed and verified in CI. **Tension with [ADR-26](26-repo-as-install-unit.md):** the install unit shifts from the rsynced repo subtree to a versioned release — the repo stays the source of truth, what is *deployed* changes; reconcile on execution.

## When this matters

Context for the cadence review, not a gate — pick this up when **any** holds:

- **Distribution:** Memoria ships to operators who cannot run from a Git checkout — the tarball delivery and copy-install path become live (the git-tag path needs none of this).
- **Support burden:** the `sys.path`/`__file__` bootstrapping (17 sites across 13 files) or the three-way `requirements*.txt` split becomes a recurring source of import/CI breakage — the package-install half (step 2) is the relief and can land first.
- **Boundary risk:** any incident or near-miss where the gate and servers could run divergent policy — the policy-core extraction moves to the front.

**Guard:** the step-1 tooling `pyproject.toml` and the step-2 packaging (package install, deleting the conftest/`__file__` import hacks) are safe to pursue on their own merits. Do **not** stand up tarball publishing or signing before a no-checkout audience is real — git-tag is the correct posture until then, and the rest costs nothing to defer.

## Alternatives considered

- **Package the runtime as a shipped wheel; vault holds data, not source.** The first-instinct framing, and correct about import hygiene — but wrong as the deployment spine: it models only the Python third, cannot carry the authored two-thirds (profiles, host-loaded gate shim, cron), makes "vault holds no source" unreachable, adds a supply-chain trust surface and non-atomic rollback before any audience needs them, and leaves gate-skew as an open execution blocker. This decision keeps its package work (as the code layer's install mechanism) and discards the wheel as the *shipped artifact*.
- **Status quo: rsync from a checkout.** Fine while the audience is the PI, but unversioned, prone to the renamed-file-lingering hazard the scoped `--delete` pass exists to paper over, and with no story for gate/server co-versioning beyond "they came from one tree." Git-tag + reconciling installer keeps the transparency while adding versioning and a real manifest.
- **Gate calls the policy server over IPC.** Structurally skew-free, but adds per-tool-call latency on the hot path and a fail-closed availability dependency (a crashed policy server bricks the agent). Importing the tiny installed core achieves skew-freedom without either cost; IPC remains a fallback only if in-process import proves infeasible in the host interpreter.

## Related

- **Tracking issue:** [#521](https://github.com/eranroseman/memoria-vault/issues/521) — proposal shaping and scheduling live on the issue.
- **Origin:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) (research) and
  implementation tracker [#521](https://github.com/eranroseman/memoria-vault/issues/521).
- **Depends on:** [ADR-44](44-tests-in-pytest-tree.md) (the conftest `sys.path` block the package work deletes); [ADR-46](46-seven-layer-architecture.md) (the MCP-only sandbox that *is* integrity protection); [ADR-55](55-src-scaffold-populate-golden-copy.md) (the golden manifest this generalizes into the release manifest); [ADR-69](69-operations-layer-naming.md) (operations layout, now landed); [ADR-73](73-docs-reference-conventions.md) (reference conventions for moved paths).
- **In tension with:** [ADR-26](26-repo-as-install-unit.md) (install unit becomes a versioned release, not the repo subtree).
- **Strengthens:** [ADR-63](63-multi-machine-deployment.md) — one versioned release across N vaults is the natural multi-machine substrate.


---

<!-- source: adr/77-project-gate.md -->

# ADR-77: Project gate

## Context

[ADR-70](70-navigation-gates-dashboards.md) reserved the fourth top-level gate for
Project work, and [ADR-68](68-workspaces-desk-library-studio.md) left `projects/`
empty while Studio carried drafting. alpha.5 is the first checkpoint where that
slot has a concrete job: bounded inquiry that turns catalog/source work into a
defended or falsified thesis. The gate must preserve Memoria's deepest boundary:
agents propose, deterministic Operations derive views, and the PI promotes.

## Decision

Memoria adopts a **Project gate** as the fourth intent-named gate. A project is a
bounded research inquiry rooted in a project note and one thesis target. The gate
surfaces the project question, thesis, descriptive map, argument graph, ranked
gaps, saturation signal, and outline path from Obsidian, using the existing
workspace machinery and a custom Bases view where the Obsidian API permits it.

All load-bearing Project logic is deterministic: map traversal, structural
impact, graph maturity, saturation, and index-note materialization are Operations
over vault state. Agents may discover sources, propose gaps, and draft outlines,
but the gate never asks an LLM to judge truth, infer maturity, or promote a
thesis. The PI remains the author of the question and thesis and the only actor
who can promote the thesis to `current`.

The conservative graph-maturity default is a connected thesis-rooted component
with at least five addressed relations, including at least one `supports` edge
and at least one `contradicts` edge. The default materialization shape is a
single generated project index note read by the custom Bases view; per-note
stamps are reserved for cases where a later implementation cannot use the view.

> **Implementation status (2026-06-21).** The deterministic gate logic ships in
> Operations: thesis-rooted traversal, structural impact, maturity thresholds,
> saturation, and index-note materialization are implemented and tested. The custom
> `registerBasesView` surface remains the experimental part; the shipped Obsidian
> surface is the `.base` dashboard plus Markdown project index notes.

## Consequences

- Project becomes a first-class navigation destination rather than a promise
  hidden behind Studio.
- The gate can argue for stopping when the argument is saturated, but only over
  relations the PI or gated proposals have actually supplied. Determinism makes
  the computation repeatable, not the conclusion true.
- Falsifying a thesis is a finished project result: a `retracted` thesis plus the
  argument subgraph that refuted it is preserved rather than treated as failure.
- The implementation sequence is structural-first: schemas and templates, then
  graph/impact Operations, then gap/saturation logic, then the Obsidian surface.
- The custom Bases view remains a version-pinned pilot because `registerBasesView`
  exists in the published Obsidian API but remains a narrower extension surface
  than ordinary Markdown dashboards.

## Alternatives considered

**Keep Project as Studio-only drafting.** Rejected: Studio answers "what am I
writing?", while Project answers "what bounded inquiry am I driving to an
answer?" Merging them keeps the missing middle between map and outline.

**Use agent judgment for maturity and saturation.** Rejected: it would turn a
navigation gate into a hidden inference layer. The gate's value is that its logic
is inspectable and repeatable even when the graph inputs are incomplete.

**Materialize derived state onto every note by default.** Rejected: it creates
write amplification and stale frontmatter risk. A generated project index is the
default; per-note stamps need a specific rendering constraint to justify them.

## Related

- **Files affected:** `src/projects/`, `src/system/templates/`,
  `src/.memoria/schemas/types/`, `src/.memoria/operations/`, workspace/dashboard
  files.
- **Related decisions / Depends on:** [ADR-68](68-workspaces-desk-library-studio.md),
  [ADR-70](70-navigation-gates-dashboards.md),
  [ADR-78](78-thesis-note-type.md),
  [ADR-79](79-argument-graph-and-warrant.md).
- **Source discussion:** alpha.5 workstream
  [#577](https://github.com/eranroseman/memoria-vault/issues/577), spike workstream
  [#576](https://github.com/eranroseman/memoria-vault/issues/576), and merged implementation
  PRs [#603](https://github.com/eranroseman/memoria-vault/pull/603),
  [#604](https://github.com/eranroseman/memoria-vault/pull/604),
  [#605](https://github.com/eranroseman/memoria-vault/pull/605),
  [#606](https://github.com/eranroseman/memoria-vault/pull/606),
  [#607](https://github.com/eranroseman/memoria-vault/pull/607).


---

<!-- source: adr/78-thesis-note-type.md -->

# ADR-78: Thesis note type

## Context

Project work needs a provisional position under test. A `claim` cannot carry that
role: claim notes are born canonical and their lifecycle is `current →
retracted → archived`. Treating a tentative answer as a claim would manufacture
the exact premature-thesis and sunk-cost pressure the Project gate is meant to
avoid.

## Decision

Memoria adds **`thesis` as its own note type**. A thesis is the project anchor
whose lifecycle runs `proposed → provisional → current → retracted → archived`;
the transition to `current` is review-gated. The project question remains a
separate project note: the question is interrogative and scoped, while the thesis
is the declarative tentative answer to that question.

A project may be in thesis-driven mode or explicit survey mode. In thesis-driven
mode the project drives a thesis to `current` or `retracted`; in survey mode the
project produces a scoped map without pretending there is a defended answer yet.
The project container does not need a parallel status field: its visible state is
derived from the thesis lifecycle and output mode.

## Consequences

- "No thesis yet" and "provisional thesis" become honest, visible states rather
  than hidden drafting conventions.
- A falsified thesis is a valid result. `retracted` records that the inquiry
  answered "no" or that the current position died under evidence.
- The schema must reject a born-`current` thesis while allowing `proposed` and
  `provisional` work.
- Claim notes stay canonical. If a defended thesis later needs to become an
  ordinary claim note, that is an explicit promotion/migration step rather than a
  disguised lifecycle shortcut.

> **Implementation status (2026-06-21).** The shipped validator approximates the
> born-`current` guard by requiring promotion provenance (`promoted_at`) whenever a
> thesis has `lifecycle: current`; no validator currently reads `initial_lifecycle`
> to reconstruct historical birth state. The live invariant is therefore "current
> requires promotion evidence," not a forensic check that the note was never born
> current.

## Alternatives considered

**Model thesis as a claim with extra status.** Rejected: it contradicts the claim
schema and splits maturity between `lifecycle` and a bespoke field.

**Let the project question become the thesis.** Rejected: questions and theses
are different artifacts. A changed question triggers project staleness; a changed
thesis is ordinary hypothesis revision inside a stable inquiry.

**Require every project to have a thesis immediately.** Rejected: it biases the
system toward premature argument. Survey mode and the "no thesis yet" state are
necessary escape valves.

## Related

- **Files affected:** `src/.memoria/schemas/types/thesis.yaml`,
  `src/.memoria/schemas/types/project.yaml`, `src/system/templates/`,
  `src/projects/`.
- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-77](77-project-gate.md).
- **Source discussion:** alpha.5 schema workstream
  [#578](https://github.com/eranroseman/memoria-vault/issues/578) and merged implementation
  PR [#604](https://github.com/eranroseman/memoria-vault/pull/604).


---

<!-- source: adr/79-argument-graph-and-warrant.md -->

# ADR-79: Argument graph and warrant

## Context

The Project gate needs to produce an argument, not just organize a cluster of
notes. The existing descriptive knowledge map shows what exists inside a project
scope; it does not say how a thesis is defended. The missing layer is the
thesis-rooted argument graph: the typed relation subgraph that connects evidence,
reasons, objections, and rebuttals to the thesis.

## Decision

Memoria treats the **argument graph** as the `supports` / `contradicts` subgraph
rooted at a thesis. Project impact, gap ranking, saturation, and outline
structure derive from this graph, not from the descriptive topology alone.

`warrant` becomes an optional attribute on a relation: the inferential rule that
explains why one note supports or contradicts another. It is free to populate
when known, but its absence is not a blocker in the alpha.5 cut. The
unstated-warrant gap detector remains off until relation coverage and PI demand
justify it; this ADR only reserves the shape.

Structural Operations may test presence and topology: relation type, path to the
thesis, addressed refutations, graph maturity, and whether a warrant field is
present. They may not judge whether a warrant is good, whether the strongest
counterargument was chosen, or whether the thesis is true. Those are PI judgment
or gated proposal territory.

## Consequences

- Outlines are defenses of a thesis, not ordered copies of a map. First-level
  reasons become section structure; contradicting paths become counterargument
  work.
- Gap impact is thesis-relative. A source or knowledge gap off the argument path
  can be interesting while having impact zero for this project.
- `warrant` can be added without blocking existing relations or requiring a
  mass backfill.
- The graph maturity default requires at least one addressed support and one
  addressed contradiction so the Project gate does not report saturation over a
  one-sided graph.

## Alternatives considered

**Use only the descriptive map.** Rejected: map topology can produce a survey,
but it cannot distinguish a defended argument from an organized literature area.

**Make `warrant` mandatory.** Rejected: it would make relation entry too heavy
and punish already useful support/contradiction links.

**Enable unstated-warrant gaps immediately.** Rejected: absence detection is
cheap, but it is also gameable and noisy before the relation layer has enough
coverage.

## Related

- **Files affected:** relation schema/contracts, Project structural-impact
  Operation, Project dashboards.
- **Related decisions / Depends on:** [ADR-08](08-typed-relations-frontmatter.md),
  [ADR-52](52-links-vs-relationships.md),
  [ADR-77](77-project-gate.md),
  [ADR-78](78-thesis-note-type.md).
- **Source discussion:** alpha.5 structural-impact workstream
  [#579](https://github.com/eranroseman/memoria-vault/issues/579) and merged implementation
  PR [#605](https://github.com/eranroseman/memoria-vault/pull/605).


---

<!-- source: adr/80-ephemeral-containerized-test-env.md -->

# ADR-80: Ephemeral containerized Linux test-env harness

## Context

[ADR-64](64-native-windows-support.md) already splits provisioning into two
single-OS installers — native Windows is the production runtime (`install.ps1`),
Linux/WSL is the testing runtime (`install.sh`). That split is settled and shipped;
this ADR does **not** revisit it. What ADR-64 left open is *how thoroughly the
Linux test path is exercised*: [ADR-29](29-testing-framework.md) still places L3
integration as manual/Windows and leaves the cross-cutting suites
(installer / recovery / chaos / security / performance) and absolute L5 quality as
uncovered or per-release-manual gaps. Because the production bridge is gone, the
full stack can now run headless on one OS — making most of that automatable for
the first time. alpha.5 shipped only the thin slice this design needs as a proof:
a negative deny-assertion driven through the [ADR-28](28-write-gate-as-plugin.md)
policy-gate plugin ([#582](https://github.com/eranroseman/memoria-vault/issues/582)).
The full harness is the roadmap's next effort, captured here so the decision has an
ADR trail rather than living only in a release scratch note.

## Decision

The all-Linux test environment is a **version-controlled golden image** (a
peer-reviewed `Dockerfile`) holding the full real stack — headless Obsidian
(`xvfb-run --no-sandbox`) with all plugins, Zotero (headless) or a fixture
`memoria.bib`, Git, Hermes, the five `memoria-*` profiles + MCP, the Local REST
API + native MCP, and `qmd` — with the local model as a `--gpus all` sibling
container. `docker compose` brings it up clean per run; a fresh vault volume is
seeded from checksummed, idempotent fixtures; nothing persists across runs except
the cached model weights. The image MUST include a real `git` binary and
initialize the throwaway vault as a repository before any git-backed assertions
run; a sandbox without Git is unsupported, because obsidian-git, the pre-commit
schema gate, post-commit verification, rollback, and history are part of the
system under test. A **pytest orchestrator** drives the Obsidian CLI over the
command-palette surface (one trigger per palette command), asserting artifact
shape / frontmatter, gate decision + audit row, board transition, dashboard
re-render (injected JS), and a screenshot golden-image diff.

The local model is **served by `llama.cpp`** (already vended via `qmd`'s
`node-llama-cpp`, GPU path solved on the test box). The target is **Gemma 4 12B**,
confirmed GA (Google, 2026-06-03, Apache 2.0): it is **multimodal-input /
text-output**, so it serves cleanly through a standard OpenAI text+tool endpoint —
dissolving the earlier "any-to-any won't serve" worry — with an official GGUF
(`unsloth/gemma-4-12b-it-GGUF`, `UD-Q4_K_XL` ≈ 7–8 GB, fitting the 16 GB card) run
via `llama-server … --jinja`, exposing `/v1`. **Qwen3-MoE remains an optional
fallback, no longer load-bearing.** The model is selected per environment through a
`MEMORIA_ENV=test|prod` overlay that extends the installer's existing
`{{PYTHON}}`/`{{VAULT_PATH}}`/`{{QMD}}` substitution with `{{MODEL_PROVIDER}}` /
`{{MODEL_BASE_URL}}` / `{{MODEL_DEFAULT}}` — flipping the Hermes provider
(`kilocode` → `openai-compatible`), not just an endpoint URL. This flattens
production's per-profile model tiering ([ADR-48](48-copi-and-agent-consolidation.md)),
so absolute L5 quality and the per-profile config-shape surface stay on the
Windows production-acceptance pass; the harness validates wiring, integration,
golden path, recovery, security, and scale, plus eval *mechanics* and regression.

**Three gates scope the remaining Phase 2 work**:

1. **Prove the gate fires (safety).** The harness MUST include a negative
   deny-assertion: a known-deny write, routed through the live ADR-28 plugin, is
   **blocked** with a deny audit row — never inferred from positive assertions. The
   superseded `re.fullmatch("obsidian.*")` shell-hook never matched the real
   `mcp_obsidian_*` tool names; the plugin's substring match does, so the shim must
   route through the plugin. (Shipped as the alpha.5 thin slice.)
2. **Model exists and is text+tool-servable — RESOLVED (2026-06-16).** Gemma 4 12B
   is GA with an official GGUF and `llama.cpp` / Ollama / vLLM support; it is
   multimodal-input / text-output, so a standard OpenAI text+tool endpoint fits. No
   longer a blocker; Qwen3-MoE is a kept-in-reserve fallback.
3. **Tool-call emission — narrowed to a smoke test.** Model, GGUF, `--jinja`, the
   `/v1` endpoint, and headline tool-use are all confirmed; the one unverified
   detail is whether `llama.cpp --jinja` parses Gemma 4's chat template into
   OpenAI-format `tool_calls` Hermes can consume (Gemma 3 lacked native tool tokens,
   so it is worth a local check). A ~5-minute `llama-server` smoke test settles it;
   only if it fails is a parser/shim needed, not a `base_url` swap.

## Phased adoption — the minimal viable harness (80/20)

The full harness is a large build, but most of its release-blocking value does
**not** need the costly parts. Memoria's load-bearing logic is deterministic
(Operations, the policy gate, ingest, schemas), so the **model layer** and the
**visual layer** — the two most expensive pieces — buy the *last* increment of
confidence, not the first.

**Phase 1 — deterministic integration + golden-path harness (~20% of the cost,
~80% of the value), covering L0–L4 + cross-cutting.** No GPU, no live model, no
screenshots. The framework's own cheap/expensive line is the **L4/L5 boundary**
([ADR-29](29-testing-framework.md)): L0–L4 are *wiring* (does the lifecycle produce
the right artifacts and transitions), L5 is *quality* (judgement). So **L4 belongs
in this tier** — the agent steps need a model only to emit a structurally-valid
output, which a recording or a seed supplies, so **the model is needed at record
time, not run time.** Containerize the *existing* offline stack —
`scripts/e2e-smoke.sh` already builds a vault installer-equivalently and walks
scaffold → golden → commit gate → offline ingest → honesty card → lint with no
network — and add:

- (a) **headless Obsidian over the command palette with data-layer asserts**
  (artifact / frontmatter, gate decision + audit row, board transition, dashboard
  re-render) — *not* pixel diffs;
- (b) **record/replay cassettes** for the agent-wiring loops, matched on tool-call
  structure, so L2b runs with **no live model**;
- (c) the **deny-assertion** (already shipped) plus the **installer / recovery**
  smoke, including a hard preflight that fails when `git` is absent from the image;
- (d) the **L4 golden-path** (source → ingest → classify → discuss → claim → draft →
  verify → export), model-free, by two means that compose. **Seed** fixture
  artifacts at the generative steps and drive the deterministic stages live —
  reusing `e2e-smoke.sh` for ingest, the **g9 zero-LLM spine**
  (dispatch → claim → run → gated write → audit → `done`), and the alpha.5 **seeded
  structural-impact path** — for partial L4 immediately from existing parts; then
  **upgrade each seeded step to a cassette** as cassettes are recorded, ratcheting
  to full L4 *inside* Phase 1 with no jump to Phase 2.

Deterministic, runs per-PR, and narrows the L3-integration, **L4 golden-path**,
recovery, and safety gaps that actually block releases. It proves the
installer-equivalent vault assembly, deterministic lifecycle, known-deny gate path,
and cassette replay without requiring a live model or GUI. It does **not** close the
full live-runtime surface: the path driven by a *live* model, the Obsidian GUI/REST
tail, screenshots, chaos, security, and performance remain Phase 2 / release-candidate
runtime-integration work.

**Phase 2 — the live-model + visual + chaos/perf tail (~80% of the cost).** The
`--gpus all` sibling container + Gemma 4 + nightly real-quality L5 eval (and the
live-model golden-path run — the L4/L5 seam), the screenshot golden-image diffs,
and the chaos / security / performance suites. Its
*model* risk is now low (gate 2 resolved), but its *cost* — GPU infra,
nondeterminism, and flaky visual baselines — is what makes it the expensive tail.
Build it only once Phase 1's coverage proves insufficient.

This phasing is already latent in the design's cadence (per-PR fs-shim + cassettes
with no live model; nightly full stack on Gemma); Phase 1 simply makes the
no-model tier the shippable unit and defers the rest.

## Consequences

- Narrows the ADR-29 L3 manual/Windows gap and the recovery / security /
  performance cross-cutting gaps by making the deterministic Linux side PR-safe.
  It does not fully close those gaps until Phase 2 adds live Hermes, the Obsidian
  GUI/REST tail, local-model runtime, screenshot baselines, chaos/security/perf
  suites, and release-candidate runtime-integration evidence. Same-host localhost
  on the Linux side still makes the intended HTTPS REST closure path straightforward
  ([#527](https://github.com/eranroseman/memoria-vault/issues/527),
  [ADR-31](31-native-obsidian-mcp.md)).
- Phase 1 introduces the fixture/cassette corpus and PR-safe smoke orchestration.
  Phase 2 is the closure path for the golden image, Obsidian-CLI/GUI harness, and
  version-pinned per-run evidence that makes "green today = green tomorrow."
- Git becomes an explicit image dependency, not an ambient host assumption. The
  harness must fail early if the binary or initialized throwaway repo is missing,
  because degraded "no git" runs do not exercise Memoria's commit hooks or
  rollback/history contract.
- A binary "did it call a tool?" check misclassifies a weak local model. Assertions
  use a three-bucket classification (no tool call / wrong (tool,path) / expected
  shape); only the expected bucket asserts artifact, gate, audit, board, and
  dashboard state.
- Record/replay cassettes match on **tool-call structure** (tool name + arg shape),
  not raw prompt bytes, or they no-op on exactly the wiring refactors they exist to
  catch. The nightly trigger is a Windows Task Scheduler → `wsl.exe` job, not WSL2
  `crond` (WSL2 has no persistent init).
- Residuals are bounded: OS portability (test = Linux, prod = Windows) replaces the
  deleted bridge, checked by each installer on its own OS plus the
  production-acceptance pass; absolute output quality stays a production-model
  judgment.

## Current implementation mapping

Phase 1 is the `workflow-replay` layer in the testing model. The compatibility
entrypoint is still `scripts/e2e-smoke.sh`, which now names its PR-safe sections:
`vault-assembly`, `commit-gate`, `offline-ingest`, `workflow-replay`, and
`final-integrity`. This layer partially replaces the old L2/L4 smoke need only for
model-free cassette replay; it does **not** completely replace the ADR-29
`scripts/test-l2.sh` concept, which described live Hermes agent-wiring against a
cheap model and disposable vault. That live driver belongs under opt-in/nightly
`runtime-integration` unless a deliberately small wrapper is added later. The full
containerized/headless Obsidian/local-LLM design remains Phase 2 / nightly /
release-candidate `runtime-integration`, not a required PR gate.

## Scratch disposition

The clean-sheet alpha.5 test-env scratch is retired into this ADR and the current
testing docs. The retained parts are Phase 1 `workflow-replay`, the explicit Git
preflight, the known-deny assertion, cassette matching on tool-call structure, and
the Phase 2 `runtime-integration` plan. The stale parts are rejected rather than
carried forward: the old Desk/Library/Studio command surface, WSL2 cron as a
nightly trigger, any required PR dependency on Docker/GPU/headless Obsidian, and
the idea that workflow replay completely replaces a future live Hermes smoke. Live
Hermes, GUI/REST proof, local-model tool-call smoke, screenshots, chaos/security,
and performance stay opt-in/nightly/release-candidate work until a stable runner
exists; issue [#722](https://github.com/eranroseman/memoria-vault/issues/722)
tracks that Phase 2 closure path.

## When this matters

**Phase 1 shipped in v0.1.0-alpha.6** (model-free L0–L4 record/replay harness, #586;
the G3 tool-call smoke runs against a local OpenAI-compatible endpoint, #662) — this
ADR is `accepted` for Phase 1. **Phase 2 stays deferred**: raise it when any holds —
the manual L3 surface or an uncovered cross-cutting suite (recovery / security /
performance) becomes a recurring release-blocking gap; a real project's PI-touch
budget needs L5 regression automated rather than hand-run. **Phase 1 needed no model
work at all** — its trigger was simply that recurring L3 / recovery gap; gate 2 is
already resolved and Phase 2 carries the remaining model / visual cost. The `assumes:` list pins the
mechanisms it rests on — if the two-installer split (ADR-64), the write gate
(ADR-28), or the reconciling installer (ADR-76) change shape, re-judge this.

## Alternatives considered

**Keep the split-OS WSL2 bridge for testing.** Rejected: it needs `.wslconfig`
tuning, blocks HTTPS, and forces manual Windows-only L3 — the fragility class
ADR-64 already deleted on the production side.

**Ship the fs-shim smoke suite (ADR-29 Option B) as the whole test env.** Rejected
as the *whole* env, kept as the per-PR cheap tier: a filesystem shim cannot
exercise real plugins, REST, dashboards, Zotero, or the visual surface.

**Serve the model with vLLM.** vLLM *is* in fact supported for Gemma 4 (Google
lists it), so this is a preference, not a constraint: `llama.cpp` is still chosen
because it is already vended via `qmd`, its GGUF (`UD-Q4_K_XL` ≈ 7–8 GB) fits the
16 GB card with headroom, and the GPU path is already solved on the test box. Ollama
is acceptable only as a thin wrapper over the same `llama.cpp` engine, not a
separate stack.

## Related

- **Related decisions / Depends on:** [ADR-64](64-native-windows-support.md) (the
  two-installer split this builds the Linux side of),
  [ADR-29](29-testing-framework.md) (the testing framework this automates),
  [ADR-28](28-write-gate-as-plugin.md) (the deny-assertion path),
  [ADR-76](76-versioned-vault-release-reconciling-installer.md) (the installer the
  `MEMORIA_ENV` overlay extends), [ADR-31](31-native-obsidian-mcp.md) (HTTPS REST
  on same-host localhost).
- **Files affected:** `scripts/install.sh`, `scripts/install.ps1`, profile
  `config.yaml` templates and cron wrappers (the `{{MODEL_*}}` overlay), a new
  `Dockerfile` + `docker compose` stack, and the fixture corpus.
- **Source discussion:** alpha.5 closeout (WS-0 spike
  [#576](https://github.com/eranroseman/memoria-vault/issues/576), thin deny-slice
  [#582](https://github.com/eranroseman/memoria-vault/issues/582)) and issue
  [#527](https://github.com/eranroseman/memoria-vault/issues/527) (HTTPS REST).
  Phase 2 runtime-integration follow-up is tracked in
  [#722](https://github.com/eranroseman/memoria-vault/issues/722).


---

<!-- source: adr/81-persistent-gate-dashboards.md -->

# ADR-81: Persistent gate dashboards

## Context

ADR-68 implemented navigation as three saved Obsidian workspaces: Desk, Library, and
Studio. That made the implementation heavier than the requirement: a gate is a mode
of work, while an Obsidian workspace is a saved pane layout. The alpha.7 UI review
also split the old Studio responsibilities into Knowledge and Project, deferred the
Canvas-backed Studio concept, and verified that dashboard notes can embed specific
Bases views while ordinary internal links reuse the active tab.

## Decision

> **Superseded slice (see [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)):**
> the directory is now `src/spaces/`, not `src/gates/`, and these navigation surfaces are
> called **spaces** — "gate" is now reserved for the approval/review checkpoint. The
> dashboard decision below still stands; only the path and the "gate" naming changed, and
> the historical wording is kept as-authored.
>
> **Superseded slice (see [ADR-115](115-inbox-queue-and-retired-homepage.md)):**
> the Homepage plugin no longer opens the Inbox on startup. Startup now uses QuickAdd to
> ask the core Workspaces plugin to load the saved **Memoria** shell with `home.md`, the
> pinned rail, and the Co-PI pane.

Memoria uses **four job-named gate dashboard notes** as the primary navigation model:
Inbox, Library, Knowledge, and Project. The dashboards live under `src/gates/` and
compose existing Bases views with empty-state copy. Gate switching is a wikilink nav
row in each dashboard, not an Obsidian workspace layout swap. `home.md` and the
Homepage plugin open the Inbox dashboard on startup. The core Workspaces plugin stays
enabled only for one "Memoria" reset layout; the QuickAdd workspace loader and
per-gate workspace choices are retired.

Desk is renamed to **Inbox** because the gate is the inbox queue; the previous ADR-68
rejection of that name no longer holds once the room metaphor is dropped. Library
keeps its name. Knowledge carries claim and hub synthesis. Project carries bounded
inquiry and thesis/project steering. Studio returns only with the deferred spatial
Canvas axis.

Portals is the folder-navigation chrome for this shell, not the gate switcher. It
replaces the file explorer only through its own `replaceFileExplorer` setting, with
the core file explorer retained as fallback and ADR-74 provenance satisfied by
vendored artifacts.

The deferred set for this UI line is explicit: the general projector engine
([ADR-102](102-disposable-projection-engine.md)), projected telemetry bases, and
Canvas/argument graph ([ADR-103](103-projected-canvas-spatial-axis.md)) are not
part of alpha.7. The dedicated edge-authoring "relate" control is a separate
accepted decision ([ADR-83](83-direct-pi-relate-control.md)).

## Consequences

- Gate switching becomes vault content instead of plugin layout state: four notes and
  Bases embeds are easier to diff, restore, and test.
- The UI now has four shippable gates: Inbox, Library, Knowledge, Project. Studio is
  not shipped as an empty promise.
- Workspaces Plus is unnecessary, and the old QuickAdd `load-workspace.js` workaround
  is removed.
- The Homepage plugin launch slice is superseded by ADR-115; startup now restores the
  saved **Memoria** shell without the Homepage plugin.
- Portals adoption is gated by the vendored plugin artifact and provenance lock entry.
- The missing direct "relate" control is an acknowledged alpha.7 limitation; links
  remain authored in `links:` frontmatter through agent proposals or hand edits.

## Alternatives considered

**Keep ADR-68 workspaces and add a fourth Project workspace.** Rejected because it
continues to treat a mode as a layout, adds more serialized UI state, and leaves the
Studio/Project split ambiguous.

**Adopt Workspaces Plus for smoother switching.** Rejected because the dashboard-note
model removes the need for a workspace-switching plugin at all.

**Use Portals as the gate switcher.** Rejected because Portals pins folders and tags,
not notes, and exposes no public API for opening gate dashboards.

**Keep the Desk name.** Rejected because the gate is now explicitly the action queue;
Inbox is the accurate job label, while Desk was only coherent inside the retired room
metaphor.

## Related

- **Files affected:** `src/spaces/`, `src/home.md`, `src/.obsidian/workspaces.json`,
  `src/.obsidian/plugins/homepage/data.json`, `src/.obsidian/plugins/quickadd/data.json`,
  `src/.obsidian/plugins/cmdr/data.json`, `src/.obsidian/app.json`,
  `src/.obsidian/core-plugins.json`.
- **Related decisions / Depends on:** [ADR-13](13-homepage-front-door.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-70](70-navigation-gates-dashboards.md),
  [ADR-72](72-command-surfacing.md),
  [ADR-74](74-pinned-obsidian-plugin-supply-chain.md).
- **Related future proposals:** [ADR-102](102-disposable-projection-engine.md),
  [ADR-103](103-projected-canvas-spatial-axis.md).
- **Resolves / supersedes:** [ADR-68](68-workspaces-desk-library-studio.md).


---

<!-- source: adr/82-four-gates-canonical-vocabulary.md -->

# ADR-82: The four gates are the single user-facing vocabulary; retire the Compile/Compose cycle naming

## Context

The system describes the *same* user activity space with **two parallel vocabularies**. The **gates** — Inbox, Library, Knowledge, Project — are intent-named Jobs-To-Be-Done surfaces ([ADR-70](70-navigation-gates-dashboards.md): "dashboards organized by Jobs-To-Be-Done"), and they are the surface the user actually navigates. Alongside them, a **Compile/Compose "knowledge cycle"** — a pipeline of phase names (`find → … → connect`; `assess → … → export`) — organizes the how-to docs and two explanation pages, and a *third* partial framing ("two modes — Library / Project") lives in the knowledge-cycle explanation. The decompositions overlap but do not align: the Compile flow straddles the Library and Knowledge gates, and the "act on what needs me" job (the Inbox gate) is invisible in the flow. Carrying two organizing vocabularies for one activity space taxes the reader's cognitive model and is a standing sign of an unfinished design.

## Decision

The **four gates (Inbox · Library · Knowledge · Project) are the single canonical user-facing vocabulary** for the system's jobs. The **Compile/Compose two-flow model and its phase names are retired** as an organizing and explanatory vocabulary — not demoted to a "narrative," because a narrative in its own vocabulary is still a second model to reconcile. The agent **lanes** (`catalog / extract / link / map / draft / verify / code`) are unchanged: they are the *agents'* internal work breakdown — a different actor from the human — and so are not a user-facing duplicate ([ADR-48](48-copi-and-agent-consolidation.md)). Concretely: how-to guides are grouped by gate (`how-to-guides/{inbox,library,knowledge,project}/`); the cycle's two-flow/phase content is removed and the knowledge-cycle explanation is reconciled to *gates above, lanes beneath*.

## Consequences

- The docs navigation mirrors the app: a user standing at a gate finds the how-to section of the same name.
- The day-to-day how-to folders `compile/`, `compose/`, `curate/` are replaced by `inbox/`, `library/`, `knowledge/`, `project/`; `compile-and-compose.md` is deleted and `knowledge-cycle.md` is reconciled to the gates+lanes framing.
- The terminal/operational how-to families (`setup/`, `operate/`, `troubleshooting/`, `hermes-agent/`, `zotero/`, `using-obsidian/`) are unaffected — they are tool/operational jobs, not gate JTBDs.
- The agent lanes and every profile are untouched; this is a *user-facing vocabulary* decision, not an architecture change.
- Moving guides breaks inbound links, including ~11 ADRs that reference how-to guides. Those link **paths** are repointed (the visible label and the decision prose are unchanged) — sanctioned by the [ADR index](README.md) "Mechanics" rule to repoint doc links on a move.

## Alternatives considered

- **Keep both — gates as navigation, the cycle as an explanatory narrative.** Rejected: a narrative carried in Compile/Compose vocabulary is still a second model the reader must reconcile against the gates — exactly the duplication this ADR removes. The genuine connective information (jobs have a typical order; gaps loop back) is expressed in the gates' own terms and carried by the tutorial arc, needing no parallel taxonomy.
- **Make the Compile/Compose flow canonical and demote the gates.** Rejected: a flow is a *process* decomposition, not a jobs decomposition — JTBD organizes by user intent, not by the system's pipeline. The gates are the shipped navigation surface and the more JTBD-correct framing, and the flow hides the high-frequency "act on what needs me" (Inbox) job and the genuine Library-vs-Knowledge distinction.

## Related

- **Related decisions / Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (the gates as JTBD surfaces), [ADR-77](77-project-gate.md) (the Project gate), [ADR-48](48-copi-and-agent-consolidation.md) (the lanes are the agents' work breakdown)
- **Files affected:** the `how-to-guides/` tree (regrouped by gate); `explanation/workflows/compile-and-compose.md` (deleted), `explanation/workflows/README.md`, `explanation/knowledge/knowledge-cycle.md` (reconciled), `explanation/rationale/why-pattern-provenance.md` (one mapping cell), `explanation/overview/what-memoria-is.md` (one relationship line)
- **Source discussion:** the alpha.8 JTBD-vocabulary alignment thread


---

<!-- source: adr/83-direct-pi-relate-control.md -->

# ADR-83: Direct PI relate control

> **Verified on-box 2026-06-21 (accepted but not yet implemented).** This control is
> `accepted` but **nothing is built**: there is no PI relate command in QuickAdd/Commander,
> and the nearest scripts (`link-claim.js`, `create-linked-claim.js`) are different tools.
> Forward-looking, like [ADR-60](60-cross-vault-knowledge-sharing.md) — do not read it as a
> live capability. Tracked with the implementation-gap batch (#827).

## Context

ADR-52 makes `links:` the authored connection layer: agents may propose typed
links, but the PI confirms them. In the current interface, that confirmation is
still too close to raw YAML: the PI either hand-edits `links:` frontmatter or
accepts an agent proposal through ordinary note editing. The alpha.7 gate
dashboard work kept this gap explicit rather than smuggling in a half-designed
edge editor. The missing surface is not a new graph model; it is a safer,
faster way for the PI to write the existing source-of-truth field.

## Decision

Memoria will provide a **direct PI relate control**: an Obsidian command or
form-driven action that lets the PI choose a source note, a relation type, and a
target note, preview the resulting frontmatter change, and apply it to the
source note's existing `links:` map.

The control is a convenience writer over the current contract, not a new source
of truth. It writes only schema-valid `links:` entries, preserves existing
frontmatter, and relies on the Linter/pre-commit checks for integrity. It does
not write Catalog `relationships`, does not create hidden sidecar edge records,
does not infer relations autonomously, and does not expand the relation
vocabulary without a separate schema/reference change.

## Consequences

- The PI gets a low-friction way to connect claims, sources, hubs, and thesis
  notes without remembering YAML shape.
- `links:` remains the only durable authored-edge record, so Bases, dashboards,
  cluster views, and argument-graph operations keep reading the same field.
- Agent-proposed links stay proposals. The relate control can be the acceptance
  surface for a proposed edge, but it must make the PI's confirmation explicit.
- Validation remains structural: the control prevents malformed writes where it
  can, while the Linter remains authoritative for unresolved wikilinks, wrong
  endpoint categories, and schema drift.
- Future relation-vocabulary changes, automated relation suggestions, or
  generated Canvas/projector edges require their own decision/update; they are
  not bundled into this UI control.

## When this matters

Schedule this when hand-editing `links:` becomes a recurring synthesis
bottleneck, when project argument work needs faster support/contradiction entry,
or when agent-proposed relation cards need a dedicated acceptance surface. It
also becomes higher priority if first-run feedback shows that the Knowledge gate
looks complete but users cannot tell how to integrate a claim into the graph.

## Alternatives considered

**Keep hand-editing `links:` only.** This preserves the cleanest architecture,
but makes the most important graph operation depend on frontmatter fluency. That
is tolerable during early alpha work and poor as soon as the vault has enough
claims for relation work to become routine.

**Create standalone edge notes or a sidecar edge store.** Rejected because it
splits the authored-edge source of truth. The existing `links:` map is already
linted, queryable, and consumed by dashboards and graph operations.

**Use Canvas as the edge editor.** Rejected for this decision because Canvas is
a spatial view, not the authoritative record. A future projected Canvas may
visualize or propose edges, but confirmed edges still land in `links:`.

**Let agents write confirmed relations directly.** Rejected because relation
choice is PI judgment under ADR-52. Agents can propose candidates and rationale;
the control is the human confirmation surface.

## Related

- **Workflows affected:** Knowledge synthesis, claim linking, Project argument
  graph work, and agent-proposed relation review.
- **Files affected:** `src/system/scripts/`, `src/.obsidian/plugins/quickadd/data.json`,
  `src/.obsidian/plugins/cmdr/data.json`, `src/spaces/knowledge.md`, `docs/reference/linking.md`,
  `docs/reference/frontmatter.md`, and the claim-linking how-to.
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md),
  [ADR-71](71-structured-capture-forms.md),
  [ADR-72](72-command-surfacing.md),
  [ADR-79](79-argument-graph-and-warrant.md),
  [ADR-81](81-persistent-gate-dashboards.md).
- **Source discussion:** implementation tracker
  [#691](https://github.com/eranroseman/memoria-vault/issues/691).


---

<!-- source: adr/84-read-only-obsidian-inspector.md -->

# ADR-84: Read-only Obsidian Inspector

## Context

Memoria already exposes state through in-vault dashboards, CLI checks, logs, and
the Obsidian surface. During debugging, those surfaces can be too scattered for
the operator to answer "what is loaded, what just happened, and what is unhealthy?"
without switching context. ADR-32 keeps any external access gated through MCP; this
proposal stays inside Obsidian and remains read-only.

## Decision

Memoria adds a read-only Obsidian Inspector sidebar pane showing board counts,
WIP depth, recent audit entries, and the Linter verdict band. It reads existing
dashboards and logs and adds no write path.

## Consequences

- Gives the operator one compact operational view inside Obsidian.
- Adds an Obsidian UI surface that must stay consistent with the existing dashboard
  and log sources.
- Must remain read-only; write actions belong to the existing command/gate paths.
- Covers the live operational-health view inside Obsidian; the static-snapshot
  question ([ADR-87](87-static-html-admin-reports.md)) remains a separate, deferred
  concern.

## When this matters

Routine debugging needs a compact "what is loaded / what happened / what is
unhealthy" view, and the existing CLI plus dashboards are slowing resolution.

## Alternatives considered

**Use only dashboards and CLI checks.** Lowest maintenance cost, but it keeps
routine state inspection split across surfaces.

**Add inspector write actions.** Rejected because it would create a second control
surface and raise policy-gate complexity for a debugging pane.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md).
- **Tracking issue:** [#697](https://github.com/eranroseman/memoria-vault/issues/697)
  (implementation-ready tracker; closed after the plugin shipped and tests covered
  the read-only surface).


---

<!-- source: adr/85-todoist-gap-card-mirroring.md -->

# ADR-85: Todoist gap-card mirroring

## Context

Gap cards are Memoria work items in `inbox/`, but the human may already use
Todoist as a personal task surface. Mirroring can reduce missed gap work, but it
adds an external dependency and does not change the source of truth.

## Proposal

Memoria may mirror Peer-reviewer gap cards to Todoist when the human uses Todoist
as the primary task surface. The vault card remains authoritative; Todoist is only
a notification and task-surfacing mirror.

## Consequences

- Makes gap work visible in an existing personal task surface.
- Adds Todoist API credentials and sync failure modes.
- Does not solve review capacity; ignored Todoist tasks still leave vault gap
  cards stale.

## When this matters

The human uses Todoist as their primary task surface and gap cards regularly sit
unactioned for more than two weeks.

## Alternatives considered

**Keep gap cards only in the vault.** Simpler and fully local, but it misses the
human's actual task surface if Todoist is the daily queue.

**Make Todoist authoritative.** Rejected because Memoria's audit, gate, and review
state live in the vault.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md), [ADR-51](51-inbox-category-and-honesty-card.md).
- **Tracking issue:** [#698](https://github.com/eranroseman/memoria-vault/issues/698).


---

<!-- source: adr/86-open-design-deliverable-rendering-agent.md -->

# ADR-86: Open-design deliverable-rendering agent

## Context

Pandoc-style exports cover plain scholarly deliverables, but some outputs need
polished presentation, designed PDF, or web rendering. A rendering agent could
apply Memoria's design system, but that creates a new handoff contract outside the
core vault workflow.

## Proposal

Memoria may add an open-design deliverable-rendering handoff: the Engineer
scaffolds an external rendering request from a Pandoc-exported Markdown
deliverable and `.memoria/design-system.md`; the external agent renders; the human
reviews the final artifact.

## Consequences

- Enables polished formats that plain Pandoc does not produce.
- Requires a maintained design-system file and a clear Engineer-to-renderer
  contract.
- Must keep human review as the acceptance step; generated design output is not
  automatically published.

## When this matters

The human needs a deliverable format such as a presentation or designed PDF that
plain Pandoc cannot produce, and is willing to maintain the design-system file.

## Alternatives considered

**Use Pandoc only.** Lower operational cost, but does not cover designed outputs.

**Build native rendering into Memoria.** Rejected for now because design rendering
is not core research OS behavior and carries a large maintenance surface.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md).
- **Tracking issue:** [#699](https://github.com/eranroseman/memoria-vault/issues/699).


---

<!-- source: adr/87-static-html-admin-reports.md -->

# ADR-87: Static-HTML admin reports

## Context

Memoria already has dashboards and metrics, but periodic snapshots may be useful
for review or sharing without opening Obsidian. Static reports add a generated
artifact and possible renderer dependency, so they should not be bundled with
ordinary dashboard work.

## Proposal

Memoria may generate static HTML admin reports for board state, Linter verdict
summary, and metrics, stored under `system/reports/`. Quartz is a candidate
renderer because it understands Obsidian-style vaults, backlinks, and graph views.

## Consequences

- Creates shareable or archivable operational snapshots.
- Adds a scheduled report job and renderer maintenance surface.
- Risks duplicating dashboard state unless generation is treated as a snapshot,
  not another live source of truth.

## When this matters

The human wants to share or archive periodic health snapshots, or Dataview
dashboards are too slow for a quick weekly review.

## Alternatives considered

**Use only live dashboards.** Simpler and avoids snapshots, but less useful for
archival or sharing.

**Publish the whole vault.** Rejected for admin health reporting because it
exposes too much and solves a broader problem than the snapshot need.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md), [ADR-62](62-measurement-and-verification-harnesses.md).
- **Tracking issue:** [#700](https://github.com/eranroseman/memoria-vault/issues/700).


---

<!-- source: adr/88-literate-code-note.md -->

# ADR-88: Literate code-note

## Context

Research code often needs prose explanation beside executable logic. Memoria can
store project code and notes separately today, but it has no first-class note type
that weaves explanation with executable code while checking drift between them.

## Proposal

Memoria may add a `code-note` type that interleaves prose and executable code,
with weave/tangle behavior and Linter checks for code/prose drift. The note is a
research notebook artifact, not a replacement for normal repository source.

## Consequences

- Helps computational-method notes stay executable and explainable.
- Adds a new note type, schema, and drift detector.
- Must avoid blurring the boundary between canonical vault notes and source code
  maintained in a repository.

## When this matters

The human is writing computational-method notes where code and prose regularly
diverge and the divergence is costly to catch manually.

## Alternatives considered

**Keep code in repositories and prose in notes.** Simpler and clear, but makes
small method notebooks awkward.

**Use external notebooks only.** Rejected as the primary path because it moves
method rationale outside the vault's schema and review discipline.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md), [ADR-57](57-engines-write-agents-judge.md).
- **Tracking issue:** [#701](https://github.com/eranroseman/memoria-vault/issues/701).


---

<!-- source: adr/89-learning-to-rank-triage.md -->

# ADR-89: Learning-to-rank triage

## Context

Triage ordering is personalized: the same candidate can be valuable or noise
depending on the human's prior keep/discard decisions and current research focus.
LLM tournament ranking is useful as a cold start, but it is expensive and less
auditable than a trained ranker once enough human decisions exist.

## Proposal

Memoria may train a learning-to-rank model, such as LightGBM LambdaRank, over the
human's past triage decisions to order future candidates. The scalar ordering or
LLM tournament remains the cold-start path until enough training data exists.

## Consequences

- Produces a cheaper, reproducible, personalized ordering after sufficient data.
- Requires stored training examples, evaluation, and drift monitoring.
- Poor early training data can make the ranking confidently wrong.

## When this matters

The human has made at least 300 triage decisions and notices that triage ordering
feels generic or unconditional on research priorities.

## Alternatives considered

**Keep LLM tournament ranking.** Better cold-start behavior, but high cost and low
auditability at scale.

**Use a fixed heuristic ranker only.** Cheap and deterministic, but unlikely to
learn the human's actual research preferences.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-54](54-two-decision-kinds-batch-worklists.md).
- **Tracking issue:** [#702](https://github.com/eranroseman/memoria-vault/issues/702).


---

<!-- source: adr/90-claim-sentence-classification.md -->

# ADR-90: Claim-sentence classification

## Context

Claim extraction can waste LLM attention on full-paper text when only a small
subset of sentences are plausible claims. A classical rhetorical-zone classifier
or structured heuristic pass could narrow the candidate set before any generative
judgment.

## Proposal

Memoria may add claim-sentence classification before LLM claim proposal. Candidate
methods include CoreSC/ART-style rhetorical-zone classifiers and heuristics based
on citations, hedging, and numeric claims.

## Consequences

- Reduces LLM input size and can improve precision of proposed claim notes.
- Requires labeled or validated examples and false-positive monitoring.
- Bad classification can hide useful claims before the LLM ever sees them.

## When this matters

Agent-proposed candidate claim notes are being piloted and the LLM false-positive
rate on non-claim sentences is producing meaningless candidates.

## Alternatives considered

**Send full paper text to the LLM.** Simpler, but costlier and less auditable.

**Use classifier output as final truth.** Rejected because claim status still needs
review and context; the classifier only narrows the candidate set.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-51](51-inbox-category-and-honesty-card.md).
- **Tracking issue:** [#703](https://github.com/eranroseman/memoria-vault/issues/703).


---

<!-- source: adr/91-classical-prose-metrics-export-gate.md -->

# ADR-91: Classical prose metrics for the export gate

## Context

The export gate needs to catch prose quality issues, but many symptoms are
mechanical: readability, repetition, sentence length, passive-voice ratio, and
citation density. An LLM judge can assess coherence and tone, but it should not be
the first or only tool for deterministic prose signals.

## Proposal

Memoria may run classical prose metrics before the LLM-judge export gate. Metrics
may include Flesch-Kincaid readability, passive-voice ratio, citation density,
n-gram repetition, and sentence-length outliers.

## Consequences

- Adds cheap, reproducible signals before generative review.
- Risks false alarms if thresholds are not tuned to scholarly prose.
- Keeps the LLM judge responsible for coherence and tonal drift rather than
  replacing it.

## When this matters

The LLM-judge export gate is live and recurring false alarms on structural prose
issues dominate the report.

## Alternatives considered

**Keep export review purely LLM-judged.** Simpler, but wastes generative review on
deterministic symptoms.

**Block exports on prose metrics alone.** Rejected because metrics are symptoms,
not final quality judgments.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-14](14-advisor-review-vs-frozen-deliverable.md), [ADR-62](62-measurement-and-verification-harnesses.md).
- **Tracking issue:** [#704](https://github.com/eranroseman/memoria-vault/issues/704).


---

<!-- source: adr/92-discovery-relevance-scoring.md -->

# ADR-92: Discovery relevance scoring

## Context

Discovery candidates currently need ranking against the human's research focus.
An LLM skill can rank candidates, but a deterministic scorer could provide an
auditable first ordering using embeddings, citation graph overlap, and topic-tag
overlap.

## Proposal

Memoria may add a deterministic `[!suggestions]` weighted scorer that ranks
discovery candidates against `research-focus.md`, using embedding similarity,
citation-graph overlap, and topic-tag overlap. The scorer would feed triage; it
would not accept or reject candidates automatically.

## Consequences

- Reduces LLM ranking cost and makes the ordering auditable.
- Requires a maintained `research-focus.md` and tuned weights.
- Can become misleading if the focus file drifts from the human's current agenda.

## When this matters

The discovery loop is live and morning triage exceeds 15 minutes because
candidates are not pre-sorted by relevance.

## Alternatives considered

**Keep LLM ranking only.** Flexible, but less reproducible and more expensive.

**Use recency or citation count only.** Cheap, but weakly aligned with the human's
research priorities.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-95](95-nightly-proactive-discovery-loop.md).
- **Tracking issue:** [#705](https://github.com/eranroseman/memoria-vault/issues/705).


---

<!-- source: adr/93-keyphrase-extraction-tag-candidates.md -->

# ADR-93: Keyphrase extraction for tag candidates

## Context

Memoria classifies paper metadata today, but controlled-vocabulary tag recall can
lag when new terms appear that a classifier has not seen. Keyphrase extraction can
surface candidate vocabulary terms without asking an LLM to invent tags.

## Proposal

Memoria may use KeyBERT, YAKE, or a similar keyphrase extractor to propose tag
candidates, then map those phrases onto the human's controlled vocabulary. This
also requires defining the host tag-classification path it extends.

## Consequences

- Improves recall for vocabulary gaps and emerging terms.
- Adds another classifier/extractor to tune and validate.
- Extracted phrases remain candidates; the controlled vocabulary remains the
  authority.

## When this matters

A tag classifier has been active for at least three months and the human notices
recurrent vocabulary gaps.

## Alternatives considered

**Use only existing metadata topics.** Simpler, but can miss domain-specific terms.

**Let the LLM freely create tags.** Rejected because it bypasses controlled
vocabulary discipline.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md).
- **Tracking issue:** [#706](https://github.com/eranroseman/memoria-vault/issues/706).


---

<!-- source: adr/94-record-linkage-entity-deduplication.md -->

# ADR-94: Record linkage for entity deduplication

## Context

Author and venue entities can duplicate when external IDs are missing or
inconsistent. Memoria already prefers deterministic ingest and catalog integrity;
record linkage should use identifiers and string-similarity blocking before any
LLM judgment.

## Proposal

Memoria may add record linkage for entity deduplication: ORCID/OpenAlex IDs first,
then string-similarity blocking over by-name collisions, with human review before
merge when identity is uncertain.

## Consequences

- Reduces duplicate person and venue entities with auditable evidence.
- Requires careful threshold selection to avoid false merges.
- Extends the deterministic ingest discipline without making the LLM an identity
  authority.

## When this matters

Entity notes accumulate duplicate person or venue entries that the human notices
while cleaning the graph.

## Alternatives considered

**Ask the LLM whether two entities match.** Rejected as the primary path because
identity merge needs deterministic evidence and review.

**Only merge on exact external IDs.** Safe, but leaves no-ID duplicates unresolved.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-49](49-catalog-in-bases-linter-monitor.md).
- **Tracking issue:** [#707](https://github.com/eranroseman/memoria-vault/issues/707).


---

<!-- source: adr/95-nightly-proactive-discovery-loop.md -->

# ADR-95: Nightly proactive discovery loop

## Context

Discovery is currently operator-triggered. A nightly loop could make Memoria
proactive, but unattended work can flood the inbox and silent cron failure is a
serious operational risk.

## Proposal

Memoria may add a nightly discovery cron that reads `research-focus.md`, selects
top priorities, runs `find` per priority, ingests confirmed candidates, enriches
stale paper notes, commits, and posts a morning summary. It fails loud and keeps
human confirmation gates intact.

## Consequences

- Converts discovery from reactive to proactive.
- Requires an always-on machine and written inclusion criteria.
- Bad criteria can make morning triage the slowest part of the day.

## When this matters

Memoria v0.1 is stable, `research-focus.md` has been maintained for at least four
weeks, always-on deployment is active, and `screening-plan.md` is written down.

## Alternatives considered

**Keep discovery manual.** Safer and simpler, but leaves repeated discovery work
on the operator.

**Run unattended discovery without a screening plan.** Rejected because it invites
inbox flooding.

## Related

- **Supersedes:** [ADR-61](61-nightly-discovery-loop.md).
- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md), [ADR-48](48-copi-and-agent-consolidation.md).
- **Tracking issue:** [#708](https://github.com/eranroseman/memoria-vault/issues/708).


---

<!-- source: adr/96-code-lane-keep-revert-experiment-loop.md -->

# ADR-96: Code-lane keep/revert experiment loop

## Context

Some coding work follows a repeated edit, test, keep-if-improved, revert-if-worse
cycle. That pattern is safer in code than in synthesis because the work can be
bounded by a scalar success criterion and reversible diffs.

## Proposal

Memoria may add a lane-bounded `code-experiment-loop` skill with `success_metric:`,
`budget_iterations:`, and `budget_cost_usd:`. Outputs land under
`projects/<project>/code/experiments/<run-id>/`, and human promotion remains
required.

## Consequences

- Automates repetitive code experiments while keeping the review gate intact.
- Optimizes the metric, not necessarily the goal.
- Requires strict budgets and write-scope enforcement.

## When this matters

The operator repeats the same edit/test/revert cycle more than about 10 to 20
times per project, and a scalar success criterion exists before the loop starts.

## Alternatives considered

**Use ordinary coding agents only.** Simpler, but loses the keep/revert loop's
measurement discipline.

**Apply the loop to synthesis.** Rejected because synthesis lacks a monotonic,
safe scalar metric and reversible success semantics.

## Related

- **Supersedes:** [ADR-61](61-nightly-discovery-loop.md).
- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md).
- **Tracking issue:** [#709](https://github.com/eranroseman/memoria-vault/issues/709).


---

<!-- source: adr/97-writer-proposed-candidate-claim-notes.md -->

# ADR-97: Writer-proposed candidate claim notes

## Context

After discussion or distillation, the Writer may be able to propose candidate
claim notes. This is judgment-adjacent: fluent proposals can anchor the human or
encourage rubber-stamping, so proposals must not become canonical claims without
PI authorship.

## Proposal

Memoria may let the Writer propose candidate claim notes as Inbox cards, each with
source provenance and passage evidence. The policy MCP continues to deny agent
writes to `notes/claims/`; the human edits, authors, or discards.

## Consequences

- Reduces transcription effort when claim comprehension is already done.
- Increases rubber-stamping and framing-capture risk.
- Requires measurement of accept-unedited rate as a warning signal, not a success
  metric.

## When this matters

`discuss` and `distill` are stable, and the felt bottleneck is transcribing claims
rather than comprehending them.

## Alternatives considered

**Let Writer write canonical claims.** Rejected because ADR-21 and the review gate
reserve canonical claim authorship for the PI.

**Never propose claims.** Safer, but leaves repetitive transcription work entirely
manual even when provenance is clear.

## Related

- **Supersedes:** [ADR-61](61-nightly-discovery-loop.md).
- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md), [ADR-51](51-inbox-category-and-honesty-card.md).
- **Tracking issue:** [#710](https://github.com/eranroseman/memoria-vault/issues/710).


---

<!-- source: adr/98-relation-vocabulary-expansion.md -->

# ADR-98: Relation-vocabulary expansion

## Context

ADR-52 establishes authored `links:` as the source of truth for typed note
relations. The current vocabulary is intentionally small. Expanding it too early
creates half-populated fields and unreliable queries; expanding it at the right
time can make relation work more expressive.

## Proposal

Memoria may expand the `links:` relation vocabulary one value at a time, starting
with `similar`, then considering `cross-domain` and `uses-method` only after
`similar` proves useful. Relation keys remain documentary and validated for
resolution, not automatically inferred truth.

## Consequences

- Makes graph queries more expressive when the corpus is dense enough.
- Adds template, reference, Linter, and dashboard updates per relation.
- Inconsistent typing makes query results incomplete and erodes trust.

## When this matters

There are at least 200 claim notes and 500 inter-claim wikilinks, and the human
regularly wants "find similar" queries that manual backlink walks do not answer.

## Alternatives considered

**Adopt the full PARNESS taxonomy.** Rejected for now because it was designed for
ML/science workflows and may be wrong-shaped for Memoria's knowledge work.

**Keep only supports/contradicts/extends forever.** Simpler, but likely too narrow
once the claim graph becomes dense.

## Related

- **Supersedes:** [ADR-65](65-retrieval-and-schema-extensions.md).
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md), [ADR-79](79-argument-graph-and-warrant.md).
- **Tracking issue:** [#711](https://github.com/eranroseman/memoria-vault/issues/711).


---

<!-- source: adr/99-massw-aligned-paper-aspects.md -->

# ADR-99: MASSW-aligned paper aspects

## Context

Paper summaries do not always expose method or outcome in a queryable way.
MASSW-style aspects could make key idea, method, and outcome queryable, but they
add an extraction call and risk low-quality abstract-only fields.

## Proposal

Memoria may add `_aspects.key_idea`, `_aspects.method`, and `_aspects.outcome` to
paper records, populated at ingest, human-correctable at review, and queryable in
Obsidian. `context` and `projected_impact` are excluded because they overlap other
fields or need evidence ingest lacks.

## Consequences

- Improves filtering by method and outcome.
- Adds extraction cost and review burden per paper.
- Abstract-only aspects may be weaker than full-text or figure-informed aspects.

## When this matters

The Librarian regularly ingests papers and the human wants to filter by method or
outcome, but must read full summaries to do it.

## Alternatives considered

**Adopt all MASSW fields.** Rejected because `context` overlaps existing metadata
and `projected_impact` needs post-publication evidence.

**Wait for figure-informed extraction.** Rejected as a prerequisite because an
abstract-only slice can be useful independently.

## Related

- **Supersedes:** [ADR-65](65-retrieval-and-schema-extensions.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md).
- **Tracking issue:** [#712](https://github.com/eranroseman/memoria-vault/issues/712).


---

<!-- source: adr/100-exploration-trace-capture.md -->

# ADR-100: Exploration-trace capture

## Context

Map and scope work often explores directions that turn out not to help. Without a
trace, the human may repeat the same dead end later. But rejected directions are
project-local context, not canonical knowledge.

## Decision

Memoria captures rejected directions and dead ends as a structured artifact
beside a Librarian map-lane scope or gap report. The artifact stays at the project
level and is never auto-promoted into canonical knowledge layers.

## Consequences

- Reduces repeated exploration of known dead ends.
- Adds an artifact-management obligation to map-lane outputs.
- Risks over-recording if every weak lead becomes durable state.

## When this matters

The human notices repeating an already-explored direction: the "I am sure I
checked this before" failure mode.

## Alternatives considered

**Do not record rejected directions.** Simpler, but repeats wasted exploration.

**Promote traces to canonical knowledge.** Rejected because dead ends are often
project-local and may be productive elsewhere.

## Related

- **Supersedes:** [ADR-65](65-retrieval-and-schema-extensions.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-52](52-links-vs-relationships.md).
- **Tracking issue:** [#713](https://github.com/eranroseman/memoria-vault/issues/713).


---

<!-- source: adr/101-navigation-spaces-gate-reserved-for-approval.md -->

# ADR-101: Navigation surfaces are "spaces"; "gate" is reserved for the approval gate

## Context

[ADR-82](82-four-gates-canonical-vocabulary.md) made the four intent-named navigation surfaces — Inbox · Library · Knowledge · Project — the single canonical user-facing vocabulary, and called them **gates**. But "gate" was *already* the system's word for a different, deeper concept: the **structural human approval checkpoint** ([ADR-03](03-structural-review-gate.md)) — the review / human / policy / write gate the policy MCP enforces. That sense is also the industry-standard one: a quality gate, a stage-gate, a human-in-the-loop *approval gate* all name a pass/fail checkpoint, not a place.

So "gate" carried two heavily-used senses at once — a navigation surface (a place you stand) and an approval checkpoint (a wall a write must pass) — and they collide. A bare "the gate" became genuinely ambiguous, and a lexical audit found the approval sense outnumbering the navigation sense roughly 480:190. Two further minor senses muddied it: the git **pre-commit** check ("the commit gate") and the Hermes **gateway** process. When one word names several load-bearing concepts, the cognitive model degrades — the same design smell ADR-82 itself invoked.

## Decision

**"Gate" is reserved for the gating sense — the approval/policy/review checkpoint. The navigation surfaces are renamed "spaces."**

1. **Navigation surfaces → spaces.** The four surfaces are the **Inbox · Library · Knowledge · Project spaces**. The note type is `space` (`type: space`, `space:` enum field), they live in `src/spaces/`, and the `gate: gates` type→folder map becomes `space: spaces`. "Spaces" is chosen over the other candidate, "views," because Obsidian already uses **view** natively (Reading view, graph view, `ItemView`) — reusing it would relocate the overload, not remove it. "Space" is clean in Obsidian's vocabulary and keeps the destination feel the surfaces need.
2. **"Gate" = the approval checkpoint, always stated fully.** The structural human gate is written **review gate / human gate / policy gate / write gate** — never a bare "gate" where the surrounding text does not already establish it ([ADR-03](03-structural-review-gate.md), [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md), [ADR-41](41-configurable-review-gate-mode.md) are unchanged).
3. **Pre-commit is a hook, not a gate.** The git schema-validation check is the **pre-commit hook**; CI enforcement is **required status checks** — not "the commit gate."
4. **The runtime entry point is the gateway.** Always "gateway"; never abbreviated to "gate."
5. **The project readiness gate keeps "gate."** The deterministic structural-impact check (`project-gate.md`, `project-gate.base`, `project-gate-index.md`, `refresh project gate`) is a *quality/readiness gate* and correctly keeps the word — the navigation rename disambiguates it from the Project space.
6. **Compile/Compose stays retired** (carried forward from ADR-82): the how-to guides remain grouped `how-to-guides/{inbox,library,knowledge,project}/` and the cycle vocabulary is not revived.

## Consequences

- Data model: `schemas/types/gate.yaml` → `space.yaml` (type, category, enum field); `folders.yaml`, the Linter `detectors.py` folder maps, and the installer `manifest.sh` skeleton all move `gates` → `spaces`; the four `src/gates/*.md` notes move to `src/spaces/`.
- App config follows the move: the Homepage startup target and the saved-workspace layout point at `spaces/inbox`; the plugin-provenance lock digest for `homepage/data.json` is re-pinned to match.
- ~190 navigation prose references across the live docs and `src/` change `gate` → `space`; the approval-gate references (the majority) are left in place or qualified, never renamed.
- ADR and `releasing/` decision prose is **not** rewritten — those are historical records in the vocabulary of their time; only broken vault **paths** (`gates/` → `spaces/`) are repointed where a checker validates them.
- The saved Obsidian **Workspaces** core-plugin feature (the reset layout) keeps its name — "space" and "workspace" are distinct, and the one sentence that names both is worded to keep them apart.

## Alternatives considered

- **"Views" instead of "spaces."** Rejected: Obsidian's own UI and plugin API already use "view" pervasively (Reading view, graph view), so adopting it for navigation manufactures a fresh in-app overload — the opposite of the goal.
- **Rename the approval gate instead, keep "gates" for navigation.** Rejected: "gate" is the industry-standard and architecturally central term for the approval checkpoint ([ADR-03](03-structural-review-gate.md)); the navigation surface is the newer, borrowed, jargon use. The rightful owner keeps the word.
- **Keep "gates" for navigation and only forbid bare "the gate."** Rejected: it leaves two load-bearing concepts sharing one root, which is the duplication this decision removes.

## Related

- **Supersedes:** [ADR-82](82-four-gates-canonical-vocabulary.md) (carries its Compile/Compose retirement forward; changes only the surface name gate → space).
- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (the surfaces as JTBD dashboards), [ADR-77](77-project-gate.md) (the Project surface + its readiness gate), [ADR-48](48-copi-and-agent-consolidation.md) (the lanes are the agents' work breakdown).
- **Reserves "gate" for:** [ADR-03](03-structural-review-gate.md), [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md), [ADR-41](41-configurable-review-gate-mode.md).
- **Source discussion:** the alpha.8 overloaded-terminology audit (gate's four senses).


---

<!-- source: adr/102-disposable-projection-engine.md -->

# ADR-102: Disposable projection engine

## Context

Memoria already has one narrow projection: Hermes board state is mirrored into
markdown rows so Obsidian can render it as ordinary vault content. Several future
surfaces want the same pattern for audit windows, metrics, eval runs, skill state,
and other non-markdown sources. Building that as ad hoc emitters would multiply
stale-row, schema-drift, cold-cache, and failure-surfacing bugs.

## Proposal

Memoria may add a deterministic projection engine that renders non-markdown sources
of record into disposable markdown rows under a consumer-only projection zone. The
source remains authoritative; projected files are regenerated, may be deleted on
the next pass, and are never edited by hand.

The contract is strict:

- one source row maps to one projected artifact;
- reconciliation handles create, update, and delete;
- filenames use collision-safe slug/hash encoding while the raw source id remains
  in frontmatter;
- event sources sort on a real event time, while snapshot sources sort on a domain
  key rather than fabricated timestamps;
- output enum values are checked against the same schemas as authored notes;
- dirty source rows are quarantined and logged while conforming rows continue;
- bulk projections wait for Obsidian metadata-cache settlement before signalling
  readiness;
- projector failures raise an Integrity signal and dashboards show a distinct
  "last refresh failed" state.

The projector's operator model is part of this proposal, not an implementation
detail. The engine must name what process runs it, what writes it can perform, how
it coordinates concurrent passes, and how it fits ADR-27/28's single audited write
path.

## Consequences

- Future non-markdown views share one tested reconciliation and failure model.
- Projected dashboards can stay ordinary Bases/Dataview consumers instead of
  bespoke UI code.
- The system gains a new engine with filesystem write authority; its operator,
  locking, sync, and failure boundaries must be explicit before acceptance.
- Projected artifacts are local runtime products. Multi-device visibility needs
  either local regeneration or a non-git sync story; gitignored projections cannot
  be treated as shared source.

## When this matters

This becomes worth deciding when a real dashboard cannot be expressed as an
authored Base, Dataview over existing logs, or the current board mirror; when stale
projected rows become a recurring release issue; or when telemetry volume makes
pull-on-read views too slow.

## Alternatives considered

**Keep one-off emitters.** Simpler for the first surface, but repeats the hard
parts — deletion, dirty data, schema conformance, cold-cache timing, and failure
states — in every emitter.

**Make projected files authoritative.** Rejected because it creates a second source
of truth. Projections are views; sources of record stay in logs, metrics, board
state, schemas, or authored note frontmatter.

**Do not project; query raw sources directly.** Works for small Dataview or script
readers, but does not give Obsidian Bases a stable one-row-per-object surface and
does not solve operator-facing dashboard ergonomics.

## Related

- **Workflows affected:** Operational-health dashboards, board projection, eval
  trend, skill state, and future integrity projections.
- **Files affected:** future projection engine under `src/.memoria/operations/`,
  projection registry, dashboard references, Linter/projector conformance tests.
- **Related decisions / Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md),
  [ADR-57](57-engines-write-agents-judge.md),
  [ADR-69](69-operations-layer-naming.md),
  [ADR-70](70-navigation-gates-dashboards.md),
  [ADR-81](81-persistent-gate-dashboards.md).
- **Tracking issue:** [#719](https://github.com/eranroseman/memoria-vault/issues/719).


---

<!-- source: adr/103-projected-canvas-spatial-axis.md -->

# ADR-103: Projected Canvas spatial axis

## Context

ADR-79 gives Project work an argument-graph vocabulary, but the current shipped UI
is intentionally tabular: Spaces and Bases carry the day-to-day workflow. Canvas
could help when arrangement and edges are the content, but Canvas JSON is invisible
to the Linter, Bases, and graph operations. Treating hand-drawn Canvas edges as
truth would repeat the off-store failure that ADR-71 rejected.

## Proposal

Memoria may add Canvas as a **spatial projection**, not as an authoritative edge
store. Confirmed edges stay in `links:` frontmatter. A projected Canvas renders
file-reference nodes and relation-labelled edges from those authored links; a
scratch Canvas remains a human sense-making workspace whose edges become durable
only when the PI graduates them through the direct relate control or another
`links:` writer.

The projected Canvas contract is:

- nodes point to real notes rather than copied text;
- edges derive from `links:` and optional ADR-79 warrants;
- Project pages open projected canvases by link/button in their own pane, not as a
  load-bearing inline embed;
- inline embeds may be thumbnails only, because they show topology but not file-node
  content;
- projected canvases are read-only/regenerated and offer a fork-to-scratch escape;
- accepting the ephemeral-position model requires a layout-feasibility spike that
  proves incremental-stable layout: existing nodes keep position and new nodes are
  placed without global reflow;
- if that spike fails, persisted positions in a governed projection registry are
  the designed fallback. Authoritative hand-drawn Canvas edges remain rejected.

## Consequences

- The spatial surface can support argument maps without splitting the edge source of
  truth.
- The PI gets an escape hatch for exploratory arrangement while durable relations
  still land in `links:`.
- The hardest technical requirement is layout stability, not Canvas file creation.
  Without it, regenerated views erase the PI's mental map.
- Forked scratch canvases need a staleness signal showing how many source-graph
  edges changed since the fork.

## When this matters

This becomes worth deciding when real Project work shows that tabular Spaces and
Bases cannot carry the argument; when the PI asks for a spatial map while reviewing
claims/theses; or when relation density makes the graph's topology itself the
object under discussion.

## Alternatives considered

**Use authored Canvas as the edge source of truth.** Rejected because it bypasses
the Linter, frontmatter schemas, and ADR-79 graph operations.

**Use projected Canvas with no layout persistence.** Plausible only if the layout
spike proves stable enough. Otherwise every regeneration resets the user's mental
map.

**Skip Canvas and keep tables only.** Correct for the current sparse vault and
therefore the shipped posture. It may become too narrow for dense argument review.

## Related

- **Workflows affected:** Project argument review, Knowledge synthesis, scratch
  spatial sense-making, and direct relation authoring.
- **Files affected:** future projection engine/registry, `projects/` pages,
  Canvas projection tests, and relation-authoring docs.
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md),
  [ADR-79](79-argument-graph-and-warrant.md),
  [ADR-81](81-persistent-gate-dashboards.md),
  [ADR-83](83-direct-pi-relate-control.md),
  [ADR-102](102-disposable-projection-engine.md).
- **Tracking issue:** [#721](https://github.com/eranroseman/memoria-vault/issues/721).


---

<!-- source: adr/104-telemetry-three-planes.md -->

# ADR-104: Telemetry as three planes — audit, analytics, diagnostic

## Context

Memoria's logging grew signal-by-signal: an append-only audit trail ([ADR-25](25-session-logging-two-logs.md)), the publication-benchmark capture ([ADR-20](20-publication-path.md)), and a dozen purpose-named JSONL streams documented in [Telemetry & logs](../reference/telemetry.md). The pieces work, but the *posture* was never decided as a whole, and one need is missing entirely: when Memoria's own deterministic code (an MCP server, an ingest run, a cron) fails, the only trace is a stderr print — there is no persisted, queryable diagnostic record. At the same time the existing signals conflate concerns with opposite requirements: forensic permanence, content-free analytics, and (the missing) content-bearing debugging all want different integrity, retention, and privacy rules. Treating them as one substrate forces the strictest rule onto everything and still leaves debugging unserved. This decision settles the overall shape; the diagnostic plane's privacy contract ([ADR-105](105-diagnostic-plane.md)) and the cost/disposition capture points ([ADR-106](106-cost-and-disposition-capture.md)) are decided separately. Where this ADR changes audit storage layout for future multi-machine operation, it amends [ADR-25](25-session-logging-two-logs.md) without changing ADR-25's audit semantics: append-only, hash-paired, full-history-readable audit evidence remains the invariant.

## Decision

Memoria's telemetry is **three planes, separated by their intrinsic requirements**, not one log family:

- **Audit plane** — forensic: *"what writes hit the vault, and were they authorized?"* This is `audit.jsonl` today, and may become a union of per-machine audit files when multi-machine writes are enabled, plus its deterministic per-session digest projection ([ADR-25](25-session-logging-two-logs.md)). Content-free, append-only, with per-write SHA-256 before/after hashes. **Its tamper-evidence and sync substrate is Git, not in-file cryptography.** The vault is already a Git repository; commit history is a Merkle chain, a remote the researcher does not solely control is a genuine second trust domain, and signed commits (optional) add authorship. Memoria therefore does **not** add a per-entry `prev_hash` chain: a linear chain forks under the multi-machine reality ([ADR-63](63-multi-machine-deployment.md)) and is recomputable by whoever owns the file, so it adds complexity without a guarantee Git does not already give. Per-write pairing stays (it pins vault content state at finer grain than a commit); external cryptographic anchoring (OpenTimestamps / RFC-3161) is **deferred** until a second party or compliance driver makes it more than theater under single-researcher scope ([ADR-24](24-single-researcher-scope.md)).
- **Analytics plane** — operational and publication signals: board state, transitions, disposition, cost, attention, triage, linkage, lint findings. **Content-free** (hashes, IDs, counts, enums, durations — never note content), retained, and Git-synced. Derived metrics (lane notes, trust-score, eval trends) are **pure, reproducible projections** over these events — never a second source of truth, so a formula change re-runs over history rather than going dark. The plane is a small set of streams grouped by writer and cadence, not one merged stream and not a file per metric.
- **Diagnostic plane** — operability: *"why did Memoria's own code break?"* Structured records from Memoria's **own Python MCP servers and Operations only** — never agent cognition, which lives inside the external, unmodified Hermes runtime ([ADR-22](22-build-on-hermes-runtime.md)) and is unreachable. This plane lives **outside the vault and outside Git**, is rotated and disposable, defaults to errors/warnings, and is content-light by default. Its full privacy and lifecycle contract is [ADR-105](105-diagnostic-plane.md).

**Multi-machine partitioning is the migration target once more than one machine writes.** Because the vault syncs by Git and exactly one dispatcher runs per vault but the dispatching machine can change over time ([ADR-63](63-multi-machine-deployment.md)), every Git-synced plane (audit, analytics) must move to **per-machine files** before multi-machine writes are supported — a `machine` stamp in the envelope and in the filename — so two machines appending across a sync never collide. This generalizes the per-session-file naming already used for digests. The diagnostic plane is out of Git, so it is per-machine by construction. Until that trigger fires, the current single-machine audit and analytics files remain valid current behavior.

## Consequences

- When multi-machine writes are enabled, the audit log moves from a single shared `audit.jsonl` to per-machine audit files; every full-history consumer (the pairing reads, `vault-hash-drift`, the digest writer) reads the union. This is the cost of conflict-free Git merges across machines. Until then, this ADR records the target layout rather than requiring an immediate migration.
- Integrity ties to Git: the guarantee is only as strong as "an out-of-your-sole-control remote plus you do not force-push history." A self-hosted vs. hosted remote is the lever for how much activity-cadence metadata leaves the machine — content-free, but a timestamped trail reveals *when* the researcher works.
- The diagnostic plane fills the operability gap but is honestly scoped: it cannot see prompts, agent retries, or tool-selection inside Hermes. Whole-system diagnosis is not on offer; Memoria-side failure diagnosis is.
- Three planes mean three retention rules (audit: forever; analytics: retained, content-free; diagnostic: rotated, disposable) and three privacy rules. This is more written policy than one log family, but each rule is simpler because it serves one reader.
- Reproducibility is preserved: wall-clock timestamps remain event facts, but no vault content or nondeterministic derived state enters the audit/analytics planes that digests and the benchmark read. Derived metrics stay pure projections over retained events. The diagnostic plane is explicitly non-canonical, so its timing-dependence and lossiness pollute nothing reproducible.
- No heavyweight "spine": there is a shared event envelope and a small emit helper per language, not a correlation-ID propagated through Hermes (impossible across an unmodified runtime) nor a taxonomy registry. `task_id` remains the join key where a card exists.

## When this matters

The diagnostic plane becomes worth building the first time a Memoria MCP/Operations failure is diagnosed by guesswork because stderr was gone — most concretely during unattended `always-on` operation ([ADR-63](63-multi-machine-deployment.md)), where no human watches the terminal. The per-machine partitioning becomes load-bearing the moment a second device writes to the vault. Until either is real, the existing single-machine audit + analytics streams are adequate; this ADR records the shape so the move is a refactor, not a redesign.

## Alternatives considered

**Keep one log family, add levels/rotation to it.** Rejected: forces forensic-permanence rules onto disposable diagnostics and content-free rules onto the one plane that needs content, while still not separating the readers. The planes have opposite requirements; one substrate serves none well.

**Collapse the analytics streams into a single event stream.** Rejected as dogma: for a single-user local tool it is a wash — one envelope and metrics-as-projection are the real wins, and those hold with a few cadence-grouped streams without making every reader filter one firehose or making a corrupt line poison everything.

**Per-entry hash-chaining of the audit log (with later external anchoring).** Rejected on merits, not authority: Git already provides a Merkle chain plus remote anchoring and merges without forking, whereas a linear in-file chain forks across machines and is recomputable by the file owner — speculative generality for a future the single-researcher scope does not have.

**A correlation/trace ID propagated across all processes.** Rejected: it cannot be threaded through the external unmodified Hermes runtime, and at n=1 local there is no service mesh to reconstruct. `task_id` already correlates everything card-scoped.

## Related

- **Related decisions / Depends on:** [ADR-25 (two session logs)](25-session-logging-two-logs.md) (the audit plane; amended by this ADR only for future multi-machine storage layout); [ADR-20 (publication path)](20-publication-path.md) (the analytics plane's capture-now mandate); [ADR-63 (multi-machine deployment)](63-multi-machine-deployment.md) (partitioning); [ADR-24 (single-researcher scope)](24-single-researcher-scope.md) (the integrity threat model); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) (why agent cognition is unreachable).
- **Decided separately:** [ADR-105 (diagnostic plane)](105-diagnostic-plane.md); [ADR-106 (cost and disposition capture)](106-cost-and-disposition-capture.md).
- **Tracking issue:** [#735](https://github.com/eranroseman/memoria-vault/issues/735) — implementation readiness and ADR-25 mapping.
- **Design rationale:** [Telemetry architecture](../explanation/architecture/telemetry-architecture.md).
- **Reference:** [Telemetry & logs](../reference/telemetry.md); [Policy MCP](../reference/policy-mcp.md).


---

<!-- source: adr/105-diagnostic-plane.md -->

# ADR-105: Content-light diagnostic plane — out of the vault, ephemeral, opt-in detail

## Context

The three-plane model ([ADR-104](104-telemetry-three-planes.md)) introduces a diagnostic plane to close a real gap: Memoria's own deterministic code (MCP servers, ingest, crons) currently fails with nothing but stderr, so an already-happened or intermittent failure cannot be diagnosed. But this plane is the **first place vault-derived content could land in a log** — failed-request payloads, malformed note lines, provider error bodies — and Memoria's posture is otherwise content-free ([Telemetry & logs](../reference/telemetry.md)) and local-first. Done naively it would convert a content-never-logged system into one where a forgotten debug flag plus a routine `git push` exfiltrates unpublished research. The norm across comparable local tools (Obsidian plugins, VS Code, local AI runtimes) is also unambiguous: ship diagnostics, default them quiet, keep content behind a distinct opt-in, and never auto-exfiltrate. This decision fixes the plane's privacy and lifecycle contract so the benefit is captured without the leak.

## Decision

Memoria's diagnostic plane is **content-light, local, and disposable**, governed by these rules:

- **Scope: Memoria's own Python MCP servers and Operations only.** Agent reasoning, prompts, retries, and tool selection live inside the external unmodified Hermes runtime ([ADR-22](22-build-on-hermes-runtime.md)) and the MCP-only sandbox ([ADR-46](46-seven-layer-architecture.md)) and are not reachable; the plane does not pretend to cover them.
- **Outside the vault, outside Git.** Diagnostic files live under an OS state directory (`$XDG_STATE_HOME/memoria/diagnostics/`, falling back to `~/.local/state/memoria/diagnostics/` on Linux/WSL), **never** under `system/logs/` or anywhere in the Git-tracked, sync-tracked vault tree. A `.gitignore` entry is a belt-and-suspenders backstop, not the primary control. Each machine keeps its own; diagnostics are not shared state.
- **Content-light by default, deny-by-default for raw payloads.** Default capture is errors and warnings as **typed error codes plus a SHA-256 + length of any payload** — never the payload itself, never free-text that embeds content. Paths and note titles are treated as content (hashed or basename-stripped) in anything shareable. Raw payloads are available only through an **ephemeral, self-disarming capture**: a single run/session that reverts to content-light on restart, with a visible banner while active. There is no persistent "log content = on" configuration key.
- **Leveled and bounded.** Levels are error/warn/info/debug/trace, default errors-and-warnings, raised per-component via an environment variable. Files rotate by size with an explicit backup cap (bounded total footprint, tens of MB), compressed; diagnostics are troubleshooting aids, not a record.
- **No remote telemetry.** Nothing is sent anywhere automatically. Sharing is a single **user-triggered redacted bundle** that is **human-reviewable before it leaves the machine** and is covered by a redaction self-test (a golden corpus of known-sensitive strings asserted absent). The bundle defaults to codes-and-hashes; including any raw content is a separate, per-bundle, explicit opt-in.

## Consequences

- The operability gap is closed for the parts Memoria controls, which are the parts that actually break, without adding a content-exfiltration surface.
- Diagnostics from one machine are invisible on another — acceptable, because they are local troubleshooting, not shared record.
- "Content-light by default" means the *most useful* debugging detail (the exact bad payload) needs the deliberate ephemeral capture step. This is a real friction, accepted as the price of the privacy guarantee.
- A small dependency (a structured-logging library) and a first-party redaction step enter the codebase; redaction logic and its golden-corpus test stay first-party and unit-tested rather than delegated to a transitive dependency.
- The shared envelope ([ADR-104](104-telemetry-three-planes.md)) must keep the diagnostic plane's rotation/disposal rules from ever touching the audit plane's append-only-forever rule, and vice versa — the planes share an envelope, not a retention policy.

## When this matters

The plane earns its place the first time an unattended `always-on` run ([ADR-63](63-multi-machine-deployment.md)) or a cron fails and the cause is unrecoverable from stderr. The ephemeral content-capture path matters only when a typed error code plus payload hash is genuinely insufficient to reproduce a parse/enrichment failure — build the content-light core first and add the capture path on first real need.

## Alternatives considered

**Full structured logging with content, redacted by an allow-list at emission, stored in `system/logs/`.** Rejected: an allow-list cannot sanitize free-text error bodies, malformed lines (whose payload *is* the content), or tracebacks, and `system/logs/` is Git-tracked and pushed — one forgotten toggle plus `git push` leaks unpublished notes. The "off OneDrive" protection does not cover the Git channel.

**Opt-in-only, no standing diagnostic file (bundle-on-demand only).** Rejected as the sole model: it cannot diagnose intermittent or already-happened failures, because nothing was recording when the bug occurred. Kept as the *sharing* model, layered over a content-light standing log.

**Persistent content-logging toggle.** Rejected: for the single non-expert user ([ADR-24](24-single-researcher-scope.md)) a left-on flag is the classic forgotten-leak, and a verbosity/content config surface fights the opinionated-not-configurable posture. Ephemeral self-disarming capture gives the capability without the standing risk.

## Related

- **Related decisions / Depends on:** [ADR-104 (telemetry three planes)](104-telemetry-three-planes.md) (the plane this details); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) and [ADR-46 (seven-layer architecture)](46-seven-layer-architecture.md) (why agent cognition is out of scope); [ADR-24 (single-researcher scope)](24-single-researcher-scope.md) (the one-user foot-gun argument).
- **Tracking issue:** [#736](https://github.com/eranroseman/memoria-vault/issues/736) — implementation-readiness tracker; closed after `memoria/runtime/diagnostics.py` and its unit tests shipped.
- **Design rationale:** [Telemetry architecture](../explanation/architecture/telemetry-architecture.md).
- **Reference:** [Telemetry & logs](../reference/telemetry.md) (the content-free posture this plane is the sole exception to).


---

<!-- source: adr/106-cost-and-disposition-capture.md -->

# ADR-106: Cost and disposition capture — Hermes session store and the review action

## Context

At the time of this decision, two analytics signals the publication path depends on ([ADR-20](20-publication-path.md)) — per-card **cost/tokens** and reviewer **disposition** (accept / edit / reject) — were empty. The reference doc attributed this to an upstream limitation: that the current Hermes did not surface a cost/token overlay in its serialized card JSON, so the exporter had nothing to read. Verification against the installed Hermes (v0.14.0) showed that explanation was misleading. Hermes **does** compute and persist per-call cost and token usage — in its per-profile session store, not on the card — and the data is reachable from Memoria without modifying Hermes. The exporter was querying the one CLI endpoint (`kanban list --json`) that drops it. These signals cannot be back-filled ([ADR-20](20-publication-path.md)), so every day they stayed empty was permanently lost data; the fix should not wait on an upstream change that is not actually required.

## Decision

Memoria captures both signals at points it controls, per machine ([ADR-104](104-telemetry-three-planes.md)):

- **Cost / tokens — from the Hermes session store.** A Memoria-side exporter (host tooling, not an agent toolset, so unaffected by the MCP-only sandbox) reads, per completed card, the run metadata exposed by `hermes kanban show <id> --json` (`runs[].metadata.worker_session_id`), joins it to the per-profile session store (`~/.hermes/profiles/<lane>/state.db`, `sessions` table), and emits a cost event carrying Hermes's already-priced figures: `input_tokens`, `output_tokens`, cache and reasoning tokens, `estimated_cost_usd`, and the provenance fields (`cost_source`, `billing_provider`, `pricing_version`). Memoria does **not** maintain its own pricing table — it records Hermes's estimate and its provenance. The session store is per-machine and unsynced, so this exporter runs on each machine that dispatches and writes that machine's partitioned cost events.
- **Disposition — at the review action.** The accept / edit / reject outcome is a human decision taken in Obsidian, not an inference event. It is captured where the PI resolves a review (the board/QuickAdd review action), the same Memoria-controlled surface that already emits `attention` and `triage` — never inferred from a card-metadata overlay.

Because this couples to Hermes's internal, undocumented SQLite schema, Memoria pins the
**observed session-store contract** with a **Hermes cost doctor** before any
updater/exporter automation trusts the join. The doctor verifies, against the installed
Hermes runtime under test, that `hermes kanban show <id> --json` exposes
`runs[].metadata.worker_session_id`, that the per-profile `state.db` has the expected
`sessions` table shape, that a fixture or recent completed card can join from card run
to session row, and that missing-session cases fail closed with a counted miss rather
than a fabricated zero. Each Hermes upgrade must follow the same order: upgrade first,
verify the join, then re-enable cost export. A local model-gateway proxy at the profile
`base_url` remains a documented future option if provider-independent or actual (not
estimated) cost is ever required, but is **not adopted** now: it would re-capture data
Hermes already stores and add a process in the inference hot path.

## Consequences

- Both benchmark signals are populated at Memoria-controlled capture points, with no Hermes modification and no inference-path risk.
- The cost figure is Hermes's **estimate** (with the current kilocode provider `actual_cost_usd` is null); the recorded `cost_source` / `pricing_version` make that explicit rather than silently presenting an estimate as actual.
- Coupling to a private Hermes DB schema is brittle across upgrades — the contract doctor plus upgrade-time verification is the standing maintenance cost this accepts.
- Cost capture is per-card via a `kanban show` call per completed card and a session-store lookup; session rotation can occasionally drop an aged session (observed ~1 in 13), so a small miss rate is expected and not treated as an error.
- The misleading "upstream limitation" note in [Telemetry & logs](../reference/telemetry.md) is corrected to describe the real mechanism and its brittleness.
- [ADR-62](62-measurement-and-verification-harnesses.md)'s current implementation mapping records the session-store/review-action capture path.

## When this matters

This matters as soon as the publication benchmark ([ADR-20](20-publication-path.md)) needs real cost or acceptance-quality numbers — i.e. before any run whose cost or disposition is meant to appear in the paper. Until then the capture is wired but the absence is documented, not silently empty.

## Alternatives considered

**Wait for Hermes to surface the card overlay (status quo).** Rejected: it leaves an un-back-fillable signal empty indefinitely, gated on an upstream roadmap, when the data is already reachable today.

**Local model-gateway proxy at the profile `base_url`.** Rejected for now: it couples only to the stable OpenAI wire protocol (a real advantage) but re-captures data Hermes already prices, adds a daemon in the inference hot path, and would need its own pricing table for dollars. Kept on the shelf for provider-independence or actual-cost needs.

**Scrape Hermes logs post-hoc.** Rejected: more brittle than the session store and not guaranteed to contain usage at all.

## Related

- **Related decisions / Depends on:** [ADR-20 (publication path)](20-publication-path.md) (the capture-now mandate these signals serve); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) (the runtime whose store is read); [ADR-104 (telemetry three planes)](104-telemetry-three-planes.md) (the analytics plane and per-machine partitioning).
- **Files affected:** [`src/.memoria/mcp/board_export.py`](https://github.com/eranroseman/memoria-vault/blob/main/src/.memoria/mcp/board_export.py) (the exporter CLI/orchestrator) and [`src/.memoria/mcp/board_export_cost.py`](https://github.com/eranroseman/memoria-vault/blob/main/src/.memoria/mcp/board_export_cost.py) (the session-store join and cost doctor).
- **Tracking issue:** [#737](https://github.com/eranroseman/memoria-vault/issues/737) — implementation readiness and Hermes cost doctor.
- **Reference:** [Telemetry & logs](../reference/telemetry.md) (cost/disposition schemas and the corrected mechanism note); [Hermes CLI](../reference/hermes-cli.md).


---

<!-- source: adr/107-okf-interchange-bundle-format.md -->

# ADR-107: OKF as Memoria's import/export bundle format

## Context

Memoria's substrate — a directory of markdown files with YAML frontmatter,
`type`-routed presentation, path-derived ids, links between notes, agent- and
version-control-friendly — was independently arrived at by Google Cloud's **Open
Knowledge Format** (OKF, `okf/SPEC.md`, v0.1 draft). The convergence is near
total: OKF's *Concept* is a typed markdown document (a tangible asset or an
abstract idea), its *Concept ID* is the file path minus `.md`, relationships are
markdown links, and it reserves `index.md` (progressive disclosure) and `log.md`
(history). That an external, vendor-backed spec landed on the same shape is
validation of [ADR-47](47-type-first-category-folders.md) /
[ADR-26](26-repo-as-install-unit.md), but it also names a contract Memoria lacks.

Memoria's **outbound** layer is its least-defined. The Path-4 open-artifact
release is deferred ([ADR-20](20-publication-path.md)); navigation spaces
([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)) and the
disposable projection engine ([ADR-102](102-disposable-projection-engine.md))
produce views with no *named, runtime-independent* serialization. OKF supplies
exactly that missing unit: the **Knowledge Bundle**, "the primary unit of
distribution," consumable without Memoria's gates, MCPs, or Hermes runtime.

OKF's defining trait, however, is the inverse of Memoria's thesis. OKF mandates
permissive consumption — "Consumers MUST NOT reject a bundle because of missing
optional fields, unknown `type` values, or broken cross-links" — and holds that "the
specific kind of relationship is conveyed by the surrounding prose, not by the link
itself." Memoria deliberately rejected prose-typed relationships in favor of typed
edges ([ADR-08](08-typed-relations-frontmatter.md) →
[ADR-52](52-links-vs-relationships.md)) because graph queries need the type *on*
the edge, and it enforces strict schemas, controlled vocabularies, and category-error
rejection in the Linter. OKF is therefore a fit for the **boundary**, not the core.

## Proposal

Memoria may treat OKF as its import/export lingua franca, adopted strictly at the
vault boundary and never as a relaxation of the internal model.

**Export.** A projection or navigation space may be serialized as an
OKF-conformant Knowledge Bundle: one Memoria note or catalog entity → one OKF
concept; the projection's folder tree → the bundle tree; the bundle's root
`index.md` declares `okf_version`. The export is **lossy by contract**, and the
loss is documented, not hidden:

- typed `links:` / `relationships:` ([ADR-52](52-links-vs-relationships.md))
  collapse to untyped markdown links, with the relation type emitted as prose per
  OKF convention — graph-queryable typing does not survive the round trip;
- `lifecycle` / `maturity` / gate state ([ADR-50](50-universal-lifecycle-and-maturity.md))
  survive only as custom frontmatter that conformant consumers may ignore;
- the bundle carries no gate, no Linter, and no MCP surface — it is inert data.

The serialization runs through the projection engine's reconciliation and failure
model ([ADR-102](102-disposable-projection-engine.md)) rather than as a bespoke
emitter; bundles are disposable consumer-only artifacts, not a second source of
truth.

**Import.** An external OKF bundle may be ingested as a new source type through the
deterministic pipeline ([ADR-30](30-deterministic-ingest-pipeline.md)). OKF
concepts enter as candidate material subject to the normal write/link gates
([ADR-28](28-write-gate-as-plugin.md)) — Memoria's tolerance of OKF's permissiveness
stops at ingest; nothing from a foreign bundle reaches a canonical surface ungated.

**Conventions borrowed outright.** Independently of the bundle contract, Memoria
may align two cheap conventions: a standardized `index.md` progressive-disclosure
manifest at folder roots, and OKF's reserved body headings `# Schema` /
`# Examples` / `# Citations` as a presentation convention for notes that already
carry that content.

## Consequences

- Memoria gains a runtime-independent publication artifact, de-risking the deferred
  Path-4 release ([ADR-20](20-publication-path.md)) and making "exports as OKF
  bundles" an interoperability claim in an emerging agent-knowledge ecosystem.
- Export is lossy; the typed-relation and gate-state loss must be stated in the
  bundle and in user-facing docs so a shared bundle is never mistaken for the live
  vault.
- Import widens the inbound surface to foreign bundles; the gate, not OKF's
  permissive consumer rule, governs what lands.
- A new serialization format to track against OKF's version line; `okf_version`
  pins the target and bounds breakage.
- No change to the internal model: typed links, strict schemas, and category-error
  rejection stay as-is. OKF's permissiveness is honored only when *reading* foreign
  bundles, never when authoring Memoria's own.

## When this matters

This becomes worth deciding when there is a concrete consumer for an exported
bundle (a publication artifact, a shared subset, another tool that reads OKF), or a
concrete foreign OKF corpus worth ingesting. Below that, the projection and ingest
layers already cover internal needs and the format adds surface without a reader.
OKF is a v0.1 draft; its stability and adoption are themselves a gating signal.

## Alternatives considered

**Invent a Memoria-specific export schema.** Rejected: it repeats OKF's design with
none of its interoperability, and forfeits alignment with a vendor-backed format
that already matches the substrate.

**Adopt OKF's permissiveness internally** (untyped prose relationships, tolerate
unknown types, never reject). Rejected outright: it is the inverse of the typed-edge
and structural-gate thesis ([ADR-52](52-links-vs-relationships.md),
[ADR-28](28-write-gate-as-plugin.md)) — Memoria is deliberately *ahead* of OKF here.

**Export only, no import.** Viable as a first slice, but the inbound direction is
near-free given the format symmetry and positions Memoria to consume the broader OKF
corpus; deferring it is a sequencing choice, not a different decision.

## Related

- **Workflows affected:** publication / open-artifact release, navigation-space
  export, OKF-bundle ingest.
- **Files affected:** future OKF (de)serializer under `src/.memoria/operations/`,
  the projection registry ([ADR-102](102-disposable-projection-engine.md)), the
  ingest pipeline source-type registry ([ADR-30](30-deterministic-ingest-pipeline.md)),
  schema/Linter conformance for emitted bundles.
- **Related decisions / Depends on:**
  [ADR-26](26-repo-as-install-unit.md),
  [ADR-30](30-deterministic-ingest-pipeline.md),
  [ADR-47](47-type-first-category-folders.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-52](52-links-vs-relationships.md),
  [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md),
  [ADR-102](102-disposable-projection-engine.md);
  serves the deferred Path-4 release of [ADR-20](20-publication-path.md).
- **Reference:** Open Knowledge Format (OKF) v0.1 draft —
  `GoogleCloudPlatform/knowledge-catalog`, `okf/SPEC.md`.
- **Tracking issue:** [#753](https://github.com/eranroseman/memoria-vault/issues/753).


---

<!-- source: adr/108-liteparse-local-document-parsing.md -->

# ADR-108: LiteParse as the local document-parsing engine

## Context

The tiered ingest pipeline ([ADR-30](30-deterministic-ingest-pipeline.md)) prefers
pre-extracted full text (PMC, S2ORC, CORE, arXiv) and falls back to parsing a local
Zotero PDF, with OCR as the last resort. The local-parse tier uses `pymupdf4llm`,
which wraps PyMuPDF. Two properties of that choice are worth revisiting:

- **License.** PyMuPDF is **AGPL-3.0** (dual-licensed commercial). Memoria ships it
  in the deterministic ingest stack, which is the strictest license obligation in
  the dependency set.
- **Parse surface.** ADR-30 already isolates the parser in a subprocess with
  `rlimit` caps because MuPDF has a CVE history; the C parsing surface is the
  reason the sandbox exists.

[LiteParse](https://github.com/run-llama/liteparse) (LlamaIndex, released March 2026)
is a **Rust**, **Apache-2.0** document parser that runs entirely local — no cloud,
no LLM, no API key — and emits Markdown with spatial layout, bounding boxes, and
built-in Tesseract OCR. It parses PDF plus DOCX/XLSX/PPTX and PNG/JPG, and ships a
Python binding. Its design statement is nearly a restatement of
[ADR-30](30-deterministic-ingest-pipeline.md) / [ADR-32](32-external-access-over-mcp.md):
offline, deterministic, no model in the loop. This is the opposite of GROBID/Marker,
which ADR-30 rejected as too heavy.

Because LiteParse would live in the self-hosted ingest tier (a library dependency of
`extract.py`, run as an MCP tool), not as an agent capability, it does not touch the
MCP-only sandbox boundary.

## Proposal

Memoria may replace the `pymupdf4llm` + OCR fallback in the ingest
full-text extractor (`extract.py`) with
LiteParse, keeping the existing subprocess `rlimit` sandbox, lazy import, and
extraction-coherence checks (≥200 chars/page, ≤2% replacement chars). LiteParse's
DOCX/XLSX/PPTX support would also be the parsing substrate if Memoria later admits
office-document source types.

This is **deferred, not adopted**. The local-parse tier is a last-resort fallback
(most full text arrives pre-extracted), so the upside is bounded and does not justify
betting the deterministic spine on a library with no track record.

## Consequences

- Drops the only AGPL dependency in the ingest stack for an Apache-2.0 one.
- Replaces a C parse surface (MuPDF CVE history) with a memory-safe Rust core; the
  subprocess sandbox stays regardless, since Tesseract and the format parsers remain
  untrusted input.
- Adds office-document and real OCR capability the current tier lacks.
- Spatial-layout and bounding-box output is unused by today's text→markdown pipeline;
  it is latent value, not a current need.
- Takes a dependency on a young library (released March 2026) in a reliability-
  sensitive path.

## When this matters

Adopt when any of these trips, not before:

- LiteParse reaches a stable Python API with roughly 6–12 months of track record.
- The PyMuPDF AGPL obligation becomes a real constraint (relicensing, distribution).
- OCR / scanned-PDF quality becomes an actual ingest pain point.
- Memoria commits to office-document ingestion.

The trial gate is a head-to-head against `pymupdf4llm` on the real Zotero corpus,
scored by the existing coherence checks, before any switch.

## Alternatives considered

**Adopt now.** Rejected: the library is ~3 months old and the local-parse tier is a
narrow fallback, so the reliability risk outweighs the bounded gain.

**Keep `pymupdf4llm` indefinitely.** The default if no trigger trips, but it leaves
the AGPL obligation and the MuPDF parse surface in place.

**LlamaParse or other cloud parsers.** Rejected: cloud, API-key, and (for LlamaParse)
LLM-in-the-loop dependencies are incompatible with the offline-first stance of
[ADR-30](30-deterministic-ingest-pipeline.md) and [ADR-32](32-external-access-over-mcp.md).

## Related

- **Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md),
  [ADR-32](32-external-access-over-mcp.md).


---

<!-- source: adr/109-project-management-native-views.md -->

<!-- cspell:words Gantt TTRPG Vikunja Thino -->

# ADR-109: Project management uses native views over project notes

## Context

Issue [#329](https://github.com/eranroseman/memoria-vault/issues/329) surveyed
Obsidian project-management plugins and methodologies for the Project space. The
survey evaluated whether Memoria should adopt a PM plugin stack, borrow patterns
from those tools, or reject them where they conflict with the vault's gate and
lifecycle model.

Memoria's constraints rule out most PM plugins as write surfaces: state must stay
plain-text, git-diffable, lintable, and owned by the existing schemas; the universal
lifecycle is the status vocabulary; and a view must not become a second frontmatter
authority that writes outside the policy MCP. The recurring conflict is the same
class of defect recorded in [ADR-12](12-obsidian-linter-reference-only.md): a plugin
that looks convenient but rewrites, renames, or duplicates state the vault already
owns.

## Decision

Memoria's Project workspace uses Memoria-native project notes plus read-only views:
Bases for portfolio/table surfaces, Dataview where calculated dashboards are needed,
Modal Forms for schema-valid project creation, and the existing lifecycle/project
fields as the single source of truth. Project-management plugins may be studied for
interaction ideas, but they are not adopted as bundled dependencies when they write
parallel status fields, store project state outside notes, move files as workflow
state, or depend on an external service as the source of truth.

The only surveyed plugin class that remains a candidate for normal use is a
plain-Markdown checkbox task layer, specifically the Obsidian Tasks plugin, and only
as an optional/recommended human-surface tool. Tasks metadata stays in note bodies; it
does not become gated schema state and does not replace project lifecycle fields.

## Consequences

- Project state continues to live in `projects/` notes and their schema fields, not
  in plugin databases, plugin `data.json`, external PM services, or board-column
  sync state.
- The Project space can borrow PM affordances without adopting their storage model:
  portfolio views, next-action lists, stuck-project queries, WIP visibility,
  milestone/progress summaries, and read-only relationship graphs.
- Drag-to-status boards, folder-shuffling methods, and plugin-owned status
  vocabularies remain out of bounds unless they can render from existing fields
  without writing them.
- Tasks-style checkboxes may help humans run a project locally, but they are a body
  affordance, not a policy-gated contract.
- Future Project-space work should be framed as arrangements of existing primitives
  first: project note, project Bases, per-project dashboard, related claims/sources,
  and review/worklist inputs.

## Alternatives considered

**Adopt native Obsidian Bases and Dataview.** Adopted. They are already bundled or
native, read the vault's plain-text fields, and match [ADR-49](49-catalog-in-bases-linter-monitor.md)'s
view-layer model.

**Adopt the Tasks plugin for human todos.** Borrow/adopt as an optional recommended
plugin, not a bundled dependency. Tasks is plain Markdown and git-diffable, so it fits
better than most PM plugins, but its checkbox metadata is body-local human context,
not a replacement for project schemas or lifecycle.

**Adopt obsidian-kanban.** Rejected as a dependency; borrow only the WIP/board
interaction idea. Board-as-Markdown is attractive, but drag-to-status workflows invite
dual-state drift, and bundling adds licensing/maintenance cost when Bases can render
from the canonical fields.

**Adopt Projects-style plugins.** Rejected. The surveyed Projects-style plugins either
are abandoned, store view/project state in plugin configuration instead of notes, or
write their own status fields outside the gate. Native Bases covers the useful view
layer without adding a second state owner.

**Adopt obsidian-pm / Project Manager.** Rejected; borrow feature scope only. It has
useful PM affordances (tables, Gantt, Kanban, dependencies, scheduling), but it owns a
parallel status vocabulary and rewrites frontmatter in ways that would destroy
Memoria-owned fields.

**Adopt Project Browser.** Rejected; Bases supersedes the useful part. Its card views
are relevant, but auto-writing `state`/`priority` fields creates a second workflow
authority.

**Adopt Relations.** Reject as a bundled plugin, borrow the read-only graph pattern.
Its read-only posture fits Memoria, but its schema expectations and TTRPG domain do
not. It remains a design reference for a future typed-relationship graph over
`links:` and `relationships:`.

**Adopt external bridges such as Todoist, Vikunja, or GitHub Projects.** Rejected as
Project-state backends. They make the external service the source of truth and the
vault a projection. One-way mirrors may still be considered separately for
notification convenience, as in [ADR-85](85-todoist-gap-card-mirroring.md).

**Adopt Day Planner, Tracker, Thino, Task Genius, or Checklist.** Rejected for the
baseline Project workspace. They either solve adjacent time-tracking/charting
problems, overlap existing QuickAdd/Modal Forms/Dataview surfaces, have licensing
concerns, or are stale.

**Adopt PARA or Johnny Decimal folder methods.** Rejected as mechanics; borrow only
the "active committed project" lens from PARA. Folder moves as workflow state conflict
with [ADR-47](47-type-first-category-folders.md) and
[ADR-50](50-universal-lifecycle-and-maturity.md).

**Borrow GTD, Agile/Kanban, Zettelkasten, MOC/hub, and research-specific PM methods.**
Borrowed selectively. The useful parts are queryable project dashboards, WIP
visibility, next-action/stuck-project views, weekly review prompts, hub-like project
workbenches, and source/claim/project progress rollups.

## Related

- **Workflows affected:** Project space, project notes, Project gate views, Library
  reading pipeline, weekly review.
- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-49](49-catalog-in-bases-linter-monitor.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-54](54-two-decision-kinds-batch-worklists.md),
  [ADR-77](77-project-gate.md), [ADR-81](81-persistent-gate-dashboards.md).
- **Source discussion:** [#329](https://github.com/eranroseman/memoria-vault/issues/329).


---

<!-- source: adr/110-ruff-format-python-layout.md -->

# ADR-110: Ruff — formatter owns layout (line-length 100), curated lint ruleset

This ADR records two related decisions about the Ruff configuration: how layout is
governed (the **formatter**) and what the **linter** checks. Both were rethought from
first principles for an all-agent contributor model.

## Context

Ruff has been the Python linter for repo tooling and runtime code, but `ruff format`
was deliberately **not** used, and the lint selection was a small set
(`F/E4/E7/E9/W/I/B/C4/UP/RUF/PIE`). The recorded rationale for not formatting was that
the codebase was hand-formatted — "aligned comment columns, deliberate line breaks" —
and that reformatting would churn ~2k lines for no behavioral gain, with "many lines
intentionally long" cited as the reason E501 stayed disabled.

Two facts undercut that rationale once examined against the actual code:

- **All Python here is generated and maintained by agents**, across many independent
  sessions. There is no human artisan whose deliberate layout would be churned. What
  looked like intentional style is per-session entropy: collections, for example, were
  a ~43/57 split between compact multi-item rows (721) and one-item-per-line (936),
  and ~112 of 148 files lacked the conventional blank line after the module docstring.
  There was no coherent house style to protect.
- **The codebase is not wide.** Of 21,109 lines, ~96% fit within 88 columns; only 50
  exceed 120, and those are long string literals (argparse help, prompt and
  error text) that a formatter cannot break and leaves untouched. "We write wide code on purpose" did
  not describe the real situation — a handful of long *strings* did.

With an all-agent contributor model, any consistent style — even a hand-curated one —
is unmaintainable without a formatter, because every new session re-injects its own
defaults. A formatter is the only mechanism that holds a style steady against that
drift, and it removes a whole class of whitespace-only diffs and merge conflicts
between concurrent agent sessions.

## Decision

### Formatter — owns layout

Adopt `ruff format` as the single source of truth for Python layout in `memoria/`,
`scripts/`, `src/.memoria/`, `.github/scripts/`, and `tests/`, at **line-length 100**.

Enforcement mirrors the existing `ruff check` wiring: a `ruff-format` pre-commit hook,
a `ruff format --check` step in the CI `lint` job, and the same in `scripts/test.sh`
L0. E501 stays disabled — the formatter owns width, and the only remaining over-100
lines are string literals it cannot break, so E501 would only add noise.

Line-length 100 is chosen from the distribution, not convention: it leaves the
comfortable 88–100 one-liners agents already produce intact, wraps only the longer
expressions that genuinely benefit, and roughly halves the one-time reformat churn
versus the 88 default. The bulk reformat is isolated in a single commit listed in
`.git-blame-ignore-revs` so `git blame` continues to attribute lines to their real
authors.

### Linter — curated high-signal ruleset

The linter's job is to catch real bugs, enforce the consistency the formatter cannot
(imports, idioms), and modernize — not to relitigate layout. The selection adds, on
top of the prior set, rules chosen for what agents plausibly get wrong here:

- `A` (shadowing `id`/`type`/`list`/`dict`), `PT` (pytest-style), `DTZ` (naive
  datetimes), `FLY` (`str.join` → f-string), `BLE` (blind `except`), `S`
  (bandit — the real subprocess/network/deserialization surface), `RET` (return
  hygiene).

Three classes of rule are turned **off** with inline rationale, each because it is
noise *for this codebase*, not because the rule is bad:

- **Layout-owned:** `E1/E2/E3`, `W291/293`, `E501`, `COM`, `ISC`, `Q` — the formatter
  owns these, and `COM`/`ISC` actively conflict with it.
- **Bandit threat-model misfits** for a local, single-user CLI (no untrusted remote
  input): `S603`/`S607`/`S310`/`S311`. The high-value S rules (yaml/xml/SQL injection,
  eval/exec, pickle) stay enabled. Tests ignore `S` wholesale; the e2e smoke harness
  ignores `S101`.
- **pytest-idiom rules** that clash with this suite's deliberately pytest-independent
  test style: `PT011`/`PT017`/`PT018`. Most test files do not import pytest so they run
  under both pytest and the ADR-44 `CheckHarness`; the `try/except/else` assertion idiom
  is intentional. `DTZ011` (`date.today()`) is off because local-date semantics are
  intended for a single-user vault.

The previously-deferred `UP017` ignore is dropped and the `datetime.timezone.utc` →
`datetime.UTC` migration completed (py311). Every finding the new rules surfaced was
resolved by a fix or a documented `# noqa` — never blanket suppression: broad excepts
are narrowed where the failure modes are knowable, otherwise kept broad with a one-line
justification at each deliberate fault boundary; a few security findings are annotated
false positives (e.g. `BaseLoader` keeps the GitHub Actions `on:` key a string where
`safe_load` would parse it to `True`; a parameterized query whose only interpolation is
a hardcoded column constant; XML parsed from the trusted NIH PubMed endpoint).

## Consequences

- Python layout is now deterministic and consistent across all agent sessions;
  formatting leaves every contributor's decision space.
- Whitespace-only diffs and the merge conflicts they cause between concurrent
  worktrees largely disappear.
- One-time churn: 112 files reformatted (+4215/−1865), behavior unchanged (433 tests
  pass, `ruff check` clean). The churn is mostly collection layout, driven by the
  trailing commas the codebase already uses, not by line-length.
- The dense compact-collection style is lost in a few places — `ruff format` explodes
  trailing-comma collections one-item-per-line. This is accepted as the cost of
  consistency; it is also more diff-friendly.
- A first `git blame` pass over reformatted lines requires the ignore-revs file (GitHub
  honors it automatically; locally `git config blame.ignoreRevsFile .git-blame-ignore-revs`).
- The wider lint ruleset now catches a real bug class going forward (builtin shadowing,
  naive datetimes, blind excepts, the dangerous bandit subset) and made every broad
  `except` carry an explicit justification or a narrowed type.
- Some broad excepts that are genuine fault boundaries now carry `# noqa: BLE001`
  comments; this is intended — it documents intent rather than hiding it.

## When this matters

Revisit the line-length choice only if the over-100 string-literal tail grows enough
that wrapping policy becomes a real readability problem, or if a future contributor
model (human-authored modules) reintroduces a deliberate style worth preserving
differently. Neither is the case today.

## Alternatives considered

**Keep Ruff linter-only (status quo before this ADR).** Rejected: it preserved
inconsistency, not craft — the measured 43/57 layout split is what "trust the agents
to be consistent" produces, and it drifts further every session.

**Line-length 88 (Black/Ruff default).** Rejected: it forces ~768 comfortable
88–100 one-liners to wrap for no readability gain and produces the most churn; its
only benefit is matching the ecosystem default.

**Line-length 120.** Rejected as the steady-state width: so permissive it rarely
engages (only ~1.2% of lines exceed 100), so it fails to enforce a sane width on
future sprawling expressions. It minimizes churn but at the cost of doing little.

**Keep the small lint set.** Rejected: it caught syntax/import errors but missed whole
bug classes (builtin shadowing, naive datetimes, blind excepts, unsafe deserialization)
that are exactly what agents get wrong.

**Enable the full bandit / pytest rule families.** Rejected: for a local single-user
tool, the subprocess/partial-path/urlopen/random bandit rules are threat-model misfits
that would be all-noise, and the pytest.raises-idiom rules fight this suite's
pytest-independent design. Enabling the high-signal members and turning the misfits off
with rationale beats both all-on and all-off.

## Related

- Formatter implemented in [PR #790](https://github.com/eranroseman/memoria-vault/pull/790).
- Lint ruleset implemented in [PR #794](https://github.com/eranroseman/memoria-vault/pull/794).


---

<!-- source: adr/111-two-mode-tutorial-spine.md -->

# ADR-111: Two-mode tutorial spine, seeded by a half-built corpus

This ADR records two coupled decisions about the onboarding tutorials: what the
tutorial **spine** is organized around, and how the one-sitting-vs-months problem is
solved with a **seeded completion corpus**. Both were rethought from the question
"what is a real Memoria use case?" rather than "what is the system's data model?"

## Context

The previous tutorials (`01-set-up-from-zero` … `07-find-new-sources`) walked the
note-type dependency graph in order: fleeting note → source → reading → claim → hub →
project → verify → discover. That was Memoria's internal data model, sequenced. The
step *titles* are already task-shaped, but the *spine* is the ontology, and two tells
give it away:

- **It starts on the fleeting note** — the system's cheapest object, not how a
  researcher actually enters. People arrive holding a paper they're reading or a thing
  they have to write; nobody arrives wanting to "create a fleeting note."
- **It is drawn as a line, but the system is a loop.** [The knowledge
  cycle](../explanation/knowledge/knowledge-cycle.md) is explicit that the cycle "is not
  a linear path"; `06` even names the "compounding loop." Real use is not one pass 1→7.

Stripped to user motivation rather than our nouns, Memoria has **one meta-use-case** —
sustain a months-to-years inquiry that *compounds* instead of decaying — which
decomposes into **two modes a researcher alternates between**:

- **Accumulate** (continuous, low-stakes per action) — turn what you read into durable,
  connected, traceable knowledge instead of a pile.
- **Produce** (periodic, high-stakes) — write something defensible from what you know.

Plus three jobs that serve the loop, not entered for their own sake: **stay honest**
(verify), **find the gaps** (discover), **don't rot** (maintenance the agent does). The
two failure modes named in [What Memoria is](../explanation/overview/what-memoria-is.md)
— "capture without synthesis" and "synthesis without rigor" — are exactly these two
modes *decoupled*. The product is keeping them coupled.

**The methodology problem this raises:** done for real, the loop takes months, so a
one-sitting tutorial cannot reproduce the payoff — writing from a *dense* claim graph —
without pre-existing state. The two modes compress differently: Accumulate is a
**habit** (only a single rep is teachable; the months are its repetition), Produce is an
**event** (naturally sitting-shaped, but it needs accumulated state the day-one vault
does not have).

A [deep-research pass](#related) over four adjacent domains (PKM tools, sample-database
pedagogy, SaaS onboarding, learning science) converged on the resolution and is the
evidentiary basis for the decision below.

## Decision

Restructure the tutorials around the two modes, and resolve the months-vs-sitting
problem by shipping a **small, authored, deliberately half-built sample corpus that the
learner finishes** — completing it *is* the core Accumulate lesson.

### Spine (6 tutorials, was 7)

| # | Tutorial | Mode | What the learner does | Ends with |
| --- | --- | --- | --- | --- |
| 00 | Set up and pick your path | Setup | Install, keys, meet the Co-PI. A **labeled fork**: "start with your own source" **or** "load the sample vault" (half-built, neutral topic, skippable). Write a one-line Produce goal. | A working vault, a goal, optionally a sample to *finish* |
| 01 | Bring in your first source | Accumulate | Capture a real source of your own from scratch (the independent rep). Sample's worked source notes sit alongside as models. Fleeting note demoted to a one-paragraph aside. | Own Catalog entity + source note |
| 02 | Build claims and connect them | Accumulate | The transfer-fragile move, **faded in one tutorial**: *study* a worked claim+links → *finish* the sample's un-distilled claims and un-made links → *then* distill your own source and wire it into the existing cluster. | A cluster, partly completed and partly built — dense enough to write from |
| 03 | Draft a section from your claims | Produce | Open a Project, map the now-dense corpus, draft from your own + completed claims with bound citations. | The 00 goal, in cited prose |
| 04 | Verify it holds | Produce | Verification pass; read finding-first cards; fix or trust. | A draft you'd defend |
| 05 | Close the loop | Capstone | A **planted gap** the map/draft surfaces becomes a discovery that sends you back to Accumulate. Meet the weekly review. Archive the sample if desired — it drops out without breaking links. | A loop you keep turning; a clean handoff to your own vault |

### Seed-corpus rules

1. **Half-built by design** — ~5 of ~8 sources fully worked; ~3 left as completion
   problems (source present, claims/links missing). Finishing them is tutorial `02`.
2. **Authored from real, citable sources — never generated.** Neutral topic.
3. **Subgoals labeled, shapes varied** — each claim/link states what it is *for*;
   include a support, a contradiction, and an open-question across the sources, not
   identical paper→claim pairs.
4. **~8 sources / ~15 claims** — the "semi-realistic" band: not toy (understates the
   real effort), not large (a steep curve that blocks the payoff). Paired with an honest
   in-line line: *"this sample is weeks of reading compressed; you finish a few reps to
   learn the moves."*
5. **One planted gap** — a known hole the map/draft will surface, to fuel `05`.

### The months-long rhythm is not a tutorial

The tutorials teach the **moves** (compressed, one sitting). The real-time loop —
capture as you read, distill once ~10 sources accumulate, map/draft/verify when a
deadline appears, let gaps pull the next reading — lives in a separate **"Your first
month" practice guide** (how-to/explanation genre). Cramming the real timeline into a
by-doing tutorial is a genre mismatch.

## Consequences

- A shipped seed corpus becomes a **maintained artifact**: it drifts as the note schema
  / frontmatter / space layout change, and must be kept valid. It pays for itself by
  doubling as an end-to-end **test fixture** and a **demo**.
- Authoring ~8 real-sourced sources + ~15 claims is real one-time work; the half-built
  rule trims ~3 sources to completion stubs.
- Structural shape changes: entry flips fleeting→source · "your first note" folds to an
  aside · "build a reading batch" folds into `02` as technique · `06`/`07` become the
  Produce-rigor + loop-close capstone · **7 → 6**.
- The **provenance risk is mitigated structurally** by rule 2: because novices imitate
  the surface form they are shown, a faked/LLM-generated seed would model the exact
  anti-pattern the product exists to prevent (claims that don't trace). Authoring from
  real sources is non-negotiable, not a quality nicety.
- The **sample → own-vault handoff stops being a cliff**: the learner builds part of the
  seed, so the "is this fake or mine?" boundary dissolves.
- The seed does **double duty** — density for Produce *and* the planted gap for the
  loop-close — so one artifact carries two pedagogical jobs.
- Bounded by the **expertise-reversal effect**: heavy guidance helps novices but harms
  experienced learners, so the sample must stay **optional and skippable**, and the
  fade-to-own-data step is load-bearing, not decorative.

## When this matters

*(Proposed.)* Finalize when the alpha10 docs pass reaches the tutorials. The spine rests
on the current note-type model and four-space navigation staying stable — a change to
either reshapes it, which is why this is `proposed` rather than silently implemented.
The one open lever is the **seed topic**: it must be broadly legible (no domain jargon),
built from real open sources, and mildly contested (so the contradiction and the planted
gap are natural, not forced). Picking the topic is the long pole, because seed authoring
gates the `02`/`03` rewrites.

## Alternatives considered

**Keep the pipeline spine.** Rejected: it is the ontology sequenced — it starts on the
wrong object and draws a loop as a line, so it reads as a tour of five note types rather
than one researcher's work.

**No seed, or a toy seed (2–3 claims).** Rejected: the Produce payoff and the
"feel the density" lesson cannot land at one-session scale without pre-existing state;
toy data both understates the real effort and exercises nothing — the same gap the
Sakila/Northwind/Chinook teaching corpora exist to close (Dyer & Rogers, JISE 2015).

**A generated / LLM-authored seed.** Rejected: provenance *is* the product; because
learners imitate the form they are shown (Catrambone 1994; Robertson 2000), a faked seed
teaches fabrication of the exact thing the system prevents.

**A finished showcase seed the learner synthesizes beside.** Rejected: passive finished
examples do not secure transfer (the strong "just show a complete worked example" claim
was refuted 0–3 in the research pass); fading a worked example into a **completion
problem finished on the learner's own data** is what bridges to their messy reality
(Renkl & Atkinson guidance-fading; Paas 1992 completion problems).

**Make the months-long loop a tutorial directly.** Rejected: a habit cannot be taught
by-doing in a sitting — genre mismatch. It belongs in a practice guide.

## Related

- **Builds on:** [What Memoria is](../explanation/overview/what-memoria-is.md) (the two
  failure modes), [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)
  (the loop, the six delegable tasks), and the current
  [Tutorials](../tutorials/README.md).
- **Implementation (follows acceptance + topic choice):** rewrite `docs/tutorials/`
  `00`–`05`, author the seed corpus, add the "Your first month" practice guide.
- **Research basis (deep-research pass, 2026-06-22):** worked-example & cognitive-load —
  [ACM ToCE 2025](https://dl.acm.org/doi/full/10.1145/3732791); subgoal/transfer-failure
  — [Catrambone 1994](https://link.springer.com/article/10.3758/BF03198399); fading &
  completion —
  [Renkl/Chen 2023](https://www.tandfonline.com/doi/full/10.1080/01443410.2023.2273762);
  expertise-reversal —
  [Kalyuga et al.](https://www.researchgate.net/publication/226748784_The_expertise_reversal_effect_and_worked_examples_in_tutored_problem_solving);
  sample-corpus pedagogy — [MySQL Sakila](https://dev.mysql.com/doc/sakila/en/),
  [Dyer & Rogers, JISE 2015](https://jise.org/Volume26/n2/JISEv26n2p85.pdf); empty-state
  vs sample-data UX —
  [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/).
- **Source discussion:** design session, 2026-06-22.


---

<!-- source: adr/112-tutorial-destination-first-arc.md -->

# ADR-112: Onboarding is one destination-first project arc

This ADR redesigns the onboarding tutorials from first principles — learner
requirements plus Diátaxis and the learning-science evidence [ADR-111](111-two-mode-tutorial-spine.md)
already cites — rather than from the shipped implementation. It **supersedes ADR-111's
tutorial spine** while **retaining ADR-111's seeded half-built sample vault**.

## Context

ADR-111 reorganized the tutorials around the two modes a researcher alternates between
(Accumulate / Produce) and solved the one-sitting-vs-months problem with a seeded
half-built corpus. That shipped: tutorials `00`–`05`, the `sample-vault` bundle, and the
`Memoria: load/remove sample vault` commands are live on `main`.

Re-derived from scratch, two parts of ADR-111 are **forced by real constraints and
kept**, and the rest is **challenged**:

- **Forced, kept:** the beat *order* capture → distill → draft → verify → loop is fixed
  by knowledge-cycle dependencies (no claim without a source, no draft without claims).
  The **seeded half-built corpus** is forced by the one-sitting-vs-months problem and the
  research pass — without pre-existing state the payoff (writing from a dense graph)
  cannot land in a sitting.
- **Challenged:**
  1. **Setup lives inside the tutorial.** Install / keys / Obsidian / git has one right
     way and teaches no Memoria *idea* by doing — it is how-to, and Diátaxis says keep it
     out. Embedding it also duplicated the [Quickstart](../how-to-guides/setup/quickstart.md),
     and the two copies drifted (e.g. restart-Obsidian and git-init present in one, absent
     in the other).
  2. **Feature-tour framing.** "Learn six moves" is weaker motivation than "produce one
     real thing you wanted."
  3. **The two-mode concept as the *spine*.** Diátaxis is explicit that tutorials should
     not be organized around concepts; the concept is the *why* (explanation), the *doing*
     is the structure.
  4. **Bottom-up entry.** Starting on capture buries the motivation until the payoff three
     beats later.
  5. **A vague "close the loop" ending** instead of a concrete graduation into real use.

## Decision

Onboarding is **one deliverable-driven, destination-first project arc**: *from a working
vault to a verified, cited paragraph you'd defend, in one sitting.* Every beat is a
sub-task of that single artifact.

- **Setup is excluded** — the tutorial assumes a working vault with the Co-PI answering
  and links to the [Quickstart](../how-to-guides/setup/quickstart.md). (This dissolves the
  Quickstart ↔ tutorial duplication and its drift.)
- **The two modes are narrative, not spine** — their canonical home stays
  [What Memoria is](../explanation/overview/what-memoria-is.md); the tutorial references
  the *why* but is structured by the *doing*.
- **ADR-111's seeded half-built sample vault is retained** — and now earns a third job:
  it **enables the destination-first opening** (you cannot map an empty vault).

### The arc

1. **Orient** — load the sample, open a project over it, and *read* the Co-PI's narrated
   coverage map: a dense corpus and its planted gap. Destination-first.
2. **Capture** — bring in one source of your own (provenance: catalog + source note in
   your words).
3. **Distill & connect** — the transfer-fragile move, faded: *study* a worked claim →
   *finish* the sample's half-built claim/link → *distill your own source, cold* (the link
   gate).
4. **Draft** — your paragraph from the now-denser corpus, citations bound. **The payoff
   lands here.**
5. **Verify** — trace it, read the argument (not a verdict), fix or trust.
6. **Close the loop** — the gap from beat 1 re-triggers discovery; it is a cycle, not a
   finish line. *(A tight beat — the *why* of graduation.)*
7. **Graduate** — `Memoria: remove sample vault`, import your own library, open your real
   project.

### Two design rules that make the arc work

- **Beat 1 is *read* the map, not *perform* mapping.** A novice cannot map concepts they
  have not met, but can be *shown* one — a narrated worked-example tour that introduces
  *claim / cluster / gap* in context at low load.
- **Beat 3 includes one rep of distilling the learner's *own* source.** Otherwise
  graduation (beat 7) is the first contact with their own material, and learning-science
  transfer requires the fade-to-own-data to happen *inside* the lesson. Graduation then
  *scales* (one source → a library), it does not introduce.

The months-long rhythm stays out of the tutorial (a "Your first month" practice guide),
per ADR-111.

## Consequences

- **The Quickstart/tutorial duplication disappears** — setup has a single home (how-to),
  and the drift it caused cannot recur.
- The arc is **shorter and deliverable-driven**: ~6–7 short beats (four *doing*, three
  *framing*) versus ADR-111's six feature-tutorials including setup.
- The seed now carries **three** jobs, not two: density for Produce, the planted gap for
  the loop, and the built corpus that makes destination-first possible on day one.
- The **graduation beat** gives `Memoria: remove sample vault` and the library import a
  natural home and ends the learner standing in their own project — the strongest point
  for activation and retention.
- This redesigns the **narrative arc and packaging only**: the sample vault, the
  load/remove commands, and the provenance discipline from ADR-111 are reused unchanged.
- **Implementation (pending):** rewrite `docs/tutorials/` to the arc — setup leaves,
  orient/map opens, graduation closes; the existing `00`–`05` collapse and reframe.

## Alternatives considered

**Bottom-up order (capture first) — ADR-111's spine and the first cut of this redesign.**
Rejected: it buries motivation until the payoff. Opening with the map sells Accumulate via
the *visible gap* — something a from-scratch vault cannot do but the seed can.

**Bundle map + draft as one "Produce" beat.** Rejected: *map* is a survey move that belongs
early (orient), *draft* is a synthesis move that belongs after the learner has contributed;
conflating them mis-sequences the arc.

**Keep setup inside the tutorial (ADR-111).** Rejected: setup is how-to; embedding it
duplicates the Quickstart, and the duplicates drift in practice.

**Co-PI-guided onboarding instead of doc pages.** Deferred, not rejected — see
[ADR-113](113-copi-guided-onboarding.md). The doc arc is the script the agent layer would
later dramatize, so it must exist and stabilize first.

## Related

- **Supersedes:** [ADR-111](111-two-mode-tutorial-spine.md) (replaces its tutorial spine;
  retains its seeded sample-vault decision and the load/remove commands).
- **Deferred alternative:** [ADR-113: Co-PI-guided onboarding](113-copi-guided-onboarding.md).
- **Builds on:** [What Memoria is](../explanation/overview/what-memoria-is.md),
  [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md), and the
  [Quickstart](../how-to-guides/setup/quickstart.md) (which now owns setup).
- **Research basis:** the deep-research pass recorded in ADR-111 (worked-example,
  guidance-fading, expertise-reversal, sample-corpus pedagogy).
- **Source discussion:** first-principles design session, 2026-06-22.


---

<!-- source: adr/113-copi-guided-onboarding.md -->

# ADR-113: Co-PI-guided onboarding (deferred)

This ADR records a deferred design: letting the **Co-PI run the first loop in
conversation** instead of (or alongside) the doc tutorial that [ADR-112](112-tutorial-destination-first-arc.md)
ships. It is kept `proposed` so the idea is on record with its preconditions, not built.

## Context

ADR-112 delivers onboarding as **doc pages the learner reads while doing**. But Memoria's
entire interface is the **Co-PI** — a conversational agent that already "questions your
thinking, explains the system, and delegates durable work." The AI-native form of
onboarding is therefore not a manual read beside the work; it is the Co-PI *walking the
learner through the first loop in conversation* — driving the palette through
orient → capture → distill → draft → verify → loop → graduate, with the docs as the
reference behind it.

## Decision

*(Proposed — deferred.)* When built, an onboarding skill lets the Co-PI dramatize the
ADR-112 arc conversationally. The **single-script** rule is the crux: the agent and the
docs read from **one** beat definition, so the two representations cannot drift. The
lazy-correct path is incremental — the doc arc (ADR-112) ships first, then the Co-PI
merely *offers* "want me to walk you through your first loop?" against that same script.

## Consequences

- **Pro:** native to the tool, adaptive to the learner, no read-while-do split, higher
  activation than prose.
- **Con:** a real build — an onboarding skill plus the Co-PI driving palette commands —
  and a *second representation of the same flow* that must be held in sync with the docs.
- **Why deferred:** the ADR-112 doc arc is the script the agent layer would dramatize, so
  it must exist and stabilize first; building the agent layer against a moving doc flow
  would mean syncing two moving targets.

## When this matters

Revisit when both hold: (a) the ADR-112 doc arc is implemented and stable, and (b) a
skill/onboarding mechanism exists for the Co-PI to drive palette commands. The
single-script design (docs and agent from one source) is the precondition that keeps the
two from drifting — which is why this `assumes: [112]`: if the doc arc's beats change, this
proposal's script changes with them.

## Alternatives considered

**Build the agent-guided flow now, instead of the doc arc.** Rejected: the doc arc is the
script; authoring the script first is cheaper and is the thing the agent would read.

**Drop agent-guided onboarding entirely.** Rejected: for an agent-centric tool it is the
best-practice end state; keeping it as a deferred ADR preserves the intent without paying
for it before its preconditions are met.

## Related

- **Assumes / dramatizes:** [ADR-112: Onboarding is one destination-first project arc](112-tutorial-destination-first-arc.md).
- **The agent it would drive:** [The Co-PI](../explanation/profiles/co-pi.md).
- **Source discussion:** first-principles design session, 2026-06-22.


---

<!-- source: adr/114-left-pane-navigator.md -->

# ADR-114: Left pane is a navigation rail — Now over Places

## Context

Space switching happens through dashboard notes under `spaces/` opened in the **main**
pane: each dashboard carries a nav row linking to the other three, and the Homepage
plugin opens `spaces/inbox` on startup ([ADR-81](81-persistent-gate-dashboards.md)). The
left pane held only the file explorer. This left two gaps:

- **No ambient awareness.** "Is anything waiting on me?" required switching to the Inbox
  space, even though [ADR-70](70-navigation-gates-dashboards.md) already establishes that
  system health should be *ambient*, not a destination you enter.
- **No persistent orientation.** The four spaces ([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md))
  were reachable only from inside whichever space note was open in the main pane; nothing
  stable showed where you could go.

A clean-slate review of the left pane (this decision's source discussion) settled on the
standard activity-bar + side-bar division the mature tools converge on (VS Code, Linear,
Notion email-style counts), constrained by Memoria's plain-note / single-source discipline
([Home explanation](../explanation/obsidian/home.md)).

## Decision

**The left pane is a thin navigation rail, never a second dashboard.** One rule governs it:
*the left pane navigates and alerts; analytics live in the main pane.* The moment the rail
renders a dashboard view it duplicates the main pane and drifts from it — the same
single-source hazard the Home note already names.

The rail is a single pinned plain note, `_nav.md`, at the vault root (a global
navigation surface, not a space — it carries no `type`, like `home.md`), in two zones:

1. **Now (awareness).** The Inbox action queue as a live count. Inbox is a *state* that
   converges to empty, not a *place* you dwell — so it surfaces here as a glanceable signal,
   not as a peer destination. Clicking opens the Inbox space in the main pane.
2. **Places (destinations).** The three durable rooms — **Library · Knowledge · Project** —
   each with one context badge (sources to read · open contradictions · active projects).
   Selecting opens that room's full dashboard in the main pane.

Counts are **Dataview inline-JS** expressions, not Bases formulas: a Bases formula computes
per row and cannot emit a standalone count into a note. The filters mirror the existing
`.base` view definitions (Inbox "Needs me", sources "Reading pipeline", claims
"Contradictions", projects "Active projects") so the badges and dashboards stay consistent.

The file explorer is retained as a collapsed second tab — the escape hatch to the raw vault,
never the primary path. The saved **Memoria** workspace pins the nav note as the first left
tab at width 280.

**Per-space object browsing in the rail is deferred.** A contextual panel that swaps its
contents when you select a Place (VS Code's side bar) is the one piece Obsidian cannot
express natively — a sidebar leaf does not re-point on a link click. Until a plugin
`ItemView` earns that cost, selecting a Place opens its dashboard in the main pane, which
already covers browsing.

## Consequences

- New surface `_nav.md` at the vault root (`cssclasses: memoria-nav`); a `memoria-nav.css`
  snippet tightens its spacing and pills the counts.
- `workspaces.json` left split gains the nav leaf ahead of the file explorer and narrows
  320 → 280; `appearance.json` enables the snippet.
- The badge queries depend on Dataview's inline-JS being enabled (it already is) and on the
  `notes/sources` / `notes/claims` / `projects` / `inbox` folder paths the `.base` files use.
- The in-note nav row on each space dashboard is now redundant with the rail but is left in
  place; it remains the fallback if the workspace layout is reset or the plugin is disabled,
  consistent with the degradation stance in [ADR-81](81-persistent-gate-dashboards.md).

## Alternatives considered

- **Four equal space tabs in the left pane.** Rejected: it gives a converges-to-empty queue
  (Inbox) the same permanent real estate as the durable rooms, and stacking full dashboards
  in a 280px pane forces a cramped second-class copy of each — the duplication the governing
  rule forbids.
- **Render every space's full content in the rail.** Rejected for the same drift reason: the
  rail would re-embed the main-pane analytics and inevitably diverge from them.
- **Bookmarks core plugin for the switcher.** Viable and lighter, but a bookmark list cannot
  carry live counts, so it delivers orientation without the ambient awareness that is the
  main gap this decision closes.

## Related

- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (ambient health, JTBD
  dashboards), [ADR-81](81-persistent-gate-dashboards.md) (dashboards as persistent notes,
  the saved workspace), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) (the
  four spaces).
- **Reference:** [Obsidian workspaces](../reference/obsidian-workspaces.md),
  [Home — the vault front door](../explanation/obsidian/home.md).
- **Source discussion:** the alpha.8 left-pane clean-slate review.


---

<!-- source: adr/115-inbox-queue-and-retired-homepage.md -->

# ADR-115: Inbox is the queue, not a space; retire the homepage front door

## Context

[ADR-114](114-left-pane-navigator.md) introduced the left-pane navigation rail and
committed to a principle the rest of the model had not caught up to: **the Inbox is a
*state*, not a *place*.** The rail surfaces the Inbox count as an ambient signal under
*Now* and owns space-switching. Three things still assumed the pre-rail world:

1. **Inbox was the fourth co-equal space** ([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) — `type: space`, `space: inbox`), despite being a triage queue that converges to empty rather than a room you dwell in.
2. **Every space note carried a nav row** — the switcher the rail replaced.
3. **The homepage plugin opened the Inbox on launch** ([ADR-13](13-homepage-front-door.md), [ADR-81](81-persistent-gate-dashboards.md)). With the rail now carrying the "what needs me?" signal, forcing the full queue as the launch workspace is redundant, casts a knowledge/writing tool as inbox-management, and — since empty is the goal — often lands the human on nothing.

## Decision

**Reclassify the Inbox as the queue, drop the nav rows, and retire the forced-landing homepage in favour of a startup restore of the saved Memoria shell.**

1. **Inbox is the queue (`type: queue`), not a space.** A new `queue` type (`schemas/types/queue.yaml`, category `spaces`, mapped `queue → spaces/`) is added; `spaces/inbox.md` becomes `type: queue` (still titled "Inbox"). The `space` type's enum drops `inbox` → `[library, knowledge, project]`. **The durable spaces are three** — Library, Knowledge, Project; the Inbox is the transient triage surface reached from the rail's *Now*.
2. **Space notes carry no nav row.** The rail owns switching ([ADR-114](114-left-pane-navigator.md)), so a space note is purely its JTBD dashboard — title, brief, embedded views, guides. The four notes' nav rows are removed.
3. **The homepage plugin is retired.** The old forced landing opened the Inbox queue and made Memoria feel like an inbox manager. The `homepage` community plugin, its vendored bundle, and its provenance-lock entry remain removed.
4. **Startup restores the saved Memoria shell.** QuickAdd's `Memoria: restore shell on startup` macro runs after Obsidian's first layout is ready and calls the core Workspaces plugin's `loadWorkspace("Memoria")`. That restores `home.md` in the main pane, the pinned `_nav.md` rail in the left pane, and the Co-PI pane on the right without reintroducing the old Inbox homepage.
5. **The launch/reset shell seeds `home.md`.** The saved **Memoria** workspace points its main pane at `home.md`, recast as a thin welcome note ("start here": capture your first source, the three places, ask the Co-PI). It is not a dashboard and not a daily front door; it owns no computation. Daily movement belongs to the pinned rail.

## Consequences

- Data model: new `queue` type; `space` enum loses `inbox`; `folders.yaml` and the Linter `detectors.py` folder map gain `queue → spaces/`. Type count 24 → 25; templates exclude `queue` (authored, not template-created), so the template count stays 20.
- App config: `community-plugins.json` drops `homepage`; `src/.obsidian/plugins/homepage/` is deleted and removed from `plugin-provenance-lock.json`; the **Memoria** workspace's main leaf points at `home.md` and pins `_nav.md`.
- `home.md` is rewritten from a homepage-fallback into the welcome note. The launch behaviour now depends on the already-bundled QuickAdd startup hook plus Obsidian's core Workspaces plugin — no new community plugin or provenance lock.
- Live docs are updated to current-state: the Inbox is "the queue" (not a space), the spaces are three, and the launch surface is the saved **Memoria** shell restored on startup. ADR and `releasing/` prose are left in their own vocabulary; only [ADR-13](13-homepage-front-door.md) is marked superseded.
- The "what needs me?" ambient signal is fully carried by the rail's *Now*; the daily glance still lives on the Inbox queue note.

## Alternatives considered

- **Keep Inbox nominally a "space" but stop launching into it (Phase 1 only).** Rejected: it fixes the launch redundancy but leaves the model saying a converges-to-empty queue is a durable room. Reclassifying is what makes the model say what it means.
- **Keep the homepage plugin to force a stable daily landing.** Rejected: the old plugin opened the Inbox queue and duplicated the rail's ambient signal. The saved-shell startup macro restores the rail without another vendored community plugin.
- **Rely on native last-session restore only.** Rejected after live Obsidian verification: a stale session can reopen without the rail or Co-PI pane, and then the normal shell fails before the user clicks anything. Loading the saved shell on startup is the boundary that makes the rail pattern durable.
- **Delete `home.md` entirely and seed startup into Library.** Rejected: a brand-new user benefits from a curated welcome over an empty dashboard, and onboarding ([ADR-113](113-copi-guided-onboarding.md)) needs a landing to attach to. `home.md` is kept as the startup/reset welcome seed.

## Related

- **Supersedes:** [ADR-13](13-homepage-front-door.md) (the homepage front-door note auto-opened by obsidian-homepage).
- **Refines:** [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) (the four spaces become three + the Inbox queue), [ADR-81](81-persistent-gate-dashboards.md) (dashboards stay persistent notes; only the launch target changes), [ADR-114](114-left-pane-navigator.md) (completes "Inbox is a state, not a place").
- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (system health is ambient).
- **Onboarding seed:** [ADR-113](113-copi-guided-onboarding.md).
- **Source discussion:** the alpha.8 spaces-and-homepage clean-slate review.


---

<!-- source: adr/115-profile-config-materialization.md -->

# ADR-115: Profile config capability blocks are materialized from the tool registry

## Context

ADR-48 made the old SOUL/profile compiler unnecessary: the five profile postures are
short and genuinely distinct. The drift that remains is narrower. ADR-27 makes
`src/.memoria/tool-registry.yaml` the source for each profile's positive
`platform_toolsets` and MCP tool filters, but the checked-in `config.yaml` files
still repeated those derived blocks by hand.

Hermes v0.17 reads plain per-profile `config.yaml`; the local docs and
`cli-config.yaml.example` do not provide profile-config includes or inheritance.

## Decision

Keep plain checked-in Hermes `config.yaml` files, but materialize their capability
blocks from `src/.memoria/tool-registry.yaml` with
`scripts/render_profile_configs.py`.

The render script owns only the mechanical parts:

- `platform_toolsets` for every Hermes runtime platform
- MCP `tools.include` filters for non-Obsidian MCP servers

Profile posture, MCP server endpoints/commands/timeouts, model placeholders, memory
settings, plugin enablement, and package metadata stay ordinary profile source.

## Consequences

- Capability edits happen in one file: `tool-registry.yaml`.
- CI can fail on stale generated profile configs instead of relying on humans to
  copy allowlist changes into five files.
- Runtime remains boring: Hermes receives normal `config.yaml` files; no install-time
  template language or runtime include mechanism is introduced.
- Comments inside generated profile configs are intentionally sparse. The rationale
  lives in ADRs and reference docs; the config is the deployable machine view.

## Alternatives considered

**Keep hand-authored configs.** Rejected: it preserves five-way copying for the
highest-risk profile capability surface.

**Full profile compiler.** Rejected: too broad for the actual duplication. The SOUL files
and package manifests remain small and profile-specific.

**Hermes-native inheritance.** Not available on the installed v0.17 configuration model.

## Related

- **Assumes:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-48](48-copi-and-agent-consolidation.md)
- **Implementation:** `scripts/render_profile_configs.py`


---

<!-- source: adr/116-obsidian-surface-architecture.md -->

# ADR-116: Obsidian surface architecture — View, Collection, Rail

## Context

The Obsidian surface grew one decision at a time — the navigation rail
([ADR-114](114-left-pane-navigator.md)), the Inbox→queue reclassification
([ADR-115](115-inbox-queue-and-retired-homepage.md)), the JTBD dashboards
([ADR-70](70-navigation-gates-dashboards.md)), the spaces vocabulary
([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)), and the Bases view
layer ([ADR-49](49-catalog-in-bases-linter-monitor.md)). Each was locally sound, but
the accreted whole carries three overlaps a clean-slate review surfaced:

1. **Two navigation taxonomies.** The rail navigates by *intent* (Library · Knowledge ·
   Project); Portals navigates by *storage folder* (sources, claims, hubs, projects) —
   the same destinations named twice, as two competing left-pane models.
2. **Two dashboard engines defining the same view twice.** Five `system/dashboards/`
   pages re-query in Dataview what a `.base` view already defines and a space already
   embeds (contradictions, open-questions, discuss-queue, drift-watch, loose-ends). The
   twins have already drifted — different columns, and a string-sorted `drift-watch`
   that orders loudness alphabetically instead of by severity.
3. **One queue mixing two cadences.** The Inbox embeds *needs-me* (decide now) beside
   *drift-watch* / *loose-ends* (review Friday), violating the system's own
   "one decision per dashboard" rule.

This ADR rethinks the surface from the jobs the human actually does, not from the
current pieces.

## Decision

The human asks seven questions in the vault — *what needs me · is anything wrong · where
do I go · open a note · do the work · help me think · where do I start*. They reduce to
**three primitives and two edges**, and the six surfaces (left pane, Portals, Inbox,
spaces, home, dashboards) collapse onto them.

### Primitive 1 — View (one definition, ever)

A dashboard is not a page; it is a **view** — one Bases query over notes, defined once in
a `.base` file and surfaced by embedding (`![[x.base#view]]`), never re-queried.

- **Bases for anything over note frontmatter** — one definition, many embeds.
- **Dataview only where the source is not notes** — JSONL metrics/logs (audit, eval,
  fleet, skill) and inline scalar counts Bases cannot emit (the rail badges).
- Re-querying a note-frontmatter view in Dataview is prohibited; the five duplicate
  pages become single-definition embeds.

### Primitive 2 — Collection (a space is a set of views)

A **space is a named collection of views for one work-context** — that definition
dissolves the "is it a space or a dashboard?" ambiguity. The durable spaces are three:

- **Library** = {reading pipeline, discuss queue, catalog}
- **Knowledge** = {claims by maturity, open questions, contradictions, hubs, patterns}
- **Project** = {active, saturation, gaps}

Two non-durable collections sit beside them, **split by cadence**:

- **Queue** (daily, converges to empty) = {needs me, fleeting to process} — pure action.
- **Maintenance** (weekly) = {drift watch, loose ends, board state} — the Linter's
  structural debt, on its own rhythm.

Operational-health (fleet, audit, eval, skill) stays a separate **pull-only** collection
— Dataview over JSONL, deliberately outside the daily loop.

### Primitive 3 — Rail (the left-pane navigation)

The left pane has two tabs — the **rail** (`_nav.md`) and **Portals** (the file browser):

- The **rail** carries **Now** — the two ambient signals: the action count (→ Queue) and a
  health band (drift + fleet → Maintenance / ops), answering *what needs me* and *is
  anything wrong* without a click — over **Go**, the three durable spaces by **intent**
  (selecting opens that space).
- **Portals** is the **object browser** — the curated file-explorer replacement that hides
  `system/`/`.memoria/`. It answers *open a note*, navigating by folder.

Intent navigation (the rail's Go) and object browsing (Portals) are **complementary axes**,
not competitors — kept as sibling tabs.

> **Amendment (2026-06-23):** the original decision folded Portals into the rail as a single
> stacked *Now / Go / Find* spine. That is **retired** — see Alternatives. The rail is Now +
> Go; Portals stays its own tab, the arrangement
> [#908](https://github.com/eranroseman/memoria-vault/pull/908) settled.

### Edges

- **Home** — the startup/reset welcome seed only ([ADR-115](115-inbox-queue-and-retired-homepage.md));
  the rail owns the daily loop, so home is never the navigation hub.
- **Co-PI** — the right pane, unchanged.

## Consequences

This is a **consolidation** — the net is fewer surfaces, mostly deletion and reframing,
no new machinery.

- **Delete:** the five Pattern-C duplicate dashboard pages collapse to single-definition
  embeds; the conceptual "dashboard ≠ space" split goes away.
- **Move:** drift-watch + loose-ends + board-state leave the Queue note for a new
  **Maintenance** collection; the rail's **Now** grows a health band to carry the
  "is anything wrong?" signal those views used to answer in the queue.
- **Reframe:** spaces are documented as view collections; the Bases-over-notes /
  Dataview-over-JSONL engine split becomes an enforced rule, not a convention. (Portals
  keeps its file-browser identity — the spine fold is retired; see Alternatives.)
- **Keep:** the three spaces, the Co-PI pane, home-as-seed, the operational-health pull
  pages, and the queue-is-a-state principle ([ADR-115](115-inbox-queue-and-retired-homepage.md)).

**Phasing** (sequencing lives in the milestone/issues, not here):

1. **Views** — collapse the five Pattern-C pages to single-definition embeds. *Shipped
   ([#911](https://github.com/eranroseman/memoria-vault/pull/911)); fixed the drift-watch
   ordering defect for free.*
2. **Cadence split** — Queue = action only; new Maintenance collection for Linter debt;
   add the health band to the rail's Now. *The remaining design change.*
3. ~~**Spine** — fold Portals into the rail as the Find zone.~~ **Retired** — the two-tab
   rail + Portals arrangement stands (see Alternatives).

## Alternatives considered

- **Fold Portals into the rail as a stacked *Now / Go / Find* spine (the original Phase 3).**
  Retired after review: stacking the file tree *under* the rail regresses its height (a
  sibling tab gives it the full pane), and — decisively — stacking is only *visual*. The
  intent-vs-storage overlap (Context #1) survives whether the two are tabs or stacked, so the
  spine pays an ergonomic cost without delivering the consolidation that motivated it. The
  two-tab arrangement settled in [#908](https://github.com/eranroseman/memoria-vault/pull/908)
  stands; the two axes — intent navigation (the rail) and object browsing (Portals) — are
  accepted as complementary, not collapsed.
- **Keep the daily queue and maintenance views together (no cadence split).** Rejected:
  it keeps "decide now" and "review Friday" in one surface, which is the
  one-decision-per-dashboard violation, and leaves the queue unable to converge to empty.
- **Let standalone dashboard pages keep their own Dataview queries (two engines by
  choice).** Rejected: the twins have already drifted in columns and sort order — proof
  that two definitions of one view is a defect surface, not a feature.
- **Drop Portals for the core file explorer.** Rejected: it loses `system/` hiding. Portals
  stays as the object-browser tab.

## Related

- **Refines:** [ADR-114](114-left-pane-navigator.md) (the rail gains a Now health band; the
  left pane keeps the rail + Portals two-tab layout), [ADR-115](115-inbox-queue-and-retired-homepage.md) (the queue splits
  off Maintenance by cadence), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)
  (a space is defined as a collection of views), [ADR-70](70-navigation-gates-dashboards.md)
  (ambient health becomes the rail's Now band).
- **Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md) (Bases are the view
  layer; notes are the source of truth).
- **Source discussion:** the alpha.8 left-pane / Portals / Inbox / spaces / home /
  dashboards clean-slate review.


---

<!-- source: adr/117-type-naming-scheme.md -->

# ADR-117: Document types — kind-scoped names with a fleeting exception; no folder/space collision

## Context

A clean-slate review walked all 26 typed-document types. Most are well-chosen field terms —
`paper`, `venue`, `claim`, `source`, `hub`, the kanban `card` — but there is **no stated
naming rule**, and that absence costs twice:

- **Apparent overloads read as bugs.** A reviewer "fixes" `worker-card` → `worker-row`, not
  knowing the board is a *kanban* board where `card` is the correct, Hermes-native term; or
  flags `card` as colliding with the Inbox's ADR-51 honesty card. Neither is a defect.
- **New types can drift in form** with nothing to check them against.

Three concrete issues surfaced: **`fleeting`** is the lone adjective among nouns, but it is also
the entrenched capture term; the **`notes/` category doubles the medium word** — every typed
object is a note, yet one category is named "notes"; and a tempting fix for that doubling
(`notes/ → knowledge/`) would have created a *worse* problem — a `knowledge/` folder and the
**Knowledge space** sharing a name with **different meanings** (the folder holds `source`
documents shown in the *Library* space, not just claims). The resolution turns out to be cheaper
than any folder rename: change the **umbrella term**, not the folder, and make `fleeting` the
explicit naming exception.

## Decision

Adopt an explicit naming rule, apply the umbrella rename, and record what the rule deliberately
leaves alone.

### The rule

**The umbrella term for a typed object is "document," not "note."** Every typed object is a
*document*; a *note* is then **one kind** of document (the `notes/` documents — `source`,
`claim`, `hub`, `fleeting`; ADR-119 later retired `index`). This single move dissolves the `notes/` doubling:
once the umbrella is "document," a `notes/` folder is a legitimate subset, not a circular
"notes are notes." Type schemas, the page that lists them, and prose say **document type**.

A type name is normally a **singular common noun for what the object is**, drawn from
**ubiquitous language** (the field's own term), scoped to its **kind**. The vault has four kinds;
the kind is a bounded context carried by the **category folder**:

| Kind | Role | Folder(s) |
| --- | --- | --- |
| **Record** | the content — entities, knowledge, project work | `catalog/` `notes/` `projects/` |
| **Signal** | a prompt awaiting a human decision | `inbox/` |
| **Surface** | a navigation view | `spaces/` |
| **Control** | agent-execution machinery | `system/` |

What the rule entails:

- **Singular noun by default; no adjectives or verbs.** `fleeting` is the one accepted
  exception because it names the established capture workflow and preserving it avoids runtime
  migration without creating ambiguity.
- **Use the established term** — `paper`/`venue` (bibliographic), `source`/`claim`/`hub`
  (Zettelkasten lineage), `card`/`lane` (kanban), `thesis`/`project` — never invent where a
  field word exists.
- **One word, one concept _within_ a kind.** A word may recur _across_ kinds only because the
  folder disambiguates: **`card`** is legitimately both the kanban execution unit
  (`worker-card`, Control) and the [ADR-51](51-inbox-category-and-honesty-card.md) inbox
  honesty card (Signal). Prose must always qualify it ("board card" / "inbox card"), never bare.
- **Suffixes are kind-local and meaningful**, not a global registry: in Control, `-card` = a
  kanban unit, `-task` = a gold-eval entry, `-item` = a list row — each correct on its own.
- **No folder name may also name a navigation surface with a *different* meaning.** A shared
  name is fine when the folder and the space are the *same* concept (1:1) — `projects/` ≈ the
  Project space, `inbox/` ≈ the Inbox queue. It is forbidden when the meanings differ — which
  is exactly why `notes/` is **not** renamed to `knowledge/`: that folder feeds *both* the
  Library space (its `source` documents) and the Knowledge space (its `claim` documents), so
  "knowledge" the folder ≠ "Knowledge" the space.

### The changes

1. **Umbrella: "note types" → "document types."** The collection of types, the page that lists
   them (`document-types.md`), and generic prose call a typed object a **document**. This
   dissolves the `notes/` doubling at the root — and because it keeps `notes/`, it also avoids
   the `knowledge/` ↔ Knowledge-space collision entirely. No folder moves; no `type:` value
   changes.
2. **`fleeting` stays `fleeting`.** It is the named exception to the singular-noun default,
   kept because it is already the product term for raw capture and does not collide with another
   type or surface.

### What the rule validates — do NOT change

- **`notes/` stays.** Under the document umbrella it is a legitimate content-kind folder (the
  note documents), not a circular name — and renaming it would only create a space collision.
- **The spaces stay**, and the 1:1 folder overlaps `projects/` ≈ Project and `inbox/` ≈ Inbox
  are fine (same concept, not a clash).
- `fleeting` — accepted exception to the singular-noun default; do not rename it only to satisfy
  the naming rule.
- `worker-card` — a Hermes/kanban card; correctly named (`worker-row` would be wrong).
- `worklist-item`, `eval-task`, `work-prompt`, `code-note` — each the correct term in its kind.
- the catalog six, `claim`, `source`, `hub`, `project`, `thesis`, `pattern`, `space`,
  `queue`, `maintenance` — already conform.

### Documentation (not renames)

- Document the `flag` vs `alert` distinction — the names are fine; only the *difference* is
  currently undocumented.

## Consequences

- The rule is enforceable going forward and ends the recurring "card"/"note" debate by naming
  the bounded-context and no-collision principles.
- **The umbrella rename is cheap** — terminology and docs route only: the `document-types.md`
  reference page (filename, title, and prose), schema/code comments that say "note type," and
  generic docs. **No folder moves, no `type:` values change, no paths change** — so none of
  `folders.yaml`, the `gated_prefixes`, the detectors, the producers, or existing documents are
  touched by it.
- `fleeting` remains the live type, template, QuickAdd setting, and dashboard filter. Existing
  fleeting notes need no migration.
- One internal note: the four *kinds* include "Record"; "document" as the umbrella pairs cleanly
  with Record/Signal/Surface/Control, though "Record document" is faintly redundant — the kind
  could be renamed **Content** if that ever grates. Not load-bearing.

## Alternatives considered

- **Rename the `notes/` folder** (to `knowledge/`, or a Zettelkasten *slip-box* name).
  Rejected: `knowledge/` collides with the Knowledge space *with a different meaning* (the folder
  feeds Library too) — the no-collision rule forbids it; a slip-box name avoids the collision but
  is jargon and inconsistent with the non-Zettelkasten type names (`claim`, not "permanent note").
  Either way it is a heavy path migration. The document-umbrella rename fixes the same doubling
  more cheaply and keeps `notes/`.
- **`file types` as the umbrella.** Rejected: "file type" conventionally means the *extension*
  (`.md`), so it clashes with the OS sense ("the file type is Markdown"). "Document" is clean,
  collision-free, and more precise for schema-validated structured documents.
- **Kind-prefixed type names** (`entity:paper`, `signal:flag`, `board:card`). Maximally
  collision-proof, but over-engineered: the folder already encodes the kind, real collisions are
  rare and already managed, and it would churn every `type:` value and every query. Rejected on cost.
- **`worker-card` → `worker-row`, `worklist-item` → `worklist-row`.** Rejected: the board is a
  kanban board and `card` is its correct, Hermes-native term — there is no collision to fix.

## Related

- **Refines:** [ADR-47](47-type-first-category-folders.md) (type-first category folders — the
  category folders and type homes are **kept**), [ADR-51](51-inbox-category-and-honesty-card.md) (inbox honesty cards — formalizes `card`
  as a Signal/Control dual-use), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)
  (the overloaded-term principle — applied to types, plus the folder/space no-collision corollary),
  [ADR-116](116-obsidian-surface-architecture.md) (the storage-vs-intent two-axis model the
  no-collision rule builds on).
- **Source discussion:** the alpha.8 type-naming clean-slate review.


---

<!-- source: adr/118-dashboard-consolidation.md -->

# ADR-118: Dashboard consolidation and the read-only system window

## Context

After [ADR-116](116-obsidian-surface-architecture.md) Phase 1 (collapse duplicate Dataview
pages to single-definition embeds) and Phase 2 (the Queue/Maintenance cadence split), a
walk of `system/dashboards/` found the 13 standalone `.md` pages split cleanly into four
groups: thin aliases of views the spaces already embed; one duplicate base; a pre-Queue
leftover; and the read-only operational dashboards.

ADR-116's **View** primitive says a view has *one definition, surfaced by embedding* — so a
standalone page whose view already lives in a space is redundant. And [ADR-84](84-read-only-obsidian-inspector.md)'s
read-only **Inspector** is the natural always-on system window, but it predates the
operational dashboards it should summarize and the rail health-band ([ADR-116](116-obsidian-surface-architecture.md)
Phase 2) it now overlaps.

## Decision

Apply ADR-116's "one view, in its space" rule to `system/dashboards/`, and align the
Inspector with it.

### 1. Delete six redundant pages — their view already lives in a space

| Page | View already in |
| --- | --- |
| `contradictions.md`, `open-questions.md` | Knowledge |
| `discuss-queue.md` | Library |
| `drift-watch.md`, `loose-ends.md` | Maintenance |
| `reading-pipeline.md` | Library + Knowledge |

`reading-pipeline.md` also carries a **broken embed** — `![[sources.base#To read & distill]]`
references a view that does not exist (the real view is `Reading pipeline`), so it renders
empty; deleting the page removes the bug. Point each page's deep-links at the space-section
anchor (`spaces/<space>#<heading>`).

### 2. Merge `project-gate` into the Project space

`project-gate.base` and `projects.base` both define an **"Active projects"** view — two
definitions of one view. Merge `project-gate.base`'s views into `projects.base`, fold the
readiness-gate views into the **Project** space (the gate *is* the project steering surface),
and delete `project-gate.md`.

### 3. Fold `weekly-review`'s unique part into Maintenance, retire the page

`weekly-review.md` is a pre-Queue leftover (created in v0.1.1, before the Queue/Maintenance
split): its notice-findings ≈ Maintenance's **Loose ends**, and its fleeting backlog is the
Queue's (the note self-admits the duplication). Its only unique content — the 7-day
**"New this week"** catalog/notes digest — moves into the **Maintenance** space (the weekly
surface). Delete `weekly-review.md`.

### 4. Keep five read-only system dashboards in `system/` — never a space

`board-state`, `audit-log`, `eval-trend`, `fleet-health`, `skill-state` stay where they are.
`system/` is **read-only, system-owned internals** (hidden by Portals); the user *views* these
on a trigger but never authors them. A **space is a user work-context**, so these are
categorically not space material — the same error that made Inbox-as-a-space wrong
([ADR-115](115-inbox-queue-and-retired-homepage.md)). They remain single-decision,
pull-on-trigger dashboards, reached by deep-link and the Inspector.

### 5. Make the Inspector the read-only system index — and update it

The [ADR-84](84-read-only-obsidian-inspector.md) Inspector pane (verdict band · board counts ·
recent audit) is the always-available read-only window behind the pull dashboards. Update it:

- **Add a fleet/trust band** — per-lane trust from the `system/metrics/` lane-metric notes. It
  is the one *continuous* system-health signal the Inspector currently lacks (it already reads
  `system/metrics/` for the verdict).
- **Deep-link each panel to its full dashboard** — board → `board-state`, audit → `audit-log`,
  verdict → the Linter/drift surface, fleet → `fleet-health` — turning the Inspector into the
  read-only index for the system dashboards.
- **Carry only the *continuous* signals** (verdict/drift, board, audit, fleet). The *episodic*
  dashboards — `eval-trend` (quarterly) and `skill-state` (on config change) — stay pure
  pull dashboards reached on their own triggers, not in the Inspector.
- **Reconcile with the rail health-band** ([ADR-116](116-obsidian-surface-architecture.md)
  Phase 2): the rail's Now band is the one-glance ambient *signal*; the Inspector is the
  read-only *detail panel* it points to. Ship one signal + one panel — not two competing health
  surfaces, and not a third status-bar indicator.

### 6. Harden the base-embed tests

`tests/test_bases.py` asserts an embed's *text* without checking the view exists — which is why
`reading-pipeline.md`'s broken embed stayed green. Embed tests must assert the `#View` name
exists in the target `.base`.

## Consequences

- `system/dashboards/` drops from 13 `.md` to **5** (the read-only system dashboards) plus the
  `.base` view definitions. The spaces (Knowledge / Library / Maintenance / Project) gain the
  folded views; the Inspector gains the fleet band and deep-links.
- One definition per view, no standalone aliases: the user reaches **content** views in spaces
  and **system** views via the Inspector and on-trigger deep-links.
- The Inspector update is **coupled to the rail health-band** ([ADR-116](116-obsidian-surface-architecture.md)
  Phase 2) — sequence them together so the ambient signal and the read-only panel are designed
  as one.
- Migration touches: updating the deep-links for the six deleted pages (~30 links), the
  `project-gate.base` → `projects.base` merge (tests + docs), the Maintenance space note (the
  "New this week" view), the Inspector plugin (`main.js`), and `tests/test_bases.py`.

## Alternatives considered

- **Merge the five system dashboards into a "System space."** Rejected: `system/` is read-only
  internals, not a user work-context; the five have different triggers and are never used
  together; and a "space" implies a place you *work*, so treating pull-on-trigger diagnostics as
  one repeats the Inbox-as-a-space error. A read-only **index** — the Inspector — is the right
  home.
- **Keep the alias pages as thin embeds.** Allowed by ADR-116, but they add nothing the space
  section does not; deleting them and deep-linking to the space heading is cleaner and removes a
  surface to maintain.
- **Merge `weekly-review` into Maintenance wholesale.** Rejected: most of it is redundant with
  Maintenance and the Queue; only the "New this week" digest is unique.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (the View primitive; spaces are
  view collections; operational dashboards are pull-only), [ADR-84](84-read-only-obsidian-inspector.md)
  (the read-only Inspector — extended into the system index), [ADR-70](70-navigation-gates-dashboards.md)
  (ambient health; one decision per dashboard).
- **Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md) (Bases are the view layer;
  notes are the source of truth).
- **Source discussion:** the alpha.8 dashboards clean-slate review.


---

<!-- source: adr/119-schema-driven-document-creation.md -->

# ADR-119: The type schema is the complete declarative contract

## Context

Validating *and* creating a typed document touches **eight** concerns: identity & placement,
fields, controlled vocabulary, the state model, the typed-edge graph, cross-field/referential
invariants, generation metadata (labels, defaults, which fields a creation form asks for), and
evolution.

Today the type schema (`types/<t>.yaml`) carries only **fields + enums**. Everything else is
scattered and hand-synced:

| Concern | Where it lives today |
| --- | --- |
| placement / gating | split between `folders.yaml` and the schema's `category`/`gated` |
| state transitions | ADR prose + detector code — *not declared anywhere* |
| graph / edges | `links: map` (untyped); the edge vocabulary ([ADR-52](52-links-vs-relationships.md)) is convention |
| invariants | **hand-coded in the Linter detectors** (`thesis`→`promoted_at`, `claim`→`sources`, …) |
| defaults | in the **templates**, not the schema |
| labels / creation-required | **nowhere** |

So the "schema" is a *fragment* of the contract. The consequences compound: the Linter
hard-codes per-type knowledge it shouldn't have to; the template frontmatter and the Modal Form
**re-encode the field list** (three hand-synced copies — the source form already drifted, adding
`summary` and dropping `links`); and adding a type or a rule means editing **four** places
(the YAML, a detector in code, a template, and `folders.yaml`).

Best practice and Memoria's own single-source-of-truth philosophy converge on the same fix:
stop scattering and duplicating the contract — make the schema **complete and declarative**, and
derive everything else from it.

A per-type audit of all 26 schemas confirms the diagnosis. Alignment is mostly strong — the inbox
honesty-card set (`candidate`/`gap`/`flag`/`alert`/`work-prompt`) and `claim`/`source`/`thesis` are
exemplary — and the *systematic* gaps are exactly this fragment problem: only `project`, `thesis`,
and `code-note` declare their `initial_lifecycle`/promotion gate (the other 23 leave the state
machine implicit); `required_any` is declared in-schema while the conditional and referential rules
(`thesis` `current` → `promoted_at`, `claim.sources` → citekeys, `source.entity` → a Catalog
wikilink) live in the detectors; and `project` is over-required at creation. The audit also surfaced
a handful of concrete per-type fixes, folded into the decision below.

A parallel audit of the four human forms points the same way. They are already ahead of the schema
on validation — every enum is a select, lists are multi-select fields, and `entity`/`sources` use
note-pickers that validate references against real Catalog notes (`fleeting` and `claim` are
exemplary). The telling case is `source_type`: the form renders it as a **required five-value
select** (`paper · dataset · repository · web-page · report`) while the schema declares it an
**optional free `str`** — the controlled vocabulary lives in the *form*, not the *schema*, which is
exactly the inversion this decision removes (once the form is generated, a `str` field loses the
select). The form audit's remaining fixes are folded in below.

## Decision

Promote the type schema from a partial field-list-plus-validator to the **complete declarative
contract** that everything executes or generates from.

### 1. The schema declares the whole contract

One type definition holds all eight concerns:

- **Fields as first-class specs** — `{type, required, default, label, description,
  creation: required|optional, constraints}` — where `creation` may be **conditional on another
  field** (e.g. ask for the provisional thesis only when `output_mode == thesis`), with value
  types richer than `str/list/map`:
  `link(endpoint-type)`, `citekey`, `date`, `enum(ref)`, `list<T>`, and `edges(edge-vocab)` for
  the graph.
- **Placement & gating** — `folder`, `gated` (folding `folders.yaml`'s per-type map in).
- **State machine** — `lifecycle: {states, transitions, gated-transitions}`: the universal chain
  projected to this type's subset, with the review-gated transitions declared (not inferred in
  detectors).
- **Typed edges** — reference the shared edge vocabulary ([ADR-52](52-links-vs-relationships.md)) with
  declared endpoint types, so the graph is typed *in the schema*.
- **Invariants as declarative rules** — conditional requirements
  (`when lifecycle == current, require promoted_at`) and referential rules
  (`sources: each is a citekey resolving to a paper`), replacing the hand-coded detector rules.

### 2. The Linter becomes a generic engine

It **executes the declared** field/enum/invariant/transition/placement rules — no per-type code.
Adding a type or a rule is a *schema edit*, not a detector edit. Declarative beats imperative:
the detector engine runs the contract; it doesn't *contain* it.

### 3. Forms, templates, the folder map, and the reference docs are generated from the schema

- **The Modal Form is generated** — creation-required fields → inputs, enums → selects, defaults
  prefilled, labels/descriptions attached. Validation happens **at submit**; the Linter is the
  backstop, not the primary gate.
- **The template splits** — frontmatter generated from the schema's defaults; the **only
  hand-authored per-type artifact is the body scaffold** (the thinking-shape sections, with
  fading prompts that are easy to delete — hints in comments or `[!hint]` callouts).
- **`folders.yaml` and the reference docs** (`note-types.md`, `frontmatter.md`) are generated,
  not hand-mirrored.

### 4. One creation engine, two input adapters

A single `create(type, inputs)` loads the schema spec, applies defaults, merges inputs, validates
at creation, prepends the generated frontmatter to the body scaffold, and writes to the schema's
folder. **Both the human form and the agent writers (`inbox.py`, ingest) call it** — unifying the
two creation tracks. This also explains why 16 types have a template but no form: they are
agent-created through the *same* engine with a different input adapter.

### 5. Format

Use an **enriched native DSL** — extend the current YAML with field-objects plus
`transitions`/`edges`/`constraints` blocks — structured so the field layer can be **projected to
JSON Schema later** if external tooling (IDE autocomplete, form-generation libraries) ever
justifies it. The decisive wins — completeness and the generic engine — are *format-independent*;
JSON Schema models a document's internal shape, not the vault's placement/graph/referential layer,
so a full migration would buy standard tooling for the easy half while the hard half stayed custom.

### 6. Per-type and per-form cleanups (from the audit)

Concrete fixes the schema and form audits surfaced, folded into the phases below:

- **Drop `index`.** Its schema is title-only — it expresses none of its register purpose — it has
  no creation path, and the register function (a list of hubs) is already the `hubs.base#Hubs index`
  view. It is the one type whose schema simply does not match its purpose; remove the type, the
  template, the schema, and the `notes/indexes/` folder. (This is the only fix *outside* the
  schema-as-contract work — a type-roster decision, recorded here.)
- **Make `source_type` an enum.** A free `str` today but controlled vocabulary in practice
  (paper · dataset · repository · web-page · report); the form *already* renders it as a five-value
  select, so generating the form from a `str` schema would **lose** the constraint — the enum must
  move into the schema. *(Phase 2.)*
- **Carry field `description` in the schema, not just `label`.** The `creation` block should hold a
  per-field description alongside the label, generated into the form as inline help. The `source`
  and `project` forms have none today — and they carry the most jargon (CEBM grades, PICO, FINER),
  where help text matters most. *(Phase 2.)*
- **Declare `initial_lifecycle` and gated transitions uniformly** — three types declare them, 23 do
  not; close the inconsistency as part of the state-machine work. *(Phase 3.)*
- **Document the fine distinctions the schemas already encode** — `flag` vs `alert` (a pointed
  finding with a verdict + target, vs a looser standing warning) and `candidate` vs `gap`
  (accept-this vs fill-this). They are correct in the schemas but undocumented; add the prose (and,
  for `candidate`/`gap`, consider one `proposal` type with a subtype — an ADR-51 question, not a
  schema fault).
- **`project` form fixes.** Derive `slug`, default `question_version`, and defer PICO/FINER to
  shaping. Make **`scope_topics` `creation: optional`** — required before the *project gate* runs,
  not at the first form: a project's scope sharpens while reading, so blocking on it fights
  start-then-shape (keep it mandatory only under a strict "no unbounded projects" rule). **Restore
  the full five-criterion FINER** — the form drops Interesting and Ethical, so projects never
  capture the full answerability lens. And add a **conditional creation field**: in **thesis** mode
  the form asks for the one-sentence **provisional thesis**; in **survey** mode it does not — keyed
  on `output_mode`, which *is* the thesis/survey distinction (thesis starts with a provisional
  answer, survey starts open). This also **matches the tutorial** (`tutorials/01-orient.md`), which
  already describes the thesis prompt the form currently omits — so it is the *form* that catches up,
  not the tutorial that changes. *(Phase 5.)*

## Consequences

- **Single source, no drift** — the contract is declared once; the Linter executes it, and the
  forms, templates, folder map, and docs are generated from it.
- **Declarative validation** — adding a type or invariant is a schema edit; the detector engine is
  generic.
- **Field minimization + progressive enrichment** (`creation`), **validate-at-input** (enum
  selects, required checks), **fading scaffolding**, and **labels/descriptions** all fall out for
  free.
- **Phasing** (sequencing lives in the milestone/issues):
  1. **Move invariants into the schema; make the detector engine generic** — replace hand-coded
     per-type rules with declared `constraints` the engine runs. *(Biggest correctness win.)*
  2. **Fold defaults + labels + `creation` in** — removes the template-frontmatter duplication.
  3. **Declare the state machine + typed edges** — remove implicit lifecycle/graph knowledge from
     detectors.
  4. **Fold `folders.yaml`'s per-type map into the type definitions.**
  5. **Generate the forms and template frontmatter; reduce templates to body scaffolds; route the
     human form and agent writers through one `create()`** — the creation pipeline. Trim the
     project form (derive `slug`, default `question_version`, defer non-essential PICO/FINER).
  6. **(Optional) project the field layer to JSON Schema** — only if external tooling pays.
  - A cheap floor for Phase 5: a **drift test** asserting each form's creation-required fields and
    enums equal the schema's — catches divergence immediately, no architecture change.
- Migration touches: the schema files (enriched), the Linter (generic engine), `folders.yaml`
  (folded/generated), the Modal Forms config (generated), the templates (split to body scaffolds),
  the agent writers (routed through the engine), `note-types.md`/`frontmatter.md` (generated), and
  the test suite.

## Alternatives considered

- **Keep fields-only schemas + per-type detector code + hand-synced templates/forms (status quo).**
  Rejected: the contract stays scattered across four places and the creation layer keeps drifting.
- **Adopt full JSON Schema as the format.** Standard and well-tooled, but it models a document's
  internal shape, not the vault's placement/graph/referential layer — so a custom layer survives
  regardless — and it is verbose. Better deferred to a *projection* of the field slice (Phase 6).
- **Model + projections** (author types in a rich internal model, emit JSON Schema / forms / docs).
  The strongest single-source, but the most upfront engineering; the enriched DSL reaches most of
  the benefit at lower cost, and can grow into this.
- **Put the body scaffold in the YAML schema.** Rejected: a markdown body shape is best authored
  as markdown — keep it a separate body-scaffold file the engine combines with generated
  frontmatter.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (the single-definition principle —
  applied here to document validation *and* creation), [ADR-117](117-type-naming-scheme.md) (the
  document-type vocabulary).
- **Depends on:** [ADR-47](47-type-first-category-folders.md) (the type→folder map),
  [ADR-49](49-catalog-in-bases-linter-monitor.md) (the schema as the authoritative contract the
  Linter and Bases read), [ADR-52](52-links-vs-relationships.md) (the typed-edge vocabulary the graph
  declares against).
- **Source discussion:** the alpha.8 schemas, templates, and form-creation clean-slate review.

