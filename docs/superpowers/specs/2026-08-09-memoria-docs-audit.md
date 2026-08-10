# Consistency Audit Record — Memoria, 2026-08-09

> **Status:** findings reported, none applied. The 27 applicable repairs are planned in
> [`plans/2026-08-09-audit-repairs.md`](../plans/2026-08-09-audit-repairs.md); the 12
> `owner-call` findings and 2 gate specs await a decision pass. This file is the frozen
> record — kept for the coverage line, the verdict split, and above all the refuted list,
> so a future audit does not re-litigate what this one already killed.

**HEAD:** `217fc35835bcc37ce872be09e777afb1e02a5dac`, clean tree.

**Method:** six concern slices, two independent readers each (`repo-consistency-reader`,
read-only), deduplicated, then every surviving candidate sent to an independent skeptic
instructed to refute it and to default to `refuted` where evidence did not clearly hold.
113 agents. Pairing was deliberate: a single-pass check measured on this corpus recovered
roughly one real defect in three, which is why the 2026-08-03 audit used nine readers plus
skeptics and why one reader alone is not enough.

---

## Headline

**101 candidates → 81 confirmed verdicts → 41 distinct defects; 20 refuted.**

The corpus is structurally sound and factually behind the code. Nothing found is a
Diátaxis problem — quadrant discipline held everywhere, consistent with the 2026-08-03
finding that it is "close to exemplary." What the audit found instead is **drift between
what the code does and what the docs say it does**, concentrated in two places: guides
whose commands cannot run as written, and reference rosters that fell behind a rename or
a shipped surface.

The single highest finding is not a docs defect at all: a documented HIGH-severity
detector reads frontmatter fields **no type schema declares**, so it cannot fire.

| Verdict | Count |
|---|---|
| `direct-fix` | 26 |
| `owner-call` | 12 |
| `graduate` | 2 |
| `record` | 1 |

---

## Confirmed findings

### HIGH

**`fama-exposure` and `fama_clean` key on undeclared frontmatter** — `linter.md:37`,
`vault-eval.md:94`, `detectors.py:346-348`, `eval_score.py:92-94` against
`types/note.yaml:36`. The detectors test `status:` / `superseded_by`; the schema declares
`superseded: bool`, and closed validation rejects the fields they read. `owner-call`: the
design record points both ways — the alpha23 plan rules a bool flag, `design-principles.md:59`
promises a successor pointer a bool cannot carry.

### MEDIUM — 15

Guides that cannot work as written (all `direct-fix` unless noted):

- `set-up-obsidian.md` — instructs entering a server URL and token the packaged plugin has
  no field for; it obtains port and per-boot token itself via `memoria handshake --spawn`.
- `run-the-linter.md:16` — names `memoria workspace check` as the unattended Linter surface;
  that command runs the integrity sweep and never reaches the Linter.
- `safe-mode.md` — the export fallback is circular: routes a missing-Pandoc failure back to
  Pandoc, and teaches the one format that requires it.
- `inspect-session-logs.md:63` — invokes the summary generator by repo source path,
  unreachable from a deployed vault.
- `run-a-retraction-sweep.md:26,34` — runs a vault-local package under the system `python3`.
- `export-a-draft.md` — `memoria project export` runs bare `pandoc`, so the CSL prerequisite
  and the "citations resolved" check do not hold. `owner-call`.
- `tutorials/03-connect-notes.md` — attaches a JITAI claim to whichever seed Work the reader
  picked and calls it the source. `owner-call`; cascades through 04, 05, 07.

Reference and seed drift:

- `on-disk-layout.md` — `concept-types.yaml` (hard-required) and `system/templates/session-diary.md`
  (seeded by `cli.py:65`) missing from both the tree and the Packaged Seed Inventory. `graduate`.
- `telemetry.md:89-102` — `runs.jsonl` misattributes the writer and shows a schema no code
  emits; `lint-findings.jsonl` inventoried as standing output but written only under an
  undocumented `--jsonl-out`.
- `frontmatter.md:209`, `linter.md:68` — call `system/` and vault-root pages "untyped"; the
  seed ships them all with `type: system`.
- `integrations.md:104,106` — Obsidian adapter rows frozen at the pre-pane plugin state.
- `workspace_seed/system/vocabulary.md:28-29` — routes provider taxonomies to a `_enrichment`
  frontmatter namespace that exists nowhere and closed validation rejects.
- `vault.md:105-109` — says Concept archive state is "runtime state"; six schemas, the
  frontmatter reference, and every code reader say frontmatter `archived: bool`.
- `design-principles.md:91-93` — "Planned (beta.1)" banner on a principle the citing page
  states as shipped.
- `glossary.md` — four live names for the attention artifact (projection, card, prompt,
  item); the glossary rules on two while its own body uses the others. `owner-call`.

Policy:

- `AGENTS.md:74-77` — "not a stored readiness verdict" contradicts "Readiness is authored"
  fifteen lines later; pre-state-machine residue.
- `cross-tool-parity.md` — names Kilo as one of three tools and gives it no entry.
  `owner-call`; its config is gitignored, so the facts are the owner's.
