---
topic: decisions
id: 129
title: Layered machine judgment — proposers, deterministic extraction, shadow-first calibration
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [127, 128]
supersedes: [9, 10, 30, 38, 39, 56, 66]
superseded_by: []
---

# ADR-129: Layered machine judgment

Consolidation ADR (see ADR-125 preamble). Everything a model or score is
allowed to decide, and the calibration discipline that governs it. Amends
ADR-11 (below) without superseding it.

## Context

The comparator/proposer decisions were scattered: contradictions dashboard v1
(09), human-set supersession (10), the pre-file similarity gate (38),
acceptance checklists (39), uncertainty flagging (56), triage scoring with
`calibration.yaml` (66), and the tiered ingest merge (30). Several were bound
to retired surfaces; their disciplines survive and are restated here against
the alpha.15 engine. One honest premise governs all numbers: **no threshold in
the prior corpus was ever validated — there has never been a production vault.
Inherited constants are initial knob positions, not experience.**

## Decision

- **Layered contradiction/supersession/dedup proposer.** No mechanism decides;
  each is a bounded, auditable proposer, and the human sets the directional
  link. Tier-1: a pinned, local-capable NLI comparator, tri-class verdict with
  first-class abstain and an FP budget, dedup keyed on canonical IDs; it may
  gate candidates **only after passing a HANS-style overlap-but-opposite
  acceptance set** (NLI shares cosine's lexical-overlap blind spot). Tier-1
  failing HANS is a **loud degraded mode**: cosine/BM25 candidates route to
  ask, attention is raised — never a silent no-op. Tier-2: an LLM judge,
  admissible only on Tier-1 abstain/hard cases, retrieval-grounded, abstain
  first, temperature 0 — **a proposer, never an authority**; its verdict never
  promotes or demotes anything by itself. Each tier must beat a declared cheap
  baseline (cosine/BM25) on its fixture or it is disabled. NLI silence is
  never presented as "no contradiction."
- **Supersession semantics** (10's mechanism, narrowed): the human sets
  `superseded-by`; machine-proposed supersession is a candidate. Superseded/
  retracted items are never presented as current but stay first-class
  retrievable and tagged — hard exclusion is rejected because cross-period
  queries need the historical baseline. Partial supersession rides the link's
  `why`.
- **Deterministic edge extraction.** On materialization, explicit-typed body
  links extract to **unchecked candidate edges** with zero LLM calls; bare
  wikilinks yield at most weak `mentions`/`related` candidates. Argument-class
  edges (`supports`/`contradicts`/`extends`) are **never** auto-promoted;
  the act-promotable allowlist is `{mentions, related, cites, version-of}`,
  and its tuning is deferred until real usage data exists. Extraction
  provenance makes re-chunks add-only and keeps hand-curated links safe.
- **Enrichment merge by field authority** (supersedes 30's merge slices;
  30's spike lessons are binding): per-field best-source-wins **with
  provenance**; references are the union across providers deduped by DOI (no
  single provider is complete); author sub-fields are never paired by index
  across sources; provider output is claims, not ground truth; high-authority
  conflict marks `provider_coverage = degraded` and raises attention, never a
  silent overwrite. Degraded acceptance is a scope decision that bypasses no
  content check. Capture-commits-first and scriptable-before-LLM (30) carry.
  Two operational policies bind (providers drift, extractors upgrade):
  provider-side record drift and **work-ID merges raise attention and never
  auto-merge** Memoria works or digests (historical provider IDs are kept as
  aliases; per-field drift observed at re-enrichment is journaled so the
  re-enrichment cadence is calibrated from measured volatility); and anchors
  are **re-anchored, never silently rebound or dropped**, across extractor
  upgrades (old text blobs are never deleted; exact-then-fuzzy re-anchoring;
  failures become orphaned-anchor attention items — the Hypothes.is lesson).
  Semantic Scholar is **conditional, default-on when keyed** (reference union,
  citation intents — the free Tier-0 contradiction candidates — TLDRs, SPECTER
  embeddings; never promotion-required); scite.ai is an optional, explicitly
  opted-in provider of the same signal class. Like every provider and judge:
  proposers, never authorities.
- **Gap engine + saturation.** Gap analysis reads checked inputs only, scores
  on fixed `{0,1,2}` ordinals (confidence = confidence the gap is real), and
  emits the project saturation block (a claim is saturated with ≥1 addressed
  support and ≥1 counterpoint) as the compose-flow phase signal. Advisory,
  never gating.
- **Runner policy.** Two OpenAI-compatible providers (`local`, `gateway`);
  operation manifests **declare untrusted fields** and the runner serializes
  them into sealed data blocks — raw source text never interpolates into an
  instruction template (a manifest violating this fails to load); sealing
  narrows the channel without making the model unsteerable, so every
  text-reading operation carries a negative poisoned-input fixture.
  Providers:
  each operation pins `runner.test` and `runner.live`, selected by
  `--mode test|live`; the manifest is the hard ceiling; resolved model and
  actual token cost are journaled per run. `eval select-models` pins the
  cheapest candidate that passes the operation's bar — human-triggered and
  inspectable, never an online optimizer. Non-sandbox use is licensed only by
  the **live** model's seeded-error verdict, per `(operation, model, mode)`.
- **Shadow-first calibration, generalized** (66's contract, now the rule for
  every score): a new score reports and is journaled but changes no routing,
  promotion, or visibility until its thresholds are grounded on recorded PI
  dispositions (ADR-128) with a named fixture and pinned model. 56's rule
  carries: gate the uncertainty, not the category — below-floor identity
  calls flag, never merge. 38/39's capabilities (pre-file similarity check,
  acceptance checklists) are re-scoped as shadow-mode candidates for the
  `new note` flow, to be enabled only against usage data.

**Amendment to ADR-11** (which stays accepted): whole-system vault-eval
verdicts remain diagnostic and never gate work; `eval select-models` gating a
*build-time model choice* is a different act and is permitted.

## Consequences

- Every LLM opinion in the system is a proposer feeding attention; every
  auto-action is deterministic, allowlisted, and reversible.
- Every tunable number ships behind `production_enabled: false` semantics;
  the first grounded thresholds arrive with beta-era disposition data.

## Alternatives considered

- **LLM judge as contradiction/dedup authority** — rejected (GBrain's failure;
  09/10's own framing; ~28% wrong belief-flips in ConCoRD-class systems).
- **Hard-excluding superseded claims from retrieval** — rejected (breaks
  cross-period/evolution queries; TEMPO).
- **Auto-typing bare wikilinks into argument edges** — rejected (corrupts the
  argument graph; a bare link means "see also").

## Related

- Design §4/§7/§8/§9/§10/§14; ADR-127 (propagation), ADR-128 (disposition
  telemetry the calibration reads).
