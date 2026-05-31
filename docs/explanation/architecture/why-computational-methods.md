---
topic: architecture
---

# Computational methods: when Memoria uses LLMs vs classical methods

Every task Memoria performs is classified as **deterministic**, **hybrid**, or **generative**. The class determines the implementation method, the cost profile, and the audit shape. Per-agent specifics live in [profiles/](../profiles/).

## Classification

| Class | Definition | Method | Examples |
| --- | --- | --- | --- |
| **Deterministic** | Has a single right answer derivable from rules, regex, math, or graph algorithms. | Scripts, regex, classical ML, vector search, graph walks. | Citation token extraction, schema-version check, link suggestion ranking, similarity-check, find-duplicates, structural detectors, dashboard queries. |
| **Hybrid** | A deterministic step narrows the problem; an LLM handles the residual judgment on the narrow result. | Classical pre-filter + LLM on top. | `_proposed_classification` proposals (classifier first, LLM fallback), `cite-check` (embedding similarity first, LLM on ambiguous claims), `[!brief]` candidate selection + prose. |
| **Generative** | No fixed output; quality is judged subjectively or requires open-ended composition. | LLM-required. | Socratic conversation, Writer's `draft`, `counter-outline`, comparative-brief prose, synthesis writing. |

**The default placement test:** if there is a regex, a graph algorithm, or a similarity threshold that would produce the right answer most of the time, the task is **deterministic** or **hybrid** — not pure LLM. The LLM enters only where the residual judgment genuinely requires generation.

## Why this classification

A research vault accumulates tasks of two qualitatively different kinds. Memoria treats them differently — and naming the boundary explicitly is what keeps the design honest about cost, determinism, and what it can actually test. Without the classification, every task is reflexively routed to an LLM "because it's text"; with it, the LLM's role contracts to where its judgment is actually load-bearing.

## Decision criteria

When designing a new workflow or skill, choose the method class by asking five questions in order. The first "yes" pins the class:

1. **Can a regex, schema rule, or graph algorithm produce the answer?** → Deterministic. (Examples: citation token extraction, schema-version-mismatch detection, orphan note detection.)
2. **Can vector similarity over note embeddings produce a useful ranking?** → Deterministic. (Examples: similarity-check, find-duplicates, link-suggestion candidate ranking.)
3. **Can a small classifier trained on past human decisions produce a calibrated proposal?** → Deterministic with an LLM fallback for low-confidence cases. → **Hybrid.** (Examples: `_proposed_classification`, future classification confidence scoring.)
4. **Can a deterministic step narrow the candidate set before an LLM judges the remainder?** → Hybrid. (Examples: `cite-check` with embedding-pre-filter on claim-source matches.)
5. **Is the task open-ended generation — prose, dialogue, alternative outlines, creative comparison?** → Generative. LLM-required. (Examples: Socratic processing, draft synthesis, counter-outline.)

If none of the first four applies and the task isn't open-ended generation, it's a gap — the task probably doesn't need to be automated at all.

## The hybrid pattern

The most common Memoria pattern is **deterministic narrowing + LLM enrichment**. It keeps LLM cost bounded and most decisions auditable while preserving judgment-quality output where it matters:

```text
Deterministic step:  Reduce N candidates to K (where K ≪ N)
                              ↓
LLM step:            Generate, judge, or compose over the K
                              ↓
Result:              Audit-trail = deterministic step's output; final = LLM's
```

Concrete instances in Memoria:

- **`[!suggestions]` callout.** 5,000 notes → top-10 candidates by (embedding similarity + shared-citation graph + topic-tag overlap, weighted) → optional LLM prose for *why* each candidate is suggested. LLM works on 10 candidates, not 5,000.
- **`cite-check`.** A draft has 80 claims → citekey-resolution gives 80 candidate sources → embedding similarity gives a quick score per (claim, source) pair → LLM judges only the middle band (similarity 0.4–0.75); above is auto-clean, below is auto-fail.
- **`[!brief]` comparative read.** New source → top-5 most-comparable existing sources by shared citations + embedding similarity → LLM composes the comparative narrative across 5 sources, not the entire corpus.
- **`_proposed_classification`.** A new paper-note → small multi-label classifier produces topic/methods/study_design proposals → if classifier confidence > 0.85, accept; else fall back to LLM proposal.

The benefit isn't just cost. The deterministic step's output is *auditable* (it can show which sources contributed to the rank, what the similarity score was, why the candidate was selected). The LLM's output is qualitative — useful but opaque. The hybrid keeps the audit trail authoritative.

## Methods Memoria uses