- `consistency-audit-brief.md:63-66` — excludes all `design-history/` as "frozen by design",
  but `design-history/README.md` declares `arcs.md` maintained. `owner-call`.

### LOW — 15

`verify-check-citation` cited as a live Peer-reviewer surface but exists nowhere in the
repository · `empirical-events.md:92` names `resolve-evidence-review`; the shipped id is
`resolve-evidence` · `fulltext.yaml:2` declares `category: fulltext`, orphaned by the
alpha.19 rename to `fulltexts` · `policy-audit-log.md:25` says "the eight actions above" on
a page with no action list · `prompt-operations.md:71` enumerates a two-value `output_target`
its own roster contradicts · `read-api.md` omits three public `engine.api` functions
(`graduate`) · `reference/README.md:103` advertises a Zotero↔Obsidian comparison the target
no longer contains · two Knowledge pages both declare `nav_order: 2`, introduced at HEAD ·
`what-memoria-is.md:46` marks OKF conformance target-state after v0.2 shipped whole-tree
checking · `states.md:127` "Board-states lookup table" is kanban-era residue · three
explanation pages route Linter promises to a class page naming neither · `CHANGELOG.md:9`
calls the project "early pre-alpha" one line before "alpha source install" · `README.md:137,140`
names a `test-vault/vault` path both scripts contradict · upstream template residue in two
`docs/agents/` pages · **`record`**: "SRD" is load-bearing in a published how-to and
expanded nowhere.

Deferred by verdict: `_sources.yml` as an unread second ledger, the callout-palette anchors,
the nested-bundle triplication, the board-state duplication, `set-up-zotero.md`'s upstream
pins — all `owner-call`.

---

## Flags that did NOT survive verification

Recorded so they are not re-raised. Twenty candidates died at the skeptic step; the pattern
is instructive — nearly every one had **accurate quotes** and drew a false inference from
them.

**A page declaring its own intent (4).** `quickstart.md` duplicating `set-up-the-vault.md`'s
install body — quickstart.md:15-17 declares itself "Tutorial 00 — onboarding exception… stays
in Setup so new users can install a vault first." The `claims.base` "Open questions" view
filtering orphans rather than question state, raised twice — a published explanation page
specifies exactly the shipped semantics and disclaims what the candidate said was missing.
`README.md`'s Requirements restating CONTRIBUTING toolchain facts — the "no-second-copy rule"
it invoked does not say what the candidate claimed.

**Marker present, candidate said absent (3).** OKF export/import "stated in the present
indicative with no Planned marker", raised twice — the page's opening callout at :12-14 names
both items verbatim, and `okf-compliance.md:54-55` uses the identical present-tense-plus-marker
construction. "Surfaces frames every composed view as planned" — the quoted sentences are
scoped to named adapter views; `memoria cockpit` and `memoria dashboard` do ship (`cli.py:233,242`).

**Term is defined, elsewhere (3).** "Board" and "lane" undefined — `dashboards.md:27` carries
Board state as a shipped inventory row. "Triage" ambiguous between product and tracker senses
— the glossary declares its jurisdiction two lines below the promise, and the two senses never
share a surface. The Cockpit "absent from explanation" — `structural-health.md:35-37` says
"request **and** attention", not "the same state".

**Absence is the designed state (2).** `.out-of-scope/` mandated but missing, raised twice —
an empty lazily-written store looks exactly like this; `/triage` writes it at close.

**Shipped, contrary to the claim (2).** The retraction guide's Contradictions view is real —
`claims.base:35-43`. The alpha.20 pins in `folders.yaml:1` and `manifest.json:4` fail on three
independent checks.

**Partially accurate, over-claimed (6).** The installer-commit fact in three setup guides;
`steering.md`/`vocabulary.md` view-preference lifecycle; CONTRIBUTING's link rule versus
`_config.yml`'s exclude list (already owned by `doc_link_targets.py`); AGENTS.md's chapter
versus CONTRIBUTING's CHANGELOG as "two per-release records"; `policy-mcp.md`'s delete/move
framing versus the hook; `memoria onboard`'s Obsidian offer and Zotero probe versus
`installer.md`.

---

## Scope line

**Read:** 227 files, ~221k tokens — `docs/` (185, excluding `superpowers/`), the packaged
workspace seed (42), plus `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `CONTEXT.md`, and
`docs/agents/`.

**Excluded, with reasons:** `design-history/` — frozen by design, so a stale claim there is an
accurate record of what was true then (note: one confirmed finding disputes this exclusion for
`arcs.md`). `docs/superpowers/` — point-in-time working records; the 30 rotted code citations
living there are not defects. `test-vault/` — gitignored build artifact.

**Not re-audited, by brief:** territory owned by `doc_link_targets`, `doc_cited_paths`,
`schema_doc_drift`, `doc_claims_gate`, `checked_terminology_gate`, `mermaid-parse`, cspell,
vale, and markdownlint.

**Comparisons not made:** none at the slice level — every slice was read whole by two readers.
Cross-slice contradictions (a reference page against an explanation page in a different slice)
were caught only where a reader's slice happened to span both; a corpus this size does not fit
one reader's context, and that residual is the known limit of the concern-split approach.
