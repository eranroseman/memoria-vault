---
topic: explorations
title: Session logging and audit — two logs, tamper-evidence, fleet trust
status: historical
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 23
---

# Session logging and audit — two logs, tamper-evidence, fleet trust

> **Historical (v0.1.0).** This note describes the pre-v0.1.1 logging layout and is
> kept for design rationale only. Logs now live under `system/logs/` and the Linter
> is an engine — see [ADR-25](../adr/25-session-logging-two-logs.md) and
> [Telemetry](../reference/telemetry.md).

A design capture of how Memoria records what its agents did in v0.1.1: the
hash-paired policy audit log, the operational JSONL logs around it, and the fleet
trust-score that rolls them up. Reconstructed from
[`vault/.memoria/mcp/`](../../src/.memoria/mcp) and the dashboards. Implements
[ADR-25](../adr/25-session-logging-two-logs.md); the audit half is produced by the
engine described in
[Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md).

> **Why capture this.** ADR-25 decides *that* there are two logs; this is the
> as-built view of their schemas, the hash-pairing mechanism, and the trust-score
> formula — none of which lived in an exploration before.

## What it is

ADR-25's model is two separate logs in `system/logs/`, written by different
components for different readers:

- **`audit.jsonl`** — the policy MCP's terse, append-only, SHA-256-paired record of
  every write decision. Built for tamper-detection and querying, not reading.
  **Shipped and live.**
- **`sessions/<id>.jsonl`** — per-session narrative summaries of agent activity,
  one file per session, never rotated. Built for humans.
  **Not built in v0.1.1** — see the deferral note below.

Keeping them apart is the decision: mixing narrative into the audit log would make it
verbose and harder to verify; mixing per-write events into summaries would make them
unreadable.

## How it works

### The audit log

`policy_mcp.py` appends one JSON object per decision (`append_audit`). Schema:

```
timestamp · profile · action · path · task_id · decision · policy_rule
            · reason?            (when the request carries one)
            · before_hash?       (mutating actions)
            · after_hash?        (null at pre-check; filled by complete_write)
```

