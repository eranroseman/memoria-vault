---
topic: board
---

> [!note] Status: Phase 1 (ships with v0.1).
> The board is the **Hermes-native Kanban** (`~/.hermes/kanban.db`), created at runtime by `hermes kanban` — not a file authored in the starter vault. Memoria adds the `metadata` review overlay (convention) and the read-only Dataview projections written by `.memoria/mcp/board_export.py` (shipped). The earlier "Phase 4" tag was a misclassification.

# Why the card schema is split

This page explains *why* the card schema is shaped the way it is: why it splits into Hermes' fixed built-in fields and a Memoria `metadata` overlay, why the review gate and provenance live in that overlay rather than as columns, and how the handoff payload is designed to be self-contained. For the field-by-field tables — each field's name, source, type, required/optional status, allowed values, and who writes it — see [the card-schema reference](../../reference/card-schema.md).

For the conceptual narrative see [README.md](README.md); for the state machine and the review gate see [states.md](states.md).

## Fixed fields vs. the Memoria overlay

The board **is** the Hermes built-in Kanban. Its task schema is fixed and not user-customizable, so Memoria does not define its own card columns — it uses Hermes' built-in fields and stores everything Memoria-specific inside the free-form `metadata` JSON. This is the central design constraint the whole schema works around: Memoria cannot rename, extend, or add columns, so anything Memoria needs that Hermes does not provide has to ride inside a field Hermes treats as opaque.

