---
topic: explorations
title: Session logging and audit — two logs, tamper-evidence, fleet trust
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 23
---

# Session logging and audit — two logs, tamper-evidence, fleet trust

A design capture of how Memoria records what its agents did: the hash-chained policy
audit log, the per-session narrative summaries, and the fleet trust-score that rolls
them up. Reconstructed from [`vault/.memoria/mcp/`](../../src/.memoria/mcp) and
the dashboards. Implements [ADR-25](../adr/25-session-logging-two-logs.md); the
audit half is produced by the engine described in
[Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md).

> **Why capture this.** ADR-25 decides *that* there are two logs; this is the
> as-built view of their schemas, the hash-chain mechanism, and the trust-score
> formula — none of which lived in an exploration before.

## What it is

Two separate logs in `99-system/logs/`, written by different components for
different readers:

- **`audit.jsonl`** — the policy MCP's terse, append-only, SHA-256-chained record of
  every write decision. Built for tamper-detection and querying, not reading.
- **`sessions/YYYY-MM-DD-HHMM.jsonl`** — the Linter's per-session narrative summary
  of Hermes activity. One file per session, never rotated, accumulating indefinitely.
  Built for humans.

Keeping them apart is the decision: mixing narrative into the audit log would make it
verbose and harder to verify; mixing per-write events into summaries would make them
unreadable.

## How it works

### The audit log

`policy_mcp.py` appends one JSON object per decision (`append_audit`). Schema:

```
timestamp · profile · action · path · task_id · decision · policy_rule
            · reason?            (when a rule carries one)
            · before_hash?       (mutating actions)
            · after_hash?        (null at pre-check; filled by write_complete)
```

Every allowed mutating write produces **two** records: the decision (with
`before_hash`, `after_hash: null`) and a later `write_complete` record carrying both
hashes. Hashes are `sha256:<hex>`; a not-yet-existing file hashes as the digest of
the empty byte string — the `before_hash` of a create is never null.

**Tamper-evidence, not tamper-prevention.** The chain is the invariant that each
path's latest `after_hash` equals the file's current SHA-256. The Linter's
`vault-hash-drift` detector (CRITICAL severity) walks the log and flags any path
whose current hash diverges from its last recorded `after_hash`. Editing a gated
file out-of-band, or rewriting history, breaks the chain and is caught after the
fact. The log is rotated weekly by the Linter.

### The session summaries

The Linter writes `sessions/YYYY-MM-DD-HHMM.jsonl`, one per session, summarizing
Hermes raw activity into a narrative record rather than per-write events. These are
never rotated — the long-horizon trail. (This substrate is *audit memory* in
[Memory substrates — seven scoped stores, not one](memory-substrates.md).)

Adjacent operational logs in the same directory feed the dashboards:
`lint-findings.jsonl`, `disposition.jsonl` (accept / edit / reject per review),
`cost.jsonl`, `board-transitions.jsonl`, and `cron-history.jsonl`.

### Fleet trust score

[`vault/.memoria/mcp/metrics_aggregate.py`](../../src/.memoria/mcp/metrics_aggregate.py)
composes a per-lane trust score (`trust_score`) from those logs — a single 0–100
number with fixed bands:

```
90+  healthy   (no action)
70–89 watch    (something slipping)
<70   act       (pause that lane's scheduled work)
```

It starts at 100 and subtracts weighted penalties:

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
`insufficient-data` rather than reported as a real score.

## Design rationale

- **Two readers, two logs.** Machine-verifiable tamper-detection and human-readable
  narrative have opposite shapes; one log optimized for both would serve neither.
- **Detective, not preventive.** The hash chain doesn't stop an out-of-band edit (the
  human owns the filesystem) — it makes one *visible*. That fits the single-researcher
  trust model: the threat is silent corruption and agent error, not a malicious admin.
- **One number for triage.** The trust score exists so the daily-glance can answer
  "is any lane slipping?" without reading raw logs; the underlying signals stay
  available in [Fleet Health [placeholder]](../../src/00-meta/01-dashboards/fleet-health.md)
  and [Audit log](../../src/00-meta/01-dashboards/audit-log.md).
- **Denials are load-bearing.** A spike in denials is how a prompt-injection or
  misconfigured lane shows up; the formula reflects that by weighting it top.

## Related

- [ADR-25](../adr/25-session-logging-two-logs.md)
- [Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md) — the audit producer
- [Memory substrates — seven scoped stores, not one](memory-substrates.md) — audit memory as one of seven substrates
- [Dashboards — eleven views, four groups, two data sources](dashboards-design.md) — `audit-log`, `fleet-health`, `drift-watch` consumers
- Reference docs: [`docs/reference/telemetry.md`](../reference/telemetry.md)
