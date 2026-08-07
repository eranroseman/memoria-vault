# Glossary Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every glossary entry addressable, evidence-earned, and drift-safe; add the 22 missing terms the docs already use; replace the CONTEXT.md symlink with a pointer stub.

**Architecture:** Docs-only change centered on `docs/reference/data-model/glossary.md`. Entries become `###` headings (kramdown auto-anchors) inside the existing `##` domain sections, alphabetized within each section. Planned-surface micro-terms fold into their parent entry; milestone codes give way to a plain "Planned" marker; enum rosters move to their owning spec pages; 22 new entries land in their domain sections. Root `CONTEXT.md` becomes a 4-line regular-file stub.

**Tech Stack:** Markdown (kramdown/GFM, Just the Docs v0.12.0 on GitHub Pages), pre-commit manual-stage lint (cspell, markdownlint, vale), `python scripts/verify`.

## Global Constraints

- Docs-only plus root files (`CONTEXT.md`, `AGENTS.md`, `docs/_config.yml`); **no `src/` changes**.
- Correctness gate: `python scripts/verify` must pass before the PR.
- Stage explicit paths only — the repo's `PreToolUse` hook rejects `git add -A` (shared index rule).
- American English; if cspell flags a real term, add it to `project-words.txt` (lowercase, sorted) — never inline-suppress.
- Links inside `docs/` are relative, following the target's Pages route. Never relative-link into `src/` — cite source files as inline-code paths.
- One definition per term; disambiguation noted where a term has two senses.
- Trust order is schema → tests → code → docs: if a definition given in this plan contradicts the owning page or code, fix the definition to match the code/schema and note the change in the commit message.
- Entry format inside a section: `### Term` heading, then the definition paragraph (no leading `**Term** —` prefix — the heading carries the term).
- End commit messages with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

**Lint command used throughout** (pre-commit manual stage, scoped to changed files):

```bash
pre-commit run --hook-stage manual --files <changed files>
```

---

### Task 1: CONTEXT.md pointer stub + AGENTS.md wording

**Files:**
- Delete + recreate: `CONTEXT.md` (currently a git symlink, mode 120000)
- Modify: `AGENTS.md:60-64` (the "Where things live" glossary bullet)

**Interfaces:**
- Produces: a regular-file `CONTEXT.md` that later tasks never touch; AGENTS.md language other tasks may quote.

Why: the symlink serves nothing — `raw.githubusercontent.com` returns the literal path string, GitHub's blob view shows a "Symbolic link" banner instead of content, Windows stock clones materialize it as a path-string file, and pre-commit's `types: [file]` filter means no lint hook ever sees it. A regular-file stub works on every surface and can also route to AGENTS.md, which a symlink cannot.

- [ ] **Step 1: Verify current state (expect symlink)**

Run: `git ls-files -s CONTEXT.md`
Expected: `120000 7988ed42... 0	CONTEXT.md`

- [ ] **Step 2: Replace symlink with stub**

```bash
git rm CONTEXT.md
```

Then create `CONTEXT.md` (regular file) with exactly:

```markdown
# Context

Canonical vocabulary: [glossary](docs/reference/data-model/glossary.md) —
read it before naming things; add usage rulings there; never start a
second glossary. Agent operating facts: [AGENTS.md](AGENTS.md).
```

- [ ] **Step 3: Update AGENTS.md**

In `AGENTS.md`, replace the sentence:

```
Root `CONTEXT.md` is a symlink to it for tools that look for that file by convention.
```

with:

```
Root `CONTEXT.md` is a pointer stub routing to it (and back here) for tools that look for that file by convention.
```

- [ ] **Step 4: Verify stub is a regular file and lint sees it**

Run: `git add CONTEXT.md AGENTS.md && git ls-files -s CONTEXT.md`
Expected: mode `100644` (regular file).

