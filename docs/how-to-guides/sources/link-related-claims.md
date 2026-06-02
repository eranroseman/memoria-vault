---
title: How to link related claims (typed relations)
parent: Sources
---


# How to link related claims (typed relations)

Once you have more than a handful of claim notes, the useful signal is not just *that* two claims relate but *how*. A `relations:` block records `supports` / `contradicts` as machine-queryable, **human-set** links — and a `contradicts` link is the data the [contradictions dashboard](../../explanation/dashboards/synthesis-agenda/contradictions.md) reads. This guide is for adding a typed relation between two claims that **already exist**. To set one at the moment you write a claim, use Step 7 of [Write a claim note](write-a-claim-note.md) instead.

## Prerequisites

- At least two claim notes in `30-synthesis/01-claims/`
- These links are yours to set — agents only *propose* relations, never write them (ADR-08)

## Steps

**1. Decide whether the relationship is worth typing.**

Link for usefulness, not completeness. Add a typed relation only when "*what contradicts X?*" or "*what supports X?*" would matter in a later reading or writing session. Untyped concept links (a plain `[[wikilink]]` in the body) remain first-class — don't promote every link to a typed one. The vocabulary is deliberately small precisely so the block stays meaningful.

**2. Pick the relation type.**

| Relation | Meaning | Direction |
| --- | --- | --- |
| `supports` | This claim supports the linked claim | Directional — set it on the supporting claim |
| `contradicts` | The two claims disagree | Symmetric — set it on either; the dashboard reads both ways |

These are the only two relation types in v1. There is no `extends`/`refines` relation — if you reach for one, it doesn't exist yet (it's named as future work in ADR-08). If the relationship is *temporal replacement* — this claim makes an older one obsolete — that is **not** a `relations:` entry; it's supersession (`superseded_by`), covered in [Promote a claim](promote-a-claim.md) and Step 7 of [Write a claim note](write-a-claim-note.md).

**3. Add the block to the claim you're editing.**

Open the claim note and add (or extend) the `relations:` block in frontmatter:

```yaml
relations:
  contradicts:
    - "[[receptivity-decreases-under-high-cognitive-load]]"
```

`supports` and `contradicts` can both appear, each a list — a claim may support one claim and contradict another.

**4. Point with the exact slug.**

The target is a wikilink to the other claim's **permanent slug** (lowercase kebab-case, subject-verb-object — see [Wikilink and link conventions](../../reference/linking.md#slug-conventions-for-wikilinks)). A mistyped slug is a dangling relation the dashboard can't resolve, and it fails silently. Copy the slug from the target note's filename rather than retyping it.

**5. Let the agent propose, but confirm it yourself.**

The Verifier or Mapper may surface a candidate contradiction into the proposal namespace (`_proposed_classification`). Never treat an agent-proposed relation as canonical — read it, judge it, then set the link by hand. Typing a link is a canonical-surface judgment; the agent proposes, you dispose (the autonomy boundary, ADR-08).

**6. Confirm it surfaced.**

For a `contradicts` link, open the [contradictions dashboard](../../explanation/dashboards/synthesis-agenda/contradictions.md). The pair should now appear there — that visibility is the whole payoff of typing the link rather than leaving it untyped.

## Verify

- The `relations:` block validates against the vocabulary — the Linter's `schema-check` flags any key outside `supports` / `contradicts`.
- A `contradicts` pair appears on the contradictions dashboard.
- Every relation target resolves to a real claim note (no dangling slug).

## Related

**How-to**

- Set a relation while authoring: [Write a claim note](write-a-claim-note.md) (Step 7)
- The temporal complement (replacement, not disagreement): [Promote a claim](promote-a-claim.md), supersession (ADR-10)

**Reference**

- Syntax and vocabulary: [linking.md — Typed relations](../../reference/linking.md#typed-relations-relations-block), [Frontmatter fields](../../reference/frontmatter.md)

**Explanation**

- The consumer: [contradictions dashboard](../../explanation/dashboards/synthesis-agenda/contradictions.md)
- Why the Connections section is required: [Note body structure](../../explanation/knowledge/note-body-structure.md)

**Background**

- Why typed links are human-set and opt-in: [ADR-08](../../../project-files/decisions/08-typed-relations-frontmatter.md)
