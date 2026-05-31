---
topic: architecture
---

# Review gate

The review gate is the policy constraint that prevents agents from autonomously promoting work into canonical vault zones. It operates at two levels: the **policy MCP** degrades writes to review-gated zones to `dry_run`, and the **board state machine** keeps a card non-canonical until a human sets `metadata.review_status: approved`. Neither gate substitutes for the other — they catch different failure modes.

## What a review gate is

A review gate is not a profile and not a workflow step. It is a structural enforcement point built into the policy MCP and the board simultaneously:

- **At the MCP level** — every write to a review-gated zone returns `dry_run` regardless of the requesting profile's lane policy. The write is logged and reported but not performed; the worker must surface the proposed change as a board comment for human approval. See [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md#the-decision-protocol).
- **At the board level** — a card with `status: done` is not canonical until the human sets `review_status: approved`. The `done` state is a real waiting state, not a label; nothing advances past it on a worker's say-so.

## Review-gated zones

Four vault folders require human approval before any agent write is committed:

| Folder | Contents |
| --- | --- |
| `30-synthesis/01-claims/` | Durable claims in the human's own words — the most protected zone. |
| `30-synthesis/02-reference/` | Stable reference pages synthesized from claim notes. |
| `30-synthesis/03-moc/` | Maps of Content; navigation hubs. |
| `50-deliverables/` | Final manuscripts, slides, and submission-ready exports. |

Every write to any of these paths degrades to `dry_run` at the policy MCP, for every profile. The policy MCP's `review_gated.dry_run` rule sits above lane-override configuration — no lane can grant itself write access to a review-gated zone. See [profile-matrices.md](../../reference/profile-matrices.md#lane-permissions-matrix) for the per-profile view of this constraint.

## The `review_status` overlay

The overlay is a frontmatter field (`metadata.review_status`) on each board card, tracking the human-approval lifecycle independently of the execution `status` field:

| Value | Meaning |
| --- | --- |
| `unreviewed` | Default while the card is in flight (`triage` → `running`). |
| `requested` | Worker handed off for review; `status` is now `done`. |
| `in-review` | A human is actively examining the work. |
| `approved` | Human accepted the work as canonical. |
| `rejected` | Human declined this pass. |

The review overlay only becomes meaningful once `status: done` is set. A card can hold `status: running` with `review_status: unreviewed` — that is the normal mid-flight state. See [kanban-board/states.md](../kanban-board/states.md) for the full state machine.

## Post-rejection paths

When a human sets `review_status: rejected`, the card is archived with a stated outcome — it never quietly reopens. Two follow-up paths are available:

1. **Revise (supersede).** Spawn a fresh card on the same lane. The new card carries a `metadata.supersedes` link back to the original; the original is archived with `metadata.archive_reason: superseded`. The agent is notified via the board comment on the new card.
2. **Discard.** Archive the original with `metadata.archive_reason: discarded`. No follow-up card. The work is abandoned.

The agent learns of the rejection through the board — the card state change and the comment log are the notification mechanism. There is no out-of-band signal; the board is the shared state machine.

## Gate vs. zone distinction

These two terms are related but distinct:

- **Review gate** — the *policy mechanism*: the MCP `dry_run` decision and the board `review_status` field together. The gate is a constraint on behavior, not a location.
- **Review-gated zone** — the *vault location* where the gate applies: the four folders listed above. A zone is a folder; the gate is what happens when a write targets that folder.

The distinction matters when extending the system: adding a new folder to the review-gated set changes a zone; changing the enforcement logic (e.g., adding an agent-recommendation prerequisite before `dry_run` fires) changes the gate. The two axes are independent.

## Related

- [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) — the full decision protocol and `dry_run` response contract
- [kanban-board/states.md](../kanban-board/states.md) — the review overlay state machine and post-rejection paths
- [profiles/README.md](../profiles/README.md) — per-profile write scope and the lane permissions matrix