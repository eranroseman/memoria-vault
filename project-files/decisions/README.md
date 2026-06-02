---
topic: decisions
---

# Decisions

Accepted architectural decisions for Memoria. Each records one choice: what was decided, why, what alternatives were weighed, and what the consequences are.

Rules:
- **Only accepted decisions live here.** Proposed or deferred items go in [proposals/](../proposals/).
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Retired decisions are removed.** If a decision was made but the question it answered no longer applies, delete it. The git history is the record.
- **Sequencing is not decided here.** *When* a decision is implemented lives in the [release roadmap](../plans/release-plan-v0.1.md), which can change independently of these decisions. Decisions record the choice; the timeline records the schedule — link to it rather than restating phase order, so a re-plan does not strand stale dates in these files.

---

## Index

### Architecture

| # | Title |
|---|---|
| [01](01-three-layer-architecture.md) | Three-layer architecture: board, workers, vault |
| [02](02-seven-specialist-profiles.md) | Seven specialist profiles over one generalist |
| [03](03-structural-review-gate.md) | Review gate is structural, enforced by the policy MCP |
| [04](04-lifecycle-over-topic-folders.md) | Folders encode lifecycle stage, not subject area |
| [05](05-zotero-as-bibliographic-backbone.md) | Zotero + Better BibTeX as the bibliographic backbone |
| [21](21-l3-autonomy-ceiling.md) | L3 autonomy ceiling, structurally enforced (Coder-lane exception) |
| [22](22-build-on-hermes-runtime.md) | Build on the Hermes Agent runtime, not a bespoke one |
| [23](23-six-memory-substrates.md) | Memory is seven scoped substrates, not one store |
| [24](24-single-researcher-scope.md) | Single-researcher scope; multi-user out of scope |

### Vault and schema

| # | Title |
|---|---|
| [06](06-citekey-naming-convention.md) | Citekey naming convention |
| [08](08-typed-relations-frontmatter.md) | Typed relations in frontmatter (`supports` / `contradicts`) |
| [09](09-contradictions-dashboard.md) | Contradictions dashboard |
| [10](10-claim-supersession.md) | Claim supersession relation |
| [15](15-project-auto-classification.md) | Project membership is agent-proposed, human-confirmed |
| [17](17-shared-candidate-frontmatter.md) | Shared candidate frontmatter (`candidate-note`, the 16th type) |

### Tooling and integrations

| # | Title |
|---|---|
| [07](07-code-agent-attachment.md) | External coding agent boundary |
| [12](12-obsidian-linter-reference-only.md) | obsidian-linter is reference-only, not control-plane |
| [13](13-homepage-front-door.md) | Homepage front-door note |
| [25](25-session-logging-two-logs.md) | Two session logs — hash-chained audit vs. narrative |
| [26](26-repo-as-install-unit.md) | The repo is the install unit; profiles hand-authored |
| [27](27-hermes-native-config-and-gate-enforcement.md) | Configure Hermes the way it reads config; gate via toolset allowlist + obsidian-only writes |
| [28](28-write-gate-as-plugin.md) | The vault write gate is a Hermes Python plugin, not a shell hook |

### Workflows

| # | Title |
|---|---|
| [11](11-vault-eval-integration.md) | vault-eval as a maintenance capability |
| [14](14-advisor-review-vs-frozen-deliverable.md) | Advisor-review exports are live-citation artifacts |
| [16](16-adopt-on-demand-for-reviews.md) | Adopt-on-demand: systematic-review tooling cluster |
| [18](18-rename-agent-verdict.md) | Rename card field `agent_verdict` → `agent_recommendation` |
| [19](19-moc-threshold-alert.md) | Agent-proposed MOC threshold alert (Tier 1, report-only) |
| [20](20-publication-path.md) | Publication path: vault-eval benchmark first, capture-now |
