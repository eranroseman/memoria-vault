# Docs Migration (#1366) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the corpus's durable product doctrine into the published `docs/` Diátaxis tree (consolidation §5 routing map of record), then retire the six held working records — closing #1366 and completing the corpus fold.

**Architecture:** Docs-only. Unifies the subsumed `2026-07-11-foundations-reconcile` plan (Tasks 1–4 here, its prose reused with two dispositions updated) with the remaining §5 routings: three new explanation pages, targeted merges into architecture/knowledge/surfaces pages, one reference contract, and the final retirement. Each task edits few files, runs the gate, commits.

**Tech Stack:** Markdown (Jekyll / just-the-docs); gate is `python scripts/verify` (cspell + markdownlint cover `docs/` excluding `docs/superpowers/`).

Spec: consolidation §5 (`docs/superpowers/specs/2026-07-12-beta.1-consolidation.md`). Issue: #1366 (milestone `0.1.0-alpha.21`).

## Global Constraints

- **Gate:** `python scripts/verify` green before each commit batch.
- **Spelling:** American English; unknown terms go to `project-words.txt` (lowercase, sorted) — never inline-suppress.
- **Links:** relative links follow the target's Pages route (existing pages use `../../../reference/...` form — match depth per page). Never relative-link into `src/`.
- **No doctrine invention:** every added claim must already be stated in a corpus source (`product-statement.md`, `okf-note.md`, `user-workflow.md`, `autoresearch-note.md`, design §12). Do not add new positions.
- **Current-truth only:** pages describe the shipped system. Target-state behavior gets an explicit **Planned** marker naming its package (consolidation §2), or is deferred to that package's own PR (see Deferred routings at the end).
- **Retirement = deletion** (owner ruling 2026-07-12): retired files are removed, not banner-kept; git history is the archive. This supersedes the reconcile plan's banner approach.
- **Frozen:** never touch `design-history/`.
- Stage explicit paths only — never `git add -A`.

---

### Task 1: intellectual-foundations.md — four pillars

**Files:**
- Modify: `docs/explanation/rationale/foundations/intellectual-foundations.md`
- Modify: `project-words.txt`

*(Reused from the subsumed reconcile plan Task 1 — prose unchanged.)*

- [ ] **Step 1: Reframe the opener as four pillars.** Replace the first paragraph ("Memoria is built on four converging ideas…") with:

```markdown
Memoria stands on four pillars — each owning one layer with no overlap — and is
informed by a full review of ~400 papers spanning contemporary AI-research systems
and the HCI, extraction, evaluation, and retrieval traditions they build on:
**LLM-Wiki** (inflow), **Zettelkasten** (topology), **Toulmin** (logic), and
**autoresearch** (self-improvement). Understanding where the design comes from
makes it easier to understand why specific choices were made.
```

- [ ] **Step 2: Fold Memex into the LLM-Wiki section.** Append to the end of `## Karpathy's LLM-Wiki pattern`:

```markdown
The idea is related in spirit to Vannevar Bush's [Memex](../../../reference/evidence-and-integrations/bibliography.md#bush1945) (1945) — a personal, curated knowledge store with associative trails between documents. Bush's vision was closer to this than to what the web became: private, actively curated, with the connections between documents as valuable as the documents themselves. The part he couldn't solve was who does the maintenance. The LLM handles that.
```

- [ ] **Step 3: Remove the standalone `## Bush's Memex` section** (heading + paragraph) — its point now lives in Step 2 and the synthesis.

- [ ] **Step 4: Add the Toulmin section** after `## Luhmann's Zettelkasten` (before `## The literature review`):

```markdown
---

## Toulmin's argument model

Stephen Toulmin's model of argument (1958) gives the knowledge graph its logical basis. An argument decomposes into six roles — Claim, Grounds, Warrant, Backing, Qualifier, and Rebuttal — and Memoria makes those roles the *types* of the graph rather than leaving argument structure implicit in prose.

Typing the roles types the consequences: losing grounds, losing a warrant, a qualifier bounding a regression, and a rebuttal that strengthens when its target falls are different graph events with different blast radius. A graph that only stores "claim links to claim" cannot tell them apart; one that stores the Toulmin roles can. This is why Memoria assesses *grounding* rather than truth — the roles are the structure grounding is assessed against.
```

