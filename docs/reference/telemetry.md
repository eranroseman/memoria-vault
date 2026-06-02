---
title: Telemetry & logs
parent: Reference
---


# Telemetry & logs

Every signal Memoria records about its own operation, with the exact on-disk schema. All logs live under `99-system/logs/`. For the design rationale — why these particular signals and how they map to a publication — see the measurement proposal `project-files/proposals/measurement-and-verification.md` (the "six-signal log").

## Conventions (apply to every log)

- **Format.** One JSON object per line (JSONL). No top-level array, no trailing comma; a partial last line is the only acceptable corruption and is dropped on read.
- **Append-only.** Writers only ever `open(..., "a")`. Rows are immutable events; nothing is rewritten in place. Rotation (truncate-after-archive) is the *only* sanctioned mutation, and only the owning profile may do it (see the `authorized-targeted` auto-fix class in [Policy MCP](policy-mcp.md)).
- **Time.** Every row carries a timestamp in ISO-8601 **UTC** with a trailing `Z` (`2026-06-01T14:23:01Z`). The key is `timestamp` in every log. Never local time — cross-log joins depend on a single clock.
- **Identity.** Card-scoped rows carry `task_id` (board card ID) and `lane` (the assignee profile, e.g. `memoria-writer`). `task_id` is the join key across `board-transitions`, `disposition`, and `cost`.
- **Encoding.** UTF-8, `ensure_ascii=false` — em-dashes and accented author names survive verbatim.

## Log inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | policy MCP | per gated write | one `allow_with_log` / `deny` decision |
| `board-state.jsonl` | `board_export.py` | per export run | a snapshot of per-lane queue counts |
| `board-transitions.jsonl` | `board_export.py` | per export run | one card changing `status` or `review_status` |
| `disposition.jsonl` | `board_export.py` | per export run | one review reaching a terminal outcome |
| `cost.jsonl` | `board_export.py` | per export run | one card's API spend at completion |
| `lint-findings.jsonl` | `memoria-linter` | per Linter run | one detector finding |
| `sessions/<id>.jsonl` | `memoria-linter` | per Linter session | a human-readable per-session summary (one file per session, never rotated) |

Derived, not raw: `99-system/metrics/lane-<lane>-<period>.md` notes are *computed* by `metrics_aggregate.py` from the logs above; they are reference output, not a capture point. See [their schema](#derived-lane-metric-notes) below.

## audit.jsonl

The write-gate's decision trail. Schema and SHA-256 rules are owned by [Policy MCP](policy-mcp.md#audit-log-format); reproduced here for completeness:

```json
{
  "timestamp": "2026-05-31T14:23:01Z",
  "profile": "memoria-librarian",
  "action": "write",
  "path": "20-sources/01-papers/smith-2024.md",
  "task_id": "TASK-2026-05-31-003",
  "decision": "allow_with_log",
  "policy_rule": "librarian.write.sources",
  "before_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
  "after_hash":  "sha256:a87ff679a2f3e71d9181a67b7542122c..."
}
```

Only `allow_with_log` and `deny` decisions are logged. `dry_run` previews and plain `allow` (no `audit_log` requirement) write nothing.

## board-state.jsonl

A queue-depth snapshot appended once per `board_export.py` run. Counts only — no card identity — so it is safe to keep forever and cheap to plot as a time series.

```json
{
  "timestamp": "2026-06-01T09:00:00Z",
  "lanes": {
    "memoria-writer":    {"running": 1, "ready": 0, "blocked": 1, "review_queue": 2},
    "memoria-librarian": {"running": 0, "ready": 3, "blocked": 0, "review_queue": 0}
  },
  "totals": {"running": 1, "ready": 3, "blocked": 1, "review_queue": 2}
}
```

`review_queue` counts cards that are `status: done` **and** sitting in a non-terminal `review_status` (awaiting a human). A card is counted in exactly one of `running` / `ready` / `blocked`; `review_queue` is an orthogonal overlay.

## board-transitions.jsonl

The card-level state-change stream — the spine the other event logs hang off. Emitted by diffing the previous per-card state (held in `99-system/logs/.board-state-cache.json`, an internal dotfile, not a telemetry log) against the current board. **A card seen for the first time emits no transition** — it is seeded into the cache silently, so the log records only genuine movements, never the initial population.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "status", "from": "running", "to": "done"}
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "review", "from": "requested", "to": "approved"}
```

| Field | Values |
| --- | --- |
| `kind` | `status` or `review` — which axis moved |
| `from` / `to` | the prior and new value of that axis (either may be `null` on the first observed change) |

**Decision time** is computed downstream by pairing a card's `kind: review, to: requested` transition with its later terminal-review transition — the wall-clock minutes a card waited for a human.

## disposition.jsonl

The **un-backfillable** signal: what the human actually did with a finished card. Emitted when a card's `review_status` reaches a terminal outcome.

```json
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "edited", "agent_recommendation": "clean"}
```

| Field | Values |
| --- | --- |
| `disposition` | `accepted` \| `edited` \| `rejected` — the three-way human verdict |
| `agent_recommendation` | what the agent proposed (`clean` / `issues-found` / `inconclusive`); pairs the agent's self-assessment against the human's call |

The terminal mapping is: `review_status: approved → accepted`, `rejected → rejected`. A card may override the default by setting `metadata.disposition` explicitly — this is the only way to record `edited` (accepted-after-changes), which the board's `review_status` cannot express on its own. **Without `edited` you cannot distinguish "accepted as written" from "accepted after I fixed it," which is the core acceptance-quality measure for the paper — hence un-backfillable.**

## cost.jsonl

API spend and token counts, captured once, at the transition into `status: done` (cost is only final when the work is).

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "cost": 0.0142, "tokens_in": 8200, "tokens_out": 1450}
```

