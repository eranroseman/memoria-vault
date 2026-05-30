# `weekly-review.md` — weekly ritual entry point

**Location.** `00-meta/01-dashboards/weekly-review.md`

**Decision.** Open at the start of each weekly session and work top-to-bottom.

## Inbox review queue

Clear unreviewed synthesis before new drafting.

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "10-inbox"
WHERE type = "answer-note" AND lifecycle = "proposed"
SORT file.mtime ASC
```

## Discovery candidates

Include or exclude candidates from the corpus. Requires the candidate frontmatter format from ADR-21 — until that decision is adopted and a `candidate-note` template is added, this query returns no results.

```dataview
TABLE file.link AS Candidate, candidate_status, file.mtime AS Modified
FROM "10-inbox/03-candidates"
WHERE candidate_status = "pending"
SORT file.mtime ASC
```

## Classification debt

Promote classification and complete paper notes.

```dataview
TABLE file.link AS Note, projects, lifecycle, file.mtime AS Modified
FROM "20-sources/01-papers"
WHERE lifecycle = "proposed"
SORT file.mtime ASC
```

## Reference promotion backlog

Promote durable notes into stable reference pages. Excludes notes already in `30-synthesis/02-reference/`.

```dataview
TABLE file.link AS Note, maturity, sources, file.mtime AS Modified
FROM "30-synthesis/01-claims"
WHERE maturity = "evergreen"
SORT file.mtime ASC
```

## Stale active literature

Refresh neglected papers in active projects, or archive if no longer relevant. Filters out already-archived and superseded notes.

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "20-sources/01-papers"
WHERE file.mtime < date(today) - dur(180 days)
  AND lifecycle = "current"
  AND pub_status = "active"
SORT file.mtime ASC
```

## Stale items

Revisit tool and repo notes that may have drifted. Filters out archived items.

```dataview
TABLE file.link AS Item, file.mtime AS Modified
FROM "20-sources/02-items"
WHERE file.mtime < date(today) - dur(90 days)
  AND !contains(file.path, "/archive/")
SORT file.mtime ASC
```

## Orphan notes

Link, file under a MOC, or archive notes that are not integrated. Excludes MOC notes (which legitimately have no inlinks at the top of the hierarchy).

```dataview
TABLE file.link AS Note, file.mtime AS Modified, maturity
FROM "30-synthesis/01-claims" OR "30-synthesis/02-reference" OR "30-synthesis/03-moc"
WHERE length(file.inlinks) = 0
  AND type != "moc"
SORT file.mtime ASC
```

## Project assembly

Identify the note set that should feed the current manuscript or chapter. Filters out seedling-maturity notes.

```dataview
TABLE file.link AS Note, maturity, sources
FROM "30-synthesis/01-claims"
WHERE contains(projects, "phd-dissertation")
  AND maturity != "seedling"
SORT maturity DESC
```

Adjust the `projects` value to match the active project name.
