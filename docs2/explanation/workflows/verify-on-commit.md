# Verify-on-commit

When a Writer commits a draft to `40-workbench/<project>/04-drafts/`, a git post-commit hook fires automatically and creates a `verify` card in the Verifier's lane queue. This is what makes verification automatic rather than something you have to remember to trigger — committing a draft is sufficient.

## What fires it and when

A git post-commit hook at `.git/hooks/post-commit` in the vault repository. The hook calls the Hermes API (port 8642) to create the verify card; it does not invoke the Verifier directly. The hook is registered by the installer (`install.ps1`) during vault setup.

The hook fires only on commits that include files in `40-workbench/*/04-drafts/`. Commits to `00-meta/`, `20-sources/`, or project map folders do not trigger a verify card.

## What happens next

1. The Kanban dispatcher sees the new `verify` card in the Verifier's queue (`status: ready`).
2. Within 60 seconds the Verifier claims the card and runs `cite-check` on the committed draft.
3. The Verifier writes a report to `40-workbench/<project>/05-verification/<chapter>-<date>.md` and attaches a `[!verification]` callout to the draft.
4. The card reaches `status: done` with an `agent_verdict` of `verify-clean`, `verify-needs-revision`, or `verify-needs-attention`.
5. You review the verdict and either address the gaps or proceed to export.

## Why automatic rather than manual

The verify step is easy to skip under deadline pressure. Making it automatic means the cost of skipping is a deliberate override — you'd have to ignore the `[!verification]` callout appearing in the draft — rather than just forgetting. The asymmetry is intentional: the system makes verification the path of least resistance.

## Related

- [how-to-guides/writing/verify-and-revise.md](../../how-to-guides/writing/verify-and-revise.md) — how to read the report and address gaps
- [explanation/profiles/verifier.md](../profiles/verifier.md) — what the Verifier checks and how