Seven deterministic methods cover the bulk of Memoria's non-generative work: regex and rule-based scripts, vector embeddings + cosine similarity, classical clustering (HDBSCAN, k-means), topic modeling (LDA, NMF, BERTopic), small classifiers (logistic regression, gradient boosting, fine-tuned BERT), graph algorithms (BFS, PageRank, shortest path), and API calls. Two more — NLI (contradiction detection) and learning-to-rank (triage ordering) — are catalogued as candidates, not yet in use; see [§"Candidate displacements"](#candidate-displacements-where-the-llm-can-still-recede) and the toolbox.

**See [architecture/computational-toolbox.md](../../reference/architecture/computational-toolbox.md)** for the per-method catalog (what each is good for, where Memoria uses it, implementation notes, cost and determinism profile).

## Anti-patterns

These are patterns to avoid because they substitute LLMs for tasks that have deterministic answers:

- **"Ask the LLM if this paper is similar to that one."** Use cosine similarity over embeddings. LLM-as-similarity-judge is expensive, slow, and gives different answers on different runs.
- **"Ask the LLM to extract the citations from this draft."** Use regex `\[@[a-z0-9-]+(?:; ?@[a-z0-9-]+)*\]`. Citations are tokens, not prose.
- **"Ask the LLM to classify which topic this note belongs to."** Train a classifier on the human's past classifications. The LLM's classification is generic; the classifier's is *yours*.
- **"Ask the LLM to find the orphan notes."** Graph walk. The wikilink graph either has an edge or it doesn't.
- **"Ask the LLM if frontmatter looks valid."** Run the schema-check. Frontmatter validation is structural.
- **"Ask the LLM to confidence-score its own classification."** LLM self-reported confidence is uncalibrated — a 0.9 from an LLM is not a 90% probability of being right. Use the classifier's softmax output instead; that *is* a probability.
- **"Use the LLM for the audit trail."** The LLM's output is a recommendation, not the audit record. The deterministic step's output (similarity score, classifier probability, graph distance) is what should be logged for verdict-band and dashboard queries.
- **"Ask the LLM whether these two claims contradict each other."** Use a natural-language-inference (NLI) model — it returns entailment / contradiction / neutral as a calibrated label, deterministically and locally. Contradiction is a *classification* task with a purpose-built model family, not an open-ended judgment. (See the candidate displacement below.)
- **"Ask the LLM to rank the triage queue."** Train a learning-to-rank model on the human's past keep/discard decisions. The LLM's ranking is generic and drifts run-to-run; the ranker's is *yours* and reproducible.

The underlying mistake in all of these: asking an LLM to do work where the answer is *derivable*. LLMs are right for *generation*, not for *derivation*.

## Cost and audit implications

Adopting the hybrid pattern across Memoria changes the operational profile:

| Concern | LLM-everywhere | Memoria's hybrid approach |
|---|---|---|
| Per-action API cost | $0.01–$0.10 per routine task | $0–$0.01 per routine task; LLM only on ambiguous cases |
| Latency per routine task | 2–5s | <100ms for deterministic; same as LLM for the hybrid fallback |
| Test coverage | Hard — LLM outputs drift | Easy — deterministic steps have fixed expected outputs |
| Audit trail | "LLM said X" | "Similarity score 0.87, classifier confidence 0.92, three shared citations: [list]" |
| Calibration | LLM self-reported confidence is unreliable | Classifier softmax is a true probability |
| Privacy | Prompts leave the machine | Routine work runs entirely local |
| Reproducibility | Different runs give different outputs | Same input → same output, always |

The discovery loop's $1–3/day budget ([roadmap/future-directions.md §"The discovery loop"](../../project/roadmap/future-directions.md#the-discovery-loop)) is set assuming LLM-heavy ingest. Under the hybrid pattern, the same volume costs $0.20–$1/day. The savings compound: across a year, that's $300–$700 in API spend not paid.

## Per-task classification

Memoria's components, classified by method:

### Deterministic (no LLM)

