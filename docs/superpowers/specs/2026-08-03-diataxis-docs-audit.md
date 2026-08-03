# Diátaxis Audit Record — Memoria docs, 2026-08-03

> **Status:** the confirmed findings below were repaired in
> [PR #1752](https://github.com/eranroseman/memoria-vault/pull/1752); the two
> reader-task coverage gaps are tracked as
> [#1753](https://github.com/eranroseman/memoria-vault/issues/1753) (evidence-set
> review queue how-to) and
> [#1754](https://github.com/eranroseman/memoria-vault/issues/1754) (MCP setup
> how-to). This file is the frozen audit record — kept for the coverage matrix,
> the accepted gaps, and the refuted-findings list, so a future audit does not
> re-litigate them.


**Method:** nine sectional auditors read every page in full and classified it; each
quadrant's findings then went to an independent skeptic instructed to refute them against
the file text and the repo's binding conventions (`CONTRIBUTING.md` → "Documentation
authoring conventions"). Both HIGH findings were then re-verified by hand against the
running code. Eight of seventeen auditor flags did not survive verification and are listed
below so they are not re-raised.

---

## Headline

**This is not a Diátaxis-structure problem.** Quadrant discipline is close to exemplary:
150 of 167 pages passed clean, the how-to quadrant produced zero confirmed defects, and
exactly one page anywhere drifts across a quadrant boundary. Indexing, `nav_order`, and
links are effectively perfect — a full crawl of every relative link and in-page anchor
across the published tree resolved with zero failures, every content page is listed in its
section README, and exactly one glossary exists.

The real weaknesses are **reference accuracy** (two rosters that claim completeness and are
not complete), **a trust label that lies about what CI enforces** (the root cause of both
roster drifts), **three shipped capabilities documented in reference only**, and **a
one-directional link topology** in which the most-trafficked reference pages point nowhere
back out.

| Quadrant | Pages | Clean | Confirmed defects | Refuted flags |
|---|---|---|---|---|
| Tutorials | 8 | 6 | 4 (1 med, 3 low) | 0 |
| How-to | 42 | 41 | 2 (1 med, 1 low) | 1 |
| Reference | 55 | 47 | 9 (2 high, 4 med, 3 low) | 2 |
| Explanation | 62 | 56 | 3 (3 low) | 5 |
| **Total** | **167** | **150** | **18** | **8** |

---

## Findings by severity

### HIGH — reference pages that claim completeness and are not complete

**1. `docs/reference/commands-and-transports/cli.md` — roster omits five real commands.**
Line 89 makes a closed claim: "This roster mirrors the live argparse tree." Walking
`_build_parser()` in `src/memoria_vault/cli.py` yields five leaves that appear nowhere in
the file: `memoria onboard`, `memoria context`, `memoria cockpit`, `memoria seed install`,
`memoria journal revert-preview`. All five are ordinary non-hidden registrations, and all
five respond to `--help` today. *Verified by hand: zero mentions in `cli.md`; all five
exist in the live parser.*

**2. `docs/reference/data-model/wikilink-and-link-conventions.md` — relation table
contradicts the code and its own cited authority.** Line 33 states "The only frontmatter
link relations are:" and lists three (`supports`, `contradicts`, `extends`). The code
defines six frontmatter-legal relations —
`LINK_RELATIONS = EDGE_RELATIONS - {"tension"}` over
`{supports, contradicts, extends, tension, warrant, qualifier, rebuttal}` in
`runtime/vocabulary/edges.py` — and `frontmatter.md`, which this section names as the
authority, says "the six frontmatter-legal relations" at line 162. Under the repo's trust
order (schema → tests → code → docs) the page is simply wrong, and a reader authoring a
`warrant` or `rebuttal` edge would believe it illegal. *Verified by hand against
`edges.py` and both docs.*

### MEDIUM

**3. `docs/reference/README.md` — the "Source" column mislabels which pages are
machine-checked, and is the root cause of findings 1 and 2's class.** `cli.md` and
`system-actions.md` are labeled "Guarded mirror", but `scripts/checks/doc_claims_gate.py`
validates **docs → code only** ("fail when docs cite a CLI path or operation id that
doesn't exist") — nothing checks code → docs, which is exactly the direction both rosters
drifted. `system-actions.md` contradicts its own label in its second paragraph ("keep the
operation manifest roster in sync by hand"). The error runs the other way too:
`control-plane.md` is labeled "Manual" but is the one page with a dedicated drift gate
(`control_plane_actor_gate.py`). A label that says "guarded" about an unguarded page is
worse than no label — it tells the maintainer the gate will catch drift, and it did not.

**4. `docs/tutorials/02-first-source.md` — step 5 breaks the offline path the chapter
promises.** The page opens "If you are offline, one local file gives you the same capture
path", step 2 is an explicit offline branch, and line 47 merges the branches ("Either way
— seed corpus or local file —"). Step 5 then runs
`memoria work add --url https://github.com/AkariAsai/OpenScholar` as an unconditioned
numbered step requiring live network, with no skip note. Every *other* post-merge step is
carefully guarded for the offline reader, which marks this as an oversight rather than a
choice; the design record states the acceptance bar as "Chapter 02 completes offline via
its local-file/-PDF alternative path."

**5. `docs/reference/commands-and-transports/system-actions.md` — operation roster is
wrong on 2 of 60.** The package ships 60 operation manifests; the stated roster parses to
58, missing `apply-decision-rule-notices` and `seed-install`. `seed-install` is described
nowhere in the catalog cluster despite being a real PI-only worker operation.

**6. `docs/reference/commands-and-transports/read-api.md` — eight of 29 public
`engine/api.py` functions are undocumented.** Missing: `read_attention_view`,
`read_evidence_review_view`, `read_dashboard_view`, `read_dashboard`, `read_canvas_forks`,
`read_revert_preview`, `read_context`, `read_cockpit`. Four of those eight appear in **no
published page at all**. The page closes by telling adapters to call this API instead of
opening SQLite directly, so silent partiality has teeth. (Unlike `cli.md` this page makes
no completeness claim — hence medium, not high.)

**7. `docs/reference/data-model/glossary.md` — `certainty` is defined in only one of its
two live senses.** The glossary defines the attention-projection sense
(`confident`/`likely`/`unsure`). A second, differently-valued `certainty` enum ships on
note frontmatter (`reported`/`contested`/`unknown`/`hypothesized`, per
`workspace_seed/.memoria/schemas/types/note.yaml`). The glossary's own stated method is
"one definition per term; disambiguation noted where a term has multiple senses", and
AGENTS.md makes it the only place definitions live — so the frontmatter sense is currently
undiscoverable from the canonical term home.

**8. `docs/reference/system/failure-modes.md` — the table is not sorted the way the page
twice says it is.** Both line 10 and line 34 promise severity ordering; the actual column
reads CRITICAL, CRITICAL, HIGH×3, **LOW**, MEDIUM×7, **HIGH**, MEDIUM, **HIGH**, LOW, LOW.
Two HIGH rows (backup target absent after interruption; restore reports rollback also
failed) sit buried below the MEDIUM block — the failure direction that costs an incident
reader the most.

**9. `docs/how-to-guides/library/run-a-systematic-review.md` (and
`library/capture-and-ingest.md` at its source) — the batch guide sends readers down the
one-at-a-time path.** Step 3 defers to the capture guide's per-Work
`memoria work enrich <work-id>`, but `memoria work import --enrich` queues enrichment for
every newly admitted item with a DOI (`cli.py:329`, `cli.py:1668`) and the reference tier
already documents it. The guide that exists *specifically for the batch case* never
mentions the batch flag.

### LOW (9)

Tutorial 01 lists macOS as a supported platform in a venv-activation parenthetical, though
Quickstart, `set-up-the-vault`, and the roadmap all state "macOS is not supported" (a
one-word deletion). Tutorial 01's recap asserts "the workspace is local and git-backed"
though no step showed it. Tutorial 07 credits the tutorial project to Chapter 04; it is
framed in Chapter 01. `reference/README.md` omits `evidence-review.md` from its table (the
only such omission in 45 pages) and describes the glossary as "alphabetical" when it is
organized thematically. `explanation/knowledge/common-pitfalls.md` answers its recurring
"What prevents it" slot in the imperative five times out of seven — the only genuine
quadrant drift in the audit. Two `Related` rows on `co-pi.md` promise different pages and
resolve to the same URL. One unlinked design-history milestone reference in
`distribution-model.md`.

---

## Mixed content (requires splitting)

One page, and it is a section-level drift rather than a structural mix:

- **`docs/explanation/knowledge/common-pitfalls.md`** — the "**What prevents it:**" slot
  drifts from explanation into instruction in five of seven pitfalls ("pin citekey…").
  Recommendation: rewrite those five in the discussing voice, or link out to the how-to
  that gives the directive.

No page requires splitting into separate documents. This is the finding a Diátaxis audit
usually exists to produce, and the tree essentially does not have it.

---

## Missing quadrants (coverage gaps)

The core loop is fully covered in every quadrant that needs it: installation, ingest,
search, bundles and claims, projects and drafting, vocabulary, backup/recovery,
control-plane policy, telemetry, and the Obsidian and Zotero adapters. Three shipped
capabilities are **reference-only**:

| Capability | Has | Missing | Why it matters |
|---|---|---|---|
| Evidence-set review queue (`memoria review`, 7 subcommands) | reference ×3, tutorial covers the *other* front (`project resolve-evidence`) | how-to, explanation | A PI-only family that gates whether a draft can export. Not fully blocking — Tutorial 05 and `compose-a-draft` teach the per-finding path — but the batch cockpit is undiscoverable from any index a working user consults, and its reference page is the one page missing from `reference/README.md`. |
| MCP transport | reference ×2 | how-to, explanation, tutorial | Setup ships focused guides for *every other* optional adapter — Obsidian, Zotero, gateway runner, second vault — and none for MCP, though AGENTS.md names MCP hosts as supported. "Point my agent host at this vault and understand what it may write" has no entry point. |
| Prompt operations (`memoria operation run`, 9 shipped patterns) | reference ×2 | how-to, explanation | `prompt-operations.md` has zero non-index inbound links. Worse, `how-to-guides/knowledge/README.md` and the Knowledge row of the how-to index both **advertise "pattern-running" and "refactoring"** — neither is delivered by any of that section's five guides. The index promises what the section does not contain. |

Two low-severity gaps: the troubleshooting escalation path terminates with no "capture a
diagnostics bundle" step, and the Engineer posture has explanation but no practice
anywhere (one inbound link, no outbound).

---

## Cross-linking opportunities

A systematic one-directional topology: how-to and explanation point **down** into
reference, and the most-trafficked reference pages carry **zero** cross-quadrant links back
out. Highest value first:

| From | To | Why |
|---|---|---|
| `reference/data-model/frontmatter.md` (23 inbound, 0 out) | `explanation/knowledge/document-types.md`, `troubleshooting/fix-broken-frontmatter.md` | Second most-linked page in the docs; readers arrive from a validation failure with no route to the fix. |
| `explanation/execution/operation-postures/*` (all five) | the how-to that enacts each posture | The conceptual heart of the product links only to itself. |
| `reference/data-model/document-types.md` (17 in, 0 out) | `explanation/knowledge/document-types.md` | A same-named explanation page with the epistemic reasoning already exists one directory over. |
| `reference/control-and-policy/control-plane.md` (15 in, 0 out) | `inbox/work-the-action-queue.md`, `troubleshooting/fix-stuck-card.md`, `explanation/execution/control-plane/states.md` | Explanation links down here twice; nothing returns. |
| `reference/analysis-and-surfaces/linter.md` (13 in, 0 out) | `operate/run-the-linter.md` | Reader looks up a detector, has no link to the guide that runs it. |
| `reference/pipelines-and-io/ingest.md` (10 in, 0 out) | `library/capture-and-ingest.md` | Highest-traffic pipeline reference; the how-to already links here. |
| `explanation/architecture/vault.md` (9 in, 0 out) | any how-to | Entry explanation for the write path with no "now do it". |
| `tutorials/07-customize.md` | `inbox/return-to-work.md`, `inbox/run-the-weekly-review.md` | The arc's final page exits to a generic index link; 01–06 all hand off specifically. |
| `library/capture-and-ingest.md` | `explanation/knowledge/knowledge-cycle.md` | Most-referenced Library guide (7 inbound) has the leanest link set of any how-to — two links, both to reference. |

---

## Recommendations (priority order)

1. **Fix the two HIGH reference defects** — add the five missing commands to `cli.md`;
   correct the relation table to the six frontmatter-legal relations (carrying over
   `frontmatter.md`'s caveat that `tension` is machine-surfaced and never authored).
2. **Fix the "Source" column in `reference/README.md`, or delete it.** Correct `cli.md`
   and `system-actions.md` to "Manual" until a completeness gate exists, and
   `control-plane.md` to "Guarded mirror". Define the three labels in one line. This is
   the highest-leverage item: it is why 1, 5, and 6 drifted unnoticed.
3. **Decide on a code → docs completeness gate.** `doc_claims_gate.py` runs one direction
   only. Either extend it (assert the argparse leaf set and the operation-manifest id set
   are fully rostered — both are mechanically enumerable, as this audit did) or drop the
   "mirrors the live argparse tree" claim. Per AGENTS.md's *deletion > mechanism > rule >
   checker*, dropping the claim is the cheaper honest option; extending the gate is
   justified only because two independent rosters drifted the same way.
4. **Fix Tutorial 02's offline break** — one clause on step 5 restores the chapter's
   stated acceptance bar.
5. **Close the index-overpromise** in `how-to-guides/knowledge/README.md`: either write the
   pattern-running and refactoring guides or stop advertising them.
6. **Add the reciprocal links** for the six highest-traffic reference pages above; this is
   mechanical and buys the most navigational value per edit.
7. **Then the remaining mediums** (read-api roster, `system-actions` roster, glossary
   `certainty` disambiguation, `failure-modes` sort order, systematic-review `--enrich`).
8. **Consider a how-to for the review queue and one for MCP setup** — the two coverage gaps
   where a real reader task has no entry point. Prompt operations may be a
   stop-advertising decision instead.

---

## Flags that did NOT survive verification

Recorded so they are not re-raised. Four of these were `nav_order`-versus-README-table
ordering complaints in `explanation/rationale/*` — the skeptic found the frontmatter facts
correct but the claimed reading-order dependency unsupported in three of four cases. Also
refuted: `run-a-systematic-review.md`'s filename-versus-title mismatch (the title is
accurate about scope); `system-actions-scheduled.md` "points the reader nowhere" (lines
11–12 do cross-reference the guarded operation list); `failure-modes.md` line 48's Fix cell
as a quadrant mix (the Fix column is directive **by design**, stated at line 10, and every
row is imperative); and `engineer.md` as "reference dropped into explanation" (thin, but
the charge overstated — recorded as a LOW coverage note instead).
