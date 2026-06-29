---
name: verify-trace-claim
description: "The claim-trace: every substantive factual claim in a draft must trace to a supporting checked note in knowledge/notes/, by a fixed three-route order — explicit wikilink, [@citekey] + prose embedding match, then similarity search across checked claim-bearing notes. Deterministic ranking; an LLM verdict only on ambiguous top candidates. A failed trace becomes a worker-owned gap attention item via verify-card-gap. Flag-only — the draft is never edited. Run when tracing a draft before review or export."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Verification, Claims, Provenance]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "verify-trace-claim"
    profile: memoria-peer-reviewer
    lane: verify
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - pyzotero.get_references
      - pyzotero.get_citations
      - pyzotero.find_related
      - policy.check_permission
    write_scope: []
    outputs: [flag, gap]
---

# verify-trace-claim

Answer one mechanical question per substantive claim in a draft: **does it trace to a
supporting checked note in `knowledge/notes/`?** A claim can be perfectly cited and still
untraced — the trace is to the vault's reviewed knowledge, not to the literature. You
judge traceability, never truth, and you **flag, never fix**.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| target | yes | The draft or claim-bearing note to trace. |

## Procedure

Walk each substantive claim through the **fixed trace order** (detail:
`../verify-check-citation/references/sub-checks.md` §2):

1. **Explicit `[[...]]` wikilink** to a checked claim-bearing note — a deterministic
   graph walk. A wikilink that lands outside `knowledge/notes/` is **untraced**, not
   traced.
2. **`[@citekey]` + prose embedding similarity** to checked notes derived from the cited source —
   deterministic. A citekey with no derived checked notes falls through to route 3 rather
   than auto-failing.
3. **Similarity search across checked claim-bearing notes** (the shared `qmd` index) —
   deterministic ranking; an LLM verdict on the top candidates **only** when the
   similarity score is ambiguous.

Then **report**: one worker-owned `flag` attention projection summarizing traced vs
untraced claims (finding-first, ADR-51); each failed trace is handed to
`verify-card-gap`, which requests the `gap` attention item for the missing evidence.
Batch results stay one summary projection, never N (ADR-54).

## Output contract

- One worker-owned `flag` attention projection: `finding` = the trace summary
  (n traced / n failed, with the untraced sentences quoted), `agent_recommendation`
  in `clean / issues-found / inconclusive`, `target` = the draft path.
- Failed traces -> `gap` attention projections raised through `verify-card-gap`.

## Honesty rules

- Trace order is fixed — never skip to similarity search because routes 1–2 are slower.
- Route-3 verdicts on ambiguous candidates name the candidate and the score; a
  confident top match needs no LLM and says so.
- Never edit the draft, never create the missing note — the gap attention item is the
  whole output.
- You verify work you did not produce; if asked to trace your own prior card, say so
  and recommend independent review.