Run: `pre-commit run --hook-stage manual --files CONTEXT.md AGENTS.md`
Expected: hooks run (no "no files to check — Skipped" for CONTEXT.md); all pass.

- [ ] **Step 5: Commit**

```bash
git add CONTEXT.md AGENTS.md
git commit -m "CONTEXT.md: pointer stub replaces symlink

Symlink served raw fetchers and Windows checkouts a path string and was
invisible to every pre-commit hook (types: [file]). A regular-file stub
works on every consumption surface and also routes to AGENTS.md.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Entries become addressable headings, alphabetized within sections

**Files:**
- Modify: `docs/reference/data-model/glossary.md` (whole file)
- Modify: `docs/_config.yml` (search block, currently `heading_level: 2`)

**Interfaces:**
- Produces: `###`-heading entries whose kramdown auto-ids later tasks and other docs link to; the pinned id `open-knowledge-format-okf`.

Conversion rule, applied to every `**Term** — definition…` paragraph in the five `##` sections (the `## Verdicts` table is untouched):

```markdown
**Co-PI** — the research-partner role exposed through the standalone
`memoria ask` / `memoria project ask` commands.
```

becomes

```markdown
### Co-PI

The research-partner role exposed through the standalone `memoria ask` /
`memoria project ask` commands.
```

Special case — the OKF entry drops its hand-written `<a id=...>` and pins the same id with a kramdown IAL so the three existing inbound links keep resolving:

```markdown
### Open Knowledge Format (OKF) {#open-knowledge-format-okf}
```

- [ ] **Step 1: Record the inbound anchor links that must keep working**

Run: `grep -rn "glossary.md#" docs/ README.md AGENTS.md --include="*.md"`
Expected: exactly 3 hits, all `#open-knowledge-format-okf`. Note the files; Step 5 re-checks them.

- [ ] **Step 2: Convert every entry to a `###` heading**

Apply the conversion rule above to all entries. Then alphabetize entries **within each section** (case-insensitive; entries only — section order and the intro stay). Current rosters, in target order:

- **System:** Agent, autoresearch, Co-PI, generated, Knowledge Bundle, Memoria, Open Knowledge Format (OKF), Operation, PI, sources, Standalone runtime, Toulmin roles, verified, Workspace
- **Surfaces and navigation:** Cockpit, Maintenance, Navigator rail, Now, Places, Queue, Rail health band, System dashboard
- **Board and delegation:** Ceiling, Dispatcher, Handoff payload, Runner, Task/request, Worklist
- **Notes and lifecycle:** Attention projection, Card, Check status, Concept, Document type, Hub, Links vs work-graph edges, loudness, Pattern, State, Work
- **Policy and audit:** Audit log, Extraction-uncertainty flag, Policy gate

(Later tasks delete/fold some of these; this task only converts and orders what exists.)

- [ ] **Step 3: Add the context sentence to the intro**

After the line `Term definitions for Memoria, organized by domain. …`, add:

```markdown
Memoria is a phase-gated personal knowledge-production tool for one
researcher; these are its canonical terms and usage rulings.
```

- [ ] **Step 4: Raise search granularity so each term is its own search hit**

In `docs/_config.yml`, change:

```yaml
search:
  heading_level: 2
```

to:

```yaml
search:
  heading_level: 3
```

(Leave `previews`/`preview_words_*` unchanged.)

- [ ] **Step 5: Verify structure and anchors**

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 42 (14 + 8 + 6 + 11 + 3).

Run: `grep -n "{#open-knowledge-format-okf}" docs/reference/data-model/glossary.md`
Expected: 1 hit on the OKF heading line.

Run: `grep -n "<a id" docs/reference/data-model/glossary.md`
Expected: no output.

Re-run the Step 1 grep — the 3 inbound links are unchanged and still target `#open-knowledge-format-okf`.

