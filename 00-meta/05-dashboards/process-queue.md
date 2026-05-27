# `process-queue.md` — what to think about today

**Location.** `00-meta/05-dashboards/process-queue.md`

**Decision.** Surface every literature note that has been triaged but not yet processed (workflow #14 in [04-workflows.md](../04-workflows.md)). This is the upstream-discipline dashboard: if cards pile up here, your processing rhythm is slipping. The corollary signal — when the list is short, your processing is keeping up with ingest.

**When to open.** During a reading session, when deciding which source to think about next. The single most important dashboard for protecting upstream cognitive discipline.

## Cards awaiting Socratic processing

Sources that are fully triaged but haven't had a Socratic pass yet. The `process` card is open; the operator owes it a conversation.

```dataview
TABLE
  file.link AS Source,
  triage_completed AS "Triaged",
  topic AS Topic,
  methods AS Methods
FROM "20-sources/01-literature"
WHERE triage_status = "full" AND !contains(file.tasks.text, "processed:")
SORT triage_completed ASC
LIMIT 20
```

**How to read this.** The oldest items (top of the list) are the most stale — sources you triaged but never came back to process. Five or fewer rows means the queue is healthy. Ten or more is a signal to schedule a reading session.

**Note on the `contains(file.tasks.text, "processed:")` filter.** The convention is that the Process workflow (workflow #14) appends a `- [x] processed: YYYY-MM-DD` task line to the literature note when the operator closes the `process` card. The dashboard reads that marker to determine whether processing has happened. Until that convention is in place, this query falls back to surfacing all `triage_status: full` notes; the operator filters by recall.

## Stale processing (over two weeks old)

Sources that have been waiting longer than two weeks for a Socratic pass. These deserve special attention — either process them or decide they don't yield a claim and close the card with `outcome: no-claim`.

```dataview
TABLE
  file.link AS Source,
  triage_completed AS "Triaged",
  date(today) - date(triage_completed) AS Age,
  topic AS Topic
FROM "20-sources/01-literature"
WHERE triage_status = "full"
  AND !contains(file.tasks.text, "processed:")
  AND date(triage_completed) < date(today) - dur(14 days)
SORT triage_completed ASC
LIMIT 10
```

Empty result is the goal. If anything appears here, decide: process now, or close with `outcome: no-claim` (and a reason in the source note's body).

## Recent processings (last 14 days)

Confirmation that the processing rhythm is real. Each row is a literature note that produced thinking — and (typically) at least one claim note.

```dataview
TABLE WITHOUT ID
  file.link AS Source,
  filter(file.tasks, (t) => contains(t.text, "processed:"))[0].text AS "Processed"
FROM "20-sources/01-literature"
WHERE triage_status = "full"
  AND contains(file.tasks.text, "processed:")
SORT file.mtime DESC
LIMIT 14
```

## What this dashboard does not do

- **Not a to-do list.** It's a queue surface, not a task tracker. Use the Hermes Kanban itself for the actual `process` cards' state.
- **Not for Socratic conversation transcripts.** Socratic is `read_only_mode` — it produces no artifacts. The processing happens in the operator's head; the claim note (when written) lives in `30-synthesis/01-permanent/`.
- **Not the same as the `reading-pipeline` dashboard.** [`reading-pipeline.md`](reading-pipeline.md) shows papers by triage stage (the upstream-of-process question: "what's still partially triaged?"). This dashboard shows papers post-triage, pre-claim (the processing question).

## Related

- [`04-workflows/14-process.md`](../04-workflows/14-process.md) — the Process workflow this dashboard surfaces.
- [`reading-pipeline.md`](reading-pipeline.md) — upstream of this; shows papers stuck before triage.
- [`weekly-dashboard.md`](weekly-dashboard.md) — operator's Friday ritual; consumes this dashboard's stale-queue numbers as one input among many.
