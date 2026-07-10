# Architecture review — alignment with the promise — 2026-07-09

Verdict of a 6-dimension architecture sweep (`wf_df19877b-e3f`, 1.03M tokens,
314 tool calls; import structure grep-verified, schema.sql read in full).
Judges *structure* — layers, substrates, topologies — against
`product-statement.md` (axioms, graph basis) and `roadmap.md` tiers.
Complements `promise-audit.md` (feature delivery).

## The one-line verdict

**Rim-strong, center-soft.** The perimeter — write door, request envelope,
read barrier, verdict store, surface contract, capability roster —
genuinely implements the axioms in structure. The center — the typed
grounding graph and provenance-in-depth, the two things the statement is
*about* — is where structure gives way to convention. The skeleton is
right; the load-bearing span is missing. Notably, the architecture has
already *chosen* the hybrid graph substrate the warrant open-question
recommends (frontmatter authors, SQLite derives); its seams are dormant,
not absent.

## Where the axioms are structural (keep; build on)

- **trusted_writer as single machine-write choke point**: staged →
  schema-validate → promote → dual journal → git; verdicts live only in
  SQLite; `RETIRED_FRONTMATTER_FIELDS` rejection means a file cannot
  self-assert its verdict — axiom 1 in the schema.
- **Truth-free verdict vocabulary by CHECK constraint everywhere**
  ({unchecked, checked, quarantined}); verdict cascades to passages via DB
  triggers — integrity propagation independent of app code.
- **One envelope schema at every surface** (actor, provenance_json,
  causal_refs, precondition_hashes as columns) — axiom 2 at the rim; CLI,
  HTTP, MCP all enter the same queue.
- **Read barrier**: byte-hash + verdict, fail-closed, origin-blind
  demote-and-rescan — the purest axiom-2 mechanism in the system.
- **surface_contract.py**: one drift-tested registry binding 16 actions to
  CLI/HTTP/MCP — T3's surface plugs in as new actions, not a rewrite.
- **Closed capability roster**: package-only manifests, sha256 trust
  stamps, worker↔catalog parity tests — "opinionated" enforced.
- **Detective posture toward PI edits** (observe → demote → backfill,
  never block) — files-first and one-human-owns-judgment as structure.
- Deployed sandbox matches the documented on-disk layout nearly
  file-for-file; the docs are honest about the fake embedder and BM25.

## Where the structure resists the axioms (ranked)

1. **Provenance is structural at the rim and evaporates mid-path.** Only 3
   of ~40 operations read the envelope's actor (worker.py:316,352,583);
   curate/resolve/interview leaves hardcode `actor: "pi"`;
   `operation_requests.actor` DEFAULT 'pi' + `request_envelope` coercing
   empty→'pi' record *absence of origin information as "the human did
   it"*; `observe_pi_edit` attributes every unmediated write to 'pi'; and
   the `derivations` CHECK (pi/operation/integrity) **actively forbids**
   `actor='agent'` — the schema blocks the T0 fix. Fix shape: one
   operation-context built in `worker._run_claimed_job`, consumed by
   trusted_writer, plus a schema migration; not twenty leaf kwargs.
2. **The blast-radius engine is origin-sensitive and walks the wrong
   graph.** `propagate_scan_demotion`/`cascade_rollback` branch
   *consequences* on actor (integrity.py:915-925, 999-1003) — origin as
   authorization inside the central operation, against axiom 2, keyed on
   the very field that is unreliably stamped. And `_downstream_events`
   traverses the derivation DAG only: supports/contradicts edges are
   invisible to propagation, so a claim decided wrong demotes what was
   *derived* from it but never touches what it *supports*. The central
   operation's engine does not read the argument graph.
3. **The graph has no owner.** Five substrates, four edge notations, four
   independent parsers, three contradictory relation rosters
   (schema.py:39 vs state.py:1884 vs structural_impact_graph.py:14);
   `concept_edges` — the designed join point — is permanently empty (stub
   returns [], and every index refresh wipes it); `derivations` is written
   and never read; claim→work edges are blocked at three independent
   gates even though the `catalog/sources/<work_id>` identity namespace
   (62 call sites + SQL triggers) already bridges the substrates. The
   two graphs are parallel but not connected — undocumented, since
   docs/explanation/architecture has **no graph page at all**.
