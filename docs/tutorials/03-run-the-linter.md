---
topic: tutorials
---

# Tutorial: Run the Linter and read its findings

By the end you will have run a lint pass over your sources, read the report, and understood the verdict band (PASS / REVIEW / FAIL) that gates scheduled work.

> **Status.** See [implementation status](../project/implementation-status.md).

**Prerequisite:** [Tutorial 02](02-ingest-and-classify-a-batch.md) complete (a batch of classified sources).

## Steps

1. **Fill the Linter's secrets** (first run only): copy `.env.EXAMPLE` to `~/.hermes/profiles/memoria-linter/.env` and fill it, as you did for the Librarian.
2. **Run a dry-run lint over the sources:**

   ```bash
   hermes -p memoria-linter run lint --target 20-sources/ --dry-run
   ```

   Dry-run is the default — the Linter reports, it does not fix (except the `safe-and-unambiguous` and `authorized-targeted` classes). See [profiles/linter.md](../explanation/profiles/linter.md).
3. **Read the report.** Findings carry a severity (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`) and roll up to a **verdict band**: PASS (only LOW/INFO), REVIEW (any MEDIUM, no HIGH/CRITICAL), FAIL (any HIGH or CRITICAL). The [eight M-detectors](../explanation/profiles/linter.md#the-eight-m-detectors) catch silent-failure modes (broken `extract_path`, dashboard field drift, plugin-config drift, …).
4. **Act on findings.** Most are a per-item human decision; auto-fixable ones the Linter offers to apply within its class gate.

## What to check

- [`drift-watch`](../explanation/dashboards/drift-watch.md) surfaces the structural findings; HIGH/CRITICAL also reach [Daily Health](../explanation/dashboards/daily-health.md).

## Next

- [Tutorial 04 — Promote a claim note](04-promote-a-claim-note.md).
