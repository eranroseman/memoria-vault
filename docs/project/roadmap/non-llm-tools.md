---
topic: roadmap
---

# non-LLM tools

The principle worth holding throughout: **use the simplest tool that produces a reliable answer.** Scripts beat NLP beats ML beats LLMs on cost, speed, determinism, and auditability — but each gives up some flexibility. The art is matching the tool to the job's actual complexity, not the job's surface complexity.

---

## Layer 1: Pure scripts (regex, file ops, deterministic logic)

These are jobs where the right answer is *defined,* not inferred. No model needed.

**Linter's structural detectors (M1-M8).** Profile-install drift, vault-hash drift, skeleton drift, dashboard-field drift, command-vocab drift, plugin-config drift, orphan working files, broken extract paths. Memoria's docs already specify these as "deterministic, zero-LLM" — and they should stay that way. These are diff operations on known structures. A 50-line Python script catches all of them.

**Tag normalization.** `#JITAI` ↔ `#jitai` ↔ `#just-in-time-adaptive-intervention`. Build a canonical map; apply it. No LLM should ever touch this — it's a `str.lower()` plus an alias dictionary.

**Frontmatter validation.** Schema check: does this `claim-note` have `id`, `type`, `created`, `maturity`? Are types correct? Are required cross-references resolvable? JSON Schema or Pydantic. Microseconds.

**Link health.** Broken wikilinks, orphan notes, circular MOC references, dead Zotero citekeys. Graph operations on the link structure. NetworkX or plain BFS.

**Filename and path enforcement.** Does this file live in the right lifecycle folder? Does its name match its citekey or its slug? Pure path manipulation.

**Citation key extraction and validation.** Pull `[@citekey]` patterns; verify each citekey exists in the Zotero database. Regex + database lookup.

**Audit log analysis.** Deny rate per lane, drift per agent, retry distributions. Group-by aggregations over `audit.jsonl`. Pandas or even `jq`.

**Stale fleeting detection.** Files in `10-inbox/01-fleeting/` older than N days. `os.stat()`. Microseconds.

**Date and time normalization.** Standardize timestamps, compute deltas, detect missing dates. Pure datetime operations.

**Word count and length checks.** "Notes >800 words may want splitting." Trivial.

Roughly **30-40% of what we've discussed as agent work is actually script work.** That's not a criticism — agents are useful precisely *because* the boundary between scripts and reasoning is hard to see in advance. But once you've identified a job, if it's deterministic, demote it to a script.

---

## Layer 2: Classical NLP (no neural networks)

Jobs where you need linguistic processing but not "understanding." These are decades-old techniques that work well, fast, locally.

**Named entity recognition for source notes.** spaCy's `en_core_web_sm` extracts PERSON, ORG, GPE, DATE in milliseconds. Use it to:

- Pull author names from PDF text for verification
- Extract institutional affiliations
- Identify study locations
- Find dates mentioned in abstracts (study period, publication, etc.)

spaCy isn't LLM-accurate but it's 100x faster and good enough for metadata extraction. The LLM is overkill.

**Keyword extraction.** YAKE, RAKE, or TextRank for "what are this paper's key concepts?" Useful for auto-tagging during ingest. Memoria's Librarian could run YAKE on a source's abstract, propose 5-10 candidate tags, and let you confirm. No LLM needed.

**Sentence segmentation.** Breaking a paragraph into discrete claims for claim-tracing. NLTK or spaCy. Hard to beat with an LLM, and LLMs sometimes get sentence boundaries wrong in academic prose because of citation interrupters.

**Stemming and lemmatization.** "therapeutic alliance" / "therapeutic alliances" / "alliance" should match. Porter stemmer. 1970s technology, still optimal.

**N-gram matching for citation context.** Finding which sentences contain citation markers, what context they appear in. Regex over tokenized text.

**Stopword removal and TF-IDF.** For cluster cartography, you want to identify the distinctive terms in a cluster of notes. TF-IDF with stopwords removed is the right tool. No LLM needed.

**Edit distance for fuzzy matching.** Detecting near-duplicate notes, matching slightly-misspelled author names, finding citekey typos. Levenshtein distance.

**Language detection.** Confirming a note is in English (or in the right language). FastText's language ID. Microseconds.

The Librarian profile, in particular, could do most of its ingest work with classical NLP and only fall back to an LLM for things that genuinely require it.

---

## Layer 3: Embeddings (transformer-based but lightweight)