- [ ] **Step 6: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md docs/_config.yml`
Expected: pass (markdownlint heading rules: h1 title → h2 sections → h3 terms, no skips).

```bash
git add docs/reference/data-model/glossary.md docs/_config.yml
git commit -m "glossary: every term is an addressable heading

Entries become ### headings (kramdown auto-ids), alphabetized within
their domain sections; OKF keeps its anchor via IAL pin; site search
now indexes per-term.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Planned-surface consolidation and milestone-code strip

**Files:**
- Modify: `docs/reference/data-model/glossary.md`

**Interfaces:**
- Consumes: `###`-heading entries from Task 2.
- Produces: single `Navigator rail` entry (no `Now`/`Places`/`Rail health band` headings); `Work` entry carrying the identity-calibration ruling; no milestone codes anywhere in the file.

Evidence driving this task: `Places` has zero uses anywhere outside the glossary; `Now` and `Rail health band` appear on 2–3 pages only; `Extraction-uncertainty flag` appears nowhere outside the glossary; milestone codes (K1, G4/G5, B1, I1/E1, beta.2) duplicate readiness that AGENTS.md says lives in GitHub milestones.

- [ ] **Step 1: Merge the rail micro-terms into Navigator rail**

Delete the `### Now`, `### Places`, and `### Rail health band` entries. Replace the `### Navigator rail` entry body with:

```markdown
A planned optional-adapter navigation model
([thin read-API surfaces over one engine, PI direct access preserved](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)):
a **Now** band — what is waiting on you right now (your Inbox action
queue, open integrity flags, and a health-band count of open `flag` /
`alert` attention projections) — over a **Places** band of durable corpus
homes (Library: `digests/`, `fulltexts/`, `bibliography.bib`; Knowledge:
`notes/`, `hubs/`; Project: `projects/`). It requires no persisted
navigation note. The standalone CLI does not render it. Planned — see
[Roadmap](../../roadmap.md).
```

- [ ] **Step 2: Strip milestone codes from the three planned entries**

In `### Knowledge Bundle`, replace `The format ships; the export and import path is **planned beta.1 — K1.**` with:

```markdown
The format ships; the export and import path is planned — see
[Roadmap](../../roadmap.md).
```

In `### Toulmin roles`, replace `**Planned G4/G5, beta.1/B1.**` with:

```markdown
Planned — see [Roadmap](../../roadmap.md).
```

In `### autoresearch`, replace `**Planned beta.2; beta.1 precursors I1/E1.**` with:

```markdown
Planned — see [Roadmap](../../roadmap.md).
```

- [ ] **Step 3: Delete Extraction-uncertainty flag; move its ruling into Work**

Delete the `### Extraction-uncertainty flag` entry. Append to the `### Work` entry body:

```markdown
Memoria ships no cross-Work identity calibration floor or automatic
merge decision; a future near-tie rule may raise an Inbox `flag` for PI
review.
```

- [ ] **Step 4: Verify**

Run: `grep -nE "K1|G4/G5|B1|I1/E1|beta\.[12]" docs/reference/data-model/glossary.md`
Expected: no output.

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 38 (42 − Now − Places − Rail health band − Extraction-uncertainty flag).

- [ ] **Step 5: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md`

```bash
git add docs/reference/data-model/glossary.md
git commit -m "glossary: fold rail micro-terms, strip milestone codes

Places had zero uses anywhere; Now and Rail health band 2-3 pages; all
three fold into Navigator rail. Readiness codes duplicated GitHub
milestones (AGENTS.md: no separate readiness fields) - now a plain
Planned marker linking the roadmap. Extraction-uncertainty flag was
glossary-only; its shipping ruling moves into Work.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Disambiguation fixes — Ceiling, Pattern, Home Co-PI wording

**Files:**
- Modify: `docs/reference/data-model/glossary.md`
- Modify: `docs/README.md:153` (Co-PI row in the core-terms table)

**Interfaces:**
- Consumes: Task 2 heading format.
- Produces: no `### Pattern` heading (folded into Operation); a two-sense `Ceiling` entry.

