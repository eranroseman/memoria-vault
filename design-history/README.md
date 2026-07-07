# Memoria Design History

This directory is the durable design-history record for released Memoria design.
It preserves facts about what each alpha release claimed, changed, removed, and
implemented.

Latest completed checkpoint: `alpha.18`

## Rules

1. Per-version chapters are frozen evidence after the release closes. Correct
   only transcription errors or broken links; do not rewrite the chapter to fit
   a later opinion.
2. `arcs.md` is the maintained synthesis. Update it when a release changes the
   current design line, and mark unreleased work as pending rather than fact.
3. Historical evidence is not authority. If an old note, ADR, or chapter
   conflicts with current implemented behavior, the implemented behavior and
   current release decision win.
4. Decision-time capture happens in the active release workspace as dated
   Y-statements with typed pointers to evidence, implementation, tests, and
   reversals.
5. Release close folds accepted/rejected decisions into the new frozen chapter
   and updates `arcs.md`; the scratch decision ledger remains evidence.

## Files

- `00-origins.md` through `18-alpha.18.md`: frozen release-history chapters.
- `arcs.md`: maintained cross-release synthesis and current/pending state.
