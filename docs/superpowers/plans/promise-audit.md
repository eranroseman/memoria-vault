# Does Memoria live up to its promise? — 2026-07-09

Verdict of an 8-assessor sweep (`wf_d8990898-3f3`, 1.56M tokens, 447 tool
calls) judging the implementation against `product-statement.md` under the
repo's own standard: a promise counts only where a mechanism delivers it.
Assessors ran the product empirically in fresh vaults and inspected the
deployed sandbox vault read-only.

## Scorecard

| Promise | Verdict |
|---|---|
| Opinionated (structure/types/gates are the design, not config) | **Delivered** — gates frozen in code (`REVIEW_GATED_PREFIXES` tuple, auto-fix deny classes, one-way skill-policy composition); knob census: ~1 config file + secrets env vars, none reshape structure |
| Personal (one human owns judgment; not a team tool) | **Delivered with two leaks** (below) |
| Phase-gated: staged→checked→materialized→consumable | **Delivered** — verdicts only in SQLite, frontmatter smuggling rejected, hash-chained journal, fail-closed crash recovery, byte-hash read barrier |
| "captured, enriched, read, compiled" | **Partial** — compile hard-gated; enrichment bypassable for local-full-text captures (capture mints `checked` directly); **"read" has no enforcing line at all** (interviews optional, compile runs with zero) |
| Draft verified before deliverable | **Delivered** (draft path raises on any finding) / **Partial** overall: non-draft export gated only behind opt-in `--ready-only` |
| ...and accepted | **Partial + bug** — `reject` clears the export gate identically to `accept` (`_disposed_evidence_ids`, knowledge.py:3078) |
| Catalog knowledge graph (ZK bibliography box) | **Delivered** — `work_graph_edges` from provider payloads, 7 relation types, provenance-hashed |
| Extract/digest/index (LLM-Wiki) | **Delivered** for extract+index; digest gated but *undriven* (nothing surfaces checked-but-undigested; sandbox: 1 source, 0 digests) |
| Toulmin overlay | **Partial, generously** — 2.5 of 6 roles (claim_text, contradicts, extends); warrant/backing/qualifier actively excluded by `LINK_RELATIONS`; "unstated-warrant" fires on `supports==0`; "Toulmin" appears in zero docs/src |
| Argument graph parallel to + connected with catalog graph | Parallel **delivered**; connected **partial** — argument edges cannot target catalog rows (`FileNotFoundError`); connection rests on work_id provenance |
| Nested Knowledge Bundle | **Partial** — the hardcoded `projects/<name>/` folder; no general nesting; "Knowledge Bundle" survives only as an export-format relic (alpha.15 retreat) |
| Structural maintenance keeps the graph coherent | **Delivered** — 9 integrity checks + 14 deterministic detectors + cascade rollback with quarantine and git-restore; self-measured (seeded-error battery with recall/FPR bars) |
| ...compounds over months and years | **Scaffolded** — no scheduler ships; worklists/hub-handoff/session-summary are orphan `python3 -m` CLIs with zero product callers; the one deployed vault has never been swept |
| Three spaces, navigable | **Partial** — real as folders + CLI nouns; **catalog is un-listable** (`memoria list --type work` always returns `[]` — dead option the tutorial instructs) |
| Co-PI, not a knowledge base | **Contradicted today** — `memoria ask` is BM25 returning ranked paths; no questioning mechanism exists in code; nothing initiates; default install performs zero LLM inference (deterministic fixtures); the brain is bring-your-own via MCP host |

## The shape of the result

**The trust half is over-delivered.** The write path, gates, provenance,
quarantine, and self-calibration realize "enforcement is a mechanism, not a
label" more thoroughly than most production systems: verdicts that can't be
smuggled, exports that refuse when unclean, rollback that spares PI-authored
content, a checker that measures its own recall before licensing itself.
Assessors' words: "a scrupulous lab manager," "a skeptical librarian plus
peer-reviewer with an excellent inbox."

**The partner half is honest scaffolding.** Conversation, initiative,
semantic understanding, synthesis: BM25, a lexical negation stand-in for
NLI, deterministic excerpt-stitching for compose, structural-only verify
(ponytail comments in code admit each), prompt templates, and orphan
subsystems. `docs/explanation/rationale/boundaries/why-not-autonomous.md`
deliberately caps autonomy at L3 — so part of the co-PI gap is principled
design, not failure. But the statement's tagline currently describes the
roadmap, not the product.

**Nobody has lived in it yet.** The only installed vault has empty digests,
placeholder steering.md, zero graph edges, no audit log, and no `.git`
(materialization would fail there). "Compounds over months and years" is
untested by construction.

## Bugs and leaks found (actionable now)

1. **Reject == accept at the export gate** (knowledge.py:3078) — rejecting
   evidence unlocks export with the unsupported passage still in the draft,
   marker silently stripped. Judgment-inverting.
2. **`memoria list --type work` always empty** (engine/api.py CONCEPT_TYPES
   has no `work` branch) — the catalog cannot be enumerated from any
   surface; Tutorial 01 instructs the dead command.
3. **CLI hides failures**: `_emit` prints literal `ok` on a FAILED operation
   (exit 1; error only in `--json`), prints `True` instead of created paths
   — so the enforced gates are invisible in human mode.
4. **Tutorials fail verbatim**: 02 and 04 omit the check steps the runtime
   enforces; a new researcher's first loop silently stalls.
