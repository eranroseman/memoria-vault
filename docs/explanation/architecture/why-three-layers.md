# Why three layers, not one

Memoria separates three concerns — active work, execution, and settled knowledge — into three distinct layers. This is not a layering convention; it is the mechanism that makes retries safe, handoffs lossless, and review enforceable.

---

## The three concerns

Any knowledge production system that uses AI agents must manage three kinds of state:

1. **Active work state** — what tasks are in flight, what's their status, who owns them, what happened when they failed.
2. **Execution context** — which agent is running, what permissions it has, what tools it can use.
3. **Settled knowledge** — what has been established, synthesized, and approved as canonical.

The failure mode of most single-agent or single-document systems is that these three concerns share the same substrate. They collapse together in chat history, in the agent's working context, or in a flat document store.

---

## What happens when they collapse

**Board + workers collapsed (no separate orchestration layer):**
Work state lives in agent memory or chat context. When a session ends, the state is gone. The next session starts fresh: it doesn't know what was already done, what failed and why, or where the previous worker left off. Retries duplicate work. Handoffs lose context. Long-horizon tasks that span multiple sessions become unreliable.

**Workers + vault collapsed (no separation between execution and knowledge):**
Agents write directly to canonical knowledge without review. There is no gate between "the agent finished" and "this is now trusted information." A confidently-wrong agent writes claims that downstream work cites — and those errors compound.

**Board + vault collapsed (tasks and knowledge share the same store):**
Task history pollutes the knowledge graph. In-flight notes get confused with settled notes. The canonical vault contains both "this is a claim" and "this is a work-in-progress" — and there is no structural way to tell them apart. Queries against the vault return noise.

---

## Thin control over thick state

The three-layer design follows a principle that three independent research systems identified from different starting points:

**[Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous)** (*Toward Autonomous Long-Horizon Engineering for ML Research*) describes this as "thin control over thick state": the orchestrator and workers carry as little persistent context as possible; durable knowledge lives in files. Their ablation removes the persistent knowledge layer and measures a drop of 6.41 points on PaperBench and 31.82 points on MLE-Bench Lite. The persistent layer isn't overhead — it's the mechanism that enables long-horizon work.

**AgentRxiv** ([Schmidgall and Moor 2025](../../reference/bibliography.md#schmidgall2025agentrxiv)) shows that agents reading prior agent-generated reports gain ~11% over isolated agents on MATH-500. Cross-session knowledge persistence is the mechanism; agents that can't read prior work start from scratch every time.

**PARNESS** ([Wang and Luan 2026](../../reference/bibliography.md#wang2026parness)) names "no existing tool persists cross-run knowledge in a form that can be retrieved into a finite LLM context" as one of five structural problems in the field — and addresses it with a persistent knowledge layer. The architecture is near-identical to Memoria's three-layer split; the defining difference is that PARNESS is fully autonomous where Memoria has a blocking human gate.

Three unrelated systems, three architectures, one finding: long-horizon agent work fails when state lives in chat and succeeds when state lives in files.

---

## The load-bearing rules

The three-layer separation is maintained by three rules that cannot be violated without breaking the design:

**The board never holds knowledge.** It tracks work. Cards die at `archived`; knowledge lives in the vault. A card can reference a vault note by path; it never *is* a note.

**The workers never hold permanent state.** They claim cards, act, and release. Continuity comes from the board (in-flight) or the vault (settled). Between sessions, a worker re-grounds on the files it can read — it does not rely on conversational memory.

**The vault never schedules work.** It is the destination, not the orchestrator. A vault note does not trigger agent action; a board card does.

---

## The policy MCP as the guard

The boundary between workers and vault is enforced at runtime by a policy MCP that intercepts every vault write. Without this enforcement, a worker could write to review-gated zones simply by issuing the file operation. The MCP makes the boundary structural rather than relying on prompt discipline.

Review-gated zones (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) always degrade to `dry_run` for any profile. Every allowed write is audited. The boundary isn't "a worker should not write here" — it's "a worker cannot write here."

---

## Related

- The three layers described: [architecture/README.md](README.md)
- How the worker layer is structured: [why-specialist-profiles.md](why-specialist-profiles.md)
- Why the vault's review gate is structural: [why-human-gate.md](why-human-gate.md)
- How the knowledge model is organized: [../knowledge/README.md](../knowledge/README.md)
