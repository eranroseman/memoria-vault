---
topic: explorations
title: Red-team findings — adversarial review of the redesign
status: exploration
created: 2026-06-10
parent: Design notes
grand_parent: Explanation
nav_order: 28
nav_exclude: true
---

# Red-team findings — adversarial review of the redesign

> **Status: exploration.** A six-pass adversarial review of the
> [redesign](memoria-redesign.md) + [system architecture](system-architecture.md) +
> [decisions](memoria-redesign-decisions.md), each pass attacking one load-bearing
> assumption (co-PI/delegation · the gates · engine/agent split · v0.2 scope · the unified
> model · the data model). The clear corrections are **applied**; the genuine decisions are
> **open** (below). Overall: the design is unusually self-aware — almost nothing is naïve;
> the gaps are that safeguards are mostly *informational / design-time* while the failure
> modes are *behavioral / runtime*.

## Sharpest result — four internal contradictions

1. **Transparency vs automation bias.** §8/D22 makes "hand the PI the **verdict**" the
   primary guard — but D35 says "handing a verdict **induces** automation bias." The
   primary guard ships the artifact the schema-decision warns against. *(High)*
2. **The biggest gate is the least protected.** §7's rule is "an item clearable without
   reading is a design smell" — yet §7 then **exempts** the high-cardinality batch
   worklist (the highest-volume keep/reject) as "the exception that proves the rule."
   *(High)*
3. **The layering contract was false for the key actors.** §1 said "each layer depends only
   on the one below" — but the PI edits the Vault directly, the co-PI reads it directly, and
   cron/CI/PI skip MCP. *(High — **fixed**: scoped to the agent write-path.)*
4. **D42 re-imported what D25 removed.** D25 kept *where* (layers) and *who* (actors)
   separate; D42 merged them, then re-annotated the table with actor-kinds. *(Med — **fixed**:
   3-actor cognitive headline restored, 7 layers as the build expansion.)*

## The five themes

