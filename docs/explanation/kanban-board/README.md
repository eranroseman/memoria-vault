
# The Kanban board

The Kanban board is Memoria's **control plane** — the shared state machine that tracks every piece of in-progress work across profiles and sessions. Every meaningful operation produces a card that lives on the board until a human approves it into the vault, fails it, or decides it shouldn't exist. Nothing becomes canonical without passing through the board.

---

## The three dimensions

A card carries three independent dimensions, and keeping them separate is the central design move of the board:

| Dimension | Field | Owner | Answers |
| --- | --- | --- | --- |
| **Execution** | `status` — Hermes built-in enum | Dispatcher + workers | *Where is the work?* |
| **Review** | `metadata.review_status` — Memoria overlay | The human | *Has the human accepted this as canonical?* |
| **Agent recommendation** | `metadata.agent_recommendation` — Memoria overlay | Verifier or Linter | *What does the checking agent advise?* |

**Why three dimensions, not one?** `status` is a fixed Hermes enum with no "human-approved" value — Memoria cannot extend it. Overloading `done` to mean both "worker finished" and "human accepted" would erase the review gate. And the agent recommendation must be separate from the human decision because they can legitimately disagree: an agent may recommend approval while the human rejects, or vice versa. Merging them would let an agent's view masquerade as a human judgment.

---

## A card's life

Every card follows the same arc:

1. **Created** by a trigger: a command-palette action, a cron job, or a file-watcher event. Human-initiated cards start in `triage` (spec not yet finalized); automated cards start directly in `ready`.
2. **Specified and released.** A `triage` card waits for the human to shape its spec and release it to `ready`. Automated cards skip this step entirely.
3. **Dispatched.** The dispatcher atomically claims a `ready` card matching an available profile and moves it to `running`.
4. **Completed.** The worker finishes its slice, moves the card to `done`, and writes a handoff summary plus structured metadata. If the card produced a checkable artifact, Verifier or Linter attaches a recommendation in `agent_recommendation`.
5. **Human review.** The human reads the output, and either approves (then archives) or rejects (then archives with a reason, and optionally spawns a successor card).

The worker reaching `done` is not the same as the work being accepted. That distinction — execution state versus review state — is the whole reason these dimensions are kept separate.

---

## Cards and notes are different kinds of thing

A **card is work** — transient, board-resident, and archived when done. A **note is knowledge** — durable, vault-resident, and persists indefinitely. A card typically reads notes (its handoff specifies which paths) and produces notes (its `promote_target` points at the output). But these are not the same object: card vocabulary (`status`, `review_status`) and note vocabulary (`lifecycle`, `maturity`, `type`) are deliberately disjoint. A note never carries board fields; a card never carries note fields.

---

## Why no Reviewer and no Orchestrator

**No Reviewer profile.** Review is a human action on `metadata.review_status`, enforced by the policy MCP. Agents only *recommend* via `agent_recommendation`; no profile can self-approve or rubber-stamp work into canonical. The consequence is that the human is the review bottleneck — but that is the design's core guarantee. An unbounded review queue is made visible by the review-queue WIP cap, which applies back-pressure before the backlog becomes invisible.

**No Orchestrator profile.** Routing is encoded in lane-override files and Kanban dispatch rules, not decided by a reasoning agent. Once a reasoning orchestrator exists, every routing decision becomes hard to audit and potentially self-modifying. Routing by rule is less flexible but far more trustworthy.

---

## Post-rejection paths

A rejected card is not "back to the worker." The human has judged the work wrong, and what happens next is a deliberate choice:

- **Supersede** — spawn a new card with a revised spec. The new card carries a reference to the original; the original is archived as `superseded`. This is the standard "revise and retry."
- **Discard** — the work shouldn't exist. Archive the card as `discarded` with no successor.

There is no implicit return to the queue. Every rework is a new card with a new spec — which is more honest about what revision actually is. Usually the original prompt was wrong, not just the output.

---

## What the board does not do

- **Not a knowledge store.** Cards die; knowledge lives in the vault.
- **Not a chat log.** Context travels in handoff summaries, not card history or conversation transcripts.
- **Not a home for canonical claims.** Claims live in `30-synthesis/01-claims/`; the board references them by path.
- **Not a substitute for review.** `review_status: approved` is meaningful; a comment saying "looks fine" is not.

---

## How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Dataview cannot query directly. Two read-only projections bridge the gap.

**Board export → `00-meta/board/`** — a `board_export.py` job writes each live card to a markdown file on a **~60-second cadence** (matching the dispatcher's tick, so the projection never lags the board by more than one cycle). The [board-state dashboard](../dashboards/board-state.md) reads these files via Dataview. Each file carries the queryable fields in frontmatter (`task_id`, `status`, `assignee`, `review_status`, `retry_count`) plus the human-readable handoff summary in the body.

**Board-state snapshot → `board-state.jsonl`** — the same ~60s pass appends a compact JSONL line with per-lane running/ready/blocked counts and review-queue depth. The status-line widget reads this instead of re-querying the database, keeping its refresh lightweight.

The projections are one-way and ephemeral: editing a projected markdown file does nothing to the board. The projections are regenerated on each pass; any manual edit is overwritten. The board stays authoritative; the markdown is a read view.

A scheduled metrics aggregator rolls run history into `00-meta/08-metrics/` notes for the fleet-health dashboard's trust score. It activates meaningfully only once the system has accumulated real weekly volume.

---

## Related

**Explanation**

- State machine detail: [states.md](states.md)
- Schema design: [card-schema.md](card-schema.md)
- Dashboard that reads the board export: [dashboards/board-state](../dashboards/board-state.md)
- Why review is structural: [architecture/why-human-gate](../architecture/why-human-gate.md)
- Profiles that interact with the board: [profiles/README.md](../profiles/README.md)
- Pipelines that run on the board: [workflows/README.md](../workflows/README.md)
- The board as control plane: [why-three-layers.md](../architecture/why-three-layers.md)
