# Foundation (F1–F4) — alpha.21 design

Date: 2026-07-12. Status: approved design; first sub-project of the beta.1
consolidation (`2026-07-12-beta.1-consolidation.md` §2 Foundation). Milestone:
`0.1.0-alpha.21`. Issues: #1361 (F1), #1362 (F2), #1363 (F3), #1364 (F4).

## Purpose

Make the delivered machinery **true and visible** before anything is built on
top of it (roadmap Tier 0). Four repair packages: faithful provenance, a
verifiable journal, durable evidential grounds, honest surfaces. No new
features; no propagation-semantics changes (that is G5, alpha.22+); no edge
parsing changes (G2).

## Decided (owner, 2026-07-12)

1. **Actor vocabulary:** 4-value enum — `'pi' | 'agent' | 'operation' |
   'integrity'` — with one CHECK on both tables. The concrete agent identity
   (claude/codex, MCP `--actor`) travels in the envelope/journal metadata, not
   the enum.
2. **Schema mechanics (pre-G1):** edit `schema.sql` in place, bump
   `SCHEMA_VERSION` 8→9, `state._init` accepts `{0, 9}`. No migration code:
   pre-beta there are zero durable vaults (`test-vault/` is disposable by
   rule), so old DBs rebuild. This is the migration-cost-is-zero window working
   as intended; numbered ALTER migrations begin with G1.
3. **Blob backup:** real `workspace backup` / `workspace restore` commands, not
   report-only and not git-tracked blobs (okf-note: git holds knowledge, not
   corpora). K3 (beta.1) formalizes the full restore matrix on top.

## F1 · Provenance & actor integrity (#1361)

Falsified provenance is the design's worst defect class. F1 gives both actor
columns one vocabulary and requires every mediated request to carry one
validated provenance context from claim through mutation and journaling.

- **Schema (rides v9):** `CHECK (actor IN ('pi','agent','operation','integrity'))`
  on both `operation_requests.actor` and `derivations.actor`. Drop
  `DEFAULT 'pi'` — a missing actor is an error, never silently "the human did it."
- **Operation context:** one immutable `OperationContext` is the provenance
  interface for a claimed request. It lives at the existing `trusted_writer`
  seam and contains exactly five normalized strings: `actor`, `run_id`,
  `request_id`, `operation_id`, and `machine`. The type is frozen and slotted;
  it has no fallback values or actor-changing helper.
- **Construct once:** `worker._run_claimed_job` builds the context inside its
  failure-recording block before dispatch. The builder requires an envelope,
  validates `actor` against `state.ACTORS`, rejects blank identifiers, and
  rejects disagreement between the job and envelope request or operation ids.
  An explicit nonblank envelope `args.run_id` wins; otherwise `run_id` is the
  request id. The builder normalizes `machine` once as
  `safe_filename(machine or platform.node() or "local")` so the JSONL filename
  and SQLite event row cannot disagree.
- **Consume at the writer seam:** every request-mediated mutation or journal
  append receives the context. `trusted_writer` derives actor, run, request,
  operation, and machine metadata from it; leaf-supplied conflicting metadata
  raises. Request-mediated writer and state functions require the context.
  Functions outside a request envelope require an explicit actor and machine;
  neither interface supplies a provenance default. Domain arguments remain
  domain arguments; the context replaces distributed actor, run, request,
  operation, and machine keyword parameters.
- **Declare actors at request creation:** CLI, MCP, and HTTP adapters keep their
  declared `pi` or `agent` defaults and pass them explicitly. Engine and worker
  interfaces require an actor. Engine-created child requests declare
  `operation`; integrity sweeps and read-barrier scans declare `integrity`.
  `observe_pi_edit` remains explicitly `pi` because it records an unmediated
  edit from the researcher's editor.
- **Respect authority:** `resolve-attention` and `acknowledge-attention` are
  PI-only judgment operations. The worker rejects a non-`pi` context instead
  of relabeling an agent action as human; the runtime helper records the
  validated actor it receives. Supporting an agent-submitted PI decision would
  require separate `submitted_by` and `decided_by` provenance and is out of
  scope.
- **Current derivation projection:** `derivations` stores the actor of the most
  recent write for each `(input_id, output_id)` pair. Repeated staging upserts
  that actor; append-only `event_log` rows retain the complete history. The
  production write path validates the actor and lets the schema CHECK fail on
  an invalid value — it never uses `INSERT OR IGNORE` to suppress the error.
  F1 updates only the actor on an existing pair; changing which derivation
  edges exist belongs to G5.
- **Named hardcodes retire:** remove the hardcoded `"actor": "pi"` at
  `operations.py:85`, `knowledge.py:323/387/2208`, and the
  `envelope.get("actor") or "pi"` fallbacks in `worker.py` (316/352/583).
  Genuine unmediated and internal actors remain explicit at their request or
  observation seam.
- **Reject-marker trace — N/A (verified 2026-07-12):** reject dispositions
  never strip the durable inline `%%ev%%` marker. Export rendering strips
  markers only from its derived output copy, so no `stripped_*` reject event
  would be truthful. Adding durable-marker removal would change disposition
  semantics and requires a separate cross-store design.