Evidence: docs use "ceiling" mostly in the operation-manifest sense (4 pages) while the glossary pins the adapter-policy sense (1 page) — the entry currently rules the minority sense canonical. "Pattern" in the prompt-operation sense appears on only 2 pages. Home's Co-PI row ("read-only conversational posture") drifted from the glossary ("research-partner role").

- [ ] **Step 1: Read the two ceiling senses in context**

Read `docs/reference/control-and-policy/policy-mcp.md` (search "ceiling") and `docs/explanation/rationale/execution/why-operation-postures.md` (search "ceiling"). Confirm both senses exist as described; if the manifest sense is named differently there, use that page's wording in Step 2.

- [ ] **Step 2: Broaden the Ceiling entry**

Replace the `### Ceiling` body with:

```markdown
The maximum write scope a policy grants, in either of two places: an
operation manifest's capability ceiling, or the write scope an optional
adapter policy grants. Request payloads may narrow a ceiling, never
widen it.
```

- [ ] **Step 3: Fold Pattern into Operation**

Delete the `### Pattern` entry. Append to the `### Operation` entry body:

```markdown
A **Pattern** is a package-owned prompt operation
([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md))
executed through `memoria operation run`.
```

- [ ] **Step 4: Align the Home core-terms table**

In `docs/README.md`, the Co-PI row currently reads:

```markdown
| Co-PI | The read-only conversational posture behind `memoria ask`. See [The Co-PI](explanation/execution/operation-postures/co-pi.md) for its full mission. |
```

Replace with:

```markdown
| Co-PI | The research-partner role behind `memoria ask` — read-only conversation over the checked corpus. See [The Co-PI](explanation/execution/operation-postures/co-pi.md) for its full mission. |
```

First read `docs/explanation/execution/operation-postures/co-pi.md`; if it contradicts "read-only conversation over the checked corpus", prefer that page's wording (docs describe shipped behavior).

- [ ] **Step 5: Verify**

Run: `grep -n "^### Pattern$" docs/reference/data-model/glossary.md`
Expected: no output.

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 37.

- [ ] **Step 6: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md docs/README.md`

```bash
git add docs/reference/data-model/glossary.md docs/README.md
git commit -m "glossary: two-sense Ceiling, Pattern folds into Operation, Home Co-PI realigned

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Split the links contrast entry; enum rosters move to owning pages

**Files:**
- Modify: `docs/reference/data-model/glossary.md`
- Possibly modify: `docs/reference/data-model/wikilink-and-link-conventions.md` (only if it lacks the `relation_type` roster)

**Interfaces:**
- Consumes: Task 2 heading format.
- Produces: `### links (frontmatter)` and `### Work-graph edge` entries (replacing `### Links vs work-graph edges`); a `loudness` entry that names no value roster except `block`.

Rationale: trust order puts schema above docs — value rosters duplicated in the glossary drift against the schema. The glossary keeps meaning and rulings; owning pages keep rosters. Exception kept as-is: the Verdicts table's `certainty` row, whose whole job is contrasting two enums.

- [ ] **Step 1: Check the roster's owning page**

Read `docs/reference/data-model/wikilink-and-link-conventions.md`. If it does NOT already list the `work_graph_edges` `relation_type` values (`references`, `related`, `topic`, `keyword`, `authorship`, `institution`, `published_in`), add them there in that page's own style (verify the roster against `src/memoria_vault/runtime/schema.sql` first — schema wins over this plan).

- [ ] **Step 2: Split the contrast entry**

Delete `### Links vs work-graph edges`. Add, in alphabetical position within Notes and lifecycle:

```markdown
### links (frontmatter)

The authored kind of connection: `links:` frontmatter on Concepts,
written by the PI or proposed by operations, with its relation
vocabulary specified in
[Frontmatter fields](frontmatter.md#links-and-catalog-resources).
Distinct from given [Work-graph edges](#work-graph-edge); the
distinction and its rationale are explained in
[Wikilink and link conventions](wikilink-and-link-conventions.md).
```

