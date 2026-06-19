---
topic: decisions
id: 82
title: The four gates are the single user-facing vocabulary; retire the Compile/Compose cycle naming
status: superseded
date_proposed: 2026-06-18
date_resolved: 2026-06-18
assumes: [48, 70, 77]
supersedes: []
superseded_by: [84]
parent: Decisions
grand_parent: Explanation
nav_order: 82
---

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
