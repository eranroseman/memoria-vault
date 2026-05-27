# `weekly-dashboard.md` — weekly ritual entry point

**Location.** `00-meta/05-dashboards/weekly-dashboard.md`

**Decision.** Open at the start of each weekly session and work top-to-bottom.

## Inbox review queue

Clear unreviewed synthesis before new drafting.

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "10-inbox"
WHERE type = "synthesis-note" AND status = "unreviewed"
SORT file.mtime ASC
```

## Discovery candidates

Include or exclude candidates from the corpus. Requires the candidate frontmatter format from [07-roadmap.md Decision 21](../07-roadmap/decisions/21-shared-candidate-frontmatter.md) — until that decision is adopted and a `candidate-note` template is added, this query returns no results.

```dataview
TABLE file.link AS Candidate, candidate_status, file.mtime AS Modified
FROM "10-inbox/03-candidates"
WHERE candidate_status = "pending"
SORT file.mtime ASC
```

## Triage debt

Promote classification and complete source notes.

```dataview
TABLE file.link AS Note, projects, triage_status, file.mtime AS Modified
FROM "20-sources/01-literature"
WHERE triage_status = "partial"
SORT file.mtime ASC
```

## Wiki promotion backlog

Promote durable notes into stable reference pages. Excludes notes already in `30-synthesis/02-wiki/`.

```dataview
TABLE file.link AS Note, maturity, sources, file.mtime AS Modified
FROM "30-synthesis/01-permanent"
WHERE maturity = "evergreen"
SORT file.mtime ASC
```

## Stale active literature

Refresh neglected papers in active projects, or archive if no longer relevant. Filters out already-archived and superseded notes.

```dataview
TABLE file.link AS Note, file.mtime AS Modified
FROM "20-sources/01-literature"
WHERE file.mtime < date(today) - dur(180 days)
  AND triage_status = "full"
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
FROM "30-synthesis/01-permanent" OR "30-synthesis/02-wiki" OR "30-synthesis/03-moc"
WHERE length(file.inlinks) = 0
  AND type != "moc"
SORT file.mtime ASC
```

## Project assembly

Identify the note set that should feed the current manuscript or chapter. Filters out seedling-maturity notes.

```dataview
TABLE file.link AS Note, maturity, sources
FROM "30-synthesis/01-permanent"
WHERE contains(projects, "phd-dissertation")
  AND maturity != "seedling"
SORT maturity DESC
```

Adjust the `projects` value to match the active project name.
