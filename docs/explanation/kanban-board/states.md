---
topic: board
---

> [!warning] Status: Deferred (Phase 4)
> The Kanban board does not exist in the starter vault. This document describes the planned design. See `board-export.md` for implementation notes.

# Why the board states are shaped this way

This page is the *design* narrative behind the board's state machine: why execution and review are two separate lifecycles, the transition rules and their rationale, what each lane's exit contract guarantees, the dispatch-interval reasoning, and why the WIP limits are set where they are.

For the bare lookup — the `status` enum and its transitions, the `review_status` enum, the lane-assignment table, escalation thresholds, and the WIP-cap table — see [the board-states reference](../../reference/board-states.md).

The board tracks **three card dimensions** (two execution/review lifecycles plus agent recommendation):

1. **Execution** — the Hermes built-in `status` field, a fixed seven-value enum. This is what the dispatcher and workers move.
2. **Review** — a Memoria overlay stored in `metadata.review_status` (plus `metadata.agent_verdict`). Hermes has no review gate, so Memoria layers one on. It rides on top of `status: done`.

Keeping them separate is what lets `status` hold real Hermes values while Memoria's approval semantics live where Hermes has a slot for them (the free-form `metadata` JSON). For the field definitions see [card-schema.md](card-schema.md); for the conceptual narrative see [README.md](README.md); for term disambiguation see the [glossary](../../reference/glossary.md).

## Execution lifecycle (Hermes `status`)

