# I1-skeleton — Feedback/instrumentation event plumbing (alpha.21) — Design

Date: 2026-07-14
Status: design (approved; revised for server-side disposition events), pre-plan
Issue: #1365 (milestone `0.1.0-alpha.21`)
Governing specs: `0.1.0-beta.1-empirical-use-action-plan.md` §2 (event field
table), `2026-07-12-beta.1-consolidation.md` §2 (I1 bullet — full package is
beta.1; this is the skeleton).

## Goal

Establish the disposition-telemetry seam end to end so the **non-backfillable**
baseline can begin accruing, without building the full beta.1 I1 package. This
is the last open item in the alpha.21 milestone; F1–F4 and
content-security-alpha21 are already merged. Closing it lets alpha.21 close.

"Skeleton" is the operative word: complete the client event shape, prove the
disposition path fires from one real PI decision as an **honest server-side
event**, prove `staleness_hit` populates from one real read path, and plant the
shadow-first discipline flag — nothing more.

## Design decisions (made here; confirm at review)

- **Dispositions are honest server-side journal events, not synthesized
  client-telemetry events (chosen approach: option B).** The
  `empirical_event.v1` schema was built for *client-supplied* events: every one
  requires `session_id` and `surface`, which a server-side emitter would have to
  fabricate (`session_id` has no honest value inside a single operation;
  `surface` uses a different vocabulary in the request envelope —
  `memoria-cli`/`memoria-http`/`memoria-mcp` — than the `SURFACES` enum). Rather
  than fabricate those fields, the server emits a small, honest **`disposition.v1`**
  journal event carrying only what it truly knows: `decision`, `item_type`,
  `item_id`, `request_id`, `timestamp`, and the F1-true actor (from
  `OperationContext`, via journal provenance). Client-side empirical events —
  with genuine sessions and surfaces — remain beta.1. The two reconcile by
  `request_id`.
- **`staleness_hit` is schema plumbing only in the skeleton; real read-path
  emission is deferred to beta.1.** A `read-observed.v1` validator and the
  `staleness_hit` field ship, but nothing emits from `answer-query` in the
  skeleton. Rationale (found in review): a read that appends a journal event
  rewrites the **git-tracked** `.memoria/journal-head` anchor (via
  `_append_decorated_event`), so an `answer-query` that emitted would leave the
  vault tree dirty until the next write op — misleading `observe-pi-edits` and
  surprising `git status`. A read must not mutate tracked state. The proper
  read-path telemetry sink (one that does not dirty the tree) is beta.1 scope.
- **`empirical_event.v1` (the client shape) still gains `loudness` and
  `staleness_hit` fields.** The action-plan §2 names "verify/extend the
  `empirical_event.v1` shared shape" as an I1 deliverable and lists both fields.
  The skeleton completes the shape so beta.1 clients can emit them; the skeleton
  has no client emitter of its own for these fields, which is expected.
- **`disposition.recorded` (the client event type) is untouched.** Because the
  server emits the separate `disposition.v1` event, the existing
  `disposition.recorded` type keeps its required `reason_code`. No contract
  relaxation, no client-schema test change.
- **`production_enabled: false` gates acting, not recording.** Events always
  record (preserving the non-backfillable baseline); the flag governs whether any
  future consumer may drive product behavior from the signal. Reconciles the
  action-plan's "record from day one" with the consolidation bullet's "false
  default."
