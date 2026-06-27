---
topic: decisions
id: 39
title: Per-note-type acceptance checklists ("frozen evaluator")
nav_exclude: true
status: accepted
assumes: []
date_proposed: 2026-05-30
date_resolved: 2026-06-19
supersedes: []
superseded_by: []
---

# ADR-39: Per-note-type acceptance checklists ("frozen evaluator")

## What

Explicit, per-note-type acceptance criteria the agent checks before filing — the structural definition of a *good* note of each type. For a claim-note, e.g.: "makes a falsifiable claim, supported by >= 1 citekey, title is the claim itself, under 250 words." By analogy to Karpathy's overnight loop, where the unchanging `train.py` evaluator is the constant every experiment is judged against.

## Why

Quality standards are currently implicit and human-judged. Making them explicit and uniform would catch under-supported or mis-shaped notes before they are filed, and pairs naturally with the ratchet gate ([ADR-38](38-pre-file-similarity-gate.md)), which could use the checklist to decide what to flag.

## Trade-offs

- Typing every claim against criteria adds an extraction step.
- Partial adoption (some claims checked, most not) is worse than none — it makes type-aware checks unreliable.
- "Falsifiable claim" is not machine-checkable, so the "evaluator" is partly a prompt for the human, not a hard guard.

## When this matters

The vault holds **50+ `claim-note`s**, so the criteria can be grounded in real examples rather than guessed.


## Alternatives considered

**Adopt now as a mechanical pre-file gate.** Rejected: premature (criteria ungrounded) and partly unenforceable — mechanical enforcement of soft criteria creates friction; non-enforcement makes the checklist decorative.

**Drop the idea entirely.** Rejected: it is a cheap, high-optionality enhancement once grounded, and it composes with the ratchet. Worth accepting as future direction rather than forgetting.

## Related

- **Tracking issue:** [#372](https://github.com/eranroseman/memoria-vault/issues/372) — implementation readiness lives on the issue.
- **Pairs with:** [ADR-38 — ratchet duplicate gate](38-pre-file-similarity-gate.md)
- **Note type concerned:** [claim-note](../reference/document-types.md)
- **Re-entry trigger:** 50+ claim-notes in `notes/claims/`
