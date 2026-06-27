---
title: Verify-on-commit
parent: Workflows
grand_parent: Explanation
nav_order: 4
---

# Verify-on-commit

Committing a draft to `projects/<project>/` automatically creates a verification card in the Peer-reviewer's verify lane. This document explains why the trigger is automatic rather than manual, and what the design is trying to prevent.

## Why automation is the right fit here

The verify step occupies an awkward position in the writing workflow: it is important enough to be non-negotiable in principle, but easily deferred under deadline pressure. A manual trigger depends on the human remembering to invoke it — the exact behavior that erodes under time pressure. An automatic trigger converts the decision from "should I verify this?" to "should I skip this verification?" The latter requires a deliberate act, not just forgetfulness.

The asymmetry is the point. The post-commit hook cannot be invisibly bypassed once the vault hooks are wired: a committed project draft creates a visible verify-lane card. Ignoring it requires leaving an auditable card in the queue. Skipping a manual step requires nothing.

## Why the trigger is a git hook, not a cron job

The trigger fires on `post-commit` to `projects/*/`, not on a schedule. A cron-based verification would verify drafts based on time, not on change — it might re-verify unchanged drafts and miss recently changed ones. The commit is the natural unit of change in the writing workflow; triggering on the commit ensures verification tracks actual edits.

The hook calls `hermes kanban create` to create the verify card — it does not invoke the Peer-reviewer directly. This keeps the trigger thin: it creates a card and returns. The Peer-reviewer claims the card through the normal dispatch mechanism, which means verification is audited, retryable, and visible in the board like any other task. A direct invocation from a hook would bypass all of that.

**Draft commits are deliberate, not timed.** This change-based triggering only holds if commits track edits rather than the clock. obsidian-git's `autoSaveInterval` (a ~30-minute scheduled commit; see [Obsidian plugins](../../reference/obsidian-plugins.md)) is configured as an offsite-backup safety net for the vault at large — it is **not** the verify trigger for drafts. Committing a draft you want verified is a deliberate act (`Cmd-P → Obsidian Git: Commit`), so "I committed this draft" means "verify it," and the verify card appears from that commit rather than on the next timer tick. If you rely on the auto-save timer for draft commits instead, verification still fires — but batched to the timer, up to ~30 minutes after your last edit, which dilutes the immediate feedback the workflow is designed around.

## What the automatic trigger is not

The automatic card creation is not automatic verification completion. The card enters the Peer-reviewer's queue; the Peer-reviewer processes it within its normal dispatch window. The result is an `agent_recommendation` — a soft signal, never an automatic gate (the enum and that constraint are owned by [The Peer-reviewer](../profiles/peer-reviewer.md)). The human still reviews the verification report and decides whether to address gaps or proceed to export.

This is consistent with the rest of the system's posture: agents produce recommendations; humans make decisions. The automation eliminates the "forget to trigger verification" failure mode without removing the "read and decide on the findings" step.

## Related

- [The Peer-reviewer](../profiles/peer-reviewer.md) — what the Peer-reviewer checks and how
- [Verify and revise a draft](../../how-to-guides/project/verify-and-revise.md) — how to read the report and address gaps