| Component | Method | Reference |
|---|---|---|
| the Linter's structural detectors | Hash compare, file existence, regex, graph walk | [profiles/linter.md](../profiles/linter.md) |
| Schema validation | Frontmatter rule check | [profiles/linter.md](../profiles/linter.md) |
| Citation token extraction in `cite-check` | Regex | [profiles/verifier.md](../profiles/verifier.md) |
| `similarity-check` | Cosine similarity over embeddings | [profiles/verifier.md](../profiles/verifier.md) |
| `find-duplicates` | Embedding clustering / pairwise similarity | [profiles/verifier.md](../profiles/verifier.md) |
| `retraction-check` | API call + DOI match | [profiles/verifier.md](../profiles/verifier.md) |
| `enrich` metadata fetches | API calls (OpenAlex, PubMed, etc.) | [profiles/librarian.md](../profiles/librarian.md) |
| `ingest` type detection | Rule-based dispatch table | [workflows/README.md workflow Ingest](../../how-to/workflows/README.md) |
| Bib watcher, git hooks, cron triggers | Shell scripts | [architecture/README.md](README.md) |
| Audit-log analysis and verdict band rollup | Aggregation stats | [profiles/linter.md](../profiles/linter.md) |
| `cluster-map`, `scope-project` density, `gap-report` topic identification | HDBSCAN / BERTopic / LDA over embeddings | [profiles/mapper.md](../profiles/mapper.md) |
| `[!suggestions]` candidate ranking | Weighted scoring (embedding + citation + topic) | [obsidian-ui/callouts.md callouts](../obsidian-ui/callouts.md) |
| `[!brief]` candidate selection | Shared-citation + embedding similarity | [obsidian-ui/callouts.md callouts](../obsidian-ui/callouts.md) |
| Dataview dashboards | SQL-like queries over frontmatter | [obsidian-ui/README.md](../obsidian-ui/README.md) |
| MOC hub identification | PageRank / centrality over the wikilink graph | [profiles/linter.md](../profiles/linter.md) (graph-analyze) |
| Drift propagation enumeration (future) | Graph walk over wikilinks | [roadmap/README.md propagation debts](../../project/roadmap/README.md) |

### Hybrid (deterministic narrowing + LLM enrichment)

