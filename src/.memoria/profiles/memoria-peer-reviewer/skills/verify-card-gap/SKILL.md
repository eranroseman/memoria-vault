---
name: verify-card-gap
description: "Turn a verification finding about MISSING evidence into a well-formed gap card in inbox/ — the synthesis backlog entry the PI (and the Librarian's discovery pass) picks up. Used standalone when review surfaces a hole, or called by verify-trace-claim for each failed trace. Writes only inbox/ gap cards with the full ADR-51 honesty body; never creates the missing claim or source itself."
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
      - obsidian.put_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["inbox/"]
    outputs: [gap]
---

# verify-card-gap

*(legacy name: `gap-card`; load on disk as `verify-card-gap`.)*

Turn "the evidence for X is missing" into a card the PI can act on. A gap is a
**finding about an absence**: a claim with no supporting claim note, an argument leg
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

1. **Check for an existing card.** Search `inbox/` (via the `obsidian` skill) for an
   open gap card covering the same absence — extend reasoning happens in the Co-PI pane,
   so a duplicate card is noise. If one exists, stop and report it instead.
2. **State the gap concretely.** Quote the unsupported sentence; name what would close
   the gap (a claim note? a source? a replication?). "Coverage is thin" is not a gap;
   "the claim ‹…› in `projects/p1/drafts/intro.md` has no supporting claim note" is.
3. **Write — gated.** Create `inbox/gap-<slug>.md` (schema `gap`) with the full ADR-51
   honesty body. Related gaps from one review pass go on ONE card with a list, never N
   cards (ADR-54).

## Output contract

A `gap` card (schema `gap`, `lifecycle: proposed`) with every required field:

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
- Never write the missing claim, never delegate work yourself (the Peer-reviewer has no
  delegation path) — the card IS the handoff.
