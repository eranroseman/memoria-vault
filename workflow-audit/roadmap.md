# Roadmap — live up to the promise, then exceed it — 2026-07-09

The change program synthesized from the day's record: `promise-audit.md`
(feature verdicts and defects), `product-statement.md` (axioms, graph basis,
warrant question), `autoresearch-note.md` (self-improvement loops),
`architecture-review.md` (structural findings — "rim-strong, center-soft"),
`okf-note.md` (bundle boundary, placement doctrine, consistency model), and
`schema-analysis.md` (column-level sharpening of items 1, 2, 6, 8, 9, 20).
Shape: make the delivered half honest and visible, repair the trust
substrates the architecture review exposed, build the graph the statement
promises, add initiative and a voice, then exceed via typed blast-radius
propagation and a self-calibrating instrument.

## Tier −1 — The supersession pass (before any implementation)

0. **Absorb the blind-spot sweeps** (2026-07-09; see
   `blind-spots-review.md`). Owner rulings: the dossier IS the current
   decision record; **ADRs and design-history are historical reference
   only — never justification, never evidence, unlock conditions
   ignored.** No supersession ceremony. What survives on current facts or
   merit: **fulltext v2's anchor-substrate dependency** (item 12 note —
   open design question) and the **journal repair within the multi-log
   planes** (item 2, spike-proven anchor). Merge Section C's blind spots
   into the items they gate — most urgently: **disposition telemetry
   before the bulk import** (non-backfillable), **bulk-admission flood
   mechanics** in onboarding, and the **seeded-error license gate**
   before item 19. Adopt Section B formulations where better on merit.

## Tier 0 — Make the delivered machinery true and visible (first)

1. **Provenance faithfulness — structural, not spot fixes.** The
   architecture review showed the hardcoded `actor: "pi"` journal events
   are symptoms of a missing layer: only 3 of ~40 operations read the
   envelope's actor. The fix has a one-choke-point shape: build an
   operation context once in `worker._run_claimed_job` and consume it in
   `trusted_writer` (staging + journal), instead of ~20 leaf kwargs. Two
   schema blockers move first — and the schema analysis showed the actor
   vocabulary fails in both directions at once: `operation_requests.actor`
   is unconstrained TEXT with `DEFAULT 'pi'` while `derivations.actor`
   CHECK actively forbids `'agent'`. Define **one actor enum, one CHECK,
   applied to both tables, no default** — so *absence of origin
   information is never recorded as "the human did it."* Note `observe_pi_edit` attributes all
   unmediated writes to 'pi' — acceptable for a personal tool, but say so
   in the memory-model doc. Under axiom 2, provenance is origin's entire
   job; cascade/demotion already branch on this field, so it must be
   faithful before Tier 1 builds on it.
2. **Journal trust repair — within the recorded multi-log design**
   (redesigned per the blind-spot review; the owner ruled the event-log
   reversal one of two needing real engagement). ADR-25/104's plane
   decomposition stands: separate logs with opposite requirements
   (forensic permanence / content-free analytics / disposable
   diagnostics), per-machine JSONL files kept sync-ready, and the
   git-tracked `.memoria/journal-head` anchor the alpha.12 spike proved
   necessary for tamper evidence. The actual defects to fix inside that
   design: **trust-critical reads (quarantine, PI-edit detection, blast
   radius) must consume the hash-chained `event_log`, not the un-chained
   JSONL copy**; add the missing chain verifier (walk the chain, check
   against journal-head); define the crash story for the dual append
   (order + reconciliation sweep); and add `event_type`/`timestamp`
   indexes when event_log becomes the trust-read substrate. "Sole
   authoritative journal" is retired as the goal; "one authoritative
   trust-read path" replaces it.
3. **Grounds durability.** `.memoria/blobs/` — captured source content,
   the evidential grounds of the whole Toulmin stack — is gitignored as
   "regenerable runtime data" and is not regenerable. Resolved by the
   bundle-boundary decision (`okf-note.md`): **backup as data, not git
   tracking** — full texts are external material in engine-space, git
   holds knowledge not corpora, and the bundle stays self-contained via
   `bibliography.bib`. Ship the backup/restore story. Cheap fix;
   data-loss class.
4. **Surface honesty** — `_emit` stops printing `ok` on failed operations
   and prints created paths; the catalog becomes enumerable (`list --type
   work` gets a real SQLite branch, or a `work list` command).
