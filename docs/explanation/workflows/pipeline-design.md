---
topic: workflows
---

# Pipeline design

This document explains the *design* of Memoria's operational workflows: the two pipelines and their stages, why the Kanban is the substrate workflows are made of, who executes each stage (the role × stage matrices), and why the system has two pipelines rather than one.

For the *usage* side — the named-workflow inventory, how a human triggers work from the Command Palette, the research-directions steering file, the day-in-the-life cadence, and the anti-patterns — see the [how-to workflows README](../../how-to/workflows/README.md).

For each workflow, "owner" means *who has decision authority* — not just who executes. Hermes can execute many steps; the human owns the decisions that determine whether the work moves forward.

## The two pipelines

Memoria has two distinct pipelines. They share the vault but operate independently — most days the human works in one or the other, not both.

Both are **conditional paths, not fixed sequences.** A note or project advances only as far as its nature warrants: most sources never become claims, most claims never reach promotion, and stages like `discuss`, `revise`, and `archive` fire only when their precondition holds. The diagrams below show the *canonical* path. A `[bracketed]` stage (currently only `arrange`) is a **skippable intermediate** — one bypassed *mid-path* on an otherwise-complete pipeline, distinct from a stage a note simply never reaches.

### Upstream: source → durable knowledge

The upstream pipeline transforms raw sources into stable, well-linked claim notes ready to feed writing. It has nine stages:

```text
find ──► ingest ──► classify ──► discuss ──► distill ──► link ──► corroborate ──► promote ──► archive
```

| Stage | Goal | Primary owner | Output |
| --- | --- | --- | --- |
| **Find** | Find candidates worth adding to the corpus. | Librarian | `10-inbox/03-candidates/` |
| **Ingest** | Create the right paper note in the right folder with enrichment. | Librarian | `20-sources/01-papers/` (or items / entities) |
| **Classify** | Promote agent-proposed classification into canonical metadata. | Human | Paper note with `lifecycle: current` |
| **Discuss** | Read and think the paper note through via Socratic conversation. No artifact yet; the human's understanding sharpens. | Human (Socratic profile, write-denied) | A `discuss` card closes; the human is ready to distill |
| **Distill** | Distill the now-discussed source into 1–3 atomic claim notes. | Writer (human-authored) | `30-synthesis/01-claims/` with `maturity: seedling` |
| **Link** | Cross-reference the claim, add to MOC, link related claims. | Writer / human | Claim with `maturity: budding` |
| **Corroborate** | Multi-source support; well-linked; ready for canonization. | Human | Claim with `maturity: evergreen` |
| **Promote** | Move evergreen claim to the reference layer. | Human | `30-synthesis/02-reference/` (reference-note) |
| **Archive** | Preserve superseded material without deleting it. | Human | `95-archive/` |

