---
title: How to run a retraction sweep
parent: Maintenance
---

# How to run a retraction sweep

This guide shows you how to identify papers in your vault that have been retracted, corrected, or flagged since you ingested them, and update any claim notes that cite them.

## When to run it

Monthly, or whenever you're about to cite a cluster of older papers in a draft. A retracted paper silently corrupting several claim notes is the kind of structural debt that only surfaces embarrassingly late if you don't check.

## Steps

1. **Start a Verifier session:**

   ```bash
   hermes -p memoria-verifier chat -s retraction-sweep
   ```

2. **Run the sweep:**

   ```text
   /retraction-sweep
   ```

   The Verifier checks each paper-note's `pub_status` against Zotero retraction alerts and CrossRef retraction metadata. For any paper whose status has changed, it updates the `pub_status` field and surfaces the affected notes.

3. **Review the findings.** The Verifier writes a report listing:
   - Papers whose `pub_status` changed (e.g., `published` → `retracted`)
   - Claim notes that cite each affected paper

4. **Decide what to do with each affected claim.** For each claim note citing a retracted paper, you have three options:
   - **Soften the claim** — rewrite to hedge: "X was suggested by [author], though the paper was subsequently retracted."
   - **Supersede the claim** — find a cleaner source, write a new claim note with that source, set `superseded_by` on the old one.
   - **Accept with a caveat** — if the specific finding wasn't part of the retraction, note the retraction in the claim body and keep it.

   No claim is rewritten automatically. The judgment is always yours.

5. **Update the `contradictions` dashboard.** After updating claims, check `contradictions.md` — retraction-related updates sometimes surface new tensions between notes.

## Owners

The Verifier detects and flags status changes. You decide what to do with affected claims.

## Related

- [how-to-guides/writing/verify-and-revise.md](../writing/verify-and-revise.md) — the per-draft citation check (different workflow, same Verifier)
- [reference/frontmatter.md](../../reference/frontmatter.md) — `pub_status` values (`published`, `preprint`, `retracted`, `unknown`)
- The failure mode sweeps prevent: [common-pitfalls.md](../../explanation/knowledge/common-pitfalls.md)
- The profile running the sweep: [verifier.md](../../explanation/profiles/verifier.md)
