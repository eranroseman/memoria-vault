# Memoria — data structure: as-built map + clean-slate rethink

> **Two parts.** **Part 1** is the exhaustive *as-built* map (what the data
> structure is today). **Part 2** is a *first-principles rethink* — the design
> derived independently from requirements, then measured against Part 1. Read Part 1
> for "what is," Part 2 for "what it should be and where it diverges."

---

# Part 1 — The as-built map (alpha.16)

## Context

This is an **analysis deliverable**, not a code change: a single map of where every
piece of Memoria's data lives and how the layers derive from one another. It answers:
what is in the database, what is in files inside the OKF knowledge bundle, what is in
files *outside* any bundle, and the frontmatter + file-content schemas for each.

Basis: the runtime code under `src/memoria_vault/` (authoritative) and the shipped
`vault-template/` (a fresh/empty vault with `.gitkeep` placeholders). The template is
the right basis for a *structure/schema* analysis of a new vault. Every claim below is
grounded in code/config first, docs second (code wins on any conflict). Reference
docs already cover parts of this (`docs/reference/vault-data-model.md`,
`on-disk-layout.md`, `frontmatter.md`, `memory-substrates.md`, `system-artifacts.md`);
this consolidates and cross-checks them against the implementation.

---

## 1. The one idea: source-of-truth / derivation spine

**Corrected framing** (this got the direction backwards in the first pass): Memoria's
*entire* interoperability/survivability requirement is satisfied by exactly two things —
**the knowledge bundle** (markdown Concepts: notes/hubs/projects and whatever `source-note`
folds into) **and `bibliography.bib`.** Nothing else needs to be portable. And the
general rule underneath that: **structured data is never represented as files — it
belongs in the database, full stop.** Files are for two things only: human-authored
prose knowledge (needs to be hand-edited, so it must be markdown) and the one portable
citation interchange format that already exists for exactly this purpose (BibTeX). Any
other "let's also keep this in a file for safety" instinct — the earlier survival-copy
fields, `csl_json`/`identifiers` duplicated onto `work.yaml` — is exactly the anti-pattern
this rules out, not a set of isolated one-off fixes (G0 below is now read as instances of
this one rule, not a separate judgment call).

```
AUTHORITATIVE KNOWLEDGE                MEMORIA-INTERNAL MACHINERY               THE PORTABLE EXPORT
(git-tracked markdown)                 (.memoria/memoria.sqlite, blobs —        (git-tracked, at vault root)
                                        zero portability requirement)
─────────────────────────────         ────────────────────────────────        ─────────────────────────
OKF bundle Concepts              ──►   concepts (store='file' MIRROR)          index.md
  notes/ hubs/ projects/                 concept_verdicts (check_status)       bibliography.bib  ◄── THE
  (frontmatter + body,                   evidence_sets (%%ev%% markers)            portable knowledge
  hand-authored)                         search index, queue, journal,             representation of
                                          provider payloads, graph edges,           every catalog fact
                                          provenance — ALL of it disposable,
                                          rebuildable, Memoria-only

catalog_sources SPLITS DOWN THE MIDDLE OF ONE TABLE:
  knowledge columns (title, authors, issued, doi/identifiers, csl_json)   → belong in bibliography.bib,
                                                                             not withheld as DB-only
  operational columns (content_hash, raw_hash, content_path, raw_path,    → correctly DB-only, no
  provider_coverage, text_status, check_status)                            portability need at all
```

Rules that fall out of this and explain most of the design:

1. **Markdown = the knowledge; SQLite = internal state, not a second knowledge store.**
   A Concept's *meaning* (frontmatter + body) lives in the bundle markdown. Everything
   else — verdict, queue state, materialization lifecycle, derived indexes, the catalog's
   *operational* columns — is Memoria's own bookkeeping, with no portability claim on it
   at all. It isn't "authoritative and not markdown" in the sense of being a second
   knowledge repository; it's infrastructure.
2. **`check_status` is NOT frontmatter.** It lives only in `.memoria/memoria.sqlite`,
   worker requests, and read-API responses. Writers *reject* a set of retired
   frontmatter verdict fields (`check_status`, `verdict`, `lifecycle`, …) so a forged
   file field can't grant a "checked" verdict. (`runtime/vaultio.py`
   `RETIRED_FRONTMATTER_FIELDS`; `docs/reference/frontmatter.md`.)
3. **`bibliography.bib` is the knowledge; `catalog_sources` is a queryable cache of it,
   not the other way around.** The direction matters: the bibliographic-fact columns of
   `catalog_sources` should be understood as re-derivable **from** `bibliography.bib`
   (plus re-fetching enrichment on demand), not as an irreplaceable original that
   `bibliography.bib` merely echoes a lossy copy of. **Precise, narrow scope for what
   that requires** (not "capture every field" — specifically three things: enough to
   *produce a citation*, the `citekey`, and the `work_id` pointer):
   - **Citation-production fields** — verified against the actual renderer
     (`capture.py:1100-1119`, `_render_source_bibtex`): it emits `title`/`author`/`year`/
     `journal`/`doi`/`url`/`abstract`, close to sufficient for a basic citation already;
     worth checking for gaps in standard fields a full citation sometimes needs
     (volume/issue/pages/publisher), but this is a minor completeness check, not a
     redesign.
   - **`citekey`** — already rendered as the BibTeX entry key. Fine as-is.
   - **`memoria_work_id`** — **the actual gap, and the load-bearing one.** Confirmed: no
     `work_id`/`source_id` field is emitted anywhere in the entry today. Without it, a
     note's `work_id` pointer has no reliable way to resolve to its bib entry —
     matching by `citekey` alone isn't safe, since `catalog_sources.citekey` defaults to
     empty (`schema.sql` `DEFAULT ''`) and may never be populated for a given source.
     *Fix:* add `memoria_work_id` as a field on every rendered entry (a plain custom
     BibTeX field, e.g. `memoria_work_id = {...}` — namespaced so any generic BibTeX
     consumer reads it unambiguously as a tool-specific extension to ignore, not a
     standard field to interpret, tolerated the same way `note`/`keywords` fields
     already are) so resolution never depends on citekey being present. This is the one
     addition that actually closes the loop
     between "notes point at `work_id`" and "bibliography.bib is where that resolves."
   Per the standing zero-migration-cost principle, ship this now — it's what G0's
   "one bibliography file" fix already needs in order to be true, not a separate task.

---

## 2. Layer A — the OKF knowledge bundle (files *inside* a bundle)

