---
name: map-report-coverage
description: "Surface thin-coverage topics adjacent to a project brief: topic-model the relevant corpus via the cluster MCP, threshold topics by note count and claim presence, and compose a ranked gap report — which thin topics matter for this brief and why. The report informs; thin coverage may be fine. Use when a gap-report request lands or a project review asks where the corpus is weak."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Coverage, Gaps]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map-report-coverage"
    profile: memoria-librarian
    lane: map
    mcp_tools:
      - cluster.cluster_model_topics
      - cluster.cluster_build_graph
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["notes/fleeting/", "inbox/"]
    outputs: [fleeting, gap]
---

# map-report-coverage

Tell the PI where the corpus is thin **relative to a brief** — not where it is thin in
the abstract (every corpus is thin almost everywhere). Topics come from the
deterministic operation; the one judgment you exercise is **ranking which thin topics
matter for this brief** — and that ranking is argued, not asserted.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| project brief | yes | The lens that defines "matters". |
| folders | no | Retrieval restriction (default: `notes/sources`, `notes/claims`). |
| threshold | no | Notes-per-topic floor below which a topic counts as thin (default from calibration). |

## Procedure

1. **Retrieve** the brief-relevant corpus with `qmd`; record the query trail.
2. **Model topics deterministically** — `cluster_model_topics(folder, …)`; the topic
   set, sizes, and outliers are the operation's verbatim. Missing cluster stack → report
   and stop (a coverage report without real topics would be confabulation).
3. **Threshold**: thin = below the note-count floor, or note-rich but **claim-poor**
   (sources held, nothing promoted — read claim presence off `cluster_build_graph()` +
   folder counts). Both kinds are listed, labeled differently.
4. **Rank by the brief** — the one LLM-judgment step: for each thin topic, why it
   matters to this brief (which argument leg it would carry), or why it doesn't
   (adjacent but out of scope). Out-of-scope thin topics go in a parking section, not
   the ranking.
5. **Write — gated.** The report to
   `notes/fleeting/maps/gap-report-<project>-<YYYY-MM-DD>.md`. If you considered any
   rejected directions, dead ends, or parked lenses that should prevent repeated work,
   write the companion trace note
   `notes/fleeting/maps/gap-report-<project>-<YYYY-MM-DD>-exploration-trace.md` before
   the card. Then raise ONE `gap` card in `inbox/` pointing at the report (a report's
   findings are one card, never N — ADR-54).

## Output contract

- The gap-report note: frontmatter `sources:` (query trail · folders · `params_echo` ·
  threshold used); the ranked thin-topic list (topic · size · claim presence · why it
  matters · what evidence would thicken it); the parked out-of-scope list.
- The optional exploration-trace note: `type: fleeting`, `lifecycle: proposed`,
  `origin: agent`, stored beside the report, with structured sections for each rejected
  direction: `direction`, `why_rejected`, `evidence_checked`, `retry_only_if`, and a
  link back to the report. It is project-local context, not a claim/source/hub, and is
  never auto-promoted into canonical knowledge.
- One `gap` card (schema `gap`, ADR-51 honesty body): `action` = "review the gap
  report; delegate `catalog-find-source` for the topics you accept";
  `argument_for` = the top-ranked gaps' stakes; `argument_against` = the honest
  rebuttal ("thin may be fine — topics 3–5 are background, not argument legs");
  `what_tipped_it`; `certainty`.

## Honesty rules

- Thin coverage is a fact, not a failure — the card must not pressure acquisition; the
  PI may rule a gap acceptable, and that closes it.
- The ranking argues from the brief, never from topic size alone; a tiny topic that
  carries the central claim outranks a large peripheral one.
- Claim-poor ≠ unread: distinguish "no sources" from "sources held, nothing distilled"
  — the remedies differ (find vs extract).
- Topics, sizes, and outliers are the operation's; you rank and narrate, never re-draw.
