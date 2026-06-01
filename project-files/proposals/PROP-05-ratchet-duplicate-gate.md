---
topic: proposals
id: PROP-05
title: Ratchet — a qmd similarity gate before filing a synthesis note
status: deferred
created: 2026-05-30
---

# PROP-05: ratchet — a `qmd` similarity gate before filing a synthesis note

## Context

Memoria catches duplicate knowledge **retrospectively**: `find-duplicates` runs on a cadence
and surfaces near-duplicate notes *after* they already exist and have been wikilinked into
other notes — at which point merging them is painful (every inbound link must be repointed).
The most common synthesis failure mode — writing a `claim-note` or `reference-note` that
paraphrases something already in `30-synthesis/` — slips through until the next sweep.

The predecessor (v1.5) design proposed a **ratchet**: a similarity check at the *moment of
creation*. Borrowed from Karpathy's overnight-loop pattern (every addition is gated against
existing state before it's committed), adapted from "revert if loss didn't improve" to
"don't file if it duplicates."

## Decision

**Defer.** Record the ratchet design; do not adopt it now. The gate is useless on an empty or
early vault — it needs (a) a live `qmd` index in the agent retrieval path and (b) a synthesis
corpus large enough that filing a duplicate is a real risk, *and* it can only be tuned (the
similarity threshold, the false-positive rate) against real notes. Revisit when both hold;
when adopted, wire it into the same pre-file moment as the deferred [frozen-evaluator
checklist (PROP-06)](PROP-06-frozen-evaluator-deferred.md).

## Proposed mechanism (for when the trigger fires)

Before a synthesis note (`claim-note`, `reference-note`) is filed into `30-synthesis/`, run a
`qmd` hybrid-search similarity check against existing synthesis notes. If the top match exceeds
a threshold (start at cosine **0.8**, tune), **flag** the note and present the candidate
neighbours to the human, who **confirms / merges / overrides** — never an automatic block or
merge. The gate is owned by the **Linter** (validation discipline) or **Mapper** (it already
surfaces neighbouring notes and better wikilinks); the human decision stays at the review gate.

```bash
# Ratchet: check the proposed note against existing synthesis notes before filing.
qmd search "{proposed note title or claim}" --scope 30-synthesis --top 3
# If top score > 0.8 → present neighbours; human confirms new / merges / overrides.
# Requires a current qmd index; run `qmd index --incremental` if stale.
```

Carry-over caveats: depends on a current `qmd` index (a stale index silently misses recent
notes — the gate must trigger an incremental index or warn when the index is old); expect a
noisy first ~6 months (keyword-near, claim-distinct pairs the human must still read); **no
`--force` bypass** — the human's confirm/merge/override *is* the escape valve.

## Consequences

- Holding the design (rather than building it) avoids friction at the most creative moment
  (capturing a new idea) on a corpus too small to benefit.
- When adopted: catches the duplicate at the point of action, before links accrete — cheap to
  resolve versus an after-the-fact merge — and forces a look at neighbouring notes, which
  routinely surfaces better links (a Mapper concern).
- A clear re-entry trigger (live `qmd` index + a dense synthesis corpus) keeps the idea from
  being silently lost.

## Alternatives considered

**Adopt now.** Rejected: nothing to dedup against on an early vault, and the threshold can't be
tuned without real false-positive data — premature.

**Keep only retrospective `find-duplicates` forever.** Rejected: the two are complementary —
ratchet at creation, sweep for what slipped through — not redundant; the retrospective sweep's
cost (painful post-link merges) is exactly what the deferred ratchet exists to remove.

**Auto-merge above the threshold.** Rejected: similarity is not identity (two JITAI-receptivity
notes can be near-duplicate by keyword, distinct by claim). Merging is a human judgement; the
gate only *surfaces* candidates.

## Related

- **Pairs with:** [PROP-06 — frozen-evaluator checklist (deferred)](PROP-06-frozen-evaluator-deferred.md)
- **Retrospective counterpart:** `find-duplicates` (maintenance cadence)
- **Profiles:** [Linter](../../docs/explanation/profiles/linter.md), [Mapper](../../docs/explanation/profiles/mapper.md)
- **Note types gated:** [claim-note, reference-note](../../docs/reference/note-types.md)
