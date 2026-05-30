---
topic: workflows
---

# Discuss

**Group.** Upstream (stage workflow)
**Goal.** Transform a classified source from "fully classified metadata" into "thought-about enough to write a claim from." No artifact is produced. The output is the human's sharpened understanding.

## Pipeline position

Between [Classify](classify.md) and [Distill](distill.md).

## Steps

1. A `discuss` card opens automatically when a paper note's `lifecycle` becomes `current`. The card targets the human (no profile claims it).
2. The human opens the paper note, reads (or re-reads) the relevant passages, and switches to the **Socratic profile** via ACP: `Cmd-P → Memoria: ask about this note`. The ACP pane on the right (see [obsidian-ui/workspaces.md](../../../reference/obsidian-ui/workspaces.md) — Reading & Processing workspace) opens the Socratic profile, whose lane policy is `policy.allow.write: []` (write-denied across the entire vault).
3. The Socratic profile runs the `socratic-processing` command: "What's the strongest single claim? What does it connect to? What would falsify it? What's the smallest version of this idea that stands alone?" — the questions are the profile's whole product. The human answers in dialogue.
4. The human either: (a) decides this source yields one or more claim notes → proceeds to [Distill](distill.md); writing the claim note auto-closes this `discuss` card via the git hook (`outcome: claim-written` — there is no intermediate `ready-for-distill` state), or (b) decides the source doesn't yield a claim → closes the card with `outcome: no-claim` and notes the reason in the paper note's body.

## Owners

Human owns the thinking; Socratic owns the questioning. Architecturally the Socratic profile cannot author the claim — its lane policy denies all writes. That constraint is what makes the discussion remain the human's cognitive work rather than something that gets quietly authored.

## Card lifecycle

`ready` (opens automatically when `lifecycle` becomes `current`; the card is on the human-targeted lane, not Kanban-dispatched) → human invokes Socratic via ACP → Socratic conversation happens (no card state change, no writes) → human writes the claim note in `30-synthesis/01-claims/`, which closes the card via the git hook → `archived` (with `outcome: claim-written`) OR human manually archives with `outcome: no-claim`. The card never reaches `running` in the dispatcher sense — Socratic is `routing.invocation: interactive_only`.

## Command

`Cmd-P → Memoria: ask about this note` (preferred) or `hermes -p memoria-socratic chat --command socratic-processing --source {citekey}` (CLI).

## Why the card auto-closes only on human action

The system cannot tell whether thinking has happened. A paper note with `lifecycle: current` and no `discuss` card closure is the dashboard's signal that the human is behind on discussion. Letting the agent close the card would defeat the visibility argument that made `discuss` a stage in the first place.

## Example

`mamykina2010sense.md` finishes classification at `lifecycle: current`. A `discuss` card opens. Three days later it's still open — the `weekly-review` surfaces it in the "discuss queue" view. The human opens the note, invokes Socratic, and the profile asks: "What's Mamykina's strongest claim?" The human answers ("receptivity depends on momentary cognitive load — strongest at idle / commute / waiting-room moments, weakest during task focus"). Socratic follows up: "What would falsify it?" → human thinks → answers. After ten minutes, the human closes the ACP pane and switches to Writer profile (or just writes in the editor without ACP) to author `30-synthesis/01-claims/receptivity-decreases-under-high-cognitive-load.md` from scratch in their own words. The `discuss` card auto-closes on the new claim note's creation.

## Related

- **Profile:** [profiles/socratic.md](../../../explanation/profiles/socratic.md)
- **Dashboard:** [discuss-queue.md](../../../explanation/dashboards/discuss-queue.md)
- **Previous workflow:** [Classify](classify.md)
- **Next workflow:** [Distill](distill.md)
