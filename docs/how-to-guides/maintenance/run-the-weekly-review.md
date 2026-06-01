
# How to run the weekly review

Walk through the Friday ritual: clear classification debt, process the discuss queue, promote evergreen claims, and run a lint check. The whole session takes 30–60 minutes once the vault is established.

## Prerequisites

- Obsidian open with the vault
- The `weekly-review.md` dashboard open (navigate to `00-meta/01-dashboards/weekly-review.md`, or open it from the dashboard index)

## Steps

Work through the dashboard top to bottom. Each section surfaces a queue; your job is to empty or consciously defer each one.

**Step 1 — Review research priorities (2 min).**

Open `00-meta/research-directions.md`. Confirm or update the week's active projects and reading focus. This sets the lens for every decision in the steps below.

**Step 2 — Clear unreviewed synthesis (10–15 min).**

The dashboard shows any notes in `30-synthesis/` added since the last review with `lifecycle: proposed`. For each:

- Accept and set `lifecycle: current`, or
- Delete if it's a duplicate or error

These are usually Writer-session drafts or claim notes you started but didn't finalize.

**Step 3 — Process discovery candidates (5–10 min).**

The `10-inbox/` queue surfaces notes flagged as discovery candidates — sources that appeared in the Mapper's `comparative-brief` but aren't in your vault yet. For each:

- Add to Zotero and queue for ingest, or
- Mark `excluded: true` with a reason (out of scope, already have equivalent, etc.)

Don't leave this queue growing unbounded — it becomes invisible background debt.

**Step 4 — Resolve classification debt (10–15 min).**

All notes at `lifecycle: proposed` with a `_proposed_classification` block. For each:

- Run the [classify-a-source](../sources/classify-a-source.md) steps: review, promote, set `lifecycle: current`

Target: zero notes in this queue by end of session. If you can't finish all, accept the residual and note the count.

**Step 5 — Promote evergreen claims (5–10 min).**

Claim notes at `maturity: evergreen` that haven't been promoted to `30-synthesis/02-reference/`. For each qualifying note:

- Move to `30-synthesis/02-reference/`
- Set `lifecycle: current`

For the rule on when a claim qualifies as evergreen, see [frontmatter.md — `maturity` values](../../reference/frontmatter.md#maturity-values-claim-notes-only).

**Step 6 — Review orphan notes (5 min).**

Notes with no inbound or outbound links. For each:

- Add at least one `[[link]]` to a related note, or
- Add the note to a relevant MOC, or
- Archive if genuinely standalone and no longer relevant

**Step 7 — Inspect stale literature (5 min).**

Source notes whose enrichment timestamp is more than 90 days old. For each:

- Run `/obsidian-paper-note --source <citekey>` to refresh enrichment, or
- Archive if the source is no longer active

**Step 8 — Run lint dry-run (1 min + review).**

```bash
hermes -p memoria-linter chat -s lint
# then, in the session:
/lint --dry-run
```

Read the report. Address any CRITICAL or HIGH findings immediately. Defer MEDIUM and LOW if they're cosmetic. Close the session.

## Verify

- Classification debt queue is empty or has a known acceptable residual
- No CRITICAL or HIGH lint findings outstanding
- The `weekly-review.md` dashboard shows all queue sections at zero or explicitly deferred
- A new per-session log file in `00-meta/02-logs/sessions/` (named `YYYY-MM-DD-HHMM.jsonl`) records the date and any decisions made

## Related

- Classify a source: [classify-a-source.md](../sources/classify-a-source.md)
- Run the Linter: [run-the-linter.md](run-the-linter.md)
- Dashboard explanation: [explanation/dashboards/weekly-review.md](../../explanation/dashboards/weekly-review.md)
