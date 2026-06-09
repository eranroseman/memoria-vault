---
topic: decisions
---

# Decisions

Accepted architectural decisions for Memoria. Each file records one choice: what
was decided, why, which alternatives were weighed, and the consequences.

Files are named `NN-title.md` and are **browsable in this directory** — numbered in
acceptance order. To add one, copy [_template.md](_template.md) and take the next
number.

## Index

<!-- ADR-INDEX:START -->

| # | Decision | Status |
|---|---|---|
| [01](01-three-layer-architecture.md) | Three-layer architecture — board, workers, vault | accepted |
| [02](02-seven-specialist-profiles.md) | Seven specialist profiles over one generalist agent | accepted |
| [03](03-structural-review-gate.md) | Review gate is structural, enforced by the policy MCP | accepted |
| [04](04-lifecycle-over-topic-folders.md) | Folders encode lifecycle stage, not subject area | accepted |
| [05](05-zotero-as-bibliographic-backbone.md) | Zotero + Better BibTeX as the bibliographic backbone | accepted |
| [06](06-citekey-naming-convention.md) | Citekey naming convention | accepted |
| [07](07-code-agent-attachment.md) | Code agent attachment | accepted |
| [08](08-typed-relations-frontmatter.md) | Typed relations frontmatter | accepted |
| [09](09-contradictions-dashboard.md) | Contradictions / tensions dashboard | accepted |
| [10](10-claim-supersession.md) | Claim supersession relation | accepted |
| [11](11-vault-eval-integration.md) | vault-eval as a maintenance capability | accepted |
| [12](12-obsidian-linter-reference-only.md) | obsidian-linter is reference-only, not a control-plane formatter | accepted |
| [13](13-homepage-front-door.md) | Homepage front-door note, auto-opened by obsidian-homepage | accepted |
| [14](14-advisor-review-vs-frozen-deliverable.md) | Advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract | accepted |
| [15](15-project-auto-classification.md) | Project membership is agent-proposed from a lightweight per-project topic hint, human-confirmed | accepted |
| [16](16-adopt-on-demand-for-reviews.md) | Adopt-on-demand — systematic-review tooling | accepted |
| [17](17-shared-candidate-frontmatter.md) | Shared candidate frontmatter format | accepted |
| [18](18-rename-agent-verdict.md) | Rename `agent_verdict` → `agent_recommendation` | accepted |
| [19](19-moc-threshold-alert.md) | Agent-proposed MOCs (threshold alert; Mapper stub deferred) | accepted |
| [20](20-publication-path.md) | Publication path — vault-eval benchmark first, capture-now | accepted |
| [21](21-l3-autonomy-ceiling.md) | L3 autonomy ceiling, structurally enforced, with the Coder-lane exception | accepted |
| [22](22-build-on-hermes-runtime.md) | Build on the Hermes Agent runtime rather than a bespoke one | accepted |
| [23](23-six-memory-substrates.md) | Memory is seven scoped substrates, not one store | accepted |
| [24](24-single-researcher-scope.md) | Single-researcher scope — multi-user semantics are out of scope | accepted |
| [25](25-session-logging-two-logs.md) | Two separate session logs — hash-chained audit vs. narrative summaries | accepted |
| [26](26-repo-as-install-unit.md) | The repo is the install unit; profiles are hand-authored and idempotently deployed | accepted |
| [27](27-hermes-native-config-and-gate-enforcement.md) | Configure Hermes the way Hermes reads config; the review gate enforces via a toolset allowlist with obsidian as the only write path | accepted → ADR-28 |
| [28](28-write-gate-as-plugin.md) | The vault write gate is a Hermes Python plugin, not a shell hook | accepted |
| [29](29-testing-framework.md) | A layered testing framework, not a pile of plans | accepted |
| [30](30-deterministic-ingest-pipeline.md) | Tiered ingest pipeline (capture → fallback-chained enrichment → gated write) | accepted |
| [31](31-native-obsidian-mcp.md) | Vault access via the Local REST API plugin's native MCP (HTTP), not uvx mcp-obsidian | accepted |
| [32](32-external-access-over-mcp.md) | Profile capabilities and external access reach the agent only over MCP; deterministic tools are self-hosted | accepted |
| [33](33-cluster-mcp-bertopic.md) | The Mapper's clustering runs over a Memoria-authored BERTopic MCP, not in-agent ML skills | accepted |

<!-- ADR-INDEX:END -->

This table is generated from each ADR's frontmatter by
[`scripts/gen-adr-index.py`](../../scripts/gen-adr-index.py) — run it after adding or
editing an ADR; CI fails if it is stale. Do not edit the table by hand.

Rules:

- **Only accepted decisions live here.** Proposed or deferred items go in [rfc/](../rfc/).
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Retired decisions are removed.** If the question a decision answered no longer applies, delete it — git history is the record.
- **Sequencing is not decided here.** *When* a decision ships lives in the [release plan](../release/v0.1/release-plan-v0.1.md), which changes independently of these decisions. Link to it rather than restating phase order, so a re-plan does not strand stale dates here.