- [ ] **Step 5: Add the autoresearch section** immediately after:

```markdown
---

## The autoresearch loop

The fourth pillar is Karpathy's autoresearch framing — a fixed harness, one metric, keep-or-discard, run overnight — the self-improving trial-and-error loop that the contemporary [autoresearch systems](../../../reference/evidence-and-integrations/bibliography.md#liu2026autoresearchclaw) also pursue. Memoria applies it narrowly: to improve its *own instruments* — detectors, prompts, gates — by measuring a change against a frozen benchmark and keeping only what beats the bar.

The boundary is strict and load-bearing: autoresearch tunes the instruments that *assess* knowledge, never the knowledge itself. A self-improving loop pointed at the researcher's claims would optimize the vault toward whatever the metric rewards; pointed at the instruments, it sharpens the tools while the human keeps authorship of what they measure.
```

- [ ] **Step 6: Update `## The synthesis`** so the list reads:

```markdown
- The wiki is the compiled artifact, with its associative trails (Karpathy, after Bush's Memex).
- The document types preserve atomicity and lifespan distinction (Zettelkasten).
- The argument roles type the knowledge graph and its consequence propagation (Toulmin).
- The self-improvement loop sharpens Memoria's own instruments, never its knowledge (autoresearch).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that the earlier traditions required from the human.
```

Keep the synthesis *sentence* above the list in its current four-pillar form (already on `main`).

- [ ] **Step 7: project-words.txt** — ensure present (sorted, lowercase): `autoresearch`, `toulmin`, `rebuttal`, `qualifier`.

- [ ] **Step 8: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/rationale/foundations/intellectual-foundations.md project-words.txt
git commit -m "docs: intellectual-foundations — four pillars, Toulmin + autoresearch sections, Memex folded into LLM-Wiki"
```

---

### Task 2: what-memoria-is.md — OKF bundle constitution

**Files:**
- Modify: `docs/explanation/rationale/foundations/what-memoria-is.md`

*(Reused from reconcile plan Task 2.)*

- [ ] **Step 1: Insert after `## What Memoria is` (before `## What Memoria is not`):**

```markdown
---

## The bundle constitution

The vault — everything except `.memoria/` — is one self-contained **Knowledge Bundle** in the [Open Knowledge Format](../../../reference/data-model/glossary.md#open-knowledge-format-okf) sense: the unit of distribution, readable by anything with no Memoria present (`cat` works). Memoria is an opinionated OKF producer; `.memoria/` is engine-space — verdicts, provenance, queues, blobs: trust state *about* the knowledge, never the knowledge itself.

Each project is its own nested, detachable bundle: projects reference vault knowledge freely, permanent knowledge never links into a project, and project close harvests durable claims into the vault before the working bundle archives. The vault must live without its projects.
```

- [ ] **Step 2: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/rationale/foundations/what-memoria-is.md
git commit -m "docs: what-memoria-is — add the OKF bundle constitution"
```

---

### Task 3: design-principles.md — two axioms + the master pattern

**Files:**
- Modify: `docs/explanation/rationale/foundations/design-principles.md`

*(Reused from reconcile plan Task 3.)*

- [ ] **Step 1: Replace the opening** ("Ten principles that settle ambiguous decisions…") with:

```markdown
Twelve principles that settle ambiguous decisions. When a tool choice, workflow step, or architectural question is unclear, these are the tiebreakers.

Underneath them runs one master pattern: **the fluent, judging half of any capability stays with the human; the structural, inspectable half goes into the engine.** Truth/grounding, judgment/method, agent-loop/fenced-operation, and knowledge/trust-state are all this one cut — a design fork that resists resolution usually has not been cut along this line yet.
```

- [ ] **Step 2: Append principles 11 and 12** after principle 10 (before `## Related`):

```markdown
**11. Grounding, not truth.**

Memoria never reads a claim and asks whether it is true; it asks how the claim is grounded in evidence. No single node is judged true or false — the system asserts only how a change affects knowledge-graph integrity. "Checked" means required checks and warrants passed, never a truth verdict; dispositions record judgment events, they do not adjudicate content.

**12. Origin-blind consequences.**

The origin of a change — human, machine, or LLM — does not affect its *epistemic* consequences. When a claim is found wrong, the grounding consequences propagate across the graph identically whoever authored it; flags, demotions, and blast radius are origin-blind. Write and revert *authority*, by contrast, stays origin-gated: human-authored spans are never auto-destroyed, machine material auto-reverts. Origin is provenance, not authorization.
```

