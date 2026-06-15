---
title: Ingest routing
parent: Reference
---

# Ingest routing

The ingest engine (`src/.memoria/operations/processing/ingest`): the deterministic spine that turns a citekey into a draft `paper` catalog bundle, the Catalog outputs it plans, the uncertainty floor, and the recovery sweeps. The Librarian reaches it over the ingest MCP (`src/.memoria/mcp/ingest_mcp.py`) — its lane has no terminal — fills the two LLM holes, and performs the gated writes; the engine itself writes no vault notes.

---

## The pipeline

`src/.memoria/operations/processing/ingest/runner.py` chains four deterministic stages into a single **draft bundle**:

| Stage | Module | Does |
| --- | --- | --- |
| Tier-0 capture | `ingest_paper.py` | Identity + route + captured frontmatter from the local `.bib` alone — the offline, nothing-lost floor. |
| Tier-1 resolve/merge | `resolve_merge.py` | Semantic Scholar + OpenAlex (co-primary) + Crossref, merged per-field best-source-wins **with provenance**; references = the union across sources, deduped by DOI. |
| Tier-1 classify | `classify.py` | `research_area` (and a `methodology` facet when derivable) from the OpenAlex topics already in the merged payload — automated, audited, flag-on-ambiguity ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)). Also proposes project membership from the optional `.memoria/project-hints.yaml` ([ADR-15](../adr/15-project-membership-from-topic-hint.md)). No extra network call; without enrichment it is a no-op. |
| Tier-1 extract | `extract.py` | Full text, pre-extracted-first: PMC JATS → local Zotero PDF via pymupdf4llm. A deterministic coherence check (chars/page, replacement-char ratio, word ratio) gatekeeps so only good text reaches the model; non-English text is flagged, never auto-failed. |
| Tier-1 link | `link.py` | The knowledge-graph plan: entity find-or-create keyed on stable IDs (ISSN / ORCID / ROR — never name-merged) + cites edges by local DOI/arXiv match. |

The bundle arrives **with two holes** the Librarian fills: `_proposed_classification` (LLM #1 — its `projects` sub-key is pre-filled deterministically from the optional project hints, [ADR-15](../adr/15-project-membership-from-topic-hint.md)) and the `[!brief]` comparative read (LLM #2). `ingest_pipeline(citekey, enrich=True, pdf_path="")` is the MCP tool; without `enrich` only Tier-0 runs.

### Catalog outputs

The link plan is what populates the Catalog ([ADR-52](../adr/52-links-vs-relationships.md)):

- **Entities** — find-or-create records in `catalog/` (`paper`, `person`, `organization`, `venue`, `dataset`, `repository`), keyed on the stable ID so same-named entities never merge. Entities without a stable ID are recorded by name only, never node-created.
- **Relationships** — the engine writes only the **given** `relationships` edges on those entities (`cited_by`, `authored_by`, `published_in`, …), applied bidirectionally by the worker; it never writes the PI's authored `links:`. The field contract behind the given-vs-authored split is in [Frontmatter fields](frontmatter.md).

---

## The uncertainty floor

The engine never merges identities silently ([ADR-56](../adr/56-extraction-uncertainty-flag.md)). `resolve_merge.py` scores **cross-source identity agreement** (title + year across the sources that resolved) in `[0,1]`; the floor comes from `src/.memoria/schemas/calibration.yaml` (`entity_resolution.confidence_floor: 0.85`, drift-bound — recalibrate on model/source-version change).

Below the floor, the bundle carries a `flag_needed` block instead of a silent best-source-wins merge: the Librarian raises a **near-tie `flag` card** in the Inbox ("Identity disagreement on `<citekey>`", with the agreement score and the disagreements), and the PI decides. One source found = trusted (1.0) — the floor measures _disagreement_, not coverage.

---

## Automated classification

classify is **not a gate** ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)): low-stakes metadata a human would rubber-stamp is automated, audited, and correctable. `classify.py` reads the **scored OpenAlex topics already in the enrichment payload** (no new network call), rolls them up to their subfield (the research-area granularity, best score per area), and decides:

