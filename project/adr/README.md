---
topic: decisions
---

# Decisions

Accepted architectural decisions for Memoria. Each file records one choice: what
was decided, why, which alternatives were weighed, and the consequences.

Files are named `NN-title.md` and are **browsable in this directory** — numbered in
acceptance order. To add one, copy [_template.md](_template.md) and take the next
number.

Rules:

- **Only accepted decisions live here.** Proposed or deferred items go in [proposals/](../proposals/).
- **Numbers are permanent.** When a decision is superseded, the old file stays and its `superseded_by` field points to the new one.
- **Retired decisions are removed.** If the question a decision answered no longer applies, delete it — git history is the record.
- **Sequencing is not decided here.** *When* a decision ships lives in the [release plan](../releases/v0.1/release-plan-v0.1.md), which changes independently of these decisions. Link to it rather than restating phase order, so a re-plan does not strand stale dates here.