**OKF = Open Knowledge Format** (Google Cloud's interchange spec). A *Concept* is a
typed markdown document; a *Concept ID* is its path minus `.md`; a *Knowledge Bundle*
is a runtime-independent set of Concept files. Memoria is a **strict producer,
permissive consumer** — it emits schema-valid typed content but only tolerates OKF's
"consumers MUST NOT reject" permissiveness at the *ingest* boundary (the gate, not
OKF's rule, governs what reaches a canonical surface). OKF's prose-typed relationships
are the *inverse* of Memoria's typed edges, so OKF is a **boundary format, never the
core** (full import/export is ADR-107, still deferred). What ships in alpha.16 is the
OKF *bundle-root nouns* and *OKF-style projections*, not a full OKF pipeline.

**So: is Memoria's knowledge bundle actually OKF-compliant? No — and that's by a stupid
design mistake that we should learn not to repeat, not a gap.** "Boundary format, never
the core" means exactly this: Memoria's *internal*
bundle borrows OKF's **nouns** (Concept = typed markdown doc, Concept ID = path minus
`.md`, the bundle-root convention, an `index.md` manifest) but deliberately **violates
OKF's core rule** — OKF requires relationships to be **prose-typed** ("the specific kind
of relationship is conveyed by the surrounding prose, not by the link itself"); Memoria's
`links:` are **typed edges** (`supports`/`contradicts`/`extends` as structured frontmatter
keys), the polar opposite, adopted on purpose (ADR-126: typed edges over prose-typing).
The reserved OKF headings (`# Schema`/`# Examples`/`# Citations`) aren't implemented
either — confirmed absent from every shipped template. A generic OKF consumer opening
`works/`/`notes`/`hubs`/`projects` today would find well-formed typed markdown (the
Concept-as-file idea holds) but would not find the relationship semantics its own spec
promises.

The genuinely OKF-compliant artifact would be a **different, not-yet-built thing**: the
lossy *export* ADR-107 describes — a conversion pass where typed `links:` collapse down
to untyped prose-typed markdown links, `check_status`/lifecycle survive only as ignorable
custom frontmatter, and the result carries no gate/Linter/MCP, making it standalone-
consumable by any OKF tool. That conversion is **proposed and deferred**, not shipped —
so today there is no OKF-compliant artifact anywhere in the system, only an OKF-*inspired*
internal one plus a documented plan for producing a real one on export. Three distinct
things worth not conflating: (1) the internal bundle — OKF-inspired, not compliant, by
design; (2) the hypothetical export — would be genuinely OKF-compliant, unbuilt; (3) OKF
as an *ingest* boundary (accepting a foreign OKF bundle as an import source) — a third,
separate concern, gated through Memoria's normal strict validation before anything is
trusted, not a "be permissive like OKF says" posture applied to Memoria's own content.

### Can the bundle become a strict superset of OKF instead?

**Method note:** the answer above leaned on ADR-126 ("Memoria deliberately rejected
prose-typed relationships") as if that settled the question. Per this project's own
stated policy, an ADR is evidence of a past decision, never a standing justification —
so this is re-derived fresh, checked against the actual code (templates, the writer that
names files), not re-argued from the ADR. Result: **mostly yes, and mostly by addition —
with one piece that is a genuine fork, not a free add.**

**Additive — no conflict, just build it:**
- **Relationship typing.** OKF requires the relationship kind to be conveyed by
  surrounding prose. Checked: the `## Links` body section is **not** template-generated
  or schema-enforced (`system/templates/note.md`/`hub.md` are minimal `# {{title}}` +
  free-body placeholders) — it's already pure freeform prose, independent of the
  structured frontmatter `links:` map. Nothing stops that prose from *also* narrating
  each relationship in OKF's style ("this finding supports [[X]] because...") while the
  frontmatter `links:` map stays exactly as strict as it is today for Memoria's own
  validation/gap-analysis. The two aren't exclusive — one file can carry both a
  human-readable prose-typed narrative (satisfying OKF) and a machine-checked typed-edge
  index (satisfying Memoria) with no format conflict. This is a **writing-convention and
  lint addition**, not a schema change: require the Links section prose to name each
  frontmatter link's relation for every target, checkable the same way the linter
  already checks structural link targets.
- **Reserved headings** (`# Schema`/`# Examples`/`# Citations`) — currently absent from
  every shipped template; adding them is pure addition, no existing behavior to disturb.
- **A real progressive-disclosure `index.md`** — today a static 5-line manifest (§ above,
  already flagged as doc/code drift); replacing it with one that actually enumerates the
  checked corpus is real implementation work, but nothing in it conflicts with Memoria's
  own model — it's a generated projection either way.
- **Self-correction:** OKF's "permissive consumption" rule governs how an OKF-*reading*
  tool must behave toward malformed input — it is not a constraint on the *shape* of
  files a producer emits. Memoria staying a strict producer (schema validation,
  quarantine) was wrongly treated above as something in tension with "being OKF" — it
  isn't. Producer discipline and bundle-shape compliance are orthogonal; strictness on
  the way in doesn't stop the file on disk from satisfying OKF's structural contract.

**Mostly additive after all — corrected.** OKF's identity model assumes **the path is
the identity** (rename the file, the Concept ID changes). Memoria's ULID `id:` was
introduced to give the *opposite* guarantee — "identity ≠ filename ≠ title," so
retitling or moving a file never breaks an existing reference (confirmed:
`knowledge.py:3233-3234` derives the actual filename from a **title-slug**, never the
ULID). The first pass here treated freezing filenames to `<id>.md` as costing "human
legible filenames" — that overstated the cost. **Verified core Obsidian mechanism:
`Settings → Appearance → Show inline title`, toggled off.** With it off, Obsidian
doesn't render the filename as a heading at all; the note's own `# ` heading in the
body — which Memoria's templates already write (`# {{VALUE:title}}`) — is what the PI
sees, in both edit and reading view. So renaming files to `<id>.md` costs **nothing** on
the single most important surface: the PI reading and editing the note itself. That's a
zero-dependency, single-settings-toggle fix, not a plugin or a workaround.

What that setting does **not** cover (unverified whether any core mechanism reaches
these — the long-standing 2020 Obsidian feature request "use H1 or YAML title as display
name... everywhere: links, backlinks, graph view, search" is still open, which implies it
doesn't): the file-explorer sidebar list, tab-bar titles, graph-view node labels, and
quick-switcher/search results would likely still surface the raw `<id>.md` filename.
That's a real but much narrower and lower-stakes gap than "the PI has to work with ugly
filenames" — it affects *finding* a note by browsing, not *reading or writing* one. If it
matters, the community plugin **Front Matter Title** (not core) closes it by rendering a
frontmatter-sourced title across those remaining surfaces without renaming the file; a
different plugin, *File Title Updater* (2025), does the opposite — it *syncs*
filename/frontmatter/heading together rather than decoupling them, so it wouldn't help
here specifically.

**Net, revised:** freezing filenames to `<id>.md` is achievable **now, for free**, for
the PI's actual day-to-day reading/writing workflow (one core settings toggle + the
existing template convention). The only remaining, genuinely optional cost is
file-explorer/graph-view/quick-switcher browsability by name, closeable with one
well-established community plugin if wanted. That's a much smaller ask than the original
"pick one" framing implied — full OKF identity compliance in the *live* vault, not just
the export, is realistically in reach.

### Every `projects/<slug>/` subfolder is itself an OKF bundle — previously unaddressed

Design-history already called a project "a nested, **detachable sub-bundle** with
**one-way project→corpus references**" (alpha.15, ADR-126/77/79 lineage) — this analysis
initially worked out the wrong half of that phrase's implications. Correction:

**"Detachable" means safely *erasable in place* — not "extractable and self-contained."**
The one-way link direction is the load-bearing fact, and it's a *structural* guarantee,
stronger than any spec tolerance: `notes/`/`hubs/`/`digests/` never link **into** a
project (only `project.md`'s own `links:` point *out*, project→corpus). So deleting a
`projects/<slug>/` folder can **never** leave a dangling reference anywhere else in the
vault — not because broken links are tolerated somewhere, but because nothing outside
the project ever pointed into it in the first place. The rest of the corpus is immune to
a project's deletion by construction, full stop.

**A separate, genuinely different question — copying a project *out* to share
standalone — is where the spec-tolerance point actually applies**, and it's still worth
keeping: `project.md`'s own outbound links (project→corpus) *would* be dangling in a
copy detached from the rest of the vault. Per §5.3, that's still not malformed —
"Consumers MUST tolerate broken links... it may simply represent not-yet-written
knowledge" — so a project *can* also be shared standalone without being spec-broken.
But that's a secondary, opt-in use case, not what "detachable" was describing.

- **Nested bundles are explicitly contemplated either way.** §3: "A bundle is a
  directory tree of markdown files. The directory structure is independent of the
  domain." The reserved `index.md`/`log.md` conventions (§6/§7) "MAY appear in any
  directory, including the bundle root" — so a `projects/<slug>/` folder *could* carry
  its own local `index.md` if the standalone-sharing case is ever wanted.
- **What's a genuine (optional) enhancement, not a requirement:** that per-project local
  `index.md` — worth adding for quality if standalone project-sharing matters, not
  required for the erasure-safety property, which needs nothing beyond the one-way link
  discipline already in place.
- **What's a genuine (separate) product choice, not a compliance question:** whether
  "share a project standalone" should ever *also* pull in the concepts it references (so
  a recipient gets supporting context, not just dangling pointers) — a usefulness
  decision, independent of OKF, compliant either way per the tolerance rule.

**`<slug>` vs `<project_id>` for the folder itself — resolved: `<slug>`.** Unlike
notes/digests, this didn't inherit a free fix, so the choice was made deliberately
rather than by default:
The free fix that resolved notes' identity fork (`Show inline title` off + the
template's own heading) covers reading/editing *inside Obsidian* — but project folders
are plausibly handled *outside* Obsidian far more than individual notes (attaching a
draft, terminal work, sharing the folder with a collaborator, opening `draft.md`
elsewhere), where that setting provides zero help. So this doesn't inherit the
"basically free" verdict notes got:
- **`<project_id>` (ULID):** full path=identity consistency, rename-safe as scope
  evolves over a project's (often long) lifetime — but a real, uncompensated legibility
  cost on every surface outside Obsidian's editor pane.
- **`<slug>`:** legible everywhere, including outside Obsidian entirely — at the cost of
  a one-axis, deliberate non-compliance (`project.md`'s `id:` ≠ its path-derived OKF
  identity) and no rename-safety unless the folder is simply never renamed post-creation.
- **Independent of either choice:** the erasure-safety property above depends only on
  the one-way link direction, not on how the folder is named — so `<slug>` doesn't put
  that guarantee at risk. **Decision: `<slug>`**, accepting the localized
  non-compliance, since the property that actually matters here doesn't require the ID
  match — but this is a real trade-off, not a settled call.

### The export mechanism, once this is a real superset: copy-paste, not a conversion pipeline

If the additive fixes above actually ship (prose-narrated Links, reserved headings, a
real progressive `index.md`, `<id>.md` filenames), the live bundle stops being merely
OKF-*inspired* and becomes genuinely OKF-*compliant* — at which point "export" needs no
transformation step at all. **A file-explorer copy-paste of the relevant folders *is*
the export.** This **replaces, not complements**, the ADR-107 lossy-conversion pipeline
described earlier (typed links collapsing to prose, `check_status` surviving only as
ignorable frontmatter) — that pipeline was designed to bridge a non-compliant bundle to
a compliant one. If the bundle is compliant already, there's nothing left to convert;
building the lossy converter would now be solving a problem that no longer exists.
Recommendation: don't build ADR-107's converter — invest in the additive fixes instead,
since they make the converter unnecessary rather than merely delayed.

That reframing surfaces real issues a literal copy-paste would hit, each resolved below
rather than left open:

1. **The export unit is bigger than the 5 bundle-root folders.** `bibliography.bib` and
   `index.md` sit at vault root, *siblings* to the bundle roots, not inside them — a copy
   of only `works/`/`notes/`/`hubs/`/`projects/` would leave every `work_id`/`source_id`
   pointer (per G0, the *only* place catalog data lives now that the survival-copy fields
   are gone) dangling, since the citations they resolve through live in
   `bibliography.bib`, not in any bundle-root file. **Resolved by definition, not new
   code:** the export unit is *the vault root minus `.memoria/`* — bundle roots +
   `bibliography.bib` + `index.md` (+ optionally `system/`, `inbox/` if wanted, neither
   load-bearing). In practice a PI copying "my vault" via file-explorer naturally selects
   everything at vault root together — this just needs to be *stated* as the defined
   export unit so an automated/scripted copy doesn't narrow it incorrectly.
   **One more exclusion, found while explaining `.memoria/` directly: `journal/` also
   needs excluding, and it's easy to miss because it isn't under `.memoria/` at all.**
   `vault / "journal"` (confirmed in `trusted_writer.py`/`operations.py`/`integrity.py`)
   is a **vault-root sibling** to `.memoria/`, `notes/`, etc. — not nested inside it —
   holding per-event `.jsonl` files, and `vault-template/.gitignore`'s bare `journal/`
   pattern (no `.memoria/` prefix) confirms it's gitignored, ephemeral, regenerable
   runtime state, same bucket as `.memoria/`'s disposable contents. "Vault root minus
   `.memoria/`" as stated doesn't exclude it — should read "vault root minus
   `.memoria/` and `journal/`."
2. **`.memoria/` must be explicitly excluded.** It holds the working SQLite DB, the local
   `.venv`, secrets-adjacent config, and disposable staging/quarantine state — none of it
   belongs in a knowledge export, and copying it wholesale risks leaking more than
   intended (unchecked/quarantined content, local provider config). Resolved by making
   the exclusion explicit in whatever documents the export unit (point 1) — this is
   already how `vault-template/.gitignore` treats these paths for git purposes; the same
   boundary applies to a manual copy.
3. **Evidence markers reference page-spans in a file that, today, doesn't reliably
   exist.** `%%ev%%` markers cite `work_id#^pNNNN` — a specific span inside the source's
   extracted text. Earlier in this analysis, `works/<work_id>/fulltext.md` turned out to
   be **described in docs but never actually written** by any current code path (the real
   text lives in the gitignored `.memoria/blobs/` instead). A copy-paste export today
   would carry evidence markers with **no resolvable target** — every citation would be
   a dangling span reference. **This doesn't cut against materializing `fulltext.md` as a
   real bundle file — it's the strongest reason yet to actually build it**, not treat its
   absence as acceptable: the raw/original blob (PDF, HTML) still doesn't need to travel
   (it's provenance, not knowledge), but the extracted, block-ref-anchored plain text
   does, precisely so a copied bundle is self-contained and its citations verifiable
   without Memoria's own database in the loop.
4. **`check_status`/verdicts don't travel — by design, and that's fine, not a gap.**
   Meaning-only frontmatter means no exported file carries "checked" or "quarantined."
   OKF has no notion of this anyway (a permissive OKF consumer wouldn't know what to do
   with it), so its absence isn't a compliance shortfall. The one real question —
   *"if this copy is ever re-imported into Memoria later, could a stale or forged verdict
   sneak back in?"* — is **already resolved by existing behavior, not a new fix**: ingest
   always runs through Memoria's normal strict gate regardless of what a foreign bundle
   claims about itself ("the gate, not OKF's permissive-consumer rule, governs what
   reaches a canonical surface" — established earlier in this section). A re-imported
   note always starts `unchecked`.
5. **Prose-typed narration needs an actual enforcement mechanism, not just a
   convention.** `## Links` being freeform prose makes OKF-style narration *possible* per
   file, but nothing currently guarantees a given note's Links section actually names
   the relationship for every frontmatter `links:` target — a note could have
   `links: {supports: [...]}` and a Links section that never says so in words. Without
   enforcement, "the bundle is a superset" is only true *on average*, not per file, and a
   copy-paste export would silently carry through whichever notes fail the convention.
   **Resolved by adding a linter check** (alongside the existing structural
   link-target-validity check): every frontmatter `links:` target must be referenced in
   the Links section prose in language that names its relation — flag it the same way
   other structural link issues are already flagged.
6. **Correction, checked against the real OKF spec (GoogleCloudPlatform/knowledge-catalog
   `okf/SPEC.md`, v0.1) rather than Memoria's paraphrase of it:** the reserved headings
   are genuinely optional — §4.2: "There are no required body sections... SHOULD be used
   when applicable," not a compliance requirement. **`index.md` stays
   load-bearing for a different reason**, unrelated to the reserved headings: it's the
   one thing this analysis already needs for its own sake (a real, navigable corpus
   index instead of the current static 5-line manifest), so build it regardless of
   what OKF strictly requires.
7. **A second, separate correction, caught on a closer re-read of §3.1 — this one
   changes something load-bearing, not just downgrades a nice-to-have.** The earlier
   framing above ("only `type:` is spec-required for a file to count as a Concept at
   all") had the direction backwards. §3.1's actual text: *"All other `.md` files [i.e.
   every one except `index.md`/`log.md`] are concept documents"* — full stop, not
   conditioned on `type:` being present. §4.1 separately makes `type` the one REQUIRED
   frontmatter field. So the correct reading is: **every `.md` file in the export unit,
   other than `index.md`, already *is* an OKF concept document by classification alone;
   lacking `type:` doesn't exempt it from that classification, it just makes it a
   non-conformant one.** There is no such thing as a "plain, non-Concept `.md` file"
   living inside an OKF-compliant bundle — that category doesn't exist in the spec.
   This lands squarely on `fulltext/<work_id>.md` (categorized earlier in this analysis
   as "a plain file, not a Concept" — wrong under this reading) and on every loose `.md`
   file this analysis had been treating as outside the compliance question entirely:
   the root-level docs (`home.md`, `steering.md`, `AGENTS.md`/`AGENTS.override.md`,
   `_nav.md`, `troubleshooting.md`) and everything under `system/`
   (`vocabulary.md`, `templates/*.md`, `eval/*.md`, `dashboards/*.md`,
   `patterns/_preamble.md`) — all of it sits inside the export unit (vault root minus
   `.memoria/`), so all of it is, structurally, an OKF concept document today, and all
   of it is missing its one required field. **Resolved by adding `type:`, not by
   re-scoping the export unit** — cheaper and more honest than trying to argue any of
   this out of "the bundle":
   - `fulltext/<work_id>.md` → `type: fulltext`. Concept ID becomes `work_id` itself,
     the same identity pattern already settled for `digests/<work_id>.md` — the two are
     siblings in this respect, not fulltext being the odd one out.
   - Root-level docs and `system/vocabulary.md`, `system/patterns/_preamble.md` →
     `type: system` (generic operator/system documentation).
   - `system/templates/{note,hub,project}.md` — **not `type: template`; checked and
     that recommendation was wrong.** Read the real file: `type: note` (literal, not a
     `{{VALUE:...}}` placeholder like `title`/`id`/`description`/the body) is already
     there, and it's load-bearing — it's the exact value Obsidian's templating
     mechanism copies verbatim onto every new file created from it. `type:` is a single
     YAML key; there's no room for a second value, and overwriting it to `template`
     would break the one thing the template exists to do (new notes would come out
     stamped `type: template` instead of `type: note`). **Leave these three files'
     `type:` exactly as-is.** Residual, accepted imprecision: to a permissive external
     OKF consumer with no notion of Memoria's folder-scoping convention, an exported
     `system/templates/note.md` is indistinguishable by `type:` alone from a real
     PI-authored note. Not fixed, because it can't be without breaking the template —
     mitigated three ways, none requiring new machinery: Memoria's own tooling never
     confuses them (`schema.py::_concept_files` already scopes concept-enumeration to
     the bundle-root folders only, `system/` isn't one of them); the `{{VALUE:...}}`
     placeholder body is an obvious tell to anyone who opens the file; and `system/` was
     already marked optional/non-load-bearing for the export unit (Part 4) — a PI who
     cares can simply leave it out of what they copy.
   - `system/eval/*.md` (the gold-task fixtures) — **correction: this value already
     exists, checked against `system/eval/README.md` rather than invented.** They
     already ship `type: eval-task` (plus `lifecycle`/`workflow`/`eval_role`/
     `references`, undeclared-but-conventional), and the README already states
     "`eval-task` is not a checked Concept type and has no schema under
     `.memoria/schemas/types/`" — i.e. this repo has *already*, independently, adopted
     the exact OKF-concept-document-vs-Memoria-internal-Concept-hood decoupling this
     analysis derived. Nothing to add here beyond noticing it. `system/eval/README.md`
     itself has no frontmatter at all today; it should get `type: system` (it's prose
     *about* the eval suite, not a fixture itself).
   - `system/dashboards/*.md` → `type: dashboard` (machine-regenerated views, not
     authored content).
   This is a spec-conformance label only, **decoupled from Memoria's own internal
   Concept-hood** (whether something gets a `concepts` DB row, a `check_status`, a
   schema under `.memoria/schemas/types/`). None of `fulltext`/`system`/`template`/
   `eval-task`/`dashboard` need to appear in `concepts.concept_type`'s CHECK or get
   DB-tracked — that registry answers "what does Memoria itself treat as significant,
   checked content," a narrower and separate question from "is this `.md` file, per
   OKF's own classification, a concept document." A permissive OKF consumer handles all
   five the same way it handles any unrecognized `type:` value — per §4.1, "consumers
   MUST tolerate unknown types gracefully (typically by treating them as generic
   concepts)" — no special-casing needed on either side.
7. **Copy against a clean, committed state, not mid-write.** A drag-and-drop copy is a
   snapshot; since the vault is git-tracked and writes land via atomic commits, the
   correct invariant is "export from a clean checkout at a commit," the same way any
   git-tracked project is normally cloned/shared — not a new problem, just worth stating
   as the implicit precondition rather than assuming a copy mid-background-enrichment is safe.

**Net:** every issue a literal copy-paste export creates is resolvable by things this
analysis was already going to recommend (materialize `fulltext.md`, ship the reserved
headings, build a real `index.md`) plus two small, cheap additions (a prose-narration
linter check; an explicit statement of the export unit's boundary). None of it requires
building the ADR-107 conversion pipeline — that pipeline becomes unnecessary scope to
retire, not scope to eventually build.

**Exact boundary rule (code):** a vault path is part of the bundle **iff its top-level
segment is one of the five bundle roots.** Declared identically in two source-of-truth
places — `runtime/projections.py` `BUNDLE_ROOTS = ("works","sources","notes","hubs","projects")`
and `.memoria/schemas/folders.yaml` (`bundle_roots:` == `categories:`).

| Bundle root | Holds | Concept type(s) | Authored / generated |
|---|---|---|---|
| `works/<work_id>/` | Objective work record, full text, machine digest, raw source | `work`, `digest` | Machine-owned (capture), PI-observed |
| `sources/` | Human source-notes bridging Works into the notes graph (thesis, findings, critique) | `source-note` | PI-authored judgment layer |
| `notes/` | Atomic claim & question notes | `note` | PI-authored or machine-*proposed* |
| `hubs/` | Topic hubs with human salience (framing / curating / planning) | `hub` | PI-curated |
| `projects/<slug>/` | `project.md` (Concept) + `outline.md`, `draft.md`, `argument.canvas` (artifacts) | `project` | PI-authored |

Notes on the boundary:
- **6 Concept types map onto 5 roots** — `work` and `digest` both home in `works/`.
- **Folder membership ≠ Concept-hood.** Non-Concept files live inside roots too:
  `works/<id>/` full-text/raw source, and `projects/<slug>/` outline/draft/canvas are
  project *artifacts*, not new Concept types. **Correction**: an earlier pass of this
  analysis named these `evidence.md`/`gaps.md` — neither exists in the real code
  (`knowledge.py`'s `_project_outline_rel`/`_project_draft_rel`/`_project_canvas_rel`
  confirm `outline.md`/`draft.md`/`argument.canvas` instead); gap-analysis and evidence
  checks are query-time reports, never persisted as project-folder files. Fixed
  throughout; see Part 4 for the detail (and the §3.1 typing this now needs).
- The strict producer validator enforces that a Concept file sits under its declared
  home (`type X must live under <home>/`).

### What's actually in `works/<work_id>/` — a doc-vs-code drift, verified

`on-disk-layout.md` describes the folder as holding four things: "objective work
record, full text, digest, raw source" — implying `record.md`, `fulltext.md`,
`digest.md`, and a raw-source file all live under `works/<work_id>/`. **Checked against
every writer in `capture.py`/`operations.py`/`enrichment.py` — only one of those four is
actually written there today:**

- `digest.md` — real: `operations.py:448`, `digest_rel = f"works/{source_id}/digest.md"`,
  written by `compile_source_digest`.
- `record.md` (the `work` Concept) — **never written by any code path.** Zero hits for
  `record.md` as a write target anywhere in the runtime. This independently confirms
  G0's "delete `work`" finding from a different angle: it's not just redundant, it may
  not exist as a real artifact anywhere today.
- Full text and raw source — **not under `works/<work_id>/` at all.** `capture.py:113-115`
  writes them to `.memoria/blobs/source-content/<source_id>/content.txt` and
  `.../raw/<filename>` — a gitignored blob path, unrelated to the bundle. `on-disk-
  layout.md`'s tree diagram is describing a folder shape the code doesn't build.

**So the subfolder collapses almost entirely on its own, independent of any proposal:**
once G0 confirms `record.md` was never real, `works/<work_id>/` holds exactly
**one file, `digest.md`** — full text and raw source were already elsewhere. The only
open question left is whether `digest.md` itself needs to be a bundle file. Checked for
evidence it's ever a *link target* (something wikilinking to the digest as a whole,
as opposed to an evidence marker citing a page-span via `work_id#^pNNNN`) — found none;
`digest.yaml`'s `links:` field and `check_contradiction_links` both describe the digest
*linking out* to other Concepts, not other Concepts linking *in* to it. That's consistent
with — but doesn't fully prove — collapsing `digest.md` the same way as `record.md`: into
a DB/blob payload materialized to a file only when Obsidian needs to read it, per the
same materialization pattern already used elsewhere (`outputs`/`materialization_payloads`).
Worth one more targeted check (does any code path construct a wikilink *to*
`works/<id>/digest.md` specifically) before deciding; not done in this pass.

**Net effect if both moves are made:** the `works/` bundle root stops holding any
Concept file at all — it becomes pure machine-materialized artifact space (a digest
export, if kept as a file), and the catalog (`work_id` → SQLite row) plus
`bibliography.bib` are the only durable "this Work exists" representation.

---

## 3. Layer B — the database (`.memoria/memoria.sqlite`)

Single embedded SQLite DB. `SCHEMA_VERSION = 6`; `connect()` sets
`foreign_keys=ON`, `journal_mode=WAL`, `synchronous=FULL`. **The DDL is not inline
Python** — it lives entirely in the packaged resource `runtime/schema.sql`, applied by
`state._init()` (there is no `create_table` code, just `executescript(schema.sql)`
with `IF NOT EXISTS` + a final `PRAGMA user_version = 6`). One explicit migration
function exists: `_migrate_v4_to_v5` (rebuilds `concepts` to add the `concept_type`
CHECK). v5→v6 is implicit via the `IF NOT EXISTS` statements (adds the
`consumable_outputs` view). Fresh vaults go straight 0→6.

**16 tables, 2 views, 2 triggers, 2 indexes** (all verified against `schema.sql`):

| Table | Role | Authoritative or derived |
|---|---|---|
| `operation_requests` | Operation queue + per-request job snapshot (status pending→running→done/failed/cancelled; idempotency key) | **Authoritative** working state |
| `journal_events` | Append-only, **hash-chained** event ledger (`prev_hash`→`row_hash`); triggers block UPDATE/DELETE | **Authoritative** (JSONL files are a mirror) |
| `concepts` | Registry `concept_id → concept_type + store('db'\|'file')` | `store='db'` authoritative; **`store='file'` is a rebuildable MIRROR of markdown frontmatter** |
| `concept_verdicts` | Per-concept `check_status` (separate so verdicts survive mirror rebuilds) | **Authoritative** (this is where "checked" lives) |
| `concept_flags` | Per-concept flags (only `stale`) with reason/trigger/time | Authoritative working state |
| `outputs` | Materialization lifecycle (target path, `check_status`, `materialization_status`, sha, commit) | **Authoritative** working state |
| `materialization_payloads` | Durable exact text to materialize (crash recovery before git commit); FK→`outputs` ON DELETE CASCADE | **Authoritative** (recovery) |
| `catalog_sources` | Bibliographic catalog: identifiers, `csl_json`, coverage/text status, content/raw blob paths+hashes | **Authoritative db-store catalog** (NOT markdown) |
| `external_ids` | External identifier mappings per owner (namespace/value + provenance) | Authoritative catalog state |
| `enrichment_runs` | Per-source provider-enrichment run tracking | Authoritative working state |
| `provider_payloads` | Raw+normalized provider fetches (one per run/provider/request) — evidence & cache | Authoritative cache (blobs on disk) |
| `field_provenance` | Per-source/field winning provider, alternatives, conflict status (merge record) | Authoritative catalog state |
| `work_graph_edges` | Citation/relationship graph edges per work (references/related/topic/…) | Authoritative catalog state |
| `work_aspects` | Extracted aspects (context/key_idea/method/outcome/limitation/assumption) + verdict | Authoritative catalog state |
| `evidence_sets` | One row per `%%ev%%` marker found in markdown, classified by type/completeness | **Fully DERIVED** (rebuilt by scanning `*.md`) |
| `derivations` | Input→output lineage edges (actor pi/operation/integrity) | Authoritative provenance |
| *view* `concept_status` | `concepts ⋈ concept_verdicts`, COALESCE check_status→'unchecked' | Read projection |
| *view* `consumable_outputs` | Outputs safe to consume (checked + db-store or materialized) | Read projection |

Other DB-adjacent on-disk paths (not the sqlite file): `.memoria/memoria.sqlite-wal`/`-shm`
(WAL sidecars), `.memoria/journal-head` (committed hash anchor over the journal),
`journal/<machine>.jsonl` (filesystem mirror of `journal_events`).

**Search is a SEPARATE, filesystem store — not FTS in this DB.** Production retrieval
is deterministic pure-Python BM25 (k1=1.5, b=0.75) over checked-only markdown; the
store is `.memoria/index/search/checked/` + `manifest.json` (a document catalog +
hashes), with scores recomputed in memory per query. FTS5 appears *only* against an
in-memory `:memory:` DB as an evaluation spike, never in `memoria.sqlite`.

---

## 4. Layer C — files that are NOT in a bundle and NOT the DB

Everything else. Two `.gitignore` files matter: the **repo-root** one (governs the code
repo) and **`vault-template/.gitignore`** (ships inside the vault; governs what a
*deployed* vault commits). Under the vault ignore file, non-bundle files fall into three
groups:

**(a) Disposable `.memoria/` runtime — only the `.gitkeep` skeleton is tracked** (pattern
`<dir>/**` + `!.gitkeep`):
- `.memoria/memoria.sqlite(+-wal/-shm)`, `.memoria/.venv/`, `.memoria/locks/`,
  `.memoria/queue/**`, `.memoria/data/` (Retraction Watch CSV) — fully ignored.
- `.memoria/index/` (search index + `capability-index.json`), `.memoria/staging/{5 roots}/`
  (worker output before promotion), `.memoria/quarantine/` (rejected writes),
  `.memoria/state/`, `.memoria/blobs/provider-payloads/` + `blobs/source-content/`
  (the blobs `catalog_sources`/`provider_payloads` point at) — contents ignored,
  `.gitkeep` kept.

**(b) Generated-but-TRACKED (visible "audit/metrics" memory that commits carry):**
- `.memoria/audit/` (audit anchors — no ignore rule), `.memoria/journal-head`
  (the `journal/` rule is directory-only, doesn't match this file),
- **all of `system/`** — `system/logs/*.jsonl` (audit/classify/lint), `system/metrics/**`
  (incl. `eval/runs.jsonl`), `system/incidents/**`, `system/eval/last-run.md` — because
  the vault ignore file has **no `system/**` rule**.

**(c) Template source that is gitignored in a deployed vault** (the sharpest nuance):
- `.memoria/config/providers.yaml` and everything under `.memoria/schemas/` are **tracked
  in `vault-template/`** (the template is their source of truth) but **listed as ignored**
  by `vault-template/.gitignore` — because in a *deployed* vault they mirror the installed
  `memoria_vault` package, which is authority.

**Straightforwardly tracked authored source (present in template):**
- Vault-root pages: `index.md` (generated seed), `home.md`, `steering.md` (program
  memory), `AGENTS.md` (+`AGENTS.override.md`), `_nav.md`, `troubleshooting.md`,
  `bibliography.bib` (0-byte generated seed).
- `.githooks/pre-commit` (schema gate the installer copies into `.git/hooks/`),
  `.memoria/design-system.md`, `.memoria/plugins/memoria-policy-gate/` (fail-closed
  write gate: `plugin.yaml` + `__init__.py`), `.memoria/scripts/cron-runner.sh`.
- `system/vocabulary.md` (controlled vocab), `system/manifest.jsonl` (1-byte seed),
  `system/dashboards/` (3 dataviewjs dashboards), `system/templates/{note,hub,project}.md`
  (only 3 ship — none for the machine-owned work/source-note/digest),
  `system/patterns/_preamble.md`, `system/eval/` (README + 9 gold-task fixtures +
  `alpha15-seeded-errors.json`).
- `inbox/` — **transient** attention-projection root (`folders.yaml transient_prefixes`),
  not a bundle and not a Concept home; items converge to empty.

---

## 5. Frontmatter schemas (the 6 Concept types)

Single source: `.memoria/schemas/types/*.yaml`; loader/validator
`runtime/subsystems/lib/schema.py`; enforced by the pre-commit hook + scheduled linter.
Each schema declares `category`, `gated: false`, `required:`/`optional:` maps of
`field: kind`, and (note only) an `enums:` block.

**Field-kind grammar:** `str`, `int` (not bool), `bool`, `date` (ISO-8601), `list`,
`map`, `links` (map from `supports`/`contradicts`/`extends` → local Concept targets),
`literal:<v>` (exact), `enum:<name>`, `ulid` (26-char Crockford base32). Unknown extra
fields are **accepted** during the alpha.16 migration; the `x: map` field is the
sanctioned extension namespace (present on all 6 types).

**Universal required core (all 6 types):** `type` (literal), `id` (ulid), `title` (str),
`tags` (list), `links` (links). Empty `tags: []` and `links: {}` count as *present*
(validator treats a field missing only if absent or `None`/`''`).

| Type | Home | Extra required | Notable optional |
|---|---|---|---|
| `note` | `notes/` | — | `mode`(claim/question), `question_status`(open/resolved), `certainty`(reported/contested/unknown), `claim_text`, `quote`, `topics`(vocab-checked), `source_id`, `superseded`, `evidence_set` |
| `hub` | `hubs/` | `tag` (str, **singular** — the one canonical tag this hub is the page for) | `salience`, `aliases`, `citations` |
| `project` | `projects/` | — | `thesis`, `outcome_frame`(map), `paper_plan`(map), `question` — the only type with no `work_id`/`citations` |
| `work` | `works/` | `work_id` (str → catalog row) | `csl_json`, `identifiers`, `citekey`, `source_type`, `source_sha256`, `evidence_set` |
| `source-note` | `sources/` | `work_id` | `citekey`, `topic`(list, **singular**, not vocab-checked), `project`(list) |
| `digest` | `works/` | `work_id` | `anchors`, `evidence_set` — smallest optional set (machine-owned) |

- **No per-field defaults in the YAML.** Seeding comes from templates and
  `vaultio.apply_universal_concept_frontmatter` (setdefaults `id=new_ulid()`,
  `tags=[]`, `links={}` at write time).
- `folders.yaml` also carries: `machine_staging_roots` (5), `quarantine_root`,
  `transient_prefixes: [inbox/]`, and the installer `skeleton`. It declares **no**
  `gated_prefixes`, so `schema.py` falls back to `('notes/','hubs/')`; all 6 schemas
  are `gated: false` (gating now = staging → promotion → quarantine).
- `calibration.yaml` is **not** a frontmatter schema — it's drift-bound thresholds
  (entity-resolution 0.85 floor; classify floor 0.6 / near-tie 0.15; candidate-rank &
  outline scoring all `production_enabled: false` until calibrated).

---

## 6. File / body content schemas

**The validator checks frontmatter only** — the body is split off and never inspected.
Reserved headings and required sections are **doc/linter conventions**, not
schema-enforced. Shipped templates (note/hub/project) are minimal placeholders and do
*not* hardcode section headings.

- **note (claim mode):** `## Claim` (one atomic idea), `## Evidence and argument`
  (citekeys/evidence), `## Links` (authored typed connections — the structurally most
  significant section; body counterpart of the frontmatter `links:` map). Question mode
  uses `question_status` instead of the claim triad.
- **source-note / work / digest:** two-layer authorship — the mechanical catalog Work
  row (facts, identifiers, hashes, source-derived aspects; machine-owned) vs the PI
  judgment layer. A source note adds `## Critique` and `## Open questions`.
- **hub:** answers three questions — framing / curating / planning (a hub doing only
  the first two is static).
- **project:** body carries thesis/direction; `outline.md`/`draft.md` are artifacts.
- **Evidence markers (project drafts):** inline `%%ev: ev-<8hex> type=… state=…
  items=work_id#^pNNNN%%` markers are the **durable source**; the SQLite `evidence_sets`
  table is derived/rebuilt from them. Items reference stable `work_id#^pNNNN` source
  spans (never citekeys).
- **Typed links / wikilinks:** `links` relations are exactly
  `supports`/`contradicts`/`extends` → **local** Concept targets. `[[Target]]`,
  `[[Target|alias]]`, `[[Target#heading]]` are unwrapped; external URLs (`://`,
  `mailto:`, leading `/`) and `..` escapes are rejected. Work Concepts point at the
  catalog via `work_id`; backing URLs/identifiers live in SQLite +
  `works/<work_id>/record.md`, never in frontmatter.

---

## 7. Key cross-layer facts (don't miss these)

1. **The DB concept vocabulary is a *superset* of the markdown schema types.** The
   `concepts.concept_type` CHECK has **15** values:
   `source, source-note, work, digest, note, hub, capability, operation, skill, adapter,
   workflow, person, organization, venue, project`. Only **6** (work, digest, note, hub,
   project, source-note) have a frontmatter YAML schema and live as bundle markdown. The
   other **9** (`source`, `capability`, `operation`, `skill`, `adapter`, `workflow`,
   `person`, `organization`, `venue`) are **db-store-only** concepts (the catalog
   `source` row, capability/operation registries, entity types) with no frontmatter
   schema. **DB `source` ≠ markdown `source-note`** — a catalog row vs a PI-authored
   Concept.
2. **`check_status` and evidence sets never live in frontmatter** — SQLite is authority;
   forged verdict fields are rejected.
3. **Two vault-root generated projections** (`TRACKED_PROJECTION_PATHS`), both tracked,
   both carrying a "Generated by … edit source records instead" banner, both at root
   (*not* inside a bundle): `index.md` (static 5-root manifest) and `bibliography.bib`
   (BibTeX projected *from the SQLite catalog* — lossy relative to the catalog graph).
   `check_tracked_projections` re-renders both to detect drift.

### Doc-vs-code drift flags (code wins; not a full audit)
- `frontmatter.md`'s universal-fields table lists `id` kind as `str`; the real schema is
  stricter `id: ulid`.
- `system-artifacts.md` / a `write_workspace_indexes` docstring say `index.md` is
  "generated from checked Concept files," but `_workspace_index()` emits a **fixed
  5-root** manifest, enumerating neither Concepts nor per-bundle indexes.
- The optional `evidence_set:` **frontmatter field** (on note/work/digest) is a
  different mechanism from the draft `%%ev%%` **markers** + derived `evidence_sets` rows
  that `frontmatter.md`/`evidence-sets.md` call "not frontmatter." Two distinct things.
- Dormant machinery in `schema.py` unused by the 6 schemas: `required_any`,
  `promotion_gate`, `enums.lifecycle`/`enums.check_status` (`lifecycle` is itself a
  retired field). `VOCABULARY_FIELDS['source']` matches no schema type (types are
  `source-note`/`work`), so only note `topics` can be vocab-checked.
- `enrichment_runs.journal_id` and `provider_payloads.ttl_until` are declared in
  `schema.sql` but never written — reserved/unused.
- `vault-template/.gitignore` states every secret file ships a sanitized `.example`
  sibling, but no `.env`/`.example` exists in the template — a small convention gap.
- **`vault-template/.gitignore`'s `catalog/sources/*/raw/` rule is stale.** Grepped for
  any code that actually *writes* a file under a real `catalog/` folder (as opposed to
  constructing a `catalog/sources/{id}`-shaped string) — found none. `folders.yaml` and
  `projections.py`, the two authoritative sources for real bundle-root folders (per this
  document's own "exact boundary rule"), don't list `catalog/` at all. `catalog/...`
  strings are purely a virtual `concept_id` namespace `integrity.py` constructs for
  `concept_check_status` lookups and attention-flagging on db-store concepts (the
  catalog `source` rows) — never a real on-disk path. The gitignore rule references a
  folder no code has ever created.
- **`.obsidian/` doesn't exist in the template at all** — confirmed via both
  `git ls-files` and a plain `find`, zero hits either way. The two gitignore entries
  (`workspace.json`, `workspace-mobile.json`) are pre-emptive, for when Obsidian creates
  `.obsidian/` itself on first open of a live vault; the template ships no Obsidian
  config (plugin list, themes, etc.) of its own.

---

## 8. How this was verified

- **DB:** read `runtime/schema.sql` (all 16 `CREATE TABLE` + 2 views + 2 triggers +
  2 indexes) and `runtime/state.py` (`_init`/`_migrate_v4_to_v5`, writers/readers) in
  full; confirmed the 15-value `concept_type` CHECK directly. Settled the "is search a
  separate store" question by reading `search_index.py`/`retrieval_substrate.py`.
- **Schemas:** read all 6 `types/*.yaml` + `folders.yaml` + `calibration.yaml` + the
  `schema.py` loader/validator; cross-checked `frontmatter.md`/`document-types.md`.
- **Bundle boundary & non-bundle inventory:** `projections.py`, both `.gitignore`
  files, `on-disk-layout.md`/`system-artifacts.md`/`memory-substrates.md`, and a full
  `git ls-files vault-template` walk — every tracked file maps to exactly one bucket
  with no double-counting.
- A fifth completeness-critic pass re-checked the enumeration against the live tree and
  DDL (it caught a 16→**15** miscount, corrected above).

To reproduce the DB truth: `sqlite3 <vault>/.memoria/memoria.sqlite '.schema'` (matches
`src/memoria_vault/runtime/schema.sql`).

---

# Part 2 — Rethink: the clean-slate design

> **Method note (firewall).** This part derives the data structure from requirements
> *as if the current code and its design-history did not exist*, then compares. Where
> my independent derivation lands on the same structure Memoria shipped, I say
> **"converges"** and show the derivation — I do **not** cite Memoria's own ADRs as
> proof they were right (that would be a rubber stamp, not a rethink). The design
> ledger is used only in §5 to measure the gap.

## 1. Requirements (derived independently)

**Who.** A single principal investigator doing scholarly research synthesis: collects
academic sources, extracts claims and evidence, builds a linked argument graph, drafts
cited papers. **Single-user, local, primarily one machine.** Time horizon: a research
program is a **career-scale asset** (years to decades).

**What the data must do.**
1. Capture heterogeneous sources with rich bibliographic metadata pulled from external
   providers, keeping **provenance** (which provider asserted what; how conflicts resolved).
2. Let the human author **atomic, densely-linked, typed** claims/questions grounded in
   cited evidence.
3. Admit **machine assistance** (extraction, enrichment, drafting) that the human
   reviews — machine output must be **quarantinable and verifiable**, never blindly trusted.
4. Produce **verifiable** outputs: every claim traces to evidence; citations survive.
5. Be **auditable / tamper-evident**: who wrote this, when, derived from what.
6. Be **crash-safe**: a half-finished operation must never corrupt state.
7. Be **graph-queryable**: citation networks, argument graphs, gap analysis.

**Success test.** After a fresh clone on a new machine (and after the tool is gone
entirely), the human-authored knowledge is still complete, readable, and navigable in a
generic tool; every checked claim still resolves to its cited source; no machine-written
content is silently trusted.

## 2. The pivotal requirement: interrogating the "keep-test"

Every expensive structure below hangs off **one** constraint: *must the durable
substrate be tool-independent plain text, or is export-on-exit enough?* This is the
pivot, so it's the rethink — not a premise to inherit.

**The fork.**
- **(A) Tool-independent plain text is a hard requirement.** For a career-scale asset,
  the dominant risk is not disk failure (backups handle that) but **tool/format death** —
  the app is abandoned, the vendor folds, the binary won't run on a 2040 OS. The field's
  standard mitigation for exactly this risk is **open, human-readable, plain-text
  formats** (why scholarship runs on LaTeX/BibTeX/Markdown; why archives mandate open
  formats; the *longevity* and *ownership* ideals of local-first software, Kleppmann &
  Ink & Switch 2019). Under (A) the durable store **must** be plain markdown + a portable
  bibliography, and anything not reproducible from plain text is at risk.
- **(B) Export satisfies longevity.** SQLite is itself an exceptionally durable, open,
  single-file, self-describing format (a US Library of Congress recommended archival
  format — *sqlite.org/locrsf.html*). Under (B) the primary store could be **SQLite**,
  with markdown/BibTeX generated as an *export*, and the whole cross-store apparatus
  (survival copies, two-phase materialization, bibliography atomicity) disappears.

**Deciding sub-question:** is the durable artifact *lived in by other tools
continuously*, or only *recovered at exit*? For this user it is lived in: the PI reads
and edits in a markdown tool (Obsidian) daily — wikilinks, graph view, and dashboards all
operate on the **live** markdown. So the human-authored knowledge must be
**markdown-authoritative continuously**; if SQLite were primary, every Obsidian edit
would be a fork against it — a two-writer reconciliation problem on every keystroke. The
*catalog* (bibliographic facts, provider payloads, citation graph) is the opposite: never
hand-edited in a markdown tool, inherently relational/graph, and gains nothing from being
files.

**Call: framing (A) holds — but for one reason only, and it isn't portability.**
I take side (A), but the paragraph above overstates why: it credits *both*
live-editing *and* portability/longevity as joint support. **Correction, prompted by a
direct challenge to this reasoning:** those are two separate justifications, and only
one currently earns its keep.

- **Live-editing (real, present-tense, load-bearing):** the PI edits in Obsidian daily;
  markdown must be authoritative *now*, continuously, or every edit forks against a
  primary store elsewhere. This alone is sufficient to require markdown-primacy for the
  content that's actually hand-edited.
- **Portability/longevity (currently NOT earning its keep):** this is the justification
  that cites Kleppmann/Ink & Switch and "tool-independent plain text." But Part 1 §2
  just established that Memoria's bundle is **not** OKF-compliant — it borrows OKF's
  nouns without its relationship semantics or identity model. So "these files are
  portable to any tool" is **not currently true**. Counting portability as a reason the
  architecture is earning its cost today is treating an aspiration as a present fact —
  exactly the mistake it's fair to call out. Keeping content in files "to be portable"
  when (a) portability isn't needed at every moment and (b) the portability you'd get
  isn't real yet, is paying an ongoing cost for a payoff that isn't being delivered.

**What this changes:** the honest boundary for markdown-primacy today is narrower than
originally framed — it's earned *only* by live-editing, not by longevity. Given the
zero-migration-cost standing principle (§5), the correct response isn't to keep
gesturing at portability — it's to **actually build the compliant OKF export now**
(Part 1 §2's superset analysis already worked out how: mostly additive, one identity
fork resolved at the export boundary). That's the only way "portability" stops being a
borrowed justification and becomes a real, present-tense property. Until that export
ships, don't cite portability as a reason anything is designed the way it is — cite only
live-editing, and treat the rest of the "keep-test" framing as a target, not a fact.

Where it flips to (B) entirely: **if the PI never edited in a markdown tool (CLI-only),
SQLite-primary + markdown-as-export would be the simpler correct design, full stop** —
and with portability now isolated as a build-it-or-it-doesn't-count property rather than
an automatic side effect of "being files," that flip condition is easier to hit than the
original framing implied, not harder.

## 3. Prior art, used to *derive* structure (not decorate)

| Pattern / source | What it derives here |
|---|---|
| **System-of-record vs derived data** (Kleppmann, *DDIA*) | The core seam: put each fact in the store whose writer/consistency-model matches it. Human claims (edited live in markdown) → markdown SoR. Objective catalog (machine-maintained, relational) → DB SoR. |
| **CQRS / Event Sourcing** (Fowler; Greg Young) | An append-only event record + separately-maintained read models; *and* the decision **not** to go full event-sourcing (below). |
| **Local-first software** (Kleppmann/Ink & Switch 2019) — longevity & ownership ideals | The *aspiration* the keep-test reaches for — but per §2's correction, this ideal isn't currently delivered (no OKF compliance yet), so it names a target to build toward, not a property the current design should be credited with. |
| **SQLite as an application/archival file format** (sqlite.org) | The counter-case (B) that makes the keep-test a *choice*, not an axiom — and the justification for putting working state in one embedded DB. |
| **Datomic** (accretion-only log, "as-of") | The append-only, hash-chained audit ledger lineage. |
| **W3C PROV** (entity/activity/agent) | The provenance graph: per-field winning-provider records + input→output derivation edges. |
| **CSL-JSON** (Citation Style Language) | The catalog's interchange representation for bibliographic records. |
| **BibTeX** (entry travels with the document) | The **survival-copy** pattern: denormalize the minimal citation into the markdown so it stands alone. |
| **Zettelkasten / Luhmann** | Atomic notes + dense **typed** links as the knowledge-graph shape. Also the direct precedent for the project/corpus split (§2, on `projects/`): Zettelkasten's own permanent slip-box vs. project-specific reference collection — the slip-box never depends on or links into a project's working notes, so the project can be discarded when finished without touching the permanent graph. Same one-way structure, same reason it's safe to erase. |
| **W3C Web Annotation / TextQuoteSelector** | Anchoring quotes/evidence as selectors over source text rather than as note *types* or frontmatter fields. |
| **Two-phase commit / write-ahead intent** | The cross-store write protocol: a durable intent record (the exact bytes) before the second-phase git commit, so recovery can replay. |

## 4. The clean-slate design (derived) — and where it converges

Deriving purely from §1–§3:

1. **Two systems of record, split on *authorship*.** Objective catalog (bibliographic
   facts, provider payloads, citation/entity graph, provenance) → **relational DB**;
   human interpretive knowledge (claims, questions, hubs, projects, source-notes) →
   **plain markdown with typed frontmatter + typed links**. Derived from
   system-of-record-vs-derived + the §2 live-editing call. **Converges** with Memoria's
   two-graph model.
2. **The bridge is a live pointer (`source_id`/`work_id`); per-file survival copies are
   *not* re-derived here — see G0.** My first pass derived "denormalize a compact
   citation into every note, because the DB might die" (the BibTeX-travels-with-the-
   document pattern). On reflection that derivation picked the wrong unit of survival:
   files and the DB live in the **same git-tracked vault** and are lost or recovered
   *together*, so the granularity that matters is **per-vault** self-sufficiency (does
   the whole recovered vault, including its bibliography export, stand alone), not
   **per-file** self-sufficiency (does one cherry-picked note, opened with nothing else
   present, still resolve its citation). Baking a copy into every note buys robustness
   against a scenario — recovering a single file stripped of the vault around it — that
   isn't the actual threat model. **Revises, not converges** — see G0.
3. **Verdicts and lifecycle are DB-only, never frontmatter.** "Checked" is a *claim about*
   a file; if it lived in the file, writing it would rewrite the file, hand-edits could
   forge it, and every reader would have to distrust what it reads. So it belongs in the
   store that isn't the artifact. Derived from "machine output must not be blindly
   trusted" + "the human edits the artifact live." **Converges** (meaning-only frontmatter;
   `check_status` in SQLite).
4. **Machine writes are staged → verified → promoted; readers gate on a barrier.** Since
   machine output is untrusted, it cannot land in the human corpus until checked; and a
   file-owned output isn't *consumable* until it's actually on disk (checked ≠
   materialized — two independent states). Derived from requirement 3 + the two-store
   reality. **Converges** (staging/quarantine + the `consumable_outputs` barrier;
   `check_status` and `materialization_status` as separate columns).
5. **Cross-store writes need a durable intent record of the *bytes*.** DB-commit-then-git
   can tear. A hash alone can't rebuild lost staging, so the intent record must hold the
   exact payload text. Derived from two-phase-commit + "recovery must reconstruct."
   **Converges** (`materialization_payloads` stores bytes). *This structure exists only
   because of the §2 (A) call — under (B) it vanishes.*
6. **An append-only, hash-chained audit ledger — as a side-record, not the SoT.** Tamper
   evidence wants a Merkle-style chain. But should everything *fold from* the log
   (full event-sourcing)? For **single-user, local**, no: there are no concurrent writers
   to serialize and no need to rebuild-by-replay, and the durable human artifact is the
   markdown, not the log. So the log records *what happened*; it is not the generative
   source. **Converges** — and see §6 for the condition that flips it.

**Honest conclusion:** independently derived, the clean-slate design **is** the spine
Memoria already ships. That is a legitimate rethink outcome, not a failure to find
improvements — the interesting output is the *boundary conditions* (§2, §6) and the
genuine divergences (§5).

## 5. Where the as-built *diverges* from the clean-slate ideal (the payload)

> **Project-stage note.** Memoria is pre-install, early alpha: **no vault has ever been
> deployed**, so there is no populated database and no legacy frontmatter anywhere to
> protect. That makes migration cost **zero right now** — every fix below should pay its
> full cost immediately rather than ship a hedge (grace period, compat shim, dual-write)
> for a constraint that doesn't exist yet. That hedge is itself a cost — it's code that
> has to be written, tested, and later removed, for a transition with no one on the other
> side of it. The fixes below assume this; hedging returns only once a real installed
> base exists (beta/GA), and should be added *then*, not pre-built now.

Ranked by severity. These are real gaps between the ideal and the code.

**G0 — Per-file citation/backing-metadata survival copies should collapse into
SQLite-only (product direction: SQLite as SSOT and the only repository, wherever a
field isn't something the PI hand-edits).** Confirmed scope: the knowledge graph
(notes/claims/hubs/projects, source-notes) stays live-edited markdown — Obsidian remains
a first-class editor for that. But several optional fields exist on the 6 type schemas
*only* to let a single file stand alone if SQLite dies — nobody hand-types them:
- `citations: list` on `note.yaml`/`digest.yaml`/`hub.yaml` — the baked-in compact
  citation (title/authors/issued/one-of doi-url-citekey), enforced by
  `integrity.check_citation_survival` / `state.check_citation_payload`.
- `csl_json`, `identifiers`, `source_sha256` on `work.yaml` — objective catalog facts
  duplicated onto the Concept, reachable via `work_id` already.
Per the corrected §4.2 derivation, the right unit of survival is the **vault**, not the
**file** — these fields buy per-file self-sufficiency for a scenario (a note recovered
with nothing else present) that isn't the real threat model, at the cost of a second
copy of catalog data to keep in sync on every enrichment.
*Fix:* delete these fields from the 6 schemas; keep only the live pointer (`source_id`/
`work_id`). Replace the per-file `citation-survival` integrity check with an
**export-completeness** check: every catalog source referenced by a `checked` Concept
must be present in the bibliography/citation export, not baked into the note itself.

**One bibliography file, either regeneration path is fine.** There should be exactly
**one** BibTeX file — the existing `bibliography.bib` already is this — holding
everything needed to cite a catalog Work. It doesn't need an atomic-with-capture trigger:
`render_references_bib` reads `catalog_sources` fresh and is cheap/idempotent, so it can
be regenerated **either** by hand (an on-demand CLI/operation call) **or** live
(triggered automatically on catalog-affecting writes) — either satisfies the invariant,
as long as regeneration (or a freshness check against it, via the existing
`check_references_bib`/`check_tracked_projections` drift check) runs as part of promoting
a note/digest/hub to `checked`. That's the concrete gate the export-completeness check
needs: **checked implies the bibliography is current**, not "the bibliography is updated
transactionally with every write." Today `write_references_bib` is only invoked from a
worker operation and the tracked-projections drift path (no atomic capture-time hook) —
that's fine for *either* regeneration mode; it just means the check-promotion step must
itself trigger (or verify) a regeneration rather than assuming one already happened.

**G0 continued — the type roster shrinks further once the SSOT-collapse is followed to
its conclusion.**

- **Delete `work` as a Concept type; it is a duplicate SSOT, not just duplicate fields.**
  Once G0's optional catalog-mirror fields are stripped, `work.yaml`'s remaining surface
  is `type/id/title/tags/links/work_id` — a bare identity wrapper. If `bibliography.bib`
  is keyed to include `work_id` (not just `citekey`), the catalog row + that one export
  file already answer "does this work exist, how do I cite it" — the file buys nothing
  a `work_id` field can't. `tags`/`links` for "this source as a graph node" have a home
  already: `source-note` (or its replacement below), which is the file every catalog row
  gets linked to in practice anyway. Concrete check before deleting: I grepped
  `capture.py`/`operations.py`/`knowledge.py` and found no code path that *requires*
  `works/<work_id>/record.md` to exist (the one hit, `knowledge.py:1591`, just recognizes
  the filename if present — it doesn't assert it) — but this was a targeted check, not
  an exhaustive sweep of the capture/worker pipeline, so confirm before removing the type.
- **Fold `source-note` into `note` as a `mode` value, not a separate type.** This isn't
  just simplification — it's applying the project's **own already-established principle**
  (ADR-126, alpha.15: a mode is "declared intent," used when something is "a flippable
  state, not a fundamentally different artifact"; note already uses this for
  `mode: claim | question`). A source-note is the same kind of artifact as a claim note —
  atomic, densely linked, evolving — just doing different intellectual work
  (interpreting a source vs. asserting a claim). It fits the *mode* bucket, not the
  *type* bucket, by the schema's own stated test. Concretely: extend
  `enums.mode` to `[claim, question, hypothesis, tension, definition, work]` — **naming
  corrected from an earlier pass** (see Part 3): the original proposal used
  `mode: source`/`mode: concept`, which is exactly the terminology collision Part 3
  audits against — `source` is OpenAlex's word for a *venue*, and `concept` collides
  with Memoria's own load-bearing "Concept" noun *and* OpenAlex's deprecated Concept
  entity. `mode: work` is available once G0 deletes the markdown `work` Concept type
  (freeing the word) and correctly names "a note about a specific Work" the way
  OpenAlex itself names that entity; `mode: definition` replaces the term-pinning mode
  without colliding with anything. The `## Critique`/`## Open questions` body sections
  become the `mode: work` body convention, same as `## Claim`/`## Evidence and argument`
  is for `mode: claim`. Two schema wrinkles to resolve, not blockers:
  - `work_id` is *required* on `source-note` today; `note` only has optional `source_id`.
    The field-kind grammar has no "required only when `mode: X`" primitive — either add
    one, or enforce "`mode: work` implies `work_id` present" at the linter level
    instead of the schema level (matching how `question_status` is already
    mode-conditional only by convention, not by schema enforcement).
  - `note.topics` (vocab-checked against `research_area`) and `source-note.topic`
    (unchecked, singular) look like the same idea with two names and two behaviors —
    reconcile which one survives the merge; don't carry both forward silently.
- **`digest` stays a separate type — it's genuinely different-in-kind, not a mode.**
  Cross-referencing the wiki-LLM digest pattern you linked (Karpathy's gist): that
  pattern's "write a summary" sub-step is exactly Memoria's `digest` — a compressed,
  machine-authored reading of one immutable source. ADR-126's mode-vs-type test asks
  whether something is "a flippable state and role" on a human-authored artifact; a
  digest isn't a PI epistemic move at all, it's a derived machine artifact analogous to
  `fulltext.md` or `record.md` — so it doesn't fit the mode collapse the same way
  `source-note` does. Open question as originally posed here (both since resolved,
  documented where each was settled — see below): does `digest` need independent
  Concept-hood (its own `id`, linkable target) at all, or could it be a plain artifact
  like `fulltext.md`, referenced only by `work_id#^pNNNN` span?
  **Resolved, twice over, elsewhere in this document — and the framing above turned out
  backwards on one point:** `digest` stays a Concept (`work_id` as its own Concept ID,
  no separate ULID — Part 4). And `fulltext.md` was never actually the "plain,
  non-Concept" alternative this passage poses it as: per the §3.1 correction (Part 1
  §2), every `.md` file except `index.md` already *is* an OKF concept document, so
  `fulltext.md` gets `type: fulltext` and the identical `work_id`-as-Concept-ID pattern
  as `digest` — the two aren't examples of opposite choices, they're the same choice.
  The real, still-relevant distinction this passage was reaching for isn't
  Concept-hood-per-se — it's that neither needs a `concepts` DB row / `check_status`
  tracked the way PI-authored content does; that's a separate axis from whether a file
  counts as an OKF concept document at all.
- **Terminology note, mostly self-resolving:** OpenAlex's "Source" entity means a
  journal/repository/venue that hosts works — already what Memoria's DB `concept_type`
  enum calls `venue`. Memoria's own "source" vocabulary (`source-note`, `sources/`, the
  catalog's `concept_type='source'` row) means something unrelated: a document being
  read. If `source-note` folds into a `note` mode, the `sources/` folder and the
  `source-note` type name disappear, which removes most of the collision surface. The
  residual piece is the DB catalog's `concept_type='source'` label itself, which still
  reads as "OpenAlex Source" to anyone who knows that vocabulary — worth a rename pass
  (e.g. to something like `work-record`) if this is touched, but that's a separate,
  narrower cleanup from the roster changes above.

**G1 — Frontmatter validation was flipped closed, then re-opened (regression).**
A schema-validated substrate must be **closed** (reject undeclared fields) — otherwise the
schema doesn't actually constrain and consumers can't trust field presence. alpha.15
correctly shipped closed validation with an `x:` escape hatch; alpha.16 re-opened it to
permissive ("unknown fields accepted during migration"). This is a **documented reversal
of a first-principles decision**, and it's the sharpest catch.
*Fix:* re-close it now, no phase-in. There is no installed vault anywhere carrying a
frontmatter field this would break, so the "migration grace period" it was reopened for
protects nobody — flip `validate_frontmatter` back to rejecting undeclared fields in the
same change, keep the `x:` hatch for real extension data. A sunset-dated grace period is
warranted once real vaults exist and could be broken by tightening; today it's a hedge
against a risk that isn't there yet.

**G2 — The concept-type vocabulary lives in two hand-maintained places and has already
drifted.** The 6 markdown types own their fields in `schemas/types/*.yaml`; the DB
re-declares a **15-value `CHECK`** hardcoded in `schema.sql`, hand-maintained, and out of
sync — it still carries `person/organization/venue` (entity types with **no** YAML schema
and no shipped writer — the entity graph is design-only) and it splits DB `source` vs
markdown `source-note`. There is no single "what is a Concept" definition.
This resolves in **either** direction (pick per roadmap, don't just shrink):
- **(a) single-source-down:** derive the DB `CHECK` from the schema registry at init
  (generate the enum, or replace the `CHECK` with a FK to a `concept_types` table seeded
  from the YAMLs). DRY, drift-proof; couples DB init to the schema loader.
- **(b) single-source-up:** if the two-graph *entity* model is real, actually build the
  `entities` / `catalog_links` tables the design specced-but-never-shipped and give
  entities a real representation — the enum stops being aspirational. More work, honors
  the model.

Which one is a scope call (does the entity graph ship or not), not a migration-cost call —
either way, with no installed vaults there's no back-compat shim to write: change the
`CHECK` list directly to whatever the chosen shape needs, in the same PR.

**G3 — `_migrate_v4_to_v5` is dead code protecting a DB that has never existed in the
wild, and it's the wrong shape for the day migration starts mattering.**
`_init` runs `schema.sql` (all `CREATE … IF NOT EXISTS` + `PRAGMA user_version=6`) plus
exactly one explicit migration, `_migrate_v4_to_v5`. Since **no vault has ever been
installed**, no v4 (or v5) database exists anywhere outside a developer's disposable
test fixture — this function has zero real rows to migrate today. Carrying it is pure
accreted cost: dead code, plus a false signal that "migrations are handled here" when the
mechanism (`CREATE IF NOT EXISTS`, no `ALTER`) is actually unsound the moment a real
migration is needed — any **column** added to an existing table would silently fail to
land on a populated DB (`enrichment_runs.journal_id` and `provider_payloads.ttl_until`
are declared in `schema.sql` but never backfilled — invisible today only because nothing
reads them yet).
*Fix — pay it now, not later:* delete `_migrate_v4_to_v5` and collapse `schema.sql` to
the single intended shape directly (there is nothing to preserve). Do **not** pre-build a
migration-ladder framework speculatively — that machinery earns its cost only once a real
installed base exists to protect, per the project-stage note above. What to add *now*,
cheaply: a written rule ("a schema change to an existing table always ships as an
explicit numbered migration with `ALTER`, never bare `CREATE IF NOT EXISTS`") so the
ladder is built correctly *when* the first real installed vault makes it necessary —
not before.

**G4 — Three mechanisms for one idea ("evidence set") + dead schema surface.**
Evidence sets exist as (i) an `evidence_set:` **frontmatter field** (note/work/digest),
(ii) inline `%%ev%%` **body markers**, and (iii) the derived `evidence_sets` **table**.
alpha.15's own relocation logic ("quote/excerpt fields relocate to a W3C anchor, not a
type") argues the frontmatter field should likewise be a marker-derived DB row — keep the
marker+table pair, retire the frontmatter field. Alongside it, prune dead schema
machinery no type uses: `required_any`, `promotion_gate`(+`promoted_at`),
`enums.lifecycle`/`enums.check_status`, and `VOCABULARY_FIELDS['source']` (matches no
type). A clean-slate schema omits machinery nothing exercises.

**G5 — Minor: authority ambiguities.** `index.md` is a *static* 5-root manifest but docs
say it's "generated from checked Concepts" (doc/code drift). And `.memoria/schemas/` +
`config/` are tracked-in-template but gitignored-in-deployed-vault, mirroring the package
— two authorities that can silently drift. *Fix:* one authority + a generated mirror
carrying a drift check (the tracked-projection drift mechanism already exists; extend it).

## 6. Trade-offs and where the call flips

- **The whole DB/file split is *earned* by the §2(A) call, not free.** Its remaining
  price: the two-phase materialization protocol and bibliography atomicity exist **only**
  because the knowledge-graph markdown is authoritative-and-live. If the product ever
  drops that live-editing surface (CLI-only), delete both and make SQLite primary with
  markdown-as-export. Re-check this boundary before building anything else on the
  cross-store machinery.
- **G0's collapse trades per-file robustness for per-vault robustness.** A note recovered
  in total isolation (no bibliography export alongside it) now carries a bare `source_id`
  pointer instead of a self-sufficient citation — correct once files and the DB are
  understood to live and die together in the same vault, but it means the export path is
  now **load-bearing**, not a nice-to-have. If citation-survival is ever needed at
  finer-than-vault granularity (e.g. sharing a single note outside the vault), that's the
  condition that flips G0 back toward per-file copies.
- **Log as audit-ledger, not source-of-truth, is correct *for single-user local*.** It
  flips under **multi-writer or multi-machine sync**: there you want an ordered log as the
  SoT plus CRDTs to reconcile — which is precisely the scope Memoria deferred. If
  cross-machine sync enters scope, revisit §4.6 first; it changes the spine.
- **Closing frontmatter (G1)** trades migration convenience for trust. The trade only
  favors "open" while a live migration is in flight; past that, open validation is pure
  liability.

## 7. Migration sketch (target first, then sequence)

Target = the §4 design with G0–G4 closed. Order by risk, smallest-destructive-first
(matches the repo's "structural change gets its own tiny PR, merged first" rule):

Pre-install means every step below ships directly, in one PR, with no flag/shim/grace
period — that hedging machinery is itself the thing to avoid building right now.

1. **G0 (the SSOT-collapse):** make check-promotion (for any note/digest/hub/work
   referencing a catalog source) trigger-or-verify a `bibliography.bib` regeneration —
   this is the one prerequisite the rest of G0 depends on, and it's cheap since
   `render_references_bib` is idempotent (no need to also wire an atomic capture-time
   hook; hand or live regeneration both work as long as this gate exists). Then: delete
   `citations:` from `note.yaml`/`digest.yaml`/`hub.yaml` and `csl_json`/`identifiers`/
   `source_sha256` from `work.yaml`; swap `check_citation_survival` from a per-file
   payload check to an export-completeness check against `bibliography.bib`.
2. **G3 (correctness, isolated):** delete `_migrate_v4_to_v5`; rewrite
   `schema.sql` directly to the intended final shape (drop or genuinely wire up
   `enrichment_runs.journal_id` / `provider_payloads.ttl_until`); add the "existing-table
   changes are explicit numbered `ALTER` migrations" rule to the repo's schema-change
   guidance so it's ready the day a real install exists. No behavior change today,
   removes dead code and a latent footgun.
3. **G2 (structural, its own PR):** choose (a) or (b); if (a), generate the DB `CHECK`/FK
   from `schemas/types/*.yaml` at init and delete the hardcoded enum literal; remove
   vestigial types (`mcp`, and `person/org/venue` unless (b) ships their tables) directly.
4. **G1 (closes the trust gap):** flip `validate_frontmatter` to closed now, no flag, no
   sunset date — nothing installed depends on permissive validation.
5. **G4 (cleanup):** retire the `evidence_set` frontmatter field in favor of markers+table;
   delete dormant schema machinery. Pure deletion once nothing references them.
6. **G5 (docs/drift):** correct the `index.md` docs; put the schemas/config mirror under
   the existing tracked-projection drift check.

**Verification:** each step is gated by `python3 scripts/verify pr`; G3 by a fresh-install
schema test (`open a new vault DB, assert every declared column exists and is reachable`)
rather than a populated-fixture replay, since there is no populated fixture to protect
yet; G1 by the closed-validation path rejecting an undeclared field in a test.

---

# Part 3 — OpenAlex terminology audit

> **Goal, as stated:** adopt OpenAlex's vocabulary completely — use only its terms, and
> never reuse one of its terms for a different meaning, or invent a different term for
> something it already names. Grounded in OpenAlex's own docs (fetched directly, not
> from memory) and an exhaustive sweep of every schema, doc, and code path touching
> catalog/entity terminology. Two independent full-repo sweeps (schemas+docs; runtime
> code+DB) plus a third pass fetching OpenAlex's official terminology, cross-referenced
> below.

## OpenAlex ground truth (condensed)

| Entity | Means | Canonical ID |
|---|---|---|
| **Work** | A scholarly document (article, book, dataset, thesis, preprint...) | DOI |
| **Author** | A person who creates works | ORCID |
| **Source** | A journal, repository, conference series, or book series that **hosts** works — **not a document** | ISSN-L |
| **Institution** | A university, research org, or other affiliation | ROR |
| **Topic** | One of ~4,500 machine-assigned research topics, in a **Domain(4) > Field(26) > Subfield(254) > Topic(~4,500)** hierarchy | — |
| **Concept** | **Deprecated** — the old ~65,000-term Wikidata-derived taxonomy, superseded by Topic. Endpoint still technically live, explicitly unmaintained. | — |
| **Publisher** | An org that publishes works | — |
| **Funder** | An org that funds research | — |
| **Keyword** | A short phrase derived from a work's assigned Topics (not independent free tags) | — |
| **Authorship** | The compound object linking one Work to one Author, *with* that author's institutions, position, and corresponding-author flag | — |

## Confirmed collisions — same word, conflicting meaning

**1. `source` — the headline collision, and it's self-inflicted twice over, not just against OpenAlex.**
Within Memoria's *own* `schema.sql`, the word means two opposite things:
- `concepts.concept_type = 'source'` (line 50) / the `source-note` type / the `sources/`
  folder — **a captured document** (the thing OpenAlex calls a **Work**).
- `work_graph_edges.relation_type = 'source'` (line 174) — populated straight from
  `location.get("source")` in OpenAlex API responses — **literally OpenAlex's own
  `Source` entity, a venue.**

So the same schema file uses "source" for a document in one table and a venue in
another. Design-history shows the project has *felt* this collision before — alpha.14
docs write "OpenAlex **Source(s)**" (capitalized, disambiguated) specifically to avoid
confusion with Memoria's own "source" — but that disambiguating habit never made it into
the schema or the current docs.

**2. `Concept` — Memoria's most load-bearing architectural noun, colliding with OpenAlex's deprecated entity.**
Memoria's "Concept" = any typed markdown document (`docs/reference/glossary.md`,
`frontmatter.md`, `on-disk-layout.md` — used dozens of times, the term the whole schema
system is named after). OpenAlex's `Concept` = the retired Wikidata topic taxonomy,
replaced by Topic. **Purely lexical** — Memoria correctly maps OpenAlex's `concepts`
field to `topic` graph edges, never to its own "Concept" doc type, so there's no
semantic bleed. But it's the single highest-risk term for anyone reading both
vocabularies side by side, precisely because it's Memoria's *most* central word.

**3. `topic`/`topics` — three overlapping things wearing one name, plus an internal singular/plural drift.**
- Memoria's frontmatter `topics:` (note.yaml, vocab-checked against a ~30-term curated
  `research_area` list) — free-form, PI-curated, unrelated in structure to OpenAlex's
  machine-classified Domain>Field>Subfield>Topic hierarchy.
- `source-note.yaml`'s `topic:` (**singular**, unchecked) — looks like the same idea as
  `note.topics` with a different name and no validation. Independent of the OpenAlex
  question, this is just drift between two schemas describing the same kind of value.
- `work_graph_edges.relation_type = 'topic'` — silently merges **four** different
  taxonomies into one edge bucket: OpenAlex's current Topics, OpenAlex's *deprecated*
  Concepts, MeSH descriptors, and SDGs (`enrichment.py:1023-1037`). This is a real
  information-loss issue, not just naming — once merged, nothing at query time can tell
  which taxonomy a `topic` edge came from without re-parsing `raw_json`.
- `csl_json.memoria.topics` (`update-work.md`, free-text, PI-editable) — a *third*
  "topics," disconnected from both of the above.

**4. `authorship` (relation_type) only carries the Author, not OpenAlex's actual `Authorship` object.**
OpenAlex's `Authorship` bundles author + institutions + position + corresponding-flag.
Memoria splits this into two sibling edges — `relation_type='authorship'` (author only)
and `relation_type='institution'` (institutions only) — so neither one, alone, is what
OpenAlex means by the word it's named after.

**5. `institution` (relation_type) vs. `organization` (concept_type) — same real-world
entity, two different Memoria names, in the same codebase.** `integrity.py:675-679`
carries the Rosetta stone that admits this: `{"authorship": "person", "institution":
"organization", "source": "venue"}` — proving the design *intended* `organization` and
`institution` to be the same thing, but never reconciled the name.

## Confirmed synonyms — Memoria-invented word for something OpenAlex already names

| Memoria's term | OpenAlex's term | Note |
|---|---|---|
| `venue` (concept_type, never populated) | **Source** | The correct disambiguating move, blocked only because "Source" is taken (see below) |
| `organization` (concept_type) | **Institution** | `integrity.py`'s own mapping already treats these as equivalent |
| `person` (concept_type) | **Author** | Reasonable, generic synonym — lowest-severity of the set |
| `research_area` | (seeded from) **Topic**/topics | **Deliberate, self-aware decoupling** per design-history — not an oversight, a documented choice to keep a small human-curated facet instead of OpenAlex's ~4,500-term machine hierarchy |
| `published_in` (historical edge name) | Work → **Source** (`primary_location.source`) | Retired/entangled with the source/venue mess above |

## The central tension this audit surfaces

**"Adopt OpenAlex's terms completely" and "never reuse a term for a different meaning"
are in direct conflict for exactly one word: `Source`.** Memoria cannot call the
venue-entity "Source" without recreating the collision this audit exists to eliminate,
*because* Memoria's own, deeply embedded sense of "source" (a captured document) already
owns that word throughout the product — schema, folder names, docs, design-history. The
only way to free "Source" for its correct OpenAlex meaning is to first rename Memoria's
document-sense of "source" to something else.

**That something else is already available: `Work`.** G0 (§5) deletes the markdown
`work` Concept type as a redundant SSOT; deleting it frees the word "work" at exactly
the layer that needs it. Renaming `concept_type='source'` → `'work'` (the catalog row
that alpha.16's own operation manifests *already call* "Work" in prose —
`capture-source.md`, `update-work.md` "Update one SQLite catalog **Work** row" — while
the code says `'source'`) closes the gap between what the docs already say and what the
schema names, using a word OpenAlex already owns for exactly this meaning. Once that
move is made, `Source` is free, and Memoria can choose either to adopt it outright
(rename `venue` → `source`, `relation_type='source'` keeps its current, already-correct
meaning) or keep `venue` as a plainer synonym — a real judgment call, not something to
decide silently; see the rename table below for both options.

## Structural finding, distinct from naming: the entity vocabulary is declared but dead

`person`/`organization`/`venue` are schema-declared `concept_type` values, with a
`catalog/entities/{owner_type}-{id}.md` naming convention reserved for them
(`integrity.py:720-721`) and the Rosetta-stone mapping above proving real design intent
— but **no runtime writer path ever creates a `concepts` row of any of these three
types** (confirmed by grep: the only hit is a one-off test fixture in
`seeded_errors.py:481`, which uses `"type": "entity"` — not even a value in the
`concept_type` CHECK list, and not a recognized type in any `.memoria/schemas/types/
*.yaml`). This connects directly to **G2** (§5): it's the same "declared-but-unwired"
pattern as the 9 concept types with no schema/writer, just for a different subset of
the same list. Resolve alongside G2, not separately: either wire up a real writer for
these entity types (matching the two-graph model's stated ambition), or drop them from
the CHECK until they are.

## Rename plan

Zero-migration-cost (per the standing project-stage rule in §5) — every rename below
ships directly, no phased aliasing.

| Current | Issue | Recommended rename | Depends on |
|---|---|---|---|
| `concept_type='source'` (catalog row, DB) | Means "document" where OpenAlex's Source means "venue"; docs already call this row "Work" | → `'work'` | G0 deleting the markdown `work` type first (frees the name) |
| `source-note` type, `sources/` folder | Same document-sense collision, at the markdown layer | Dissolves — folds into `note` `mode: work` per G0-continued (§5); no folder/type survives to rename | G0-continued |
| `work_graph_edges.relation_type='source'` | Already means venue (correct!), but shares a word with the above | Rename to `'venue'` once `concept_type='source'` is renamed away, **or** leave as `'source'` and adopt OpenAlex's own word fully once the document-sense is gone — pick one, don't leave both spellings live | The `concept_type` rename above |
| `concept_type='organization'` | Synonym for OpenAlex's Institution | → `'institution'` (matches `relation_type='institution'`, already correct) | none — safe now |
| `concept_type='person'` | Synonym for OpenAlex's Author | → `'author'` | none — safe now |
| `relation_type='authorship'` | Only half the object (author, not institutions) | Keep the name (it's correct); either fold `institution` edges into a richer `authorship` payload matching OpenAlex's real object, or explicitly document that Memoria splits it into two edges by design | Judgment call, not a rename |
| `source-note.topic` (singular, unchecked) vs `note.topics` (plural, checked) | Same idea, two names/behaviors | Reconcile to one — likely `topics`, carried over when source-note folds into `note` | G0-continued |
| `work_graph_edges.relation_type='topic'` merging 4 taxonomies | Information loss, not just naming | Split into distinct edge types (e.g. `topic`, `mesh`, `sdg`; decide whether the deprecated OpenAlex Concepts taxonomy is worth its own bucket or should be dropped since OpenAlex itself no longer maintains it) | Independent of the type-roster changes above |

## What's already correct — leave alone

- `work`/`work_id`/`works/` at the markdown-and-catalog-pointer level (the FK usage,
  not the now-redundant markdown Concept type) — clean, consistent match to OpenAlex Work.
- `providers.yaml`'s OpenAlex block — correct endpoint, correct API usage, the ground
  truth the rest of this audit checks against.
- Namespace strings `"openalex"`, `"orcid"`, `"ror"`, `"doi"`, `"semanticscholar"` in
  `external_ids`/`identifiers_json`.
- Field names lifted straight from OpenAlex responses: `primary_location`,
  `best_oa_location`, `locations`, `is_oa`, `open_access`, `referenced_works`,
  `related_works`, `authorships`, `institutions`, `keywords`, `primary_topic`.
- `relation_type='keyword'` — correct, 1:1 with OpenAlex's `keywords` field.
- `research_area` — a deliberate, documented decoupling from OpenAlex Topics, not an
  error; don't "fix" this one, just make sure it's *named* as deliberate wherever the
  vocabulary is documented (it already is, in `system/vocabulary.md`).
- The Domain>Field>Subfield>Topic hierarchy is **correctly not reproduced** in Memoria's
  vocabulary — `system/vocabulary.md` explicitly parks OpenAlex's raw taxonomies in a
  separate `_enrichment` namespace rather than competing with `research_area`. Leave
  this boundary exactly where it is.

---

# Part 4 — Projected on-disk structure, all recommendations applied

> Synthesis of Parts 1–3. Two items below are **open questions this analysis raised but
> never settled** (digest's Concept-hood; whether to wire up or drop the entity types) —
> marked inline rather than silently resolved one way.

## Vault root

```text
<vault>/
├── index.md                 real progressive index (not the current static 5-line
│                             manifest — must actually enumerate the corpus; §2)
├── home.md                  + `type: system` (already has *some* frontmatter today —
│                             `created`/`updated`/`cssclasses` — just no `type:`; §3.1
│                             correction: every .md file besides index.md is already an
│                             OKF concept document, this is what makes it conformant)
├── steering.md               + `type: system` — checked: currently **no** frontmatter
│                             block at all, not just missing `type:`
├── AGENTS.md / AGENTS.override.md   + `type: system` — same, no frontmatter today
├── _nav.md                  + `type: system`, same reason — its "Places" list also
│                             shrinks (no sources/)
├── troubleshooting.md       + `type: system`, same reason
├── bibliography.bib         THE portable knowledge artifact (§1 rule 3) — renderer
│                             extended to emit `memoria_work_id` on every entry
├── notes/<id>.md            note Concepts — mode: [claim, question, hypothesis,
│                             tension, definition, work]. `mode: work` absorbs what
│                             source-note used to be (G0-continued); filenames are
│                             `<ulid>.md` (identity fork resolved, §2), readable via
│                             Obsidian's "Show inline title" off + the template's own
│                             `# {{title}}`
├── hubs/<id>.md              unchanged shape
├── projects/<slug>/
│   ├── project.md            unchanged (Concept)
│   ├── outline.md            **correction, checked against real code**: this analysis
│   │                         previously listed `evidence.md`/`gaps.md` here — neither
│   │                         exists. `outline.md` is real (`_project_outline_rel`,
│   │                         `knowledge.py`), written by `write-project-slice`:
│   │                         BM25-ranked checked notes in argument order. Per the §3.1
│   │                         correction above, it's a `.md` file inside the export unit
│   │                         → gets `type: outline` (a real, distinct kind — a
│   │                         note-ordering list — but no DB `concepts` row: nothing
│   │                         needs to cite "the outline as a whole" as a stable target)
│   ├── draft.md               real (`_project_draft_rel`), written by
│   │                         `compose-project-draft`: composed prose from the outline,
│   │                         carrying `%%ev%%` evidence markers that cite *into*
│   │                         checked notes/`fulltext/` (the direction runs draft →
│   │                         evidence, not the reverse — draft.md is never itself an
│   │                         evidence-marker *target*). `verify-project-draft` checks
│   │                         those markers resolve; `promote-draft-passage` extracts a
│   │                         passage back out into a new unchecked note. → `type: draft`
│   │                         under the same §3.1 logic, same no-DB-row reasoning as
│   │                         `outline.md`.
│   └── argument.canvas        real (`render-project-argument-canvas` →
│                             `_project_canvas_rel`), an Obsidian **Canvas** file (JSON,
│                             not markdown) rendering the project's argument graph.
│                             Falls outside §3.1's "`.md` files are concept documents"
│                             rule entirely, the same way `bibliography.bib` does — no
│                             `type:` question applies to it at all.
│   There is no persisted "evidence.md" or "gaps.md": argument-health and gap analysis
│   (`analyze-project-argument`, `analyze-gaps`, `integrity-evidence-check`) are
│   query-time reports returned to the caller, not files written into the project
│   folder. The one place gap-analysis *does* write anything to disk is vault-wide
│   discovery-candidate flags (`_write_gap_discovery_candidates`, uncaptured-work
│   suggestions) — unrelated to any single project, and not under `projects/<slug>/`.
├── digests/<work_id>.md      RESOLVED (supersedes the earlier open question): digest
│                             stays a Concept, but with `work_id` itself AS its Concept
│                             ID — no separate ULID. This is the exact point where the
│                             objective catalog fact and the machine-produced knowledge
│                             projection merge at the *identity* level, not just by
│                             reference (contrast `notes/` `mode: work`, which is a
│                             *reference*-level bridge — a separately-identified Concept
│                             that points at `work_id` via a field). Its own bundle root
│                             now, not nested under a leftover `works/` folder.
├── fulltext/<work_id>.md     `type: fulltext` — a real OKF concept document (§3.1
│                             correction: every .md file besides index.md already is
│                             one; this analysis previously miscalled it "plain, not a
│                             Concept," backwards from the spec). Concept ID = `work_id`
│                             itself, same identity pattern as `digests/<work_id>.md` —
│                             siblings, not one being the exception. No filename prefix
│                             needed — the folder name itself disambiguates type, unlike
│                             a shared folder. Same shape and same gap as before: the
│                             content already gets GENERATED at query time by
│                             `search_index.py::_checked_work_documents` (title + compact
│                             citation + full text) but only in-memory for the disposable
│                             BM25 corpus — the fix is to persist that generator's
│                             output, not invent new logic. Still needs `^pNNNN`
│                             block-ref anchors inserted at extraction time, which no
│                             code does yet — persisting as-is is necessary but not
│                             sufficient for evidence-marker resolution. Belongs in the
│                             bundle, not the DB (block-refs only resolve within a real
│                             vault file Obsidian indexes). Raw original bytes (PDF/HTML)
│                             stay in `.memoria/blobs/` — provenance, not knowledge.
│                             **Naming, checked against real precedent, not preference:**
│                             `fulltext` is right — `catalog_sources.text_status`
│                             already uses `'full-text'` (schema.sql CHECK) for exactly
│                             "complete text, not just an abstract," and
│                             `on-disk-layout.md` used the same term originally. `raw`
│                             was rejected — it would collide with the *already*
│                             established meaning of `raw_path`/`raw_hash`/`blobs/.../raw/`
│                             (the original unprocessed bytes), the same
│                             same-word-different-meaning anti-pattern the OpenAlex/OKF
│                             audits exist to catch. `extract` was rejected — as a noun
│                             it connotes a partial excerpt, the opposite of "the
│                             complete, citable-at-any-span text" this file promises.
│                             One loose end: the DB enum spells it `full-text` (hyphenated),
│                             the folder is `fulltext` (no separator) — cosmetic, but
│                             worth naming so it doesn't read as accidental drift later.
├── works/                    GONE — nothing left to hold once digest and fulltext each
│                             get their own folder (`record.md` was already confirmed
│                             dead code; deleting the `work` Concept type per G0 removed
│                             the last other reason for this folder to exist)
├── sources/                  GONE — folded into notes/ via `mode: work` (G0-continued)
├── inbox/                    unchanged (transient, not Concepts)
└── system/                   folder structure unchanged (vocabulary, templates, eval,
                              dashboards, logs, metrics, incidents). Checked each real
                              file directly (not assumed): `vocabulary.md`,
                              `patterns/_preamble.md`, and every `dashboards/*.md` ship
                              with **no frontmatter block at all today** — not just
                              missing `type:`. `eval/*.md` gold-task fixtures are the one
                              exception — they **already** carry `type: eval-task` (plus
                              `lifecycle`/`workflow`/`eval_role`/`references`,
                              undeclared-but-conventional) and the folder's own
                              `README.md` already documents "`eval-task` is not a
                              checked Concept type, no schema under
                              `.memoria/schemas/types/`" — this repo independently
                              arrived at the OKF-document-vs-Memoria-Concept-hood split
                              this analysis derived, before this analysis existed.
                              Resolution: add `type: system` to `vocabulary.md`/
                              `patterns/_preamble.md`/`eval/README.md`; add
                              `type: dashboard` to `dashboards/*.md`.
                              **`templates/{note,hub,project}.md` excluded from this
                              fix — corrected below**, they already carry a load-bearing
                              `type: note`/`hub`/`project` (the literal value the
                              templating mechanism stamps onto every new file) that
                              must not be overwritten to `template`; see the
                              correction in the copy-paste-export section above.
                              None of these
                              values are added to `concepts.concept_type` — OKF
                              concept-document-hood (mechanical, per §3.1) and Memoria's
                              own DB-tracked Concept-hood are different questions; these
                              satisfy only the former. Reserved-heading templates
                              (`# Schema`/`# Examples`/`# Citations`) remain a
                              nice-to-have per the real OKF spec (optional, not
                              required), not a compliance blocker.
```

**Three categories, further corrected — narrower than the previous pass had it.** The
§3.1 correction above (every `.md` file except `index.md`/`log.md` is *already* an OKF
concept document, `type:` just makes it a conformant one) collapses most of what the
previous pass treated as "outside the Concept question" into category 1. Once `type:`
is added everywhere per the resolution above, the accurate three-way split is:

1. **OKF concept documents** (every `.md` file except `index.md`, once `type:` is
   added): `notes/`, `hubs/`, `projects/`, `digests/`, `fulltext/` — and now also every
   root-level doc and everything under `system/`. This is a much larger set than "the
   four knowledge-bearing bundle roots" the previous pass drew the line at; OKF's
   classification doesn't distinguish "content the PI reasons about" from "operator
   documentation and machine-generated dashboards" — both are concept documents to a
   permissive consumer, differentiated only by `type:` value, most of which fall to
   `system`/`template`/`eval-task`/`dashboard` rather than anything Memoria tracks
   internally.
2. **OKF-reserved, non-Concept file**: `index.md` only — the one filename the spec
   itself assigns "defined meaning" to independent of the Concept/`type:` mechanism
   (§3.1). `log.md` is the other reserved name; Memoria doesn't use it.
3. **Outside the `.md` classification entirely**: `bibliography.bib` — not markdown, so
   §3.1's rule doesn't reach it at all; it's the one real Memoria-specific addition OKF
   says nothing about either way.

The **export unit** is unchanged from before: vault root minus `.memoria/`. What's
changed is how much of that unit is *classified* as OKF concept documents once `type:`
is added — nearly all of it, `index.md` and `bibliography.bib` being the only two
exceptions. A literal file-explorer copy of that set is the OKF export once the
additive fixes ship, and categories 1 and 2 together now cover almost everything that
travels — category 3 (`bibliography.bib` alone) is the only piece whose usefulness to
Memoria and the PI doesn't also make an OKF-compliance claim.

## `.memoria/` (runtime layer)

```text
.memoria/
├── schemas/
│   ├── types/
│   │   ├── note.yaml          expanded enums.mode; absorbs former source-note fields
│   │   │                     (work_id optional+lint-enforced-when-mode:work; topic/
│   │   │                     topics naming reconciled to one); evidence_set field
│   │   │                     removed (G4); closed validation, `x:` hatch kept (G1)
│   │   ├── hub.yaml            unchanged shape; closed validation
│   │   ├── project.yaml        unchanged shape; closed validation
│   │   └── digest.yaml         present — resolved: digest stays a Concept
│   │                         (`work_id` as its own Concept ID; Part 4)
│   ├── work.yaml               DELETED (G0)
│   ├── source-note.yaml        DELETED (G0-continued, folded into note.yaml)
│   ├── folders.yaml            categories/bundle_roots shrink to match; `homes` drops
│   │                         work/source-note entries
│   └── calibration.yaml        unchanged
├── config/providers.yaml       unchanged — **correction: this whole bucket is less
│                              uniform than "pure internal machinery" implied.**
│                              Checked `vault-template/.gitignore` directly: `config/`
│                              and `schemas/` *are* gitignored — but only once a vault
│                              is a live, deployed instance (its own git repo). Inside
│                              *this* repo, `vault-template/.memoria/{config,schemas}/`
│                              are tracked seed content (a fresh install needs
│                              something to copy) — not a contradiction, just two
│                              different repos with different rules for the same path
├── memoria.sqlite               schema rewritten directly to final shape (G3 — no
│                              `_migrate_v4_to_v5`, no ALTER ladder needed pre-install)
├── journal-head                 **a file, not a folder** — a single-line anchor
│                              (`state.py::write_journal_head_anchor`, `"GENESIS"` if
│                              none) recording the SQLite journal position the last
│                              commit corresponds to. The *only* DB-adjacent thing
│                              that's actually git-committed (`trusted_writer.py`:
│                              "commit only writer-touched files plus the SQLite
│                              journal-head anchor") — `memoria.sqlite` itself never is.
│                              Note: the fuller per-event `journal/*.jsonl` content
│                              this anchors against lives at **vault root, not here**
│                              (`vault/journal/`, a sibling to `.memoria/` — easy to
│                              assume it's nested underneath and it isn't) and is
│                              itself gitignored
├── design-system.md            **missing from this tree in an earlier pass —
│                              genuinely tracked, hand-relevant content, not runtime
│                              state.** The vault's visual-style source (colors,
│                              type scale, spacing, voice, brand) — read by CSS-snippet
│                              generators, Pandoc export configs, and open-design.
│                              PI-edited when the brand evolves; not disposable, not
│                              regenerated, not gitignored (checked directly)
├── plugins/memoria-policy-gate/  real, tracked, functional — not placeholder
│                              scaffolding. Routes external-adapter tool calls through
│                              Memoria's policy gate (`pre_tool_call`/`post_tool_call`
│                              hooks, fail-closed); the standalone CLI is the baseline
│                              write path regardless
├── scripts/cron-runner.sh       **also missing from this tree in an earlier pass.**
│                              Shared dispatcher for the four scheduled jobs (worker
│                              scan/drain, lint, eval, retraction-refresh) — real,
│                              tracked, load-bearing for anyone running Memoria on a
│                              cron
├── blobs/
│   ├── provider-payloads/       unchanged
│   └── source-content/          unchanged — still holds the RAW bytes; fulltext.md
│                              above is the new addressable projection of this
├── index/search/, staging/, quarantine/, state/, audit/
│                              gitignored runtime/disposable state, confirmed against
│                              `.gitignore` directly — this part of the original claim
│                              holds: pure Memoria-internal machinery, zero portability
├── .venv/, locks/, queue/, data/
│                              **not previously listed at all** — gitignored,
│                              per-machine or regenerable (`.venv` — MCP server deps;
│                              `locks/` — runtime locking; `queue/` — alpha.12 worker
│                              holding areas; `data/` — downloaded reference datasets
│                              like the Retraction Watch CSV, refreshed on a cron).
│                              No tracked `.gitkeep` skeleton for these — created
│                              purely at runtime, unlike `staging/`/`quarantine/`/etc.
```

**Net correction:** `.memoria/` is not uniformly "internal machinery, zero
portability" — `design-system.md`, `plugins/`, `scripts/`, and `journal-head` are real,
tracked, either PI-relevant or load-bearing-for-operation content; `config/`, `schemas/`
(once deployed), `memoria.sqlite`, `blobs/`, `index/`, `staging/`, `quarantine/`,
`state/`, `audit/`, `.venv/`, `locks/`, `queue/`, `data/` are the actually-disposable,
gitignored-in-a-live-vault part. Worth the distinction since "explain `.memoria/`" and
"what's `.memoria/`'s portability status" turn out to have different answers per file,
not one blanket answer.

## Database `concept_type` roster (schema.sql)

| Before (15 values) | After | Why |
|---|---|---|
| `work` (markdown type) | **deleted** | G0 — redundant SSOT |
| `source` (catalog/document row) | → **`work`** | frees the name for the catalog row the docs already call "Work"; resolves the internal `source`/`source` self-collision (Part 3) |
| `source-note` | **deleted** | folds into `note` + `mode: work` |
| `venue` | → **`source`** | now free (old `source` moved to `work`) — lets Memoria adopt OpenAlex's actual word for the venue entity, fully resolving Part 3's central tension |
| `organization` | → **`institution`** | matches OpenAlex's real entity name; also matches the already-correct `relation_type='institution'` |
| `person` | → **`author`** | matches OpenAlex's real entity name |
| `digest`, `note`, `hub`, `project` | unchanged | digest resolved: stays a Concept |
| `capability`, `operation`, `skill`, `adapter`, `workflow` | unchanged | product/system registry, separate population, not research content |

Net: **12–13 values** (depending on `digest`), down from 15, with the internal
self-collision gone and full OpenAlex alignment on every entity name. `person`/
`organization`(→`institution`)/`venue`(→`source`) remain **unwired** (no writer ever
creates these rows — the "declared but dead" finding, G2) unless the open question on
building the `catalog/entities/*.md` writer path is resolved toward "build it" rather
than "drop it" — this analysis surfaced the choice but didn't make it.

## What's explicitly still open, not decided here

1. ~~`digest.md`'s Concept-hood~~ — **resolved**: stays a Concept, identified by
   `work_id` itself (no separate ULID), living at `digests/<work_id>.md`.
2. ~~`person`/`institution`/`source` entity types~~ — **resolved below**: neither
   "build the full entity-resolution system" nor "drop entirely" — join on the raw ID
   already captured, drop the CHECK values, defer the rest until a real trigger.

## Rethink: `person`/`institution`/`source` entity resolution

Scoped rethink of open item 2 above, run through the full requirements → prior art →
design → trade-offs → gap sequence, per this analysis's own discipline (ADRs and
Memoria's existing code are gap-measurement, never justification, per the standing
rule).

### Requirements, derived fresh

For a single-PI, small-corpus (hundreds–low-thousands of works) literature synthesis
tool, four distinct needs, none of which require inventing entity-resolution machinery
from scratch:

1. **Cross-paper recognition** — the same author/institution/venue, seen across
   multiple captured works, should be recognizable as *the same thing*, not silently
   split into look-alikes ("J. Smith" vs "John A. Smith").
2. **Venue/institution context** — knowing a work's venue or an author's institution
   helps the PI judge relevance and quality; this is a read need (surface it), not a
   write need (no requirement for the PI to *author* content about a venue).
3. **Gap-discovery via entity traversal** — the stated-but-unbuilt ambition from the
   prior exchange: extend the existing citation-graph coverage-discovery
   (`analyze_gaps`, currently `relation_type IN ('references','related')` only) through
   shared authors/institutions/venues too ("three captured papers by this author, here's
   a fourth you don't have").
4. **Data integrity** — avoid the same real-world entity silently existing as multiple
   `work_graph_edges` targets under name variants, which would quietly break (1) and (3).

None of these four requires an author/institution/venue to be an **addressable link
target in PI prose** — the Concept-hood rule established earlier in this document
("needs Concept-hood iff it can be an addressable link target in the human argument
graph, independent of how it was produced") is not met here. A hub about a research
area can discuss "foundational work by several authors in this space" in free prose
without those authors being clickable Concepts — exactly as `catalog_sources`' raw
bibliographic facts don't need their own Concept type either. This rules out
`store='file'` for these three types before design even starts.

### Prior art

The load-bearing, already-verified fact in this document: **OpenAlex is not just a
possible model to imitate — it is Memoria's own enrichment provider, and it already
does this resolution upstream.** Every OpenAlex Work record ships resolved,
deduplicated IDs for its authors (OpenAlex Author ID, with ORCID when the author has
registered one), its venue (OpenAlex Source ID, ISSN-L-linked), and its institutions
(OpenAlex Institution ID, ROR-linked) — confirmed earlier this session:
`enrichment.py`'s `_openalex_external_ids` already extracts these IDs
(`owner_type="person"`/`"organization"`, `namespace="openalex"`/`"ror"`) as part of the
existing enrichment pipeline. The hard part of entity resolution — disambiguating
author names, merging institutional name variants — is not a problem Memoria needs to
solve; OpenAlex has already solved it, centrally, for every work it enriches. Memoria's
job is narrower: **trust that resolved ID as a stable join key**, not re-derive
disambiguation locally.

For the residual cases without a strong external ID (see coverage boundary below), the
general shape — trust a strong external identifier when one exists, fall back to
calibrated matching with human review only for the genuinely uncertain remainder — is
the standard posture in authority-control and record-linkage systems generally. Rather
than pin specific papers/standards from memory (this document has twice been burned
this session citing remembered specifics that turned out imprecise — OKF's reserved
headings, Obsidian's inline-title scope — until verified against the primary source),
the honest citation here is: **Memoria's own `calibration.yaml` already declares
exactly this fallback policy** (`entity_resolution.confidence_floor: 0.85`, "below the
floor, ingest emits an Inbox near-tie flag instead of merging"). That's real,
already-verified, in-repo prior art for the fallback tier — it just isn't wired to any
actual entity table yet.

### Clean-slate design

**The correction, stated plainly:** current intent (per `integrity.py:687`'s framing)
poses record-linkage as *candidate-detection-for-PI-review by default*. That's
backwards. For the OpenAlex-enriched majority of captured works, entity resolution
should be **deterministic and silent** — matching on a strong external ID needs no
review, any more than matching two rows on a primary key does.

But a second look narrows the build further than the correction alone suggests.
Requirements 1 and 3 (cross-paper recognition, gap-discovery) don't need a dedicated
entity *table* — they need a stable join key, and `work_graph_edges.target_id`
**already is one** for every OpenAlex-enriched work: it already holds the raw OpenAlex
Author/Institution/Source ID. Two rows with `relation_type='authorship'` and the same
`target_id` are, by construction, the same author — no new table, no mirror-on-create
wiring, no verdict lifecycle required to get that join. **The decision: take this path,
not the fuller build.**

What the fuller design (a dedicated `catalog_entities` table, mirrored into
`concepts`/`concept_verdicts`, with a calibrated Tier-2 fallback for works with no
strong ID) would add *on top of* the free join is narrower than it first looks:

- a human-readable `display_name` (without it, callers fall back to `target_title`/
  `raw_json` — a minor lookup cost, not a blocked requirement),
- record-linkage/dedup and a review flow for the minority of works with **no** strong
  ID (requirement 4) — real value, but for a need nobody has hit yet: no duplicate-
  entity complaint, no request for a "papers by this author" view exists anywhere in
  this document or the codebase.

That second piece is genuine infrastructure — a new table, mirror-on-create wiring
into the existing `concepts`/`concept_verdicts` registry (reusing
`_upsert_concept_mirror_conn`'s pattern), and the already-declared
`calibration.yaml`/`confidence_floor` fallback finally wired to a real merge action.
It would not be wasted work if built — it's a correct design, and if built, `entity_id`
should be the OpenAlex ID (ORCID/ROR/ISSN-L as supplementary fields, not the primary
key, since ORCID coverage among OpenAlex author records is still sparse). But it's
speculative *today*: build it when a concrete trigger shows up (a real duplicate, a
real request to browse by entity), not preemptively.

**Decision:**

1. Extend `analyze_gaps` (`knowledge.py`) to traverse `work_graph_edges` by raw
   `target_id` for `relation_type IN ('authorship','institution','source')`, alongside
   the existing `references`/`related` queries — zero new schema, delivers requirements
   1 and 3 for the entire OpenAlex-enriched majority of the corpus today.
2. **Drop** `person`/`organization`/`venue` from `concepts.concept_type` entirely.
   They've had zero writers since the schema was declared (the "declared but dead"
   finding, G2) and this leaner design gives them no job to do — no Concept-hood, no
   `store='db'` row, nothing to mirror.
3. **Retire** `integrity.py`'s `catalog/entities/{owner_type}-{owner_id}.md` path
   builder (line ~721) and its `{"authorship":"person","institution":"organization",
   "source":"venue"}` rosetta dict as dead scaffolding — both were building toward the
   fuller entity table this analysis is explicitly deferring. Zero migration cost, so
   delete outright rather than deprecate.
4. Leave the fuller `catalog_entities` design above **on the shelf, specified but not
   built**, until dedup or entity-browsing becomes a real, hit need.

### Trade-offs

- **Coverage boundary, named explicitly**: the free join only recognizes the same
  entity across works when both have a strong OpenAlex ID. A work captured via bare
  BibTeX import with no DOI, or with `catalog_sources.provider_coverage` at
  `'partial'`/`'degraded'`, has no ID to join on and is simply invisible to this
  traversal — not flagged, not queued for review, just not found. For a mostly-DOI'd
  corpus this misses a minority of works, but it's a silent miss, not a handled
  fallback — worth naming so it isn't mistaken for complete coverage.
- **Gives up, deliberately, for now**: dedup/record-linkage (requirement 4) and any
  "browse by author/institution/venue" view. Both require the fuller design (a real
  entity table + verdict lifecycle) that this decision defers. If either becomes a real
  need, the fuller design above is already specified, not re-derived from scratch.
- **Gives up, permanently**: a bespoke local disambiguation model — never worth
  building, since OpenAlex already resolves this upstream for every enriched work.
- Consistent with the earlier-established survivability boundary: this data was never
  going to be part of the copy-paste export anyway (it's Memoria-internal gap-discovery
  machinery, not knowledge the PI needs to survive Memoria's death) — dropping the
  Concept types changes nothing about that boundary.

### Migration sketch (zero-cost, ships in full — standing rule)

1. Extend `analyze_gaps` (`knowledge.py`) to traverse `work_graph_edges` by raw
   `target_id` for `relation_type IN ('authorship','institution','source')`, alongside
   the existing `references`/`related` queries.
2. Drop `person`/`organization`/`venue` from `concepts.concept_type`'s CHECK.
3. Delete `integrity.py`'s `catalog/entities/*.md` path builder and its rosetta dict.
4. Apply the `venue`→`source` relation-type/terminology alignment from the earlier
   rename table (§ rename table above) in the same pass — no reason to sequence it
   separately.
5. Leave the fuller `catalog_entities` design (this section, "Clean-slate design")
   as a specified-but-unbuilt option for whenever dedup or entity-browsing becomes a
   real, hit need — don't re-derive it later, just build it.

---

# Part 5 — Rethink: required/optional frontmatter and body structure, per concept type

Full requirements → prior art → design → trade-offs → gap sequence, scoped to the
question as asked: for each concept type, what's required vs. optional in
**frontmatter**, and what's the recommended **structural markdown** shape of the
**body**. Builds on, and corrects in places, Part 1 §5/§6.

## The headline finding, stated before anything else

"Required and optional" is the validator's own vocabulary, and the validator
(`schema.py::validate_frontmatter`) checks **frontmatter only** — confirmed again this
pass, not assumed. Body structure is a different kind of thing entirely: OKF's own
§4.2 makes reserved headings SHOULD-not-MUST, Memoria's shipped templates are minimal
(`# {{title}}` + free body, no hardcoded sections — reconfirmed this pass), and the
one body-touching check this document has proposed anywhere (the Links-section ↔
frontmatter-`links:` correspondence check, Part 1 §2) is a **proposal, not yet built** —
grepped `subsystems/integrity/linter/detectors.py` this pass; it doesn't exist. So the
honest, first-principles answer is:

**Required/optional lives in frontmatter, machine-validated. Body structure stays
recommended convention, not enforced schema, per type — with enforcement earned only
where a check is decidable and worth its cost, never invented as generic scaffolding.**

Deriving a mandatory `## Warrant` / `## Rebuttal` / `## Framing` heading set per
type/mode would be building exactly the speculative enforcement machinery this
document's own standing rules (and OKF's own SHOULD-not-MUST stance) argue against.
That's not what follows from first principles here — it's what a naive reading of
"required and optional" would tempt into existing regardless of principles.

## Prior art, and which of it is load-bearing vs. color

**Load-bearing (verified this session, anchors real requirements):**
- OKF §4.1 — `type` is the only required frontmatter field; `title`/`description`/
  `resource`/`tags`/`timestamp` are recommended, not required. §4.2 — no required body
  sections; `# Schema`/`# Examples`/`# Citations` are conventional SHOULD.
- The real, current `.memoria/schemas/types/*.yaml` and shipped templates (re-read this
  pass) — the actual baseline to measure every proposal against.
- Karpathy's wiki-LLM digest pattern (fetched earlier this session) — a digest is a
  compressed, kept-current summary of one immutable source; it directly shapes
  `digest`'s body recommendation below.
- This document's own already-adopted Zettelkasten lineage (cited earlier for the
  project/corpus split) — atomic, one-idea, densely-linked notes. This system already
  *is* in that lineage; it's not a new import.

**Color, not a source of any required field (per the correction below on Toulmin):**
- Toulmin's claim/grounds/warrant/qualifier/rebuttal model — a recognized
  argumentation framework, useful as a **prose checklist** for what a `claim` note's
  free-form content should *cover*, never as a mandate for separate `## Warrant`/
  `## Rebuttal` headings. Cited for what it is (a well-known named framework), not for
  precise internals I haven't verified against a primary source this session — the
  discipline this document adopted after being burned twice on exactly that.
- IMRaD — relevant only to how a `digest` of an empirical paper *might* read, not a
  requirement for every captured work (a captured blog post or a spec doesn't have
  Methods/Results).

**A real tension, resolved rather than left implicit:** Toulmin pulls toward more body
structure; Zettelkasten pulls toward atomic prose. This system already committed to
Zettelkasten's lineage, so atomicity wins where they conflict — Toulmin informs
*content* (does this claim note state its grounds, its qualifier), never *schema*.

## Design: frontmatter, per type

Universal required core, unchanged and re-confirmed: `type` (literal), `id` (ulid),
`title` (str), `tags` (list), `links` (links) — on every type below.

### `note` — first, a mode-collapse finding, not just a field table

The proposal earlier in this document (G0-continued) carried six modes: `claim`,
`question`, `hypothesis`, `tension`, `definition`, `work`. Applying ADR-126's own
mode-vs-type test properly — "is this a flippable *state* on the same underlying
content, or a genuinely different kind of thing" — two of the six don't survive:

- **`hypothesis` collapses into `claim` + `certainty`.** A hypothesis *is* a claim whose
  confidence hasn't resolved yet — exactly the flippable-state case the mode/type test
  exists to catch. It needs no new mode. It needs one new `certainty` enum value:
  `reported, contested, unknown` → add **`hypothesized`** (an explicit "proposed,
  awaiting evidence" state, distinct from `unknown`, which reads more like "not yet
  assessed" than "deliberately provisional"). One enum value, not a mode, not a schema.
- **`tension` collapses into `claim` + `links.contradicts`.** The `links` field already
  has a `contradicts` relation. A tension note's actual content — "I've noticed X and Y
  disagree, and here's why that matters" — is itself a claim (about a relationship
  between two other notes), fully expressible as `mode: claim`, `claim_text` stating
  the tension, `links: {contradicts: [X, Y]}`. No new mode, no new field.
- **`question` and `definition` and `work` survive** — each is a genuinely different
  kind of epistemic move (interrogative vs. assertive vs. terminological-convention vs.
  source-bridging), not a state change on the same content.

**Net: 4 real modes, not 6 — `claim`, `question`, `definition`, `work`.** This is a
simplification this document's own earlier pass didn't catch; running the mode-vs-type
test rigorously against all six, rather than accepting the proposal once made, is what
this rethink pass adds.

| Field | Real today? | Required when | Notes |
|---|---|---|---|
| `mode` | yes (enum currently `[claim, question]` only) | optional | extend enum to `[claim, question, definition, work]`; `work` replaces `source-note` as a type (G0-continued) |
| `claim_text` | yes (optional today) | **conditionally required** when `mode: claim` (and covers `hypothesis` via `certainty`, per above) | the atomic assertion itself |
| `certainty` | yes | optional | add `hypothesized` value |
| `question_status` | yes | **conditionally required** when `mode: question` | open/resolved |
| `work_id` | yes, on `source-note` today | **conditionally required** when `mode: work` (migrating from `source-note`'s current unconditional-required) | |
| `citekey`, `project` (list) | on `source-note` today | **drop, don't carry forward** | `citekey` duplicates `bibliography.bib` (G0 already resolved catalog data to be catalog-only); `project` duplicates what a project's own `links`/backlinks already surface — carrying both is the same survival-copy mistake G0 fixed elsewhere |
| `topics` vs `topic` | both exist today, unreconciled (note vs. source-note) | optional | reconcile to one name (`topics`, vocab-checked) — the wrinkle this document already flagged, not new |
| `quote`, `source_id`, `temporal_scope`, `tense`, `qualifier`, `evidence_set`, `anchors`, `annotation_ref`, `extraction_confidence`, `reading`, `superseded`, `aliases`, `archived`, `description`, `citations`, `x` | yes | optional | unchanged from current schema |

**Conditional-required, resolved:** neither of the two mechanisms this document
previously left open (a new schema primitive vs. linter-level enforcement) has a real
precedent to lean on — grepped for `question_status`/`claim_text` conditional
enforcement in the runtime this pass and found **none**; the earlier "already enforced
by convention" framing was itself unverified and turns out wrong. Correct principle,
derived fresh: **a check belongs in the frontmatter validator if it's decidable from
frontmatter alone; it belongs in the linter if it needs the body too.**
Mode-conditional-required (`claim`→`claim_text`, `question`→`question_status`,
`work`→`work_id`) is decidable from frontmatter alone → **add a `required_when`
schema primitive**, not a linter detector. (`required_any`, the one dormant primitive
schema.py already has, doesn't fit — it's disjunctive-across-fields, not
conditional-on-a-value; it wouldn't solve this even if wired up.) The
Links-section-correspondence check, by contrast, inherently needs frontmatter *and*
body → correctly a linter detector, and correctly still unbuilt, not miscategorized as
already-existing.

### `hub`

| Field | Required? | Notes |
|---|---|---|
| `tag` | required (unchanged — the one canonical tag this hub pages for) | |
| `salience`, `aliases`, `citations`, `description`, `archived`, `x` | optional (unchanged) | |

No changes derived — the current shape already matches what a hub needs to do
(page one tag, optionally aliased/salient).

### `project`

| Field | Required? | Notes |
|---|---|---|
| `thesis` | **stays optional, deliberately** | a project has a lifecycle — exploratory before a thesis crystallizes (real academic-writing practice: the question can precede the thesis); forcing it required would penalize early-stage projects for a state they're honestly in |
| `outcome_frame`, `paper_plan`, `question`, `aliases`, `archived`, `description`, `x` | optional (unchanged) | |

No changes derived beyond confirming `thesis` optional is a deliberate design point,
not an oversight.

### `digest`

| Field | Required? | Notes |
|---|---|---|
| `work_id` | required (unchanged) | |
| `anchors`, `evidence_set`, `description`, `citations`, `archived`, `x` | optional (unchanged) | |

No changes derived — machine-owned, smallest optional surface already, matches the
Karpathy pattern's "compressed, regenerable summary" shape.

### `fulltext` (new this pass — added per the §3.1 correction, Part 4)

| Field | Required? | Notes |
|---|---|---|
| `type: fulltext` | required | new — this is what makes it an OKF-conformant concept document |
| universal core (`id`/`title`/`tags`/`links`) | required, same as every type | `links` will typically be empty (`{}`) — a mechanical text reproduction has no PI-authored relationships to declare, but the field stays present for schema uniformity rather than special-cased away |
| everything else | none needed | it's a reproduction, not authored content |

**Body isn't "structural markdown" in the heading sense at all** — its structure is
paragraph-level `^pNNNN` block-ref anchors, not `##` headings. Worth naming explicitly:
this is the one type where the question "what body sections" doesn't really apply.

### Types deliberately out of this table's scope, named rather than dropped silently

- **`person`/`institution`/`source`(venue)** — resolved in the prior exchange to **not
  exist** as concept types at all (dropped from `concepts.concept_type`, no
  frontmatter schema ever existed for them). Nothing to derive.
- **`system`/`template`/`eval-task`/`dashboard`** (Part 4, the §3.1 typing fix) —
  OKF-conformance labels, not DB-tracked types; frontmatter need is `type:` alone (plus
  universal core for uniformity), body is whatever the underlying artifact already is
  (a template's placeholder syntax, an eval fixture's task spec, a dashboard's
  dataviewjs block) — deriving a "required/optional" table for these would be
  over-fitting a research-content question onto non-knowledge plumbing.
- **`capability`/`operation`/`skill`/`adapter`/`workflow`** — real, DB-tracked
  `concept_type` values with real `type:` frontmatter (confirmed this session reading
  `analyze-gaps.md` etc.: `type: operation`, `title`, `description`, `operation_id`,
  `allowed_tools`, `allowed_paths`, `allowed_network`, `prompt_version`,
  optionally `io_schema`). **Named, not silently excluded** — but out of scope for a
  frontmatter/body rethink grounded in research-content requirements: these are
  product/system registry documents (what the system can do), not PI knowledge
  artifacts, and rethinking their shape is a different question than this document has
  been answering throughout (it was scoped to research content from the first
  message). If that rethink is wanted, it's a separate pass, not an extension of this
  one.

## Design: body structure, per type (recommended, not enforced)

Stated once, applies to all: none of the following are schema-checked. They're the
convention this document recommends documenting (in `system/vocabulary.md` or
equivalent), matching OKF's own SHOULD-not-MUST stance on reserved headings.

- **`note`, `mode: claim`**: `## Claim` (the one atomic idea — Zettelkasten atomicity,
  governing), `## Evidence and argument` (grounds — Toulmin as color: does this cover
  what backs the claim, its qualifier, its rebuttal-awareness, without mandating those
  as separate headings), `## Links` (prose naming what the frontmatter `links:` map
  declares — this is the one relationship where a real enforcement case exists, via the
  not-yet-built linter check above).
- **`note`, `mode: question`**: no claim triad — `question_status` carries the state;
  body is the question itself plus whatever framing helps (no enforced shape).
- **`note`, `mode: definition`**: the term (reuse `title`, don't invent a `term:`
  field) plus the definition; optionally a "why this needs pinning down" line where a
  collision motivated it (this document's own OpenAlex audit is full of examples).
- **`note`, `mode: work`**: two-layer authorship, unchanged from Part 1 §6 — machine
  catalog facts vs. PI judgment (`## Critique`/`## Open questions`), now attached to
  `mode: work` instead of a separate `source-note` type.
- **`hub`**: the three-question test already in Part 1 §6 — framing / curating /
  planning — recommended as `# Framing`/`# Curating`/`# Planning` if headings are
  wanted at all; a hub answering only the first two is still valid, just static.
- **`project`**: thesis/direction in free prose; the granular structure lives in the
  sibling artifacts (`outline.md`, `draft.md`, `argument.canvas`), not in `project.md`
  itself (per the prior exchange on project-subfolder contents).
- **`digest`**: lead with the source's core claim/contribution, then supporting detail
  — directly derived from Karpathy's "kept-current summary" framing, not a heading
  schema.
- **`fulltext`**: N/A, as above — anchors, not headings.

## Trade-offs

- **Gives up**: enforced body consistency across notes of the same mode (two `claim`
  notes could structure their evidence completely differently and both validate).
  Accepted — Zettelkasten atomicity and OKF's own SHOULD-not-MUST stance both argue
  this is a feature (freeform prose is easier to write and read) not a gap, and nothing
  in the stated requirements needs machine-parseable body sections. The one place a
  real per-relationship invariant exists (Links section ↔ `links:` map) already has a
  proposed, cheap, targeted fix — that's the right size of enforcement, not a template
  for enforcing everything else too.
- **Costs one real schema-grammar addition** (`required_when`) and **one real enum
  addition** (`certainty: hypothesized`) — both small, both driven by a genuine
  recurring need (three real/soon-real cases), neither speculative.
- **The mode-collapse (6→4) is a real behavior change** if `hypothesis`/`tension` were
  already in active use anywhere — they aren't (both are proposals from earlier in
  this same document, never shipped), so there's no migration cost to weigh, only a
  proposal not to make in the first place.

## Gap to current, and migration sketch (zero-cost, ships in full — standing rule)

1. Add `required_when` to the schema grammar (`schema.py::validate_frontmatter`); wire
   `claim`→`claim_text`, `question`→`question_status`, `work`→`work_id`.
2. Extend `note.yaml`'s `certainty` enum with `hypothesized`; extend `mode` enum to
   `[claim, question, definition, work]` (not six — the collapse above).
3. Delete `source-note.yaml`; fold its surviving fields into `note.yaml` as
   `mode: work` (G0-continued, already planned) — drop `citekey`/`project` per the
   table above rather than carrying them forward unreconciled.
4. Add `fulltext.yaml` (`type: fulltext`, universal core only) alongside materializing
   `fulltext/<work_id>.md` for real (already planned, Part 4).
5. Document (not schema-enforce) the per-type body conventions above in
   `system/vocabulary.md` or wherever body conventions are already documented today.
6. Build the Links-section-correspondence linter detector — proposed earlier in this
   document, still not built; this pass doesn't add new justification for it, just
   confirms it's the one body-touching check that's earned.

---

# Part 6 — What can move from the vault into `.memoria/`

## A load-bearing assumption, checked and found wrong

Every earlier judgment call in this document about "should this stay PI-visible or
move to internal machinery" leaned, implicitly, on an assumption that `.memoria/` (and
dotfolders generally) are hidden from Obsidian's normal file explorer the way
`.git/`-style folders often are elsewhere. **Checked via web search this pass — false.**
Obsidian does not hide dotfolders by default; the existence of a small ecosystem of
community plugins built specifically to hide `.obsidian/`/dotfolders (Explorer Hider,
Hide Folders, File Hider, File Explorer++) — and an Obsidian-forum thread asking "any
way to hide a whole folder?" — is itself the evidence: if core Obsidian already hid
them, that plugin category wouldn't need to exist. So `.memoria/` is fully visible and
browsable in Obsidian by default, same as any other folder — nothing moved there
becomes literally hidden.

The test applied below went through two revisions by direct instruction after this
section was first written — briefly toward "default to `.memoria/` for everything
unless something structurally breaks," then back — landing on the original
human-used-vs-machine-only distinction after all, just now confirmed rather than
merely assumed. See "The governing rule, settled" for the final version and why the
detour mattered.

## Good candidates to move

1. **`system/templates/{note,hub,project}.md` → `.memoria/templates/`.** Nobody reads
   a template for its content — it's `{{VALUE:...}}` placeholder boilerplate, consumed
   only by Obsidian's Templates plugin via its configured template-folder-path setting.
   Checked Obsidian's own docs this pass: that setting accepts a path "anywhere in your
   vault" — nothing suggests it can't point into a dotfolder, and given dotfolders
   aren't specially hidden or blocked (previous section), there's no mechanical reason
   it wouldn't work. **This also elegantly dissolves the `type:` collision found two
   turns ago** — these three files carry a load-bearing `type: note`/`hub`/`project`
   that can't be relabeled `type: template` without breaking the templating mechanism,
   which left a residual, accepted OKF-conformance imprecision (a permissive consumer
   can't distinguish the template from a real note by `type:` alone). Move the folder
   out of the export unit entirely (`.memoria/` is already excluded by definition) and
   the question stops applying — not fixed by relabeling, fixed by removing it from the
   domain the question was ever asked about.
2. **`system/eval/` (gold tasks, `README.md`, `alpha15-seeded-errors.json`) →
   `.memoria/eval/`.** Explicitly diagnostic self-test machinery ("not a benchmark and
   not a gate," per its own README) — the PI doesn't browse these as part of normal
   work. Already handles the `type:`/Concept-hood question correctly on its own
   (`type: eval-task`, explicitly "not a checked Concept type" — Part 4), so this move
   isn't fixing a problem the way the templates move is; it's just better filing
   (diagnostic tooling next to the rest of Memoria's internal machinery, not mixed into
   the same folder as things the PI actually opens).
3. **`system/patterns/_preamble.md` → `.memoria/patterns/_preamble.md`** (or folded
   into `.memoria/config/`). A machine prompt-preamble prepended to every pattern run —
   the same category of thing as `.memoria/config/providers.yaml`, which already lives
   there. Being inside `.memoria/` doesn't block editing it (it's still a plain text
   file); it just files it correctly as configuration, not vault content.

4. **`journal/` (vault root) → `.memoria/journal/`.** A fourth candidate, cleaner than
   the other three — no design tension to weigh, just an inconsistency to fix. It's
   purely machine-written, hash-chained event-sourced state (`journal_events`,
   `state.py`) that the PI never hand-edits, already gitignored (confirmed,
   §"is there anything gitignored outside `.memoria/`" two turns ago), and unlike every
   other Memoria-internal runtime folder (`.memoria/staging/*/`, `state/`,
   `blobs/*/`, `quarantine/`, `index/search/`), it ships **no tracked `.gitkeep`
   skeleton at all** — checked directly, zero hits. Every other piece of pure runtime
   state already nests under `.memoria/`; `journal/` sitting at vault root as a
   sibling looks like it predates that convention rather than deliberately opting out
   of it. Three call sites to update (`trusted_writer.py`, `operations.py`,
   `integrity.py`, all currently `vault / "journal"`), plus swapping the `.gitignore`'s
   standalone `journal/` line for a `.memoria/journal/**` pattern matching its
   siblings' style (with the same `.gitkeep`-preserving negation) — a consolidation
   onto the one existing convention, not a second special case. **What must *not*
   move:** `.memoria/journal-head`, the single-line commit anchor — already correctly
   placed, already the one DB-adjacent thing that *is* committed; only the fuller
   per-event log folder is the candidate here.

**Migration cost for all four: zero, per the standing rule** — pre-install alpha,
update the hardcoded/configured paths (Obsidian's template-folder setting; whatever
reads `system/eval/`; whatever prepends the pattern preamble; the three `journal/`
call sites) in the same pass, no phased rollout.

## The governing rule, settled

Two passes at this, worth showing rather than silently collapsing into one:

1. First pass (this section, originally): keep out whatever the PI actually opens or
   edits as part of their workflow; move whatever only a machine/plugin touches.
2. Then, by instruction: drop that distinction — default to `.memoria/` for
   everything, stay out only where something structurally breaks. Applied that,
   found only 3 of 6 exceptions were structural; reclassified the other 3 as "move."
3. **Then, corrected back, by instruction: human-used files don't belong in
   `.memoria/`, full stop.** Pass 1 had the right test after all — not because
   nothing *breaks* when a human-edited file moves (nothing does; `.memoria/` isn't
   hidden from Obsidian), but because **the folder's purpose is to hold what a human
   doesn't need to touch.** Filing something a PI edits weekly under "the runtime
   layer" is a category error even when it's technically functional — the same kind of
   miscategorization this document has spent this whole exchange correcting elsewhere
   (mislabeling `fulltext.md` as non-Concept, inventing `type: eval-fixture` instead of
   checking the real `eval-task` value). "Nothing breaks" was never sufficient
   justification on its own; it has to be paired with "and nothing human depends on it
   living here."

**Settled rule: machine/plugin-only content → `.memoria/`. Anything a human opens,
edits, or is expected to find without already knowing Memoria's internals → stays
vault-visible**, regardless of whether moving it would technically still work.

**Stays vault-visible (human-used):**

- `system/vocabulary.md` — PI extends it as the corpus grows.
- `system/dashboards/*.md` — PI opens these routinely to check system health.
- `home.md`, `_nav.md` — the PI's navigation entry points.
- `steering.md` — PI-edited weekly, "the main lever you have over what gets surfaced."
- `troubleshooting.md` — for offline recovery; doubly right to keep out, since a copy
  nested inside `.memoria/` would be unreachable exactly when `.memoria/` itself is
  what's broken.
- `AGENTS.md` / `AGENTS.override.md` — human- *and* agent-read, and structurally
  required at repo root regardless (external tool convention).
- `index.md`, `bibliography.bib` — structurally required to be part of the exported
  bundle; `.memoria/` is excluded from the export unit by definition.

**Moves into `.memoria/` (machine/plugin-only, never opened by the PI for its own
sake):**

- `system/templates/{note,hub,project}.md` — Templates-plugin input only.
- `system/eval/` — Memoria's own diagnostic self-test fixtures.
- `system/patterns/_preamble.md` — a machine prompt-preamble.
- `journal/` — pure hash-chained event-sourced state.

## Net

`system/` still empties out — but for a narrower reason than the previous draft of
this section had it: `vocabulary.md` and `dashboards/*.md` **stay at vault root**
(they're human-used), while `templates/`, `eval/`, and `patterns/_preamble.md` move.
Since `system/` becomes `vocabulary.md` + `dashboards/` alone, the folder itself is
still worth keeping — it's no longer emptied out, just thinned to its genuinely
human-facing contents. **Vault root, final:** `index.md`, `AGENTS.md`,
`AGENTS.override.md`, `bibliography.bib`, `troubleshooting.md`, `home.md`, `_nav.md`,
`steering.md`, `system/{vocabulary.md, dashboards/}`, the bundle-root folders
(`notes/`, `hubs/`, `projects/`, `digests/`, `fulltext/`), `inbox/`, and `.memoria/`
itself (now also holding `templates/`, `eval/`, `patterns/_preamble.md`, `journal/`).

---

# Part 7 — Rethink: a first-principles taxonomy for `.memoria/`, `system/`, and root

Full requirements → prior art → design → trade-offs → gap sequence, scoped to the
whole non-bundle layer. Part 6 (the multi-pass exchange that preceded this) is
gap-measurement input here, not the template — but stated up front: **this pass
converges with where Part 6 landed.** That's the honest result, not a hedge. Per
Rethink's own rule — when the current answer already is the first-principles one, say
so rather than inventing a difference — the value of this pass isn't new file moves,
it's a categorical justification precise enough to explain the one class of case
Part 6 handled correctly without ever stating why.

## Requirements, derived fresh

What does the non-bundle layer of a Memoria vault need to do, for whom:

1. **Carry the portable knowledge** (the bundle + `bibliography.bib`) somewhere an
   export can find it, intact, without the rest of the vault.
2. **Give the PI a small set of operational surfaces** — navigation, steering,
   troubleshooting, health dashboards, vocabulary — that support running their own
   research practice day to day, distinct from the knowledge itself.
3. **Let the PI (or an operator) tune Memoria's behavior** — provider config, visual
   brand, calibration thresholds — occasionally, without that tuning being mistaken
   for either knowledge or daily workflow content.
4. **Let Memoria run** — disposable runtime state, caches, queues, an event log —
   that needs to exist on disk but that nothing else depends on surviving.
5. **Satisfy external convention** where one exists (agent tooling expecting
   `AGENTS.md` at repo root; OKF expecting `index.md` at a bundle level) — a hard
   constraint, not a design choice.

Four distinct needs (2–4 are easy to conflate; they aren't the same thing), plus one
hard external-convention constraint that overrides category logic when it applies.

## Prior art

**`.git/`** — the closest, most load-bearing analogy, and worth being precise about
why: it's a single dotfolder holding both pure machine state (`objects/`, `refs/`,
`index`) *and* human-tunable tool configuration (`config`, `hooks/`) that a developer
edits directly, sometimes often. Nobody treats `.git/hooks/pre-commit` as
"human-edited, therefore shouldn't live in a dotfolder" — because it's configuring the
tool, not authoring project content. That's the precedent this pass leans on most.

**`.vscode/settings.json`** — same shape in a different tool: human-edited,
often committed, lives in a dotfolder, uncontroversial. Confirms `.git/` isn't a
one-off special case but a recognized pattern for project-local tool configuration.

**The XDG Base Directory pattern** (freedesktop.org) — cited for the general
separation-by-purpose idea (config vs. data vs. cache vs. state as genuinely different
categories with different survivability expectations), not for its exact directory
names, which aren't verified this pass and aren't what's load-bearing here.

**Already-established this session, load-bearing:** Obsidian does not hide dotfolders
by default (verified via web search, Part 6) — so placement inside `.memoria/` cannot
rest on "hide it from the human," full stop. That single fact is *why* a binary
"human-used vs. machine-only" test was always going to misfire on files like
`design-system.md` — it isn't hidden either way, so "human-used" alone can't be the
sorting key.

## Design: four categories, not two

| Category | Test | Lives |
|---|---|---|
| **1. Portable knowledge** | Must an external OKF consumer, or a PI who's left Memoria entirely, be able to read this? | Vault root / bundle roots — the export unit |
| **2. Operational workflow content** | Does the PI author, extend, or read this *as part of doing their research* (not as tuning the tool)? | Vault root, outside `.memoria/` |
| **3. Tool configuration** | Is a human occasionally tuning *how Memoria behaves*, rather than authoring content or doing research? | `.memoria/` — matches `.git/config`, `.vscode/settings.json` |
| **4. Runtime/machine state** | Does only code read and write this, ever? | `.memoria/`, gitignored |

The category-3/category-2 line is the one that actually needed deriving — everything
else in this table restates constraints already established (category 1 is the
export-unit boundary from Parts 1–4; category 4 is what Part 6 already called
machine-only). **The test for 3 vs. 2: does editing this change what Memoria *does*,
or does it change what the PI *knows/is working on*.** `providers.yaml` changes which
API Memoria calls — category 3. `steering.md` changes what the PI is investigating —
category 2. Both are edited by a human; only one is *content*.

**Per-file placement — this is where the convergence claim gets checked, not assumed:**

| File | Category | Placement | Matches Part 6? |
|---|---|---|---|
| Bundle roots, `bibliography.bib`, `index.md` | 1 | vault root | yes |
| `home.md`, `_nav.md`, `steering.md`, `troubleshooting.md`, `system/vocabulary.md`, `system/dashboards/*.md` | 2 | vault root | yes |
| `.memoria/config/providers.yaml`, `.memoria/design-system.md`, `.memoria/plugins/` | 3 | `.memoria/` | yes — never proposed moving, now explained |
| `.memoria/schemas/`, `.memoria/scripts/`, `system/templates/`, `system/eval/`, `system/patterns/_preamble.md`, `journal/`, DB, blobs, staging, queue, index, locks | 4 | `.memoria/` | yes |
| `AGENTS.md`/`.override.md` | external convention overrides category | vault root | yes |

Every file lands exactly where Part 6 already put it. **The one genuine addition is
category 3 itself** — Part 6 never needed to name it because nobody proposed moving
`design-system.md`/`providers.yaml` out of `.memoria/` in the first place, so the
"human-used" test was already being applied selectively without anyone stating the
exception it was silently making. Naming category 3 makes that exception principled
instead of accidental.

## Trade-offs

- **`design-system.md` is the genuinely borderline case, named rather than forced into
  a crisp bin.** It's edited rarely, and arguably closer to "brand content" than "tool
  config" in feel — but it's read by generators/renderers, never by the PI as research
  material, and changing it doesn't advance any research question. Category 3 fits,
  but it's the one placement in this table that could reasonably go the other way if
  the PI's actual usage pattern turns out to treat it more like `steering.md`.
- **This taxonomy is a tiebreaker for future ambiguous files, not a re-opening of
  anything settled.** Where a file cleanly reads as category 2 or 3, use the test
  above. Where it doesn't cleanly resolve, the user's stated preference — content the
  PI touches stays visible — is what breaks the tie, not a cleverer rule.
- **Gives up** a single unified rule ("human-used" or "can-be-there") in favor of a
  four-way distinction that costs one extra category to hold in mind. Worth it only
  because the two-way version demonstrably misclassified real files (Part 6, pass 2).

## Gap to current, and migration

None beyond what Part 6 already specified — `templates/`, `eval/`,
`patterns/_preamble.md`, and `journal/` move into `.memoria/`; everything else stays
put. This pass changes the *justification*, not the *placement*. No new migration
steps beyond Part 6's.

---

# Part 8 — Schema Deltas for the Query Architecture

`query-mechanism-analysis.md` is a separate, prerequisite pass answering "what is the
best way to query the data" — kept as its own document per the project owner's
direction. This Part is the inversion: given that design, what must the data
*structure itself* — tables, columns, CHECK values, frontmatter fields — become to
make it queryable as designed, **and** what must it become to stop colliding with
OpenAlex's own vocabulary, per a comprehensive collision audit run this session
against the real, current `schema.sql` and all six type YAMLs (not from memory, not
from an earlier pass's assumptions). Every change below traces to a specific
requirement or finding in the query-mechanism document (cited by section), to the real
schema described in this document's own Parts 1–7, or to that OpenAlex audit; nothing
here is speculative beyond what those three sources justify. Where current
implementation is cited, it is for gap-measurement only, per the methodological rule
`query-mechanism-analysis.md` §1 states and that applies identically here — never as
an argument for or against a design choice.

**A naming note, so the sections below can be read in the order requested without
forward-reference confusion:** every table/column/value name used in "The schema
design" is given in its *target* (post-fix) form already — `work_id` rather than
`source_id`, `catalog-record`/`catalog-note` rather than `source`/`source-note`,
`published_in` rather than the bare `source` relation, `event_log` rather than
`journal_events`. The dedicated OpenAlex-collision subsection at the end of that
section supplies the justification and the exact old→new mapping for each; the real,
currently-shipped names appear verbatim only in the Gap/Migration sketch, where the
distinction between old and new is the entire point.

**A reconciliation this Part owes the rest of the document:** Part 3's own earlier
rename plan proposed `concept_type='source'` → `'work'` and
`relation_type='source'` → `'venue'`, contingent on Part 2's clean-slate deletion of
the markdown `work` Concept type first freeing the word "work." This Part does not
carry that precondition forward — it grounds in the real, currently-shipped
`schema.sql`/`work.yaml` (re-read directly this session), where `concept_type='work'`
and a live `work.yaml` schema both already exist and are therefore *not* available to
reuse. The resolution below (`catalog-record`/`catalog-note`, `published_in`) was
independently re-derived against the live files rather than assuming Part 2's
hypothetical deletion had happened, and supersedes Part 3's plan for exactly the
`source`/`source-note`/`work_graph_edges.relation_type='source'` triad. Part 3's other
findings (the `Concept` collision, the `organization`/`institution` duplication, the
merged `topic` edge taxonomy) are untouched by this Part and stand as Part 3 left them.

## Requirements, by pointer

Not re-derived — restated only enough to anchor each schema change below to its
source:

- **One query spanning relevance and structure** — `query-mechanism-analysis.md` Q1,
  §4.3–§4.4 (filter-before-rank, one statement).
- **Tension recordability** — Q0(b), §4.11 (today: no).
- **Evidence-thinness visibility** — §4.12 (a `COUNT`/`GROUP BY` primitive, not an
  algorithm — no new schema of its own; it queries structure already proposed below).
- **Verbatim-context retrieval unit** — Q13, §4.1/§4.14 (the passage, not the fact).
- **Embeddings storage** — Q2, §3 (sqlite-vec `vec0`), §4.1.
- **Freshness tracking, no daemon** — §4.2 (query-time mtime-gated lazy reindex).

## The schema design

### `passages`: new table, reconciled against `work_aspects` and `evidence_sets`

`query-mechanism-analysis.md` §4.1 sketches an illustrative `passages` table and
explicitly defers the real question to here: "Whether it should be a genuinely new
table, or generalize the real, already-existing `work_aspects`/`evidence_sets` tables,
is a schema question resolved in `data-structure-analysis.md` Part 8, not here."
Taking each candidate in turn, not hedging:

**Does `evidence_sets` already serve this role? No — and nothing about it needs to
change.** Its real shape — `id, block_ref, items_json, type, state, review_required,
run_id` — already gives a claim its originating verbatim span, structurally:
`block_ref` is the claim's own location; `items_json` holds one-or-more pointers into
source spans, each in the `work_id#^pNNNN` form `runtime/evidence.py`'s
`SourceSpanRef`/`_SOURCE_SPAN_RE` already parses, or a chained `ev-xxxxxxxx` id for a
multi-hop warrant; `type`/`state`/`review_required` already distinguish
single-span/multi-span/multi-hop/implicit and completeness. This *is* "a claim carries
its originating verbatim span," already built. What it was never built to do is store
or index the text at those pointers — `items_json` is a list of references, never the
referenced text, and `evidence_sets` has no relationship to FTS5 or `vec0`. The gap is
not in `evidence_sets`'s shape; it's that the spans its pointers name were never
themselves an independently retrievable row anywhere. Zero schema change to
`evidence_sets`.

**Should `work_aspects` be generalized beyond its current scope? No — that would
replace it, not generalize it.** Its defining constraint is `aspect_type TEXT NOT NULL
CHECK (aspect_type IN ('context','key_idea','method','outcome','limitation',
'assumption'))` with `PRIMARY KEY (work_id, aspect_type)` — at most six rows per work,
ever, each a named analytical facet. Dropping that CHECK to admit arbitrary passage
rows, and widening scope to any `concept_id` (notes/hubs/projects, not just catalog
works), would not extend `work_aspects` — it would delete the two things that make it
what it is (a bounded vocabulary, a fixed scope) and build a different table under the
old name. The bounded shape is the feature: it is what keeps "every work's `outcome`
facet" a small, clean query today, and generalizing it away would cost that for
nothing `passages` doesn't already deliver on its own. `work_aspects` stays exactly as
it is.

**So: a new table — populated from what already exists, not re-authoring it.**

```sql
CREATE TABLE passages (
    passage_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (
        origin IN ('note-body', 'source-span', 'work-aspect', 'db-mirror')
    ),
    anchor TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
    updated_at TEXT NOT NULL
);
```

Four origins, `origin` distinguishing them (deliberately not the prerequisite
analysis's own illustrative `source_kind` name for this column, §4.1 — reusing that
name here would collide two unrelated things in one document):

- **`note-body`** — markdown body text from `notes/`, `hubs/`, `projects/`, `digests/`
  parsed into passage-sized spans (§4.1's first origin).
- **`source-span`** — the `^pNNNN` page-anchors already written into every catalog
  work's full-text file today (the same anchors `runtime/evidence.py`'s
  `_SOURCE_SPAN_RE` and `runtime/state.py`'s `_source_span_pages` already parse to
  validate `evidence_sets.items_json`). Indexing these is what makes an
  `evidence_sets` pointer resolve to something retrievable for the first time —
  closing the gap identified above without touching `evidence_sets` itself.
- **`work-aspect`** — one `passages` row mirrors each `work_aspects` row; `anchor`
  reuses that row's `aspect_type` value, so a `key_idea` facet becomes independently
  lexically/semantically retrievable without a second place to author it.
- **`db-mirror`** — synthetic markdown-shaped text generated from the catalog
  table/`work_graph_edges` rows with no file counterpart (§4.1's second origin) — a
  work's `description`, an edge's relation — satisfying Q0(b)'s universal
  addressability for DB-native facts.

`concept_id` holds a `concepts.concept_id` for `note-body`/`db-mirror` rows, and a
catalog `work_id` (the catalog table's own primary key — see "Applying the
OpenAlex-collision fixes" below for why that column is `work_id` and not `source_id`)
for `source-span`/`work-aspect` rows. `anchor` is the `^pNNNN` value for
`source-span`, the `aspect_type` value for `work-aspect`, a parse-time-derived
heading/paragraph locator for `note-body` (Memoria does not write per-paragraph
block-ref ids into note bodies today, so this is computed at parse time, not new
authoring-time markup), and empty for `db-mirror` (the row's identity is `concept_id`
alone).

`passages.text` is, for the `work-aspect`/`source-span` origins, a copy of text whose
authority lives elsewhere (`work_aspects.aspect_text`, or the markdown file itself) —
a derived, regenerable index cache, not a second place knowledge is authored. This
sits squarely inside the rule this document's own Part 1 §1 already states for
everything in `.memoria/memoria.sqlite` ("ALL of it disposable, rebuildable,
Memoria-only"); `passages` is an instance of that rule, not an exception to it.

`passages.check_status`, copied from the owning concept's verdict at index time, is
required independently by Q5 (retrieval must never surface unchecked or quarantined
content as checked) — that requirement, not any existing pattern, is why the column is
needed. Noted here for gap-measurement only, not as justification for the column:
`work_aspects` already carries its own `check_status` column, independent of both
`concept_verdicts` and the catalog table's own `check_status`, so a derived per-row
table holding its own copy of the gate is not a new shape for `schema.sql` to contain.

`PRIMARY KEY passage_id TEXT` follows every other keyed table in `schema.sql`
(`concepts`, `catalog_sources`, `evidence_sets`); an implicit integer rowid still
exists underneath (no table in `schema.sql` declares `WITHOUT ROWID`), which is what
lets the FTS5 table below reference it directly.

**A named, not-built, adjacent gap:** `query-mechanism-analysis.md` §4.6's
local-level graph expansion wants "notes sharing a wiki-link" as a traversal edge
alongside `work_graph_edges`. A Concept's `links:` frontmatter map is not mirrored
into any table in `schema.sql` today, and no such mirror is proposed here — this
Part's requested list of changes does not include one. Without it, §4.6's local-level
expansion over "wiki-links" resolves only through `work_graph_edges` (the
catalog/bibliographic graph); a note-to-note `links:` hop needs a query-time
frontmatter parse outside SQL, breaking Q1's one-statement requirement for exactly
that edge type. Flagged as an addressable gap against §4.6, left for a future pass —
not resolved by the schema changes in this Part.

### `work_graph_edges`: the CHECK-constraint migration — `tension`, and `source` → `published_in`

`query-mechanism-analysis.md` §4.11 answers Q0(b)'s "can the schema represent a
tension today" — no — and names the fix: extend `relation_type`'s CHECK constraint
with `tension`, written only once a journaled `surface_tensions`/`_compare_claims`
candidate is PI-confirmed — edge existence is the confirmation signal, never a
provisional row (§4.11).

Separately, the OpenAlex collision audit's C3c flagged `relation_type='source'` as
the one place in the table where "recommend a targeted code check before deciding" was
the honest answer, rather than a rename call made from the schema alone. That check
was run this session: `integrity.py:675-679`'s own `relation_types` mapping —
`{"authorship": "person", "institution": "organization", "source": "venue"}` — used at
`integrity.py:687` to classify `work_graph_edges` rows for duplicate-entity-name
detection, is direct code evidence that `relation_type='source'` already means
"the venue this work was published in," i.e. OpenAlex's actual `Source` sense, not
Memoria's document-sense of "source." This is **not a collision** — it is the one
edge value in the table that already agrees with OpenAlex — but leaving the literal
spelling `'source'` in place, right where every other value already means what
OpenAlex means, is exactly the kind of accidental-looking coincidence this whole audit
exists to remove. Since both `catalog-record` and `catalog-note` (below) free the word
"source" from Memoria's document-sense in the same migration, and `'venue'` is already
taken by `concept_type`, the clean, unambiguous name is `published_in` — read
unambiguously as "`target_id` is the venue this `work_id` was published in" — not
`'source'` (still readable as the older document-sense by anyone who hasn't read this
audit) and not `'venue'` (would create a same-schema, cross-table homonym with
`concept_type='venue'`). Because this is the same table, the same column, and the same
CHECK-rebuild mechanic as the `tension` addition, both changes are made in one rebuild,
not two.

```sql
CREATE TABLE work_graph_edges (
    work_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'references', 'related', 'topic', 'keyword',
            'authorship', 'institution', 'published_in', 'tension'
        )
    ),
    target_id TEXT NOT NULL,
    target_title TEXT NOT NULL DEFAULT '',
    target_doi TEXT NOT NULL DEFAULT '',
    source_provider TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    discovered_at TEXT NOT NULL,
    PRIMARY KEY (work_id, relation_type, target_id)
);
```

SQLite has no `ALTER TABLE ... ADD CHECK`/`ALTER CONSTRAINT`; the rebuild mechanic
(rename old, create new with the extended/edited CHECK, copy rows, drop old) is
specified in the migration sketch below, not repeated here. Three things the rebuild
alone doesn't settle — gap-measurement against the real write path, not an argument
against making the change:

**A required write-path guard, narrow in scope.** `replace_work_graph_edges`
(`runtime/state.py:1003–1029`) deletes every row for a `work_id` before reinserting
(`DELETE FROM work_graph_edges WHERE work_id = ?`, `state.py:1006`) — the mechanism a
work's OpenAlex re-enrichment already uses to refresh its edges. Whatever writes a
confirmed `tension` row must keep that delete scoped to exclude
`relation_type = 'tension'`, or a confirmed tension is silently destroyed the next
time its `work_id` happens to be re-enriched.

**A documented, not hidden, namespace widening.** Every existing `relation_type`'s
`work_id`/`target_id` is normalized to a bare catalog `work_id` — the table's
non-key column set (`target_title`, `target_doi`, `source_provider`, `raw_json`) is
OpenAlex-provenance-shaped. A tension between two claims is ordinarily a tension
between two notes (`mode: claim`), whose id is a `concept_id` (Part 1's "Concept ID is
its path minus `.md`") — a different id space than every other row in this table
uses. Nothing mechanically prevents storing a `concept_id` in `work_id`/`target_id`
(both are unconstrained `TEXT`), and `target_doi`/`source_provider`/`raw_json` simply
go unused (`''`/`'{}'` defaults) for `tension` rows — a real, first-of-its-kind
widening of what those two columns hold, worth documenting as such rather than
assumed compatible because the column types happen to allow it.

**The `published_in` rename's companion code edits, found by direct grep, not
inferred.** `integrity.py:675-679`'s `relation_types` dict key `"source"` must become
`"published_in"`; `integrity.py:687`'s `relation_type IN ('authorship', 'institution',
'source')` must become `('authorship', 'institution', 'published_in')`. Not
exhaustively re-audited beyond these two confirmed sites — sized fully in the
migration sketch below, not here.

### FTS5 and `vec0`: what's indexed, and over which column

`query-mechanism-analysis.md` §4.1/§3 require lexical (FTS5) and semantic (`vec0`)
indexes over the retrieval unit resolved above — `passages.text`, one row per
`passage_id`, is that unit; nothing else is indexed.

```sql
CREATE VIRTUAL TABLE passages_fts USING fts5(text, content='passages', content_rowid='rowid');
-- plus the standard content-table sync triggers (AFTER INSERT/UPDATE/DELETE on
-- passages) — the freshness property DuckDB's FTS extension explicitly lacks (§3).

CREATE VIRTUAL TABLE passages_vec USING vec0(passage_id TEXT PRIMARY KEY, embedding FLOAT[N]);
-- N fixed by whichever local embedding model is chosen at implementation time — a
-- query-mechanism decision (§4.1), not a schema one. Exact vec0 declaration grammar
-- to confirm against the installed sqlite-vec version, per §4.4's own hedge on the
-- same point.
```

`passages`'s implicit rowid is what lets `content_rowid='rowid'` work directly — no
extra integer key needed alongside `passage_id TEXT PRIMARY KEY`.

### `file_index_state`: the mtime gate

`query-mechanism-analysis.md` §4.2 requires comparing each file's on-disk mtime
against a stored value before a query runs, reparsing only what changed — no daemon,
no watcher.

```sql
CREATE TABLE file_index_state (
    subject_id TEXT PRIMARY KEY,
    indexed_mtime TEXT NOT NULL
);
```

`subject_id` is a `concept_id` for `note-body` origins (Part 1's concept-id-is-the-
path convention resolves it to exactly one file) or a catalog `work_id` for
`source-span`/`work-aspect` origins (resolves to that work's full-text content path,
one file backing potentially many `^pNNNN` spans and up to six `work_aspects` rows,
all invalidated together when it changes). `db-mirror`-origin `passages` rows need no
entry here at all: the database row is its own source of truth and resyncs on write
via an ordinary trigger, not by comparison against an external file's mtime — there is
no external file to go stale relative to.

### Frontmatter: `todo` on all six type schemas, and `source_type` → `item_type`

**`todo`, on all six type schemas.** Add `todo: list` to `optional:` in `note.yaml`,
`work.yaml`, `source-note.yaml`, `hub.yaml`, `project.yaml`, and `digest.yaml` — the
pending-action-items field requested for every Concept type. `schema.py`'s field-kind
grammar (`runtime/subsystems/lib/schema.py`, module docstring) is `str | int | bool |
date | list | map | links | ulid | literal:<value> | enum:<name>` — no union kind
exists, so "list or str" isn't literally expressible; `list` is the reasoned
single-kind choice, not a silent narrowing — every other repeatable free-text
optional field already in these schemas (`aliases`, `topics`, `citations`) is `list`,
not a str/list union, and a single todo item is simply a one-element list.

**`source_type` → `item_type`, on `work.yaml` and `source-note.yaml` — closing a
real, already-discovered doc-vs-code drift, not new scope.**
`design-history/memoria-design-history-alpha.1-to-alpha.15.md:1441` documents
"`source_type` became an enum (`[paper, dataset, repository, web-page, report]`, was
free `str`)" as landed in alpha.10; both real files today still have `source_type:
str` with no `enums:` block for it, confirmed directly against the live YAMLs this
session — the enum never actually shipped in either file. The OpenAlex collision audit
adds a second, independent reason to fix it now rather than merely restoring the
never-landed enum under its old name: `source_type` reads as OpenAlex `Source.type`
(a venue classification — `journal`, `repository`, `conference`, `ebook platform`,
`book series`) but is meant as a work-kind classification, and `repository` means
opposite things in the two systems (a code/software repository vs. a platform that
hosts/distributes works). The rename target is not invented for this Part — it
reuses `catalog_sources.item_type` (`schema.sql:102`, `TEXT NOT NULL DEFAULT
'article'`), a column that already exists and already does a version of this job.
**A third fact, found this session and not previously flagged anywhere in this
document, noted here for gap-measurement only — not as further justification for a
decision already made above on doc-vs-code-drift and OpenAlex-collision grounds:**
`integrity.py:2069-2074`'s `_source_metadata_issues` already reads
`frontmatter.get("item_type")` directly and branches on membership in `{"article",
"book", "report"}` to decide whether a CSL author/year is required — i.e. real, live
code already expects a frontmatter key literally named `item_type`, and today neither
`work.yaml` nor `source-note.yaml` declares one (only `source_type` is declared, so the
check is currently a silent no-op against any real file). The rename incidentally also
closes this gap, alongside the OpenAlex naming collision and the YAML/DB name mismatch
already named above as the actual grounds for the decision.

One residual point, decided explicitly rather than left implicit: `catalog_sources
.item_type` (`state.py:691`, `item_type=str(frontmatter.get("item_type") or
csl_json.get("type") or "article")`) is populated from **CSL-JSON's own `type`
vocabulary** (`article-journal`, `book`, `chapter`, `paper-conference`, `webpage`,
`dataset`, `report`, …) when no explicit value is given — a bibliography-rendering
vocabulary, unconstrained by any CHECK in `schema.sql`. The alpha.10-documented
five-value list (`paper, dataset, repository, web-page, report`) is not the same
vocabulary — CSL has no `repository` type at all, and Memoria needs one (a captured
GitHub repo is a real Work kind here, not a CSL citation format). The call: give the
frontmatter field the **same name** as the DB column (closing the naming drift above)
but not the same **constrained vocabulary** — the frontmatter enum stays the coarser,
PI-facing classification; the DB column stays an unconstrained CSL-shaped passthrough
for citation rendering. Same name, deliberately different value domains, stated here
rather than silently assumed compatible because the names now match.

```yaml
enums:
  item_type: [paper, dataset, repository, web-page, report]
optional:
  item_type: enum:item_type   # replaces source_type: str
```

### Preventing schema-documentation drift structurally, not just this one instance

The `source_type` incident above is not isolated — a second instance of the identical
failure pattern turned up this session while checking whether Memoria already had a
precedent to build this recommendation on. Alpha.10's own design-history entry
documents *two* things landing together: `source_type` becoming an enum, and every
user-facing type gaining an in-schema `creation.form` block (field, label, description,
input widget, vocabulary/enum bindings). Neither shipped — confirmed this session by a
direct grep of all six live `schemas/types/*.yaml` files for `creation`/`form:`,
returning zero matches, exactly as `source_type`'s `enums:` block does not exist. Two
independent claims, in the same design-history entry, describing a schema-file change
that never happened — not a one-off slip.

This is a *data structure* question, not a documentation-process one, for a specific
reason: Memoria has two candidate single-sources-of-truth for a type's fields and
enums — the schema YAML file itself, and prose describing it (design-history entries,
`docs/reference/frontmatter.md`, `docs/reference/note-types.md`) — and nothing in the
data structure enforces that the second ever gets checked against the first.
`runtime/subsystems/lib/schema.py::validate_frontmatter` already treats the YAML file
as authoritative for validating a *written note* against its schema; it has no role
validating that *other documents describing the schema* stay in sync with it, and no
docgen script produces `frontmatter.md`/`note-types.md` from the schema files
(confirmed by grep this session: zero hits for either filename anywhere in `src/`).

Two candidate structural fixes, named for a future pass, not built in this one:

1. **Generate, don't hand-author.** `docs/reference/frontmatter.md` and
   `note-types.md` become build artifacts produced from `schemas/types/*.yaml`'s own
   `required`/`optional`/`enums` blocks — the same source `validate_frontmatter`
   already reads — removing the drift by removing the second, independently-maintained
   copy.
2. **Cheaper: a cross-validation check, not a generator.** A lint/CI step that parses
   any explicitly-stated field/enum claim in `docs/reference/frontmatter.md`/
   `note-types.md` and asserts it matches the corresponding live `schemas/types/*.yaml`
   `enums:` block — catching exactly the `source_type` and `creation.form` incidents
   mechanically, without requiring the docs themselves to become generated.

Neither is built in this pass — named as a real, now-twice-evidenced gap, not a
hypothetical one.

### Applying the OpenAlex-collision-audit fixes: every rename, in the real schema

The comprehensive OpenAlex collision audit run this session (against the real, live
`schema.sql` and all six YAMLs, plus OpenAlex's own current OpenAPI schema) found six
distinct collisions, `source_type`/`item_type` above being one (C1). The remaining
five resolve as follows — each stated as a concrete schema edit, not a restatement of
the audit's prose:

**C2 — `source_id` → `work_id`, everywhere it names the same identifier as
`work_graph_edges.work_id`.** Confirmed in code this session (`integrity.py:685`,
`s.source_id = e.work_id`; `state.py:1004`, `stable_work_id = _source_id(work_id)`) —
`catalog_sources.source_id` and `work_graph_edges.work_id` are the same identifier,
named inconsistently. `work_id` is the name that already matches OpenAlex `Work.id`;
`source_id` is the name that borrows OpenAlex's "Source" word for a Work-shaped
thing. Rename:
- `catalog_sources.source_id` (the table's `PRIMARY KEY`) → `work_id`
- `enrichment_runs.source_id` → `work_id`
- `field_provenance.source_id` (half of the composite `PRIMARY KEY (source_id,
  field_path)`) → `work_id`
- `work_aspects.source_id` (half of the composite `PRIMARY KEY (source_id,
  aspect_type)`) → `work_id`. Noted for context, not as a further reason for the
  rename (which rests on the `Work.id` match alone): this table's own name
  (`work_aspects`) already uses "work," so its FK column being `source_id` was already
  an internal name mismatch before OpenAlex is even considered.
- `note.yaml`'s optional `source_id: str` → `work_id: str`, bringing it in line with
  `work.yaml`/`source-note.yaml`/`digest.yaml`, which already correctly use `work_id`

None of these four DB columns sit inside a CHECK-constraint expression (verified
directly: `catalog_sources`'s three CHECKs are on `provider_coverage`/`text_status`/
`check_status`; `work_aspects`'s CHECK is on `aspect_type`; `enrichment_runs`'s CHECK
is on `enrichment_status`; `field_provenance` has no CHECK at all) — so, unlike the
`concept_type`/`relation_type` value-list edits, this rename does not need the
rebuild-copy-drop mechanic; SQLite's `ALTER TABLE ... RENAME COLUMN` (present in every
SQLite version bundled with Python ≥3.10) suffices, updating the column's own
`PRIMARY KEY` position in place.

**C3a/C3b — `concept_type` values `'source'`/`'source-note'` → `'catalog-record'`/
`'catalog-note'`.** Both are the document-sense of "source" (a captured Work), the
opposite of OpenAlex's `Source` (a venue). `'source'` is DB-store-only — confirmed by
grep: its only writer is `state.py:794`'s literal `_upsert_concept_mirror_conn(conn,
concept_id, "source", "db")`, never derived from any markdown frontmatter (no
`source.yaml` schema exists to author it from) — so this rename costs nothing in
already-authored vault content, only the literal string in code and the CHECK list.
`'source-note'`, by contrast, is written from real frontmatter (`type: source-note` in
every `sources/*.md` file), so renaming it to `'catalog-note'` does carry a real
content-migration step for any already-authored `source-note` files, sized in the
migration sketch below (though, per the same Q11-style rule the prerequisite document
applies to itself, there is nothing deployed today whose content actually needs
rewriting — this is a build-sequencing description, not a live data conversion).
`source-note.yaml`'s own `type: source-note` line becomes `type: catalog-note`;
its `category: sources` line becomes `category: catalog` — verified this session that
`category:` is schema-definition metadata only (grepped `schema.py` and every runtime
consumer for any read of a `"category"` key: zero hits), never a per-file frontmatter
value, so *that* half of the edit is a schema-file-only change with no content
migration at all, unlike `type:`.

```sql
CREATE TABLE concepts (
    concept_id TEXT PRIMARY KEY,
    concept_type TEXT NOT NULL
        CHECK (concept_type IN (
            'catalog-record', 'catalog-note', 'work', 'digest', 'note', 'hub', 'capability',
            'operation', 'skill', 'adapter', 'workflow', 'person',
            'organization', 'venue', 'project'
        )),
    store TEXT NOT NULL CHECK (store IN ('db', 'file'))
);
```

Companion code edits found by grep, not exhaustively re-audited beyond these:
`state.py:794`'s literal `"source"` → `"catalog-record"`; `vaultio.py:17`'s
`UNIVERSAL_CONCEPT_TYPES` frozenset entry `"source-note"` → `"catalog-note"`.
`state.py:1213`, inside the *existing* `_migrate_v4_to_v5` function, keeps its
literal `'source', 'source-note', ...` list exactly as-is — that function is pinned
to what the v5 CHECK list correctly was at the time, and editing it would corrupt the
one migration path a real v4 database still depends on; only `schema.sql`'s current
`CREATE TABLE concepts` and the new `_migrate_v6_to_v7` (below) carry the renamed
values. **Left named but not resolved here, since it's a separate convention from the
`concept_type` value:** the `concept_id` string prefix `catalog/sources/<id>`
(`state.py:775`, `integrity.py:222`) is independent of `concept_type` itself — whether
it should also become e.g. `catalog/records/<id>` for naming consistency is not
answered by the OpenAlex audit and is not decided here.

**A separate, related finding from this session's grep, flagged rather than folded
in:** `integrity.py:235,330,1976,2005` check — via equality, inequality, or set
membership — whether `frontmatter.get("type")` is the bare value `"source"`, not
`"source-note"`; and `integrity.py:2012`'s `_source_row_frontmatter` constructs a
*synthetic* frontmatter dict carrying a literal `"type": "source"` key, to feed
DB-only catalog rows through the same code paths as file-backed ones. No shipped YAML
schema (`work.yaml`, `source-note.yaml`, or any other) permits `type: source` — there
is no `source.yaml`. Whether this is dead code left over from a pre-rename period, or
an independent, deeper drift this Part hasn't traced to ground, is not resolved here;
it does not depend on, or block, the `concept_type` rename above (that column and
these frontmatter references are different things), but it is exactly the kind of
loose end a schema-scoped pass like this one can name and not chase further without
turning into a full code audit.

**C4 — Memoria's `Concept` (the `concepts` table and everything named `concept_*`)
vs. OpenAlex's own, deprecated `Concept` entity.** No schema fix — see Open Questions.

**C5 — `concept_type='venue'` vs. OpenAlex's deprecated `host_venue` alias of
`Source`.** Not a collision — `'venue'` is already the one term in the schema that
correctly matches OpenAlex's venue sense. No rename. The binding constraint this adds
to C3a/C3b above: neither rename may free "source" for reuse at the journal/publisher
level — confirmed satisfied, since neither `catalog-record` nor `catalog-note` nor
`published_in` reintroduces the bare word at that level.

**C6 — `journal_events` → `event_log`; `enrichment_runs.journal_id` → `event_id`.**
In a citation/catalog codebase, "journal" defaults to meaning an academic periodical
(the single most common OpenAlex `Source.type` value); `journal_events` is an
unrelated append-only audit/event ledger (PK `event_id`, hash-chained,
`journal_events_no_update`/`journal_events_no_delete` triggers blocking mutation), and
`enrichment_runs.journal_id` is — by its own column name mismatch with the table it
references — a foreign key into that ledger, not any bibliographic journal. Confirmed
by grep this session that `journal_id` is written nowhere (`state.py`'s writers never
set it; it carries only its `DEFAULT ''`), matching Part 1 §7's own doc-vs-code-drift
flag — so this rename carries zero populated-value risk. `event_log` (not the audit's
alternate `audit_log`) is the chosen target specifically because `.memoria/audit/`
already exists as a distinct, real, tracked directory (Part 1 §4) — `audit_log` would
recreate a new, smaller collision immediately after fixing this one.

```sql
CREATE TABLE event_log (
    event_id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    machine TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL UNIQUE
);
CREATE TRIGGER event_log_no_update BEFORE UPDATE ON event_log
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER event_log_no_delete BEFORE DELETE ON event_log
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
```

A residual naming asymmetry, flagged not fixed: the on-disk mirror `journal/
<machine>.jsonl` and the `.memoria/journal-head` anchor file (Part 1 §3/§4) keep the
word "journal" after this rename — a file-layout question (Part 6/7's territory, not
this Part's), out of scope here.

## Trade-offs

- **`passages.text` duplicates text whose authority lives elsewhere** (in
  `work_aspects.aspect_text`, or the markdown file itself) for the `work-aspect`/
  `source-span`/`note-body` origins — a deliberate, bounded, regenerable duplication,
  consistent with Part 1's disposable-DB-mirror rule, but real bytes-on-disk and
  reindex-time compute, not free.
- **`work_aspects` stays bounded and unchanged** — gives up a single unified
  "everything is a passage" model in exchange for keeping the deterministic six-facet
  extraction queryable on its own small, clean shape.
- **`tension` and `published_in` are bundled into one `work_graph_edges` rebuild** —
  cheap (one rebuild instead of two, since both are CHECK-list edits on the same
  table) but coupled: if the `tension` feature were ever deferred independently, the
  `published_in` rename would need to be split back out into its own rebuild rather
  than riding along.
- **`published_in` gives up column-semantic cleanliness for `tension` rows**
  (`target_doi`/`source_provider`/`raw_json` unused when `relation_type='tension'`)
  and requires the write-path guard above, in exchange for reusing every existing
  local-level traversal query (§4.6) against one edge table rather than teaching
  retrieval about a second one.
- **Existence-based tension gating** (no status column, per §4.11) — a
  disconfirmed/retracted tension has no soft "retracted" state, only outright row
  deletion; simpler, but loses the history a status column would have kept.
- **`file_index_state.subject_id` shares one column across two id namespaces**
  (`concept_id`, catalog `work_id`) — a deliberate one-table simplification over two
  parallel, more type-clean tables.
- **`todo: list`, not the literally-requested "list or str"** — a trivial ergonomic
  cost (single items wrap in a one-element list), forced by the schema grammar's lack
  of a union kind, not a capability loss.
- **`item_type`'s frontmatter enum and the DB column of the same name deliberately
  hold different value vocabularies** (a coarse work-kind list vs. an unconstrained
  CSL-passthrough) — the naming collision and the name/name drift are both closed,
  but a reader who assumes "same column name across layers implies same allowed
  values" will be wrong here; stated explicitly above so it isn't a silent trap.
- **`concept_type='source-note'` → `'catalog-note'` is not free the way
  `'source'` → `'catalog-record'` is** — the latter is pure code+DB (zero
  vault-content cost), the former is frontmatter-authored and would require rewriting
  `type: source-note` in every already-existing `source-note` file, a real cost sized
  in the migration sketch (though nothing deployed today actually carries that cost,
  per Q11).
- **C4 (Memoria's `Concept` vs. OpenAlex's) is documented, not eliminated** — the
  collision persists permanently in Memoria's single most pervasive term; see Open
  Questions.
- **The `integrity.py` bare `type == "source"` checks (C3 finding, above) are named
  but not run to ground** — a real, acknowledged incompleteness of this pass's code
  grounding, not a schema gap.
- **Community-detection library adoption, ANN indexing, and reranking/synthesis
  remain deferred**, exactly as `query-mechanism-analysis.md` §5/§8 already decided —
  retrieval-algorithm trade-offs, not restated here.
- **The concept-to-concept `links:` mirror gap (above) is left open, not resolved** —
  a deliberate scope decision, not an oversight, but it means §4.6's graph leg is not
  fully satisfiable by the schema specified here alone.
- **Schema-documentation-drift prevention is named, not built** — the generate-docs-
  from-schema and cross-validation-lint options above stay unimplemented this pass;
  `source_type` and `creation.form` are fixed as instances, but the mechanism that
  would have caught both mechanically, before a design-history entry could claim a
  schema change that never landed, still does not exist.

## Gap to current implementation, and migration sketch

Per the project owner's correction (mirroring `query-mechanism-analysis.md`'s own
Q11): there is currently nothing deployed to migrate — no external vault depends on
today's shape. The steps below are build/sequencing steps for constructing the v7
schema, not a data-preserving conversion of production content; where a step below
would, hypothetically, need to rewrite already-authored vault content (the
`source-note` → `catalog-note` `type:` value), that is named as a future mechanism,
not a present-tense migration this Part performs.

1. **Schema-version plumbing, before any table rebuild.** Bump `SCHEMA_VERSION`
   (`state.py:29`, today `6`) to `7`; change `schema.sql`'s trailing `PRAGMA
   user_version = 6` to `7`; add a new `_migrate_v6_to_v7` function modeled directly
   on the existing `_migrate_v4_to_v5` (`state.py:1204–1233`); extend `_init`'s
   tolerance set (`state.py:1196`, today `current not in {0, 5, SCHEMA_VERSION}`) to
   route a v6 database through it. `schema.sql`'s `CREATE TABLE IF NOT EXISTS` is a
   no-op against a table that already exists in its old shape — confirmed by why
   `_migrate_v4_to_v5` exists at all — so none of the CHECK-list edits below can land
   through a `schema.sql` edit alone.
2. **Inside `_migrate_v6_to_v7`, rebuild `concepts`** (rename `'source'` →
   `'catalog-record'`, `'source-note'` → `'catalog-note'` in the CHECK list and in
   every existing row, via `CASE concept_type WHEN 'source' THEN 'catalog-record'
   WHEN 'source-note' THEN 'catalog-note' ELSE concept_type END` in the `INSERT ...
   SELECT`) using the same four-step shape (`DROP VIEW concept_status` → `RENAME TO
   concepts_v6` → `CREATE TABLE concepts` with the new CHECK → `INSERT ... SELECT`
   with the `CASE` remap → `DROP TABLE concepts_v6` → recreate `concept_status`)
   `state.py:1204–1233` already used once for this exact table. In the same
   transaction, **rebuild `work_graph_edges`** (add `'tension'`, rename `'source'` →
   `'published_in'` via an analogous `CASE relation_type WHEN 'source' THEN
   'published_in' ELSE relation_type END`); patch `replace_work_graph_edges`'s delete
   (`state.py:1006`) to `DELETE FROM work_graph_edges WHERE work_id = ? AND
   relation_type != 'tension'`; wire `surface_tensions`'s PI-confirmation step to
   write the row instead of only closing the journal entry; update
   `integrity.py:675-679`'s `relation_types` dict key `"source"` → `"published_in"`
   and `integrity.py:687`'s IN-list to match; update `state.py:794`'s literal
   `"source"` → `"catalog-record"` and `vaultio.py:17`'s `UNIVERSAL_CONCEPT_TYPES`
   entry `"source-note"` → `"catalog-note"`. Leave `state.py:1213` (inside
   `_migrate_v4_to_v5`) untouched, per the reasoning above.
3. **Also inside `_migrate_v6_to_v7`, the plain renames (no CHECK involved, no
   rebuild needed):**
   ```sql
   ALTER TABLE catalog_sources RENAME COLUMN source_id TO work_id;
   ALTER TABLE enrichment_runs RENAME COLUMN source_id TO work_id;
   ALTER TABLE enrichment_runs RENAME COLUMN journal_id TO event_id;
   ALTER TABLE field_provenance RENAME COLUMN source_id TO work_id;
   ALTER TABLE work_aspects RENAME COLUMN source_id TO work_id;
   ALTER TABLE journal_events RENAME TO event_log;
   DROP TRIGGER IF EXISTS journal_events_no_update;
   DROP TRIGGER IF EXISTS journal_events_no_delete;
   CREATE TRIGGER event_log_no_update BEFORE UPDATE ON event_log
   BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
   CREATE TRIGGER event_log_no_delete BEFORE DELETE ON event_log
   BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
   ```
   Whether SQLite's table-level `RENAME TO` re-points a bound trigger's `ON <table>`
   clause automatically varies enough across versions that the explicit
   drop-and-recreate above is the safer statement to ship, not an assumption. Every
   application-code call site keyed to the old column/table names must move in
   lockstep — confirmed by grep to be a large, mechanical surface (representative
   sites: `state.py:675-1446`, roughly fifty `source_id`-keyed lines (67 occurrences,
   by direct grep count);
   `integrity.py:685`; `enrichment.py`, `search_index.py`, `capture.py`,
   `knowledge.py`, each holding at least one `work_graph_edges`/`catalog_sources`
   join or dict-key reference) — sized here as a scope estimate, not exhaustively
   enumerated, since a full call-site inventory is a code task, not a schema one.
4. **Add `passages`, `passages_fts`, `passages_vec`, and `file_index_state`** to
   `schema.sql` as new `CREATE TABLE IF NOT EXISTS`/`CREATE VIRTUAL TABLE`
   statements — no rebuild needed, since none of these exist in any shape yet.
   One-time backfill: parse the four `passages` origins (note-body markdown under
   `notes/`/`hubs/`/`projects/`/`digests/`, source-span `^pNNNN` anchors under every
   catalog work's full-text path, one row per existing `work_aspects` row, db-mirror
   text from the catalog table/`work_graph_edges`), compute embeddings, populate
   `file_index_state` for every file-backed origin.
5. **Frontmatter-only changes** — no `schema.sql`/DB migration, validated instead by
   `schema.py::validate_frontmatter` at write time:
   - Add `todo: list` to `optional:` in `note.yaml`, `work.yaml`, `source-note.yaml`,
     `hub.yaml`, `project.yaml`, `digest.yaml`.
   - On `work.yaml` and `source-note.yaml`: remove `source_type: str` from
     `optional:`; add the `item_type` enum block (`[paper, dataset, repository,
     web-page, report]`) and `optional: item_type: enum:item_type`.
   - On `source-note.yaml`: `type: literal:source-note` → `type:
     literal:catalog-note`; `category: sources` → `category: catalog`. If any
     already-authored vault markdown carries `type: source-note`, rewrite that key's
     value in place as part of this step — a content migration, not a schema-file-only
     edit; whether any such files currently exist in a given vault is not established
     here, per Q11.
   - On `note.yaml`: `source_id: str` → `work_id: str`.
6. **Add the C4 glossary note** — a header comment in `schema.sql` above `CREATE
   TABLE concepts` ("Memoria's 'Concept' is unrelated to OpenAlex's deprecated
   Concept entity — a legacy Wikidata-derived subject taxonomy, superseded by Topic;
   when referring to OpenAlex's subject-taxonomy notion anywhere in this codebase,
   say 'topic', never 'concept'") and the same statement added to `docs/reference/
   glossary.md` (confirmed already the home of Memoria's "Concept" definition, per
   Part 3).
7. **Re-run this document's own benchmarking discipline**
   (`query-mechanism-analysis.md` §4.10/§6, phases 1–3) against the new
   `passages`/FTS5/`vec0` schema once populated — a query-mechanism verification, out
   of this Part's scope, named only so the schema migration and the query benchmark
   aren't conflated as one step.

## Open questions

**Only item that qualifies: C4, Memoria's `Concept` vs. OpenAlex's deprecated
`Concept` entity.** The audit's own conclusion is that no clean rename exists — the
word is Memoria's single most pervasive architectural noun (`concepts` table,
`concept_id`, `concept_type`, `concept_verdicts`, `concept_flags`, the
`concept_status` view, `concept_path`, the whole `.memoria/schemas/types/`
directory), and renaming it would be a disproportionate rewrite relative to the
problem, which is purely lexical (Part 3 already confirmed no semantic bleed:
OpenAlex's `concepts` field maps to Memoria's `topic` edges, never to Memoria's own
"Concept" noun). The glossary-note mitigation specified in the migration sketch above
contains the confusion for a reader who knows to look for it; it does not remove the
underlying naming collision, which remains permanent. No rename is proposed here, and
none should be invented to manufacture a resolution this audit didn't find.

## Resolved or out-of-scope items, logged for cross-reference (not open questions)

Neither item below is an open question — both are resolved or scoped elsewhere in this
session's work — but each is adjacent enough to this Part's subject matter that it is
worth cross-referencing here rather than leaving a reader to wonder why it isn't
addressed above:

- **Repo/dataset digest/full-text mapping** — already resolved-as-not-a-schema-
  question this session (webpage/podcast/repo/dataset imports need a different
  ingest mechanism but no schema change); the one real exception (importing a
  dataset's raw data into the knowledge bundle itself) is tracked in
  `scratch/releases/0.1.0-beta.1/0.1.0-beta.1-design.md` item 18, not this Part's
  concern.
- **`system/templates/` → `.memoria/templates/`, missing `work.md`/`source-note.md`
  templates, missing template-driven CLI commands** — captured in
  `scratch/releases/0.1.0-beta.1/0.1.0-beta.1-design.md` items 15–17, not this Part's
  concern.
