# The four claim sub-checks in detail

This is the per-check detail for the four non-retraction verification sub-checks owned by the
`claim-checks` skill — citation, claim-trace, filing-time duplicate, and the retrospective
duplicate sweep. The retraction sub-check lives in the `retraction-check` skill, and the
completeness sub-check is a final gate described in the profile SOUL; neither is covered here.

Each check below may surface issues independently, and a single failure is enough to flag a
card for revision. Across all four, the governing rule is mechanical-first, interpretive
never: you check whether a citekey resolves or a claim traces, not whether the underlying
claim is true.

## 1. Citation check (cite-check)

Every `[@citekey]` in the draft must resolve to a real paper note in `20-sources/01-papers/`.

The token side is purely deterministic: citation extraction is a regex pass over the draft,
and each extracted citekey is looked up against `.memoria/memoria.bib` and the corresponding
paper note. An unresolved citekey — one with no matching bib entry or no paper note — is a
critical finding.

The claim-source side is the one hybrid step in the whole skill. Matching a claim's prose to
the cited source uses embedding similarity as a pre-filter, then bands the score:

- **Above roughly 0.75** — auto-clean. The claim and the cited source are close enough that
  the match stands with no further judgment.
- **Below roughly 0.4** — auto-fail. The claim and the cited source are far enough apart that
  the citation is treated as not supporting the claim.
- **The middle band (roughly 0.4 to 0.75)** — and only this band — is handed to an LLM judge
  to decide whether the source supports the claim. This is the single deliberately
  non-deterministic surface in the four checks; everything outside the band is fixed by the
  threshold.

The reason the bands are wide and the LLM is confined to the gap is to keep the check
reproducible: the same draft and the same source produce the same verdict on every run except
where the embedding score genuinely lands in the ambiguous gap.

## 2. Claim-trace check

Every substantive factual claim in the draft must trace to a supporting claim note in
`30-synthesis/01-claims/`. Trace order matters, and it is followed in this fixed sequence:

1. **Explicit `[[wikilink]]`** to a claim note — a deterministic graph walk. If the claim
   carries a wikilink to a claim note, that is the trace; no similarity math is needed.
2. **`[@citekey]` mention plus prose embedding similarity** to the cited source's claim notes
   — deterministic. When the claim cites a source, the candidate claim notes are the ones
   derived from that source, and the prose is matched against them by embedding similarity.
3. **Similarity search across all claim notes** when there is no wikilink and no citekey
   context — deterministic ranking of candidates. An LLM verdict is taken on the top
   candidates only when the similarity score is ambiguous; a confident top match needs no
   LLM.

A claim that traces by any of the three routes is traced. A claim that fails all three is a
failed trace, and each failed trace spawns a gap card at
`10-inbox/03-candidates/gap-<slug>.md` (`type: candidate-note`, `source: gap`,
`candidate_status: pending-screen`) with a backlink to the verification report. Librarian
picks these up at the next discovery pass.

Failure modes to watch for: a claim with a wikilink that points at a non-claim note (the
graph walk lands outside `30-synthesis/01-claims/` — treat as untraced, not traced); and a
citekey present but no claim notes derived from that source yet (fall through to route 3
rather than auto-failing).

## 3. Duplicate check, filing-time (similarity-check)

A point-of-action check run when a new claim note is about to be filed. It computes cosine
similarity between the new claim's embedding and the existing claim notes through the **shared
`qmd` vector index** — the same similarity primitive the Librarian uses for the `[!brief]`
neighbours and the Mapper for `find related`, just with the Verifier's own threshold — returns
the top 3 by score, and flags at roughly 0.8. It is **fully deterministic — no LLM call** —
and it never blocks filing.

A flag attaches a `near-duplicate-candidate` marker to the card and surfaces the top matches
as a callout comment. The human decides whether to file, merge, or extend; the check never
auto-merges and never auto-files.

There is a human-invoked variant via the `Memoria: similarity-check this claim` command in
the command palette. That surface returns results in a transient ACP chat **without** writing
an audit entry — useful for an ad-hoc pre-filing duplicate check. The card-time
`similarity-check` is the one that produces the audit-trail entry; the two should not be
confused when reading the audit log.

False-positive handling: a high similarity score between two claims that are genuinely
distinct (e.g., same topic, opposite finding) is expected and is exactly why the check is
informational rather than blocking — surface it and let the human judge.

## 4. Duplicate sweep, retrospective (find-duplicates)

A monthly retrospective sweep for near-duplicate claim notes across the whole index. It is the
**same `qmd` similarity primitive as the filing-time `similarity-check`, swept over every
claim note** instead of one: collect each note's high-similarity neighbours (those above the
dup threshold) and group the resulting pairs by transitive linkage into candidate clusters,
emitted as a ranked list for human review. (No HDBSCAN — true density clustering would need
`scikit-learn`, which this lane doesn't grant, and pairwise near-duplicate detection is the
right tool for dedup regardless.) Like the filing-time check it is **fully deterministic — no
LLM call — and dry-run only**: it never merges, deletes, or edits a claim note.

The output is written to the monthly report (e.g.
`40-workbench/maintenance/duplicates-<YYYY-MM>.md`); the human-side ritual is the monthly
review of those groups. Ranking is by group similarity, so the tightest near-duplicate groups
surface first and the long tail of weak pairs sinks.

False-positive handling: clusters of claims that share boilerplate phrasing but cite
different sources are common; the ranked output is meant to be skimmed, not actioned wholesale
— the human confirms each merge.

## Why these are deterministic by design

All four checks are deterministic except the single bounded cite-check middle band. The
boundary rules — and the project's rationale for avoiding LLM-as-similarity-judge outside that
band — live in the project's computational-methods design notes and are not shipped to the
runtime vault.
