# Discuss Queue

Classified papers (`lifecycle: current`) not yet processed via Discuss — the upstream-discipline queue (long = processing is falling behind ingest). Open during a reading session to pick what to think about next. [Discuss workflow](https://eranroseman.github.io/memoria-vault/how-to-guides/sources/discuss-a-paper/) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/discuss-queue/).

## Cards awaiting Socratic processing

Classified sources with no Socratic pass yet. Oldest first; ≤ 5 healthy, ≥ 10 = schedule a reading session.

```dataview
TABLE
  file.link AS Source,
  created AS Created,
  topic AS Topic,
  methods AS Methods
FROM "20-sources/01-papers"
WHERE lifecycle = "current" AND !contains(file.tasks.text, "processed:")
SORT created ASC
LIMIT 20
```

> The `processed:` filter reads a `- [x] processed: YYYY-MM-DD` task line the Discuss workflow appends when a `discuss` card closes; until that convention is wired, the query surfaces all `lifecycle: current` notes.

## Stale processing (over two weeks old)

Sources that have been waiting longer than two weeks for a Socratic pass. These deserve special attention — either process them or decide they don't yield a claim and close the card with `outcome: no-claim`.

```dataview
TABLE
  file.link AS Source,
  created AS Created,
  date(today) - date(created) AS Age,
  topic AS Topic
FROM "20-sources/01-papers"
WHERE lifecycle = "current"
  AND !contains(file.tasks.text, "processed:")
  AND date(created) < date(today) - dur(14 days)
SORT created ASC
LIMIT 10
```

Empty result is the goal. If anything appears here, decide: process now, or close with `outcome: no-claim` (and a reason in the paper note's body).

## Recent processings (last 14 days)

Confirmation that the processing rhythm is real. Each row is a paper note that produced thinking — and (typically) at least one claim note.

```dataview
TABLE WITHOUT ID
  file.link AS Source,
  filter(file.tasks, (t) => contains(t.text, "processed:"))[0].text AS "Processed"
FROM "20-sources/01-papers"
WHERE lifecycle = "current"
  AND contains(file.tasks.text, "processed:")
SORT file.mtime DESC
LIMIT 14
```

## Related

- [[reading-pipeline|Reading Pipeline]] — upstream: papers still being classified (`lifecycle: proposed`).
- [[weekly-review|Weekly Review]] — consumes this queue's depth as one input.
