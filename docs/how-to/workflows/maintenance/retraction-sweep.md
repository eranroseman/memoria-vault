---
topic: workflows
---

# Retraction sweep

**Group.** Maintenance
**Goal.** Make sure retracted or superseded sources stop influencing synthesis.

The [workflows/README.md](../README.md) names a periodic retraction sweep; this is it. It is the maintenance counterpart to the in-draft retraction check the Verifier runs during [verify](../downstream/verify.md).

## Steps

1. The **Verifier** periodically re-checks `pub_status` for paper-notes against Zotero / source metadata (a retraction, an expression-of-concern, a deprecation).
2. Any source whose status changed is flagged: its `pub_status` is updated and the [`contradictions`](../../../explanation/dashboards/contradictions.md) / drift surfaces show claims that cite it.
3. The **human** decides per affected claim: soften it, mark the claim `superseded_by` a newer one, or accept with a caveat.

## Owners

The **Verifier** detects and flags status changes (mechanical). The **human** decides what to do with the affected claims (judgment). No claim is rewritten automatically.

## Commands

`hermes -p memoria-verifier run retraction-sweep` (run periodically; the Verifier updates `pub_status` and surfaces affected claims on the contradictions dashboard for human review).

## Related

- Stage: [verify](../downstream/verify.md) — the per-draft retraction check.
- Field: [vault/frontmatter-schema.md](../../../reference/frontmatter-schema.md) — `pub_status`, `superseded_by`.
- Decision: [ADR-22 claim supersession](../../../project/decisions/22-claim-supersession.md).
