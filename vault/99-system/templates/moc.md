---
title: "{{VALUE:moc title}}"
type: moc
scope: topic
lifecycle: current
parent_moc: ""
projects: []
moc: []
schema_version: 1
created: {{DATE:YYYY-MM-DD}}
updated: {{DATE:YYYY-MM-DD}}
---

# Overview
Short description of the area and why it matters.

# Key notes
- [[note-1]] — short annotation.
- [[note-2]] — short annotation.
- [[note-3]] — short annotation.

# Open gaps
- What needs synthesis.
- What is missing.
- What should be split into a child hub.

# Live query

## Papers in this MOC
```dataview
TABLE file.link AS Note, lifecycle
FROM "20-sources/01-papers"
WHERE contains(moc, this.file.link)
SORT file.mtime DESC
```

## Claims in this MOC
```dataview
TABLE file.link AS Note, maturity, lifecycle
FROM "30-synthesis/01-claims"
WHERE contains(moc, this.file.link)
SORT file.mtime DESC
```
