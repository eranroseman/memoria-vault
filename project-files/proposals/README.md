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

Three were accepted and **moved to `decisions/`** as ADRs; the bootstrap installer is implemented and stays here (a user-requested install doc, not a numbered ADR).

| Now at | What it added |
|---|---|
| [decisions/ADR-21](../decisions/21-shared-candidate-frontmatter.md) | `candidate-note` (16th type) — discovery candidates + Verifier gap-cards (`source: gap`) + ingestion dead-letters |
| [decisions/ADR-22](../decisions/22-rename-agent-verdict.md) | `agent_verdict` → `agent_recommendation` across schema / dashboards / docs |
| [decisions/ADR-23](../decisions/23-moc-threshold-alert.md) | **Tier 1** — report-only MOC-threshold Linter check (Tier 2 still deferred) |
| [bootstrap-installer.md](bootstrap-installer.md) | One-line installer (`install.sh` + thin `install.ps1`) — implemented |

### Deferred from decisions

Files originally written as ADR candidates — real decisions that didn't get made yet or features that need conditions to be met first.

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

### Capability proposals

Thematic groups from the future-directions survey.

| File | What it covers |
|---|---|
| [discovery-loop.md](discovery-loop.md) | Proactive nightly discovery; Coder experiment loop; agent-proposed claim candidates |
| [measurement-and-verification.md](measurement-and-verification.md) | CiteME harness, chain-of-evidence taxonomy, fleet observability, propagation debts |
| [publication-strategy.md](publication-strategy.md) | Four publication paths + shapes + sequence; the deferred analysis behind ADR-24 (Path 2/3 selection) |
| [classical-method-displacements.md](classical-method-displacements.md) | NLI contradiction detection, learning-to-rank, claim-sentence classification |
| [triage-improvements.md](triage-improvements.md) | Semi-autonomous triage, consensus pre-filter, tournament ranking |
| [schema-and-retrieval.md](schema-and-retrieval.md) | Scenario-typed retrieval extensions, MASSW aspects, exploration-trace capture |
| [integrations.md](integrations.md) | Inspector plugin, Todoist gap-cards, open-design, static reports |
| [multi-vault-and-multi-machine.md](multi-vault-and-multi-machine.md) | Cross-vault retrieval, session-history sync, shared memory server |
| [skill-governance.md](skill-governance.md) | Skill lifecycle state machine and governance overlay |
| [profile-compilation.md](profile-compilation.md) | Build step to generate shared SOUL.md content from a base template |
| [bootstrap-installer.md](bootstrap-installer.md) | One-line full-stack installer (Obsidian + Hermes + Zotero + vault) — **implemented (see Adopted, above)** |

### Rejected alternatives

Tools and approaches evaluated and not adopted.

| File | What was rejected |
|---|---|
| [../rejected/obsidian-kanban.md](../rejected/obsidian-kanban.md) | Obsidian Kanban plugin as board layer |
| [../rejected/obsidian-linter.md](../rejected/obsidian-linter.md) | obsidian-linter as a control-plane formatter |
| [../rejected/zotero-integration.md](../rejected/zotero-integration.md) | Alternative Zotero integration approaches |
| [../rejected/zotlit.md](../rejected/zotlit.md) | ZotLit Obsidian plugin |
