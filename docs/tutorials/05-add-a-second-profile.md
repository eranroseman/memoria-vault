---
topic: tutorials
---

# Tutorial: Verify and activate a profile

By the end you will have confirmed a profile lane is active and exercised it. All seven profiles are installed by `install.ps1` in Tutorial 01; this tutorial covers confirming the installation, filling in per-profile secrets, and running a first task for each lane.

> **Status.** See [implementation status](../project/implementation-status.md).

**Prerequisite:** [Tutorial 01](01-set-up-from-zero.md) (all seven profiles installed by `install.ps1`) and a corpus worth mapping ([Tutorial 02](02-ingest-and-classify-a-batch.md)).

## Which profile to exercise first?

All seven are already installed. **Mapper** is the natural first profile to exercise after Librarian — once the corpus has 5+ papers, the Mapper's `scope-project` and `[!brief]` comparative-brief start producing real comparisons. See [configuration tiers](../project/roadmap/README.md#implementation-paths-configuration-tiers) for profile activation order.

## Steps

1. **Install the profile.** It already ships at `.memoria/profiles/memoria-mapper/`; register it with:

   ```bash
   # from the repo's vault/ folder (where install.ps1 lives)
   ./install.ps1 -Only memoria-mapper
   ```

   See [operations/profile-install.md](../how-to/operations/profile-install.md).
2. **Fill its secrets.** Copy `.env.EXAMPLE` to `~/.hermes/profiles/memoria-mapper/.env` and fill it.
3. **Confirm it registered:** `hermes profile list` shows `memoria-mapper`.
4. **Exercise it.** `Ctrl/Cmd+P → Memoria: scope this project` (or `Memoria: find related notes` for a quick transient query). The Mapper produces a `corpus-map.md` in `40-workbench/<project>/01-map/`. See [workflows/downstream/assess.md](../how-to/workflows/downstream/assess.md).

## What to check

- The Mapper writes only its declared scope (`40-workbench/*/01-map/`); any write outside it is denied by the policy MCP and surfaces on [audit-log](../explanation/dashboards/audit-log.md).

## Next

- Add lanes as the need appears (Writer for drafting, Verifier for citation tracing). The [profiles/README.md](../explanation/profiles/README.md) is the per-lane reference.
