---
topic: tutorials
---

# Tutorial: Add a second profile

By the end you will have installed a second lane (Mapper is the usual next one) and exercised it. The graduated-start principle: add a profile when you *feel* the absence of what it does, not before.

> **Status.** See [implementation status](../project/implementation-status.md).

**Prerequisite:** [Tutorial 01](01-set-up-from-zero.md) (Librarian installed) and a corpus worth mapping ([Tutorial 02](02-ingest-and-classify-a-batch.md)).

## Which profile next?

[roadmap/README.md (graduated start)](../project/roadmap/README.md#implementation-paths-graduated-start) sequences them by felt need. **Mapper** is the common second lane — once the corpus is large enough that "what do I already have on X?" is a real question, the Mapper's `scope-project` and `[!brief]` earn their place.

## Steps

1. **Install the profile.** It already ships at `.memoria/profiles/memoria-mapper/`; register it with:

   ```bash
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
