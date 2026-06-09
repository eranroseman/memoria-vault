---
topic: explorations
title: Profiles and the SOUL model — seven specialists, no orchestrator
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 19
---

# Profiles and the SOUL model — seven specialists, no orchestrator

A design capture of the seven agent profiles as they are actually configured — each
one's mission, write scope, posture, model, and MCP wiring — and the structural
choices that shape the set (no orchestrator, no reviewer; postures separated by
construction). Reconstructed from
[`vault/.memoria/profiles/`](../../vault/.memoria/profiles). Implements
[ADR-02](../adr/02-seven-specialist-profiles.md),
[ADR-22](../adr/22-build-on-hermes-runtime.md),
[ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), and
[ADR-32](../adr/32-external-access-over-mcp.md).

> **Why capture this.** The profiles are the most-implemented subsystem in the vault
> (seven `SOUL.md` + `config.yaml` + `distribution.yaml` triples) yet the only
> proposal touching them is the narrow [RFC-09](../adr/42-profile-compilation.md).
> This is the design view of the lane model as built.

## What it is

A profile is a Hermes agent identity: a `SOUL.md` (mission, folder permissions,
skills, exit condition), a `config.yaml` (model routing, `mcp_servers`,
`agent.disabled_toolsets` allowlist), and a `distribution.yaml` (deploy manifest).
Seven exist, each a narrow specialist with a single posture. There is **no
Orchestrator** (routing is static, encoded in [lane-overrides](policy-gate-and-permissions.md))
and **no Reviewer** (review is always human).

## The seven profiles

| Profile | Mission (from SOUL.md) | Posture | Write scope | Model | MCP servers |
|---|---|---|---|---|---|
| **librarian** | "Find, enrich, and classify evidence for later synthesis. You are optimistic." | optimistic | `10-inbox/01-fleeting/`, `10-inbox/03-candidates/`, `20-sources/**` | haiku | policy, ingest, obsidian, paper_search, pyzotero |
| **writer** | "Turn evidence into structured drafts… You do not question or verify." | generative | answers, drafts, canvas, framing; reference + deliverables (review-gated) | sonnet | policy, obsidian |
| **mapper** | "Map the corpus… You are read-only across the vault." | read-only | `40-workbench/*/01-map/` only | sonnet | policy, obsidian |
| **socratic** | "Sharpen the human's thinking through questioning. You never produce artifacts." | read-only / interactive-only | **none** | opus | policy, obsidian |
| **verifier** | "Trace every substantive claim… Catch retractions. You are conservative." | conservative | `40-workbench/*/05-verification/`, gap cards to candidates | opus | policy, obsidian, verify, pyzotero |
| **coder** | "Build and maintain code artifacts… You are transactional." | delegated | `40-workbench/*/06-code/` | haiku | policy, obsidian |
| **linter** | "Validate structure, metadata, and vault health… Your default is dry-run." | deterministic | `99-system/logs/` (+ classed auto-fix) | haiku | policy, obsidian |

Model routing matches cost to judgment load: the two conservative judgment lanes
(Socratic, Verifier) run Opus; the generative Writer and Mapper run Sonnet; the
mechanical lanes (Librarian, Coder, Linter) run Haiku. All run through the Kilocode
gateway.

### Toolset posture

Every profile carries an `agent.disabled_toolsets` allowlist. The five non-terminal
lanes (Librarian, Writer, Mapper, Socratic, Verifier) disable `code_execution`,
`web`, `terminal`, and `file` — their only write path is the obsidian MCP (ADR-27,
ADR-32). **Coder** and **Linter** alone keep `file` and `terminal` (Coder also
`code_execution`) for git and `detectors.py`. External service access never reaches
the agent directly; it arrives over an MCP server or not at all.

### Postures as structure, not instruction

The optimistic/conservative split is enforced, not requested. The Librarian's
optimism (include the candidate, propose the classification) and the Verifier's
conservatism (flag, never fix) live in *different agents with different permissions*,
so neither can drift into the other's stance. Socratic's "never produce artifacts" is
a hard wall: an empty write scope in its lane-override **and** a withheld `vault_write`
capability in the tool-registry — two independent guards — plus `invocation:
interactive_only` so it is never queue-dispatched.

## Design rationale

- **Seven narrow lanes over one generalist.** Quality responsibility is traceable
  (each output has one accountable lane); permission enforcement is practical (a lane
  writes one zone, not "everything it might need"); and opposing postures can be
  separated structurally.
- **No Orchestrator.** Routing encoded in lane-override rules is auditable and
  diffable; routing decided by a reasoning agent hides the logic in model output and
  can't be inspected. Static routing is a feature.
- **No Reviewer.** An LLM reviewer is confidently wrong on exactly the hallucinated-
  citation outputs the gate exists to catch; making it the gate converts a structural
  guarantee into a probabilistic one. Review stays human (see
  [Why the review gate is structural](../explanation/rationale/why-human-gate.md)).
- **Build on Hermes (ADR-22).** Memoria does not own the runtime — Hermes provides
  the board, dispatcher, model routing, memory tiers, and MCP host. Profiles are
  conventions on top: SOUL identities, the policy gate, the vault schema.
- **Cost tracks judgment.** Spending Opus on Haiku-shaped bookkeeping would be waste;
  spending Haiku on the Verifier's claim-tracing would be false economy. The model map
  is a deliberate cost/quality allocation.

## Related

- [ADR-02](../adr/02-seven-specialist-profiles.md), [ADR-22](../adr/22-build-on-hermes-runtime.md), [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md), [ADR-32](../adr/32-external-access-over-mcp.md)
- [RFC-09](../adr/42-profile-compilation.md) — compiling the seven SOULs from a shared base (deferred)
- [RFC-04](../adr/37-retriever-scout-profile.md) — splitting Librarian into Retriever + Librarian (deferred)
- [Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md) — the path/capability scoping behind each lane
- [Memory substrates — seven scoped stores, not one](memory-substrates.md) — agent memory per profile
- Explanation: [`docs/explanation/profiles/`](../explanation/profiles), [`why-specialist-profiles.md`](../explanation/rationale/why-specialist-profiles.md)