The state diagram lives with the full enum in the [board-states reference](../../reference/board-states.md#execution-lifecycle-hermes-status).

The lifecycle is deliberately linear with two escape edges. `triage → todo` exists so a card is never dispatched before its spec is concrete — the dispatcher ignores `triage`, which is what makes "specify before release" enforceable rather than advisory. The `todo → ready` release is a separate human act because there is no orchestrator deciding when work starts: [routing lives in lane-overrides + dispatch rules](../profiles/README.md#routing-without-an-orchestrator), and a human releasing the spec is the deliberate "go" signal.

The two escape edges handle the failure and the wait. **Retries are not a distinct status** — a recoverable run failure (`outcome: crashed` or `gave_up`, within `max_retries`) returns the card to `ready` for re-dispatch, so a transient failure looks like a re-queue rather than a new state to reason about. The `blocked` edge is for failures a worker *cannot* recover from alone: it carries a `reason`, and only a human clears it back to `ready`. The full enum, with who moves each transition, is in the [reference status table](../../reference/board-states.md#execution-lifecycle-hermes-status).

Board `status` values and note-vocabulary values are kept disjoint — Hermes `triage` does not collide with the note `draft` type — so the board needs no special state name to avoid overlap. See [frontmatter-schema.md](../../reference/frontmatter-schema.md).

## Review lifecycle (Memoria overlay, `metadata.review_status`)

```text
unreviewed ──► requested ──► in-review ──► approved   (canonical; then archived)
                                       └─► rejected   (then archived = discarded, or new card = superseded)
```

The review lifecycle only becomes meaningful once `status` reaches `done`. A card can be `status: running` with `review_status: unreviewed` — that is the normal mid-flight state, and keeping the two dimensions orthogonal is what lets a worker make progress without implying anything about acceptance. The enum values are tabulated in the [reference review table](../../reference/board-states.md#review-lifecycle-memoria-overlay).

## Worker lanes and the exit contract

Lanes are specialist execution paths under the board. A lane **is** an `assignee` value — the dispatcher routes a card to a lane by matching `task.assignee` to a Hermes profile (or a registered external worker). There is no separate `lane` field; tasks with an unresolved `assignee` stay in `ready` with a `skipped_nonspawnable` event (a Hermes dispatch event meaning no worker matched the `assignee`).

Every lane exits to `status: done`; what differs is what "done" means and which review signal applies. **The exit contract is how the board enforces that nobody self-approves** — reaching `done` is not the same as `review_status: approved`. That distinction is the whole reason the two lifecycles are separate: a Librarian or Writer can declare its own slice finished, but "finished" routes to a human review signal (`review_status: requested`) rather than to canonical. The Verifier and Linter lanes instead deposit an `agent_verdict`, because their job *is* to judge — but even that verdict is a recommendation, not an acceptance. The per-lane exit signals are listed in the [reference lane-assignment table](../../reference/board-states.md#lane-assignments-and-exit-signals).

**Socratic is not a board lane.** It runs synchronously through the ACP pane — the human opens it, converses, and closes it. It never appears on the board, claims a card, or produces a `done` card; it has no card lifecycle. (It's a profile, just not a board-dispatched one.)

There is no Review lane and no Orchestration lane either. Approval is a human action on `metadata.review_status`, gated by the policy MCP — no profile owns it; routing is encoded in lane-overrides and Kanban dispatch rules, not delegated to a reasoning agent. For the rationale, see [profiles/README.md](../profiles/README.md#routing-without-an-orchestrator) and the README's [Why no Reviewer and no Orchestrator](README.md#why-no-reviewer-and-no-orchestrator).

## Dispatch interval

The dispatcher is a periodic pass, not an event loop reacting to each state change instantly. This is deliberate: a fixed interval bounds how often workers spawn, makes the system's load predictable, and means a card returned to `ready` (by a retry or an unblock) is picked up on the next tick rather than racing. The handoff between profiles is the state change itself — a profile sets its card's exit state and the *next* dispatch pass routes it onward — so the interval is the natural clock that turns passive state into worker activity. The concrete interval value is a tuning parameter, not an architectural constant.

## The review gate

Review is first-class state in `metadata`, not a comment. The full rules:

### Rule 1: Agent recommendation and human acceptance are separate

A card carries two distinct approval signals:

- **`metadata.agent_verdict: approve`** — an agent (typically Verifier for drafts, Linter for structural checks) examined the work and judged it complete. This is the *agent recommendation*. There is no Reviewer profile; verdicts come from the profile whose job included the check.
- **`metadata.review_status: approved`** — the human accepted the work as canonical. This is always a human action.

The two are not equivalent. A card with `agent_verdict: approve` and `review_status: requested` means "agent recommends, awaiting human sign-off." A card promoted to canonical with `agent_verdict` unset, when a check was expected, is a configuration bug — humans should not advance work past agent checks silently.

The full pipeline (both signals visible, all riding on `status: done`):

```text
status: running ──► done ─────────────────────────────────► archived
agent:                 agent_verdict: approve   (agent gate)
review:                review_status: requested ──► approved (human gate)
```

The agent gate is necessary but not sufficient. Human acceptance (`review_status: approved`) is the canonical promotion gate; the agent verdict is the recommendation feeding into it.

### Rule 2: Review is a state, not a comment

A card is canonical only after a human sets `review_status: approved`, not because a worker says it is finished. The review fields all live in the `metadata` overlay — the full list is in [card-schema.md → Memoria overlay fields](../../reference/card-schema.md#memoria-overlay-fields-inside-metadata). If a comment says "I reviewed this" but `review_status` is still `unreviewed`, the card is unreviewed. The field is authoritative.

### Rule 3: Review states block dispatch

Cards in `done` (awaiting review), `blocked`, `triage`, or `todo` are not claimable by any worker until state changes. Hermes does not dispatch these statuses; Memoria additionally checks `review_status` before promoting. Non-dispatchable means non-dispatchable.

### Rule 4: Review has ownership

The reviewing party (human, Verifier, Linter) is explicitly recorded in `review_owner`, so the board can show who owes the next decision. No silent promotes. Accountability is preserved.

### Rule 5: Review is a gate in the lifecycle

Writer and Coder can finish their own slices (`status: done`), but the card is not canonical until a human sets `review_status: approved`. On rejection the original card never quietly reopens — it is archived with a stated outcome, and any rework starts on a fresh card. The supersede-vs-discard decision is a separate human action; see [Post-rejection paths](README.md#post-rejection-paths).

### Why the three verdicts

The verdict set — `approve` / `reject` / `escalate` — is the **human's** decision at the review gate; agents only *recommend* into it. The set is deliberately three, not two: a binary approve/reject forces uncertainty to collapse into one of the two, and uncertainty would default to `approve` (the path of least resistance). `escalate` exists precisely to catch that case — it is the right verdict whenever uncertainty would otherwise default to `approve`, routing the decision to a separate deliberation (typically rewriting the handoff payload or the lane-override) instead of silently passing. Every review pass must end with exactly one of the three, each with a short reason; "looks fine" is not a verdict, and the verdict lives on the card, not in chat. The verdict-to-resulting-state mapping is in the [reference verdict table](../../reference/board-states.md#review-verdict-vocabulary).

**Verifier-specific verdicts.** Verifier produces a more granular triple in `metadata.agent_verdict` on `verify` cards: `verify-clean`, `verify-needs-revision`, `verify-needs-attention` (see [verifier.md](../profiles/verifier.md#verdict-semantics)). These are recommendations the human translates into one of the three verdicts. A `verify-clean` is typically promoted to `approve`; `verify-needs-revision` to `reject` (the human then chooses to spawn a revision card or discard, per [Post-rejection paths](README.md#post-rejection-paths)); `verify-needs-attention` to either `reject` or `escalate` depending on the human's read.

## Why the WIP limits

Work-in-progress limits exist to prevent overload, and each cap is reasoned from a different failure mode:

- **Active per profile = 1.** A profile holds one `running` card at a time. This is the strictest cap because parallel runs of the same profile would contend for the same write scope and make the audit trail ambiguous about which run touched what. It is also the only cap Hermes enforces natively.
- **Review queue depth (bounded).** The constraint here is *human* attention, not machine capacity: a `done`-awaiting-review pile grows faster than a human can clear it, and an unbounded queue silently converts "reviewed" into "rubber-stamped." When the queue exceeds the cap, the dispatcher delays new card creation on that lane (or escalates a Telegram notification) so the backlog signals before it becomes invisible.
- **Writer lane / synthesis (bounded).** Too many drafts in flight at once means quality drops because evidence cannot be fully integrated — a writer juggling many drafts integrates none of them well. The cap protects synthesis quality, not throughput.

These are operational tuning parameters, not architectural constants. The concrete cap values and how each is enforced are in the [reference WIP-cap table](../../reference/board-states.md#wip-caps). *Active-per-profile = 1* is enforced natively by Hermes; the review-queue and synthesis caps are Memoria-side policies the dispatcher applies before it creates or releases new cards on a lane.
