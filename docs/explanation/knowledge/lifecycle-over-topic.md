# Why folders encode lifecycle, not topic

The vault's top-level folders (`00-meta`, `10-inbox`, `20-sources`, `30-synthesis`, `40-workbench`, `50-deliverables`) encode where a note is in its lifecycle, not what it's about. A paper on cognitive load lives in `20-sources/01-papers/`, not in `cognitive-science/`. This principle is not a stylistic choice; it is the organizational decision that makes the vault's structure stable and the agent's permissions enforceable.

---

## Why topic folders fail

Topic folders seem natural. "Put all my cognitive science notes in `cognitive-science/`." The problem is that topics are **many-to-many**:

A paper on attention and working memory belongs in `cognitive-science/`, and in `neuroscience/`, and in `HCI/`, and possibly in `productivity-tools/` if it's relevant to a current project. A topic folder forces a choice: pick one folder and lose the connections to the others, or create duplicates that immediately diverge.

Most knowledge management systems respond to this by allowing notes to exist in multiple places (aliases, copies) or by using tags for the cross-cutting topics. But this creates a different problem: the folder is now redundant. If topics live in tags and links, the folder adds no information. If the folder adds information, it must mean something other than topic.

**Lifecycle stage is what the folder can uniquely encode.** A note is at exactly one lifecycle stage: it's either in the inbox, or it's a classified source, or it's a synthesis note, or it's a deliverable in progress. Folders encode the thing that is one-to-one with the note; topics live in frontmatter and links where the many-to-many relationship can be expressed properly.

---

## What the stages mean

The numbered folders form a progression from capture to shipping:

- **`10-inbox/`** — *not yet classified*. The note exists but its role hasn't been decided. The inbox is a queue, not storage.
- **`20-sources/`** — *describes the world*. Classified source material: papers, tools, people, organizations, venues. An external perspective.
- **`30-synthesis/`** — *expresses the human's thinking*. Claims in the human's own words, reference pages, Maps of Content. An internal perspective.
- **`40-workbench/`** — *active work*. A project folder, with all its artifacts, organized by the effort not the lifecycle.
- **`50-deliverables/`** — *finished and shipped*. Manuscripts, presentations, exports.

The numbers are not just labels — they encode a one-way progression. Moving forward (inbox → sources → synthesis) is promotion. Moving backward doesn't happen structurally; deprecated notes go to `95-archive/`.

---

## What this enables

**Agent permissions align with stages.** The Librarian can write to `20-sources/` (creating paper notes) but cannot write to `30-synthesis/` (creating claim notes). This permission can be expressed simply: "write to stage X" rather than "write to everything tagged `cognitive-science` that isn't someone's personal synthesis." Lifecycle stages make permissions tractable.

**The agent's job is well-defined.** The Librarian knows its domain: everything in `20-sources/`. It doesn't need to understand topics to know where a source belongs. The Linter knows what it's looking for: schema violations, broken links, orphan notes — all of which are detectable without understanding topical context.

**Queries are predictable.** A Dataview query asking "what are all the papers on attention?" uses the `topic:` frontmatter field. A query asking "what notes are awaiting classification?" uses the folder. The two questions use different mechanisms because they're asking about different things.

---

## The workbench exception

`40-workbench/` is the deliberate exception to the lifecycle principle. Its unit is the **project**, not the stage. A project folder (`40-workbench/<project-name>/`) holds every working artifact for one effort, organized by sub-stage: `01-map/`, `02-framing/`, `03-canvas/`, `04-drafts/`, `05-verification/`, `06-code/`.

This doesn't violate the principle — it extends it carefully. The principle is an *anti-duplication rule* for many-to-many data: a source has many topics, so it can't live in one topic folder. Workbench artifacts are single-project: a draft belongs to exactly one project, so the duplication problem never arises. A project is not a topic — it's a bounded, transient effort that gets archived when it ships.

The durable knowledge from a project still migrates to the lifecycle layers: the claim notes it produced go to `30-synthesis/01-claims/`, the paper notes to `20-sources/01-papers/`, the deliverable to `50-deliverables/`. The workbench is temporary; the vault is permanent.

---

## Topics in frontmatter, not folders

With lifecycle folders handling the organizational dimension that folders can uniquely carry, topics are encoded in frontmatter:

- `topic: [cognitive-science, attention]` on a paper note
- `study_design: observational` on a paper note
- `topic: [working-memory, cognitive-load]` on a claim note

(`topic`, `study_design`, and `methods` are the schema's domain fields — see [frontmatter.md](../../reference/frontmatter.md#domain-fields). There is no `domain` or `keywords` field.)

This makes topic queries Dataview queries: `WHERE contains(topic, "cognitive-science")`. It makes cross-topic connections explicit: a claim note about HCI that cites cognitive science papers is connected to both topics through its links, not through its folder location.

The vault's navigation structure (MOCs — Maps of Content) builds the topical view on top of the lifecycle structure. A `cognitive-science` MOC is a note in `30-synthesis/03-moc/` that links to the relevant paper notes, claim notes, and reference pages — regardless of which sub-projects they were created for.

---

## Related

- What the stages mean for note types: [note-types.md](note-types.md)
- How notes move between stages: [promotion-model.md](promotion-model.md)
- How agent permissions map to stages: [../architecture/why-specialist-profiles.md](../architecture/why-specialist-profiles.md)
