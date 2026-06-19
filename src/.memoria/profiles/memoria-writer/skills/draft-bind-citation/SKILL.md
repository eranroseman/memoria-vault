---
name: draft-bind-citation
description: "Bind every factual sentence of an existing draft in project scratch to a citekey from its claim set — insert [@citekey] where the source is determined, mark visible holes where it is not, and normalize citation tokens against memoria.bib. Repair-and-normalize for drafts that arrived underbound; never invents a source. Use after heavy PI edits or on imported prose."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Drafting, Citations, Provenance]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "draft-bind-citation"
    profile: memoria-writer
    lane: draft
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.patch_content
      - obsidian.append_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["projects/"]
    outputs: [source]
---

# draft-bind-citation

*(legacy name: `citation-bind`; load on disk as `draft-bind-citation`.)*

Make a draft's provenance explicit. Heavily edited or imported prose drifts away from
its citations; this skill re-binds each factual sentence to the claim/source that
carries it — **from the draft's own claim set**, never from fresh research. Where no
source in the set carries a sentence, the hole becomes visible instead of the sentence
becoming confident.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| draft path | yes | The draft under `projects/<p>/drafts/`. |
| claim set | yes | The claim notes / citekeys the draft may bind to (frontmatter `sources:` or the handoff payload). |

## Procedure

1. **Inventory** the draft's factual sentences and existing `[@citekey]` tokens (vault
   reads via the `obsidian` skill).
2. **Bind.** For each unbound factual sentence, find its carrier in the claim set
   (claim-note prose match, `qmd` similarity over the *given set only* as a tiebreak).
   Insert `[@citekey]` only when the claim note actually supports the sentence as
   written — close-but-stronger is a hole, not a bind.
3. **Normalize.** Every citation token resolves against `.memoria/memoria.bib`; fix
   malformed tokens (`[@ key]`, bare keys) to the canonical form. An unresolvable
   citekey is left in place and listed — resolving it is the verify lane's call.
4. **Mark holes.** Unbindable factual sentences get
   `> [!todo] unbound: no claim in the set supports this` immediately below — the
   sentence is never silently deleted or weakened (the PI's prose is the PI's).
5. **Write — gated** (`obsidian` patch on the draft) and update the draft's
   frontmatter `sources:` to the exact citekeys now bound. Append a
   `## Binding report (YYYY-MM-DD)` section: bound / already-bound / holes /
   unresolvable, each listed. Never write outside `projects/`.

## Output contract

The same draft, with: every factual sentence either citekey-bound or visibly
`[!todo]`-holed; normalized tokens; a complete `sources:` list; the dated binding
report. No content rewrites — binding changes citations and adds callouts, nothing
else.

## Honesty rules

- Bind to what the claim note says, not what the sentence wishes it said — a bind that
  upgrades hedged evidence into a firm sentence is a false bind; mark the hole and
  quote the hedge.
- Never reach outside the given claim set (no new sources, no vault-wide scavenging) —
  a missing carrier is gap-workflow input, not a search prompt.
- Never verify your own binds as correct — that is `verify-check-citation`'s lane.
- The binding report counts must add up to the sentence inventory; sentences you chose
  to treat as non-factual (framing, signposting) are listed as such, auditable.
