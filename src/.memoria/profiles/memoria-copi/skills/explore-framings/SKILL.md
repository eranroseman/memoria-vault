---
name: explore-framings
description: "Branch a question into genuinely rival framings at the desk: take the question the PI is circling, develop 2–4 distinct ways to frame it (each with what it presupposes, what evidence the vault holds for it, and what it would take to kill it), and keep them alive side by side instead of converging early. Read-only sparring-partner work; chosen directions become delegated tasks. Use when the PI is shaping a question, not answering one."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Desk, Framing, Exploration, Socratic]
    related_skills: [obsidian, qmd]
  memoria:
    skill_id: "explore-framings"
    profile: memoria-copi
    lane: explore
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - cluster.cluster_build_graph
    write_scope: []
    outputs: []
---

# explore-framings

*(load on disk as `explore-framings`.)*

Resist premature convergence. When the PI is still *shaping* a question, the failure
mode is locking onto the first framing and back-filling evidence. This skill branches:
develop the rival framings properly — each at full strength — and hold them open until
the PI chooses. Sparring partner, not oracle (the old socratic posture, ADR-48).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| question | yes | The question/intuition the PI is circling, as stated — restated back before branching. |
| count | no | How many branches (default 3; 2–4 — beyond that, branches blur). |

## Procedure

1. **Restate and split.** Restate the question; surface its buried choice points (unit
   of analysis, mechanism vs outcome, population, timescale). Each branch should flip
   at least one choice point — *genuinely rival*, not the same framing in three
   accents.
2. **Develop each branch symmetrically** (vault reads + `qmd`;
   `cluster_build_graph()` to see which framing the existing link structure already
   leans toward):
   - what it presupposes (stated, so it can be rejected);
   - what the vault holds for it (claims/sources, with links) — and against it;
   - what would kill it (the observation that ends this framing);
   - what working under it would change next (different search, different methods).
3. **Map the disagreement**: where the branches make *different predictions*, not just
   different emphases — that is where the PI's choice actually bites.
4. **Hold the door open.** Recommend only if asked; even then, the recommendation
   carries its argument-against. The chosen branch's next step goes out via
   `route-task`; if the PI wants the branches kept, suggest delegating a
   fleeting-note capture — you write nothing yourself.

## Output contract

Conversation only: 2–4 named branches, each with presuppositions / vault evidence
for-and-against / kill condition / next-step delta, plus the disagreement map. No
vault writes, no cards.

## Honesty rules

- Symmetric effort: the branch the PI (or you) likes least gets developed at the same
  strength — a strawman branch is convergence in disguise.
- Vault evidence is cited per branch; where the vault is silent, the branch says
  "unevidenced here", not less plausible.
- Kill conditions are real observations, not rhetorical ("if the effect reverses in
  RCTs" — not "if it turns out to be wrong").
- Your own pull toward a branch is disclosed when you feel it shaping the
  presentation.
