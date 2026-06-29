# The four claim sub-checks in detail

This is the per-check detail for the four non-retraction verification sub-checks. Under
the `<task>-<verb>-<object>` skill registry, **verify-check-citation** handles citation
support, **verify-trace-claim** handles claim traceability, and the two duplicate
detectors are slated for the deterministic sweeps operation
(`sweep:check-similarity` / `sweep:find-duplicates`) — until that operation lands, the
Peer-reviewer may still run them ad hoc from this reference. The retraction sub-check is the
sweeps operation's `sweep:check-retraction`, and the completeness sub-check is a final gate
described in the profile SOUL; neither is covered here.

Each check below may surface issues independently, and a single failure is enough to flag a
card for revision. Across all four, the governing rule is mechanical-first, interpretive
never: you check whether a citekey resolves or a claim traces, not whether the underlying
claim is true.

## 1. Citation check

Every `[@citekey]` in the draft must resolve to a real generated bibliography row and
checked source Concept under `catalog/sources/`.

The token side is purely deterministic: citation extraction is a regex pass over the draft,
and each extracted citekey is looked up against `references.bib` and the corresponding
source Concept. An unresolved citekey — one with no matching bibliography row or checked
source — is a critical finding.

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

Every substantive factual claim in the draft must trace to a supporting checked
claim-bearing note in `knowledge/notes/`. Trace order matters, and it is followed in
this fixed sequence:

1. **Explicit `[[wikilink]]`** to a checked claim-bearing note — a deterministic graph
   walk. If the claim carries a wikilink to such a note, that is the trace; no
   similarity math is needed.
2. **`[@citekey]` mention plus prose embedding similarity** to checked notes derived
   from the cited source — deterministic. When the claim cites a source, candidate
   notes are the ones derived from that source, and the prose is matched against them.
3. **Similarity search across all checked claim-bearing notes** when there is no
   wikilink and no citekey context — deterministic ranking of candidates. An LLM
   verdict is taken on the top candidates only when the similarity score is ambiguous;
   a confident top match needs no LLM.

A claim that traces by any of the three routes is traced. A claim that fails all three is a
failed trace, and each failed trace requests a worker-owned gap attention item with a
backlink to the verification report. Librarian picks these up at the next discovery pass.

Failure modes to watch for: a claim with a wikilink that points at a non-claim-bearing
note (treat as untraced, not traced); and a citekey present but no checked notes derived
from that source yet (fall through to route 3 rather than auto-failing).

## 3. Near-duplicate review

Near-duplicate handling is review-only. The check compares a candidate or checked
claim-bearing note against checked claim-bearing notes through qmd/BM25 retrieval and
simple lexical overlap, then surfaces the top candidates for human review. It is
deterministic and never auto-merges.

A flag carries the candidate, likely neighbours, and field-level provenance. The human
decides whether to merge, supersede, or keep distinct; the check never edits Concepts.

No standalone `similarity-check` command and no QuickAdd pre-file similarity telemetry
ship in alpha.11. Retrospective duplicate sweeps remain planned operation work.

False-positive handling: a high similarity score between two claims that are genuinely
distinct (e.g., same topic, opposite finding) is expected and is exactly why the check is
informational rather than blocking — surface it and let the human judge.

## 4. Duplicate sweep, retrospective (find-duplicates)

A monthly retrospective sweep for near-duplicate claim-bearing notes across the checked
Concept corpus. It collects each note's high-similarity neighbours and groups the
resulting pairs by transitive linkage into candidate clusters, emitted as a ranked list
for human review. It is deterministic and dry-run only: it never merges, deletes, or
edits a note.

The output is written to the monthly report (e.g.
`projects/maintenance/duplicates-<YYYY-MM>.md`); the human-side ritual is the monthly
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
