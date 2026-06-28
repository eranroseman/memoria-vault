---
topic: decisions
id: 101
title: Navigation surfaces are "spaces"; "gate" is reserved for the approval gate
nav_exclude: true
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [48, 70, 77]
supersedes: [82]
superseded_by: []
---

# ADR-101: Navigation surfaces are "spaces"; "gate" is reserved for the approval gate

## Context

[ADR-82](82-four-gates-canonical-vocabulary.md) made the four intent-named navigation surfaces — Inbox · Library · Knowledge · Project — the single canonical user-facing vocabulary, and called them **gates**. But "gate" was *already* the system's word for a different, deeper concept: the **structural human approval checkpoint** ([ADR-03](03-structural-review-gate.md)) — the review / human / policy / write gate the policy MCP enforces. That sense is also the industry-standard one: a quality gate, a stage-gate, a human-in-the-loop *approval gate* all name a pass/fail checkpoint, not a place.

So "gate" carried two heavily-used senses at once — a navigation surface (a place you stand) and an approval checkpoint (a wall a write must pass) — and they collide. A bare "the gate" became genuinely ambiguous, and a lexical audit found the approval sense outnumbering the navigation sense roughly 480:190. Two further minor senses muddied it: the git **pre-commit** check ("the commit gate") and the Hermes **gateway** process. When one word names several load-bearing concepts, the cognitive model degrades — the same design smell ADR-82 itself invoked.

## Decision

**"Gate" is reserved for the gating sense — the approval/policy/review checkpoint. The navigation surfaces are renamed "spaces."**

1. **Navigation surfaces → spaces.** The four surfaces are the **Inbox · Library · Knowledge · Project spaces**. The note type is `space` (`type: space`, `space:` enum field), they live in `vault-template/spaces/`, and the `gate: gates` type→folder map becomes `space: spaces`. "Spaces" is chosen over the other candidate, "views," because Obsidian already uses **view** natively (Reading view, graph view, `ItemView`) — reusing it would relocate the overload, not remove it. "Space" is clean in Obsidian's vocabulary and keeps the destination feel the surfaces need.
2. **"Gate" = the approval checkpoint, always stated fully.** The structural human gate is written **review gate / human gate / policy gate / write gate** — never a bare "gate" where the surrounding text does not already establish it ([ADR-03](03-structural-review-gate.md), [ADR-27](27-hermes-native-config-and-gate-enforcement.md), [ADR-28](28-write-gate-as-plugin.md), [ADR-41](41-configurable-review-gate-mode.md) are unchanged).
3. **Pre-commit is a hook, not a gate.** The git schema-validation check is the **pre-commit hook**; CI enforcement is **required status checks** — not "the commit gate."
4. **The runtime entry point is the gateway.** Always "gateway"; never abbreviated to "gate."
5. **The project readiness gate keeps "gate."** The deterministic structural-impact check (`project-gate.md`, `project-gate.base`, `project-gate-index.md`, `refresh project gate`) is a *quality/readiness gate* and correctly keeps the word — the navigation rename disambiguates it from the Project space.
6. **Compile/Compose stays retired** (carried forward from ADR-82): the how-to guides remain grouped `how-to-guides/{inbox,library,knowledge,project}/` and the cycle vocabulary is not revived.

## Consequences

- Data model: `schemas/types/gate.yaml` → `space.yaml` (type, category, enum field); `folders.yaml`, the Linter `detectors.py` folder maps, and the installer `manifest.sh` skeleton all move `gates` → `spaces`; the four `vault-template/gates/*.md` notes move to `vault-template/spaces/`.
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
