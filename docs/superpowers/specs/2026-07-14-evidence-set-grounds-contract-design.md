# Evidence-set / grounds contract — beta.1 design

Date: 2026-07-14. Status: **design (PI-approved in session), pre-plan**.
Issue: #1293. Owns the V2 `evidence-set-contract` freeze blocker and the
warrant-terminology ruling scheduled by `warrant-ontology-brief.md`.

This spec is the concrete schema/state contract #1293's acceptance criteria
demand. It was stress-tested by a first-principles rethink-audit (blinded
clean-slate design + adversarial critique + prior-art research across four
families) and a machine-checked verification of the type-derivation rules;
supporting artifacts are listed in the appendix. Where this spec and
`0.1.0-beta.1-design.md` §1.4 disagree, this spec governs; §1.4 gets a
pointer patch (see §12).

## 1. Scope

Defines: the marker grammar, the five grounds types and their derivation,
resolution/state semantics (including nesting), the verification-finding and
export-refusal table, PI-disposition semantics, staleness propagation, and
the durability of the mint-once binding ledger.

Explicitly split from #560: **this contract is the MVP.** #560 owns the
later calibration/regression taxonomy (CiteME, Chain-of-Evidence) once real
drafts exist. Nothing here blocks it: verification is a pure function of
recorded state, so historical vault snapshots (vault + `.memoria` DB
together) replay to identical findings.

## 2. Terminology ruling: grounds, not warrant

Under the Toulmin pillar, an evidence set is **grounds** (the facts backing a
claim); **warrant** is the inference license connecting grounds to claim — a
different concept, owned by the six-role argument graph (G4) and the
warrant-ontology brief. The beta.1 design's "Warrant = an evidence-set"
wording (§1.4) is the collision the brief required this session to resolve.

**Ruling: full identifier sweep, warrant → grounds**, for every use of
"warrant" that means the evidence-set concept. Highlights (the complete
file:line manifest lives with the session artifacts, appendix):

- `code-warrant:` marker-item prefix → `code-grounds:`
- `CodeWarrantRef` → `CodeGroundsRef`; `parse_code_warrant_ref` →
  `parse_code_grounds_ref`; `code_warrant_complete` → `code_grounds_complete`
- code-artifact `purpose` enum value `warrant` → `grounds` (frontmatter
  default, `schema.sql` CHECK, `state.py` validation set)
- `under-warranted` gap kind → `under-grounded` (both the `GAP_KINDS` value
  and the two prose docs that echo it)
- docs prose per manifest, including "executable warrant(s)" /
  "computed-warrants" (8 sites) and "checks passed and warrants resolve"
  (5 sites) → grounds language

**Do not touch** (Toulmin-correct already): the `unstated-warrant` finding,
the six-role graph's warrant role, `warrant-ontology-brief.md`, the NLI
judge's `warrant` field in `integrity.py`, the seeded `unwarranted-claim`
error class, and consequence-propagation's formal "Warrant lost" consequence
type. General-English uses ("warrants further investigation") stay.

No migration path is needed: no Memoria installation exists beside the
sandbox (owner-confirmed), and the rename is hash-safe — the binding hash
covers the claim block with the `%%ev:%%` marker stripped before hashing, so
nothing inside `items=` ever touches a stored hash.

## 3. Marker grammar v2: id + items only

The marker is the durable, in-file source of a claim's grounding. Derived
fields must not be serialized: a stored copy of a derived value can only be
redundant or wrong. **Ruling: strip `type=`, `state=`, and `review=` from
the marker.** `items=` is the sole authoritative field; type, state, and
review-required are always re-derived (§4–§5). Human-readable status lives
in the verify report and preview surfaces, never in the marker.

```text
%%ev: ev-1234abcd items=<item>|<item>|...%%
```

- `ev-<8hex>` mint-once identifier, unchanged.
- `items=` is an ordered `|`-separated list; empty or omitted means no
  items (derives `implicit`).
- Item kinds (classification precedes rule evaluation; an item matching no
  grammar fails the record closed at parse):
  - **span** — `<work_id>#^p<NNNN>` (work charset `[A-Za-z0-9][A-Za-z0-9._-]*`,
    page `\d{4,}`), resolving through `passages.anchor`;
  - **set** — a nested `ev-<8hex>` reference;
  - **code** — `code-grounds:<run_id>:<artifact_id>:sha256:<64hex>`,
    pinning a recorded run/artifact/output-hash triple.
