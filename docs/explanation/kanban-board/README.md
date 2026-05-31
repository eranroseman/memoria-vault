---
topic: board
---

> [!note] Status: Phase 1 (ships with v0.1).
> The board is the **Hermes-native Kanban** (`~/.hermes/kanban.db`), created at runtime by `hermes kanban` — not a file authored in the starter vault. Memoria adds the `metadata` review overlay (convention) and the read-only Dataview projections written by `.memoria/mcp/board_export.py` (shipped). The earlier "Phase 4" tag was a misclassification.

# Board, states, and the review gate

The Kanban board is Memoria's **control plane** — the shared state machine across profiles and sessions. Every long-lived piece of work lives on the board until a human approves it into the vault.

This document is the conceptual narrative: the dimensions a card carries, the life of a card end to end, how a card relates to a vault note, and why the human (not an agent) owns approval. For the operational reference see [states.md](states.md) (the full state machine, lanes, review-gate rules, WIP limits), [card-schema.md](card-schema.md) (the Hermes fields, the `metadata` overlay, the handoff payload), and [board-export.md](board-export.md) (*deferred, Phase 4* — how the board projects to `00-meta/board/` markdown, the `board-state.jsonl` snapshot, and the metrics aggregator the dashboards read). When a word here carries more than one sense — `review`, `verdict`, `promote`, `lane`, `canonical` — the [glossary](../../reference/glossary.md) pins which is meant.

## The two lifecycles, and the agent layer between them

A card carries three independent dimensions. Keeping them separate is the central design move of the board:

| Dimension | Field | Owner | Answers |
| --- | --- | --- | --- |
| **Execution** | `status` (Hermes built-in, fixed 7-value enum) | dispatcher + workers | *Where is the work?* (`triage → … → done → archived`) |
| **Review** | `metadata.review_status` (Memoria overlay) | the **human** | *Has the human accepted it as canonical?* |
| **Agent recommendation** | `metadata.agent_verdict` (Memoria overlay) | Verifier / Linter | *What does the checking agent advise?* |

Why three and not one:

- **`status` can't carry approval.** It's a fixed Hermes enum with no "human-approved" value, and the schema can't be extended. Overloading `done` to mean both "worker finished" *and* "human accepted" would erase the gate — and *worker-done is never canonical* is the entire point.
- **The agent recommendation is separate from the human decision** because they can disagree (an agent reports clean, the human rejects). Merging them would let an agent's view masquerade as the human's.

The review and agent dimensions only become meaningful once `status` reaches `done`; a `running` card is normally `review_status: unreviewed`. Full state machines and the field definitions: [states.md](states.md) and [card-schema.md](card-schema.md).

### Distinctions worth keeping

Several pairings look similar but are deliberately split:

- **`triage` vs `ready`** — specification vs dispatch. A `triage` card may lack an `assignee`, a `promote_target`, or a clear task; `hermes kanban specify` turns it into a spec, and a human *releases* it to `ready`.
- **`ready` vs `running`** — dispatch vs execution. Many cards can be `ready`; a profile holds one `running` card at a time.
- **`blocked` vs awaiting review** — `blocked` means the work itself can't proceed; a `done` card awaiting review is a check on completed work.
- **`rejected` vs auto-retry** — `rejected` is a *quality* decision (human-driven, exits via discard-or-supersede); a retry is an *execution* failure (dispatcher-driven, same card back to `ready`).
- **`approved` vs `archived`** — `approved` says "the work is good"; `archived` says "everything downstream has been handled."

## A card's life, end to end

1. **A trigger creates the card.** Human actions (command palette) create it in `triage` so the human can adjust the auto-filled fields; cron jobs and file/git watchers create it directly in `ready` (fully specified, fire-and-forget — the nightly hygiene sweep, the weekly drift detector, the `library.bib` watcher, and git-hook verify cards all skip `triage`).
   > Rule of thumb: **fully specified at creation → start at `ready`; a human still needs to shape it → start at `triage`.** The dispatcher ignores `triage` cards either way.
