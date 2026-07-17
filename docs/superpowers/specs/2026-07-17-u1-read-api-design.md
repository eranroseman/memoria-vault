# U1 · Read-API + surface contract — Design

Date: 2026-07-17. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.9 output — the substrate contract U2/U3/U4 build against.
Consumes the consolidation §2 U1 unit list
(`2026-07-12-beta.1-consolidation.md:196`), the surfaces bootstrap spec
and its plan (lifecycle, tokens — honored), the merged surfaces plan's
binding contract 4 ("any /v1 route migration belongs to the future U1
gate" — this gate), the merged R2 spec §4 (retrieval honesty), and the
**shipped surface-contract spine** this spec formalizes rather than
invents: `engine/surface_contract.py` (alpha20, #1313/#1315/#1317 — 17
action rows), its consumers (`cli.py:25/:52/:569-575` help,
`http_transport.py:13-21` routing, `:298-355` **generated** openapi with
its registry parity test at `test_http_transport.py:157-167`,
`mcp_transport.py:9/:17`), and the floor sweep that already exercises
every read action per transport under a read-only guard
(`tests/test_floor_sweep_reads.py`, `floor_lib.py:358-388`).

**What this gate actually decides:** the shipped spine is the registry —
U1 ratifies it as the single source, adds the pieces that are genuinely
missing (the `job` dimension, MCP generation, the auth/scope walks, the
citable checklist), and resolves the surfaces plan's honor-or-supersede
clause. Nothing shipped is re-plumbed.

## 1. The surface-contract registry — ratified as-is, plus one field

The registry **already lives** at `src/memoria_vault/engine/
surface_contract.py`: rows carry `id, engine (binding), scope, params
(typed), http {method, path, params}, mcp {tool}, cli {commands: list},
response_version`. The shipped openapi generation and the floor sweep
depend on those fields; **the row shape is kept exactly** — U1 adds one
field:

- **`job`** — non-null, closed enum
  `read | knowledge | project | review | upkeep` (§3), on every row.

Single-source means **one definition site** (`SURFACE_ACTIONS`);
`actions_by_id()` / `http_routes()` / `mcp_tools()` / `cli_commands()`
remain its loaders. New surfaces from merged specs (explore, dashboard,
review) **must** add their row — the parity fabric below is the gate
that enforces it.

**Parity, defined per transport (the shipped fabric, upgraded where it
is soft):**

- **CLI:** the shipped registry⊆parser subset test upgrades to
  **equality against the pinned surface minus a named exemption list**
  (pure-CLI conveniences — init, onboard, steering edit, help… — listed
  explicitly in the test, so an unregistered new command fails parity).
- **HTTP:** `HTTP_ROUTES` and openapi both *derive from* the registry —
  comparing them to it is vacuous. The HTTP property is
  **reachability**: every registry http row dispatches non-404 through
  `_dispatch` (the floor sweep is this test; cited, extended for new
  rows). The shipped openapi↔routes parity test is retained as-is.
- **MCP:** the shipped closed-roster test stays; **new: parameter-schema
  parity** — each served tool's input schema ≡ its row's `params`
  (today's hand-written journal tool already drifts,
  `mcp_transport.py:76-87` vs `surface_contract.py:161-168` — the drift
  §4 exists to kill).

## 2. Route posture (PI ruling: honor the surfaces baseline)

The shipped flat read routes are the beta.1 read API — all of them
token-authenticated (shipped behavior, `http_transport.py:62-65`).
`/v1/*` stays exactly what the surfaces plan ships: lifecycle
(`/v1/status`, `/v1/shutdown`) + views, handled **before**
surface-contract dispatch and deliberately outside `HTTP_ROUTES`. New
read surfaces land where their merged specs put them and register rows.
No migration, no dual-serve; the registry is the beta.2 migration map if
unification ever earns itself. **The honor-or-supersede clause is
resolved: honored.**

## 3. The five workspace jobs

Every row names its job; the vocabulary is closed:

| Job | Rows (shipped ids + merged-spec arrivals) |
| --- | --- |
| **read** | ask, explore (R2), concept/concepts, work, journal + journal/event, status, operations, openapi, **status-paths**, **context-read** (`situated-context-read` — the bundle U4's context bus consumes) |
| **knowledge** | curate-note-candidate, curate-note-link, mark-checked, digest/capture/import family |
| **project** | project/slice, project/draft, frame-paper, gaps, export, promote-draft-passage |
| **review** | attention + attention/card, resolve-attention, acknowledge-attention, review (V2), resolve-evidence (V2), dashboard (I1) |
| **upkeep** | doctor, workspace scan, backup/restore, migrate, secrets, seed install (O1), serve lifecycle |

- **`cli-console` is satisfied by the job field**: `memoria help`
  renders commands grouped by the five jobs — the console is the CLI
  organized by the contract, not a new surface.
- `status-paths-action` and `context-read-set-action` are registry rows
  in **read** — grep-first at plan time: where a shipped action id
  already carries the semantics, the row maps it; where none exists,
  the row is **reserved** (declared, no transport) and the owning
  package wires it.
- Capture/import sits under **knowledge** (admission is knowledge-side
  inflow); `seed install` under **upkeep** (a setup act, not corpus
  curation) — the split is: recurring corpus work = knowledge, one-time
  workspace machinery = upkeep.

## 4. MCP scoping (PI ruling: registry-generated read parity)

- **`operation_run` remains the only write tool** — request envelopes,
  PI-protection, and the shipped preamble doctrine
  (`mcp_transport.py:14`) unchanged.
- The hand-written read tools are **replaced by generation from the
  registry**: every read row declaring `mcp` is served as a tool whose
  input schema derives from the row's `params` (the same field the
  openapi generation already consumes — one source, two projections).
  The closed-roster test stays; the new schema-parity test closes the
  drift the hand-written layer already shows.
- Adding a read surface = one registry row; the tool and its schema
  follow.

## 5. Lifecycle — what is shipped vs. what BOOT delivers

Shipped today: per-boot token minting (`cli.py:750-751`) and bearer auth
on **every** route with no exceptions. Arriving with the un-executed
surfaces BOOT tasks: the handshake rendezvous, the unauthenticated
`GET /v1/status` liveness probe (pre-dispatch, outside the registry),
idle-exit, bounded respawns. **U1 honors that plan and sequences behind
it where letters depend on it** — the U1 plan executes its (b)-exception
and (h) tests order-tolerantly (grep-first: if `/v1/status` and
idle-exit are absent, those tests are written against the bootstrap
plan's named seams and land with them). No resident daemon, ever, in
beta.1.

## 6. The read-api-acceptance checklist (citable; U2–U4 quote letters)

- **(a) Reachability:** every registry action is exercised on every
  transport it declares — enforcing fabric: the shipped floor sweep
  (`test_floor_sweep_reads.py`), extended as rows arrive. This is also
  the HTTP parity property (§1).
- **(b) Auth:** every `HTTP_ROUTES` route requires the per-boot token —
  **no exceptions in the registry** (a new auth walk pins shipped
  behavior). The sole unauthenticated endpoint is the lifecycle probe
  `GET /v1/status`, outside the registry; its test lands with BOOT (§5).
- **(c) Scope:** every read row **declaring a scope** refuses
  out-of-scope reads (`--read-scope` walk driven by the registry's own
  `scope` field); workspace-scope rows (status, operations, openapi)
  are exempt by that same field — the registry is the iterator.
- **(d) Views** serve the `view-spec.v1` envelope exactly (owned by the
  surfaces plan's tests; cited).
- **(e) Reads never mutate git-tracked state** — the floor
  `read_only_guard` + the I1 tree-clean pattern, API-wide. Untracked
  telemetry writes (`read-observed.v1`, I1 contract 1) are the
  sanctioned exception; the proof asserts tracked state only.
- **(f) Retrieval honesty:** ask/explore payloads carry the merged R2
  spec §4's ordered `pipeline_counts` + `excluded_strata` and
  honest-empties (owned by the R2 plan's tests; cited).
- **(g) openapi** is generated from the registry and parity-tested —
  **shipped** (`http_transport.py:298-355`,
  `test_http_transport.py:157-167`); pinned, not rebuilt.
- **(h) Idle-exit:** the server exits on idle; nothing in the API
  assumes a resident process (lands with BOOT; cited with its
  dependency named).
- **(i) MCP dispatch class:** every tool except `operation_run` binds a
  read engine function — the row's `engine`/`kind` binding determines
  the dispatch class, and the test enumerates served tools asserting
  it; plus the §4 schema-parity test.
- **(j) Errors are honest JSON** naming the refused thing (route,
  scope, token, or gate — never a bare status code).

Letters are each **owned or cited**: owned letters get enforcing tests
in the U1 plan; cited letters name their owning plan and, where
relevant, the execution-order dependency.

## 7. Deliberately not building

The `/v1` read migration (beta.2; registry-mapped); SSE/push/daemon; new
read surfaces (they arrive via their own merged specs + registry rows);
write tools beyond `operation_run`; a query language; re-plumbing of
anything shipped (openapi generation, floor sweep, roster tests);
per-transport feature skew.

## 8. Acceptance criteria

`SURFACE_ACTIONS` has exactly one definition site and every row carries
a non-null `job`; `memoria help` renders exactly five job groups; the
CLI parity test is equality-with-named-exemptions and fails on an
unregistered new command; the MCP tools are generated (the hand-written
layer deleted), the journal tool's schema drift is gone, and the
schema-parity test fails on a one-param drift; the auth walk passes
against shipped behavior (every registry route 401s without the token);
the scope walk refuses out-of-scope reads on every scope-declaring row
and passes workspace-scope rows untouched; each checklist letter has a
named enforcing test (owned) or a named owner + dependency (cited) in
the U1 plan; `python scripts/verify` green.

## 9. Implementation slices (feeds the plan)

1. `job` field on all rows (non-null, closed enum) + five-group
   `memoria help` rendering.
2. MCP tool generation from registry rows (replacing the hand-written
   read tools) + the parameter-schema parity test.
3. The auth walk (b), scope walk (c), and error-shape walk (j).
4. CLI parity upgrade: equality-with-named-exemptions.
5. Registry rows for `status-paths` and `context-read` (grep-first:
   map or reserve).
6. The checklist letter→test/owner map as the plan's cross-section
   contract (citing shipped tests by name for (a)/(e)/(g); naming
   BOOT/R2/surfaces owners + dependencies for (b)-exception/(d)/(f)/(h)).

## Appendix: session provenance

PI rulings 2026-07-17: route posture = honor the surfaces baseline (A);
MCP reads = registry-generated parity (A); five-job registry + lettered
checklist approved at presentation ("yes"). The adversarial verification
round reframed the spec against the shipped alpha20 surface-contract
spine (the registry, openapi generation, and most parity fabric already
exist — findings corrected the original draft's built-from-scratch
framing, the auth-exception route (`/v1/status`, not flat `/status`),
the row-shape regression, the vacuous HTTP parity, and the scope/BOOT
sequencing) — the ratified rulings are unchanged; the diff shrank to
the genuine gaps.