- Everything else about markers is unchanged: mint-once eligibility rules
  (plain top-level paragraph claims only), the fail-closed ambiguous-syntax
  rules, duplicate handling, and the immutable `evidence_bindings` claim-text
  hash (`block_text_sha256`, marker stripped before hashing).

Implementation note: `parse_evidence_marker` / `serialize_evidence_marker`,
their fixtures, and the content-security tests update together; compose
writes v2 markers. No data migration (no vault exists).

## 4. The five grounds types and their derivation

The author's only input is the items list; type is derived, never asserted.
Rules are first-match over the record's **own items** (never the nested
closure — typing stays a pure local function; nesting is handled by state,
§5). Machine-verified: the rules are a total, deterministic partition,
mutually exclusive even without ordering, and duplicate items never change
routing.

| # | Rule | Type | Routed |
| --- | --- | --- | --- |
| R1 | items empty | `implicit` | PI review |
| R2 | any set item, **or** span items naming ≥ 2 distinct works, **or** ≥ 1 code item mixed with ≥ 1 non-code (span or set) item | `multi-hop` | PI review |
| R3 | all items are code items (≥ 1) | `computed` | machine |
| R4 | all items are spans in one work: exactly 1 → | `single-span` | machine |
|    | … ≥ 2 → | `multi-span` | machine |

`review_required` := type ∈ {`implicit`, `multi-hop`}. Routing rationale:
the PI reviews exactly the shapes structure cannot decide — no cited
evidence at all, or a combination across independent evidence sources
(cross-work, nested indirection, or cross-kind text+computation mixes).
Same-kind multiplicity stays machine-decided.

Two rationale clauses the rules depend on (from the adversarial audit):

- **Multiple code items stay `computed` (machine).** Code gives the machine
  a verification handle text never does — every item is hash-pinned and
  re-runnable. Run-distinctness is a weak independence proxy (re-running a
  script mints a new `run_id`); counting it would route routine
  reproducibility re-runs to the PI as noise.
- **`work_id` is the declared independence boundary.** Two spans in one
  work are one authorial voice regardless of page distance. This leaks for
  container works (anthologies, proceedings): catalog such works per
  chapter, or accept that same-`work_id` spans are treated as one source.

Precision pins (each resolves an ambiguity two implementers would read
differently): distinct-work comparison happens after work-id normalization;
rules operate on classified item kinds, and an unclassifiable item fails the
record closed; counts are over the items multiset, not deduplicated; R3's
"all" guard is load-bearing — simplifying it to "any code item" recreates
the shipped masking bug; `multi-hop` is a routing bucket, not a topology
description (cross-work spans involve no literal hop).

### Examples (one per type, v2 grammar)

```text
single-span  %%ev: ev-3f9a2b10 items=smith2024climate#^p0042%%
multi-span   %%ev: ev-7c1d44e2 items=smith2024climate#^p0042|smith2024climate#^p0058%%
multi-hop    %%ev: ev-9a2e5f31 items=smith2024climate#^p0042|jones2023oceans#^p0017%%
multi-hop    %%ev: ev-b4c8d215 items=ev-3f9a2b10|jones2023oceans#^p0017%%   (nested)
multi-hop    %%ev: ev-c9d1e337 items=code-grounds:run-8842:fig3-table:sha256:<64-hex>|smith2024climate#^p0042%%   (mixed kind)
implicit     %%ev: ev-1b3c9d44 items=%%
computed     %%ev: ev-5e8f6a02 items=code-grounds:run-8842:fig3-table:sha256:<64-hex>%%
```

### One derivation, one owner

The shipped code has two divergent derivations: `_derived_evidence_type`
(`state.py`, rebuild path — never counts works, and a code item masks even a
nested set) and `_draft_evidence_type` (`knowledge.py`, compose path — can
only produce implicit/single-span/multi-span). Both are replaced by **one**
function in `state.py` implementing R1–R4; compose calls it. This closes two
confirmed review escapes: cross-work spans deriving `multi-span`
(unreviewed), and code items masking combinations (unreviewed).

## 5. Resolution, state, and nesting

`state` ∈ {`complete`, `evidence-incomplete`}, derived per record:

- **span** resolves iff the work's extracted content contains the anchor.
- **code** resolves iff `(run_id, artifact_id)` exists in the run ledger,
  the run succeeded, and the pinned output hash equals the recorded hash.
  Verification never executes code; re-running is out-of-contract work
  followed by editing the marker.
