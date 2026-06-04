---
topic: proposals
---

# Proposals

Capabilities that have been thought through but not yet adopted. Each has a clear shape, known trade-offs, and an explicit adoption trigger — a specific condition that would warrant scheduling it.

A proposal is not a to-do list item. It won't be scheduled until its trigger fires.

---

## How to use this folder

**Adding an idea:** Copy `_template.md`, fill it in, name the file `slug-describing-capability.md`. No numbers — proposals are unordered.

**When a proposal is adopted:** Move the file to `decisions/`, assign the next ADR number, update `status: accepted`. The proposal file becomes the ADR's starting point.

**When a proposal is rejected:** Add a `status: rejected` frontmatter field and a "Why rejected" section. Keep the file — it's cheaper to say "we considered this and rejected it because X" than to rediscover the same idea later.

---

## Index

### Adopted into v0.1 (2026-06-01)

Three were accepted and **moved to `decisions/`** as ADRs; the bootstrap installer is implemented and its design moved to docs (an as-built spec, not a deferred proposal).

| Now at | What it added |
|---|---|
| [decisions/ADR-17](../decisions/17-shared-candidate-frontmatter.md) | `candidate-note` (16th type) — discovery candidates + Verifier gap-cards (`source: gap`) + ingestion dead-letters |
| [decisions/ADR-18](../decisions/18-rename-agent-verdict.md) | `agent_verdict` → `agent_recommendation` across schema / dashboards / docs |
| [decisions/ADR-19](../decisions/19-moc-threshold-alert.md) | **Tier 1** — report-only MOC-threshold Linter check (Tier 2 still deferred) |
| [docs: bootstrap installer](../../docs/explanation/deployment/bootstrap-installer.md) | One-line installer (`scripts/install.sh` + thin `scripts/install.ps1`) — implemented; design now in docs ([reference inventories](../../docs/reference/installer.md)) |

### Single-capability proposals (PROP-NN)

One capability each, numbered. These follow the full [template](_template.md) — What / Why / Trade-offs / Adoption trigger / Guard, plus Alternatives considered and Related.

| File | What it proposes |
|---|---|
| [PROP-01-code-artifact-autopilot.md](PROP-01-code-artifact-autopilot.md) | Autonomous keep/revert loop in Coder lane |
| [PROP-02-cross-run-skill-insights.md](PROP-02-cross-run-skill-insights.md) | Cross-run skill-insights memory |
| [PROP-03-dedicated-review-note-type.md](PROP-03-dedicated-review-note-type.md) | Dedicated review-note type |
| [PROP-04-retriever-scout-profile.md](PROP-04-retriever-scout-profile.md) | Split Librarian into Retriever + Librarian |
| [PROP-05-ratchet-duplicate-gate.md](PROP-05-ratchet-duplicate-gate.md) | Similarity gate before filing synthesis notes |
| [PROP-06-frozen-evaluator-deferred.md](PROP-06-frozen-evaluator-deferred.md) | Per-note-type acceptance checklists |
| [PROP-07-admin-gui-surface.md](PROP-07-admin-gui-surface.md) | Admin/forensic GUI surface |
| [PROP-08-configurable-review-gate-mode.md](PROP-08-configurable-review-gate-mode.md) | Configurable review-gate mode for comparison studies |
| [PROP-09-profile-compilation.md](PROP-09-profile-compilation.md) | Build step to generate shared SOUL.md content from a base template |
| [PROP-10-skill-governance.md](PROP-10-skill-governance.md) | Skill lifecycle state machine and governance overlay |

### Capability proposals

Thematic surveys that bundle several related capabilities, kept in [surveys/](surveys/). Unnumbered; each capability carries its own What / Trade-offs / Adoption trigger / Guard block.

| File | What it covers |
|---|---|
| [discovery-loop.md](surveys/discovery-loop.md) | Proactive nightly discovery; Coder experiment loop; agent-proposed claim candidates |
| [measurement-and-verification.md](surveys/measurement-and-verification.md) | CiteME harness, chain-of-evidence taxonomy, fleet observability, propagation debts |
| [publication-strategy.md](surveys/publication-strategy.md) | Four publication paths + shapes + sequence; the deferred analysis behind ADR-20 (Path 2/3 selection) |
| [classical-method-displacements.md](surveys/classical-method-displacements.md) | NLI contradiction detection, learning-to-rank, claim-sentence classification |
| [triage-improvements.md](surveys/triage-improvements.md) | Semi-autonomous triage, consensus pre-filter, tournament ranking |
| [schema-and-retrieval.md](surveys/schema-and-retrieval.md) | Scenario-typed retrieval extensions, MASSW aspects, exploration-trace capture |
| [integrations.md](surveys/integrations.md) | Inspector plugin, Todoist gap-cards, open-design, static reports |
| [multi-vault-and-multi-machine.md](surveys/multi-vault-and-multi-machine.md) | Cross-vault retrieval, session-history sync, shared memory server |
| [multi-machine-deployment.md](surveys/multi-machine-deployment.md) | Deferred deployment topologies (local-mesh, obsidian-sync, always-on) and secondary-device patterns |

> **Deployment:** the adopted `local-only` default and the conventions common to every sync pattern are documented in [docs: deployment options](../../docs/explanation/deployment/deployment-options.md); only the multi-machine topologies above remain a proposal.

### Rejected alternatives

Tools and approaches evaluated and not adopted are recorded as *Alternatives considered* in the relevant decision, with practical detail in the plugin reference docs.

| What was rejected | Where it's recorded |
|---|---|
| Obsidian Kanban plugin as the board layer | [ADR-22](../decisions/22-build-on-hermes-runtime.md), [obsidian-plugins.md](../../docs/reference/obsidian-plugins.md) |
| obsidian-linter as a control-plane formatter | [ADR-12](../decisions/12-obsidian-linter-reference-only.md), [obsidian-plugins.md](../../docs/reference/obsidian-plugins.md) |
| ZotLit / zotero-integration Zotero connectors | [ADR-05](../decisions/05-zotero-as-bibliographic-backbone.md), [zotero-plugins.md](../../docs/reference/zotero-plugins.md) |
