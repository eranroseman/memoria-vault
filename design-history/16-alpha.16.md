## alpha.16 — READ cycle and knowledge-production substrate

**Theme:** alpha.16 is the checkpoint that turns alpha.15's standalone engine
baseline toward real research use: the READ cycle plus the substrate beta.1
needs for writing and code output. The governing requirements define "done" as
one real project moving from source capture through full-text extraction,
annotation processing, source-notes, gap analysis, corpus-grounded Ask, and
keep-test survival without presenting machine output as verified truth.

What drove it (2-3 sentences): alpha.15 proved the engine/integrity reset but
left the product short of an end-to-end knowledge loop. The redo comparison for
alpha.16 found that beta.1's draft had deleted too much of the
knowledge-production core; alpha.16 restores the READ-side substrate while
explicitly deferring the full WRITE and coding modules to beta.1.

---

### 1. Role and acceptance boundary

- **What:** alpha.16 is scoped to the READ cycle: create a project; seed it from
  Zotero, bibliography, DOI/arXiv/PMID, PDF, GitHub, or local file; land raw
  artifacts; extract full text; optionally digest; process annotations into
  notes/claims/questions; connect source records to the subjective graph through
  source-notes; run gap analysis over both graphs; Ask over anchored spans; and
  keep useful markdown/PDF/BibTeX artifacts if Memoria disappears. **Why:** the
  mission still includes writing and code, but the requirements set alpha.16 as
  the minimum real feedback-producing loop before beta.1's full output modules.

- **What:** Acceptance is one runnable dogfood loop plus technical substrate
  checks: every machine write has a `run_id`, goes through `VaultWriter`, can be
  reverted without changing human text, logs Guard egress, records cost in the
  Ledger, preserves provider payloads, and proves backup/restore on a clean
  profile. **Why:** alpha.15's integrity reset only matters if the first real
  READ workflow exercises the same provenance, cost, network, and recovery
  boundaries that later writing will depend on.

### 2. Vault layout and file contract

- **What:** The vault is the user-selected folder created by `memoria init`, not
  a nested `Memoria/` folder. The required roots become `works/<work_id>/`,
  `sources/`, `notes/`, `hubs/`, `projects/`, `bibliography.bib`, and
  `system/`. **Why:** the correction follows the keep-test and Obsidian storage
  evidence: durable artifacts stay as visible plain files, and nested vaults are
  explicitly discouraged.

- **What:** `work.md` is rejected as the human/source bridge. The source side
  splits into objective `works/<work_id>/record.md`, `fulltext.md`, optional
  `digest.md`, and raw payloads, plus human `sources/<slug>.md` source-notes.
  **Why:** objective metadata and provider payloads are catalog facts; the
  user's interpretation begins in the source-note. Collapsing both into one
  file would recreate the authority confusion alpha.15 removed.

- **What:** Stable `work_id` owns identity; citekeys remain display/citation
  attributes because bibliographic metadata changes can alter citation keys.
  `bibliography.bib` is a survival artifact, not the primary identity store.
  **Why:** alpha.15 had already separated identity from paths/titles; alpha.16
  applies the same rule to source identity.

### 3. Two graphs and the source-note bridge

- **What:** alpha.16 formalizes two graphs. The catalog graph is objective,
  relational, and SQLite-backed: sources, authors, venues, identifiers,
  references, provider payloads, and citation neighborhoods. The knowledge graph
  is subjective markdown: notes, claims/questions, hubs, projects, and
  human-authored argument edges. **Why:** the requirements call this the spine:
  beta.1's draft deletion of the ZK graph was not justified by evidence, while
  the READ cycle still needs both source coverage and argument coverage.

- **What:** The source-note is the bridge. One source-note per work links the
  objective catalog row to the human knowledge graph, carrying interpretation
  rather than bibliographic truth. **Why:** this preserves the user's authorship
  while letting gap analysis compare what the corpus contains against what the
  researcher has actually integrated.

- **What:** Hubs organize human salience and topic membership without
  machine-authoring the user's prose. Claims/questions remain human-owned
  modes/structures rather than standalone machine verdicts. **Why:** this keeps
  the alpha.15 lesson: machine output proposes and structures, but does not
  become verified knowledge by being generated.

### 4. Derived store, writer, and recovery

- **What:** The DB split becomes explicit: derived state can rebuild from vault
  files and provider payload backups; operational ledgers (`runs`, `jobs`,
  `events`, `costs`, `incidents`, Guard logs, provider payload records) are not
  rebuildable and must be backed up/exported honestly. **Why:** the keep-test is
  not a claim that every useful byte is markdown; it is a claim about what the
  researcher can keep using after Memoria disappears.