- [ ] **Step 3: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/rationale/foundations/design-principles.md
git commit -m "docs: design-principles — grounding-not-truth + origin-blind axioms, master pattern named (twelve)"
```

---

### Task 4: Glossary terms

**Files:**
- Modify: `docs/reference/data-model/glossary.md`
- Modify: `project-words.txt`

*(Reused from reconcile plan Task 5.)*

- [ ] **Step 1: Add to the appropriate domain section** (match the existing `**Term** — definition.` format; include the anchor Task 2's link targets):

```markdown
**<a id="open-knowledge-format-okf"></a>Open Knowledge Format (OKF)** — the plain-files bundle format Memoria produces: a self-contained, tool-agnostic Knowledge Bundle readable without Memoria present. The vault (excluding `.memoria/`) is one OKF bundle; each project is a nested one.

**Knowledge Bundle** — an OKF unit of distribution: the plain-file tree holding the researcher's knowledge, separable from the `.memoria/` engine state.

**Toulmin roles** — the six argument components (Claim, Grounds, Warrant, Backing, Qualifier, Rebuttal) that type the knowledge graph and its consequence propagation.

**autoresearch** — the self-improvement loop (fixed harness, one metric, keep-or-discard) applied to Memoria's own instruments — detectors, prompts, gates — never to the knowledge they assess.
```

- [ ] **Step 2:** ensure `okf` is in `project-words.txt` (lowercase, sorted).

- [ ] **Step 3: Gate + commit**

```bash
python scripts/verify
git add docs/reference/data-model/glossary.md project-words.txt
git commit -m "docs: glossary — OKF, Knowledge Bundle, Toulmin roles, autoresearch"
```

---

### Task 5: New page — consequence propagation

**Files:**
- Create: `docs/explanation/knowledge/consequence-propagation.md` (frontmatter: copy an existing `explanation/knowledge/` page's frontmatter shape — title, parent, nav order — and adapt)

- [ ] **Step 1: Write the page:**

```markdown
# Consequence propagation

Memoria's central operation is what happens *after* a change to the knowledge
base. Any change or addition — a new claim, an edited note, a new or changed
edge, a retracted source, a claim the researcher decides is wrong — has
consequences for everything grounded on it, and the graph's job is to make
those consequences visible instead of letting them rot silently.

## Typed blast radius

Because the graph carries [Toulmin roles](../rationale/foundations/intellectual-foundations.md),
the consequences are *typed*, not generic. When a node falls, its dependents
experience different events:

- **Grounds lost** — a claim's evidence went away; the claim stands unsupported.
- **Warrant lost** — the inference license connecting evidence to claim fell;
  every argument that license covered is affected at once.
- **Qualifier-bounded regression** — a hedged claim degrades only within its
  stated bounds.
- **Rebuttal strengthened** — a counter-argument gains force when its target
  weakens.

A graph that only stores "claim links to claim" cannot distinguish these; one
that stores the roles can route each dependent to the right disposition.

## Consequences are marked at write time

Derivation happens on write: the moment a change lands, its blast radius is
computed and affected nodes are marked — stale, under-warranted, needing
re-confirmation — so the knowledge base is always current and the researcher
gets immediate feedback. Reads may come weeks later; even hours of staleness
can mislead. Re-confirmation of impacted nodes is then *lazy and
impact-ranked*: marking is eager, re-verification effort follows the
researcher's attention to what matters.

## Origin-blind, authority-gated

Epistemic consequences are origin-blind: the blast radius of a wrong claim is
identical whether a human or a machine authored it. Write and revert
*authority* stays origin-gated — human-authored text is never auto-destroyed;
machine material can auto-revert. See
[Design principles](../rationale/foundations/design-principles.md), axioms 11–12.

## Related

- [Intellectual foundations](../rationale/foundations/intellectual-foundations.md) — the Toulmin pillar.
- [Knowledge cycle](knowledge-cycle.md) — where propagation sits in the daily loop.
- [Promotion and gated zones](promotion-and-gated-zones.md) — states, not places.
```

- [ ] **Step 2:** add the page to `docs/explanation/knowledge/README.md`'s index list (match its existing entry format).

- [ ] **Step 3: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/knowledge/consequence-propagation.md docs/explanation/knowledge/README.md
git commit -m "docs: new explanation page — consequence propagation (typed blast radius)"
```

