# 0.1.0-alpha.20 Decisions

This ledger captures release-time decisions as dated Y-statements. Historical
notes, ADRs, and design documents are context only, not source of truth or
justification. A decision is load-bearing only when the fact basis is stated
here or in an active top-level release file. The implemented system and this
release ledger are the decision-time record until the release closes into
`design-history/`.

## 2026-07-07 - Accept alpha.20 as the contract-spine + surface-expansion release

Y: `0.1.0-alpha.20-design.md` is accepted (moving it from "proposal" to the
release-record basis) as a **contract-hardening** release: keep the standalone
engine and its three thin control surfaces (CLI, loopback HTTP, MCP-stdio), and
make those surfaces contractual and drift-checked. Alpha.20 adds a shared
surface-contract registry, expands HTTP to the engine reads editor adapters
need, hardens HTTP scope/status-codes/OpenAPI, adds MCP descriptions and the
matching scoped read tools, polishes CLI help plus a `memoria new` template
contract, defines the minimal empirical-event contract and record operation, and
starts a thin Obsidian proof adapter. It does **not** replace the engine, move
state into an editor, or add a dedicated agent app.

Because: the alpha.19 standalone-engine conclusion holds, and the CLI/HTTP/MCP
audit (design §2) found the surfaces sound but un-contracted — hand-written
specs, no OpenAPI, `200` for unknown HTTP routes, per-request-only read scope,
HTTP exposing fewer reads than MCP, MCP lacking descriptions and three read
tools, bare CLI help, and no shared `memoria new` creation contract. Making the
surfaces precise before building an Obsidian plugin is the shortest path to real
editor integration that also keeps VS Code integration cheap later, without
introducing a second state owner. If a behavior cannot be described once and
exposed consistently, it is not ready to be an integration surface (design §0).

Pointers:
- Governing design: `0.1.0-alpha.20-design.md` (acceptance gate is its §6)
- Execution: `0.1.0-alpha.20-exec-plan.md`
- Implementation targets: `src/memoria_vault/engine/api.py` (unchanged behavior,
  wider exposure), `src/memoria_vault/runtime/http_transport.py`,
  `src/memoria_vault/runtime/mcp_transport.py`
- Workflow target: milestone `0.1.0-alpha.20` + "Release 0.1.0-alpha.20" parent
  issue — not yet created

Status: accepted for alpha.20 implementation.

## 2026-07-07 - The surface contract is a data-only registry, not a dispatcher

Y: `src/memoria_vault/engine/surface_contract.py` will be a static, data-only
registry describing each public surface action once. It is a contract *source*
for drift tests, HTTP OpenAPI generation, MCP tool descriptions, reference-doc
tables, and CLI help — never a dynamic dispatcher, plugin system, or new
dependency. Surfaces still call plain engine functions; the registry adds no
per-operation typed wrapper.

Because: the design (§3.1) explicitly weighs and rejects "one typed engine
wrapper per operation" — the deep engine interface is valuable because it hides
request-envelope mechanics, not because it mirrors every operation manifest. A
data-only registry gets drift-checking, OpenAPI, and doc/help generation from a
single source while keeping the risk (§7) of "the registry becomes a second
implementation" and "OpenAPI grows into a framework project" closed by
construction: no dynamic dispatch, OpenAPI is a static JSON object generated
from registry data.

Pointers:
- Implementation target: `src/memoria_vault/engine/surface_contract.py` (new);
  drift tests vs HTTP routes, MCP tools, and doc tables
- Design basis: `0.1.0-alpha.20-design.md` §4.1, §7 (risks)
- Workflow target: WS-1 in `0.1.0-alpha.20-exec-plan.md` — not yet implemented

Status: ratified for alpha.20.

## 2026-07-07 - HTTP stays loopback-only; remote/OAuth/CORS out of scope

Y: The local HTTP transport remains loopback-only for alpha.20. Startup
`--read-scope` sets the maximum scope for a session, per-request scope may
narrow but never widen it, unknown routes return `404` and bad methods `405`,
and an OpenAPI/surface-schema document is served. No CORS, cookies, OAuth, SSE,
WebSockets, or remote bind is added. MCP likewise stays stdio-only and an
optional extra; `import memoria_vault` must not import MCP.