This is where things blur, because embeddings are technically neural — but they're *not* LLMs in the inference sense. A pre-trained embedding model runs cheaply, locally, and produces deterministic outputs from a given input. They're the right tool for similarity work.

**Link suggestions.** "Which existing notes are similar to this new one?" Embedding similarity beats keyword matching for semantic relatedness. Smart Connections does this; you can also use sentence-transformers (`all-MiniLM-L6-v2` runs on CPU, fast, free). Output: top-N candidates. Librarian surfaces them; you approve.

**Cluster detection for cartography.** Embed all claim notes; cluster with HDBSCAN or k-means. Surface emergent clusters that haven't been named yet. No LLM needed for cluster *detection*; you only need an LLM (or your own judgment) to *interpret* what a cluster is about.

**Deduplication.** Are these two notes saying the same thing? Embedding similarity above threshold → flag for review. Pure vector math.

**Comparative reading briefs.** "Which existing notes overlap with this source?" Embed the abstract, retrieve top-K nearest neighbors from your corpus. This is RAG without the G — just retrieval. Smart Connections or a custom pipeline.

**Topic drift detection.** Compare embeddings of recent notes against historical clusters. Surface "this new note is far from anything you have" as a signal — either it's novel or it's misfiled.

**Cross-language source matching.** If a Hebrew or Spanish source comes in, embeddings can match it to English-language notes on the same topic. Multilingual embedding models handle this well; an LLM is overkill.

Embeddings are the unsung workhorse here. They handle "is X like Y?" questions at scale and cheaply. Reserve LLMs for "what does X mean?" or "should X be in the corpus?" — questions embeddings can't answer.

---

## Layer 4: Traditional ML (supervised classification on labeled data)

Jobs where you have or can produce a labeled dataset and want fast, calibrated predictions.

**Source triage classification.** "Is this paper relevant to my scoping review?" Train a logistic regression or gradient-boosted tree on your historical accept/reject decisions over abstracts. Features: TF-IDF vectors, embedding vectors, author network features, journal venue. Once trained, classification is microseconds and you can inspect feature importance. Much better than asking an LLM "is this relevant to my work" because it's *learned from your actual decisions.*

**Note type classification.** Given a fleeting note's content, predict whether it's destined to become a source-note, claim-note, or reference-note. Lightweight classifier. Output: probabilities → Librarian routes accordingly.

**Maturity prediction.** Given a claim-note, predict its maturity state (seedling/budding/evergreen). Trained on hand-labeled examples. Features: link count, age, edit frequency, reference count. Classical ML excels here because the features are tabular.

**Section classification in drafts.** Given a paragraph, predict whether it's introduction / methods / results / discussion. Useful for Verifier to know which claims need which kind of evidence.

**Reading time / complexity estimation.** Predict whether a source will be a quick read or a deep one. Helps prioritize the reading queue. Trained on your own historical patterns.

**Spam / quality filtering on auto-discovered sources.** If the Librarian's discovery loop actively discovers papers from arXiv or Google Scholar, a classifier filters out low-quality results before they reach the Kanban. Trained on your historical "this was junk" signal.

The pattern: **anywhere you make a repeated binary or categorical decision with consistent criteria, you can train a classifier on your own decision history.** Costs nothing once trained, runs instantly, can be inspected for fairness and feature importance. LLM use here is wasteful — it ignores the fact that *you've labeled hundreds of examples already* by virtue of how you've used the system.

---

## Layer 5: Specialized non-LLM tools

Worth flagging a few specific tools that solve specific problems better than any LLM:

**GROBID** for academic PDF parsing. Extracts structured metadata (authors, affiliations, references, sections) from messy PDFs. Trained specifically on academic documents. Far better than asking an LLM to "extract the bibliography from this PDF."

**AnyStyle** for parsing reference strings. Given a raw bibliography line, returns structured data. Trained on millions of references.

**PubMed / OpenAlex APIs.** When Librarian needs metadata for a paper, the right move is API call, not LLM inference. Faster, free, authoritative.

**Better BibTeX hooks.** Citekey generation, duplicate detection, library management. Zero LLM needed.

**Pandoc.** Format conversion (Markdown → DOCX, PDF, HTML). Deterministic. Don't use an LLM for this.

**dataview-publisher / Quartz.** Static site generation from vault content. Templating, not generation.

**Ollama with small models for local classification.** If you do want a "model" for classification, a 1-3B parameter local model running on your 4060 Ti is appropriate. It's not an LLM in the API sense — it's a specialized classifier that happens to use the transformer architecture.

