---
title: Run a pattern
parent: Knowledge
grand_parent: How-to guides
nav_order: 8
---

# Run a pattern

Run a shipped prompt-transformation — analyze the claims in a note, red-team an argument, summarize for recall — over the active note or a selection, and read the result. A pattern proposes; it never writes a canonical note. For the full library and the runner contract, see [Pattern library](../../reference/patterns.md).

## When to use a pattern

- You want a quick, repeatable analytical pass (claims, falsifiability, tensions) over something you're reading or drafting
- You want the same framing applied consistently every time, with a provenance line recording that it ran
- The output is *raw material you'll reshape* — not a finished note. If you want durable prose, delegate a `draft` task instead ([Draft with the Writer](../project/draft-with-writer.md)).

## Prerequisites

- The patterns MCP wired into the lane (it ships on the Librarian and Co-PI profiles)
- The note or selection you want to run over, open in Obsidian

## Steps

**1. Pick the surface.**

Open the note you want to analyze, or select the span in the editor. The active note rides along as the pattern's `input_ref` when you don't select text.

**2. Run the pattern.**

`Cmd/Ctrl-P` → **Memoria: run pattern**, then choose from the suggester. The list is the runnable (`lifecycle: current`) patterns, filtered by mode — library patterns for ongoing reading, project patterns for a writing project. The command stages a Librarian card that calls `patterns_run`; the composed prompt is the shared voice preamble plus the pattern, with your note or selection substituted in.

Equivalent: **Memoria: assist patterns**, or ask the Co-PI in the Agent Client pane ("run analyze-claims over this note").

**3. Read the result where it lands.**

The product lands in the pattern's staging target — a `projects/` scratch note or `notes/fleeting/`, never a gated zone. Treat it as a proposal: the patterns are written to *propose, never assert*, to flag uncertainty, and to mark a missing source as `[no source]` rather than invent one.

**4. Keep what's worth keeping — yourself.**

A pattern result is staging. Distil anything durable into your own note ([Write a claim note](../knowledge/write-a-claim-note.md)); a `contradicts` candidate from `surface-tensions` goes through the link gate ([Review link suggestions](../inbox/review-link-suggestions.md)), never written directly.

## Verify

- The result appears in the pattern's staging target (`projects/` or `notes/fleeting/`), not in `notes/claims/` or `catalog/`
- `system/logs/patterns.jsonl` has a new line for the run (pattern id, `run_id`, target)
- Anything you keep exists as *your* note, distilled in your words — not the raw pattern output promoted as-is

## If the result is a dry-run

If the run reports `dry_run: true`, the pattern's `output_target` is empty or points into a review-gated zone — it produced a prompt but no sanctioned write target, and the Linter flags the pattern file. This is a pattern-authoring fix, not a run-time one: see the gated-target rule in [Pattern library](../../reference/patterns.md).

## Related

- The library, schema, and runner contract: [Pattern library](../../reference/patterns.md)
- When to delegate durable prose instead: [Draft with the Writer](../project/draft-with-writer.md)
- Distilling a kept result: [Write a claim note](../knowledge/write-a-claim-note.md)
- The palette command behind this guide: [Obsidian command palette](../../reference/obsidian-command-palette.md)
