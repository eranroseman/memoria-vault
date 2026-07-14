# Warrant → grounds rename — sweep manifest

Date: 2026-07-14. Status: **implementation input** for the terminology ruling in
[2026-07-14-evidence-set-grounds-contract-design.md](2026-07-14-evidence-set-grounds-contract-design.md) §2 (issue #1293).

Produced by a 43-file audit classifying every non-archive "warrant" occurrence
(rename-to-grounds / correct-as-is / general-English / durable-on-disk), with the
three cross-file conflicts adjudicated in the PI session: "executable warrant(s)" /
"computed-warrants" → grounds (all 8 sites); "checks passed and warrants resolve" →
grounds (all 5 sites); "stale, under-warranted, needing re-confirmation" →
under-grounded (both sites; the formal "Warrant lost" consequence type stays).
Migration/back-compat rows are MOOT: no vault exists beside the sandbox, so renames
land outright with no shim.

# Warrant → Grounds Terminology Sweep — Rename Manifest (Issue #1293)

Source: per-line classifications from the independent audit pass over every file containing "warrant". This section is the authoritative sweep list for the beta.1 evidence-set/grounds rename.

---

## 1. Rename mapping table

### 1.1 Code identifiers — code-artifact `purpose` enum (`warrant` → `grounds`)

| Old | New | Reason | Sites |
|---|---|---|---|
| `purpose: str = "warrant"` (default param) | `purpose: str = "grounds"` | Enum value for why a code-artifact exists (evidence backing vs. deliverable); flows into frontmatter and SQLite | `src/memoria_vault/runtime/code/records.py:20` |
| `CHECK (purpose IN ('warrant', 'deliverable', 'both'))` | `CHECK (purpose IN ('grounds', 'deliverable', 'both'))` | Same enum, persisted DB constraint | `src/memoria_vault/runtime/schema.sql:301` |
| `if purpose not in {"warrant", "deliverable", "both"}:` | `{"grounds", "deliverable", "both"}` | Same enum, validation set | `src/memoria_vault/runtime/state.py:3429` |

### 1.2 Code identifiers — `code-warrant:` marker family (evidence-set "computed" item type)

| Old | New | Reason | Sites |
|---|---|---|---|
| `_CODE_WARRANT_RE` | `_CODE_GROUNDS_RE` | Private regex constant matching the marker prefix | `evidence.py:16,54,66` |
| `code-warrant:` (literal marker prefix, regex + on-disk text) | `code-grounds:` | The actual on-disk item-ref prefix inside `%%ev:...items=...%%` markers | `evidence.py:17` (regex literal); `knowledge.py:3321` (detection regex `\b(analysis-computed\|analysis code\|code-warrant)\b`); `tests/test_code_artifacts.py:64` (fixture marker text); `docs/reference/control-and-policy/evidence-sets.md:45,65`; `docs/superpowers/specs/0.1.0-beta.1-design.md:700` (three mentions in the same table row: header, "`code-warrant` evidence items...", "computed/code-warrant review"); `docs/explanation/rationale/boundaries/why-deterministic-methods.md:50` ("code-warrant refs", prose) |
| `CodeWarrantRef` (dataclass) | `CodeGroundsRef` | Parsed representation of the marker item | `evidence.py:29,57` |
| `parse_code_warrant_ref` | `parse_code_grounds_ref` | Public parser, cross-module | `evidence.py:52`; `state.py:28` (import), `state.py:2667` (call) |
| `"invalid code-warrant ref: {ref!r}"` | `"invalid code-grounds ref: {ref!r}"` | Runtime exception message | `evidence.py:56` |
| `return "code-warrant"` / `== "code-warrant"` (kind-discriminator string) | `"code-grounds"` | In-memory ref-kind tag from `evidence_ref_kind()` | `evidence.py:67`; `state.py:2632,2650` |
| `_code_warrant_resolves` | `_code_grounds_resolves` | Private resolver for a code-backed evidence item | `state.py:2651` (call), `state.py:2664` (def) |
| `code_warrant_complete` | `code_grounds_complete` | Checks whether the referenced code run/artifact is complete | `code/runs.py:26` (def); `state.py:2665` (import), `state.py:2668` (call) |
| local var `warrant` (a `CodeWarrantRef`/`CodeGroundsRef` instance) | `grounds` | Renames alongside the type | `state.py:2667,2670,2671,2672` |

### 1.3 CLI/API-visible output — `under-warranted` gap kind

| Old | New | Reason | Sites |
|---|---|---|---|
| `"under-warranted"` (GAP_KINDS member / `kind` literal) | `"under-grounded"` | `analyze-gaps` output value meaning "notes exist without checked source support" | `src/memoria_vault/runtime/knowledge.py:60` (GAP_KINDS), `:487` (assignment); `tests/test_worker_knowledge_cycle.py:90`; `tests/test_gap_analysis.py:172,174,604,606`; `docs/explanation/knowledge/document-types.md:53`; `docs/reference/commands-and-transports/system-actions-operations.md:123` (prose: "topic, digest, warrant, and project argument gaps" → "...grounds, and...") |
| `"but no checked sources or digests warrant it."` | `"...ground it."` | `why` text attached to the gap payload | `knowledge.py:491` |
| test mnemonic topic key `"warrant"` (fixture-only, not production) | `"grounds"` | Test fixture slug chosen to exercise the gap kind; no migration concern | `tests/test_gap_analysis.py:107,108,166,173` |

### 1.4 Docs prose — "evidence-set as warrant" (§1.4-family phrasing)

| Old | New | Sites |
|---|---|---|
| `Evidence sets are the draft-time **warrant** contract` | `...**grounds** contract` | `evidence-sets.md:10` |
| `Running code **warrants** the output provenance` | `Running code **grounds** the output provenance` | `evidence-sets.md:67` |
| `**Warrant** = an evidence-*set*, typed.` | `**Grounds** = an evidence-*set*, typed.` | `0.1.0-beta.1-design.md:169` |
| `implicit (no resolvable **warrant**)` | `implicit (no resolvable **grounds**)` | `0.1.0-beta.1-design.md:179` |
| `evidence-incomplete **warrants**` | `evidence-incomplete **grounds**` | `0.1.0-beta.1-design.md:234` |
| `implicit/multi-hop **warrants** are flagged` | `implicit/multi-hop **grounds** are flagged` | `0.1.0-beta.1-design.md:380` |
| `broken-**warrant** export refusal` | `broken-**grounds** export refusal` | `0.1.0-beta.1-design.md:701` |
| `single-span, multi-span, multi-hop, or implicit **warrants**` | `...**grounds**` | `0.1.0-beta.1-requirements.md:374` |
| `Evidence-set review UI for multi-hop/implicit **warrants**` | `...**grounds**` | `0.1.0-beta.1-requirements.md:391` |
| `chained \`ev-xxxxxxxx\` id for a multi-hop **warrant**` | `...multi-hop **grounds**` | `data-structure-analysis.md:2497` |
| `recorded **warrant** (sentence)` | `recorded **grounds**` | `pattern-provenance.md:74` |
| `code-execution **warrant** substrate` | `code-execution **grounds** substrate` | `2026-07-12-beta.1-consolidation.md:56` |
| work-unit slug `warrant-evidence-set` | `grounds-evidence-set` | `2026-07-12-beta.1-consolidation.md:159` |
| `verbatim **warrants**` | `verbatim **grounds**` | `literature-pushback.md:14` |
| `code-warrant refs` (prose form) | `code-grounds refs` | `why-deterministic-methods.md:50` |
| `Computed **warrants** can prove...` | `Computed **grounds** can prove...` | `why-write-half-is-bounded.md:56` |
| `declared **warrants** pass` | `declared **grounds** pass` | `design-principles.md:41` |

### 1.5 CONFLICTED phrase — "executable warrant(s)" / "computed-warrants" (code-execution lane)

The per-file audits disagree on this exact phrase family. **Flag for explicit adjudication before mechanical sweep** — do not resolve silently:

- **Classified `rename-to-grounds`:** `0.1.0-beta.1-design.md:278,282,401,648,700`; `0.1.0-beta.2-scope.md:42`; `2026-07-12-beta.1-consolidation.md:164,225` ("computed-warrants")
- **Classified `correct-as-is`** (with the auditor's own caveat "worth a second look," "novel coined term not explicitly named in warrant-ontology-brief.md"): `0.1.0-beta.1-requirements.md:81,377`

Recommendation: since `docs/superpowers/specs/warrant-ontology-brief.md` (the authoritative, explicitly-preserved ontology doc) never uses "executable warrant" and the phrase's only referent is code-execution-derived evidence (the "computed" derived type, same family as `code-warrant:`), the design intent is almost certainly the **grounds** sense. Recommend renaming all eight sites uniformly, including `requirements.md:81,377`, for internal consistency — but this needs sign-off since two independent per-file passes reached opposite conclusions on materially identical text.

### 1.6 CONFLICTED phrase — "checks passed and warrants resolve"

Nearly identical sentences across four docs received opposite verdicts:

- **Classified `rename-to-grounds`:** `why-review-gate-is-structural.md:17` ("the required warrants resolve"), `:65` ("required checks and warrants exist as recorded state"); `design-principles.md:41,81` ("declared warrants pass" / "required checks and warrants passed"); `what-memoria-is.md:32` ("required checks and warrants passed")
- **Classified `correct-as-is`:** `docs/explanation/execution/control-plane/states.md:75` — the *identical* phrase, "checked materialization means checks passed and warrants resolve," reasoned instead to refer to the unstated-warrant/argument-graph family.

Recommendation: these are the same underlying claim (what `checked` state requires) repeated across four docs for the same feature; they should get the **same** verdict. Given `design-principles.md:81`'s own text is immediately followed by a callout distinguishing today's shipped "checks and warrants" from the *planned* "complete Toulmin warrant graph" (line 84–85, correctly preserved), the weight of evidence favors **grounds** for all five sites including `states.md:75`. Adjudicate before sweeping.

### 1.7 CONFLICTED phrase — "computed and affected nodes are marked — stale, under-warranted, needing re-confirmation"

This is the most concrete conflict found: **the same sentence, verbatim**, appears in two docs with opposite classifications:

- `docs/superpowers/plans/2026-07-12-docs-migration.md:236` → classified `rename-to-grounds` (traced to `knowledge.py` GAP_KINDS)
- `docs/explanation/knowledge/consequence-propagation.md:38` → classified `correct-as-is` (traced to the "Warrant lost" consequence-type defined two lines above it, at `consequence-propagation.md:25`)

Because `docs-migration.md`'s content at this point is drafted/quoted material intended to become `consequence-propagation.md`'s prose (per the migration plan's own structure), these two sites should not diverge. Re-read both docs' full surrounding paragraphs before deciding; the immediate local context in `consequence-propagation.md` (directly under a "Warrant lost" bullet) leans Toulmin/correct-as-is, but the sentence's shape ("marked stale, under-warranted, needing re-confirmation") also matches gap-analysis phrasing elsewhere. **Do not sweep either side mechanically — decide once, apply to both.**

---

## 2. Durable-on-disk-format callouts

All of the following change bytes that already exist in shipped vaults and require a migration or compatibility shim — not a plain code/doc edit:

| Item | Where it lives on disk | Migration required |
|---|---|---|
| `purpose: warrant` in code-artifact frontmatter | Vault markdown, written via `write_text_durable` in `create_code_artifact` (`code/records.py:20`) | Read-path back-compat: existing files with `purpose: warrant` must still parse; either a one-time frontmatter rewrite migration, or a read-time alias mapping `warrant→grounds` at load time. |
| `purpose` column value `'warrant'` | `code_artifacts` SQLite table (`schema.sql:301`, validated in `state.py:3429`) | `UPDATE code_artifacts SET purpose='grounds' WHERE purpose='warrant'` migration, run in lockstep with the CHECK-constraint edit (SQLite CHECK constraints are not retroactively enforced on existing rows, but any future write path validating against the new enum will reject unmigrated old rows). |
| `code-warrant:<run_id>:<artifact_id>:<sha256>` marker-item prefix | Inside `%%ev: ... items=...%%` markers embedded in vault note/draft markdown bodies (confirmed on-disk by `tests/test_code_artifacts.py:64`'s fixture and documented at `evidence-sets.md:45,65`) | Existing vaults contain literal `code-warrant:` text in note bodies. Options: (a) read-time regex alias in the parser accepting both `code-warrant:` and `code-grounds:` indefinitely, or (b) a one-time content migration rewriting the literal marker text in all notes containing it, re-run through `rebuild_evidence_sets_from_markers`. Recommend (a) — cheaper, no bulk rewrite of user prose. |

### Hash-safety of the `code-warrant:` → `code-grounds:` rename

**This rename is hash-safe.** Per `docs/reference/control-and-policy/evidence-sets.md`, the `evidence_bindings` immutable hash covers the *surrounding prose block* with the `%%ev:...%%` marker **stripped out before hashing**. The `code-warrant:` prefix lives entirely inside the marker's `items=` field — i.e., inside the exact span that gets stripped before the prose is hashed. Renaming the marker-prefix text therefore:

- **Does not** change any existing `evidence_bindings` hash value (the hash was never computed over the marker content in the first place).
- **Does** require the marker *parser* (`_CODE_WARRANT_RE` / `parse_code_warrant_ref` / `evidence_ref_kind`) to keep recognizing old-format markers already written into vaults, since those markers are still live, resolvable evidence-set items — this is a parsing/back-compat concern, not a hash-integrity concern.

No other durable-on-disk item in this sweep touches hashed content; all other renames are code identifiers, in-memory strings, or prose.

---

## 3. Risk tiers

**(a) Docs-prose-only — trivial, no migration**
`evidence-sets.md:10,67`; `0.1.0-beta.1-design.md:169,179,234,278,282,380,401,648,700(prose),701`; `0.1.0-beta.1-requirements.md:374,391,(81,377 pending conflict-1.5)`; `0.1.0-beta.2-scope.md:42`; `2026-07-12-beta.1-consolidation.md:56,164,225`; `pattern-provenance.md:74`; `literature-pushback.md:14`; `why-deterministic-methods.md:50`; `why-write-half-is-bounded.md:56`; `design-principles.md:41,81`; `what-memoria-is.md:32`; `why-review-gate-is-structural.md:17,65`; `document-types.md:53`; `system-actions-operations.md:123`; `data-structure-analysis.md:2497`; plus conflicted sites in 1.6/1.7 once adjudicated.

**(b) Internal code identifiers — safe, no external contract**
`evidence.py:16,29,52,54,56,57,66,67`; `state.py:2632,2650,2651,2664,2665,2667,2668,2670,2671,2672`; `code/runs.py:26`; `knowledge.py:3321` (detection regex, internal check, though it inspects durable content — see tier d); test updates in `tests/test_code_artifacts.py:64`, `tests/test_gap_analysis.py:107,108,166,173`.

**(c) Public API / CLI-visible identifiers — needs a changelog note**
`under-warranted` → `under-grounded` gap kind (`knowledge.py:60,487,491`; consumed via `analyze-gaps` worker operation and CLI/API JSON) — any script or integration that branches on `gap_type == "under-warranted"` breaks silently without a changelog entry and, ideally, a one-release compatibility alias. `code-warrant` ref-kind string returned by `evidence_ref_kind()` is in-memory only (tier b) but worth a mention if it's ever surfaced in CLI/API output beyond `state.py`'s internal comparisons — confirm no external surface reads it before downgrading from (c).

**(d) Durable on-disk marker/format strings — needs migration or compatibility shim**
`purpose: warrant` code-artifact frontmatter + `code_artifacts.purpose` DB column (`records.py:20`, `schema.sql:301`, `state.py:3429`); `code-warrant:` marker-item prefix (`evidence.py:17`, `knowledge.py:3321`, and all doc descriptions of the marker format). See §2 for the specific migration/shim per item. `knowledge.py:3321`'s regex is a *reader* of this durable format (detecting the marker text inside draft content), so it must be updated in lockstep with the marker-prefix rename, but it does not itself need a migration — only the marker text it scans does.

---

## 4. Explicit "do not touch" list (`correct-as-is`)

Grouped by concept, all deliberately excluded because they name the genuine Toulmin inference-license warrant, the six-role argument graph, or a distinct NLI-judge field — not the evidence-set/grounds concept:

**Toulmin six-role graph / warrant-ontology (node-vs-edge) discussion**
`docs/superpowers/plans/2026-07-12-docs-migration.md:60,62,151,183,223,566`; `docs/explanation/rationale/foundations/intellectual-foundations.md:63,65`; `docs/reference/data-model/glossary.md:50`; `docs/explanation/rationale/foundations/design-principles.md:84,85`; `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md:110,137,142,143,226,304,306,308,341,375`; `docs/superpowers/specs/0.1.0-beta.2-scope.md:56,57,58,61,63,64,65,67`; `docs/superpowers/specs/0.1.0-beta.1-decisions.md:31`; `docs/superpowers/specs/2026-07-12-surface-design-notes.md:89,91`; `docs/superpowers/specs/data-structure-analysis.md:1895,1917,1919`; `docs/superpowers/specs/0.1.0-beta.1-empirical-use-action-plan.md:15,135,160,197`; all of `docs/superpowers/specs/warrant-ontology-brief.md` (title, lines 1,15,23,26,28,31,39,40,42,48,52,53,62,63,74).

**`unstated-warrant` verification finding kind**
`src/memoria_vault/runtime/knowledge.py:965,2959`.

**NLI tension/contradiction-judge `warrant` field (Tier-1/Tier-2 verdict justification, distinct from the `evidence`/quote fields)**
`src/memoria_vault/runtime/integrity.py:781,811,826,1444,1450,1455,1515,1523,1537,1552,1556,1559,1560,1568,1578,1654,1669`; `src/memoria_vault/runtime/knowledge.py:1496,1518`; `tests/test_exploration_channel.py:152,194,202`; `tests/test_integrity_surface_tensions.py:56,94,147,154,190`.

**Seeded-error "unwarranted claim" scenario (Toulmin sense: quote exists but fails to license the claim)**
`src/memoria_vault/runtime/seeded_errors.py:236,238`.

**Consequence-propagation "Warrant lost" (inference license connecting evidence to claim fell)**
`docs/explanation/knowledge/consequence-propagation.md:25` (line 38 is contested — see §1.7).

**"checked materialization means checks passed and warrants resolve"**
`docs/explanation/execution/control-plane/states.md:75` (contested — see §1.6).

**Executable-warrant / computed-lane phrasing**
`docs/superpowers/specs/0.1.0-beta.1-requirements.md:81,377` (contested — see §1.5).

---

## 5. `general-english` hits (no rename, ordinary word "warrant/unwarranted/warranted")

13 hits across 8 files, none referencing either Toulmin sense:
`docs/explanation/rationale/boundaries/why-not-autonomous.md:108`; `docs/how-to-guides/troubleshooting/fix-missing-query-results.md:18`; `docs/explanation/rationale/boundaries/why-write-half-is-bounded.md:49`; `docs/reference/commands-and-transports/system-actions-operations.md:136`; `docs/superpowers/specs/data-structure-analysis.md:1105`; `tests/test_draft_compose.py:51`; `tests/test_integrity.py:299,301,308,312`; `tests/test_seeded_errors.py:63,173,255`.