- **Clear winner** — the top score clears the floor _and_ beats the runner-up by the near-tie margin → `research_area` is applied silently. A `methodology` facet is applied whenever it is derivable from the S2 publication types (Review, MetaAnalysis, ClinicalTrial, CaseReport, Dataset — deterministic, independent of topic ambiguity).
- **Genuine ambiguity** — below the floor or within the margin → the field **stays unset** and ingest raises **one** Inbox `flag` card: what was ambiguous and the top candidates with scores, never a verdict (the [ADR-51](../adr/51-inbox-category-and-honesty-card.md) honesty rules).
- **No data** (enrichment off, or no topics resolved) → a no-op.

The thresholds live beside the entity-resolution floor in `src/.memoria/schemas/calibration.yaml`, under the same drift-bound discipline:

| Knob | Default | Means |
| --- | --- | --- |
| `classify.confidence_floor` | `0.6` | Below this top-candidate score, nothing is applied. |
| `classify.near_tie_margin` | `0.15` | The top candidate must beat the runner-up by at least this much. |

Every applied or flagged decision appends **one JSONL audit line** to `system/logs/classify.jsonl` (timestamp, run id, citekey, decision, the candidates with scores, the reason, and the thresholds in force) — the audit trail that makes the automation correctable: the PI edits the frontmatter, never approves a card.

### Project membership proposal ([ADR-15](../adr/15-project-membership-from-topic-hint.md))

When an optional `.memoria/project-hints.yaml` exists ([Configure project hints](../how-to-guides/setup/configure-project-hints.md)), the classify stage also **proposes** project membership by simple overlap: each project's `primary_topics` is scored against the paper's OpenAlex topic names and subfields (both kebab-case normalized; a hint matches a signal when equal to it or when all the hint's tokens appear in it). Every project with at least one overlapping hint topic is proposed, ranked by overlap count, into `_proposed_classification.projects` — confirmed or corrected by the PI at triage, **never** applied to the `projects` field. Each decision (proposed or no-match) appends one `stage: project_hints` line to the same `system/logs/classify.jsonl`, carrying the candidates with their matched topics and overlap counts ([ADR-51](../adr/51-inbox-category-and-honesty-card.md) honesty — counts, not confidence). An absent hints file means fully manual project tagging (a silent no-op); a malformed one warns once on stderr and degrades to manual.

---

## Derived artifacts

The ingest MCP persists the un-gated derived artifacts the agent can't:

| Artifact | Path | Notes |
| --- | --- | --- |
| Full-text extract | `.memoria/data/extracts/<citekey>.md` | Outside the Librarian's write lane; the paper note's `extract_path` points here (the `extract-path-broken` detector checks it). |
| Capture-intake anchor | `system/logs/capture-intake.jsonl` | One append-only line per capture, written **before** the gated note write — the durability anchor. |
| Classify audit | `system/logs/classify.jsonl` | One append-only line per classify decision (applied or flagged) and per project-membership proposal (`stage: project_hints`, [ADR-15](../adr/15-project-membership-from-topic-hint.md)) — see Automated classification above. |

---

## Recovery sweeps

Re-ingest and retraction maintenance are deterministic sweep engines rather than ingest stages. Their command-level contract lives in [Sweeps](sweeps.md).

---

## Frontmatter written at ingest

| Field | Value |
| --- | --- |
| `type` / `lifecycle` | `paper` / `current` from creation — Catalog facts don't queue; the pending classification lives in `_proposed_classification` + an Inbox card, not in the lifecycle. |
| `citekey`, `title`, `doi`, `authors`, `year`, `venue`, `url` | From the merged record, with per-field provenance. |
| `relationships` | The given edges from the link plan. |
| `research_area`, `methodology` | Applied by the automated classify stage when the decision is clear; left unset (plus one Inbox flag) on genuine ambiguity. |
| `extract_path`, `pdf_uri` | The extract store path and the Zotero PDF URI. |
| `_proposed_classification` | The Librarian's proposal (LLM hole #1), promoted by the PI at classify; its `projects` sub-key is the deterministic [ADR-15](../adr/15-project-membership-from-topic-hint.md) hint-overlap proposal. |

---

## Related

- The schemas and field kinds these notes must satisfy: [Frontmatter fields](frontmatter.md)
- The lane that runs the pipeline: [Profile capabilities](profiles.md)
- The crons that wire the sweeps: [Installer (bootstrap)](installer.md)
- The cards the sweeps and flags land in: [Kanban board reference](kanban-board.md)