`cost` is USD (float); `tokens_in` / `tokens_out` are integers. Any field may be `""` (empty string) if the card never carried it — consumers must tolerate missing values rather than assume zero.

## lint-findings.jsonl

One row per detector finding from a `memoria-linter` run. The in-memory shape is the `Finding` dataclass in [`detectors.py`](../../vault/.memoria/profiles/memoria-linter/detectors.py); serialized as:

```json
{"timestamp": "2026-06-01T02:00:00Z", "detector": "fama-exposure", "severity": "HIGH", "path": "40-workbench/draft-x/01-notes/n.md", "message": "cites superseded claim [[oldclaim]]"}
```

| Field | Values |
| --- | --- |
| `timestamp` | ISO-8601 UTC; one clock per lint pass (`run_all` stamps every finding in a pass with the same time) — enables periodized rollups and 4-week trends |
| `detector` | the detector slug (`orphan-working-files`, `broken-wikilink`, `fama-exposure`, …) |
| `severity` | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `path` | vault-relative path of the offending note |
| `message` | short human-readable cause |

The per-pass `PASS` / `REVIEW` / `FAIL` verdict is computed from severities (per [Linter: detectors and auto-fix](linter.md)) and persisted **per period** as a `lint-verdict` note (below), not as a field on each finding.

## Derived: lane-metric notes

`metrics_aggregate.py` reads the logs above weekly and writes one Markdown note per lane per period to `99-system/metrics/lane-<lane>-<period>.md`. These are *output*, but their frontmatter is a stable contract:

| Field | Source | Meaning |
| --- | --- | --- |
| `trust_score` | composite | the lane's headline score |
| `accepted` / `edited` / `rejected` | `disposition.jsonl` | three-way disposition counts |
| `accept_ratio` | derived | `accepted / (accepted + edited + rejected)` |
| `decision_time_min` | `board-transitions.jsonl` | median human review latency, minutes |
| `cost` / `tokens_in` / `tokens_out` | `cost.jsonl` | period totals |
| `consistency_passk` | reserved | placeholder (`null`) for a future pass^k harness |

## Derived: lint-verdict notes

`metrics_aggregate.py` also rolls the period's `lint-findings.jsonl` into one `99-system/metrics/lint-verdict-<period>.md` note (written only once the Linter has produced a findings log). It gives the drift dashboards a periodized verdict history that the timeless findings feed can't:

| Field | Meaning |
| --- | --- |
| `type` | `lint-verdict` |
| `period` | ISO week (`2026-W22`), matching the lane-metric notes |
| `verdict` | `PASS` / `REVIEW` / `FAIL` (any `CRITICAL` → FAIL; any `HIGH`/`MEDIUM` → REVIEW; else PASS) |
| `finding_count` | total findings in the period |
| `critical_count` / `high_count` / `medium_count` / `low_count` | per-severity counts |
| `computed_at` | ISO-8601 UTC when the aggregator wrote the note |

A field with no data for the period renders as `null` (never omitted) so downstream parsers see a stable key set.

## What is *not* captured

By design, to keep v0.1's capture minimal and the consent story simple:

- **No note content** ever enters a log — only paths, IDs, counts, severities, and the human verdict.
- **No keystroke- or token-level provenance** inside a draft; cost is per-card, not per-edit.
- **No `pass^k` consistency runs** — the `consistency_passk` field exists but the harness that would populate it is deferred past v0.1.
