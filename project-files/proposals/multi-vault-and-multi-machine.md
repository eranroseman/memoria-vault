---
topic: proposals
status: deferred
created: 2026-05-31
---

# Multi-vault and multi-machine

Capabilities for working across multiple research vaults or multiple devices.

---

## 1. Cross-vault read-only retrieval

**What.** MCP-mediated read access to a second Memoria vault (a collaborator's or a separate domain vault). Enables queries like "find claim notes in the adjacent vault that are relevant to this project." The foreign vault is strictly read-only; no writes, no card creation. Policy MCP enforces the boundary.

**Trade-offs.** Requires both vaults to be accessible to the same Hermes instance (shared filesystem or network mount). Introduces a trust boundary: the foreign vault's canon is someone else's — treat its claim notes as sources, not as your own synthesis.

**Adoption trigger.** The human is running two active research vaults and regularly finds themselves switching between them to check whether a claim from vault A is addressed in vault B.

---

## 2. Cross-project reading as personal AgentRxiv

**What.** Profiles read approved outputs from other projects in the same vault before starting new work on a project — the within-vault analogue of AgentRxiv's finding that agents gain ~11% by reading prior agent reports. Implemented as a "scan approved work from other projects" step in the Librarian's session-start routine.

**Trade-offs.** Useful only when the vault has enough cross-project overlap to surface relevant material. With a sparse vault, this step adds noise and latency.

**Adoption trigger.** The vault has ≥ 3 active projects with ≥ 50 approved claim notes each, *and* the human notices cross-project insights being missed until manual review.

---

## 3. Scripted session-history sync

**What.** `hermes profile export` / `import` snapshots carrying `state.db` chat history between machines, enabling session continuity across devices without a shared memory server. Extends the `memories/` junction sync pattern in deployment.md.

**Trade-offs.** Manual trigger (or cron). Sync conflicts are possible if two machines run sessions between sync cycles. The snapshot must exclude sensitive credentials.

**Adoption trigger.** The human regularly starts a session on a second machine and wants prior session context from the primary machine.

---

## 4. Hermes memory server (shared memory provider)

**What.** A cloud or remote shared memory provider for real-time, concurrency-capable cross-machine recall — replacing the scripted snapshot approach with a live memory service. Enables true multi-device continuity where session context is always current.

**Trade-offs.** Requires hosting a memory service. Adds infrastructure cost and a dependency. The scripted snapshot approach covers 90% of the need with zero infrastructure.

**Adoption trigger.** The scripted snapshot approach (above) is failing because the human switches devices frequently within a single work session — not just between sessions.

**Guard.** Do not adopt before the scripted sync approach has been tried. The memory server is the right solution for a specific failure mode; adopting it pre-emptively adds infrastructure cost without clear benefit.
