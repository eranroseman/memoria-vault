---
title: Discuss a paper
parent: Compile
nav_order: 6
---


# Discuss a paper

Run a Socratic session on a classified source to sharpen your understanding before writing a claim. The Socratic profile asks questions; it cannot write anything — the thinking and the eventual claim note are yours.

## Prerequisites

- The source is classified (`lifecycle: current`) ([Classify a source](classify-a-source.md))
- The `agent-client` Obsidian plugin is installed and connected

## Steps

**1. Open the paper note in Obsidian.**

Navigate to `20-sources/01-papers/<citekey>.md`. Open the Reading & Processing workspace if you use it: `Cmd-P → Memoria: Reading workspace` *(deferred — open the note directly today)*.

**2. Read or skim the relevant sections.**

Before invoking the Socratic profile, orient yourself in the paper. The `[!brief]` callout and the Key Findings section from classification are good starting points.

**3. Open the agent-client pane and switch to Socratic.**

Open the ACP pane (`Cmd-P → Agent Client: Open chat view`, or the ribbon icon), then switch to **Socratic** via the pane’s profile picker. The active paper note auto-attaches as context. Then ask it to discuss the note. *(`Memoria: ask about this note` is deferred — use the ACP pane today.)*

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
- **The paper doesn't yield a standalone claim right now** → close the ACP pane, open the paper note, add a brief explanation under Key Findings of why no claim was extracted (e.g., "confirms existing claims but adds no new argument"), then close the `discuss` card manually: `Cmd-P → Memoria: close discuss card → select outcome: no-claim` *(deferred — close the card from the terminal / its source file today)*.

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

- The full permission matrix: [Profile capabilities](../../reference/profiles.md)

**Explanation**

- Socratic profile design: [The Socratic](../../explanation/profiles/co-pi.md)
- Discuss queue dashboard: [The discuss-queue dashboard](../../explanation/dashboards/synthesis-agenda/discuss-queue.md)
- Paper-note structure used as context: [Note body structure](../../explanation/knowledge/note-body-structure.md)