**Note on stage granularity.** `find`, `ingest`, `classify`, `discuss`, `distill`, `promote`, and `archive` each correspond to a *named workflow* in the [inventory](../../how-to/workflows/README.md#workflow-inventory) (Find → Ingest → Classify → Discuss → Distill → Promote → Archive). `link` and `corroborate` are *maturity transitions* within the life of a claim note — they don't move files between folders, they just change `maturity` from `seedling` to `budding` to `evergreen`. The folder transitions happen at `promote`.

**Why `discuss` is a stage.** Making discussion board-visible is what answers "which paper notes have I actually thought about?" — a `discuss` card opens when classify completes and closes when the human writes a claim, so a pile-up is the signal that discussion is slipping. Full rationale in [Discuss](../../how-to/workflows/upstream/discuss.md#why-the-card-auto-closes-only-on-human-action).

### Downstream: knowledge → output

The downstream pipeline transforms stable claim notes into written deliverables. Seven stages, plus one skippable intermediate (`arrange`):

```text
assess ──► frame ──► [arrange] ──► outline ──► draft ──► verify ──► revise ──► export
```

| Stage | Goal | Primary owner | Output |
| --- | --- | --- | --- |
| **Assess** | Map the corpus for a project (what's ready, thin, missing) and decide whether to proceed or read more first. | Mapper (`scope-project`); human decides | `40-workbench/<project>/01-map/corpus-map.md` |
| **Frame** | Generate 2–3 competing project framings before drafting; choose one. | Writer (with `counter-outline`, scratch-only); Socratic (with `lens-reading`) for lens-based explorations | `40-workbench/<project>/02-framing/*.md` |
| **Arrange** *(optional)* | Arrange relevant claim notes spatially on a Canvas; identify gaps. | Human | `40-workbench/<project>/03-canvas/{section}.canvas` |
| **Outline** | Linearize the framing (and Canvas if used) into a heading scaffold. | Human (Writer-assisted) | Outline block in draft note |
| **Draft** | Write the prose with inline citekeys. | Human (Writer support) | `40-workbench/<project>/04-drafts/{chapter}.md` |
| **Verify** | Trace every substantive claim back to a claim note; flag unsupported claims. | Verifier; human decides per claim | `[!verification]` callout at top of draft + gap cards in upstream queue |
| **Revise** | Address verification findings; close the gap-loop or accept softened claims. | Human | Updated draft; closed `[!verification]` callout |
| **Export** | Run Pandoc to produce the final, frozen artifact (Word / PDF / HTML). | Coder (Pandoc); human decides to ship | `50-deliverables/` (the deliverable) |

The downstream pipeline is spread across [Write](../../how-to/workflows/downstream/write.md) (the umbrella) plus [Assess](../../how-to/workflows/downstream/assess.md), [Frame](../../how-to/workflows/downstream/frame.md), [Verify](../../how-to/workflows/downstream/verify.md), and [Revise](../../how-to/workflows/downstream/revise.md) for the new stages.

**Why assess and frame are stages.** Both judgments — "do I have what I need?" and "what argument am I making?" — happen anyway; making them stages turns them from private deliberation into board-visible work, so a card stalled in `assess` for two weeks is the same processing-debt diagnostic the upstream pipeline uses. Full rationale in [Assess](../../how-to/workflows/downstream/assess.md#why-not-skip-straight-to-drafting) and [Frame](../../how-to/workflows/downstream/frame.md#why-this-is-a-stage-and-not-a-pattern-inside-write).

**Why verify and revise are stages.** Promoting `cite-check` and the gap-loop to stages surfaces broken cites weeks before export instead of the day before — failed traces spawn upstream gap cards, and export is blocked until the `revise → re-verify` loop closes. Full rationale in [Verify](../../how-to/workflows/downstream/verify.md#why-verify-is-a-stage-instead-of-part-of-export) and [Revise](../../how-to/workflows/downstream/revise.md#why-revise-is-a-stage-instead-of-just-keep-editing).

**Arrange remains optional.** Arranging claims spatially on a Canvas is a useful step for chapter-sized work (8–15 claim notes). It bridges frame (which framing wins) and outline (linearize). For shorter pieces, framing leads directly into outline without it. See the [Canvas → Draft sub-workflow in Write](../../how-to/workflows/downstream/write.md#canvas--draft-sub-workflow).

### Maintenance (cross-cutting)

Maintenance runs continuously, not as part of either pipeline. It includes lint sweeps, merge / split / prune passes, and archival reviews. These produce reports and structural adjustments; they don't transform notes from one stage to another. (Session logging — the per-session audit trail every action writes — is a system *mechanism* rather than a workflow; it has no card and no state transitions. See [operations/session-logging.md](../operations/session-logging.md).)

### Lint is cross-cutting, not a stage

The pipeline diagrams above show *transforming* stages — each takes a note in one form and produces it in a new form. Lint does not fit this pattern. The Linter runs *against* every stage — schema checks during ingest, draft-block validation during classify, broken-link checks during distill, link-density and orphan checks before promote — but it produces **reports**, not new notes. It surfaces issues; it does not advance any single note's lifecycle.

See [Lint](../../how-to/workflows/maintenance/lint.md) for the operational details and weekly ritual; the Linter row in the [role × stage matrix](#role--stage-matrix) for per-stage behavior; and [profiles/linter.md](../profiles/linter.md) for the thresholds and auto-fix policy.

### Why two pipelines, not one

- **Different cadences.** Upstream runs daily (new sources arrive constantly); downstream runs per writing project (months apart).
- **Different artifacts.** Upstream produces knowledge (claim notes, reference notes); downstream produces documents (drafts, exports, deliverables).
- **Different judgment.** Upstream judgment is "is this true and worth filing?"; downstream judgment is "does this argument hold together?". Mixing them produces drafts that re-litigate filing decisions instead of building arguments.
- **Most sources never reach downstream.** Many paper notes provide supporting evidence (cited at the draft stage) without becoming the *originator* of a claim note. Knowing the upstream pipeline is independent of the downstream one makes this fine.

## The Kanban is the workflow's event bus

Workflows are not scripted procedures; they are **event sequences on the Kanban**. Each workflow describes which cards open, which profiles claim them, and which state transitions advance them. The board isn't storage that workflows happen to write to — it's the substrate workflows are *made of*. Three properties fall out of this:

- **Profiles don't call each other.** When Librarian finishes an ingest, it doesn't invoke Verifier; it sets the card's exit state. Verifier picks up cards in that state through the dispatcher (see [kanban-board/README.md dispatch interval](../kanban-board/README.md#dispatch-interval)). The handoff is the state change, not a message.
- **The human is one event source among several.** Human action via the [command palette](../../reference/command-catalog.md) creates cards. So do cron triggers (scheduled tasks), file-system watchers (PDF drops), and git hooks (draft commits). Each one is a card creation; the dispatcher routes them identically.
- **Workflows can be paused, resumed, or retried because the state is on the board.** A worker that fails mid-task leaves the card to be re-dispatched (returned to `ready`); the next dispatch picks it back up. A worker that succeeds completes the card to its exit state; the next workflow's trigger fires on that state change.

This is why the per-workflow `Card lifecycle` lines in each workflow file name explicit state transitions rather than function calls — workflows ARE state-machine paths, and reading them as paths makes the architecture's failure modes legible (a stuck card is a stuck workflow).

## Role × stage matrix

The matrix is split by pipeline. Upstream stages are human-pace and per-source; downstream stages are project-pace and per-deliverable. Two separate matrices keep each readable.

### Upstream

| Role | Find | Ingest | Classify | Discuss | Distill | Promote |
| --- | --- | --- | --- | --- | --- | --- |
| **Human** | Sets corpus boundary | Resolves ambiguity | **Lead** | Owns the thinking | Authors the claim | **Lead** |
| Librarian | **Lead** | **Lead** | Provides metadata | Read-only | Seed inputs only | Carry evidence forward |
| Mapper | Read-only | Read-only | Read-only | Comparative-brief on new sources | Read-only | Read-only |
| Socratic | No claim | No claim | No claim | **Lead** (human invokes; write-denied) | No claim | No claim |
| Writer | Reads context | Reads context | Reads context | No claim (human switches profiles) | **Lead** | Revise after review |
| Verifier | No claim | No claim | No claim | No claim | Filing-time similarity-check | Read-only |
| Linter | Structure check | Schema check | Dry-run validation | Surfaces stale discuss queue | Catch broken links | Gate before canon |

### Downstream

| Role | Assess | Frame | Outline | Draft | Verify | Revise | Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Human** | Decides readiness | Chooses the framing | Writes the outline | Writes the prose | Reviews findings | **Lead** | Decides to ship |
| Librarian | Source context | Read-only | Read-only | Read-only | Picks up gap cards | Read-only | Read-only |
| Mapper | **Lead** (via `scope-project`) | Read-only | Read-only | Read-only | Read-only | Read-only | Read-only |
| Socratic | No claim | Optional (human switches profiles) | No claim | No claim | No claim | No claim | No claim |
| Writer | Reads corpus map | **Lead** (via `counter-outline`, scratch-only) | **Lead** | **Lead** | Read-only (Verifier executes `cite-check`) | Revises (human-led) | Read-only |
| Verifier | Read-only | Read-only | Read-only | Read-only | **Lead** (cite-check, claim-trace) | Tracks open findings | Confirms verify-clean |
| Coder | No claim | No claim | No claim | No claim | No claim | No claim | **Lead** (runs Pandoc) |
| Linter | Validates corpus-map shape | Validates framing folder | Catch broken links | Catch broken links | Catch lingering findings | Catch unrevised flags | Validates export readiness |

**Reading the matrix.** **Lead** marks the single role that *executes* each stage — for Discuss, that's **Socratic** in the run-the-questioning sense, though the human owns the thinking itself. (This is deliberately distinct from the **Primary owner** column in the pipeline stage tables above, which names *decision authority* — for Discuss, the **Human**. A stage can have an agent Lead and a human owner.) The **Human** row is the person running the system: Lead for the stages no agent executes — Classify, Promote, and Revise — and elsewhere it names the judgment they keep while an agent runs the mechanics. The **Coder** appears downstream only (its work — running the Export pipeline — has no upstream counterpart).

Rule (both pipelines): **finding and filing** are Librarian work; **mapping the corpus** is Mapper work; **questioning without producing** is Socratic work; **durable writing and prose** are Writer work; **verifying claims trace** is Verifier work; **running the export pipeline** is Coder work; **structural safety and audit-trail housekeeping** are Linter work. The human owns the judgments — what counts as ready, which framing wins, whether a gap matters — that none of these profiles is allowed to make.

**Maintenance is cross-cutting, not a stage** — it's omitted from both matrices (see [Maintenance](#maintenance-cross-cutting)). The Linter is its primary owner; the Verifier runs the retraction sweep.

**No Orchestrator row.** Routing is encoded in lane-overrides and Kanban dispatch — see [profiles/README.md](../profiles/README.md#routing-without-an-orchestrator).

### Workflow ↔ stage mapping

Most workflows share a name with the pipeline stage they implement — Find, Ingest, Classify, Discuss, Distill, Promote, Archive (upstream) and Assess, Frame, Verify, Revise, Export (downstream) — so the shared name *is* the mapping. The exceptions:

- **`link` and `corroborate`** are *maturity transitions*, not workflows — they advance a claim note's `maturity` (`seedling` → `budding` → `evergreen`) without a named operation.
- **`arrange`, `outline`, and `draft`** have no standalone workflow; the **Write** umbrella owns them.
- **Zotero Capture** and **Fleeting Triage** are inbox-processing — they feed the pipeline but aren't stages on the `find → archive` spine.
- **Query** and **Code** are downstream *branch* workflows — off the main `assess → export` spine.
- **Lint**, **Refactor**, **Retraction Sweep**, and **Maintain MOCs** are *cross-cutting* maintenance, not pipeline stages.
