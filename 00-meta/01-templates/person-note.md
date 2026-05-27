# `person-note` template

For researchers, advisors, collaborators, and other people relevant to the research context. Lives in `20-sources/03-entities/01-people/`.

## Frontmatter

```yaml
---
title: ""
type: person-note
full_name: ""
surname: ""
given_name: ""
affiliation: ""
role: ""
orcid: ""
openalex_id: ""
semantic_scholar_id: ""
email: ""
website: ""
triage_status: partial              # partial | full (matches source-note triage discipline)
relationship_to_research: ""        # advisor-candidate | collaborator | author-to-follow | institutional | funder
relevance_to_projects: []
outreach_status: ""                  # "" | not-contacted | contacted | replied | meeting-scheduled
moc: []
projects: []
schema_version: 1
created:
updated:
---
```

## Body

```md
# Profile
One-paragraph summary of who this person is.

# Why they matter
- Research connection.
- Collaboration connection.
- Why you are tracking them.

# Works and links
- Key papers or repos.
- Related entities.
- Related venues.

# Notes
- Outreach status.
- Follow-up reminders.
- Any uncertainty in identity.
```

## Notes

`outreach_status` is for people you intend to contact — advisor candidates, potential collaborators, paper authors with open questions. Leave blank for entities you only track for research-graph purposes.