---

### Task 6: New page — OKF and portability

**Files:**
- Create: `docs/explanation/architecture/okf-and-portability.md` (frontmatter per existing `architecture/` pages)

- [ ] **Step 1: Write the page:**

```markdown
# OKF and portability

Memoria's durability promise is structural: the knowledge outlives the tool.

## The vault is a bundle

Everything in the vault except `.memoria/` is one self-contained Knowledge
Bundle in the [Open Knowledge Format](../../reference/data-model/glossary.md#open-knowledge-format-okf):
plain Markdown, standard links, a generated `index.md`, and a
`bibliography.bib` companion. `cat` works. If Memoria is removed, the corpus,
notes, projects, and bibliography remain readable and editable with any tool.

`.memoria/` is engine-space: verdicts, provenance, queues, indexes, blobs —
trust state *about* the knowledge, never the knowledge itself. A bundle
copied without `.memoria/` loses its verdict state by design: trust is
re-derived, not transported.

## An opinionated producer

Memoria is a *strict producer* of OKF: its bundles are OKF-consumable, but
internally the files carry Memoria's typed frontmatter and conventions.
Export is a copy of the bundle folder — no transformation step. Import of a
foreign bundle takes the normal source-import path: content re-enters as
unchecked and earns its way through the gates like any other source.

## Nested project bundles

Each `projects/<slug>/` is itself a nested, detachable OKF bundle. Projects
may reference vault knowledge freely; permanent knowledge never links into a
project (the one-way rule that keeps projects detachable); project close
harvests durable claims back into the vault before the working bundle
archives.

## Related

- [What Memoria is](../rationale/foundations/what-memoria-is.md) — the bundle constitution.
- [The vault](vault.md) — bundle roots and layout.
- [Consistency model](consistency-model.md) — how files and engine state stay honest.
```

- [ ] **Step 2:** add to `docs/explanation/architecture/README.md`'s index.

- [ ] **Step 3: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/architecture/okf-and-portability.md docs/explanation/architecture/README.md
git commit -m "docs: new explanation page — OKF and portability"
```

---

### Task 7: New page — consistency model

**Files:**
- Create: `docs/explanation/architecture/consistency-model.md`

- [ ] **Step 1: Write the page:**

```markdown
# Consistency model

Memoria runs two planes with different guarantees, joined by a fail-closed
boundary.

## ACID trust plane

Judgment state — verdicts, provenance, the operation queue, the hash-chained
event log — lives in SQLite under `.memoria/`, with WAL, full synchronous
durability, CHECK constraints, and append-only triggers on the journal. What
the system asserts about trust is transactional: a verdict either committed
or it didn't.

## BASE knowledge plane

The knowledge itself is plain files, edited by the researcher with any tool
at any time. Files are eventually consistent with the engine's view of them:
an edit exists before the engine has scanned it.

## Fail-closed reads: eventual freshness, immediate honesty

The boundary is the read barrier, and it fails closed. When a file's hash
does not match its checked state — an unscanned edit, an unmaterialized
output — reads *deny* rather than serve stale trust: content is treated as
unchecked until the scan catches up. Freshness is eventual; honesty is
immediate. No consumer is ever told "checked" about bytes the checks never
saw.

## Cross-substrate operations

Operations that touch both planes (stage → validate → promote → journal →
git) run as an outbox-style sequence coordinated from SQLite, with
fail-closed recovery as the compensation path: after a crash, every
interrupted machine operation resolves to committed-and-consumable,
retryable-and-pending, or failed-and-hidden. No torn output is ever visible
as checked.

## Related

- [Memory model](memory-model.md) — which substrate owns which data.
- [OKF and portability](okf-and-portability.md) — why the planes are separate.
- [Failure modes](../../reference/system/failure-modes.md) — the recovery matrix.
```

Verify the `failure-modes.md` Related link path exists (`ls docs/reference/system/`); drop that line if absent.

- [ ] **Step 2:** add to `docs/explanation/architecture/README.md`'s index.

- [ ] **Step 3: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/architecture/consistency-model.md docs/explanation/architecture/README.md
git commit -m "docs: new explanation page — consistency model (ACID trust plane, BASE knowledge plane)"
```

