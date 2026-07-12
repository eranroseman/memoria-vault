# Foundations Reconcile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the product statement's unpublished doctrine deltas into the three foundations pages, then retire the working record — no new page, no doctrine change.

**Architecture:** Docs-only edits to `docs/explanation/rationale/foundations/` + glossary + `project-words.txt`. Each task edits one file, runs the gate, and commits. No code, no tests.

**Tech Stack:** Markdown (Jekyll / just-the-docs), `python scripts/verify` (cspell + markdownlint over `docs/`, excluding `docs/superpowers/`).

## Global Constraints

- **Gate:** `python scripts/verify` must stay green. The relevant checks for these files are `cspell` and `markdownlint` over `docs/`.
- **Spelling:** American English; every unknown term must be added to `project-words.txt` (one lowercase word per line, kept sorted) — never inline-suppress.
- **Links:** inside `docs/`, relative links follow the target's Pages route (the existing pages use `../../../reference/...` form — match it). Never relative-link into `src/`. Link the retired open-question to the GitHub issue URL.
- **No doctrine invention:** every added claim is already stated in `docs/superpowers/product-statement.md`. Do not add new positions.
- **Frozen:** do not touch `design-history/`.

---

### Task 1: intellectual-foundations.md — four pillars (fold Memex, add Toulmin + autoresearch)

**Files:**
- Modify: `docs/explanation/rationale/foundations/intellectual-foundations.md`

- [ ] **Step 1: Reframe the opener as four pillars**

Replace the first paragraph ("Memoria is built on four converging ideas and informed by a full review of ~400 papers…") so the four pillars are named:

```markdown
Memoria stands on four pillars — each owning one layer with no overlap — and is
informed by a full review of ~400 papers spanning contemporary AI-research systems
and the HCI, extraction, evaluation, and retrieval traditions they build on:
**LLM-Wiki** (inflow), **Zettelkasten** (topology), **Toulmin** (logic), and
**autoresearch** (self-improvement). Understanding where the design comes from
makes it easier to understand why specific choices were made.
```

- [ ] **Step 2: Fold Memex into the LLM-Wiki section**

