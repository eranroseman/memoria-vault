---
title: Verify and revise a draft
parent: Project
nav_order: 6
---

# Verify and revise a draft

Put a draft in front of the **Peer-reviewer** — the independent, adversarial `verify` lane — read the finding-first flag cards it raises, close the gaps, and loop until clean or the remaining gaps are consciously accepted. The Peer-reviewer's posture is *flag, don't fix*: the only thing it can write is Inbox cards; every edit is yours.

## Prerequisites

- A draft in `projects/<slug>/` ([Draft with the Writer](draft-with-writer.md)), or any text whose claims you want traced

## Steps

**1. Delegate or commit a verify pass.**

For project drafts under `projects/<slug>/`, committing the draft enqueues a verify-lane card automatically through the vault's `post-commit` hook. You can also request a pass with `Cmd/Ctrl-P` → **Memoria: verify draft**, or ask in the Agent Client pane if you want help shaping the check:

> "Verify `projects/<slug>/<section>.md` — check that every claim it makes is actually supported by its cited sources."

Both manual routes create a **`verify`** task. **Memoria: verify draft** defaults to the active note when it's under `projects/` and writes a local `[!verification]` preflight trace before delegating; the Co-PI route delegates the same lane card after conversational framing (see [Command palette](../../reference/obsidian-command-palette.md)). You can point the lane at anything — one claim, a hub, a whole draft. The proposer and the checker are independent by construction: the Peer-reviewer is deliberately not the agent that gathered the evidence or wrote the prose.

**2. Read the flag cards.**

Findings land in the Inbox as **`flag` cards** — finding-first, with the verdict carried as a separate `agent_recommendation` field ([Inbox card fields](../../reference/inbox-card-fields.md)). A `clean` flag closes nothing by itself; an `issues-found` flag changes nothing by itself. You act.

**3. Address each gap.**

- **A cited source doesn't say what the draft says:** revise the sentence, or soften it and acknowledge the weakness.
- **An unsupported assertion:** add the citation, write the missing claim note from a source you hold, or rewrite the line as explicitly your view.
- **A superseded claim cited:** the draft leans on a claim with `superseded_by` set — cite the successor instead (the Linter's `fama-exposure` detector hunts the same failure across the vault).
- **A missing source:** capture it first ([Capture and ingest a source](../library/capture-and-ingest.md)), or cut the placeholder.

Resolve each handled flag (`Cmd/Ctrl-P` → **Memoria: resolve inbox card**); the Inbox converges to empty.

**4. Loop.**

After revising, commit the project draft again or delegate another pass over the same file. Verify ↔ fix is a loop, not a single gate.

**5. Accept a gap without closing it** (when appropriate).

A genuine open question you're flagging *in the paper* is a limitation, not a failure — say so in the draft's text, archive the flag, and move on. The honesty body exists so you can disagree with the agent.

**6. Remember the check you never run.**

The retraction sweep runs on cron behind you and raises Inbox `alert` cards on hits ([Run a retraction sweep](../operate/run-a-retraction-sweep.md)) — but a pre-submission manual sweep is cheap insurance.

## Verify

- The latest verify pass came back `clean`, or every remaining `issues-found` flag is consciously accepted in the draft's own text
- No flag cards for this draft remain `proposed` in the Inbox
- No citation in the draft points at a superseded claim

## Related

- Previous step: [Draft with the Writer](draft-with-writer.md)
- Next step: [Export a draft](export-a-draft.md)
- The guided first pass: [Tutorial 05: Verify it holds](../../tutorials/05-verify-it-holds.md)
- The adversarial lane: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)
