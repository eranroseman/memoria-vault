---
name: draft-score-outline
description: "Score an existing outline (or outline options) against mechanical readiness criteria — claim coverage per node, maturity of load-bearing claims, contradiction exposure, hole count — and append the scorecard to the outline note in project scratch. Advisory only: scores inform the PI's pick, they never gate. Use after draft-outline-argument, or before committing a section to draft-write-section."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Drafting, Outlining, Scoring]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "draft-score-outline"
    profile: memoria-writer
    lane: draft
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.append_content
      - obsidian.patch_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["projects/"]
    outputs: [source]
---

# draft-score-outline

Tell the PI how draft-ready an outline is, per node, with the arithmetic shown. The
score is **advisory** — it informs the pick between outline options or the go/no-go on
drafting a section; it gates nothing and ranks no one's thinking (ADR-50: a score is a
property, never trust).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| outline path | yes | The outline (or `-options.md`) note under `projects/<p>/outlines/`. |

## Criteria (mechanical, in fixed order)

| Criterion | How it is computed |
| --- | --- |
| claim coverage | per node: bound claims present / nodes total — a node with no `[@citekey]`/`[[claim]]` binding scores 0. |
| load-bearing maturity | for each load-bearing claim, its `maturity` (`seedling / budding / evergreen`) read from the claim note's frontmatter. |
| contradiction exposure | bound claims whose `links:` carry `contradicts` edges (or that an open tension card names) — counted, listed. |
| hole count | explicit `[!todo]` holes + nodes with no carrying claim. |
| citation resolvability | every bound citekey resolves in `.memoria/memoria.bib` (a failed resolve is a finding for the verify lane, noted not judged). |

## Procedure

1. **Read** the outline and every bound claim note (via the `obsidian` skill; `qmd`
   only to resolve claim links).
2. **Compute** each criterion per node; no holistic vibes — each cell of the scorecard
   traces to a count or a frontmatter field.
3. **Append — gated.** Add a `## Scorecard (draft-score-outline, YYYY-MM-DD)` section
   to the outline note itself (`obsidian` append/patch): the per-node table, the
   per-option totals when scoring options, and a one-paragraph reading of where the
   structure is thinnest. Never write outside `projects/`.

## Output contract

The appended scorecard section: per-node rows (node · coverage · weakest maturity ·
contradictions · holes), per-option summary, and the evidence trail (which claim note,
which field) for every non-obvious cell. Re-runs append a new dated scorecard — never
overwrite a prior one (the delta is information).

## Honesty rules

- Show the arithmetic: a score whose computation the PI cannot reproduce from the
  listed fields is not a score, it is an opinion.
- Contradiction exposure is reported neutrally — an exposed contradiction may be the
  paper's contribution, not a defect.
- Never auto-pick the "winning" option, never edit the outline's content, never score
  prose quality — structure readiness only.
- If two options tie, say they tie; manufactured precision (7.3 vs 7.4) is dishonesty
  in costume.
