---
title: How to build a Map of Content
parent: Maintenance
---

# How to build a Map of Content

This guide shows you how to create a navigational hub note that gives a dense claim cluster a stable entry point.

## When to create a MOC

Create one when a topic cluster crosses roughly 15–20 related claim notes, or a recurring topic appearing across 3 or more source notes. See [reference/linking.md](../../reference/linking.md#moc-thresholds) for the full threshold table including child-MOC thresholds.

## Steps

1. **Open `30-synthesis/03-moc/`.** In the file tree, right-click `30-synthesis/03-moc/` → New note from template → `moc.md`.

2. **Name the MOC.** Use the topic slug plus `-moc` suffix: `jitai-design-moc`, `receptivity-timing-moc`.

3. **Write the overview.** Two to four sentences covering what the cluster is about, what it includes, and what it doesn't.

4. **Link the member notes.** Under a `## Notes` section, list the claim notes and paper notes that belong. Use wikilinks. Curate — omit tangentially related notes.

5. **Update member notes.** Open each member note and add the MOC to its `moc:` frontmatter field: `moc: [[jitai-design-moc]]`.

6. **Add a `## Gaps` section.** Note what the cluster is missing — thin sub-topics, open questions, papers not yet ingested. This section feeds the `open-questions` dashboard.

## Splitting a child MOC

When a branch within an existing MOC grows beyond 20 claim notes and 10 paper notes, split it:

1. Create a new MOC for the branch.
2. Move the branch member notes into the new MOC (`moc:` frontmatter updated).
3. In the parent MOC, replace the individual note list for that branch with a link to the child MOC.
4. Add `parent_moc: [[parent-moc-name]]` to the child MOC's frontmatter.

## Owners

You author and curate the MOC. The Linter's `skeleton-drift` detector will flag if the MOC's `updated` timestamp lags behind its member notes' modification dates.

---

## Related

- Promotion adds MOC entries (step 5): [promote-a-claim.md](../sources/promote-a-claim.md)
- MOC creation thresholds and link vocabulary: [linking.md](../../reference/linking.md#moc-thresholds)
- The MOC as a note type: [note-types.md](../../explanation/knowledge/note-types.md)
- Why hubs matter to the knowledge cycle: [knowledge-cycle.md](../../explanation/knowledge/knowledge-cycle.md)