4. **Split-brain journal; grounds are the least durable artifact.** The
   hash-chained append-only `event_log` is ornamental: every
   trust-critical read (quarantine, PI-edit detection, blast radius) reads
   the un-chained, gitignored JSONL copy; no chain verifier exists
   anywhere; the dual write is non-atomic. Worse: `.memoria/blobs/`
   (captured source content — the evidential *grounds* of the whole
   Toulmin stack) is gitignored as "regenerable runtime data" when
   captured content is not regenerable.
5. **No schema evolvability.** `state._init` hard-fails on any
   user_version except 0/8; CREATE TABLE IF NOT EXISTS only; zero
   migration machinery. T1's relation-vocabulary change hits this wall
   first.
6. **Enforcement is two disjoint regimes, not defense-in-depth.**
   PolicyEngine + loudness blockers + review-gating bind only the adapter
   hook — which the baseline never installs; worker promotions and CLI
   writes ignore open block cards (docs claim otherwise). Manifest
   `allowed_paths`/`allowed_tools` are consulted by ~6 of ~40
   implementations — fencing is opt-in per call site. The worker
   dispatcher is an ~800-line if/elif chain with hand-rolled payload
   validation because `io_schema` is a decorative string.
7. **Path-as-identity.** Verdicts, derivations, and journal references key
   on relative file paths; frontmatter ULIDs exist but nothing references
   them. Years-scale reorganization silently severs provenance — against
   "compounds over months and years."
8. **Docs overstate enforcement, understate the graph**: a "seven-layer
   model" documented nowhere and not exhibited (cli.py imports ~35 runtime
   modules directly); "single attention writer" bypassed by three
   hand-rolled copies; telemetry pages inventory logs no code writes;
   dashboard pages narrate a rail no layer renders. The honest pages
   (write boundary, control plane, on-disk layout, fake embedder) are
   honest exactly where the promise audit found the product strong.

## Architecture work items (feeding the roadmap tiers)

- **A0 (with T0):** operation-context threading (one choke point);
  migration to widen the actor vocabulary; drop DEFAULT 'pi' (absence must
  not equal "human"); journal chain verifier + make event_log the read
  substrate (or reconcile both); stop gitignoring blobs or give grounds a
  durable backup story.
- **A1 (before/with T1):** build migration machinery first; then give the
  graph one owner — a single edge module owning the relation roster, the
  filled `concept_edges` index as the query substrate, the
  `catalog/sources/<id>` namespace promoted to the documented bridge;
  redesign propagation to traverse *grounding edges* with typed,
  origin-blind consequences (the actor branches either get owner-ratified
  as remediation-authority or removed).
- **A2 (with T2):** manifest-driven dispatch (make `io_schema` real) so
  every wired orphan and new operation is manifest+function, not an
  if-chain edit; single instrumented entry point for edge writes.
- **A-docs:** a graph architecture page + the six enforcement-claim
  corrections; retire the phantom seven-layer narrative or build it.
- **Identity:** ULID-keyed (or rename-tracked) provenance before the vault
  accumulates years of content.

## Alignment summary per statement clause

| Clause | Architectural alignment |
|---|---|
| Opinionated | **Strong** — closed roster, frozen prefixes, package-only capabilities |
| Personal / one human | **Strong at boundaries**, undermined by provenance defaults that fabricate "pi" |
| Phase-gated | **Strong** — verdict tri-state woven through schema with cascades |
| Axiom 1 (grounding, not truth) | **Strong** — truth-free vocabulary by CHECK constraint |
| Axiom 2 (origin-blind consequences) | **Rim yes, center no** — envelope structural, propagation origin-branching |
| Toulmin graph basis | **Weakest** — no owner, empty join index, three rosters, ternary inexpressible |
| Central operation (blast radius) | **Wrong graph** — derivation-only traversal, argument edges invisible |
| Compounds over years | **At risk** — path-as-identity, no migrations, gitignored grounds |
| Co-PI substrate | **Ready at the transport layer** (surface contract), starved at the query layer (no grounding query surface) |