5. **Docs tell the truth** — tutorials teach the check steps at point of
   need (02 and 04 fail verbatim today); fix the five doc-code
   contradictions from the promise audit; delete the dead knobs
   (`calibration.yaml`, the wrong `gated:` keys); and make the six
   enforcement-claim corrections from the architecture review (phantom
   seven-layer model, block-loudness pause that binds only the uninstalled
   adapter path, "single attention writer" bypassed by three hand-rolled
   copies, telemetry logs no code writes, SQLite-backed attention claim,
   present-tense dashboard rail).

Tier 0 adds no capability — it makes the built product experienceable and
its trust substrates real. Items 1, 4, 5 are ideal first features for the
superpowers-spine acceptance run (alignment-plan step 21).

## Tier 1 — The graph substrate (core gap; everything depends on it)

6. **Schema migration machinery — the new prerequisite.** `state._init`
   hard-fails on any user_version except 0/8; `CREATE TABLE IF NOT
   EXISTS` only; no ALTER path. Every substantive Tier 1 change hits this
   wall first. Build the minimal migration layer before touching relation
   vocabularies. While in there: move toward **ULID-keyed provenance** —
   the schema analysis names the exact columns: `derivations.input_id/
   output_id` and `outputs.target_path` key on paths, and the schema's
   five identity vocabularies (concept_id, output_id, work_id, passage_id,
   path) have only three FKs total; renames silently sever provenance —
   fatal to "compounds over years". OKF
   reconciliation: OKF's concept ID *is* the path, so ULID is the internal
   identity and the path is the OKF-facing address, with rename tracking
   mapping between them — conformance is not an argument for path-keyed
   internal provenance (`okf-note.md`).
7. **Decide the warrant ontology** (standing recommendation: hybrid —
   nodes when explicit, demandable on challenge) **before** touching
   `LINK_RELATIONS`. Spend the brainstorming/grilling budget here: the
   decision is expensive to reverse after accumulation.
8. **Give the graph one owner, then extend to the six-role basis.** The
   architecture review found five substrates, four parsers, three
   contradictory relation rosters, and the designed join point —
   `concept_edges` — permanently empty and wiped on every index refresh.
   Create a single edge module that owns the relation roster and all
   parsing; fill `concept_edges` (fix the stub, stop the wipe) as the
   queryable argument-graph index — and reshape it for the six-role
   future: the schema analysis found PK `(source, relation, target)` with
   **no edge_id and no attribute columns**, nothing to hang a warrant
   reference or qualifier on; promote the existing
   `catalog/sources/<work_id>` identity namespace to the *documented
   bridge* so claim→work edges cross the substrate boundary (the address
   space already exists — the verdict-cascade triggers already translate
   it; three code gates block it). Then extend to the
   Toulmin six — **as roles carried by relations and demandable slots,
   not node types**, and with the relation vocabulary earned one relation
   at a time as each is actually used (a half-populated typed field
   returns incomplete answers — the principle stands on its own merit):
   warrant nodes with backing edges; qualifier/certainty made live;
   rebuttal able to target warrants. Add the missing
   **graph architecture page** — the central substrate is currently
   undocumented.
9. **Redesign propagation, then wire the central operation.** The
   blast-radius engine walks the derivation DAG only — supports/contradicts
   edges are invisible to it — and it branches consequences on actor
   (origin as authorization, against axiom 2, keyed on the unreliable
   field item 1 fixes). Redesign: traversal over *grounding edges* with
   typed, origin-blind consequences (grounds lost vs warrant lost vs
   qualifier-bounded regression); the actor branches are either
   owner-ratified explicitly as remediation-authority or removed. Add the
   **reverse-traversal indexes first**: `concept_edges(target_concept_id)`
   and `work_graph_edges(target_id)` have no index, and "what supports X"
   is the blast-radius direction (schema analysis). Then the
   claim-disposition flow: "decided wrong" → typed propagation →
   blast-radius report in the inbox. Wiring `structural_impact` means
   bringing it **on-substrate** — today it bypasses both the read barrier
   (reads quarantined notes) and the trusted writer (raw `write_text`) and
   reads fields nothing writes.

## Tier 2 — Close the loops (make it compound)