| Component | Deterministic step | LLM step | Reference |
|---|---|---|---|
| `_proposed_classification` proposal | Multi-label classifier produces calibrated proposal | LLM fallback for low-confidence cases (probability < 0.85) | [profiles/librarian.md](../profiles/librarian.md) |
| `cite-check` claim-source match | Embedding similarity per (claim, source) pair | LLM judges only middle band (0.4–0.75); above is auto-clean, below is auto-fail | [profiles/verifier.md](../profiles/verifier.md) |
| Inline callouts (`[!brief]`, `[!suggestions]`, `[!verification]`) | Candidate selection via weighted scoring (similarity + shared-citations + topic-tag) | Per-callout prose composition or explanation | [obsidian-ui/callouts.md](../obsidian-ui/callouts.md#how-the-callout-content-is-produced-deterministic-narrowing--llm-enrichment) — authoritative site for per-callout deterministic/LLM split, including weights |

### Generative (LLM-required)

| Component | Why LLM-required | Reference |
|---|---|---|
| Socratic conversation | Open-ended dialog, no fixed output structure | [profiles/socratic.md](../profiles/socratic.md) |
| Writer's `draft` command | Generative synthesis prose | [profiles/writer.md](../profiles/writer.md) |
| `counter-outline` | Creative diversity in outline alternatives | [profiles/writer.md](../profiles/writer.md) |
| `[!brief]` prose composition (within the hybrid) | Comparative narrative requires natural language | [profiles/mapper.md](../profiles/mapper.md) |
| `cite-check` ambiguous-band judgment (within the hybrid) | Semantic judgment when similarity is in the 0.4–0.75 middle | [profiles/verifier.md](../profiles/verifier.md) |
| Open-design rendering | Aesthetic and layout judgment over content | [external-agent-workspace.md](../../how-to/coder/external-agent-workspace.md) |

## Candidate displacements: where the LLM can still recede

The tables above classify Memoria's *current* components. Several tasks the design routes to an LLM — or has not yet specified — have a classical method that does the job better (deterministic, local, auditable) or narrows it to a hybrid. These are candidates, gated on felt need like any future-direction; none is shipped. Each obeys the design's rules: the deterministic step is the audit record, and where a human judgment remains (a contradiction to confirm, a draft to accept) the agent *proposes* and the human *decides*.

| Task in the design | Currently | Classical method | New class | Trade-off |
| --- | --- | --- | --- | --- |
| Contradiction / agreement between claims — [scenario-typed `contradicts` links](../../project/roadmap/future-directions.md#scenario-typed-retrieval), [contradictions dashboard (ADR-16)](../../project/decisions/16-contradictions-dashboard.md), gap-seeking | human-assigned (relation + dashboard now adopted, ADR-9/16) | **NLI** (`roberta-large-mnli` or similar) over topically-near claim pairs → entailment / contradiction / neutral | Deterministic (proposes; human confirms the link) | NLI is trained on general text; domain claims may need a similarity pre-filter and threshold tuning, or a light fine-tune |
| Triage ordering — [3.2 tournament ranking](../../project/roadmap/future-directions.md#tournament-ranking-for-triage) | LLM pairwise tournament | **Learning-to-rank** (LightGBM LambdaRank) on past keep/discard, over features already computed | Deterministic once trained; LLM only as cold-start | Needs ~hundreds of past triage decisions to train; until then keep the scalar ordering or the LLM tournament |
| Claim-sentence detection (Verifier claim-trace) + `_aspects.*` extraction ([Knows/MASSW](../../project/roadmap/future-directions.md#massw-aligned-paper-note-aspects)) | unspecified / planned LLM | **Rhetorical-zone / claim-sentence classifier** (CoreSC/ART-style, or citation + hedge + numeric heuristics) locates candidate sentences; LLM phrases the residual | Generative → **Hybrid** | The zoning classifier needs labeled sentences or a pre-trained scientific-text model |
| Export prose-check — [LLM-judge gate for export](../../project/roadmap/future-directions.md#llm-judge-gate-for-export) | planned LLM-only | **Classical prose metrics** (Flesch–Kincaid, passive-voice ratio, citation density, n-gram repetition, sentence-length outliers) for the mechanical half | Generative → **Hybrid** | Metrics flag *symptoms*, not whether the argument is wrong — the LLM still owns coherence and tonal drift |
| Tag / keyword candidates (Librarian `classify`) | classifier + LLM fallback | **Keyphrase extraction** (KeyBERT, YAKE) for candidate tags, alongside the existing classifier | Deterministic | Extracted phrases still need mapping onto the human's controlled vocabulary |
| Overnight `find` relevance ([1.1](../../project/roadmap/autonomy-progression.md) / [1.4 discovery harness](../../project/roadmap/autonomy-progression.md)) | reuse-or-LLM | Extend the existing **`[!suggestions]` weighted scorer** (embedding + citation-graph + topic overlap) to rank discovery candidates against `research-directions.md` | Deterministic | Cold-start weighting; tune against the AutoResearchBench-style discovery harness (1.4) |
| Author / venue disambiguation (Librarian `enrich`) | API + occasional LLM | **Record linkage** — ORCID/OpenAlex IDs first, then string-similarity blocking | Deterministic | Missing IDs fall back to fuzzy match, which carries a false-merge risk — keep the human in the loop for low-confidence merges |

**The two highest-value displacements** convert tasks the design currently frames as *judgment* into *derivation*:

- **NLI for contradiction detection** is the cleanest gap. "Do these claims conflict?" feels like an LLM question, but NLI is the purpose-built model family — it returns a calibrated three-way label, runs locally, and gives the same answer every run. It slots into the existing pipeline with no new judgment surface: embeddings (already computed) pre-filter to topically-near claim pairs, NLI labels them, and contradictions are *surfaced for the human to confirm* as a typed link — never auto-written. The contradictions dashboard and the `contradicts` relation type are now adopted human-set ([ADR-16](../../project/decisions/16-contradictions-dashboard.md) / [ADR-9](../../project/decisions/09-typed-relations-frontmatter.md)); this is what would make their *candidate proposer* real without an LLM in the loop.
- **Learning-to-rank for triage** mirrors the `_proposed_classification` story exactly: a model trained on the human's own past decisions produces a reproducible, auditable ranking, and (like the classifier) it sharpens as the override history grows. It can replace or cold-start-gate the LLM tournament in [3.2](../../project/roadmap/autonomy-progression.md).

Items 3 and 4 are *demotions from generative to hybrid* rather than full displacements: a deterministic step (sentence zoning; prose metrics) carries the mechanical load and the LLM contracts to the residual semantic judgment — the same narrowing the [hybrid pattern](#the-hybrid-pattern) already applies to `cite-check` and `[!suggestions]`.

## Implementation notes

For the practical details — embedding model selection (`bge-small-en` vs `all-MiniLM-L6-v2` vs `SPECTER2`), classifier training (when to start, when to retrain), the SKILL.md frontmatter where the method-class decision is encoded, and the `llm_backend` pilot-scoped pattern — see [architecture/computational-toolbox.md](../../reference/architecture/computational-toolbox.md#implementation-notes).

## Related design documents

- [profiles/librarian.md](../profiles/librarian.md) — uses classifiers + APIs + LLM-fallback for `_proposed_classification`.
- [profiles/mapper.md](../profiles/mapper.md) — uses clustering + topic modeling; LLM only for narrative composition.
- [profiles/verifier.md](../profiles/verifier.md) — uses embeddings + regex; LLM only for ambiguous claim-source matches.
- [profiles/writer.md](../profiles/writer.md) — generative, LLM-required.
- [profiles/socratic.md](../profiles/socratic.md) — generative, LLM-required.
- [profiles/linter.md](../profiles/linter.md) — fully deterministic.
- [obsidian-ui/callouts.md](../obsidian-ui/callouts.md) — hybrid pattern for `[!suggestions]` and `[!brief]`.
- [profiles/librarian.md](../profiles/librarian.md) — the classifier-with-LLM-fallback approach for `_proposed_classification` confidence scoring.
- [architecture/capability-stack.md model routing](../../reference/architecture/capability-stack.md) — when LLM calls are needed, route synthesis to Claude and cheap tasks (embed, classify, summarize) to cheaper models or local inference.
