---
topic: explorations
title: Profiles and the SOUL model — one co-PI, four lanes, no orchestrator
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 19
---

# Profiles and the SOUL model — one co-PI, four lanes, no orchestrator

A design capture of the five agent profiles as they are actually configured in
v0.1.1 — each one's mission, write scope, posture, model, and MCP wiring — and the
structural choices that shape the set (one conversational front, no orchestrator,
no reviewer; postures separated by construction). Reconstructed from
[`vault/.memoria/profiles/`](../../src/.memoria/profiles). Implements
[ADR-48](../adr/48-copi-and-agent-consolidation.md) (which supersedes
[ADR-02](../adr/02-seven-specialist-profiles.md)),
[ADR-22](../adr/22-build-on-hermes-runtime.md),
[ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), and
[ADR-32](../adr/32-external-access-over-mcp.md).

> **Why capture this.** The profiles are the most-implemented subsystem in the vault
> (five `SOUL.md` + `config.yaml` + `distribution.yaml` triples, plus per-profile
> `skills/`) and ADR-48 reshaped the whole set for v0.1.1. This is the design view
> of the lane model as built.

## What it is

A profile is a Hermes agent identity: a `SOUL.md` (mission, posture, boundaries), a
`config.yaml` (model routing, `mcp_servers`, `agent.disabled_toolsets` allowlist), a
`distribution.yaml` (deploy manifest), and a `skills/` directory of bundled
`<task>:<verb>-<object>` skills. Each agent is two layers: the **shared instruction
layer** — the vault-root [`AGENTS.md`](../../src/AGENTS.md), the house rules every
agent reads (the bounded propose/dispose rule, the folder map, lifecycle signals,
the honesty card, provenance) — plus its **unique layer**, the `SOUL.md` posture and
its own skills (ADR-48). Five exist: **one conversational front (the co-PI)**
and **four posture-defined background lanes**. There is **no Orchestrator** (routing
is static — the co-PI's `delegate:route-task` skill files a board card through the
tasks MCP, ceiling-validated against the [lane-overrides](policy-gate-and-permissions.md))
and **no Reviewer** (review is always human). Deterministic work is **engines, not
agents** ([ADR-46](../adr/46-seven-layer-architecture.md)): the Linter, the ingest
pipeline, and the verification sweeps left the profile set.

## The five profiles

| Profile | Mission (from SOUL.md) | Posture | Write scope | Model | MCP servers |
|---|---|---|---|---|---|
| **copi** | "The one agent the PI converses with… sharpen the PI's thinking, explain the system, delegate the work." | reflective thinking-partner; **read-only** | **none** — every write leaves as a delegated card | opus | policy, obsidian, ingest, cluster, tasks, patterns, paper_search, qmd |
| **librarian** | "The faithful processing agent… the four Library-side lanes: catalog · extract · link · map." | faithful — include generously; the gate filters | `inbox/`, `catalog/`, `notes/fleeting/`, `notes/source/` | haiku | policy, ingest, obsidian, cluster, patterns, paper_search, pyzotero, qmd |
| **writer** | "The generative agent. One lane: draft… a draft is raw material, never a deliverable." | generative, draft-only, review-gated | `projects/` (scratch) | sonnet | policy, obsidian, qmd |
| **peer-reviewer** | "The formal, independent review gate… flag, don't fix." | skeptical, deliberately independent | `inbox/` (flag/gap cards only) | opus | policy, obsidian, pyzotero, qmd |
| **engineer** | "The delegating agent. One lane: code… you scaffold the handoff and own the commit/revert gate." | delegating, two-agent boundary | `projects/*/code/` | haiku | policy, obsidian |

Model routing matches cost to judgment load: the two judgment-heavy postures (the
co-PI's sparring, the Peer-reviewer's claim-tracing) run Opus; the generative Writer
runs Sonnet; the mechanical lanes (Librarian, Engineer) run Haiku. All run through
the Kilocode gateway.

