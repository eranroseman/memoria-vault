---
title: The Writer
parent: Profiles
---


# The Writer

The Writer turns evidence into structured prose — answer drafts, reference-ready content, manuscript sections, and competing outlines. Its defining constraint is **drafts, not canonical content**: every Writer output lands in a review state and never directly in `30-synthesis/01-claims/`. The human owns canonical synthesis; Writer is the composer whose work the human reviews, edits, and either promotes or discards.

---

## Why it's designed this way

**Review-gated writes degrade to dry-run.** Writer's lane policy declares writes to all canonical synthesis and deliverable zones as `dry_run` — the writes become board comments for the human to act on rather than failing loudly. This is the policy-level enforcement of "canonical synthesis is human-owned": even an aggressive Writer cannot corrupt the canonical layer, because the policy MCP intercepts any attempt.

**No external API access.** Unlike Librarian (network-heavy) or Verifier (external retraction checks), Writer doesn't reach outside the vault. Its inputs are entirely what the human has already accumulated — sources, claim notes, MOCs. This keeps the cost surface predictable, prevents prompt-injection via fetched content, and keeps the writing grounded in the human's own corpus rather than freshly retrieved material.

**The `counter-outline` skill narrows Writer further.** When the `counter-outline` skill loads during the Frame stage, it adds deny rules that restrict Writer's write scope to `40-workbench/<project>/02-framing/` only. This makes "explore competing framings before committing" a structurally enforced step rather than an optional good habit — a skill that tightens the host lane, never loosens it.

---

## What the Writer is not

**Not Socratic.** Socratic asks questions to help the human think before writing. Writer composes prose after thinking is done. They are sequential — Socratic belongs in the Discuss stage, Writer in the Draft stage — not interchangeable. A system that blurs these two produces writing that sounds like the human's thinking but was never actually theirs.

**Not Verifier.** Writer drafts; Verifier checks. Writer's job is to make tracing *possible* — cite sources explicitly, link claim notes by wikilink — not to do the tracing. The actual citation check, claim trace, and similarity check are Verifier's operations. Writer must not pre-empt them, because doing so would make the verification step redundant.

**Not Mapper.** Mapper maps the corpus; Writer composes arguments from it. Writer reads Mapper's outputs (`corpus-map.md`, `gap-report.md`) as context but does not produce maps or modify them.

**Not autonomous about canonical promotion.** Writer can *propose* promotion of a claim note to reference note via a handoff command, but cannot perform the move. The human approves. The distinction preserves the human's ownership of what becomes canonical.

---

## Related

**Explanation**

- The profile Writer relies on for pre-writing thinking: [Socratic](socratic.md)
- The profile that checks Writer's output: [Verifier](verifier.md)
- The profile that provides Writer's corpus maps: [Mapper](mapper.md)
- Why canonical synthesis belongs to the human: [why not autonomous](../rationale/why-not-autonomous.md)
- Why the Writer must not produce canonical claims: [Note body structure](../knowledge/note-body-structure.md)

**How-to**

- Workflows: [draft with the Writer](../../how-to-guides/writing/draft-with-writer.md), [frame a project](../../how-to-guides/writing/frame-a-project.md)