- **A — Informational guards vs runtime failures (deepest).** Show-the-reasoning / "smell"
  rules / cron-Linter police *designers*, not the *operator at run time*. (Gates 1/2/3/5,
  data #1.) **High.**
- **B — Extraction/parameter uncertainty has no gate.** Entity-resolution, dedup,
  license/venue typing sit inside "mechanical" engines and write **ungated** Catalog;
  clustering params shape what the PI sees ("never decides" oversold). **High.**
- **C — Conversation forced into one-shot cards.** Drafting and interrogating a
  verification are conversational, but routed through fire-and-forget cards; the co-PI
  absorbs all continuity and is a single point of failure. **High (one) / Med (rest).**
- **D — "Designed" treated as "shipped"; big-bang risk.** Superseding ADR-01/04 entangles
  co-PI + Engines + MCP + Inbox + taxonomy + state + Linter at once; issues already closed
  "resolved-by-redesign" against an `exploration` doc; v0.2 milestone is doc-trivia under a
  major-version narrative. **High (delivery risk).**
- **E — The unify pass (D42) overshot.** 7-layer is implementation-flavored for a
  *cognitive* model; not strictly linear; dropped the who-axis that load-bears D28/D44.
  **Med — mostly fixed** (headline + scoped layering + MCP-as-boundary).

## Applied in this pass (clear corrections)

- **Layering scoped to the agent write-path**; PI/cron/CI are direct edges (redesign §2,
  system-architecture §1/§2) — fixes contradiction 3.
- **3-actor cognitive headline** ("you · your agents · your engines · the Vault") leads §2;
  the 7 layers are its build expansion — fixes contradiction 4 / Theme E.
- **MCP is a trust boundary, not a stratum everyone crosses** (system-architecture §2).
- **Linter = integrity *monitor*, not guarantor** (redesign §3.5) — it detects, doesn't
  block; a write-time gate is open (decision 2).
- **Clustering "decides *how to display*, never *what is canonical*"** and its parameters
  fall under the **calibration/drift spec** (redesign §4.3, §8) — Theme B (params).
- **Appendix F relabelled** "design-resolved, not built" (build-pending) — Theme D.

## Open decisions (options + pros/cons)

### 1 — The gate model (automation bias) · Theme A, contradictions 1–2 — **RESOLVED (D49)**

The original options rested on a false premise: **for a proposal the verdict is a given** —
the agent surfaced the item because it recommends it, so "accept" carries no information.
"Ship the verdict" (D22) is vacuous, and "blind-first on the verdict" hides a foregone
conclusion. **Resolution — honesty is the guard.** The proposal card presents, symmetrically:

| Field | |
|---|---|
| **Action** | what you'd be accepting |
| **Argument for** | the case to accept |
| **Argument against** | the agent's honest self-rebuttal — the strongest reason to reject |
| **What tipped it** | why *for* outweighed *against* (the deciding reason) |
| **Certainty** | calibrated confidence (3-level) — the loudness signal |

No verdict line (it's implied). The **against-case + certainty** are the real
anti-automation-bias levers. **Exception:** verification / adjudication items
(`clean`/`issues-found`/`inconclusive`; near-tie same/different/unsure) *do* carry a
non-given verdict — they **lead with the finding**. Keep **attention instrumentation**
(time-on-gate, accept-rate; sampled re-reviews) regardless, so the gate is measurable.

### 2 — Write-time integrity gate vs cron/CI monitor · Theme A, data #1

| Option | Pros | Cons |
|---|---|---|
| **A. Cron/CI only** (status quo) | simple; git-diffable drift; fits the engine model | between sweeps the Catalog serves broken records; fails-open if `type:` itself is corrupted |
| **B. Pre-commit `schema-check`** on changed files | a real gate on git-tracked writes; cheap | doesn't catch live in-app/plugin edits before commit |
| **C. Hybrid: pre-commit + an incremental file-watcher** | closes most of the window | a watcher is a daemon — the very thing the engine model avoids; complexity |

*Recommendation:* **A is honest for v0.2 ("monitor"); add B as a cheap win; defer C.**

### 3 — Extraction-uncertainty gate · Theme B

| Option | Pros | Cons |
|---|---|---|
| **A. Keep extraction ungated** (Catalog "not gated") | simple; relationships are mostly clean facts | confidently-wrong entity-merges / license / venue calls enter ungated |
| **B. Route low-confidence extraction (entity-resolution, dedup, license/venue) to a `flag`/near-tie card** | catches the fuzzy seam; reuses the existing gate; small | needs a confidence signal from the ingest engine; some false-positive flags |

*Recommendation:* **B — gate on *uncertainty*, not all extraction.** (Clustering-params drift already applied.)

### 4 — Conversational specialist work · Theme C

| Option | Pros | Cons |
|---|---|---|
| **A. One-shot delegated cards** (status quo) | clean propose-dispose; auditable | iterative draft / verify-interrogation → card-respawn churn; co-PI carries all continuity |
| **B. Conversational lane** — a card stays `running` and takes follow-up turns relayed by the co-PI; task-scoped composition memory | fits how drafting/verifying actually work; preserves specialist context; keeps one conversational front | more complex lane lifecycle; long-running lanes complicate WIP/board semantics |
| **C. Allow direct chats with a few specialists** (the option D26 deferred) | simplest UX for interrogation | reintroduces "who do I talk to?"; splits the learning loop |

*Recommendation:* **B — a conversational lane via the co-PI;** defer C.

### 5 — Sequencing / the big-bang risk · Theme D

| Option | Pros | Cons |
|---|---|---|
| **A. Big-bang cutover** | clean end-state | high risk; half-renamed vault; strands the running v0.1 |
| **B. Migration ADR + dependency DAG + atomic ADR clusters + `effective_from: vX.Y` + a v0.2 walking-skeleton** | incremental, de-risked; supersession dated to the *shipping* release | more upfront planning; slower |
| **C. Defer the whole redesign to a major version (v1.0); keep v0.2 = small as-built fixes** | honest (Appendix F already says "major-version-sized"); v0.2 ships cleanly | the redesign waits |

*Recommendation:* **B + C** — rename the architecture target to a major version, keep v0.2 small, write the migration ADR/DAG, add `effective_from`, and close **#198** with that scope.
