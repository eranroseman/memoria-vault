---
name: verify-card-gap
description: "Turn a verification finding about MISSING evidence into a worker-owned gap attention projection — the synthesis backlog entry the PI and Librarian discovery pass pick up. Used standalone when review surfaces a hole, or called by verify-trace-claim for each failed trace. Never creates the missing note or source itself."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Verification, Gaps, Inbox]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "verify-card-gap"
    profile: memoria-peer-reviewer
    lane: verify
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - policy.check_permission
    write_scope: []
    outputs: [gap]
---

# verify-card-gap

Turn "the evidence for X is missing" into a card the PI can act on. A gap is a
**finding about an absence**: a claim with no supporting checked note, an argument leg
with no source, a comparison the draft asserts but the vault cannot back. You record
the absence precisely; you never fill it (finding the source is the Librarian's
`catalog` lane, promoting a claim is the PI's gate).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| finding | yes | What is missing, quoted from the reviewed text where possible. |
| origin | yes | The note/draft path (and check) that surfaced the gap. |
| suggestion | no | Where evidence might come from — phrased as a lead, not a verdict. |

## Procedure

1. **Check for existing attention.** Search the generated attention projections for an
   open gap covering the same absence — duplicate attention is noise. If one exists,
   stop and report it instead.
2. **State the gap concretely.** Quote the unsupported sentence; name what would close
   the gap (a claim-bearing note? a source? a replication?). "Coverage is thin" is not
   a gap; "the claim <...> has no supporting checked note" is.
3. **Request attention.** Return one worker-owned `gap` attention request with the full
   ADR-51 honesty body. Related gaps from one review pass go on one item with a list,
   never N items (ADR-54).

## Output contract

A `gap` attention request with every required field:

- `title` — the absence in one line.
- `action` — what accepting the card means (e.g. "delegate a catalog search for
  evidence on ‹…›").
- `argument_for` — why this gap matters to the argument it blocks.
- `argument_against` — your honest self-rebuttal (e.g. "the draft may not need this
  leg; the PI may cut the paragraph instead").
- `what_tipped_it` — the concrete observation (the failed trace route, the missing
  citekey).
- `certainty` — `confident / likely / unsure`, calibrated; a gap inferred from one
  ambiguous sentence is `unsure`.
- `raised_by: memoria-peer-reviewer`, `loudness` proportionate (a blocking export gap
  may be `notice`; default `quiet`).

## Honesty rules

- The card proposes; the PI disposes — never imply the gap *must* be filled.
- `argument_against` is genuine, not a strawman; if you cannot think of one, the gap is
  probably under-specified — sharpen the finding first.
- Never write the missing note, never delegate work yourself (the Peer-reviewer has no
  delegation path) — the attention request is the handoff.
