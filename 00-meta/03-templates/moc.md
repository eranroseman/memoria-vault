# `moc` template

Map of Content — a navigational hub for a topic, domain, or project. Lives in `30-synthesis/03-moc/`. Human-authored.

## Frontmatter

```yaml
---
title: ""
type: moc
scope: topic
lifecycle: current
parent_moc: ""
projects: []
moc: []
schema_version: 1
created:
updated:
---
```

## Body

```md
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
​```dataview
TABLE file.link AS Note, lifecycle
FROM "20-sources/01-papers"
WHERE contains(moc, this.file.link)
SORT file.mtime DESC
​```

## Claims in this MOC
​```dataview
TABLE file.link AS Note, maturity, lifecycle
FROM "30-synthesis/01-claims"
WHERE contains(moc, this.file.link)
SORT file.mtime DESC
​```
```

## Notes

MOCs are curated hubs, not folder dumps. Each MOC should answer three questions:

1. What is this area about? (one-paragraph overview)
2. What belongs here right now? (curated list with brief annotations)
3. What needs review, synthesis, or splitting? (open gaps)

Keep the static sections short — they should be scannable in 30 seconds. Let Dataview queries handle the long tail.