```markdown
### Work-graph edge

The given kind of connection: a `work_graph_edges` SQLite row
(`src/memoria_vault/runtime/schema.sql`) discovered for catalog Works —
not Concept frontmatter. The `relation_type` roster and the contrast
with authored links are specified in
[Wikilink and link conventions](wikilink-and-link-conventions.md).
```

- [ ] **Step 3: Delink the loudness roster**

Replace the `### loudness` body with:

```markdown
The urgency band on an attention card's frontmatter; the band roster is
specified in
[Empirical events](../control-and-policy/empirical-events.md#enum-values)
and `src/memoria_vault/runtime/attention/loudness.py`. `block` is
pull-only: an open block card pauses delegation and review-gated
promotion until the PI resolves it.
```

- [ ] **Step 4: Verify**

Run: `grep -n "quiet.*notice.*alert.*block" docs/reference/data-model/glossary.md`
Expected: no output (roster no longer in the glossary).

Run: `grep -n "relation_type" docs/reference/data-model/wikilink-and-link-conventions.md`
Expected: at least one hit (roster lives there).

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 38 (37 − 1 contrast entry + 2 split entries).

- [ ] **Step 5: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md docs/reference/data-model/wikilink-and-link-conventions.md`

```bash
git add docs/reference/data-model/glossary.md docs/reference/data-model/wikilink-and-link-conventions.md
git commit -m "glossary: links contrast becomes two entries; enum rosters live on owning pages

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: New entries — System section

**Files:**
- Modify: `docs/reference/data-model/glossary.md` (System section)

**Interfaces:**
- Consumes: Task 2 heading format and alphabetical order.
- Produces: headings `#### `-level ids `#catalog`, `#grounding`, `#memoria-doctor`, `#provenance`, `#read-api`, `#trusted-writer` other docs may link.

Six entries, each inserted in alphabetical position. Before adding each, skim the named owning page; if it contradicts the text below, follow the page (docs describe shipped behavior) and note it in the commit message.

- [ ] **Step 1: Add the six entries**

```markdown
### Catalog

The SQLite record of every source the vault knows: Works, their
identifiers and provenance, and the work-graph edges discovered for
them. Sources enter the catalog before any knowledge work; its only
file-backed faces are `digests/` and `fulltexts/`. See
[Ingest](../pipelines-and-io/ingest.md) for how sources arrive.
```

(Owning pages: `docs/reference/pipelines-and-io/ingest.md`, `src/memoria_vault/runtime/schema.sql`.)

```markdown
### Grounding

The inspectable structure connecting a claim to the sources and
reasoning that support it. All trust in Memoria lives in grounding
structure, never in any author — human or machine
(`src/memoria_vault/runtime/grounding/`). See
[Intellectual foundations](../../explanation/rationale/foundations/intellectual-foundations.md).
```

```markdown
### memoria doctor

The diagnostic command family (`memoria doctor`,
`memoria doctor bundle`): read-only checks of installation,
configuration, runner reachability, and bundle health. See
[Installer](../system/installer.md) and
[Failure modes](../system/failure-modes.md).
```

```markdown
### Provenance

The umbrella term for recorded origin, in two senses: the OKF
frontmatter fields on Concepts ([generated](#generated),
[sources](#sources), [verified](#verified)), and pattern provenance —
the recorded lineage of operation outputs
([Pattern provenance](../evidence-and-integrations/pattern-provenance.md)).
Recorded at write time, never reconstructed.
```

```markdown
### Read API

The engine's verdict-tagged read surface: the registered read actions
served over CLI and local HTTP
(`src/memoria_vault/engine/surface_contract.py`). Read-only by
contract; surfaces such as the Cockpit compose over it. See
[Read API](../commands-and-transports/read-api.md).
```

