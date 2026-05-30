---
topic: decisions
id: 9
title: Typed relations frontmatter
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-29
supersedes: []
superseded_by: []
---

# ADR-9: Typed `relations:` frontmatter

## Context

Plain wikilinks record *that* two claims relate, not *how*. Graph queries and argument-construction operations need — "what contradicts X", "what supports X", "what methods feed this lineage" — can't be answered from untyped links. [ADR-22](22-claim-supersession.md) already carved out the one correctness-critical typed relation (`superseded_by`, top-level) as a correctness-critical slice of this namespace, and [ADR-16](16-contradictions-dashboard.md)'s contradictions dashboard needs `contradicts` to have data to read. The original deferral assumed typed links would be a per-link maintenance burden; the question is whether that cost is real once the relation is *opt-in*.

## Decision

Adopt a **`relations:` frontmatter block** on claim-notes for *associative* typed links, **human-set and opt-in**. The v1 vocabulary is deliberately small — `supports` (directional: this claim supports the target) and `contradicts` (symmetric: the two claims disagree). The block is **nested** (matching the `relations: { … }` notation [ADR-16](16-contradictions-dashboard.md) assumes); new relation types are added to the [schema reference](../../reference/frontmatter-schema.md) on felt need, not coined ad hoc. The temporal relations `supersedes` / `superseded_by` stay **top-level** as [ADR-22](22-claim-supersession.md) shipped them — they govern a claim's *currency* (a value property), distinct from the *associative* links in `relations:`. Typed links are opt-in: untyped wikilinks remain first-class and coexist; the agent may *propose* a relation into `_proposed_classification`, but never writes one onto a canonical note.

## Consequences

- Unblocks [ADR-16](16-contradictions-dashboard.md): the contradictions dashboard now has `relations.contradicts` to query.
- Adopting the *namespace* costs nothing when unused — opt-in means that below the density where typed links pay off they simply stay sparse; there is no "populate every link" burden. This is what made the earlier deferral unnecessary: the cost had been modeled as mandatory.
- Adds a small schema obligation: a `relations` controlled vocabulary in the [schema reference](../../reference/frontmatter-schema.md), a `schema_version` bump on the claim-note template, and a Linter check that flags `relations:` keys outside the vocabulary.
- Richer link semantics (a `relation_type:`-per-link list, an expanded PARNESS-style vocabulary — PARNESS: a typed-relation scheme covering supports, refutes, extends, uses, and similar rhetorical moves between claims) and an **NLI candidate-proposer** for `contradicts` remain future work — see [future-directions §scenario-typed retrieval](../roadmap/future-directions.md#scenario-typed-retrieval) and [§NLI-based contradiction detection](../roadmap/future-directions.md#nli-based-contradiction-detection). v1 is human-noticed, human-typed.

## Alternatives considered

**Keep deferring** (plain wikilinks only): rejected — the maintenance cost that justified the deferral assumed *every* link must be typed; an opt-in namespace removes that, and ADR-16 plus the supersession work ([ADR-22](22-claim-supersession.md)) make the felt need concrete.

**Flat top-level keys** (`supports:`, `contradicts:` at the top level): rejected — pollutes the top-level namespace and diverges from ADR-16's `relations: { … }` notation; the nested block groups associative links under one key.

**Fold supersession into `relations:`**: rejected — `superseded_by` derives a claim's *currency* and the Linter FAMA check keys on its top-level presence ([ADR-22](22-claim-supersession.md)); moving it would re-open an accepted decision and force a field-relocation migration for no semantic gain. Temporal currency and associative relation stay distinct.

**Agent-assigned relations**: rejected — typing a link is a canonical-surface judgment; the agent proposes, the human sets (the autonomy boundary, consistent with ADR-22).

## Related

- **Workflows affected:** [Distill](../../how-to/workflows/upstream/distill.md) (where `contradicts` / `supports` are set), [Promote](../../how-to/workflows/upstream/promote.md), [Query](../../how-to/workflows/downstream/query.md) (relation-aware retrieval).
- **Files affected:** [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md) (the `relations:` namespace + vocabulary), [vault/note-types.md](../../reference/note-types.md) + `00-meta/03-templates/claim-note.md`, the Linter's `M-detectors.md` (vocabulary check), [dashboards/contradictions.md](../../explanation/dashboards/contradictions.md) (consumer).
- **Required by:** [ADR-16 (Contradictions dashboard)](16-contradictions-dashboard.md) — now unblocked.
- **Related decisions:** [ADR-22 claim supersession](22-claim-supersession.md) (the temporal relation kept top-level; this generalizes the associative rest).
