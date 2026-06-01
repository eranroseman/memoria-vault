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

### Deferred from decisions

Files originally written as ADR candidates — real decisions that didn't get made yet or features that need conditions to be met first.

| File | What it proposes |
|---|---|
| [10-code-artifact-autopilot.md](10-code-artifact-autopilot.md) | Autonomous keep/revert loop in Coder lane |
| [14-cross-run-skill-insights.md](14-cross-run-skill-insights.md) | Cross-run skill-insights memory |
| [15-dedicated-review-note-type.md](15-dedicated-review-note-type.md) | Dedicated review-note type |
| [17-retriever-scout-profile.md](17-retriever-scout-profile.md) | Split Librarian into Retriever + Librarian |
| [21-shared-candidate-frontmatter.md](21-shared-candidate-frontmatter.md) | Shared candidate frontmatter format |
| [27-ratchet-duplicate-gate.md](27-ratchet-duplicate-gate.md) | Similarity gate before filing synthesis notes |
| [28-frozen-evaluator-deferred.md](28-frozen-evaluator-deferred.md) | Per-note-type acceptance checklists |
| [29-admin-gui-surface.md](29-admin-gui-surface.md) | Admin/forensic GUI surface |
| [31-configurable-review-gate-mode.md](31-configurable-review-gate-mode.md) | Configurable review-gate mode for comparison studies |

### Capability proposals

Thematic groups from the future-directions survey.

| File | What it covers |
|---|---|
| [discovery-loop.md](discovery-loop.md) | Proactive nightly discovery; Coder experiment loop; agent-proposed claim candidates |
| [measurement-and-verification.md](measurement-and-verification.md) | CiteME harness, chain-of-evidence taxonomy, fleet observability, propagation debts |
| [classical-method-displacements.md](classical-method-displacements.md) | NLI contradiction detection, learning-to-rank, claim-sentence classification |
| [triage-improvements.md](triage-improvements.md) | Semi-autonomous triage, consensus pre-filter, tournament ranking |
| [schema-and-retrieval.md](schema-and-retrieval.md) | Scenario-typed retrieval extensions, MASSW aspects, exploration-trace capture |
| [integrations.md](integrations.md) | Inspector plugin, Todoist gap-cards, open-design, static reports |
| [multi-vault-and-multi-machine.md](multi-vault-and-multi-machine.md) | Cross-vault retrieval, session-history sync, shared memory server |
| [skill-governance.md](skill-governance.md) | Skill lifecycle state machine and governance overlay |
| [profile-compilation.md](profile-compilation.md) | Build step to generate shared SOUL.md content from a base template |
| [bootstrap-installer.md](bootstrap-installer.md) | One-line full-stack installer (Obsidian + Hermes + Zotero + vault); **user-requested, under review** |
| [moc-threshold-alert.md](moc-threshold-alert.md) | Agent-proposed MOCs: threshold alert (report-only), then optional bare-stub draft |
| [rename-agent-verdict.md](rename-agent-verdict.md) | Rename card field `agent_verdict` → `agent_recommendation` |

### Rejected alternatives

Tools and approaches evaluated and not adopted.

| File | What was rejected |
|---|---|
| [../rejected/obsidian-kanban.md](../rejected/obsidian-kanban.md) | Obsidian Kanban plugin as board layer |
| [../rejected/obsidian-linter.md](../rejected/obsidian-linter.md) | obsidian-linter as a control-plane formatter |
| [../rejected/zotero-integration.md](../rejected/zotero-integration.md) | Alternative Zotero integration approaches |
| [../rejected/zotlit.md](../rejected/zotlit.md) | ZotLit Obsidian plugin |
