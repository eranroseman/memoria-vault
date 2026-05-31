
# How to assess your corpus for a project

Run the Mapper's `scope-project` command to get a corpus map — a structured report of what claim notes and sources you have, where coverage is dense, and where the gaps are. The corpus map is the decision point before framing or drafting.

## Prerequisites

- A project folder scaffolded in `40-workbench/<project-slug>/` with a `brief.md`
- The Mapper profile installed
- At least 5 claim notes in `30-synthesis/` (fewer than that and the map is mostly gaps)

## Steps

**1. Write `brief.md` in the project folder.**

Create `40-workbench/<project-slug>/brief.md` with:

```yaml
---
type: project-brief
project: <project-slug>
deliverable: "journal article / chapter / report / etc."
audience: "who reads it"
length: "approx. word count or page count"
---
```

In the body, write 2–4 sentences describing the research question and any framing constraints (e.g., "needs to foreground equity considerations," "must cover 2020–2025 literature only").

**2. Start a Mapper session and run `scope-project`.**

```bash
hermes -p memoria-mapper chat -s scope-project
# then, in the session:
/scope-project --project <project-slug>
```

The Mapper retrieves all claim notes and reference notes matching the brief, computes cluster density and recency distribution, and identifies adjacent topics with thin coverage.

**3. Read the corpus map.**

The output is written to `40-workbench/<project-slug>/01-corpus-map/corpus-map.md`. Open it in Obsidian. Look for:

- **Dense clusters** — areas with multiple claims; safe to draft from
- **Thin clusters** — mentioned but under-evidenced; may need more reading before drafting
- **Gaps** — topics the brief requires but the vault doesn't cover at all

**4. Decide: write now or read more?**

- **Dense enough:** proceed to [frame the project](frame-a-project.md)
- **Gaps that matter:** return to the upstream pipeline — run [find new sources](../sources/find-new-sources.md) or add specific papers to Zotero

Don't proceed to framing until the gaps are either filled or explicitly accepted as out-of-scope for this deliverable.

## Verify

- `40-workbench/<project-slug>/01-corpus-map/corpus-map.md` exists and has content
- You've made an explicit "write now / read more" decision — not just noted the map and moved on

## Related

- Previous step: [Start a writing project](start-a-writing-project.md)
- Next step: [Frame a project](frame-a-project.md)
- Assess workflow reference: [how-to/workflows/downstream/assess.md](../../memoria-vault/docs/how-to/workflows/downstream/assess.md)
- Find new sources (if gaps need filling): [find-new-sources.md](../sources/find-new-sources.md)