- **`staleness_hit` is a boolean** (its name and the "read served stale/demoted
  state" framing are binary). **No new user-facing CLI** — the disposition *is*
  the resolve action, captured automatically ("dispositions as events, not
  ratings").

## Architecture

Four focused changes, each independently testable.

### 1. Complete the client event shape (`engine/empirical_events.py`)

Add the two fields the action-plan table lists but the `empirical_event.v1`
validator lacks:

- **`loudness`** — string enum `{quiet, notice, alert, block}` (the spec's
  attention-routing vocabulary). Added to `ALLOWED_FIELDS` and `ENUM_FIELDS`,
  identical in shape to the existing enums.
- **`staleness_hit`** — boolean. Needs a small `_bool_field` validator branch,
  since the current validator special-cases `duration_s`/`event_id`/`timestamp`
  and otherwise treats fields as strings. A non-bool value is rejected.

Neither field is *required* on any event type; both are optional. No new event
type is added and `disposition.recorded` is left as-is. This change is
client-shape plumbing for beta.1 emitters; the skeleton's own emitters are the
server-side events below.

### 2. Server-side disposition event + one proof call-site

- **New event schema constant** `DISPOSITION_EVENT_SCHEMA = "disposition.v1"` in
  `engine/empirical_events.py`, with a validator
  `validate_disposition_event(payload) -> dict` that requires
  `{decision, item_type, item_id}` (decision ∈ `DECISIONS`), rejects unknown
  fields, and rejects path-like `item_id`. It does **not** require
  `session_id`/`surface` — those are client-telemetry fields a server emitter
  does not have.
- **Seam:** `emit_disposition_event(vault, *, decision, item_type, item_id,
  context)` in `runtime/operations.py` builds a valid `disposition.v1` event and
  appends it to the journal **within the caller's existing operation
  transaction** via `trusted_writer.append_journal_event` (which stamps the
  F1-true actor from the operation context). No second git commit. This is the
  seam beta.1 will call from every other decision path.
- **Proof call-site: `resolve-attention`** (`runtime/integrity.py`
  `resolve_attention`, resolution `"resolved"`). It already carries an `outcome`
  in `{apply, reject, defer}` and is PI-only. After it records its resolution and
  before its commit, it emits one `disposition.v1` event with
  `item_type="attention"`, `item_id=<target_id>`, and `decision` mapped from
  `outcome`: `apply→accept`, `reject→reject`, `defer→defer`.
  `acknowledge-attention` (resolution `"acknowledged"`) does **not** emit — an
  acknowledgement is not an accept/reject/defer decision.
- **"True actor, not a rating"** is satisfied structurally: the disposition is a
  journal event whose provenance actor is the real `OperationContext.actor`
  (F1's mechanism — `pi` here), and `decision` carries the action taken, never a
  synthetic score. The payload carries `request_id` (from context) so beta.1
  client events join to it.

### 3. `read-observed.v1` validator + `staleness_hit` field (schema plumbing only)

The skeleton ships the read-observation *shape* so beta.1 can emit it, but adds
**no emitter**:

- **New event schema constant** `READ_EVENT_SCHEMA = "read-observed.v1"`, with a
  validator `validate_read_event(payload) -> dict` requiring `{workflow,
  staleness_hit}` (workflow ∈ `WORKFLOWS`, `staleness_hit` boolean).
- `answer_query` is **not** modified and its manifest is **not** changed — it
  stays a read.

**Why no `answer-query` emission (found in review).** `append_journal_event`
funnels through `_append_decorated_event`, which rewrites the **git-tracked**
`.memoria/journal-head` anchor on every append (only `.memoria/journal/`,
`.memoria/index/`, and `.memoria/memoria.sqlite*` are gitignored — the anchor is
not). `answer-query` is dispatched as a read and never calls
`commit_writer_changes`, so an emission would leave the vault tree dirty
(` M .memoria/journal-head`) until the next write op — which misleads
`observe-pi-edits` (it would attribute the anchor change to a PI edit) and
surprises `git status`. A read must not mutate tracked state. Emitting the real
read-path staleness signal needs a sink that does not dirty the tree, which is
beta.1 scope. The `staleness_hit` field and `read-observed.v1` validator are
present now so that sink has its shape ready.

### 4. Shadow-first config (`.memoria/config/feedback.yaml`)

New config file following the existing `providers.yaml` idiom, single key:

```yaml
production_enabled: false
```

A reader — `feedback_production_enabled(vault) -> bool` (in `runtime/`, beside
the existing config readers) — defaults `false` when the file is absent,
malformed, or the key is missing, and returns `true` only on an explicit boolean
`true` (mirroring `enrichment._provider_default_on`'s fail-safe parsing). It is
surfaced read-only in `doctor`/status output as established discipline. Because
the skeleton has no consumer, **nothing branches on it yet** — recording is
unconditional. The flag exists so the discipline is in place before beta.1 wires
the first consumer. The file is seeded into the workspace template
(`product/workspace_seed/.memoria/config/`).

## Data flow

```
PI runs `memoria attention resolve <id> --apply`
  → worker `resolve-attention` (actor=pi, F1-guarded)
     → resolve_attention() records resolution event
     → emit_disposition_event(decision="accept", item_type="attention",
                              item_id=<target_id>, context)
        → append_journal_event(disposition.v1, actor=pi, request_id=…)  [same txn]
     → commit_writer_changes(...)

(No answer-query emission in the skeleton — a read must not rewrite the tracked
journal-head anchor; read-path staleness emission is beta.1 scope.)
```

## Testing

- **Client schema:** `loudness` accepts the four enum values and rejects others;
  `staleness_hit` accepts `true`/`false` and rejects non-bool; existing
  `disposition.recorded` behavior (including required `reason_code`) is unchanged.
- **Disposition validator:** `validate_disposition_event` accepts
  `{decision, item_type, item_id}` with a valid `decision`, rejects an
  out-of-enum `decision`, rejects unknown fields, and requires all three fields.
  `item_id` is a vault path (e.g. `inbox/attention/x.md`) and is **not** subject
  to the opaque-id/path-like restriction — this is a server journal event.
- **Disposition emission:** resolving an attention item with `--apply`/
  `--reject`/`--defer` appends exactly one `disposition.v1` journal event with
  the mapped `decision`, `item_type="attention"`, `request_id` set, and `pi` as
  the journal-provenance actor; acknowledging appends none.
- **Read validator (no emitter):** `validate_read_event` requires `workflow` +
  `staleness_hit` and rejects a non-bool `staleness_hit`. The skeleton has no
  `answer-query` emitter (see §3), so there is no emission test.
- **Config:** `feedback_production_enabled` returns `false` for absent /
  malformed / disabled / key-missing files and `true` only for explicit boolean
  `true`; the seeded template ships the file with `production_enabled: false`.
- All new test files registered in `tests/conftest.py` `TEST_LEVELS`.

## Out of scope (→ beta.1, per consolidation §2)

Dashboard / honest-dashboard, payoff-attribution, complementarity-calibration,
three-orthogonal-signals, human-back-pressure (WIP caps + consuming ritual),
stakes-based-gating, diversity-channel, digestion-pressure, client-side
`empirical_event.v1` emission (real `session_id`/`surface`), a real session
concept, wiring the *other* decision operations (`curate-note-candidate`,
`curate-note-link`, `promote-draft-passage`, `mark-checked`, `update-work`,
`frame-paper`), **all read-path `staleness_hit` emission** (the sink must not
dirty the tracked journal-head anchor), attention-loudness policy, and any
consumer that acts on `production_enabled`.

## Constraints (inherited)

- Correctness gate: `python3 scripts/verify` passes before merge.
- Test only against disposable vaults (`tmp_path` / `test-vault/`), never a
  personal vault.
- Stage explicit paths only — never `git add -A` (shared-index rule).
- No new dependencies (Python 3 stdlib + SQLite).
- Schema mechanics: `empirical_event.v1`, `disposition.v1`, and
  `read-observed.v1` are payload/journal-event schemas, not the SQLite
  `SCHEMA_VERSION`; none of these changes bump `SCHEMA_VERSION` (still 12).
