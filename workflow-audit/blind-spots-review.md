# Blind-spots review — docs/explanation/ + design-history/ vs the dossier — 2026-07-09

Two sweeps (`wf_89a06d68-3f1`: all of docs/explanation/, 5 assessors;
`wf_12d87dbb-4a1`: all 21 design-history chapters + arcs, 4 assessors)
checked the day's decisions against the repo's recorded design reasoning.
Verdict: **the dossier is not law yet — it is one side of a conversation
with a decision record it never consulted.** Roughly half of it re-derives
recorded decisions (usually in weaker form); a significant set *reverses
recorded verdicts without superseding them*; and the record holds ~15
genuine blind spots the dossier must absorb. Per the repo's own rule,
supersession is a decision, not drift.

## A. The supersession ledger — reversals needing explicit superseding decisions

**Owner rulings (same day):** (1) most of the recorded verdicts below
were convenient decisions at the time — today's reversals stand;
(2) **ADRs and their unlock conditions are historical reference only —
never justification, never evidence.** No dossier decision owes a
"superseding decision" to any ADR; this ledger is therefore a *reference
map of where today diverges from history*, not a list of obligations.
The only sweep findings retaining force are those standing on **current
facts or current merit**: fulltext (the `work_id#^pNNNN` anchor substrate
is a fact of today's code; the keep-test is a live design value) and
event log (the journal-head tamper anchor was spike-proven; the plane
decomposition serves requirements that still differ). Everything else in
Section A is context, Section B survives only where a formulation is
better *on its merits*, and Section C's blind spots are facts regardless
of provenance.

1. **The daemon (item 12/reactive substrate)** reverses: ADR-49
   (file-watcher write-gate daemon deliberately not built), alpha.14 ("no
   internal daemon"), alpha.16 ("Resident daemon: Not adopted"), arc (f)
   ("no always-on process"). Must answer: what changed about the
   acceptable staleness window. Today's answer exists (capacity + UX; the
   barrier stays the enforcement) — alpha.19's same-transaction verdict
   cascade was *built precisely so a daemon is never load-bearing*, which
   is the superseding decision's strongest ground.
2. **Fulltext v2** reverses alpha.16/18/19 (adopted `fulltext.md` design,
   refined **two days before today**). Bigger than a reversal: it
   **destroys the `work_id#^pNNNN` anchor substrate** that evidence
   markers, digest anchor-checks, and three-way `mc` trust are built on,
   and it weakens the recorded keep-test (what survives when Memoria
   disappears). The superseding decision must ship the replacement
   locator contract, the `%%ev%%` migration, the digests/ fate, and the
   post-v2 keep-set (PDF + exported spans?).
3. **Vault-as-one-OKF-bundle** reverses alpha.11 ("the workspace is
   deliberately NOT an OKF bundle") and alpha.15/ADR-107 ("OKF is a fit
   for the boundary, not the core — its prose-typed relationships are the
   inverse of Memoria's thesis; Memoria is deliberately *ahead* of OKF").
   Reconciliation available: Memoria as a *strict producer profile* whose
   bundles are OKF-consumable while internally typed — but the recorded
   typed-edges-vs-permissive-consumption conflict must be answered, and
   "self-contained" scoped (a detached bundle loses verdict state).
4. **Warrant-leaning-node (item 8)** re-opens ADR-79: warrant reserved as
   optional attribute, judged "the single biggest labor sink for the
   least deterministic payoff," with a recorded unlock condition — "one
   real project comes in under PI-touch budget" — that is **not yet met**
   (no project has ever run). The four node-side weights are real, but
   the ratifying brainstorm must engage ADR-79, and the unlock condition
   suggests: decide after the first real project, not before.
5. **Six-role Toulmin basis (pillar 3)** collides with ADR-65
   (earn-each-type: one typed value at a time, after measured need — "a
   half-populated typed field returns incomplete answers and erodes
   trust"), ADR-126 (claim/question/thesis are *flippable roles, not
   types*), and the retired claim-maturity ladder. Reconciliation: the
   six components as **roles carried by relations and demandable slots**,
   not six node types — which is what the hybrid already implies; the
   superseding decision should say so explicitly and adopt earn-each-type
   for the relation vocabulary.
6. **Origin-blind blast radius (axiom 2)** reverses ADR-127/alpha.11's
   twice-decided origin-AWARE propagation (machine-derived auto-reverts;
   PI-authored gets ask-routed flags, never auto-destroyed). The day
   already found the scoping once (rollback = derivation topology);
   the record demands it be formal: **axiom 2 governs epistemic
   consequences (flags, demotions, gap findings — origin-blind); write
   and revert *authority* stays origin-gated (human spans protected).**
   Multiple independent sources converge on exactly this split.
7. **event_log as sole authoritative journal** reverses ADR-25 (two logs,
   one writer each; combined log rejected as "too verbose to verify or
   too noisy to read"; per-write hash *pairing*, not a chain) and ADR-104
   (three telemetry planes with opposite requirements; single substrate
   rejected). Also: the alpha.12 spike proved hash chains need the
   **git-tracked `journal-head` anchor** for tamper evidence; per-machine
   JSONL files exist for future multi-machine append-without-collision.
   The T0 repair must be redesigned as *reconciliation with a verifier
   and one authoritative trust-read path*, not naive consolidation.
8. **Editor plugin as primary surface (item 7)** collides with alpha.14
   ("dropped, not deferred" as required surface; product fully operable
   from vim) and the Obsidian page ("a plugin-rendered surface would be
   opaque to CLI/runtime checks"). Reconciliation the strategy must
   state: **the plugin renders only what CLI/files also expose** — pure
   renderer, never truth-bearing, never required.
9. **context.set/read bus + SessionStart hook (item 7)** brushes ADR-130
   (rejected shared mutable agent↔UI state — the CopilotKit-class
   inversion; read scoping enforced in-engine; "a wrapper holding logic
   is a gate failure") and alpha.10's hard-deny of cross-session history
   channels. The bus needs: an owner, enqueue-only write discipline,
   ephemerality (per co-pi.md: durable memory = checked workspace state,
   never a transcript channel), and read-scope semantics.
10. **Memoria-inside-Memoria (item 19)** vs arc (j): live ADRs were
    retired *because* old opinions looked authoritative after the thesis
    moved. Decisions-as-live-claim-notes must not recreate that: one
    mechanism owns decision authority (ledger→frozen chapter vs claim
    graph), explicitly reconciled.
11. **Autoresearch pillar** vs the refused scalar-optimization family
    (why-pattern-provenance: "autonomous keep/revert, tournament
    evolution, confidence-routed gate bypass, learned reviewer
    preferences") and why-not-autonomous's requirement of a superseding
    decision per loop. The instrument-only fence + alpha.17 §6's four
    concrete rules (throwaway vault, `production_enabled:false`, no real
    run ids/commits/exports/graph state) are the reconciliation — adopt
    them verbatim; and note "learned reviewer preferences" stays refused.
12. **Two-zone model**: compatible **only** as state-not-folders
    (promotion is a record update; a note is born and dies in its type
    home — ADR-47/50, arc (b)). The statement must say zones are states,
    not places. Also absorb ADR-128: approval-at-write measurably doesn't
    buy correctness — which *supports* checked-means-checks-passed.

## B. Richer prior formulations to adopt (the record said it better)

- **"Traces and holds, never true"** + *calibrated certainty* as the
  axiom-1 slogan (peer-reviewer.md).
- **"Propose, not dispose"** + the three orthogonal signals (execution
  status / attention state / machine recommendation — never a gate).
- **The keep-test** as the placement-doctrine discriminator: "does the
  user need this to keep thinking and writing outside Memoria?" — plus
  16-alpha §4: operational ledgers are *not rebuildable* and need honest
  backup (the trust plane is not derivable-from-files).
- **Lazy, impact-ranked blast radius** (alpha.5): eager re-confirmation
  of every downstream edge *is the sunk-cost trap inverted*; carry edges
  forward as stale, re-confirm on-path/high-impact lazily.
- **Anti-persuasion as the fence rationale** (co-pi.md: "a conversation
  drifts, accumulates context, and gets persuaded; a request envelope
  does not") + ADR-30's fenced pattern (deterministic spine, named
  judgment holes, schema-constrained) + ADR-57's batch-invariance
  evidence (1,000 samples at temperature 0 → 80 distinct outputs).
- **Attenuation-only delegation** for T2 manifests: request narrows,
  never widens, manifest authority.
- **"Make each review cheaper, not fewer reviews"** as T3's purpose
  statement; **stakes-based gating** (over-gating trains rubber-stamps).
- **Loudness taxonomy + batch worklists** (one aggregate prompt → a
  file-backed worklist for high-cardinality decisions) — the delivery
  layer the reactive substrate lacks.
- **Contradiction vs supersession as distinct types** (open tension vs
  resolved temporal replacement) — blast-radius typing must preserve it;
  **archive-in-place** is the only disposition for wrong claims.
- **Honesty in three recorded forms**: denominators, stated search sets,
  honest-empty. **Continuous promote-back** during projects, not only at
  close. **Deterministic-first class test** for every fenced LLM op.

## C. Genuine blind spots (the dossier never touched)

1. **Disposition telemetry is non-backfillable** (ADR-128: "every day
   they stay empty is permanently lost data") — it must exist **before**
   the 1000-paper import, or the calibration baseline is lost forever.
   This resequences onboarding.
2. **Bulk admission flood mechanics**: per-source candidate cards ×1000,
   the ~50-work vocabulary-consolidation window blown in one step,
   duplicate-triage and retraction-check waves, "near-empty is healthy"
   queue semantics destroyed, review collapse beyond ~60-minute batches.
   Onboarding needs a bulk-admission mode: batch worklists, quiet
   loudness, a vocabulary bootstrapping stage. Also alpha.14 removed
   Zotero-specific import (BibTeX/CSL only, with a negative gate) — the
   import goes through generic BibTeX, not a Zotero surface.
3. **Prompt injection via sources** — alpha.11 names it "the single risk
   most likely to force a gate back in"; structural checks are blind to
   crafted injections; egress rests on schema-hiding in places. Bulk
   external ingestion + agent-of-choice reading raises exposure; the
   trust story needs the injection appendix's provenance-triggered
   checkpoint, and fenced ops need abstain paths + adversarial overlap
   fixtures before any semantic dedup/supersession gate.
4. **Cost discipline**: "budget discipline replaces metric discipline" —
   the daemon tiers and bulk enrichment need token ceilings, price
   tables, circuit breakers, run attribution (Guard-brokered egress).
5. **Cross-store crash atomicity** — the alpha.12 spike *failed* on
   hash-only replay; durable payload bytes + crash-at-each-boundary
   proofs are the recorded bill any journal/daemon change re-opens.
6. **Precondition hashes for deferred tiers** (on-quiet/nightly jobs must
   not run against state they weren't scoped for) + **collision domains**
   (three tiers targeting one file need single-request attribution) +
   single-dispatcher rule (two machines racing one queue).
7. **The seeded-error license** — every release gates non-sandbox use on
   the verdict (recall 1.0, false-clean 0); the roadmap has no verdict
   gate anywhere, so item 19 is formally unlicensed until it passes.
8. **The cassette verification spine** (ADR-80/29) — the testability
   story for daemon triggers and fenced ops already exists; use it.
9. **Human-side back-pressure** — WIP caps so "reviewed" never silently
   becomes "machine finished"; the machine cadence needs its consuming
   human ritual (weekly review) or nightly tiers accumulate debt.
10. **"Given facts from ingest"** — a fourth placement lane
    (neither authored/judged/derived); every item-20 adapter produces it.
11. **Upgrade reconciliation layers** (ADR-76): who owns steering.md,
    manifests, migrations at upgrade time (release-wins vs
    customize-preserve) — item 20/T1 never says.
12. **alpha.20's deferred-behind-empirical-blockers list** — the dossier
    answered several questions (onboarding corpus, PI surface, retrieval
    promotion, host/stack) that the record holds open *pending data the
    empirical-event plumbing was built to collect*. Either route through
    the data or supersede the deferral explicitly.

## D. The meta-lesson

Today's dossier collided with its own decision record because the record
was not in the loop — 21 chapters of dated verdicts, none consulted at
decision time. This is the strongest possible argument for item 19's
Memoria-inside-Memoria: a decision graph with gap analysis would have
surfaced ADR-79 the moment the warrant discussion began, and ADR-127 the
moment axiom 2 was drafted. The immediate fix is procedural: **a
supersession pass before implementation** — each Section-A reversal
becomes a dated superseding decision answering the recorded reasons (most
of today's reasoning suffices; writing it down is the work), and the
Section C blind spots merge into the roadmap items they gate.