The authoritative schema is the upstream Hermes Kanban reference ([tools-reference#kanban-toolset](https://hermes-agent.nousresearch.com/docs/reference/tools-reference#kanban-toolset), [cli-commands#hermes-kanban](https://hermes-agent.nousresearch.com/docs/reference/cli-commands#hermes-kanban)). If a field conflicts with the live docs, the live docs win. The Hermes field list and enums track a specific release and can drift across versions, so the reference page carries a reconciliation note; reconcile against the live tools-reference before relying on exact names or values.

### Why the overlay exists

Because the Hermes schema can't be extended, Memoria's review gate and provenance live as **conventions inside the `metadata` JSON** — not as card columns. This is a deliberate trade. The alternative — forking Hermes to add real columns — would couple Memoria to a Hermes build and break the compatibility that lets Memoria cards work with stock `hermes kanban` tooling. Putting the overlay in `metadata` keeps `status` holding only real Hermes values while Memoria's approval semantics live where Hermes has a slot for them.

The cost is that the overlay is *convention*, not *schema*: nothing in Hermes validates it, so workers and the policy MCP are responsible for reading and writing the keys correctly, and dashboards query them via Dataview over exported card state. The review fields (`review_status`, `agent_verdict`, `review_owner`, …) and the provenance fields (`promote_target`, `supersedes`, `archive_reason`, …) are listed in the [reference overlay table](../../reference/card-schema.md#memoria-overlay-fields-inside-metadata).

**Why `review_status` is separate from `status`.** A card can be `status: running` while `review_status` is still `unreviewed`. Keeping them in different dimensions lets dashboards and dispatch logic query review independently of execution. Both are **board-card concerns only** — notes never carry them. A note's lifecycle phase lives in `lifecycle` (with per-type refinements like `maturity`), whose value set is disjoint from the board's. See [frontmatter-schema.md](../../reference/frontmatter-schema.md).

### Why dependencies use `parents`, not scheduling

Cards depend on other cards through the built-in `parents` array (edges created with `kanban_link`). Hermes uses these edges for execution ordering — a child becomes dispatchable once its parents complete — so Memoria expresses "do B after A" by linking B's `parents` to A rather than by scheduling a time. Scheduling would encode a guess about *when* A finishes; the dependency edge encodes the actual *constraint*, so the board stays correct even when A runs long. Use it only for genuine ordering constraints (e.g. a `verify` card that must wait for the `draft` card it checks). Routing and review are *not* dependencies: they live in `assignee` and `metadata.review_status`.

### Why not a separate registry

An earlier proposal (`memoria_task_registry_schema.md` in `raw/`) suggested a separate SQLite registry with one table per tracked entity. Memoria does not adopt that — the Hermes built-in Kanban already holds task and transition state (in its own `kanban.db`), and a parallel registry creates two sources of truth that have to be kept in sync.

Instead, the entities the card implicitly tracks — task, handoff, artifact, verdict, state transition — are **projections of card state**, not separate stores. Aggregate views come from a scheduled aggregator that reads card history; the audit trail comes from `00-meta/02-logs/audit.jsonl` (written by the policy MCP); the board snapshot for the [`board-state` dashboard](../dashboards/board-state.md) is a periodically-exported, read-only view of open cards (so Dataview can query without a live `kanban.db` connection, while `kanban.db` stays authoritative); and full card detail lives on the card itself. This keeps the board as the single source of truth while still giving the design a clear vocabulary for what the card tracks. The entity vocabulary and where each lives on the card are tabulated in the [reference entity table](../../reference/card-schema.md#entity-vocabulary); for overloaded *words* rather than entities see the [glossary](../../reference/glossary.md).

## Handoff-payload design

Handoffs carry two things: a **human-readable summary** for board readers, and a **structured payload** for the next worker (and the policy MCP). In Hermes these are the `summary` and `metadata` arguments of `kanban_complete` — both travel with the run, not as task columns. The run-level handoff fields are listed in the [reference handoff-fields table](../../reference/card-schema.md#run-level-handoff-fields).

### Why two forms, not one

The prose `summary` is for humans scanning the board; the structured `metadata` is for the next worker (and tools that read the card). Trying to use one for both produces payloads too verbose to scan and prose too vague to act on programmatically. So they stay separate, and each has a fixed shape.

The `summary` is short prose with three lines — what the next worker or the human sees at a glance:

```text
Blocker: [what's stopping forward progress]
Tried: [what's been attempted; what was learned]
Next: [the exact action the next worker should take]
```

The same three-line shape applies to every handoff: a revision card after a rejection (its `summary` describes what was wrong with the original; the card carries `metadata.supersedes: <original-id>` and the original is archived `superseded`), a Librarian → Verifier similarity-check handoff, a Writer draft firing the Verifier hook.

### Why the payload must be self-contained

The `metadata` field is JSON — what the next worker (or a delegated child agent) consumes programmatically. Hermes delegated children return summaries rather than sharing live parent state, so every handoff payload must be **self-contained**: the receiving worker should need nothing beyond the payload to start work. That constraint is *why* the payload carries an explicit `goal`, structured `context` key/value pairs (not free prose), an `allowed_paths` write scope, `expected_outputs`, and `review_checks` — each is something the receiver would otherwise have to reconstruct from a shared state that does not exist.

```json
{
  "task_id": "t_2b14",
  "origin_profile": "human",
  "target_profile": "memoria-librarian",
  "goal": "Find recent systematic reviews on persuasive digital health interventions",
  "context": {
    "research_direction": "digital health coaching",
    "project": "memoria-health-coaching"
  },
  "allowed_paths": [
    "10-inbox/03-candidates/**",
    "20-sources/01-papers/**"
  ],
  "expected_outputs": [
    "candidate paper notes",
    "classification proposal",
    "handoff summary"
  ],
  "review_checks": [
    "stable identifier present",
    "proposed classification included"
  ]
}
```

Two design points follow from self-containment. The `allowed_paths` scope **can narrow but never widen** the lane override — the policy MCP cross-checks the payload against the lane's permissions, so a handoff can tighten write scope for a specific card but cannot grant a worker more reach than its lane allows. And the exit `status` is *not* a payload field: it is set by the lifecycle terminator the worker calls (`kanban_complete` → `done`, `kanban_block` → `blocked`), so a worker cannot declare its own exit state by writing JSON. The full meaning of each payload field is in the [reference handoff-payload section](../../reference/card-schema.md#structured-payload).

The `summary` and `metadata` together form the durable trail. The conversation does not.