Because: alpha.20 is an editor/agent integration release, not a hosted-product
release (design §1 non-requirements, §4.3, §4.4). Keeping HTTP loopback-only and
MCP optional prevents the standing risk that "HTTP starts becoming a remote API
by accident" (§7) and keeps the required package small. Widening authority
(CORS/remote) is deferred until a real plugin needs it and the threat model is
updated — a specific future trigger, not a default.

Pointers:
- Implementation target: `src/memoria_vault/runtime/http_transport.py`,
  `src/memoria_vault/runtime/mcp_transport.py`
- Design basis: `0.1.0-alpha.20-design.md` §1, §3.3, §3.4, §4.3, §4.4, §7
- Workflow target: WS-2 (HTTP), WS-3 (MCP) in `0.1.0-alpha.20-exec-plan.md`

Status: ratified for alpha.20.

## 2026-07-07 - Empirical events are measurement plumbing with no body text; dashboard deferred

Y: alpha.20 defines only the empirical-event schema
(`src/memoria_vault/engine/empirical_events.py`) and the `empirical-event-record`
operation (manifest `empirical-event-record.md`). The operation ID follows the
repo's hyphenated single-token convention (`resolve-attention`, `capture-source`,
…), reconciling the design §4.8 label `empirical_event.record`, whose stated
manifest name `empirical-event-record.md` is unreachable from `empirical_event.record`
because `safe_filename` (`runtime/paths.py`) preserves `.`/`_`. The schema IDs
`empirical_event.v1` / `journal_event_ref.v1` and the idempotency namespace
`empirical-event:<event_id>` are separate and unchanged. The validator is a
strict allowlist: unknown fields, missing
per-event-type required fields, and raw source/note/draft/SRD body-text or
path-like fields are rejected before an event is queued, sent, or stored.
Accepted events are stored as journal events under `.memoria/journal/` with the
normal SQLite mirror, deduplicated on replay via
`idempotency_key=empirical-event:<event_id>`. No dashboard, metrics view, or
survey tooling ships in alpha.20.

Because: the beta.1 empirical-use plan needs a shared event shape to measure
blocker decisions, but building analytics now would be scope creep against a
release whose job is contract hardening (design §4.7, §4.8, §7). A strict
allowlist plus a body-text ban keeps the privacy rule enforceable at the trust
boundary; client-generated `event_id` plus the idempotency key keeps offline
replay from duplicating observations.

Pointers:
- Implementation target: `src/memoria_vault/engine/empirical_events.py` (new);
  `src/memoria_vault/product/capabilities/operations/empirical-event-record.md`
  (new; id `empirical-event-record`, input `empirical_event.v1`, output
  `journal_event_ref.v1`, allowed tools `trusted_writer`, allowed paths
  `.memoria/journal/` + `.memoria/index/`)
- Design basis: `0.1.0-alpha.20-design.md` §4.7, §4.8, §6, §7
- Workflow target: WS-1 in `0.1.0-alpha.20-exec-plan.md` — not yet implemented

Status: ratified for alpha.20. Dashboards, payoff attribution, and
shadow-first promotion stay deferred until real events exist.

## 2026-07-07 - The dedicated agent app and beta.1 product blockers stay deferred

Y: alpha.20 does not build a dedicated agent app, and does not claim any beta.1
product workflow. It may expose read state for a deferred area only where the
engine already has it. The agent app is reconsidered only if Obsidian+MCP cannot
provide understandable approval flows, multiple editors need the same complex UI,
plugin+MCP setup proves to be the adoption blocker, or the app can stay a pure
client over the same contracts with no state ownership.

Because: the Obsidian-plugin-plus-MCP split is the cheaper hypothesis and stays
the default until adapter testing proves it fails (design §3.5, §4.6). The
beta.1 blockers — retrieval default promotion, canvas workspace, SRD lane, PI
evidence review, onboarding seed corpus, feedback/complementarity dashboard,
deep-work/gate topology, multi-device topology, raw dataset bundling — each have
an unmet precondition (design §4.9) that must be settled before implementation
belongs in beta.1, so pulling them into alpha.20 would spend effort ahead of the
decisions that gate them.

Pointers:
- Design basis: `0.1.0-alpha.20-design.md` §4.6, §4.9
- Workflow target: GitHub issues with Readiness `Later` per deferred area — not
  yet filed

Status: ratified for alpha.20 as a scope boundary.
