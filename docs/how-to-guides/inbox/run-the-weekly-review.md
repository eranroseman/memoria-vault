---
title: Run the weekly review
parent: Inbox
grand_parent: How-to guides
nav_order: 3
---

# Run the weekly review

Walk the Friday ritual: refresh your steering, sweep the Inbox, inspect new
material, and run the structural checks. Allow up to ~60 minutes; closer to
20–30 once the vault is established and the queues run near-empty — **empty is
success**.

## Prerequisites

- A local workspace available to the `memoria` CLI
- The CLI attention, request, list, and linter commands available

## Steps

**Step 1 — Refresh research priorities (2 min).**

Open `steering.md`. Confirm or update the active questions and reading focus — the Librarian reads this to aim discovery, and it sets the lens for every decision below.

**Step 2 — Sweep the Inbox (10–15 min).**

Run `memoria attention list --workspace . --json` and work the open action items
as one batch: candidates kept or skipped, gaps
turned into discovery tasks or archived, and work prompts dismissed once no
action remains ([Work the action queue](work-the-action-queue.md)). The
weekly review is the backstop that keeps the queue from aging past a week.

**Step 3 — Run the structural checks (5 min).**

Run the vault-local linter and read its JSON report by severity:

```bash
./.memoria/.venv/bin/python -m memoria_vault.runtime.subsystems.integrity.linter.detectors \
  --vault . --json
```

On Windows, replace `./.memoria/.venv/bin/python` with
`.\.memoria\.venv\Scripts\python.exe`.

Fix CRITICAL and HIGH findings now. Record a deliberate deferral for lower
severity debt that should survive the session.

**Step 4 — Review the week's movement (5–10 min).**

List catalog entries and notes, then scan timestamps or recent Git history for
anything that landed and stalled:

```bash
memoria list --workspace . --type work --json
memoria list --workspace . --type note --json
memoria request list --workspace . --json
```

Look for an unchecked Work, a digest request that never ran, or a claim with no
connections.

**Step 5 — Clear unchecked note backlog (10–15 min).**

Use the note-list `check_status` values to find unchecked notes. Accept, edit,
or archive each one. Target: zero unchecked PI notes older than a week.

**Step 6 — Curate settled clusters (5 min).**

Scan checked notes and digests for clusters with several useful links. Curate
the genuinely settled ones into hubs ([Build a hub](../knowledge/build-a-hub.md)).
Don't create hubs just to clear a queue.

**Step 7 — Check structural health (5 min).**

Re-run the detectors after fixes. Address HIGH findings this session; MEDIUM can
wait for a maintenance pass; LOW remains advisory. The exact command and
severity meanings are in [Run the Linter](../operate/run-the-linter.md).

## Verify

- `memoria attention list --workspace . --json` has no open item that needs PI action
- No stale unchecked note backlog remains
- A fresh linter run has no HIGH or CRITICAL finding
- `steering.md` reflects what you actually intend to read next week

## Related

- The Inbox discipline: [Work the action queue](work-the-action-queue.md)
- The detectors behind Maintenance drift watch: [Run the Linter](../operate/run-the-linter.md)
- The dashboard inventory: [Dashboards](../../reference/analysis-and-surfaces/dashboards.md)
