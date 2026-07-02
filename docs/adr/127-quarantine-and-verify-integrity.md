---
topic: decisions
id: 127
title: Quarantine-and-verify integrity engine (recoverability, git/journal, recovery classes)
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [122, 125, 126]
supersedes: [25, 104]
superseded_by: []
---

<!-- cspell:words journaled Litestream -->

# ADR-127: Quarantine-and-verify integrity engine

Consolidation ADR (see ADR-125 preamble). This is the mechanism layer that
makes ADR-128's epistemics safe: errors become detectable, attributable, and
reversible instead of gated at creation.

## Context

Alpha.14's engine (ADR-122) has the lifecycle, read barrier, and rollback
skeleton but leaves the guarantees implicit: what exactly promotes, what
demotes, what happens on crash, what survives DB loss, and which store owns
which history. The old audit posture (25, 104) was built for the policy-MCP
runtime and the vault-file world.

## Decision

- **Universal quarantine-and-verify invariant.** Every mutation to tracked
  content, regardless of origin (human editor, machine operation, external
  agent, scheduled job), is non-consumable until a verification pass
  dispositions it act/ask/log. One shared check suite promotes, reached by
  two ingresses: the operation lifecycle (engine writes) and `workspace scan`
  (foreign edits). Detection covers **all tracked paths**, including
  `references.bib` and `.memoria/overrides.jsonl`.
- **Consumption guard, refuse + enqueue.** At machine consumption the on-disk
  hash must equal the recorded `checked` hash; a mismatch refuses to serve and
  enqueues scan — no write on the read path; scan demotes under the lock.
  Real-time detection is in-15: a filesystem watcher hosted in `memoria
  serve` (the on-demand process — no new daemon) turns file events into
  enqueued scans while `serve` runs; scan + guard cover the rest of the time,
  and the guard is never retired.
- **Demotion propagates, in two tiers** (the build-system stale-vs-invalid
  lesson, so one demoted foundational node cannot cascade a whole subgraph
  into an attention flood). Depth 1: machine-derived direct consumers demote;
  human-authored descendants stay live with an ask-routed flag (never
  auto-destroy human work). Depth ≥2: machine descendants are **stale**-flagged
  — a derived signal, not a verdict change; excluded from correctness-bearing
  consumers (promotion inputs, export-readiness, gap scoring) and inheriting
  down derivations, but still served to retrieval/`ask` with mandatory stale
  framing (hard exclusion breaks cross-period queries); re-checked
  opportunistically in batches. Retraction-driven demotions
  propagate one level deeper before going stale. The blast radius is journaled.
- **Cross-store recoverability at the operation boundary** (SQLite + files + blobs +
  git): 2PC with exactly two journal states — `prepared` (covering the whole
  pre-finalize window) and `materialized` (set by a finalize transaction after
  `git commit` yields the SHA); write-ahead ordering (payload fsynced before
  the DB commit that references it; DB commit durable before materialize); one
  workspace-scoped write lock held for the whole operation; crash at any
  boundary recovers to complete-or-non-consumable via `workspace recover`.
- **Integrity incidents resolve by forward repair.** An incident (triggers:
  failed change-verification, user-declared error, periodic scan) carries its
  blast radius and suggested resolutions; the ground truth for repair is the
  *present sources* (blobs, payloads, files), never a history replay. The
  **derivation graph — with consumed-at-verdict on every edge — is first-class
  DB state**; the journal's roles are attribution (feeds ADR-128 calibration),
  crash recovery, and tamper evidence — it is not "forensic truth" and is not
  required to resolve incidents.
- **Git/journal division of labor.** Git owns file-tree history and the
  tamper-evidence root (the tracked `.memoria/journal-head` anchor — 104's
  git-as-root, kept); the SQLite journal owns operation history for the three
  roles above and stores git refs, never file bytes. The journal is additionally
  row-hash-chained — this narrows 104's rejection of hash chaining, which
  targeted an in-vault log file; DB rows plus a git anchor get row-level
  tamper evidence without that cost. One commit per completed operation,
  staging **only** the operation's materialized paths plus the control files;
  never `git add -A` (a swept foreign edit would bypass quarantine). File
  rollback is a git path-restore plus the DB inverse transaction.
- **Storage recovery classes.** Authority and recovery are distinct: files own
  authored meaning (file-recoverable); provider-derived records replay from
  content-addressed blobs; verdicts/journal are DB-only accepted-loss. **DB
  loss fails closed to `unchecked`** — a rebuild from files alone starts fully
  unverified and ignores any forged frontmatter status. Human `work update`
  dispositions live in the git-tracked append-only `.memoria/overrides.jsonl`;
  on DB-loss replay they are **tiered by direction — restrictions reapply,
  permissions re-earn**: restrictive dispositions (archive, contested-block)
  auto-apply; permissive ones (degraded acceptance, retraction resolution)
  return as attention items requiring re-confirmation (the journal witness is
  gone, so the log cannot be trusted to *unblock* anything).
  No human-authored datum is ever in the accepted-loss class.
- **Audit posture carried from 25/104**: the journal is append-only and
  content-light (paths, ids, hashes, verdicts — never note content); analytics
  are pure projections over it; diagnostics stay outside the workspace and
  outside git (ADR-105, which survives unchanged).

## Consequences

- Correctness for observers is fail-closed, not transactional: a half-done
  operation is unobservable as complete.
- Every guarantee has a crash/recovery gate (exec-plan PR-C/PR-D/PR-E).
- Multi-machine sync of the SQLite authority is out of contract (markdown
  merges; SQLite does not); one workspace, one writer at a time.
- A three-store **backup contract** exists and `doctor` reports on it: git
  remote (corpus), SQLite streaming replication — Litestream or equivalent,
  documented, never a runtime dependency — and blob file-sync. Fail-closed
  recovery loses every verdict; replication is cheaper than re-checking a
  corpus. Replication is backup, not sync.

## Alternatives considered

- **Watcher as a required daemon** — rejected; the accepted form is the
  `serve`-hosted watcher (in-15, second wave): real-time when the on-demand
  process runs, scan + consumption guard otherwise, guard never retired.
- **Synchronous demote-on-read** — rejected: a write on the read path races
  the workspace lock; refusal alone is already fail-closed.
- **Git as sole history** — rejected: verdicts and the records graph are
  relational, high-cardinality, and deliberately not file-recoverable.

## Related

- Design §2/§3/§6/§9/§11; ADR-105 (diagnostic plane, unchanged); ADR-128
  (the epistemics this machinery licenses).