```markdown
### Trusted writer

The single runtime component allowed to write Concept files: it stamps
`generated` and `sources` provenance at staging and `verified` at
promotion, and enforces the frontmatter schema on every write
(`src/memoria_vault/runtime/trusted_writer.py`). Operations never write
Concepts directly.
```

- [ ] **Step 2: Verify insertion and anchors**

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 44.

Run: `grep -n "^### Catalog$\|^### Grounding$\|^### memoria doctor$\|^### Provenance$\|^### Read API$\|^### Trusted writer$" docs/reference/data-model/glossary.md`
Expected: 6 hits, in the System section, in alphabetical positions.

- [ ] **Step 3: Verify every relative link target exists**

```bash
for f in ../pipelines-and-io/ingest.md ../system/installer.md ../system/failure-modes.md ../evidence-and-integrations/pattern-provenance.md ../commands-and-transports/read-api.md ../../explanation/rationale/foundations/intellectual-foundations.md; do
  test -f "docs/reference/data-model/$f" && echo "OK $f" || echo "MISSING $f"
done
```

Expected: six `OK` lines. Fix any `MISSING` by correcting the path to the real page.

- [ ] **Step 4: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md`

```bash
git add docs/reference/data-model/glossary.md
git commit -m "glossary: System entries for Catalog, Grounding, doctor, Provenance, Read API, Trusted writer

All six are used on 13-70 docs pages but were undefined; several were
used undefined by the glossary's own entries.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: New entries — Notes and lifecycle section

**Files:**
- Modify: `docs/reference/data-model/glossary.md` (Notes and lifecycle section)

**Interfaces:**
- Consumes: Task 2 format; `#trusted-writer` anchor from Task 6.
- Produces: the PI-decision lifecycle vocabulary (`staging`, `promotion`, `triage`, `disposition`) the glossary itself uses.

Seven entries, alphabetical positions. Same rule: owning page wins over this plan's text.

- [ ] **Step 1: Add the seven entries**

```markdown
### Disposition

The recorded PI verdict on an attention item — the decision that
resolves it (for worklist items, the `decision` field the PI sweeps).
One of the three decision kinds the PI owns, with
[Triage](#triage) and [Promotion](#promotion). See
[Worklists](../control-and-policy/worklists.md).
```

```markdown
### Ingest

The pipeline stage that brings an external source into the
[Catalog](#catalog) as a Work, producing its digest and fulltext
reproduction. See [Ingest](../pipelines-and-io/ingest.md).
```

```markdown
### Promotion

The PI-gated transition where reviewed content becomes checked
knowledge; the [Trusted writer](#trusted-writer) stamps `verified` at
this moment. An open `block` card pauses review-gated promotion. See
[Promotion and gated zones](../../explanation/knowledge/promotion-and-gated-zones.md).
```

```markdown
### Staging

The trusted-writer step that places generated content into the
workspace with `generated` and `sources` provenance stamped, ahead of
PI review; re-staging strips `verified`. Not git staging. See
[Ingest](../pipelines-and-io/ingest.md).
```

```markdown
### steering.md

A project's PI-intent artifact: the standing instructions operations
read when working that project. PI-authored; operations read it, they
do not write it. See [Configuration](../system/configuration.md).
```

```markdown
### Triage

The PI's first-pass decision over Inbox items — keep, dismiss, or
route. Also the name of the Cockpit `--triage` screen that batches it.
See [Work the action queue](../../how-to-guides/inbox/work-the-action-queue.md).
```

```markdown
### vocabulary (system/vocabulary.md)

The controlled-vocabulary artifact governing `topic` and `keyword`
values across the vault. Distinct from the everyday word: when docs say
"the vocabulary", they mean this artifact. See
[System artifacts](../system/system-artifacts.md).
```

- [ ] **Step 2: Verify**

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 51.

