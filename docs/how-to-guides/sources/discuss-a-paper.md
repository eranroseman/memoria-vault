
# How to discuss a paper

Run a Socratic session on a classified source to sharpen your understanding before writing a claim. The Socratic profile asks questions; it cannot write anything — the thinking and the eventual claim note are yours.

## Prerequisites

- The source is classified (`lifecycle: current`) ([classify-a-source.md](classify-a-source.md))
- The `agent-client` Obsidian plugin is installed and connected

## Steps

**1. Open the paper note in Obsidian.**

Navigate to `20-sources/01-papers/<citekey>.md`. Open the Reading & Processing workspace if you use it: Cmd-P → Memoria: Reading workspace.

**2. Read or skim the relevant sections.**

Before invoking the Socratic profile, orient yourself in the paper. The `[!brief]` callout and the Key Findings section from classification are good starting points.

**3. Open the agent-client pane.**

Cmd-P → Memoria: ask about this note

This opens the right-side ACP pane connected to the Socratic profile (`memoria-socratic`), with the current note in context.

**4. Let the profile run its opening questions.**

The Socratic profile will ask the standard opening set:
- What is the strongest single claim this paper makes?
- What does it connect to in your existing notes?
- What would falsify it?
- What is the smallest version of this idea that stands alone?

Answer each in the pane. Write in your own words, not the paper's.

**5. Follow where the dialogue leads.**

Don't treat the questions as a checklist. When a question feels too abstract, ask the Socratic agent to ground it in a specific passage or a concrete example from the paper. When you disagree with the paper's framing, say so directly — the dialogue exists to surface *your* position, not to defend the author's. Let one answer pull the next question; the turns that matter are usually the ones you didn't plan.

The conversation is "done enough" when you can state the paper's core claim in your own words and name where you stand on it — agree, disagree, or agree-with-a-caveat. That is the signal to stop and move to the outcome below.

**6. Decide the outcome.**

After the dialogue, decide:

- **The paper yields one or more claims** → proceed to [write a claim note](write-a-claim-note.md). The `discuss` card closes automatically when you create the first claim note from this source.
- **The paper doesn't yield a standalone claim right now** → close the ACP pane, open the paper note, add a brief explanation under Key Findings of why no claim was extracted (e.g., "confirms existing claims but adds no new argument"), then close the `discuss` card manually: Cmd-P → Memoria: close discuss card → select `outcome: no-claim`.

## Verify

- If a claim was written: the `discuss` card no longer appears in the discuss queue on `weekly-review.md`
- If no claim: a `no-claim` note appears under Key Findings and the card is archived
- The paper note is NOT edited by the Socratic profile — it is write-denied

## Notes

The Socratic profile's lane policy is `policy.allow.write: []` — it cannot edit any file in the vault. If you see unexpected edits to the note after a Socratic session, that is a configuration error: check the lane-overrides file at `.memoria/lane-overrides/socratic.yaml`.

## Related

**How-to**

- Previous step: [Classify a source](classify-a-source.md)
- Next step: [Write a claim note](write-a-claim-note.md)

**Reference**

- The full permission matrix: [profiles.md](../../reference/profiles.md)

**Explanation**

- Socratic profile design: [explanation/profiles/socratic.md](../../explanation/profiles/socratic.md)
- Discuss queue dashboard: [explanation/dashboards/discuss-queue.md](../../explanation/dashboards/discuss-queue.md)
- Paper-note structure used as context: [note-body-structure.md](../../explanation/knowledge/note-body-structure.md)
