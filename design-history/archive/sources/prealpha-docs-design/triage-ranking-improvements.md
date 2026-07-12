---
topic: explorations
title: Triage improvements
status: resolved-by-redesign  # Inbox (D6) + homepage "what needs me"
created: 2026-05-31
parent: Design notes
grand_parent: Explanation
nav_order: 26
nav_exclude: true
---

# Triage improvements

Capabilities that reduce the human's per-candidate judgment cost without moving the autonomy boundary.

---

## 1. Semi-autonomous triage

**What.** The classifier that generates `_proposed_classification` already produces a confidence score. When confidence is above a threshold (e.g., > 0.92), batch the proposals into a single "approve these classifications?" card rather than requiring individual review of each. High-confidence promotions become one human action. Low-confidence proposals remain individual reviews.

**Trade-offs.** The confidence threshold must be calibrated against the human's actual error rate — a too-permissive threshold promotes wrong classifications silently. The batch card must surface the full list in a readable format, not bury it.

**Adoption trigger.** Classification backlog exceeds a week's review capacity *and* the classifier has been running for ≥ 2 months with a measured accuracy baseline.

**Guard.** Do not apply to new note types the classifier hasn't been trained on. Semi-auto triage applies only to the classification dimensions where calibrated confidence exists.

---

## 2. Agent-consensus pre-filter

**What.** Before a candidate card reaches the human review queue, a second independent profile pass reviews the output. Cards where both profiles agree get a `consensus: true` flag; cards where they disagree get `consensus: false`. The human processes disagreement cards first. Does not bypass the review gate — the gate is still structural; the pre-filter routes what reaches it.

**Trade-offs.** Adds latency and cost per card. Two profiles with correlated errors (Bisht et al. 2026's hivemind finding) can agree and be confidently wrong together — the pre-filter has diminishing value on failure modes where both profiles use similar models.

**Adoption trigger.** Review queue depth consistently exceeds 2 weeks' backlog *and* a spot-check shows that agreed cards are approved at > 90% rate by the human.

**Guard.** If the two profiles share the same underlying model or similar training, the correlated-error risk is real. Use models from different providers or fine-tuning regimes.

---

## 3. Tournament ranking for triage

**What.** When the discovery inbox is large (> 50 candidates), rank candidates by pairwise comparison — each pair evaluated by the LLM against `research-focus.md` — to surface the top-N most relevant candidates first. The human reviews in ranked order; lower-ranked candidates can be deferred.

**Trade-offs.** Pairwise comparison costs scale quadratically with queue size. Ranking is personalized only if `research-focus.md` is current.

**Adoption trigger.** Inbox regularly exceeds 50 candidates *and* the learning-to-rank model (see `classical-methods-over-llm.md §Learning-to-rank`) is not yet trained (this is the expensive cold-start alternative).

**Guard.** The tournament is a cold-start fallback. Once learning-to-rank has enough training data, switch to that — it is cheaper, faster, and personalized.
