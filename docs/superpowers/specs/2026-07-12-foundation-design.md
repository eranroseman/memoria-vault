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
   pre-beta there are zero durable vaults (sandbox is disposable by rule), so
   old DBs rebuild. This is the migration-cost-is-zero window working as
   intended; numbered ALTER migrations begin with G1.
3. **Blob backup:** real `workspace backup` / `workspace restore` commands, not
   report-only and not git-tracked blobs (okf-note: git holds knowledge, not
   corpora). K3 (beta.1) formalizes the full restore matrix on top.

## F1 · Provenance & actor integrity (#1361)

Falsified provenance is the design's worst defect class: today
`operation_requests.actor` is `DEFAULT 'pi'` with no CHECK (schema.sql:12),
`derivations.actor` CHECK **forbids** `'agent'` (schema.sql:342), and only ~3
of ~40 operations read the envelope actor — the rest hardcode `"pi"`.

- **Schema (rides v9):** `CHECK (actor IN ('pi','agent','operation','integrity'))`
  on both `operation_requests.actor` and `derivations.actor`. Drop
  `DEFAULT 'pi'` — a missing actor is an error, never silently "the human did it."
- **Context threading:** build the operation context once in
  `worker._run_claimed_job` from the envelope (actor, run_id); consume it in
  `trusted_writer` (staging + journal). Remove the hardcoded `"actor": "pi"` at
  `operations.py:85`, `knowledge.py:323/387/2208`, and the
  `envelope.get("actor") or "pi"` fallbacks in `worker.py` (316/352/583) — a
  missing envelope actor **raises**. `worker.py:141/1246` (`"operation"`) stay:
  they are genuinely engine-initiated.
- **Reject-marker trace:** rejecting a finding that strips a `%%ev%%` marker
  emits an integrity journal event recording the stripped marker id + block.
- **Doc:** memory-model page states that `observe_pi_edit` attributing
  unmediated edits to `'pi'` is intentional (unmediated = the human's editor).
- **Out of scope:** the `actor == "pi"` branches in
  `integrity.py:915-925/999-1003` keep their current *semantics* (write-authority
  protection); making them origin-blind on the epistemic side is G5. F1 only
  makes the value they read faithful.

Tests: an agent-enveloped operation lands `actor='agent'` in both tables
end-to-end; enqueue without actor raises; reject leaves the journal trace;
CHECK rejects out-of-vocabulary values.

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
`scripts/verify`; sandbox vaults rebuild after v9 (disposable by rule).

## Acceptance (alpha.21 exit for Foundation)

1. An agent-mediated write is attributed `agent` end-to-end; nothing defaults
   to `pi`.
2. `memoria journal verify` passes on a healthy vault, fails on tampering, and
   trust reads consume `event_log`.
3. backup→restore round-trip preserves grounds; doctor fails on unbacked blobs.
4. No CLI path prints success on failure; catalog is enumerable; tutorials run
   verbatim; the six doc corrections are live.
