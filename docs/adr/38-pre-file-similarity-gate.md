---
topic: decisions
id: 38
title: Ratchet — a qmd similarity gate before filing a synthesis note
status: superseded
folded_into: memoria-design-update  # near-tie/dedup residue (R2) + Fact-checker similarity-check
assumes: []
date_proposed: 2026-05-30
parent: Decisions
grand_parent: Explanation
nav_order: 38
---

# ADR-38: Ratchet — a qmd similarity gate before filing a synthesis note

## What

A similarity check at the *moment a synthesis note is created*: before a `claim-note` or `reference-note` is filed into `30-synthesis/`, run a `qmd` hybrid search against existing synthesis notes and, if the top match exceeds a threshold, flag the note and present the neighbours to the human to confirm / merge / override. Borrowed from Karpathy's overnight-loop pattern (gate every addition against existing state), adapted from "revert if loss didn't improve" to "don't file if it duplicates."

## Why

Memoria catches duplicates **retrospectively**: `find-duplicates` runs on a cadence and surfaces near-duplicates *after* they exist and have been wikilinked, at which point merging is painful (every inbound link must be repointed). The most common synthesis failure — paraphrasing something already in `30-synthesis/` — slips through until the next sweep.

## Trade-offs

- Depends on a current `qmd` index; a stale index silently misses recent notes, so the gate must trigger an incremental index or warn when the index is old.
- Expect a noisy first ~6 months: keyword-near, claim-distinct pairs the human must still read.
- No `--force` bypass — the human's confirm/merge/override *is* the escape valve.

## When this matters

Both hold: (a) a live `qmd` index in the agent retrieval path, and (b) a synthesis corpus dense enough that filing a duplicate is a real risk — the point at which the similarity threshold and false-positive rate can be tuned against real notes.

## Proposed mechanism (for when the trigger fires)

Before filing, run a `qmd` similarity check against existing synthesis notes. If the top match exceeds a threshold (start at cosine **0.8**, tune), flag the note and present the candidate neighbours; the human confirms new / merges / overrides — never an automatic block or merge. The gate is owned by the **Linter** (validation discipline) or **Mapper** (it already surfaces neighbouring notes); the decision stays at the human review gate.

```bash
# Ratchet: check the proposed note against existing synthesis notes before filing.
qmd search "{proposed note title or claim}" --scope 30-synthesis --top 3
# If top score > 0.8 -> present neighbours; human confirms new / merges / overrides.
# Requires a current qmd index; run `qmd index --incremental` if stale.
```

## Alternatives considered

**Adopt now.** Rejected: nothing to dedup against on an early vault, and the threshold can't be tuned without real false-positive data.

**Keep only retrospective `find-duplicates` forever.** Rejected: the two are complementary (ratchet at creation, sweep for what slipped through), not redundant; the sweep's painful post-link merges are exactly what the deferred ratchet removes.

**Auto-merge above the threshold.** Rejected: similarity is not identity (two JITAI-receptivity notes can be near-duplicate by keyword, distinct by claim). Merging is a human judgement; the gate only *surfaces* candidates.

## Related

- **Pairs with:** [ADR-39 — note-acceptance checklists (deferred)](39-note-acceptance-checklists.md)
- **Retrospective counterpart:** `find-duplicates` (maintenance cadence)
- **Profiles:** [Linter](../explanation/engines/README.md), [Mapper](../explanation/profiles/librarian.md)
- **Note types gated:** [claim-note, reference-note](../reference/note-types.md)
