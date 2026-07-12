# Memoria Design History

This directory is the durable design-history record for released Memoria design.
It preserves facts about what each alpha release claimed, changed, removed, and
implemented.

Latest completed checkpoint: `alpha.20`

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

- `00-origins.md` through `20-alpha.20.md`: frozen release-history chapters.
- `arcs.md`: maintained cross-release synthesis and current/pending state.
- `archive/`: primary-source research and explorations behind the chapters (see `archive/MANIFEST.md`).

## How this history was reconstructed

The chapters were rebuilt from the record, not from memory. Each version's design
state was reconstructed from its release-boundary commit on `main` (there are no
git tags — boundary commits are named per chapter), and every version-to-version
delta was produced by diffing that boundary against the prior across `docs/`,
`vault-template/`, and `src/`, cross-read against that version's own
release/design/exec-plan documents. The *why* was mined from the design docs, the
`why-*.md` essays, ADR Context/Decision sections, full commit-message bodies, and
the 401-paper literature review that drove many bets. **ADRs were reference, never
authority** — the shipped design, the `vault-template`/`src` substrate, and the
researcher's notes are the sources of truth.