Append this paragraph to the end of the `## Karpathy's LLM-Wiki pattern` section (using the owner's framing):

```markdown
The idea is related in spirit to Vannevar Bush's [Memex](../../../reference/evidence-and-integrations/bibliography.md#bush1945) (1945) — a personal, curated knowledge store with associative trails between documents. Bush's vision was closer to this than to what the web became: private, actively curated, with the connections between documents as valuable as the documents themselves. The part he couldn't solve was who does the maintenance. The LLM handles that.
```

- [ ] **Step 3: Remove the standalone Memex section**

Delete the entire `## Bush's Memex` section (heading + its paragraph). Its associative-trails point now lives inside the LLM-Wiki section (Step 2) and in the synthesis (Step 6).

- [ ] **Step 4: Add the Toulmin section**

Insert after `## Luhmann's Zettelkasten` (before `## The literature review`):

```markdown
---

## Toulmin's argument model

Stephen Toulmin's model of argument (1958) gives the knowledge graph its logical basis. An argument decomposes into six roles — Claim, Grounds, Warrant, Backing, Qualifier, and Rebuttal — and Memoria makes those roles the *types* of the graph rather than leaving argument structure implicit in prose.

Typing the roles types the consequences: losing grounds, losing a warrant, a qualifier bounding a regression, and a rebuttal that strengthens when its target falls are different graph events with different blast radius. A graph that only stores "claim links to claim" cannot tell them apart; one that stores the Toulmin roles can. This is why Memoria assesses *grounding* rather than truth — the roles are the structure grounding is assessed against.
```

- [ ] **Step 5: Add the autoresearch section**

Insert immediately after the Toulmin section:

```markdown
---

## The autoresearch loop

The fourth pillar is Karpathy's autoresearch framing — a fixed harness, one metric, keep-or-discard, run overnight — the self-improving trial-and-error loop that the contemporary [autoresearch systems](../../../reference/evidence-and-integrations/bibliography.md#liu2026autoresearchclaw) also pursue. Memoria applies it narrowly: to improve its *own instruments* — detectors, prompts, gates — by measuring a change against a frozen benchmark and keeping only what beats the bar.

The boundary is strict and load-bearing: autoresearch tunes the instruments that *assess* knowledge, never the knowledge itself. A self-improving loop pointed at the researcher's claims would optimize the vault toward whatever the metric rewards; pointed at the instruments, it sharpens the tools while the human keeps authorship of what they measure.
```

- [ ] **Step 6: Update the synthesis section**

In `## The synthesis`, replace the Memex bullet and add the two new pillars so the list reads:

```markdown
- The wiki is the compiled artifact, with its associative trails (Karpathy, after Bush's Memex).
- The document types preserve atomicity and lifespan distinction (Zettelkasten).
- The argument roles type the knowledge graph and its consequence propagation (Toulmin).
- The self-improvement loop sharpens Memoria's own instruments, never its knowledge (autoresearch).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that the earlier traditions required from the human.
```

- [ ] **Step 7: Add new terms to project-words.txt**

Add (sorted, lowercase): `autoresearch` (verify present — it may already be there), `toulmin`, `rebuttal`, `qualifier`. Grounds/Warrant/Backing/Claim are ordinary words.

- [ ] **Step 8: Run the gate on the changed docs**

Run: `python scripts/verify`
Expected: `verify: OK` (cspell + markdownlint pass on the edited page).

- [ ] **Step 9: Commit**

```bash
git add docs/explanation/rationale/foundations/intellectual-foundations.md project-words.txt
git commit -m "docs: intellectual-foundations — name four pillars, add Toulmin + autoresearch, fold Memex into LLM-Wiki"
```

---

### Task 2: what-memoria-is.md — OKF bundle constitution

**Files:**
- Modify: `docs/explanation/rationale/foundations/what-memoria-is.md`

- [ ] **Step 1: Add the OKF section**

Insert a new section after `## What Memoria is` (before `## What Memoria is not`):

```markdown
---

## The bundle constitution

The vault — everything except `.memoria/` — is one self-contained **Knowledge Bundle** in the [Open Knowledge Format](../../../reference/data-model/glossary.md#open-knowledge-format-okf) sense: the unit of distribution, readable by anything with no Memoria present (`cat` works). Memoria is an opinionated OKF producer; `.memoria/` is engine-space — verdicts, provenance, queues, blobs: trust state *about* the knowledge, never the knowledge itself.

Each project is its own nested, detachable bundle: projects reference vault knowledge freely, permanent knowledge never links into a project, and project close harvests durable claims into the vault before the working bundle archives. The vault must live without its projects.
```

- [ ] **Step 2: Add the glossary anchor link target** (handled in Task 5 — the link above points at `glossary.md#open-knowledge-format-okf`).

- [ ] **Step 3: Run the gate**

Run: `python scripts/verify`
Expected: `verify: OK`.

- [ ] **Step 4: Commit**

```bash
git add docs/explanation/rationale/foundations/what-memoria-is.md
git commit -m "docs: what-memoria-is — add the OKF bundle constitution"
```

---

### Task 3: design-principles.md — two axioms + the master pattern

**Files:**
- Modify: `docs/explanation/rationale/foundations/design-principles.md`

- [ ] **Step 1: Retitle and name the master pattern in the intro**

Change the heading count and intro. Replace the opening ("Ten principles that settle ambiguous decisions…") with:

```markdown
Twelve principles that settle ambiguous decisions. When a tool choice, workflow step, or architectural question is unclear, these are the tiebreakers.

Underneath them runs one master pattern: **the fluent, judging half of any capability stays with the human; the structural, inspectable half goes into the engine.** Truth/grounding, judgment/method, agent-loop/fenced-operation, and knowledge/trust-state are all this one cut — a design fork that resists resolution usually has not been cut along this line yet.
```

- [ ] **Step 2: Add principles 11 and 12**

Append after principle **10. The engine owns the workflow.** (before the `---` / `## Related`):

```markdown
**11. Grounding, not truth.**

Memoria never reads a claim and asks whether it is true; it asks how the claim is grounded in evidence. No single node is judged true or false — the system asserts only how a change affects knowledge-graph integrity. "Checked" means required checks and warrants passed, never a truth verdict; dispositions record judgment events, they do not adjudicate content.

**12. Origin-blind consequences.**

The origin of a change — human, machine, or LLM — does not affect its *epistemic* consequences. When a claim is found wrong, the grounding consequences propagate across the graph identically whoever authored it; flags, demotions, and blast radius are origin-blind. Write and revert *authority*, by contrast, stays origin-gated: human-authored spans are never auto-destroyed, machine material auto-reverts. Origin is provenance, not authorization.
```

- [ ] **Step 3: Run the gate**

Run: `python scripts/verify`
Expected: `verify: OK`.

- [ ] **Step 4: Commit**

```bash
git add docs/explanation/rationale/foundations/design-principles.md
git commit -m "docs: design-principles — add grounding-not-truth + origin-blind axioms, name the master pattern (twelve)"
```

---

### Task 4: Retire product-statement.md

**Files:**
- Modify: `docs/superpowers/product-statement.md`

- [ ] **Step 1: Prepend a superseded banner**

Insert at the very top of the file (above the existing `# Memoria — product statement…` title):

```markdown
> **Superseded (2026-07-11).** This working record's canonical doctrine now lives
> in the published foundations pages — [What Memoria is](../explanation/rationale/foundations/what-memoria-is.md),
> [Intellectual foundations](../explanation/rationale/foundations/intellectual-foundations.md),
> and [Design principles](../explanation/rationale/foundations/design-principles.md).
> Kept as the dated 2026-07-09 composition. The one open item, warrant ontology,
> is tracked in [issue #1353](https://github.com/eranroseman/memoria-vault/issues/1353).

```

- [ ] **Step 2: Confirm docs/superpowers/ is gate-excluded**

`docs/superpowers/` is excluded from cspell, markdownlint, and the checked-terminology gate, so this file needs no spelling additions. Run `python scripts/verify` to confirm nothing regressed.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/product-statement.md
git commit -m "docs: retire product-statement — superseded by the foundations pages"
```

---

### Task 5: Glossary terms + Related plumbing

**Files:**
- Modify: `docs/reference/data-model/glossary.md`
- Modify: the three foundations pages' `## Related` sections (if a link changed)

- [ ] **Step 1: Add glossary terms**

Add to the appropriate domain section of `glossary.md` (match the `**Term** — definition.` format), including the `<a id>` anchors the `what-memoria-is.md` OKF link targets:

```markdown
**<a id="open-knowledge-format-okf"></a>Open Knowledge Format (OKF)** — the plain-files bundle format Memoria produces: a self-contained, tool-agnostic Knowledge Bundle readable without Memoria present. The vault (excluding `.memoria/`) is one OKF bundle; each project is a nested one.

**Knowledge Bundle** — an OKF unit of distribution: the plain-file tree holding the researcher's knowledge, separable from the `.memoria/` engine state.

**Toulmin roles** — the six argument components (Claim, Grounds, Warrant, Backing, Qualifier, Rebuttal) that type the knowledge graph and its consequence propagation.

**autoresearch** — the self-improvement loop (fixed harness, one metric, keep-or-discard) applied to Memoria's own instruments — detectors, prompts, gates — never to the knowledge they assess.
```

- [ ] **Step 2: Fix Related links**

In `intellectual-foundations.md` `## Related`, no link change is required (Memex folded in-page). Verify the three pages still cross-link each other correctly after the edits; fix any anchor that moved.

- [ ] **Step 3: Add glossary jargon to project-words.txt**

Ensure `okf` is present (lowercase, sorted). `toulmin`/`autoresearch`/`rebuttal`/`qualifier` added in Task 1.

- [ ] **Step 4: Run the gate**

Run: `python scripts/verify`
Expected: `verify: OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/data-model/glossary.md project-words.txt
git commit -m "docs: glossary — define OKF, Knowledge Bundle, Toulmin roles, autoresearch"
```

---

### Task 6: Final gate + PR

- [ ] **Step 1: Full verify from the worktree**

Run: `python scripts/verify`
Expected: `verify: OK` (all lint, product gates, tests, smoke — the docs edits only touch cspell/markdownlint).

- [ ] **Step 2: Push and open PR**

```bash
git push -u origin feat/reconcile-foundations
gh pr create --base main --title "docs: reconcile product-statement doctrine into the foundations pages" --fill
```

- [ ] **Step 3: Merge when verify + gitleaks green**

```bash
gh pr merge <n> --squash --delete-branch
```

- [ ] **Step 4: Finish** — remove the worktree, sync main (finishing-a-development-branch skill).

## Self-Review

- **Spec coverage:** intellectual-foundations (Task 1) ✓, what-memoria-is/OKF (Task 2) ✓, design-principles axioms + master pattern (Task 3) ✓, product-statement retire + warrant→#1353 (Task 4) ✓, glossary + project-words + Related (Task 5) ✓, verify + PR (Task 6) ✓. No spec requirement unassigned.
- **Placeholders:** none — every doc step contains the actual prose to transcribe.
- **Consistency:** the OKF glossary anchor `#open-knowledge-format-okf` defined in Task 5 matches the link written in Task 2; "twelve" in Task 3 intro matches principles 11–12.
