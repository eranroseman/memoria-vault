---
title: "{{VALUE:title}}"
type: fleeting
lifecycle: proposed
origin: human
created: {{DATE:YYYY-MM-DD}}
---

{{VALUE:body}}

> [!suggestions] Triage options
> - Promote to a claim if this is an idea worth keeping.
> - Attach to an existing source, claim, hub, or project if it is supporting context.
> - Capture or delegate a source chase if this points to a paper, URL, or corpus gap.
> - Archive or delete it once the action is done.

```button
name Promote to claim
type command
action QuickAdd: Memoria: write claim note
```

```button
name Capture source
type command
action QuickAdd: Memoria: capture source from URL
```

```button
name Delegate task
type command
action QuickAdd: Memoria: delegate task
```

```button
name Archive done
type command
action QuickAdd: Memoria: archive fleeting note
```
