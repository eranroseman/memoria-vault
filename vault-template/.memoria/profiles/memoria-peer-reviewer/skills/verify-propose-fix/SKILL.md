---
name: verify-propose-fix
description: "When a verification finding has an obvious remedy, propose the fix as an inbox candidate card — the exact edit, spelled out, with the ADR-51 honesty body — WITHOUT touching the thing under review (flag, don't fix). Used after verify-check-citation / verify-trace-claim when a finding is mechanical enough that the remedy is clear (a typo'd citekey, a wikilink to the wrong note, a stale superseded reference)."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Verification, Proposals, Inbox]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "verify-propose-fix"
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
    outputs: [candidate]
---

# verify-propose-fix

The bridge between "flag, don't fix" and not wasting the PI's time: when a finding's
remedy is mechanical and unambiguous, spell the fix out so accepting it is one
decision, not a research task. The fix is **proposed on a card** — the thing under
review is never edited (the Peer-reviewer writes only `inbox/`; the accepted fix is
applied by the PI or delegated to the owning lane).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| finding | yes | The verification finding (usually a `flag` card or its content). |
| target | yes | The path the fix would apply to. |

## When a fix is proposable

Only when the remedy is determined by the finding itself: a citekey typo with exactly
one plausible resolution in the bib; a `[[wikilink]]` pointing at a renamed note with
one matching target; a citation to a source whose claim note was superseded, where the
`superseded_by` chain names the replacement. **If two remedies are plausible, that is a
finding, not a fix** — present both on the card and mark `certainty: unsure`, or stay
with the plain flag.

## Procedure

1. **Verify the remedy mechanically** (vault reads + `qmd` search): confirm the
   proposed target exists, resolves, and is unique. A fix you could not verify is not
   proposable.
2. **Spell out the edit** as old → new, quoted exactly, with the file path and enough
   surrounding context to apply it unambiguously.
3. **Write — gated.** One `candidate` card per reviewed target in `inbox/`
   (`inbox/fix-<slug>.md`), listing each proposed edit; link the originating `flag`
   card. One card per review pass, never one per edit (ADR-54).

## Output contract

A `candidate` card (schema `candidate`, `lifecycle: proposed`):

- `title` — the fix in one line; `action` — what accepting applies (the old → new edit
  list, verbatim).
- `argument_for` — why the remedy is determined (the mechanical verification result).
- `argument_against` — your honest self-rebuttal (e.g. "the typo may be intentional —
  the PI may have meant the 2019 companion paper").
- `what_tipped_it` — the disambiguating evidence (unique bib match, supersession
  chain).
- `certainty` — `confident` only when the remedy is unique and verified; otherwise
  `likely` / `unsure`.
- `raised_by: memoria-peer-reviewer`; `target`/`citekey` context in the body.

## Honesty rules

- Never apply the fix — not even a one-character citekey edit; the card is the entire
  output (separation of duties, ADR-48).
- Never propose fixes for judgment findings (an unsupported claim has no mechanical
  remedy — that is `verify-card-gap`'s lane).
- The PI's rejection of a fix card is information: do not re-propose the same fix on
  the next pass; note the standing rejection instead.