---

### Task 8: Merges — vault.md + memory-model.md

**Files:**
- Modify: `docs/explanation/architecture/vault.md`
- Modify: `docs/explanation/architecture/memory-model.md`

- [ ] **Step 1: Read both pages fully** (they exist and carry structure this task must respect — insert, don't restructure).

- [ ] **Step 2: vault.md — add the three-spaces + one-way rule.** After its bundle-roots material, insert a short section (adapt heading level to the page):

```markdown
## Three spaces, one bundle

Catalog (works and sources), knowledge (notes, hubs, digests), and projects
are regions of one bundle, not separate stores. Each `projects/<slug>/` is a
nested, detachable bundle: projects reference vault knowledge freely, but
permanent knowledge never links into `projects/` — the one-way rule that
keeps a project removable without breaking the vault. Project close harvests
durable claims into the vault before the working bundle archives.
```

- [ ] **Step 3: memory-model.md — add the placement doctrine.** Insert where the page discusses substrate ownership:

```markdown
## The placement rule

Every datum has one home, chosen by who authored it: **authored** content
(notes, frontmatter, steering) lives in files — part of the bundle, portable;
**judged** state (verdicts, dispositions, provenance) lives in the database —
engine-space, re-derivable trust; **derived** values (counts, health,
saturation) are computed on read or projected one-way, never stored as if
authored. Files may never self-assert judgment (no verdict fields in
frontmatter), and any "both places" data must be a declared one-direction
projection — `bibliography.bib` from the catalog, `concept_edges` from
frontmatter links — so drift is detectable and one side is always authority.
```

- [ ] **Step 4: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/architecture/vault.md docs/explanation/architecture/memory-model.md
git commit -m "docs: vault + memory-model — three-spaces rule and the placement doctrine"
```

---

### Task 9: Merges — knowledge-cycle.md + surfaces/README.md; reference okf-compliance.md

**Files:**
- Modify: `docs/explanation/knowledge/knowledge-cycle.md`
- Modify: `docs/explanation/surfaces/README.md`
- Create: `docs/reference/data-model/okf-compliance.md`

- [ ] **Step 1: knowledge-cycle.md — add the inquiry-first arc.** Read the page; insert near its top-level narrative:

```markdown
## Pull, not push

The cycle is inquiry-first: a project opens with a question or thesis, gap
analysis runs over what the vault already holds *before* new reading, and
capture is pulled by identified gaps rather than pushed by whatever arrives.
Sources are admitted to the catalog freely, but nothing enters knowledge
until a project pulls it through digestion and judgment. At project close,
durable claims harvest back into the vault — each project leaves the
permanent knowledge richer than it found it.
```

- [ ] **Step 2: surfaces/README.md — add the division-of-labor model.** Read the page; insert:

```markdown
## The division of labor

Three surfaces, one envelope: the **editor** is where judgment happens — the
researcher reading, writing, and deciding in plain files; the **plugin** is an
ambient layer — status, inbox cards, one-click dispositions — that only
enqueues through the engine, never writes on its own; the **agent** is voice
and hands — it converses and files dispositions through the same operation
envelope with its true actor. A fourth, invisible role (the engine's own
jobs) validates and indexes behind them all. Every surface goes through the
same queue; none is a second authority.

Five jobs organize the work regardless of surface: Read, Knowledge, Project,
Review, and Upkeep. Deep work (compose, canvas, drafting) stays separate from
task work (inbox, review queues, maintenance) — the compose surface never
shows the recommendation stream. And the keep-test governs all of it: the
product must remain fully operable with `vim` and a file browser; every
deep-work artifact is a plain file; the plugin is never the only way in.
```

- [ ] **Step 3: Create `docs/reference/data-model/okf-compliance.md`:**

```markdown
# OKF compliance contract

What "the vault is an OKF bundle" requires of every file. Reference for the
conformance bar; the rationale lives in
[OKF and portability](../../explanation/architecture/okf-and-portability.md).

## The bar

- Every non-reserved `.md` file has parseable YAML frontmatter with a
  non-empty `type`.
- Reserved files (`index.md`, `log.md`) follow their reserved structure.
- Concept identity is path-derived; internal ids are producer metadata, not
  OKF identity.
- OKF-facing relationships and citations use standard Markdown links
  (bundle-relative); wikilinks remain a local authoring affordance.
- Verdicts and judgment state never appear in frontmatter — trust state is
  engine-space (`.memoria/`), not bundle content.
- Imported or copied OKF content re-enters as **unchecked** and earns its
  status through the normal gates; check states never travel in files.
- Export is a copy of the bundle folder (vault minus `.memoria/`), taken from
  a clean committed state, with no transformation step.

## Related

- [Frontmatter](frontmatter.md) — the per-type field contract.
- [Glossary](glossary.md#open-knowledge-format-okf) — OKF, Knowledge Bundle.
```

Add it to `docs/reference/data-model/README.md`'s index.

- [ ] **Step 4: Gate + commit**

```bash
python scripts/verify
git add docs/explanation/knowledge/knowledge-cycle.md docs/explanation/surfaces/README.md docs/reference/data-model/okf-compliance.md docs/reference/data-model/README.md
git commit -m "docs: inquiry-first cycle, surface division of labor, OKF compliance contract"
```

---

### Task 10: Retire the six held records + close #1366

**Files:**
- Delete: `docs/superpowers/product-statement.md`, `docs/superpowers/plans/okf-note.md`, `docs/superpowers/plans/user-workflow.md`, `docs/superpowers/plans/autoresearch-note.md`, `docs/superpowers/plans/2026-07-11-foundations-reconcile.md`, `docs/superpowers/specs/2026-07-11-foundations-reconcile-design.md`
- Modify: `docs/superpowers/README.md`, `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` (§7)

- [ ] **Step 1: Verify nothing published links into the retired files:** `rg -l "product-statement|okf-note|user-workflow|autoresearch-note|foundations-reconcile" docs/ --glob '!docs/superpowers/**'` — fix any hit before deleting.

- [ ] **Step 2: Delete the six files** (`git rm` each by explicit path).

- [ ] **Step 3: Update `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` §7:** change the "**Retire at #1366 close**" bullet to "**Retired <date>** (doc-worthy prose published via #1366): …same file list…". Update `docs/superpowers/README.md` if it names any retired file.

- [ ] **Step 4: Full gate, PR, merge**

```bash
python scripts/verify
git add <the explicit modified/deleted paths>
git commit -m "docs: retire the six migrated working records — corpus fold complete (closes #1366)"
gh pr create --title "docs: migrate corpus doctrine to published pages; retire the held records" --body "Executes the #1366 routing map (consolidation §5 + subsumed foundations-reconcile plan). Closes #1366."
```

Merge on green (`--squash --delete-branch`).

---

## Deferred routings (deliberate, with owners)

- **`reference/pipelines-and-io/srd.md`** — SRD contract page ships with package **C1** (documenting an unbuilt contract as reference invites drift; the contract is still a freeze blocker).
- **`reference/system/backup-and-recovery.md`** — ships with **PR-F3** (Foundation Task 9–11), documenting the real `workspace backup/restore` commands.
- **How-to staged-import guide** — ships with **O2** (`bulk-admission-mode` doesn't exist yet).
- **`search.md` retrieval deltas** — routing map found qma's architecture already landed there; deltas ride **R2/R3** PRs.
- **Compose/canvas/daemon how-to updates** — ride **W1/U3** when the behavior ships (current-truth rule).

## Self-Review

- **Spec coverage:** §5's six new pages → Tasks 5–7 + 9 deliver four; the remaining two (`srd.md`, `backup-and-recovery.md`) are explicitly deferred to their owning packages with rationale. All §5 merge targets covered (Tasks 1–4, 8–9) except deltas deferred above. Retirement + #1366 close → Task 10.
- **Placeholders:** every docs step carries the actual prose; the only investigate-first steps (Task 8/9 "read the page") are anchor-placement, with the inserted content given in full.
- **Consistency:** the glossary anchor `#open-knowledge-format-okf` (Task 4) matches links in Tasks 2, 6, 9; "twelve principles" (Task 3) matches axioms 11–12; retirement-as-deletion matches the 2026-07-12 owner ruling and supersedes the reconcile plan's banner approach; the warrant open question routes to `warrant-ontology-brief.md`, not the closed #1353.
