---
status: deferred
created: 2026-05-31
---

# Classical method displacements

Tasks currently routed to an LLM where a classical (deterministic or hybrid) method does the job better — cheaper, faster, reproducible, and auditable. Each is a candidate displacement, not a scheduled item.

The underlying principle from `explanation/architecture/why-computational-methods.md`: **use the simplest tool that produces a reliable answer**. Scripts beat NLP beat ML beat LLMs on cost, speed, determinism, and auditability. The LLM enters only where residual judgment genuinely requires generation.

---

## 1. NLI-based contradiction detection

**What.** "Do these two claims conflict?" currently requires a human walk of backlinks or an LLM judgment. A natural-language-inference (NLI) model (e.g., `roberta-large-mnli`) over topically-near claim pairs returns entailment / contradiction / neutral as a calibrated three-way label, deterministically and locally. Contradiction is a classification task with a purpose-built model family — not an open-ended judgment. Claimed `contradicts` pairs are *proposed for human confirmation*, never auto-written.

**Trade-offs.** NLI is trained on general text; domain claims may need a similarity pre-filter and threshold tuning. False-merge risk at low confidence.

**Adoption trigger.** The human regularly wants to query "find claims that contradict X" and is resorting to manual backlink walks, *and* the vault has ≥ 200 claim notes with typed `contradicts` links (ADR-9 and ADR-16 are the prerequisite).

---

## 2. Learning-to-rank for triage

**What.** A learning-to-rank model (e.g., LightGBM LambdaRank) trained on the human's past keep/discard decisions produces a reproducible, personalized triage ordering — a deterministic ranker that sharpens as the override history grows. Replaces or cold-start-gates the LLM tournament in the triage queue.

**Trade-offs.** Needs ~hundreds of past triage decisions to train. Until then keep the scalar ordering or the LLM tournament as a cold start.

**Adoption trigger.** The human has made ≥ 300 triage decisions and notices the triage queue ordering feels generic or unconditional on their research priorities.

---

## 3. Claim-sentence classification

**What.** Locate claim / aspect sentences in a paper before handing to the LLM, using a rhetorical-zone classifier (CoreSC/ART-style, or citation + hedge + numeric heuristics). Reduces the LLM's input from full-paper to candidate sentences, lowering cost and improving precision. Enables agent-proposed candidate claim notes (see `discovery-loop.md §Agent-proposed candidate claim notes`).

**Adoption trigger.** Agent-proposed candidate claim notes are being piloted *and* the LLM's false-positive rate on non-claim sentences is causing meaningless candidates.

---

## 4. Classical prose metrics for export gate

**What.** Before the LLM-judge gate fires at export, run mechanical checks: Flesch–Kincaid readability, passive-voice ratio, citation density, n-gram repetition, sentence-length outliers. These flag *symptoms* cheaply; the LLM still owns coherence and tonal drift. Converts the export gate from pure-generative to hybrid.

**Adoption trigger.** The LLM-judge gate (see `measurement-and-verification.md`) is live and recurring false-alarms on structural issues are dominating the report.

---

## 5. Keyphrase extraction for tag candidates

**What.** KeyBERT or YAKE extracts candidate tags alongside the existing classifier, mapping extracted phrases onto the human's controlled vocabulary. Improves recall on tags the classifier missed.

**Adoption trigger.** The classifier is active for ≥ 3 months and the human notices recurrent vocabulary gaps (terms that should appear in `topic:` but don't because the training set didn't see them).

---

## 6. Discovery relevance scoring

**What.** Reuse the existing `[!suggestions]` weighted scorer (embedding similarity + citation-graph overlap + topic-tag overlap against `research-directions.md`) to rank nightly discovery candidates. Deterministic, auditable, no extra API calls.

**Adoption trigger.** The discovery loop (see `discovery-loop.md`) is live and morning triage time is > 15 minutes because candidates aren't pre-sorted by relevance.

---

## 7. Record linkage for entity deduplication

**What.** Use ORCID/OpenAlex IDs first, then string-similarity blocking, to deduplicate author and venue entities during Librarian ingest — instead of "ask the LLM if these refer to the same person."

**Adoption trigger.** Entity notes accumulate duplicate person or venue entries that the human notices while cleaning up the graph.
