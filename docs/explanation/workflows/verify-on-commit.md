---
title: Verify-on-commit
parent: Workflows
---

# Verify-on-commit

Committing a draft to `40-workbench/<project>/04-drafts/` automatically creates a verification card in the Verifier's lane. This document explains why the trigger is automatic rather than manual, and what the design is trying to prevent.

## Why automation is the right fit here

The verify step occupies an awkward position in the writing workflow: it is important enough to be non-negotiable in principle, but easily deferred under deadline pressure. A manual trigger depends on the human remembering to invoke it — the exact behavior that erodes under time pressure. An automatic trigger converts the decision from "should I verify this?" to "should I skip this verification?" The latter requires a deliberate act, not just forgetfulness.

The asymmetry is the point. The `[!verification]` callout appears in the draft automatically after a commit; it cannot be invisibly bypassed. Ignoring it requires reading past a visible signal. Skipping a manual step requires nothing.

## Why the trigger is a git hook, not a cron job

The trigger fires on `post-commit` to `40-workbench/*/04-drafts/`, not on a schedule. A cron-based verification would verify drafts based on time, not on change — it might re-verify unchanged drafts and miss recently changed ones. The commit is the natural unit of change in the writing workflow; triggering on the commit ensures verification tracks actual edits.

The hook calls the Hermes API to create the verify card — it does not invoke the Verifier directly. This keeps the trigger thin: it creates a card and returns. The Verifier claims the card through the normal dispatch mechanism, which means verification is audited, retryable, and visible in the board like any other task. A direct invocation from a hook would bypass all of that.

**Draft commits are deliberate, not timed.** This change-based triggering only holds if commits track edits rather than the clock. obsidian-git's `autoSaveInterval` (a ~30-minute scheduled commit; see [Obsidian plugins](../../reference/obsidian-plugins.md)) is configured as an offsite-backup safety net for the vault at large — it is **not** the verify trigger for drafts. Committing a draft you want verified is a deliberate act (`Cmd-P → Obsidian Git: Commit`), so "I committed this draft" means "verify it," and the `[!verification]` callout appears on that commit rather than on the next timer tick. If you rely on the auto-save timer for draft commits instead, verification still fires — but batched to the timer, up to ~30 minutes after your last edit, which dilutes the immediate feedback the workflow is designed around.

## What the automatic trigger is not

The automatic card creation is not automatic verification completion. The card enters the Verifier's queue; the Verifier processes it within its normal dispatch window. The result is a recommendation (`verify-clean`, `verify-needs-revision`, `verify-needs-attention`), not an automatic gate. The human still reviews the verification report and decides whether to address gaps or proceed to export.

This is consistent with the rest of the system's posture: agents produce recommendations; humans make decisions. The automation eliminates the "forget to trigger verification" failure mode without removing the "read and decide on the findings" step.

## Related

- [The Verifier](../profiles/verifier.md) — what the Verifier checks and how
- [How to verify and revise a draft](../../how-to-guides/writing/verify-and-revise.md) — how to read the report and address gaps