- **set** resolves iff the referenced set exists **and is itself
  `complete`** — completeness is transitive. Resolution is computed
  bottom-up in topological order over the set-reference graph; every member
  of a reference cycle (including self-reference) is `evidence-incomplete`,
  fail-closed, never fixpoint-guessed.
- `state = complete` iff every item resolves; `implicit` is always
  `evidence-incomplete` by construction.

This replaces the shipped presence-only nested check, under which a
multi-hop set could derive `complete` over an incomplete child and two
mutually-referencing sets derived `complete` with zero source spans between
them.

## 6. Findings and export refusal

Findings fall in three classes — the class, not the finding, defines what a
PI disposition may do:

**Permanent blocks** (no disposition clears; the cure is editing the draft
or the grounds):

| Finding | Severity | Trigger |
| --- | --- | --- |
| `evidence-text-drift` | high | claim block hash ≠ stored mint-once binding |
| `evidence-text-unbound` | high | stored binding missing, or anchored block unresolvable |
| `evidence-id-duplicate` | high | one id bound by more than one occurrence |
| `evidence-source-stale` | high | any work in the record's item closure has catalog `standing` ∈ {`retracted`, `superseded`}; carries `{work_id, path}` — empty path = direct, non-empty = inherited through nested sets |
| `no-evidence-set` | high | the draft contains zero evidence sets (names today's silent `ready=False`) |

**PI-clearable holds** (block until a disposition for this exact record):

| Finding | Severity | Trigger |
| --- | --- | --- |
| `evidence-incomplete` | high | `state = evidence-incomplete` |
| `review-required` | medium | `review_required = true` (implicit / multi-hop) |

**Advisories** (surfaced, never blocking):

| Finding | Severity | Trigger |
| --- | --- | --- |
| `evidence-source-archived` | medium | any closure work has `standing = archived` |

Export refusal derives from recorded state alone — files, DB, catalog
standing, run ledger — with no model judgment anywhere in the path. A draft
exports iff no permanent-block finding attaches and every hold is cleared by
a matching disposition (advisories never refuse). Structural-reference and
deterministic-number findings (§9) are unchanged and remain blocking.

Staleness clauses: standing is joined **live at verify time**, never cached
into the record (a source retracted years after a claim was written still
blocks). Propagation is transitive through resolvable nested sets at full
severity, with `path` distinguishing direct from inherited taint. An
**unset `standing` is `current` by design** — standing is PI-curated catalog
state, and the PI is the standing authority; this is a deliberate contract
clause, not an accident of a set-membership check. `evidence-source-stale`
is **not** PI-disposable: if the researcher's claim is about the retraction
itself, the cure is re-grounding on the retraction notice as its own catalog
work (the Crossmark pattern), not overriding the block.

## 7. PI dispositions: bound to content, append-only

`memoria project resolve-evidence … --decision accept|reject` appends a
journal event; it never edits the marker and never asserts truth.

**Content binding (new):** the disposition event records
`items_sha256` — SHA-256 over the UTF-8 bytes of the record's ordered items
joined by `|` (the exact serialized form). Verification honors a disposition
only while the record's current items digest matches. Editing the items
list voids the disposition (the journal keeps it; it is simply inert), and
the record re-routes to review. This closes the shipped hole where an
accepted id stayed accepted forever regardless of later item edits.

What a disposition can clear: `evidence-incomplete` and `review-required`
for the matching record (accepting an implicit set is the researcher owning
their synthesis — Rule 11's "specifically so identified" state). What it can
never clear: any permanent-block finding. That asymmetry is by construction:
tamper and staleness findings answer "is this the blessed text over sources
that still stand?" — not a question PI judgment is about.

## 8. Mint durability: bindings enter the journal

The `evidence_bindings` mint-once ledger currently lives only in SQLite
under `.memoria/` — which bundle export excludes and which is by design not
reconstructible from files. A folder-copied bundle therefore silently loses
every anti-tamper guarantee. Fix: at first binding, the trusted writer
appends an `evidence-minted` journal event
(`evidence_id`, `block_ref`, `block_text_sha256`); the bindings table
becomes rebuildable by replaying mint events, and tamper history travels
with the vault. Dispositions already journal; mints join them. This rides
the F2 journal-trust package (alpha.21) and its verifier.

## 9. Known limitations, stated honestly

- **Number checking is declared-pattern, not universal.** What ships:
  the slice-count sentence check (`deterministic-number-mismatch`) and the
  analysis-keyword scan (`analysis-number-evidence-incomplete`). The design
  doc's "every printed number is deterministic or incomplete" is a goal the
  contract does not yet enforce per-digit; a universal digit gate was
  evaluated and rejected (it deadlocks on export-generated text). Per-number
  grounding is an open beta.2 question, to be reopened with dogfood data.
- **Compose fabricates page anchors** (`#^p0001` per work). Span items on
  the compose path are work-level until R1's `source-span-anchor` unit lands
  real page anchors. The contract treats them as spans; their resolution is
  genuine (anchor existence is checked), their precision is not yet.
- **Replay caveat:** findings are functions of (files, DB, catalog standing,
  run ledger) at check time. Regression replay (#560) must snapshot vault
  and `.memoria` together; feeds F3's backup-as-data work.

## 10. Boundary decisions ratified (absorbed from closed issues)

- **#703 — claim-sentence classification:** out of beta.1 entirely. The
  "unsupported claim" refusal is the structural minimum (`no-evidence-set`);
  no per-paragraph coverage mandate, which would re-introduce the deferred
  semantic gate as a structural rule.
- **#704 — classical prose metrics:** diagnostic/report-only if ever built;
  orthogonal to this contract; never gate-adjacent without calibration
  evidence.
- **#369 — code handoff:** the `computed` type plus `code-grounds:` items
  *are* the coding handoff for beta.1. Code execution stays out; only
  recorded `code_runs`/`code_artifacts` are checked, never run.

## 11. Rejected alternatives (with flip conditions)

Evaluated via blinded clean-slate design + adversarial critique; rejected
for cause, revisable on the named trigger:

- **Marker/record split** (block-ID token + fenced grounding record):
  invited orphan-gate and set-lifecycle divergence holes; inline single
  construct stays. Flip: markers grow beyond one readable line in practice.
- **Separate hash-chained journal file:** global-brick failure mode on
  benign byte churn; the existing journal machinery suffices. Flip:
  multi-device sync or bundle-merge (both beta.2-registered) becomes real.
- **Universal digit-scan:** refuses its own export output; rejected (§9).
- **`gap` vs `none` item split** (pending-work vs authorial-stance instead
  of one `implicit`): defensible, deferred; `implicit` + PI routing covers
  beta.1. Flip: PI review overload, or gap analysis needs pending-work
  items as first-class input.
- **Warrant-node reification:** stays beta.2, evidence-gated on the
  touch-budget observation (no data exists; window extended). Interim
  Option B — roles on typed relations, promotion-ready edges — stands.

## 12. Acceptance criteria and implementation slices

#1293's checkboxes, mapped: concrete schema/state table — §§3–6 of this
spec (plus the §1.4 pointer patch below); one example per type — §4;
export refusal derivable without model judgment — §6; #560 relationship —
§1.

Implementation slices (each independently testable; feeds the plan):

1. Rename sweep (manifest-driven; code + tests + docs).
2. Marker grammar v2 (parser/serializer/fixtures/content-security tests).
3. Unified type derivation R1–R4; delete `_draft_evidence_type`.
   New tests: cross-work → `multi-hop` + review; code+span → `multi-hop`;
   same-work two-span control stays `multi-span`; fix the
   `test_evidence_markers.py` fixture that declares `multi-span` for a
   span+set mix.
4. Transitive resolution + SCC cycle detection; nested-incomplete and
   mutual-cycle fixtures.
5. Disposition `items_sha256` binding.
6. `evidence-source-stale`/`-archived` findings with `path`;
   `no-evidence-set` finding.
7. `evidence-minted` journal events + ledger rebuild (with F2).
8. Docs: patch `0.1.0-beta.1-design.md` §1.4 (fix
   "single-sentence/multi-sentence" wording, add `computed`, point here);
   update `docs/reference/control-and-policy/evidence-sets.md` to v2
   grammar and the findings table.

Slices 3–6 are small independent PRs; nothing blocks alpha.21.

## Appendix: session artifacts

Produced 2026-07-14 during the PI design session (scratchpad + task
outputs; git-recoverable from this session's records): the rename sweep
manifest (43 files audited, per-hit classification), the blinded clean-slate
design and its 17-finding adversarial critique, four prior-art research
digests (integrity/attestation, legal citators, document-embedded
contracts, scholarly claim-evidence), the machine-checked partition proof
for R1–R4 (252 quotient shapes), and the confirmed code-divergence
verification with file:line citations.