Read the `### generated`, `### verified`, and `### Attention projection` entries and confirm the terms they use (staging, promotion, trusted writer) now resolve to headings in the same file.

- [ ] **Step 3: Verify link targets exist** (same pattern as Task 6 Step 3, for the five pages referenced above).

- [ ] **Step 4: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md`

```bash
git add docs/reference/data-model/glossary.md
git commit -m "glossary: lifecycle vocabulary the glossary itself was using undefined

Disposition, Ingest, Promotion, Staging, steering.md, Triage,
vocabulary - the PI-decision triple and pipeline stages, 11-34 docs
pages each.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: New entries — Board and delegation + Policy and audit sections

**Files:**
- Modify: `docs/reference/data-model/glossary.md`

**Interfaces:**
- Consumes: Task 2 format.
- Produces: the observability triple (Journal / Audit log / event_log) distinguished; Linter/Detector/Peer reviewer defined for the Verdicts table to lean on.

Eight entries: `Sweep` into Board and delegation; the other seven into Policy and audit, alphabetical positions.

- [ ] **Step 1: Add Sweep (Board and delegation)**

```markdown
### Sweep

A scheduled scan operation over the catalog or corpus that creates
request rows for the worker — how recurring checks enter the queue
without PI action. See [Sweeps](../pipelines-and-io/sweeps.md).
```

- [ ] **Step 2: Add the seven Policy and audit entries**

```markdown
### Actor Authority Guard

The enforcement mechanism that checks, on every state-changing call,
that the acting actor (`pi`, `agent`, `operation`, `integrity`) holds
authority for that change; unauthorized calls are refused, not logged
and allowed. See
[MCP transport](../commands-and-transports/mcp-transport.md).
```

```markdown
### Detector

One structural check inside the [Linter](#linter): deterministic, over
corpus structure only. The verdict band is a rollup over the detectors.
See [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md).
```

```markdown
### Empirical event

A typed telemetry/evidence payload recorded by operations into the
`event_log`; the payload roster and enums are specified in
[Empirical events](../control-and-policy/empirical-events.md). Distinct
from the [Audit log](#audit-log) (policy decisions) and the
[Journal](#journal) (synchronization export).
```

```markdown
### event_log

The SQLite table where empirical events land
(`src/memoria_vault/runtime/schema.sql`). One of three observability
trails: `event_log` records what operations observed, the
[Audit log](#audit-log) records what policy decided, and the
[Journal](#journal) exports state changes for synchronization. See
[Telemetry](../pipelines-and-io/telemetry.md).
```

```markdown
### Journal

The per-machine append-only JSONL export of engine state changes,
derived from SQLite for multi-machine synchronization and recovery —
reconstructible, never the source of truth. See
[Backup and recovery](../system/backup-and-recovery.md).
```

```markdown
### Linter

The deterministic structural detector suite over the corpus: it checks
structure (links, frontmatter, thresholds), never knowledge content,
and rolls its detectors up into the PASS / REVIEW / FAIL verdict band.
See [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md).
```

```markdown
### Peer reviewer

The prompt operation that reviews a candidate and emits the advisory
`agent_recommendation` verdict (`inconclusive` / `issues-found` /
`clean`); advisory only — the PI decides. See
[Prompt operations](../commands-and-transports/prompt-operations.md).
```

- [ ] **Step 3: Verify**

Run: `grep -c "^### " docs/reference/data-model/glossary.md`
Expected: 59.

Confirm the Verdicts table's setters ("Peer-reviewer", "Linter operation") now resolve to entries in the same file.

- [ ] **Step 4: Verify link targets exist** (same pattern as Task 6 Step 3, for the six pages referenced above).

- [ ] **Step 5: Lint and commit**

Run: `pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md`

