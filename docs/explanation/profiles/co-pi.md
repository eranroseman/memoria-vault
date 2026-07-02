---
title: The Co-PI
parent: Operation postures
grand_parent: Explanation
nav_order: 1
---

# The Co-PI

The Co-PI is the conversational posture behind `memoria ask` and guided
interview operations. Its mission has three verbs: **question** (sharpen the
PI's thinking), **explain** (account for what Memoria is doing), and **route**
(turn durable work into explicit CLI/engine requests). Its product is the PI's
sharpened thinking and well-routed work - never a direct file write
([ADR-48](../../adr/48-copi-and-agent-consolidation.md)).

---

## The hard write-wall

The Co-PI is **read-only**. It runs the PI's read-only interactions directly —
searching, reading, questioning, explaining — but every write leaves as an
explicit CLI/worker request or attention proposal. The policy gate enforces the
wall for optional adapters; the worker/trusted-writer boundary enforces it for
runtime operations.

The wall is what makes conversational help safe. A conversation drifts,
accumulates context, and gets persuaded; a request envelope does not. By the time
durable work touches the vault it has passed through the engine lifecycle,
checks, and read barrier.

## Memory

The alpha.14 baseline treats durable memory as checked workspace state, not a
profile-owned chat transcript. Anything worth keeping must become a checked note,
digest, project update, or request outcome recorded in the journal.

## What the Co-PI is not

**Not a lane.** It does not own a board or background profile. Durable work is a
CLI/engine request.

**Not a router-only shell.** Routing is one verb of three. The informal sparring
- questioning a source, branching framings, explaining a decision - is useful
only when it stays read-only until the PI chooses a durable action.

**Not an author.** It never writes canonical content, drafts, or even staging artifacts. When the conversation produces something worth keeping, the keeping is delegated or done by the PI.

---

## Related

- Why the profile boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why one conversational front: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
