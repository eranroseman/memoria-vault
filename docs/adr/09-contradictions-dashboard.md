---
topic: decisions
id: 09
title: Contradictions / tensions dashboard
nav_exclude: true
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-29
assumes: []
supersedes: []
superseded_by: []
---

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

**LLM-judged contradictions** (let an LLM read the corpus and flag tensions): rejected — LLM-as-similarity-judge has the calibration problem named in [Why Memoria uses deterministic methods alongside LLMs](../design/why-computational-methods.md); different runs surface different tensions with no stable ground truth. The memory-benchmark review ([Measurement and verification harnesses](62-measurement-and-verification-harnesses.md)) independently confirms LLM memory/similarity judgments are unreliable.

**Ship the NLI proposer in v1**: deferred, not rejected — NLI is deterministic and the right eventual proposer ([Why Memoria uses deterministic methods alongside LLMs](../design/why-computational-methods.md)), but building it before the manual dashboard proves demand inverts the expansion-threshold rule. v1 ships the surface; the proposer graduates later.

## Related

- **Depends on:** [ADR-8 typed relations](08-typed-relations-frontmatter.md) (supplies the contradicts edges — now `links.contradicts` after [ADR-52](52-links-vs-relationships.md)).
- **Files affected:** [contradictions dashboard](../explanation/dashboards/synthesis-agenda/README.md#contradictions) (new), [Dashboards](../explanation/dashboards/README.md) (index).
- **Future proposer:** [Classical method displacements](59-classical-method-displacements.md) — the deterministic NLI candidate-generation engine that populates v2.
- **Related decisions:** [ADR-10 claim supersession](10-claim-supersession.md) (supersession is the temporal complement to contradiction).
