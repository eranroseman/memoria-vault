---
title: The Co-PI
parent: Profiles
nav_order: 1
---

# The Co-PI

The Co-PI is the one agent the PI converses with — the permanent presence in the ACP pane. Its mission has three verbs: **question** (sharpen the PI's thinking), **explain** (it knows the system and can account for what any part of Memoria is doing), and **delegate** (route work to the right background lane). Its product is the PI's sharpened thinking and well-routed work — never a file ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)).

---

## The hard write-wall

The Co-PI is **read-only**. It runs the PI's read-only skills directly — searching, reading, questioning, explaining — but **every write leaves as a delegated task**: the `route-task` skill creates a card on the board via the tasks MCP, assigned to the lane whose posture fits. The policy MCP enforces the wall; it is structural, not prompt discipline.

The wall is what makes a permanent, memory-carrying conversational agent safe. A conversation drifts, accumulates context, and gets persuaded; a card does not. By the time delegated work touches the vault it has passed through a lane's scoped permissions, the propose-not-dispose process, and the PI's gate — none of which a chat message can shortcut.

## Memory — the loop only the Co-PI carries

Concentrating every conversation in one agent lets it run Hermes' self-improving loop — **memory · /goals · skills** — and compound into a genuine Co-PI rather than a stateless assistant. It is the **sole memory carrier** among the agents (see [The memory model](../architecture/memory-model.md)); the background lanes are stateless executors that ground on their handoff payloads. **`/personality`** — interactive persona tuning — is likewise Co-PI-only: the specialists' postures are fixed by design.

## What the Co-PI is not

**Not a lane.** It never appears on the board; it converses in the pane and creates cards for others.

**Not a router-only shell.** Delegation is one verb of three. The informal, continuous sparring — questioning a source, branching framings, explaining a decision — is the Co-PI's own work, distinct from the formal artifact-level pass run by [The Peer-reviewer](peer-reviewer.md).

**Not an author.** It never writes canonical content, drafts, or even staging artifacts. When the conversation produces something worth keeping, the keeping is delegated or done by the PI.

---

## Related

- The lanes it delegates to: [Profiles](README.md)
- How a delegated card travels: [The control plane](../architecture/control-plane.md)
- Why one conversational front: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
