---
title: Discuss a paper
parent: Library
grand_parent: How-to guides
nav_order: 5
---

# Discuss a paper

Think a source through with the Co-PI before writing a claim. The Co-PI is the one conversational agent — a reflective thinking-partner that questions and pushes back; it is read-only ([The Co-PI](../../explanation/profiles/co-pi.md)), so the thinking and the eventual claim note are yours.

If the PI/Co-PI split is new, see [Home](../../README.md).

## Prerequisites

- A checked source in `catalog/sources/`, plus any checked digest or notes already created from it ([Capture and ingest a source](capture-and-ingest.md))
- The `agent-client` Obsidian plugin connected ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md))

## Steps

**1. Pick a source from the discuss queue.**

Open the Library space and choose a checked source or digest you want to think
through.

**2. Orient yourself first.**

Re-read the digest and any checked notes, and keep
`catalog/sources/<source_id>/source.md` open for source metadata while you
consult the paper/PDF if you need the full text. Bring a position, not a blank
page.

**3. Open the Agent Client pane.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) with the source note active, then ask it to discuss the source. The Co-PI reads the active note when the question is about it.

**4. Work the standard questions.**

Good opening moves, whoever asks them first:

- What is the strongest single claim this paper makes?
- What does it connect to in your existing notes?
- What would falsify it?
- What is the smallest version of this idea that stands alone?

Answer in your own words, not the paper's.

**5. Follow where the dialogue leads.**

Don't treat the questions as a checklist. When a question feels too abstract, ask the Co-PI to ground it in a specific passage. When you disagree with the paper's framing, say so directly — the dialogue exists to surface *your* position, not to defend the author's. The conversation is done when you can state the paper's core claim in your own words and name where you stand on it.

**6. Decide the outcome.**

- **The session yields a durable takeaway** → record it through Inspector with
  the source id and interview takeaway. The worker writes the journal row for
  later digest compilation.
- **The source is ready for synthesis** → queue **Compile digest** in Inspector
  with the source id and hub topics. The worker owns the checked digest record.
- **The session yields your own note** → use `Memoria: capture note` or edit the
  checked Concept directly. PI edits are direct, then observed and backfilled.
- **No standalone claim right now** → add one line to the source note saying why
  ("confirms existing claims, adds no new argument") and leave the trace in the
  journal; the decision is the work.

Closing the pane exports the transcript for later review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)). If the dialogue surfaced a durable insight, promote that insight yourself as a PI note or checked Concept update.

## Verify

- Any durable takeaway is captured as a PI note, direct PI edit, or worker-owned
  journal/digest event
- Nothing in the vault was edited by the agent — the Co-PI's write scope is
  empty; if you see an unexpected edit, treat it as a configuration error and
  check `system/logs/audit.jsonl`

## Related

**How-to**

- Previous step: [Classify a source](classify-a-source.md)
- Keep a durable synthesis: [Query the vault](../knowledge/query-the-vault.md)

**Reference**

- The full permission matrix: [Profile capabilities](../../reference/profile-capabilities.md)
- Worker-owned digest and interview actions: [System actions](../../reference/system-actions.md)

**Explanation**

- The agent in the Agent Client pane: [The Co-PI](../../explanation/profiles/co-pi.md)
- The queue this works down: [Discuss queue](../../explanation/dashboards/synthesis-agenda.md#discuss-queue)