The co-PI is `invocation: interactive_only` — it lives permanently in the ACP desk
pane and is never queue-dispatched; the four lanes are `dispatched` board workers.
All five profile packages ship and install in v0.1.1 (`scripts/install.sh`
`ALL_PROFILES`); the **Project workspace** that gives the Writer, Peer-reviewer, and
Engineer their full workflow (phases 6–8 of D39) is **v0.1.2 scope** — in v0.1.1
they are installable, gated lanes reachable by delegation.

### Toolset posture

Every profile carries an `agent.disabled_toolsets` allowlist, and since
PR [#364](https://github.com/eranroseman/memoria-vault/pull/364) the rule is
absolute: **no profile keeps `file`, `terminal`, `code_execution`, `web`, or
`browser`** — the v0.1.0 Coder/Linter exception is retired, and the policy gate
hard-denies those tool families even if config drifts (D40/ADR-46; test-enforced).
The only vault-write path any lane has is the gated obsidian MCP
([ADR-31](../adr/31-native-obsidian-mcp.md)); external services arrive over MCP
servers (paper_search, pyzotero, ingest, cluster) or not at all (ADR-32). Local
hybrid search over the vault corpus arrives the same way: the shared `qmd` vector
index is wired as an MCP server (`qmd mcp`, stdio serve mode) in the four lanes
whose skills lean on similarity — co-PI, Librarian, Writer, Peer-reviewer — with a
matching read-only `qmd_read` group in the tool registry
(PR [#384](https://github.com/eranroseman/memoria-vault/pull/384); the install-time
index bootstrap is deferred,
[#385](https://github.com/eranroseman/memoria-vault/issues/385)). The
co-PI alone keeps the `memory` toolset — it is the sole carrier of the Hermes
self-improving loop (memory · `/goals` · skills · `/personality`, D46); the four
lanes disable `memory` because a dispatched worker gets everything from the
handoff payload and the vault.

### Bundled skills

The agent skills ship inside the profile packages
(`src/.memoria/profiles/<profile>/skills/`), named `<task>:<verb>-<object>`
(hyphen-joined on disk): the co-PI's five (`ask:question-source`, `ask:read-lens`,
`explore:branch-framings`, `delegate:route-task`, `explain-the-system`), the
Librarian's twelve across catalog/extract/link/map, the Writer's four draft skills,
the Peer-reviewer's four verify skills — and the Engineer carries none by design
(MCP tools only). That is 25 `SKILL.md` packages on disk (the registry's recorded
headline — "26 skills", PR
[#362](https://github.com/eranroseman/memoria-vault/pull/362) — is one above the
shipped set). Each `SKILL.md` carries a
machine-checkable `metadata.memoria` block whose MCP tools must resolve against the
tool registry and whose write scope must sit inside the lane ceiling
(`tests/test_profiles.py` enforces both). Four map-lane skills from the design's
full registry are deferred — `map:score-writability` / `map:score-readiness` /
`map:graph-claims` / `map:canvas-hub`, tracked in
[#381](https://github.com/eranroseman/memoria-vault/issues/381) — as is the
**assist surface** that would invoke the co-PI's ask/explore skills from the
Obsidian palette, pane, and selection
([#380](https://github.com/eranroseman/memoria-vault/issues/380); in v0.1.1 they
are reachable in the desk-pane conversation only). The
[ADR-43](../adr/43-skill-governance.md) governance trigger (>15 active skills) has
fired, tracked in [#368](https://github.com/eranroseman/memoria-vault/issues/368).

### Postures as structure, not instruction

The faithful/skeptical split is enforced, not requested. The Librarian's generosity
(include the candidate, propose the classification) and the Peer-reviewer's
skepticism (flag, never fix) live in *different agents with different permissions*,
so neither can drift into the other's stance — and the agent that synthesizes never
grades its own work (separation of duties, ADR-48). The co-PI's "every write is
delegated" is a hard wall: an empty write scope in its lane-override (`deny.write:
"**"`) **and** a withheld `vault_write` capability in the tool-registry — two
independent guards — plus `invocation: interactive_only` so it is never
queue-dispatched.

## Design rationale

- **One front, four narrow lanes.** ADR-02's seven specialists created a real UX
  failure ("who do I talk to?") and fragmented the learning loop across agents that
  never conversed. One conversational context compounds; the background lanes stay
  stateless propose-then-dispose executors. Quality responsibility remains traceable
  (each output has one accountable lane) and opposing postures stay structurally
  separated.
- **No Orchestrator.** Routing encoded in lane-override ceilings and the tasks MCP's
  validation is auditable and diffable; routing decided by a reasoning agent hides
  the logic in model output and can't be inspected. Static routing is a feature; a
  routing agent was explicitly rejected in ADR-48.
- **No Reviewer.** An LLM reviewer is confidently wrong on exactly the hallucinated-
  citation outputs the gate exists to catch; making it the gate converts a structural
  guarantee into a probabilistic one. Review stays human (see
  [Why the review gate is structural](../explanation/rationale/why-human-gate.md));
  the Peer-reviewer's `clean` never substitutes for the PI's approval
  ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).
- **Agents judge; engines do.** Anything deterministic (lint, ingest mechanics,
  retraction sweeps) runs as an engine behind an MCP facade — an agent fills only
  the judgment holes. This is why the old Linter profile no longer exists.
- **Build on Hermes (ADR-22).** Memoria does not own the runtime — Hermes provides
  the board, dispatcher, model routing, memory tiers, and MCP host. Profiles are
  conventions on top: SOUL identities, the policy gate, the vault schema.
- **Cost tracks judgment.** Spending Opus on Haiku-shaped bookkeeping would be waste;
  spending Haiku on the Peer-reviewer's claim-tracing would be false economy. The
  model map is a deliberate cost/quality allocation.

## History: the v0.1.0 seven-profile fleet

> **Historical record.** This was the as-built set under ADR-02 before the ADR-48
> consolidation shipped in v0.1.1; it no longer exists. The installer prunes these
> stale profiles from `~/.hermes/profiles/` on upgrade.

| v0.1.0 profile | Posture | Where its job went |
|---|---|---|
| `memoria-socratic` | read-only, interactive-only | the co-PI (`memoria-copi`) — the conversational front |
| `memoria-librarian` | optimistic | `memoria-librarian` (catalog · extract lanes) |
| `memoria-mapper` | read-only | the Librarian's `map` lane + the cluster MCP |
| `memoria-writer` | generative | `memoria-writer` |
| `memoria-verifier` | conservative | `memoria-peer-reviewer` (judgment) + the sweeps engine (deterministic checks) |
| `memoria-coder` | delegated | `memoria-engineer` |
| `memoria-linter` | deterministic, dry-run default | the Linter **engine** (`/.memoria/engines/linter/`) |

## Related

- [ADR-48](../adr/48-copi-and-agent-consolidation.md) (supersedes [ADR-02](../adr/02-seven-specialist-profiles.md)), [ADR-22](../adr/22-build-on-hermes-runtime.md), [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), [ADR-32](../adr/32-external-access-over-mcp.md), [ADR-46](../adr/46-seven-layer-architecture.md)
- [ADR-42](../adr/42-profile-compilation.md) — compiling the SOULs from a shared base (deferred)
- [#369](https://github.com/eranroseman/memoria-vault/issues/369) — defining the Engineer's code lane (ADR-21/34 revisit)
- [Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md) — the path/capability scoping behind each lane
- [Memory substrates — seven scoped stores, not one](memory-substrates.md) — agent memory is the co-PI's alone
- Reference: [`docs/reference/profiles.md`](../reference/profiles.md); Explanation: [`docs/explanation/profiles/`](../explanation/profiles), [`why-specialist-profiles.md`](../explanation/rationale/why-specialist-profiles.md)
