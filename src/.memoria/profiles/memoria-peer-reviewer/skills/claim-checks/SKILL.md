---
name: claim-checks
description: "Run the four non-retraction verification sub-checks for a draft or claim note — cite-check (every citekey resolves to a paper note), claim-trace (every substantive claim traces to a claim note), and the two duplicate detectors (similarity-check at filing time, find-duplicates as a retrospective sweep). Mostly deterministic, with one hybrid embedding+LLM-judge step for the ambiguous cite-check middle band. Use before export (cite-check), before a new claim note is filed (similarity-check), when tracing a draft (claim-trace), or for the monthly duplicate retrospective (find-duplicates)."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Verification, Citations, Deduplication, Claims]
    related_skills: [qmd, pyzotero, obsidian]
---

# claim-checks

Run the four deterministic/hybrid verification sub-checks that sit alongside the retraction
sweep. Each check answers a mechanical question — does this citekey resolve? does this claim
trace? is this claim a near-duplicate? — and **reports** the answer. You contribute no
judgment about whether a claim is *true* or whether a gap is acceptable; that is the human's
call. **Every check is flag-only and never auto-fixes** the draft or the claim note.

The fifth sub-check (retraction) is the `retraction-check` skill; completeness is a final
gate handled in `SOUL.md`. This skill owns the other four.

## When to Use

- **Before export** — run `cite-check` so every `[@citekey]` in a draft resolves to a real
  paper note before the draft leaves the workbench.
- **Before a new claim note is filed** — run `similarity-check` at the point of filing to
  surface near-duplicates so the human can file, merge, or extend.
- **When tracing a draft** — run `claim-trace` to confirm each substantive claim has a
  supporting note in `notes/claims/`; failed traces spawn gap cards.
- **Monthly** — run `find-duplicates` as a retrospective near-duplicate sweep across the
  whole claim-note index (dry-run, ranked clusters for human review).

## Quick Reference

| Check | Method (one line) |
|-------|-------------------|
| `cite-check` | Regex-extract every `[@citekey]`; resolve against `.memoria/memoria.bib` + paper notes. Claim-source match uses embedding similarity as a pre-filter: **auto-clean above ~0.75, auto-fail below ~0.4, LLM-judge the middle band**. |
| `claim-trace` | Trace each substantive claim by (a) explicit `[[wikilink]]`, (b) `[@citekey]` + prose embedding match, then (c) similarity search — deterministic ranking, LLM verdict only on ambiguous top candidates. |
| `similarity-check` | Cosine similarity against the **shared `qmd` vector index** (the same primitive the Librarian's `[!brief]` and Mapper's `find related` use — one mechanism, per-lane threshold). Top 3 by score; **flags at ~0.8**; never blocks. Fully deterministic — no LLM. |
| `find-duplicates` | The same `qmd` similarity, swept over **all** claim notes: high-similarity pairs (above the dup threshold) grouped by transitive linkage into ranked candidate clusters. No HDBSCAN (lane has no `scikit-learn`; pairwise is the right tool for dedup). Fully deterministic — no LLM, dry-run only. |

Detailed procedures, trace order, thresholds, failure modes, and false-positive handling are
in `references/sub-checks.md`.

cite-check and similarity-check run **locally** — citekeys resolve against `.memoria/memoria.bib`
and the paper notes; similarity uses the `qmd` embedding index. When claim-trace needs external
citation context (a cited source's references or citing papers), it comes from the `pyzotero`
MCP's Semantic Scholar tools (`get_references`, `get_citations`, `find_related`) — **not** direct
HTTP; `code_execution`/`terminal` stay disabled.

## Procedure

Run each check deterministic-first; reach for the LLM only on the single ambiguous band.

1. **cite-check.** Regex-extract every citation token (deterministic). Resolve each citekey
   against the bib and paper notes; an unresolved citekey is a critical finding. For
   claim-source matching, use embedding similarity as a pre-filter: above ~0.75 auto-clean,
   below ~0.4 auto-fail, and **only** the middle band goes to an LLM judge.
2. **claim-trace.** For each substantive claim, walk the trace order: explicit `[[wikilink]]`
   first (deterministic graph walk), then `[@citekey]` + prose embedding similarity to the
   cited source's claim notes (deterministic), then a similarity search across all claim notes
   when there's no citekey context (deterministic ranking; an LLM verdict on the top
   candidates only when similarity is ambiguous). A failed trace spawns a gap card.
3. **similarity-check.** At filing time, embed the new claim and compare against the
   claim-note index. Surface the top 3; flag at ~0.8 as a `near-duplicate-candidate`.
   Informational only — never blocks, never auto-merges.
4. **find-duplicates.** Cluster the claim-note index, emit a ranked list of candidate
   clusters to the monthly report for human review. Dry-run only.

## Verification

- **Deterministic** — the same inputs yield identical output on every run (same draft + same
  bib + same embedding index → same findings). The only non-deterministic surface is the
  cite-check middle-band LLM judge, bounded to the ~0.4–0.75 ambiguity gap.
- **Flag-only** — these checks never auto-fix the draft or the claim note. cite-check and
  claim-trace produce findings and gap cards; similarity-check and find-duplicates are
  informational. No check edits the thing it inspects.
