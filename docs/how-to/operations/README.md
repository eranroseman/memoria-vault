---
topic: operations
---

# Operations

Operational concerns: what to do when things go wrong, and how to keep the running system healthy. The design documents say what Memoria *is*; this folder says what to *do* when reality diverges from design.

## What lives here

- [failure-modes.md](failure-modes.md) — Detect / Fix / Verify recipes for the common breakages: a stale `library.bib`, a missing `_proposed_classification`, broken frontmatter, a stale `qmd` search index, profile install drift, plus a dozen more in the catalog table. Open this when something looks wrong but the cause isn't clear.
- [session-logging.md](../../explanation/operations/session-logging.md) — how the per-session activity record is written and preserved. A system *mechanism*, not a workflow.
- [profile-install.md](profile-install.md) — installing and redeploying the seven Hermes profiles with `install.ps1`; the procedure the failure-mode fixes assume.

## What lives elsewhere

- **Plugin configuration** — [obsidian-plugins/](../../reference/plugins/) (per-plugin configs, lifecycle, visual style). Operationally adjacent but its own folder because of size (20+ files).
- **Deployment and secret management** — [roadmap/deployment-options.md](../../project/roadmap/deployment-options.md), [roadmap/secret-management.md](../../project/roadmap/secret-management.md). These are about *setup* rather than runtime recovery.
- **Safe-mode procedures** — `00-meta/04-reference/safe-mode.md` in the starter vault. The vault-resident counterpart of `failure-modes.md` for when Hermes, the ACP connection, or the watcher is down. See [vault/README.md vault skeleton](../../explanation/vault/README.md#vault-skeleton-human-facing-notes).
- **Audit and observability** — [dashboards/audit-log.md](../../explanation/dashboards/audit-log.md), [dashboards/fleet-health.md](../../explanation/dashboards/fleet-health.md). Dashboards show the signal; operations recipes act on it.

## Operating principles

- **Recipes follow Detect / Fix / Verify shape.** Every failure-mode entry names a symptom (what's observed), a fix (the smallest thing that resolves it), and a verification (how to confirm the fix held). Skipping verify is the most common cause of "I thought I fixed it last week."
- **Prefer reversible actions.** Schema migrations are dry-run first. Auto-fixes for canonical content are denied by policy, not by convention. Operations recipes never instruct the human to run a destructive command without a dry-run path.
- **The board is the operational dashboard.** Stuck cards, retry exhaustion, and review-queue depth are all visible on [board-state](../../explanation/dashboards/board-state.md) and [discuss-queue](../../explanation/dashboards/discuss-queue.md). Most operational diagnosis starts there.
