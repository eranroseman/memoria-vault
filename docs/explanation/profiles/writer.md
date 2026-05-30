---
topic: profiles
---

# Writer — design summary

**Runtime contract.** Full prompt and operational details live at `.memoria/profiles/memoria-writer/SOUL.md` in the starter vault.

## Mission

Writer turns evidence into structured prose — answer drafts, reference-ready content, manuscript sections, and counter-outlines. The defining trait is **drafts, not canonical content**: every Writer output lands in a review state (`10-inbox/02-answers/`, `40-workbench/*/04-drafts/`, or a `30-synthesis/02-reference/` draft awaiting approval) and never in `30-synthesis/01-claims/`. The human owns canonical synthesis; Writer is the composer whose work the human reviews, edits, and either promotes or discards.

## What this profile is not

- **Not Socratic.** Socratic asks questions to help the human think before writing. Writer composes prose after thinking is done. They are sequential — Socratic in Process, Writer in Draft — not interchangeable.
- **Not Verifier.** Writer drafts; Verifier checks. Writer's job is to make tracing *possible* (cite explicitly, link to claim notes by wikilink); the actual citation check, claim trace, and similarity check are Verifier's commands. Writer must not pre-empt them.
- **Not Mapper.** Mapper maps the corpus; Writer composes arguments from it. Writer reads Mapper's outputs (`corpus-map.md`, `gap-report.md`) as context, but does not produce maps.
- **Not autonomous about canonical promotion.** Writer can *propose* promotion of a claim-note to reference-note via the `promote` handoff command, but cannot move it. The human approves the move.

## Design decisions

- **Review-gated-zone writes degrade to `dry_run`.** Writer's lane-override declares writes to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/` as `dry_run` — the writes don't fail loudly, they become board comments for the human to act on. This is the policy-level enforcement of "canonical synthesis is human-owned"; even an aggressive Writer cannot corrupt the canonical layer.
- **Synthesis is generative, end-to-end.** Writer's method class is **generative**: composing prose, structuring arguments, suggesting alternative outlines — none of these have deterministic derivations from inputs. LLM-required throughout, with one exception: the `query` step is deterministic vault search before drafting begins.
- **The `counter-outline` skill is restrictive by design.** When loaded during the Frame stage, `counter-outline` adds policy.deny rules that narrow Writer's write scope to `40-workbench/<project>/02-framing/` only. This is the definitive example of skill-conditional policy: a skill *tightens* the host lane, never loosens it.
- **No external API access.** Unlike Librarian (network-heavy) or Verifier (Zotero/CrossRef for retraction checks), Writer doesn't reach the outside world. Its inputs are entirely the human's existing vault — sources, claim notes, MOCs. This keeps the cost surface predictable and prevents prompt-injection-via-fetched-content.

## Permissions and commands

Folder permission matrix lives in [profiles/README.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract lives in the SOUL.md.

## Related

- Workflows: [write](../../how-to/workflows/downstream/write.md), [frame](../../how-to/workflows/downstream/frame.md), [distill](../../how-to/workflows/upstream/distill.md), [revise](../../how-to/workflows/downstream/revise.md)
- ADRs: [15 dedicated review-note type](../../project/decisions/15-dedicated-review-note-type.md), [03 answer draft retention](../../project/decisions/03-answer-draft-retention.md)
- Architecture: [architecture/why-no-autonomous-synthesis.md](../architecture/why-no-autonomous-synthesis.md) — the principle that motivates the `dry_run` degradation on review-gated zones.
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Writer is on the generative side throughout.
