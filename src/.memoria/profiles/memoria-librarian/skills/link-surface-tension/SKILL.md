---
name: link-surface-tension
description: "Surface open tensions in the corpus — claim pairs (or claim-vs-source pairs) that cannot both be right as written — and present each as a candidate card with both sides quoted, possible reconciliations listed, and no verdict. Tensions feed the contradictions dashboard and the PI's synthesis backlog; adjudicating them is thinking, and thinking is the PI's. Use after link passes, after contradicting sources are ingested, or on request."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Linking, Contradictions, Tensions]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "link:surface-tension"
    profile: memoria-librarian
    lane: link
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - cluster.cluster_build_graph
      - policy.check_permission
      - policy.complete_write
    write_scope: ["inbox/"]
    outputs: [candidate]
---

# link:surface-tension

*(legacy name: `tension-surface`; load on disk as `link-surface-tension`.)*

Make disagreements impossible to ignore. A tension is a pair of statements the vault
holds that **cannot both be right as written** — two claims, or a claim and a newly
ingested source's finding. Your job is to surface it sharply and *stop*: you present
both sides at their strongest and propose no winner. Open tensions are the PI's
unfinished thinking (the `contradictions` dashboard), not defects to be cleaned up.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| scope | no | A topic/claim neighbourhood, or default: candidates from recent link passes + `[!brief]` "may contradict" notes. |

## Procedure

1. **Collect candidates**: `contradicts`-typed candidates from `link:suggest-claim`
   passes, "may contradict" lines in recent catalog `[!brief]`s, and
   `cluster_build_graph()` neighbourhoods where opposing claims sit one hop apart.
2. **Verify the tension is real** (vault reads): quote each side's exact sentence and
   check the conflict survives context — different populations, scales, or definitions
   often dissolve an apparent contradiction. A dissolved tension is reported as
   dissolved, with the dissolving distinction named.
3. **Steelman both sides**: each side gets its evidence summarized at full strength
   (sources, maturity, sample sizes where stated). Never present a strawman so the
   "resolution" looks easy.
4. **List reconciliation shapes** — as questions, not answers: moderation ("X holds
   under condition C?"), measurement difference, one side superseded. These are reading
   prompts for the PI.
5. **Write — gated.** One `candidate` card in `inbox/` per tension (a tension is a
   discrete decision, so per-tension cards are correct here — but a sweep that finds
   many becomes ONE worklist card, ADR-54).

## Output contract

A `candidate` card (schema `candidate`, ADR-51 honesty body): `title` = the tension in
one line ("X says A; Y says not-A under the same conditions"); `action` = "adjudicate
or hold open"; `argument_for` = why this tension matters now (what downstream work it
blocks); `argument_against` = your honest case that it may be apparent-only;
`what_tipped_it` = the two quoted sentences; `certainty` = how sure you are the
conflict is real, not whether either side is right.

## Honesty rules

- **No verdicts.** Even when one side is a `seedling` and the other `evergreen`, you
  report maturity and stop — maturity is development, never trust (ADR-50).
- Both quotes verbatim, with locators; a tension you cannot quote is not raised.
- Dissolved tensions are still reported (quietly) — the PI learns from near-misses,
  and silent dismissal is disposal.
- Never edit either side, never propose retraction — `lifecycle` changes are the PI's.