2. **Spec and release.** The human path for a hand-created card is **`triage` → (`hermes kanban specify`) → `todo` → (human releases) → `ready`**. From `ready` the dispatcher takes over.
3. **Dispatch and execution.** The dispatcher atomically claims a `ready` card whose `assignee` matches an available profile and spawns that profile → `running`. (Workers never self-claim.)
4. **Completion and agent check.** The worker finishes → `done`, writing a `summary` and `metadata`. If the card produced a checkable artifact, an agent attaches a recommendation in `metadata.agent_verdict` — Verifier on drafts, Linter on structural checks.
5. **Human review.** The human reads the work and sets `review_status` → `approved` (then `archived`) or `rejected`. The agent's verdict feeds this decision but never replaces it.

```text
Trigger ──► Specialist executes ──► Verifier / Linter recommendation ──► Human reviews
                                                                              │
                                                              ├─ approved ──► archived
                                                              │
                                                              └─ rejected ──► archived (superseded or discarded)
                                                                                  │
                                                                                  └─ (optional) new triage card with provenance
```

### Post-rejection paths

A `rejected` card is **not** "back to the worker" — the human has judged the work wrong, and what happens next is a fresh human decision:

| Path | What happens | Archive marker |
| --- | --- | --- |
| **Supersede** | The human spawns a new card on the same lane with a revised spec. The new card carries `metadata.supersedes: <original-id>`; the original is archived. The standard "revise and retry." | Original → `archived`, `archive_reason: superseded`. New card starts in `triage`. |
| **Discard** | The work shouldn't exist. Archived with no successor; the rejection is the answer. | `archived`, `archive_reason: discarded`. |

