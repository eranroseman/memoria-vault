---
topic: workflows
---

# Revise

**Group.** Downstream (stage workflow)
**Goal.** Close the gap-loop: address verification findings (from [Verify](verify.md)) before export.

## Pipeline position

Between [Verify](verify.md) and [Export](export.md).

## Steps

1. The `revise` card opens with the verification report attached.
2. Human reads the per-claim findings. For each failed trace, three options:
   - **Soften the claim** — rewrite the sentence so it makes a more cautious assertion. Recommended when the gap is real but the chapter's argument doesn't depend on this claim.
   - **Pursue the gap** — mark the corresponding `gap:` card with reading priority, push the chapter back to the next revision cycle, and read the missing source. Recommended when the claim is load-bearing.
   - **Accept the soft claim** — leave the sentence; tag the chapter with a known-soft-claim list in the project's `notes.md`. Recommended when the gap exists in the literature itself (the claim has been established as contested, not unsupported).
3. After revisions, the human re-commits, which fires [Verify](verify.md) again. Loop continues until verify returns clean (or the human explicitly marks remaining gaps as accepted-soft).
4. Once verify is clean (or all remaining gaps are accepted-soft), the `revise` card closes and the project card moves to `export`.

## Owners

Human only. This is not a workflow Hermes can execute — gap-loop decisions are human judgment about which gaps matter for which argument.

## Card lifecycle

Inherited from [Verify](verify.md) — the `verify` card lands in one of `verify-needs-revision` or `verify-needs-attention` and becomes human-owned. Each human revision commit re-fires [Verify](verify.md), which produces a new verification report; the same card iterates until verify returns clean (or human marks remaining gaps as accepted-soft and manually sets `review_status: approved`). [Export](export.md) cannot run while a verify card sits in a non-clean state.

## Command

No CLI command; revisions happen in the editor. The git post-commit hook re-fires [Verify](verify.md).

## Why revise is a stage instead of "just keep editing"

Drafts get revised continuously and informally already. The stage isn't about *whether* revision happens — it's about whether the verify→revise loop has *closed* before export. Without the stage, "I exported a draft with three unaddressed verification findings" is a real failure mode the human commits silently. With the stage, export is blocked on revise's closure.

## Related

- **Previous workflow:** [Verify](verify.md)
- **Next workflow:** [Export](export.md)
