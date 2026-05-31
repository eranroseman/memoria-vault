# Build a Map of Content

**Goal:** Create a navigational hub note that gives a dense claim cluster a stable entry point.

A MOC (`moc` note type, lives in `30-synthesis/03-moc/`) is authored by you — agents may surface MOC candidates but cannot write into the review-gated synthesis zone.

## When to create a MOC

Create one when a topic cluster crosses this threshold: roughly 15–20 related claim notes, or a recurring topic appearing across 3 or more source notes that you keep mentally tracking. If you're opening the same five claim notes every time you work on a topic, that's the signal.

See [reference/linking.md](../../reference/linking.md#moc-thresholds) for the full threshold table including child-MOC thresholds.

## Steps

1. **Open `30-synthesis/03-moc/`.** Create a new note using `Cmd+P → Memoria: write claim note` — wait, use the MOC template instead: in the file tree, right-click `30-synthesis/03-moc/` → New note from template → `moc.md`.

2. **Name the MOC.** Use the topic slug plus `-moc` suffix: `jitai-design-moc`, `receptivity-timing-moc`. The slug becomes the wikilink target that all member notes will use.

3. **Write the overview.** Two to four sentences: what this cluster is about, what it covers, what it doesn't. This is not a summary of every note — it's the frame that helps a reader (including future-you) understand the cluster's scope.

4. **Link the member notes.** Under a `## Notes` section, list the claim notes and paper notes that belong. Use wikilinks. You don't need to include every note — curate; omit notes that are tangentially related.

5. **Update member notes.** Open each member note and add the MOC to its `moc:` frontmatter field: `moc: [[jitai-design-moc]]`. This is what the graph view uses to show MOC membership.

6. **Add a `## Gaps` section.** Note what the cluster is missing — thin sub-topics, open questions, papers you know exist but haven't ingested. This section feeds the `open-questions` dashboard.

## Splitting a child MOC

When a branch within an existing MOC grows beyond 20 claim notes and 10 paper notes, split it:

1. Create a new MOC for the branch.
2. Move the branch member notes into the new MOC (`moc:` frontmatter updated).
3. In the parent MOC, replace the individual note list for that branch with a link to the child MOC.
4. Add `parent_moc: [[parent-moc-name]]` to the child MOC's frontmatter.

## Owners

You author and curate the MOC. The Linter's `skeleton-drift` detector will flag if the MOC's `updated` timestamp lags behind its member notes' modification dates.