Every allowed mutating write produces **two** records: the decision (with
`before_hash`, `after_hash: null`) and a later `write_complete` record carrying both
hashes — the policy-gate plugin's `post_tool_call` pass correlates the pair through
a `.pending/` stash keyed by tool-call id (stash files older than 24 h are pruned
opportunistically on each pre-call pass). Since PR
[#384](https://github.com/eranroseman/memoria-vault/pull/384) *every* mutating allow
is `allow_with_log` — a lane without `require: audit_log` can no longer land a write
with nothing to pair — and `complete_write` validates the caller's `before_hash`
against the pre-decision record, marking a disagreement `hash_mismatch: true` rather
than trusting it silently. Hashes are `sha256:<hex>`; a
not-yet-existing file hashes as the digest of the empty byte string — the
`before_hash` of a create is never null. Path-traversal attempts are audited with
the raw path (`policy_rule: path.traversal`) — the one request class most worth
logging.

**Tamper-evidence, not tamper-prevention.** The invariant is that each path's
latest `after_hash` equals the file's current SHA-256: editing a gated file
out-of-band breaks the pairing and is detectable after the fact.

A first chain guard ships in the Linter engine: the `audit_unpaired_writes`
detector ([`detectors.py`](../../src/.memoria/engines/linter/detectors.py),
PR [#384](https://github.com/eranroseman/memoria-vault/pull/384)) replays the log
and raises a MEDIUM finding for any mutating allow whose paired `write_complete`
(same path + task_id) never arrived within an hour — a hole in the reversibility
chain.

> **Deferred — the full chain verifier and rotation.** The `vault-hash-drift`
> detector that re-hashes files and flags paths whose current SHA-256 diverges
> from the last recorded `after_hash` is designed but **not shipped**: it needs
> state beyond the vault tree, and the
> [`detectors.py`](../../src/.memoria/engines/linter/detectors.py) docstring names
> it out of scope. Log rotation is likewise not yet implemented; `audit.jsonl`
> currently grows unbounded. Neither gap has a dedicated tracking issue yet.

### The session summaries — deferred

The v0.1.0 design had the Linter *profile* write `sessions/YYYY-MM-DD-HHMM.jsonl`,
one narrative file per session. The ADR-48/ADR-46 consolidation retired the Linter
profile to a deterministic engine, and **no v0.1.1 component writes per-session
summaries** — nothing in `src/` produces `system/logs/sessions/`. The substrate
(*audit memory* in
[Memory substrates — seven scoped stores, not one](memory-substrates.md)) and the
two-log decision stand; the narrative half is **v0.1.2 scope** and currently has
no tracking issue. Until it lands, the human-readable record of a session is the
Hermes session history plus the board projections below.

### The operational logs

The same directory carries the append-only operational feeds (full schemas in
[`docs/reference/telemetry.md`](../reference/telemetry.md)):

| Log | Writer | One row = |
|---|---|---|
| `board-state.jsonl` | `board_export.py` (cron) | per-lane queue-count snapshot (feeds Home's status glance) |
| `board-transitions.jsonl` | `board_export.py` | one card changing `status` / `review_status` |
| `disposition.jsonl` | `board_export.py` | accept / edit / reject per review — un-backfillable (empty until Hermes exposes the card metadata overlay) |
| `cost.jsonl` | `board_export.py` | one card's API spend at completion (same Hermes dependency) |
| `capture-intake.jsonl` | ingest MCP | one durability anchor per captured citekey |
| `patterns.jsonl` | patterns MCP | one pattern-run provenance record |
| `classify.jsonl` | classify engine | one classification proposal (audited, correctable) |
| `lint-findings.jsonl` | — | consumed by Home and the metrics aggregator, but **no producer is wired yet**: the Linter engine runs report-only (the daily `memoria-lint` cron discards its stdout) and does not append to the vault log |

`board_export.py` also projects live cards to `system/board/<task_id>.md` for the
board-state dashboard. All consumers degrade gracefully when a feed is missing.

### Fleet trust score

[`vault/.memoria/mcp/metrics_aggregate.py`](../../src/.memoria/mcp/metrics_aggregate.py)
composes a per-lane trust score for the four background lanes (librarian, writer,
peer-reviewer, engineer — no co-PI or engine lanes) from those logs — a single
0–100 number with fixed bands:

```
90+   healthy  (no action)
70–89 watch    (something slipping)
<70   act      (pause that lane's scheduled work)
```

It starts at 100 and subtracts weighted penalties (weights are Memoria's own,
tunable at the top of the file; the bands are fixed by the glossary):

| Input | Weight | Cap |
|---|---|---|
| deny rate (`denies / writes`) | 40 | — |
| failure rate (`1 − success_rate`) | 40 | — |
| retry rate | 20 | 30 |
| drift incidents | 2 each | 20 |
| secret hits | 10 each | 30 |
| accept ratio out of band (>0.9 rubber-stamping, <0.2 prompt-drift) | 10 | — |

Denials and failures are weighted hardest — a denial is the strongest signal of
injection or misconfiguration. Below 5 samples the band is downgraded to
`insufficient-data` rather than reported as a real score. Output:
`system/metrics/lane-<lane>-<period>.md` (one per lane per ISO week) plus a
`lint-verdict-<period>.md` rollup. The installer wires the weekly cron
(`memoria-metrics`, Mondays 06:30); the
[Fleet Health [placeholder]](../../src/system/dashboards/fleet-health.md) dashboard
stays a `[placeholder]` until real run-volume accrues — trust-score bands are
meaningless on sparse data
([#205](https://github.com/eranroseman/memoria-vault/issues/205)).

## Design rationale

- **Two readers, two logs.** Machine-verifiable tamper-detection and human-readable
  narrative have opposite shapes; one log optimized for both would serve neither.
  The decision survives even though the narrative half is deferred.
- **Detective, not preventive.** The hash pairing doesn't stop an out-of-band edit
  (the human owns the filesystem) — it makes one *visible*. That fits the
  single-researcher trust model: the threat is silent corruption and agent error,
  not a malicious admin.
- **One number for triage.** The trust score exists so the daily-glance can answer
  "is any lane slipping?" without reading raw logs; the underlying signals stay
  available in the fleet-health and [Audit log](../../src/system/dashboards/audit-log.md)
  dashboards.
- **Denials are load-bearing.** A spike in denials is how a prompt-injection or
  misconfigured lane shows up; the formula reflects that by weighting it top.
- **Un-backfillable feeds start on day one.** Disposition and cost trends cannot be
  reconstructed retroactively, so the exporters ship wired even where an upstream
  Hermes limitation keeps a feed empty for now.

## Related

- [ADR-25](../adr/25-session-logging-two-logs.md)
- [Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md) — the audit producer
- [Memory substrates — seven scoped stores, not one](memory-substrates.md) — audit memory as one of seven substrates
- [Dashboards — ten views, four groups, two data sources](dashboards-design.md) — `audit-log`, `fleet-health`, `drift-watch` consumers
- Reference docs: [`docs/reference/telemetry.md`](../reference/telemetry.md)
