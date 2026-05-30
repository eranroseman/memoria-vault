---
topic: dashboards
---

# `contradictions` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/contradictions.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Surface claim notes that **disagree with each other** as a synthesis starting point. The dashboard collects every `claim-note` carrying a human-set `relations.contradicts` link and lists the conflicting pairs, so the human can open "claims I've filed that conflict" in one place rather than holding them in their head. Open this when building an argument or during the weekly synthesis pass — a cluster of contradictions is usually where the interesting writing is. Adopted in [ADR-16](../../project/decisions/16-contradictions-dashboard.md); reads the `contradicts` relation from [ADR-9](../../project/decisions/09-typed-relations-frontmatter.md).

## What this dashboard is not

- **Not an LLM tension-finder.** v1 reads only **human-set** `relations.contradicts` links — there is no model judging which claims conflict, in keeping with the deterministic-rollup discipline every dashboard follows. The deterministic **NLI candidate proposer** that would *suggest* pairs to confirm is deferred future work ([future-directions §NLI-based contradiction detection](../../project/roadmap/future-directions.md#nli-based-contradiction-detection)); it never auto-writes a link.
- **Not a truth judgment.** A `contradicts` edge says two claims disagree, not which one is right — resolving the tension (soften, supersede, or keep both as a live debate) is the human's call. Supersession is a *different* relation: [`superseded_by`](../../reference/frontmatter-schema.md) records that one claim *replaced* another over time; `contradicts` records that two current claims disagree.
- **Not a defect list.** A paper refuting an earlier one is a wanted finding. The dashboard frames pairs as "worth resolving," never as errors to clear.

## Design decisions

- **Reads `relations.contradicts`, human-set (ADR-9).** The data is the opt-in typed relation; the dashboard is a pure consumer. No new schema beyond ADR-9's `relations:` block.
- **Pairs deduplicated; `contradicts` is symmetric.** A link set on either note surfaces the pair once — the query collapses A↔B so a mutually-typed pair isn't listed twice.
- **Day-one sparseness is expected — and is the signal.** Until the human files `contradicts` links the dashboard is near-empty; that emptiness is exactly what tells you whether the [NLI proposer](../../project/roadmap/future-directions.md#nli-based-contradiction-detection) is worth building (expansion-threshold discipline). Adopting the surface first, the proposer later, is deliberate.
- **Diagnostic, not gating.** Like [`open-questions`](open-questions.md), it informs synthesis; it never pauses scheduled work (unlike [`drift-watch`](drift-watch.md)'s structural FAIL).
- **Graceful degradation.** With zero `contradicts` links the page shows explanatory text, not an empty table.

## Related

- [ADR-16 contradictions dashboard](../../project/decisions/16-contradictions-dashboard.md) — the decision this implements; [ADR-9 typed relations](../../project/decisions/09-typed-relations-frontmatter.md) — supplies `relations.contradicts`.
- [`open-questions`](open-questions.md) — closest sibling; both turn the vault into a synthesis agenda (questions vs. tensions).
- [future-directions §NLI-based contradiction detection](../../project/roadmap/future-directions.md#nli-based-contradiction-detection) — the deterministic proposer that populates a v2.
- [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md) — the `relations:` namespace and how `contradicts` differs from `superseded_by`.
- [Linter design summary](../profiles/linter.md) — validates `relations:` keys against the controlled vocabulary.