There is no implicit "return to lane queue" — every rework is a **new card with new specs**, which is more honest about revision (usually the original prompt was wrong, not just the output). This is distinct from a **retry**, which is automatic re-dispatch of the *same* card after a transient failure (see [Retry pattern](#retry-pattern)).

## Cards and notes

A natural question: does a card "start as a note type and output a note type"? Partly — but cards and notes are different kinds of thing:

- A **card is work** — transient, lives on the board, and **dies** (archived) when done.
- A **note is knowledge** — durable, lives in the vault, and persists.

A card typically **reads notes** (input paths in its handoff `allowed_paths`) and **writes notes** (its `metadata.promote_target` points at the output note — e.g. a `distill` card turns a paper-note into a claim-note). But it isn't universal: a lint card emits a report, a `scope` card emits a corpus-map, a verify card emits a callout. And a card has **no note type of its own** — card vocabulary (`status`, `review_status`) and note vocabulary (`lifecycle`, `maturity`, `type`) are deliberately **disjoint** (see [frontmatter-schema.md](../../reference/frontmatter-schema.md)). A card references notes by path; it never *is* one.

## Why no Reviewer and no Orchestrator

Memoria deliberately omits two roles that comparable multi-agent systems include:

- **No Reviewer profile.** Approval is a human action on `review_status`, gated by the policy MCP. Agents (Verifier, Linter) only *recommend* via `agent_verdict`; `metadata.review_owner` records who owes the next decision. The trade-off: the human is the bottleneck and review doesn't auto-scale — but no agent can self-approve or rubber-stamp work into canonical, which is the design's core guarantee (*bookkeeping, not intelligence*). The agent recommendation front-loads the judgment, and the review-queue WIP cap (below) is back-pressure that keeps the bottleneck from silently overflowing.
- **No Orchestrator profile.** Routing is static — encoded in lane-overrides and Kanban dispatch rules, not decided by a reasoning agent. See [profiles/README.md](../profiles/README.md#routing-without-an-orchestrator).

Because review is a human action and the dispatcher only spawns *profiles*, **review is not a lane** — there is no human "worker" for a review card to be assigned to, so the human gate rides on the card's `metadata` overlay instead of on a separate card. (Agent *checks*, by contrast, **are** cards: a Writer's commit fires a hook that creates a `verify` card for the Verifier.)

## Anti-patterns

- **Reaching canonical on worker say-so.** Always wait for `review_status` to change.
- **Creating a new card for a retry.** Reuse the card; Hermes re-dispatches it and tracks the retry in run history. (A *rejection*, by contrast, does start a new card — see [Post-rejection paths](#post-rejection-paths).)
- **Burying review status in comments.** If `review_status` is the source of truth, queries must use it; a comment saying "reviewed" is not review.
- **Unbounded lanes.** Without WIP limits the synthesis or review queue fills up and the human becomes the bottleneck without noticing.

## Operational notes

Reference detail for running the board; the conceptual model above doesn't depend on it.

### Persistence pattern

The board is where work memory lives across sessions and handoffs:

- **Same card, same identity** — a retry never creates a new card.
- **Session-safe** — closing the chat doesn't lose work; the card persists in `kanban.db`.
- **No chat-history dependence** — the next worker reads the card, not the transcript.
- **Visible until archived** — any non-terminal card is on the board.
- **Shared memory across roles** — the handoff `summary` + `metadata` is the API between profiles.

### Retry pattern

Failed work returns to `ready` for re-dispatch on the **same card**. The retry comment captures the **failure reason**, **what was tried**, and the **next action**. Hermes increments the retry count in run history; the same or a different profile can reclaim.

**Escalation threshold.** After `max_retries` (default `3`) recoverable failures, the dispatcher moves the card to `blocked` with `reason: "retry_threshold_exceeded"`. Three is the operating point — enough that transient failures (a rate-limited API, a flaky lookup) self-resolve, few enough that a structurally broken task doesn't tie up the lane all night. `max_retries` is per-lane configurable (the Librarian lane may tolerate `5` because retries are cheap; the Writer lane may want `2` because each retry is a model call); the dispatcher reads it from the task/lane config — no profile enforces it. A `blocked` card stays blocked until the human revises the handoff `metadata` and re-dispatches (resetting the count), fixes the cause out of band, or archives it with `reason: "infeasible"`. The counter never auto-decrements.

This guards against four failure modes: **duplicate cards** for the same work, **lost history** about why a task is hard, **silent give-up** (work vanishing without a trace), and — via the threshold — **budget burn** (a brittle prompt quietly consuming API budget overnight).

### Board implementation: Hermes built-in Kanban

Memoria uses the **Hermes built-in Kanban board** — once a board is adopted, this is mandated, not one option among several. (The board is part of Memoria v0.1 and ships from day one — see [roadmap/README.md](../../project/roadmap/README.md#memoria-v01); what's mandated here is *which* board.) Refs: [Kanban feature](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban) · [tutorial](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban-tutorial) · [worker lanes](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban-worker-lanes).

Why native: the architecture already assumes Hermes profiles, so a lane *is* a card's `assignee` with no bridging; worker-lane contracts, cross-session persistence (`kanban.db`), and retry semantics (`max_retries`) are built in; and the one thing Hermes lacks — a human review gate — layers cleanly onto `metadata` without forking the fixed schema.

#### Dispatch interval

The dispatcher polls every **60 seconds** (`dispatch_in_gateway: true`, `dispatch_interval_seconds: 60`) — the mandated Memoria setting, not a per-deployment default. Faster (e.g. 10s) wastes cycles polling mostly-empty queues; slower (e.g. 5 min) makes command-palette actions feel laggy. The cadence is what makes the board feel ambient — a dropped PDF is picked up within a minute. If one lane needs faster response, raise its cards' priority rather than tightening the global interval.

#### Per-task skill pinning (available, unused)

Hermes can attach extra skills to a single card — `kanban_create(..., skills=[…])` or `--skill` on the CLI — added to the spawned worker for that task only (additive to its profile's defaults). Memoria currently grants skills **per lane** (lane-overrides), not per task, so this lever is unused; it's the clean way to give a one-off card a capability outside its lane's default set. A pinned skill still runs under the lane's policy-MCP gate — it adds a capability, not write scope.

#### Alternatives considered, not adopted

| Alternative | Why not |
| --- | --- |
| Obsidian Kanban plugin (via [hermes-kanban](https://github.com/GumbyEnder/hermes-kanban) bridge) | Vault-native and markdown-portable, but bridges Hermes worker semantics to the plugin's data model — a translation layer between two state machines. |
| GitHub Projects | Strong for code workflows, but lives outside the vault and outside Hermes; board state would sit in a third place. |
| Linear | Cross-team strength is irrelevant for a single-user system. |
| Plain markdown + Dataview | Reimplements Kanban semantics the native board already provides. |

### What the board does not do

- **Not a knowledge store** — cards die; knowledge lives in the vault.
- **Not a chat log** — context goes into handoff summaries, not card history.
- **Not a home for canonical claims** — claims live in `30-synthesis/01-claims/`; the board references them.
- **Not a substitute for review** — `review_status: approved` is meaningful; an unset review state is not.