10. **Manifest-driven dispatch — the enabler.** The worker is an ~800-line
    if/elif chain with hand-rolled payload validation because `io_schema`
    is a decorative string, and manifest `allowed_paths`/`allowed_tools`
    are consulted by ~6 of ~40 implementations. Make `io_schema` real and
    dispatch from a registry so every wired orphan and future operation is
    manifest + function — and the fencing the manifests promise is imposed
    by the worker, not opted into per call site.
11. **Wire the orphans** (worklists; hub_handoff so it actually enqueues;
    session_summary) as manifest-backed operations; add **digestion
    pressure** — a surface for checked-but-undigested sources. Add the
    **detachability detector** (2026-07-09 clarification: projects are
    nested, detachable bundles per ZK project notes): permanent knowledge
    (notes/, hubs/, digests/) must never link into `projects/` — flag any
    such edge; and a **project-close operation** (harvest durable claims,
    export, capture deliverable to catalog, archive the bundle).
12. **The reactive substrate — three execution tiers, one queue** (owner
    decision, 2026-07-09: move from do-on-read to do-on-write for capacity
    and UX). Principle: **on-write accelerates, on-read enforces** — the
    fail-closed read barrier stays as the backstop, so a dead daemon
    degrades gracefully to today's behavior with zero correctness loss.
    - **Tier A, on-write per-file** (sub-second, debounced): grow
      `serve --watch` into `memoria daemon` (watcher + HTTP + queue
      drainer under the existing workspace flock); file event → observed
      journal event (provenance at edit time) → demote-if-checked →
      schema/template validation with finding pushed to inbox and editor →
      incremental index upsert (passages/FTS/`concept_edges`, single
      file) → cheap local checks (link targets, evidence anchors) →
      re-promote if checks pass. Every step is an operation through the
      existing queue — no second execution path; envelope provenance and
      idempotency preserved (axiom 2: identical chain whoever wrote).
    - **Tier B, on-quiet per-subgraph**: neighborhood integrity checks,
      scoped lint, projections/attention regeneration, and the automations
      (hub thresholds, worklists) — this chain is the natural trigger the
      orphans (item 11) were missing.
    - **Tier C, on-schedule**: the nightly deep sweep (whole-vault
      integrity, retraction, discovery, gaps) — one command, one PI cron
      line; baseline stays functional daemon-free (the "no background
      process required" stance survives as a floor, not the experience).
    - **Event sources — two**: filesystem watcher + the Obsidian plugin
      pushing editor vault events via `/operation/run` (it already queues
      events); the same channel feeds the plugin live status
      (checked/unchecked badges, inbox counts) — Tier 3's surface gets its
      data feed here.
    - **Prerequisites**: incremental indexing (fix the O(vault)
      delete-and-reinsert refresh that also wipes `concept_edges`); the
      graph-owner module (item 8) for per-file edge upserts;
      `.memoria/`-internal ignore rules + debounce/coalescing for write
      storms; index decoupled from the `fulltexts/*.md` projection —
      passages read from the blob store directly, since **`fulltexts/`
      retires as a bundle root entirely** (decision v2 in
      `user-workflow.md`: external material doesn't belong in the
      knowledge bundle; the PDF is the human reading surface, the engine
      serves passages on demand for quote-in-context). **Status: open
      design question, not a settled decision** (owner ruling in the
      blind-spot review — fulltext is one of two reversals where the
      recorded reasoning has real force): the `work_id#^pNNNN` anchor
      substrate that evidence markers, digest anchor-checks, and
      three-way `mc` trust point into lives as block anchors in
      fulltext.md files, and the keep-test (what survives when Memoria
      disappears) weakens if anchored verbatim text exists only in the
      DB. v2 remains the preferred direction *conditional on*: a
      replacement locator contract in content-hash space, migration of
      existing `%%ev%%` markers and anchor checks, the fate of `digests/`
      anchor-checking, and a stated post-v2 keep-set (PDF + exported
      spans). Cheaper than first assumed on the schema side: `'fulltext'`
      was **never a concept type**, so retirement is
      folders.yaml/CONCEPT_HOMES plus index code. Bonus from the same
      analysis:
      `file_index_state` (mtime+sha per path) already exists — Tier A's
      incremental-indexing substrate is built, not new.
    - **Surface-contract gaps** (verified against the 17-action registry,
      2026-07-09): agent integration is ~90% served today
      (`operation.run` + `requests.get` covers the whole co-PI loop);
      plugin ~60%. Additive actions needed: `works.list` (catalog
      enumeration — the T0 CLI fix lands here too), `context.read`/set
      (shared editor state), `status.paths` (bulk path→verdict for badges;
      must report verdict *without* content, bypassing the consumption
      gate), one `observe-file-event` operation manifest. The one new
      transport concept: an SSE/long-poll events endpoint for sub-second
      badge updates (registry binds synchronous actions only; polling is
      the v1 fallback). Grounding-query read (`graph.read`) waits on
      item 8's filled `concept_edges`.
13. **Semantic upgrades where axioms allow** — replace the tier-1
    lexical-NLI stand-in and hash-fake embeddings: grounding-relationship
    detection, never truth scoring. Verify the runner-resolution path at
    implementation: the architecture sweep read `DEFAULT_RUNNER_POLICY` as
    package-pinning deterministic-fixture even on live, but live provider
    calls demonstrably exist (digest compilation, tier-2 judge via
    `providers.yaml`) — establish exactly which knob enables live mode
    per operation and whether the pin is a stance or an incomplete wiring.
    Decide who may author machine edges (the `tension` relation exists in
    the DB CHECK but no write path can produce it).

20. **Source-type generalization** (added 2026-07-09; lives in Tier 2 —
    numbering kept stable). The pipeline spine (capture → immutable blob →
    textual layer → index → digest+interview → claims) is type-generic;
    generalizing beyond academic papers costs four type-specific adapters:
    (a) **identity + enrichment per type** — DOI+providers for papers,
    URL-with-no-providers for blogs (the local-full-text capture path is
    the mechanism, not a bypass), feed/episode for podcasts, DOI-or-URL
    for datasets, URL+commit for repos; the enrichment gate becomes
    type-conditional. (b) **Textual-layer derivation** — extraction /
    transcription (fenced one-shot operation) / dataset profile / repo map
    at pinned commit; everything downstream consumes the textual layer
    unchanged. (c) **Anchor locators** — (artifact hash, locator):
    char-offset, timestamp span, row/query, file:line@commit; engine
    serves spans on demand per the fulltext-v2 decision. (d) **Drift
    detection for mutable sources** — the retraction sweep generalized:
    re-fetch, hash-compare, attention flag ("snapshot diverges from
    live"); flag-don't-fix, PI disposes. Free rides: biblatex covers
    @online/@software/@dataset/@audio in the bib projection; the existing
    code_artifacts/code_runs machinery is the seed for
    reproducible-run-as-grounds. Keep a **closed source-type roster**
    (paper, article, audio, dataset, software) — types are schema; schema
    is the design, and the enforcing line is a CHECK on
    `catalog_sources.item_type` (today unconstrained TEXT defaulting
    'article' — schema analysis). Also widen `work_aspects` PK when
    textual layers make aspects load-bearing: `(work_id, aspect_type)`
    currently forces one key idea and one limitation per work.

## Tier 3 — The conversational co-PI (method, never belief)

**Surface strategy (standing recommendation, 2026-07-09):** editor plugin +
agent-of-choice, not Memoria-as-agent. Memoria is designed to work with a
text editor (Obsidian first, VS Code probable second); the fork — plugin +
agent-integration vs an embedded CopilotKit-style copilot — resolves via
the co-PI qualifier: **the engine authors the method (deterministic
question cards, interrogation agendas, read off the graph); the user's
agent voices it** (via MCP + a shipped Memoria skill, dispositions filed
through the envelope with true actor). Borrow CopilotKit's one good idea —
shared app state — as an MCP read action exposing current-note/selection
context from the plugin, so conversation is situated. VS Code is nearly
free under this shape (agents already run inside it; thin status extension
later). Embedded-chat-panel earn-back: once engine-authored interrogation
exists the panel is thin (render questions, collect answers, user's own
provider); trigger — evidence the two-window experience blocks daily use.
Rationale (corrected 2026-07-09 — Memoria does make LLM API calls): the
engine owns model calls as **fenced one-shot operations** (pydantic-ai
digest compilation with grounding validation, tier-2 judge, the
prompt-operation family — sealed inputs, manifest fencing, prompt/model
provenance); what it deliberately does not own is an **agent loop**
(multi-turn, tool-using, initiating). The surface split follows that
line, not a no-LLM line: engine-authored method may itself be LLM-powered
under existing fencing — item 14's question generation can be a prompt
operation like red-team-argument — while the conversation loop stays with
the user's agent (or a thin panel later). Preserves the L3 cap,
provenance-clean entry, and solo-maintainer economics; avoids competing
with the agents the user already runs.

14. **Grounding interrogation** — the question taxonomy comes from the
    Toulmin pillar (product-statement lineage): grounds ("what
    evidence?"), warrant ("why does that evidence license this claim?"),
    backing ("what supports the inference rule?"), qualifier ("how strong,
    how scoped?"), rebuttal ("under what conditions is this false?") —
    one taxonomy feeding the interview, red-team, and gap operations.
    Generate questions from `analyze_gaps` findings; replace the static
    interview prompt; make `memoria ask` honest or genuinely
    conversational via the live path. Companion honesty fix: rename
    findings so "unstated-warrant" fires only when a warrant is genuinely
    absent (today it fires on supports==0 — Toulmin words on non-Toulmin
    checks). Argument health becomes a per-role completeness profile, and
    `argument.canvas` renders as an actual Toulmin diagram in the project
    panel. A question-generation
    *operation* is the cheapest extension in the system (the
    prompt-operation family needs only a manifest); a conversational
    *surface* is not — the surface contract has one synchronous write
    action and no session concept, so plan new contract actions. The query
    side inherits Tier 1: "how is this claim grounded" needs the filled
    `concept_edges` index as its single query surface.
15. **A surface where the PI lives** — minimum viable inbox + argument
    health rendering in the Obsidian plugin (the documented Navigator rail
    has no renderer in any layer); a CLI voice that speaks findings
    instead of `True`.

## Tier 4 — Exceed the promise

16. **Instrument autoresearch** (per `autoresearch-note.md`): the
    overnight org that measurably sharpens detectors against the
    seeded-error battery. Harness fixes first, from the architecture
    review: route the runner-under-test through the measured behavior
    (today fixture prep ignores the runner, so the experiment's subject
    cannot affect the measurement), include `prompt_version` in
    `verdict_key`, and tie prompt body hashes to `prompt_version` so
    silent pattern edits can't change the experiment unit.
17. **Prompt autoresearch** — fill the `eval_dispatch` stub (it returns a
    `planned:` string; nothing enqueues) with gold tasks from real use;
    grind operation prompts against `support_rate`.
18. **Warrant inventory as explicit methodology** (free once Tier 1
    lands): "show me everything resting on inference-type X, because I no
    longer accept it" — a years-horizon capability no notes system offers.
19. **Live in it — including Memoria as a project inside Memoria.** Seed
    the vault with the real research corpus (the relocated `papers/`
    library) **and open "Memoria" as a project in the vault**: the repo
    owns code and shipped artifacts; the vault owns the thinking that
    produces decisions. The mapping is a convention, not code: design
    decisions are claim notes (grounds = evidence links, warrant = the
    licensing design principle, qualifier = scope, rebuttals = the
    rejected alternatives); design principles (axioms, master pattern)
    are the shared warrant inventory ("show me everything resting on
    axiom 2"); a reversed decision is the central operation run on your
    own architecture; design-history chapters and docs are project
    exports, captured back on shipping. Prerequisites: Tier 0 plus two
    item-20 source types (article/URL — exists; repo-at-pinned-commit —
    missing; pin self-captures to release tags or drift detection fires
    every commit). Needs nothing from Tier 1 — starts right after Tier 0.
    This is the strongest form of dogfooding: dev knowledge work is
    daily, so the vault gets lived in as a byproduct of building it, and
    the next dossier is claims and drafts instead of a thirteenth
    markdown file. "Compounds over months and years" can only be
    demonstrated; this is the item that proves the promise.

## Sequencing

Tier 0 (items 1–5, with 1–3 as the trust-substrate repairs) → Tier 1
(design-heavy; item 6 unblocks 7–9) → Tiers 2–4 parallelize once the
substrate lands, with item 10 as Tier 2's enabler. All of it runs through
the new spine after the superpowers-alignment plan executes. One-sentence
version: Tier 0 makes it honest, Tier 1 makes it the product the statement
describes, Tier 2 makes it compound, Tier 3 makes it converse, Tier 4
makes it the only thing of its kind — and item 19 is where the promise
stops being prose.