5. **Journal misattribution**: `resolve_attention`, `curate_note_candidate`,
   `record_copi_interview_turn` hardcode `actor: "pi"` regardless of caller —
   an agent's disposition is recorded as the human's judgment.
6. **Actor is provenance, not authorization**: MCP `operation.run` with
   `actor='agent'` can execute PI-judgment operations (mark-checked,
   curate-*, resolve-attention, cascade-rollback); nothing checks actor.
7. Capture paths mint `check_status='checked'` directly (enrichment bypass);
   `state.upsert_catalog_record` accepts `checked` from any caller.
8. Doc-vs-code contradictions: knowledge-cycle.md's capture-candidate claim
   and "Library pipeline" view (no such surface); linter.md's "blocks
   delegation" claim (no code reads the verdict); frontmatter.md's schema
   example drifted from shipped note.yaml; quickstart's `ask` provider-keys
   claim (ask is keyless BM25).
9. Dead knobs contradicting "no knobs": `.memoria/schemas/calibration.yaml`
   read by nothing; `gated:` key in type YAML read by nothing (and wrong).
10. Orphans: `worklists`, `hub_handoff` (docstring claims it "creates"
    requests; it only returns payloads), `session_summary`,
    `structural_impact` (deepest argument code, unwired, depends on fields
    nothing writes), eval dispatch stub, hash-fake vector embeddings.

## Addendum (same day): re-judgment under the owner's two design axioms

Axioms supplied after the audit: (1) no node is judged true/false — the
system asserts only graph-integrity effects; (2) origin of a change
(human/machine/LLM) does not affect its consequences — origin is
provenance, not authorization.

- Finding 1 (reject==accept at export gate) **flips to design-consistent**:
  the gate requires a recorded disposition, not a favorable one. Residual:
  the silently stripped marker (integrity event without a trace) and
  Tutorial 05's wording.
- Finding 6 (no actor authorization on judgment operations) **flips to
  design-consistent**: identity-gating is what axiom 2 rejects; the read
  barrier's origin-blind demote-and-rescan is the axiom's cleanest
  implementation.
- Finding 5 (journals hardcoding `actor: "pi"`) is **elevated**: under
  axiom 2, provenance is origin's entire job and the sole mechanism behind
  "one human owns judgment" (by review, not permission). Falsified
  provenance is this design's worst defect class. Load-bearing fix.
- Finding 7 (capture minting `checked`) **downgrades** to an intentional
  path asymmetry worth documenting (axiom 1: checked = checks passed; for
  locally-supplied full text the artifact itself is the evidence).
- The "co-PI that can only count edges" criticism **inverts**: semantic
  truth-grading of claims would violate axiom 1. Edge/contradiction/
  refutation structure is the permitted assertion surface. The
  axiom-compatible co-PI roadmap is: questioning, initiative, conversation,
  and stronger tension *detection* — not truth scoring.
- The rollback tension is resolved by the owner: rollback is a cleanup
  utility, not the epistemic core. The central operation is *claim decided
  wrong → propagate grounding consequences across the entire graph*,
  origin-blind.
- Owner clarification re-weights two verdicts: the **six Toulmin
  components are the basis of the knowledge graph**, so the shipped
  3-relation link graph (warrant/backing excluded by LINK_RELATIONS,
  qualifier/certainty unread) is the largest design-to-implementation gap
  in the product — the roles are what make consequence propagation typed
  (grounds lost vs warrant lost vs qualifier-bounded regression vs
  rebuttal strengthened). And **structural_impact re-ranks from orphan to
  the axiom-central engine**: it is the built "decided wrong → blast
  radius" computation, unwired and awaiting fields nothing writes; today
  only source-level falls propagate (retraction sweep, fama-exposure).
- Findings 2, 3, 4, 8, 9, 10 are unaffected and stand.

Later same-day corrections (recorded here so the scorecard reads true):
- **"The brain is bring-your-own" is overdrawn** (co-PI row and signals):
  Memoria owns LLM calls as *fenced one-shot operations* (pydantic-ai
  digest compilation with grounding validation, tier-2 judge, the prompt
  operations — sealed inputs, manifest fencing, provenance-hashed); what
  it deliberately lacks is an *agent loop* (multi-turn, tool-using,
  initiating). The default install runs fixtures until providers are
  configured — that part stands. See roadmap Tier 3 rationale.
- **"Nested Knowledge Bundle: partial — no general nesting" is re-read**:
  per the owner (see `okf-note.md`), each project IS its own nested,
  detachable OKF bundle — the hardcoded `projects/<name>/` shape is the
  mechanism, opinionated rather than missing; the vault must live without
  its project bundles (one-way dependency rule added to the roadmap).

## Bottom line

Memoria lives up to **opinionated, phase-gated, personal** almost fully —
delivered by real, adversarially-tested mechanism. It half-lives up to
**knowledge production that compounds**: every loop exists, gated and
journaled, but the loops that would make it compound (digestion pressure,
scheduled maintenance, worklists) are unwired or unscheduled, and no vault
has lived in it. It does not yet live up to **co-PI**: today it is the most
epistemically careful knowledge base an agent could ask for — which is both
the statement's anti-goal and precisely the substrate the co-PI needs. The
gap is not architectural debt; it is the unbuilt top floor of a building
whose foundations exceed code.
