---
title: Run a retraction sweep
parent: Operate
grand_parent: How-to guides
nav_order: 2
---

# Run a retraction sweep

Check the papers in your Catalog against retraction registries and act on the hits. The sweep is part of the **sweeps operation** — deterministic, read-only runtime code in `memoria_vault.runtime.subsystems.integrity.retraction.retraction`; flag-don't-fix: it raises Inbox **`alert`** cards and never flips a note.

## When it runs without you

The installer ships a monthly cron wrapper (`retraction-refresh-cron.sh`) that refreshes the local Retraction Watch dataset and sweeps. Run it by hand before citing a cluster of older papers in a draft, or right after hearing of a retraction in your field.

## Steps

**1. Refresh the local dataset** (skippable if the monthly cron just ran):

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.retraction.retraction --refresh
```

Downloads the Retraction Watch CSV to `.memoria/data/retraction_watch.csv`.

**2. Run the sweep.**

```bash
python3 -m memoria_vault.runtime.subsystems.integrity.retraction.retraction --sweep --vault .
```

The sweep scans the Catalog's DOIs against three sources, most authoritative first: the local Retraction Watch index, the live Crossref `update-to` delta, and Open Retractions as a cross-check. Each hit raises one finding-first **`alert`** card in `inbox/`.

**3. Read the alert cards.**

Each card leads with the `finding` — what was retracted, corrected, or flagged.
Open the source Concept and the checked notes that cite it through
`evidence_set`.

**4. Decide per affected claim.** Three honest options:

- **Soften** — rewrite to hedge: "X was suggested by [author], though the paper was subsequently retracted."
- **Supersede** — find a cleaner source, write a new claim on it, set `superseded_by` on the old one and archive it.
- **Accept with a caveat** — if the specific finding wasn't part of the retraction, note the retraction in the claim body and keep it.

No claim is rewritten automatically. The judgment is always yours.

**5. Update the paper entity.**

Set the entity's lifecycle to match the record:

```yaml
lifecycle: retracted
```

Then resolve the alert card (`Cmd/Ctrl-P` → **Memoria: resolve inbox card**).

**6. Check for new tensions.**

A retraction sometimes resolves — or creates — a contradiction. Glance at Knowledge's **Contradictions** view after updating claims.

## Verify

- Every alert card from the sweep is resolved
- Affected paper entities carry `lifecycle: retracted`
- Each citing claim was softened, superseded, or caveated — and a re-run raises no new alerts

## Related

- The pipeline context: [Ingest routing](../../reference/ingest.md)
- Archiving the fallout: [Archive a source](../library/archive-a-source.md)
- Why the operation never flips a note: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)
