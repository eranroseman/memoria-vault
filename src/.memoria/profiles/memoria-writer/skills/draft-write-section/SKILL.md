---
name: draft-write-section
description: "Draft one section of prose into project scratch from the claims and sources the handoff names — every factual sentence bound to a citekey, holes left visible, the draft marked agent-drafted. The Writer's core skill: generative, draft-only, review-gated. Use when a draft card lands with a section goal, an outline node, and a claim set."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Drafting, Writing, Synthesis]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "draft-write-section"
    profile: memoria-writer
    lane: draft
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - obsidian.append_content
      - obsidian.patch_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["projects/"]
    outputs: [source]
---

# draft-write-section

Produce one section of prose the PI will reshape. A draft is **raw material, never a
deliverable**: it is marked agent-drafted, and the PI rewrites in their own words. You
compose from what the vault holds — the claims and sources the handoff names — and
nothing else.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| goal | yes | The section to draft (from the card's handoff payload). |
| outline node | no | The outline section this draft fills (`projects/<p>/outlines/…`). |
| claim set | yes | The claim notes / citekeys the section may draw on. |

## Procedure

1. **Read the inputs** (via the `obsidian` skill): the outline node, every claim note
   in the set, and the cited paper notes' `[!brief]`s for framing. Use `qmd` only to
   *locate* the named material — never to scout for new claims.
2. **Draft.** One section, in plain prose. Every factual sentence carries its
   `[@citekey]` from the given set. Where the argument needs a fact the set cannot
   back, leave the hole visible: `> [!todo] missing evidence: ‹what›` — **if you cannot
   cite it, you cannot write it.**
3. **Mark and write — gated.** Write to
   `projects/<project>/drafts/<section-slug>.md` with frontmatter
   `drafted_by: memoria-writer`, `lifecycle: proposed`, `sources:` listing every
   citekey used. Never write outside `projects/`; never touch `notes/` or `catalog/`.
4. **Hand back.** The card's `expected_outputs` names the draft path; the PI reviews
   from there. Verification is the Peer-reviewer's lane — never mark your own draft
   checked.

## Output contract

A draft note under `projects/<p>/drafts/` — agent-marked (`drafted_by`), every factual
sentence citekey-bound, holes as visible `[!todo]` callouts, frontmatter `sources:`
complete. No new claims, no edits to any other file.

## Honesty rules

- **No new claims**: a missing claim is a gap for the map lane, not something to
  improvise. Quote the hole, do not paper over it.
- **No fact-checking your own output** (separation of duties, ADR-48) — and no
  rhetorical confidence the citations do not earn: hedge exactly as much as the claim
  notes hedge.
- A sentence that synthesizes two claims cites both; a transition that smuggles in an
  uncited generalization is a factual sentence too — cite it or cut it.
- If the claim set is too thin to draft the section honestly, say so in the draft
  header and stop early — a short honest draft beats a fluent fabricated one.