---

## Where LLMs actually belong

After all that, the residual use cases that *do* need an LLM:

- **Socratic processing** — asking good questions requires general reasoning
- **Counter-outline generation** — proposing alternative framings is creative work
- **Lens reading** — applying a theoretical framework requires understanding
- **Drafting prose** — generation is the LLM's strongest suit
- **Comparative reading brief authorship** — synthesizing "how does this compare to your existing notes" requires understanding both
- **Verification reasoning** — "does this claim actually follow from this note?" is judgment, not pattern-matching
- **Skill execution where flexibility matters** — when the task is "process this novel input intelligently," an LLM is right

The pattern: **LLMs for reasoning, generation, and judgment. Scripts/NLP/ML for everything else.**

A useful test: if I gave you 200 examples of the input-output pairs for a task, could you imagine writing rules or training a classifier that would handle 90% of cases? If yes, don't use an LLM. If no — if the task genuinely requires understanding novel content each time — LLM is right.

---

## A redesign of Librarian with this in mind

To make this concrete, here's what Librarian actually does, decomposed by tool:

| Operation | Tool | Why |
|---|---|---|
| Fetch DOI metadata | API (Crossref/OpenAlex) | Authoritative |
| Generate citekey | Better BibTeX | Deterministic |
| Extract PDF text | GROBID + pdfplumber | Specialized |
| Detect language | FastText | Trivial |
| Extract named entities | spaCy | Fast, good enough |
| Propose tags | YAKE keyword extraction | Cheap, inspectable |
| Find similar notes | Embedding retrieval | Right tool |
| Classify relevance | Trained classifier | Learned from your decisions |
| Generate comparative brief | **LLM (Sonnet)** | Genuine synthesis |
| Suggest links | Embedding similarity + threshold | Cheap |
| Update link graph | Script | Pure file op |
| Write to audit log | Script + policy MCP | Required |

Look at that — **one LLM call** in the entire ingest pipeline. The rest is scripts, APIs, NLP, and embeddings. Librarian becomes 100x faster, 50x cheaper, and far more debuggable than a "use the LLM for everything" design.

---

## What this means for the architecture

Two architectural implications worth naming:

**1. Profiles shouldn't be defined by "they use an LLM." They should be defined by what they accomplish.** Librarian might use an LLM 10% of the time and scripts 90%. That doesn't make it less of a profile — it makes it a *better* profile. The Hermes profile abstraction handles tool dispatching; the LLM is one tool among many.

**2. The skill libraries should explicitly mix tool types.** A `link-suggester` skill might be 90% embedding code and 10% LLM polish. A `claim-tracer` skill might be 80% script-based traversal and 20% LLM judgment for ambiguous traces. Don't write skills that are "prompt an LLM"; write skills that orchestrate the right tool for each step.

The deeper point: **the LLM is a co-processor, not the CPU.** It's expensive, slow, non-deterministic, and inappropriate for most computational work. Use it for what it's uniquely good at — reasoning over novel input — and use the rest of the toolkit for everything else.

---

## A pragmatic starting point

If you're already designing Memoria, the highest-leverage moves are:

1. **Build the structural detectors (M1-M8) as pure scripts first.** Don't let "the Linter is an agent" trick you into using an LLM for what's actually diff logic.

2. **Use embedding-based retrieval for all "similar to X" queries.** Smart Connections does this; sentence-transformers locally does it; either way, no LLM call needed.

3. **Train one classifier early — source relevance.** It's the highest-volume decision Librarian will make, and you'll generate labels for it just by using the system. After 100 decisions, you'll have a calibrated classifier that runs in microseconds.

4. **Reserve LLM calls for the seven things in the "where LLMs belong" list.** Track LLM usage per profile in your dashboards. If a profile is making more LLM calls than its bullet-point list of legitimate uses justifies, that's a sign to decompose the work into cheaper layers.

5. **Periodically audit: for each LLM call, ask "could a classifier or script do this?"** The answer will be "yes" more often than people think. That's where the cost savings and reliability gains come from.

The architectural identity to hold: Memoria is a *bookkeeping system that uses LLMs for the irreducibly cognitive parts.* Not "an LLM workflow with some bookkeeping bolted on." The first framing leads to fast, cheap, auditable systems. The second leads to slow, expensive, opaque ones that fall over at scale.

You've already designed Memoria the right way. The implementation discipline is matching tool to job at every step — and most of the time, the right tool isn't an LLM.