- **What:** One staged, run-scoped `VaultWriter` owns all machine file changes.
  Machine writes stage, apply, verify, and commit per run, with block-level
  protection for human spans and one-click revert. **Why:** alpha.16 adds
  machine full text, digests, gap reports, evidence files, and exports; allowing
  separate writers would make provenance and rollback unprovable.

- **What:** `memoria rebuild` remains fail-closed: lost or stale DB verdicts
  return material to unchecked rather than trusting file frontmatter. **Why:**
  alpha.15's forged-status lesson still governs; structural checks can prove
  links, spans, hashes, and references, but not truth.

### 5. Capture, extraction, enrichment, and retrieval

- **What:** Capture is land-first, resolve-later. Zotero local API, DOI,
  direct PDF, GitHub, and local files land immutable raw artifacts or visible
  triage stubs before metadata repair. PDF extraction produces anchored
  `fulltext.md`; `digest.md` is opt-in, machine-authored, untrusted, and
  anchor-checked. **Why:** source capture must never lose data or convert a
  metadata failure into a silent absence.

- **What:** Provider enrichment preserves payloads and per-field provenance.
  Crossref/DOI, Zotero, OpenAlex, Semantic Scholar, arXiv/PubMed-style
  identifiers, and GitHub are inputs, not sole authorities. **Why:** the
  alpha.13/14 enrichment spike already showed provider incompleteness; alpha.16
  keeps best-source-wins and replayable payloads.

- **What:** Ask is fulltext-first and denominator-first. Retrieval returns
  anchored verbatim spans; summaries and digests can enrich but cannot replace
  source text. FTS5/BM25 ships first, with vector fusion only behind a recorded
  benchmark pass. **Why:** the evidence base says summaries and graph memory do
  not beat lexical/verbatim retrieval by default, and absence claims must state
  the searched set.

### 6. Gap analysis and machine judgment

- **What:** Gap analysis compares three things: source coverage, argument
  coverage, and mismatch between the catalog graph and the knowledge graph. It
  reports denominators rather than a synthetic saturation score. **Why:** this
  is the READ-cycle payoff: not just "what did we retrieve," but "what have we
  integrated, what is missing, and where do the two graphs disagree."

- **What:** NLI and LLM judgment remain proposers. `mc` is trusted only on
  three-way agreement: marker, current hash, and `checks` row; HANS/PAWS-style
  probes gate any NLI-backed trust. **Why:** alpha.15's no-write-time-oracle
  lesson survives unchanged: overlap/negation failures and wrong belief flips
  make machine certainty a routing signal, never authority.

- **What:** The Ledger and Guard become first-class substrate. Paid model calls
  need price tables, token ceilings, circuit breakers, and run attribution;
  workers are credential-free and networkless, with Guard brokering egress and
  logging allow/deny decisions. **Why:** alpha.16 touches providers and LLMs in
  real workflows, so cost and network authority must be in place before beta.1.

### 7. Surfaces, export, and discovery

- **What:** Acceptance is host-neutral through the read API. A provisional
  Obsidian Ask/Review pane may be the first UI, but `memoria ask --json` /
  read-API harnesses prove the behavior without relying on the host. **Why:**
  the host/stack decision remains open; the engine boundary must not depend on
  a UI being correct.

- **What:** Minimal export is allowed only as a run: structurally checked,
  revertible, and clearly below beta.1's full output-readiness gate. **Why:**
  alpha.16 must close the loop to a testable output, but publication-grade
  draft/code readiness belongs to beta.1.

- **What:** Discovery is bounded provider/citation lookup and a human-triggered
  citation monitor, not broad autonomous web research. **Why:** READ-cycle value
  needs source candidates, but an unattended discovery loop would reintroduce
  the autonomy alpha.15 removed.

### 8. Deferred to beta.1

- **What:** Deferred scope is explicit: full writing module, coding module,
  code execution sandbox, final workspace/gate topology, publication-grade
  export gates, broad discovery, and full onboarding/time-to-first-answer
  product flow. **Why:** these are the WRITE/output half of the MVP; alpha.16
  supplies the substrate and leaves enough structure that beta.1 can build on it
  instead of re-litigating the READ cycle.

---

### Notable decisions and deferrals

| Decision / deferral | Disposition |
| --- | --- |
| Memoria-born vault root | Adopted for alpha.16; no nested `Memoria/` folder. |
| `record.md` + `source-note` split | Adopted; replaces a single human/source `work.md`. |
| Two-graph model | Adopted; catalog graph in SQLite, knowledge graph in markdown. |
| `VaultWriter`, `run_id`, revert | Adopted now as write substrate. |
| Guard + Ledger | Adopted now because alpha.16 already touches providers and paid model calls. |
| FTS/BM25-first Ask | Adopted; vector retrieval remains benchmark-gated. |
| Full writing/coding modules | Deferred to beta.1. |
| Resident daemon | Not adopted; `serve` is on-demand. |
| Host/stack choice | Open; acceptance remains read-API based. |

