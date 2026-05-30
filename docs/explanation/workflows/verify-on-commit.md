---
topic: workflows
status: stub
implementation: planned-v0.2
---

# verify-on-commit hook

**Status: planned — stub only. Full implementation in v0.2.**

## What it does

When a Writer commits a draft to `40-workbench/<project>/04-drafts/`, a git post-commit hook fires automatically. The hook creates a `verify` card in the Kanban board, placing it in the Verifier's lane queue in `ready` state. This is the entry point to the [Verify](../../how-to/workflows/downstream/verify.md) workflow.

The hook is what makes verification automatic rather than something the human has to remember to trigger. Without it, the Writer would have to manually create the verify card or invoke `cite-check` directly; with it, committing a draft is sufficient.

## Which component fires it

A **git post-commit hook** (`.git/hooks/post-commit`) in the vault repository. The hook shell script calls the Hermes API (`hermes gateway`, port `8642`) to create the card — it does not invoke Verifier directly.

The hook is registered by `install.ps1` during vault setup. It has no effect outside a review-gated zone commit: commits to `00-meta/`, `20-sources/`, or `40-workbench/*/01-map/` do not trigger a verify card.

## What happens next

1. The Kanban dispatcher sees the new `verify` card in Verifier's queue.
2. Verifier claims the card and runs `cite-check` on the committed draft (within 60 seconds of commit under normal load).
3. Verifier writes results to `40-workbench/<project>/05-verification/<chapter>-<date>.md` and attaches a `[!verification]` callout to the draft.
4. The `verify` card completes to `done` with an `agent_verdict` (`verify-clean`, `verify-needs-revision`, or `verify-needs-attention`).
5. The human reviews the verdict and advances the card to [Revise](../../how-to/workflows/downstream/revise.md) or export.

The full card lifecycle is documented in [Verify](../../how-to/workflows/downstream/verify.md#card-lifecycle).

## Related

- [Verify workflow](../../how-to/workflows/downstream/verify.md) — what Verifier does once it claims the card
- [profiles/verifier.md](../profiles/verifier.md) — Verifier profile contract
- [profiles/README.md](../profiles/README.md#routing-without-an-orchestrator) — context where this hook is mentioned in the routing description