```bash
git add docs/reference/data-model/glossary.md
git commit -m "glossary: Sweep plus the policy/analysis roster

Actor Authority Guard, Detector, Empirical event, event_log, Journal,
Linter, Peer reviewer - distinguishes the three observability trails
and defines both Verdicts-table setters.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: Close-out — full gate, anchor sweep, PR

**Files:**
- Read-only verification plus PR creation. No new edits unless a check fails.

- [ ] **Step 1: Full correctness gate**

Run: `python scripts/verify`
Expected: pass. If a docs gate fails, fix the flagged wording (gate wins) and amend the relevant commit.

- [ ] **Step 2: Full lint on every changed file**

```bash
git diff --name-only origin/main | xargs pre-commit run --hook-stage manual --files
```

Expected: all hooks pass.

- [ ] **Step 3: Anchor and link sweep**

Run: `grep -rn "glossary.md#" docs/ README.md AGENTS.md --include="*.md"`
Expected: every anchor in the output exists as a heading id in the glossary (auto-id = lowercase, spaces → hyphens, punctuation dropped; plus the pinned `open-knowledge-format-okf`).

Run: `grep -rn "Links vs work-graph edges\|Rail health band\|Extraction-uncertainty" docs/ --include="*.md" | grep -v superpowers | grep -v glossary.md`
Expected: no output (nothing links to deleted entry names). Fix any hit to point at the surviving entry.

- [ ] **Step 4: Fresh-eyes read of the final glossary**

Read `docs/reference/data-model/glossary.md` top to bottom once. Check: every entry is `###`; sections are internally alphabetical; no `**Term** —` paragraphs remain; no milestone codes; the Verdicts table is intact; total 59 entries.

- [ ] **Step 5: Push and open the PR**

```bash
git push -u origin HEAD
gh pr create --title "Glossary restructure: addressable entries, earned roster, 22 missing terms, CONTEXT.md stub" --body "$(cat <<'EOF'
## Summary
- Every glossary entry is now a ### heading with a stable kramdown anchor; sections stay, entries alphabetized within; per-term site search (search.heading_level: 3)
- Planned-surface micro-terms (Now, Places, Rail health band) fold into Navigator rail; Extraction-uncertainty flag's ruling moves into Work; Pattern folds into Operation; Ceiling covers both senses
- Milestone codes replaced by a plain Planned marker linking the roadmap (readiness lives in GitHub milestones)
- Enum rosters move to owning pages; links contrast becomes two addressable entries
- 22 new entries the docs already used undefined: Catalog, Grounding, memoria doctor, Provenance, Read API, Trusted writer, Disposition, Ingest, Promotion, Staging, steering.md, Triage, vocabulary, Sweep, Actor Authority Guard, Detector, Empirical event, event_log, Journal, Linter, Peer reviewer (+ link relation routing)
- Root CONTEXT.md: pointer stub replaces symlink (raw fetch, Windows checkouts, and lint perimeter all work now); AGENTS.md wording updated

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-review notes

- Spec coverage: every audit decision (4 PI answers + rethink-audit migrate steps + entry-audit verdicts) maps to a task: ordering → Task 2; milestone strip → Task 3; all-22 entries → Tasks 6–8 (21 headings + link-relation routing inside Task 5's split entries); stub swap → Task 1; Ceiling/Pattern/Home drift → Task 4; roster delink + split → Task 5.
- Entry-count arithmetic: 42 after Task 2 → 38 (Task 3) → 37 (Task 4) → 38 (Task 5) → 44 (Task 6) → 51 (Task 7) → 59 (Task 8).
- Anchors referenced across tasks are consistent: `#catalog`, `#trusted-writer`, `#promotion`, `#triage`, `#linter`, `#audit-log`, `#journal`, `#generated`, `#sources`, `#verified`, `#work-graph-edge` all exist as headings by the task that links them or earlier.
- Deliberate deviation from strict entry-format rule: merged entries (Navigator rail, Operation, Work) keep bold sub-terms (**Now**, **Places**, **Pattern**) in their bodies so Ctrl-F still finds the folded names.