- **Doc:** memory-model page states that `observe_pi_edit` attributing
  unmediated edits to `'pi'` is intentional (unmediated = the human's editor).
- **Out of scope:** the `actor == "pi"` branches in
  `integrity.py:915-925/999-1003` keep their current *semantics* (write-authority
  protection); making them origin-blind on the epistemic side is G5. F1 only
  makes the value they read faithful.

Tests prove the context builder rejects missing, invalid, blank, and mismatched
provenance; applies the run-id fallback; and normalizes one machine identity.
Engine and queue calls without actor raise. Input-backed agent, operation, and
integrity requests preserve their actor in `operation_requests`, journal
events, and `derivations`; the JSONL filename and `event_log.machine` agree.
PI-only attention operations reject an agent context. Repeating one derivation
as `pi` and then `agent` leaves one current `agent` row while the journal keeps
both events. Production and raw-SQL paths reject an out-of-vocabulary actor.
The reject-marker trace test is N/A: reject never strips the durable marker,
and export strips only its output copy.

## F2 · Journal trust — one authoritative trust-read path (#1362)

The multi-log plane design **stands** (owner ruling, okf-note fuller version):
per-machine `.memoria/journal/<machine>.jsonl` stays as the sync-ready plane;
the git-tracked `.memoria/journal-head` anchor stays as tamper evidence. The
goal is one authoritative trust-**read** path, not a sole journal. Defects to
fix inside that design:

- **Chain verifier (missing entirely):** walk `event_log` from GENESIS
  recomputing `row_hash`/`prev_hash` (`state._journal_hash`), compare the tip
  to the `journal-head` anchor. Surfaced as `memoria journal verify` and run
  inside `workspace scan`. Mismatch = failure, not a warning.
- **Trust reads move to `event_log`:** `integrity._latest_derived`
  (integrity.py:1292-1301) and the JSONL glob at `operations.py:834` switch
  from `.memoria/journal/*.jsonl` to `event_log` queries. The JSONL becomes
  derived/sync-plane only; a reconciliation check (JSONL events ⊆ event_log)
  rides the verifier.
- **Crash story (defined):** `event_log` insert is authoritative and happens
  first; the `trusted_writer.py:75` JSONL append is second and repairable —
  the reconciliation sweep re-emits missing JSONL lines from `event_log`.
- **Indexes (rides v9):** `event_log(event_type)`, `event_log(timestamp)` —
  justified now that event_log serves reads.

Tests: verifier catches a tampered payload and a broken head anchor;
blast-radius traversal returns identical results from the DB path (fixture
comparison against the JSONL path before its removal); crash between the two
appends recovers clean via the sweep.

## F3 · Durability of grounds (#1363)

`.memoria/blobs/` (captured source content — the evidential grounds) does not
rebuild, and operational ledgers likewise. Today `_backup_report`
(cli.py:2169-2199) only detects/reports backup configuration.

- **`memoria workspace backup <dir>`:** SQLite backup-API snapshot of
  `memoria.sqlite` + copy of `.memoria/blobs/` + `journal-head`, written
  atomically (temp dir + rename). **`memoria workspace restore <dir>`**
  inverse. Round-trip test is the drill.
- **`_backup_report` upgraded:** blobs present + no backup configured and never
  run → failing doctor status, not an informational line.
- **Durable-writes sweep:** verify `write_text_durable` does
  temp-write + fsync + atomic-replace + parent-dir fsync; extend the helper and
  its call sites where it doesn't.

Tests: backup→wipe→restore round-trip preserves DB, blobs, and journal-head
(verifier passes after restore); doctor fails when blobs exist unbacked.

## F4 · Surface honesty (#1364)

- **`_emit` (cli.py:2576-2581):** the non-JSON print is
  `payload.get("workspace") or payload.get("ok") or "ok"` — a failed operation
  (`ok=False`, falsy) prints literally `ok`. Exit code is already correct. Fix:
  failure prints `FAILED: <error/evidence>`; success prints the meaningful
  result (created path, count) — never bare `True`/`ok`.
- **`list --type work`:** give the existing list path a real DB branch — when
  `type == "work"`, enumerate catalog rows (id, title, check_status) instead of
  filtering markdown concepts (`api.py:27` `CONCEPT_TYPES` has no `work`
  branch while the CLI accepts `--type work`). No new action name.
- **`new-note --mode work`:** add `work` to the argparse choices
  (cli.py:153); the seed schema already requires `work_id` when `mode=work`.
- **Dead knobs deleted:** `.memoria/schemas/calibration.yaml` (read by
  nothing), the `gated:` key in type YAML (read by nothing and wrong).
- **Doc-code contradiction fixes:** the six enforcement-claim corrections
  (phantom seven-layer model, block-loudness binding, "single attention
  writer", telemetry-writes claim, SQLite-backed attention claim, dashboard
  rail tense) + knowledge-cycle capture-candidate, linter.md "blocks
  delegation", frontmatter.md drift from note.yaml, quickstart `ask`
  provider-keys claim; tutorials 01/02/04/05 fixed to run verbatim.
- **#1351 folds in:** add `argument.canvas` to `TRACKED_PROJECTION_PATHS`
  (projections.py) + test, since it declares `required_checks:
  [projection-drift]`.

Tests: failed op → non-"ok" output + exit 1; `list --type work` returns seeded
works; `mode: work` note round-trips; projection-drift covers argument.canvas;
tutorial commands smoke-run.

## Sequencing & delivery

F1 and F2 share the v9 schema change: **F1 lands first** (schema + threading),
**F2 on top** (verifier + read migration + indexes). F3 and F4 are independent
and can run in parallel with either. Each package is its own PR through
`scripts/verify`; `test-vault/` vaults rebuild after v9 (disposable by rule).

## Acceptance (alpha.21 exit for Foundation)

1. An agent-mediated write is attributed `agent` end-to-end; nothing defaults
   to `pi`.
2. `memoria journal verify` passes on a healthy vault, fails on tampering, and
   trust reads consume `event_log`.
3. backup→restore round-trip preserves grounds; doctor fails on unbacked blobs.
4. No CLI path prints success on failure; catalog is enumerable; tutorials run
   verbatim; the six doc corrections are live.
