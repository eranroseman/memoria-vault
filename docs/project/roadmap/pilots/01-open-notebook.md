---
topic: roadmap
---

# Pilot E1 — Open Notebook as `comparative-brief` LLM back-end

**Status.** Spec drafted; not yet implementing. Activate when Phase 3 (Hermes profiles) is past the test-each-profile-in-isolation step and Mapper's `comparative-brief` is generating its first real briefs.

Pilots are *in-progress experiments with explicit rollback criteria* — architecturally distinct from Phases (committed sequential work) and [Future directions](../future-directions.md) (deferred with rationale). A pilot has a defined scope, a hypothesis about what it gains, success criteria that decide whether it's adopted, and rollback criteria that decide when it's abandoned. The default is rollback; adoption is the burden-of-proof choice.

## Goal

Replace the generic LLM call that composes the `comparative-brief` narrative ([profiles/mapper.md](../../../explanation/profiles/mapper.md)) with a call to a self-hosted [Open Notebook](https://github.com/lfnovo/open-notebook) instance. Keep the deterministic candidate-selection step (top-5 by shared-citation + embedding similarity + topic-tag overlap) unchanged. Only the LLM step that composes the narrative changes back-end.

## Hypothesis

Open Notebook's source-grounded RAG produces comparative briefs with:

1. *Better citation accuracy* — claims in the brief cite specific paper-notes that actually support the claim, rather than generic-LLM hallucinated paraphrases.
2. *Sharper "overlaps with / may contradict / new construct" judgments* — Open Notebook's bundle-scoped reasoning is more disciplined than generic-LLM open-ended composition.
3. *Lower human manual-edit rate* — humans amend the brief less often before accepting it.

If the hypothesis holds, expand the pattern (Pilot E1 → broader E or alternative integrations). If it doesn't, roll back to generic-LLM and document why.

## Scope (deliberately narrow)

- *Only* the `comparative-brief` skill. Not `scope-project`, not `gap-report`, not `cluster-map`.
- *Only* on Mapper. Not on any other profile's LLM steps.
- *Only* the LLM-composition step. Deterministic candidate selection stays unchanged.
- *Reversible at the skill level* — see "Skill-level back-end declaration" below.

The pilot is a *partial implementation* of skill-level back-end declaration — but only for one skill, with a hardcoded backend choice. If the pilot succeeds, the next move is to lift the back-end choice into SKILL.md frontmatter and apply it to other skills. If it fails, the pattern dies in one place rather than several.

## Skill-level back-end declaration

Add a `llm_backend:` field to the `comparative-brief` skill's SKILL.md frontmatter:

```yaml
---
name: comparative-brief
profile: Mapper
llm_backend: open-notebook    # values: generic | open-notebook
llm_backend_fallback: generic # values: generic | none
---
```

- `llm_backend: generic` (default if field absent) — current behavior; uses whichever LLM the profile is configured for.
- `llm_backend: open-notebook` — pilot behavior; routes the LLM composition step through Open Notebook's API.
- `llm_backend_fallback: generic` — if Open Notebook is unreachable, fall back to generic LLM and log the fallback. Setting this to `none` makes the skill fail loudly when Open Notebook is down (use only for testing).

Switching between back-ends is a one-line edit; no recompilation of the profile is needed.

## Implementation outline

1. Human opts in by setting `llm_backend: open-notebook` on the skill (default stays `generic`).
2. When `comparative-brief` fires (file watcher on new paper-note in `20-sources/01-papers/`):
   - **Candidate selection (deterministic).** Mapper runs the existing step, selecting top-5 candidate sources by shared-citation overlap + embedding similarity + topic-tag intersection.
   - **Bundle preprocessing.** Mapper assembles a source bundle from the new paper-note + the 5 candidates, applying the preprocessing operations below to each note. The output is clean prose suitable for source-grounded RAG.
   - **Open Notebook session.** Mapper POSTs to Open Notebook's API to create an *ephemeral* notebook with the 6 preprocessed sources.
   - **Prompt.** Mapper prompts Open Notebook: "Compose a comparative read of the new source against the others. Use the format: 'Overlaps with: X, Y. May contradict: Z. New construct: ...'. Cite each claim back to a specific source by its file path."
   - **Citation rewriting.** Open Notebook returns prose with inline citations to the bundle. Mapper post-processes the citations: file-path citations are rewritten as Memoria wikilinks (`[[citekey]]`) using the paper-note frontmatter's `citekey` field. Citations that don't resolve to a bundle member become plain text (and are logged as `citation_resolution_failure`).
   - **Callout write.** Mapper writes the `[!brief]` callout to the top of the new paper note via the policy MCP (standard write, normal audit trail).
   - **Cleanup.** Mapper DELETES the ephemeral Open Notebook notebook. The value was the synthesis, not the persistence — Memoria's vault is the source of truth, the notebook was scratch.
3. If Open Notebook is unreachable and `llm_backend_fallback: generic`, fall back silently and log the fallback to `00-meta/02-logs/pilot-e1-fallbacks.jsonl`.

## Bundle preprocessing operations (sub-step of 2 above)

Memoria paper-notes are *not* suitable for direct upload to RAG systems. They contain heavy non-content metadata that a model will mistake for source content if uploaded raw:

- Frontmatter (15+ fields per paper-note: `citekey`, `doi`, `zotero_uri`, `pdf_uri`, `extract_path`, `lifecycle`, `pub_status`, …).
- `_proposed_classification` and `_enrichment` blocks inside HTML comments (`<!-- ... -->`) — a model treating these as content will cite back to "topic: receptivity-detection" as if it were a finding.
- Dense wikilinks (`[[mamykina2010sense]]` references) — without context, the model sees citekey tokens as opaque strings.
- Embeds (`![[figure.png]]`) — references to files outside the bundle.
- Inline tags (`#receptivity-detection`) — treated as content text.

Mapper's preprocessing strips these to produce clean prose. The operations:

| Operation | What it does | Why |
| --- | --- | --- |
| Strip frontmatter | Remove the `---`-fenced YAML at the top of each note. | Frontmatter is metadata, not source content. |
| Strip HTML comment blocks | Remove `<!-- ... -->` blocks including `_proposed_classification` and `_enrichment`. | These are agent-managed metadata, not findings. |
| Resolve wikilinks | Replace `[[citekey]]` with the resolved target's title (or filename if title is unavailable). | Bare citekeys carry no meaning to the RAG model; resolving them to titles preserves the citation semantics. |
| Strip embeds | Remove `![[file]]` references. | The referenced file isn't in the bundle. |
| Strip inline tags | Remove `#tag` tokens from prose. | Tag-as-content is noise. |
| Collapse blank lines | Reduce consecutive blank lines to one. | Cosmetic; improves bundle readability. |
| Prepend vault path | Add a `# <vault-relative path>` heading at the top of each note in the bundle. | Gives the RAG model a stable identifier to cite back to, which Mapper's citation-rewriting step then resolves to a wikilink. |

**Reference implementation: Context Pack for NotebookLM plugin.** The [Context Pack for NotebookLM](https://obsidian.md/plugins?id=context-pack-for-notebooklm) Obsidian plugin implements exactly these preprocessing semantics. It operates human-side (manual GUI invocation in Obsidian) and outputs cleaned markdown bundles ready for upload. Mapper's preprocessing should produce **byte-equivalent output to Context Pack** when run on the same inputs. Use the plugin as:

1. The reference implementation when implementing Mapper's preprocessing step. The plugin's algorithm is open-source and small; Mapper's reimplementation is straightforward Python (~100 LOC).
2. A manual human tool for *non-E1* preprocessing tasks — for example, when the human wants to build an upstream-triage bundle without going through Mapper. Human runs Context Pack on selected notes → ZIP bundle → upload to a notebook for triage exploration.

Treating the two as separate runtimes of the same algorithm keeps Mapper independent of Obsidian plugin availability (the daemon doesn't depend on the plugin being installed or invoked) while giving the human a working manual tool for the same job.

**Acceptance test for the preprocessing step.** Pick 3 representative paper-notes (one minimal with just frontmatter and 2 paragraphs of prose; one rich with `_proposed_classification`, `_enrichment`, and 10+ wikilinks; one with embeds, inline tags, and HTML comments). Run them through both Context Pack and Mapper's preprocessing. Outputs should diff to zero, modulo whitespace. If they don't, Mapper's preprocessing has a bug; reconcile before activating the pilot.

## Fallback behavior

- *Open Notebook daemon not running:* fall back to generic LLM, log fallback, surface the count in the [drift-watch dashboard](../../../explanation/dashboards/drift-watch.md).
- *Open Notebook reachable but returns malformed output:* fall back to generic LLM, log as `malformed_output_fallback`, flag the specific Open Notebook session for inspection.
- *Open Notebook timeout (>30s):* fall back to generic LLM, log as `timeout_fallback`.
- *Open Notebook returns hallucinated citations (citations that don't resolve to bundle members):* Mapper post-processes citations; unresolvable ones become plain text rather than wikilinks. Log as `citation_resolution_failure`.

The pilot must never fail the comparative-brief outright — fallback always exists. This protects the human's daily workflow from infrastructure issues with the experimental back-end.

## Success criteria

Human-judged quality. For each brief generated under the pilot, the human logs one of four ratings in a per-brief log (`00-meta/02-logs/pilot-e1-quality.jsonl`):

- `useful_as_is` — the brief was accepted into the paper note without edits.
- `minor_edits` — accepted after small textual touch-ups; the substance and citations were correct.
- `rewrote_significantly` — kept the citations or framing but rewrote most of the prose.
- `useless` — discarded entirely; the brief did not contribute.

At the review point, compute the adoption ratio:

```text
adoption_ratio = (useful_as_is + minor_edits) / total_briefs
```

**Adopt** if `adoption_ratio > 0.70` — at least 70% of briefs needed at most minor touch-ups.

**Roll back** otherwise — keep generic-LLM as the back-end and document why Open Notebook didn't help (in the rollback log under the same path, with a per-brief rationale where the rating was `useless` or `rewrote_significantly`).

**Why human-judged quality rather than behavioral or citation-based signals.** Edit-rate is a proxy that misses "useful but rewrote in my own voice" (which is success, not failure). Citation-resolution rate is countable but a brief with perfectly-resolving citations can still be a poor read. The actual goal is research-quality judgment from the human; measuring it directly is honest about what success means. The cost is the per-brief logging effort, which is acceptable at the pilot's scale (~50 briefs).

## Rollback criteria

Any of:

- Open Notebook is unmaintained for 6 months (no commits, no security updates on the upstream repo).
- Fallback rate exceeds 25% over a 4-week window (Open Notebook is too unreliable to depend on).
- Citation-resolution failure rate exceeds 20% (hallucinated citations to non-bundle sources happen too often).
- Cost exceeds the budget ceiling below.
- Human chooses to abandon for any other reason. Pilots are abandoned at the human's discretion; documenting *why* is required, justifying *not abandoning* is not.

## Cost ceiling

- *Infrastructure:* Open Notebook self-hosted via Docker on the primary machine. No new cloud spend. Existing compute (CPU and the human's GPU for Ollama-backed inference) covers it.
- *Compute:* approximately one Open Notebook call per new paper note ingested. At the corpus growth rate of ~5 papers/week, that's ~20 Open Notebook calls/month. Each call processes ~6 source bundles; latency 5-30s; runs on local Ollama with the human's existing model.
- *Budget ceiling:* $0/month for cloud spend. The pilot's marginal cost is electricity for local GPU inference. If the human switches Open Notebook to a cloud LLM back-end (BYOK), cap that at $5/month.

## Review point

Volume-based: evaluate after **50 comparative-briefs** have been generated under the pilot.

Rationale: 50 is large enough that the adoption ratio is statistically meaningful (binomial confidence interval ~±13 percentage points at 70%), and it's not calendar-bound, so the pilot can't drag on through low-research periods or close prematurely during high-activity ones. Volume tracks the actual exposure to the experimental back-end.

At the corpus growth rate of ~5 papers/week, the pilot will reach 50 briefs in approximately 10 weeks. If the rate is faster or slower, the review point moves accordingly — but it always triggers on volume, not calendar.

If the human wants to abandon earlier, they can: rollback at the human's discretion is documented as an explicit option above. Adoption, however, waits for the 50-brief threshold — premature adoption based on a small sample is exactly the failure mode this gate prevents.

## Pilot tracking

The dispatcher counts `comparative-brief` invocations where `llm_backend: open-notebook` was active and surfaces the count on the [drift-watch dashboard](../../../explanation/dashboards/drift-watch.md). When the count crosses 50, a card is automatically created on the human's queue with `task: review-pilot-e1` and `assignee: memoria-linter` (since the Linter does pilot-tracking metadata). The card carries a link to the pilot-quality log for review.

## What this pilot doesn't decide

- It doesn't decide whether Open Notebook should be used for *other* hybrid LLM steps (Verifier's middle band, Librarian's classifier fallback, inline callout production). Those are separate decisions, separate pilots if pursued.
- It doesn't decide whether to adopt broader skill-level back-end declaration across the system. The pilot uses a hardcoded skill-frontmatter field; broad adoption would require extending the SKILL.md spec and Hermes runtime support — out of scope here.
- It doesn't decide whether Open Notebook is suitable for downstream learning artifacts. That's a parallel decision the human can make independently.

## Why this is a pilot, not a Phase or Future direction

- *Not a Phase:* phases are committed sequential work that has to happen for the system to function. E1 is optional — Memoria works correctly with generic-LLM comparative briefs.
- *Not a Future direction:* future directions are deferred-with-rationale because the prerequisite conditions aren't met yet. E1's prerequisites are met (Mapper exists, Open Notebook is mature enough, the hybrid-pattern abstraction is in place); what's missing is *evidence that the substitution helps*.
- *A pilot:* time-bounded experiment, explicit rollback criteria, decision-by-evidence. The human either adopts the pattern after seeing it work, or rolls it back without architectural debt.
