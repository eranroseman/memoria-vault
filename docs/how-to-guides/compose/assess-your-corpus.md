---
title: Assess your corpus
parent: Compose
nav_order: 2
---


# Assess your corpus

Run the Mapper's `scope-project` command to get a corpus map — a structured report of what claim notes and sources you have, where coverage is dense, and where the gaps are. The corpus map is the decision point before framing or drafting.

## Prerequisites

- A project folder scaffolded in `40-workbench/<project-slug>/` with its `README.md` project-note (from [Start a writing project](start-a-writing-project.md))
- The Mapper profile installed
- At least 5 claim notes in `30-synthesis/` (fewer than that and the map is mostly gaps)

## Steps

**1. Confirm the project-note describes the deliverable.**

The Mapper scopes against the project-note (`40-workbench/<project-slug>/README.md`, `type: project-note`) created in the previous step. Before running, make sure its body states the deliverable and target — for example:

```text
Deliverable: journal article / chapter / report / etc.
Audience: who reads it
Length: approx. word count or page count
```

and 2–4 sentences on the research question and any framing constraints (e.g., "needs to foreground equity considerations," "must cover 2020–2025 literature only"). Fill `scope` and `research_question` in the frontmatter to match.

**2. Start a Mapper session and run `scope-project`.**

`Memoria: scope this project` *(deferred — use the ACP pane / terminal today)*. For this card-producing Mapper task, the working path today is the CLI (full syntax in [Hermes CLI](../../reference/hermes-cli.md)):

```bash
hermes -p memoria-mapper chat -s scope-project
# then, in the session:
/scope-project --project <project-slug>
```

The Mapper retrieves all claim notes and reference notes matching the brief, computes cluster density and recency distribution, and identifies adjacent topics with thin coverage.

**3. Read the corpus map.**

The output is written to `40-workbench/<project-slug>/01-map/corpus-map.md`. Open it in Obsidian. Look for:

- **Dense clusters** — areas with multiple claims; safe to draft from
- **Thin clusters** — mentioned but under-evidenced; may need more reading before drafting
- **Gaps** — topics the brief requires but the vault doesn't cover at all

**4. Decide: write now or read more?**

- **Dense enough:** proceed to [frame the project](frame-a-project.md)
- **Gaps that matter:** return to the Compile flow — run [find new sources](../compile/find-new-sources.md) or add specific papers to Zotero

Don't proceed to framing until the gaps are either filled or explicitly accepted as out-of-scope for this deliverable.

## Interpreting the output — and when to reach for `cluster-map` / `gap-report`

`scope-project` is the project-scoped map. Two narrower Mapper commands answer related questions when you don't have a brief yet:

| Command | Question it answers | When to run |
| --- | --- | --- |
| `scope-project` | "For *this* brief, what do I have and what's missing?" | Before framing or drafting a specific deliverable |
| `cluster-map` | "How is my corpus distributed across a topic — dense where, recent where?" | Exploring a topic with no project yet |
| `gap-report` | "What adjacent topics are thin relative to a brief?" | Deciding what to read next |

Whichever you run, read the output by pattern:

- **Dense + recent cluster** — draft from it; the evidence is there and current.
- **Dense + stale cluster** — well-read a while ago; check for newer work before drafting (run [find new sources](../compile/find-new-sources.md)).
- **Thin cluster** — mentioned but under-evidenced; read more before you lean on it.
- **Gap the brief requires** — fill it via the Compile flow, or explicitly scope it out. A gap you neither fill nor acknowledge becomes an unsupported section later.

## Verify

- `40-workbench/<project-slug>/01-map/corpus-map.md` exists and has content
- You've made an explicit "write now / read more" decision — not just noted the map and moved on

## Related

- Previous step: [Start a writing project](start-a-writing-project.md)
- Next step: [Frame a project](frame-a-project.md)
- Find new sources (if gaps need filling): [Find new sources](../compile/find-new-sources.md)
- Conceptual background on the Mapper: [The Mapper](../../explanation/profiles/mapper.md)
