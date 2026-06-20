---
title: Telemetry architecture
parent: Architecture
nav_order: 6
---

# Telemetry architecture

This page explains *why* Memoria records what it records, and how the pieces divide
into three planes with different rules. It is the design rationale behind
[ADR-104 (telemetry three planes)](../../adr/104-telemetry-three-planes.md),
[ADR-105 (diagnostic plane)](../../adr/105-diagnostic-plane.md), and
[ADR-106 (cost and disposition capture)](../../adr/106-cost-and-disposition-capture.md).
For the exact on-disk schemas, see [Telemetry log schemas](../../reference/telemetry-logs.md);
for the audit log specifically, [Session logging](session-logging.md).

---

## Start from the questions

Telemetry exists to answer questions, and Memoria's questions fall into three groups
that pull in opposite directions:

| Plane | The question it answers | Reader | Defining requirement |
| --- | --- | --- | --- |
| **Audit** | Did this write happen, and was it authorized? | Tamper detection, dashboards, the PI | Forensic permanence, integrity |
| **Analytics** | How is the system performing — cost, throughput, my attention, decision quality? | Dashboards, the publication benchmark | Content-free, reproducible from events |
| **Diagnostic** | Why did Memoria's own code break? | The developer (the PI, debugging) | Detail now, disposable later, private |

These are not three flavors of one log. Forensic permanence wants append-only-forever;
diagnostics want rotate-and-discard. Analytics must stay content-free so it is safe to
keep and to publish; diagnostics need content to be useful. Forcing them onto one
substrate applies the strictest rule to everything and still leaves debugging unserved —
which is exactly the state Memoria was in, with a strong audit trail, a content-free
analytics family, and **no diagnostic plane at all** (failures left only a stderr print).

---

## The three planes

### Audit — forensic, integrity via Git

The audit plane is `audit.jsonl` plus its deterministic per-session digest projection
([ADR-25](../../adr/25-session-logging-two-logs.md)). It is content-free, append-only,
and records a SHA-256 before/after hash for every gated write, so a write can be reversed
and an out-of-band edit is detectable.

Its integrity substrate is **Git, not in-file cryptography.** The vault is already a Git
repository: commit history is a Merkle chain, a remote the researcher does not solely
control is a real second trust domain, and signed commits add authorship. So Memoria does
**not** add a per-entry hash chain. A linear `prev_hash` chain would *fork* the moment a
second machine appends across a sync, and anyone who owns the file can recompute it — it
adds complexity without a guarantee Git does not already provide, better. Per-write hash
pairing stays (it pins content state at finer grain than a commit). External cryptographic
anchoring (OpenTimestamps, RFC-3161) is deferred: under
[single-researcher scope](../../adr/24-single-researcher-scope.md) there is no distinct
adversary to anchor against, so it would be theater until a second party or a compliance
driver makes it real.

The honest framing: tamper-evidence here is **detective, not preventive**, and only as
strong as "a remote you do not solely control, plus you do not force-push history." Where
that remote lives (self-hosted vs. hosted) is the lever for how much activity-cadence
metadata — content-free, but it reveals *when* you work — leaves the machine.

### Analytics — content-free events, metrics as projections

The analytics plane is the operational and publication signals: board state and
transitions, disposition, cost, attention, triage, linkage, lint findings. Two principles
govern it:

- **Content-free.** Hashes, IDs, counts, enums, and durations only — never note content.
  This is what makes the plane safe to keep forever and to publish as the
  [ADR-20](../../adr/20-publication-path.md) benchmark.
- **Events are the source of truth; metrics are projections.** The lane-metric notes, the
  trust-score, and the eval trends are pure, reproducible functions over the event stream —
  never a second store. A formula change re-runs over history instead of going dark until
  new data accumulates.

It is a small set of streams grouped by writer and cadence — not one merged firehose (which
would make every reader filter and let one corrupt line poison everything) and not a file
per metric.

Two of these signals — **cost/tokens** and **disposition** — are captured at different
control points. Cost and token counts come from the per-profile Hermes session store,
joined to board cards by worker session id. Disposition is a human decision captured
at the review action, not an inference event. [ADR-106](../../adr/106-cost-and-disposition-capture.md)
records the design.

### Diagnostic — the operability plane, scoped honestly

The diagnostic plane closes the real gap: when a Memoria MCP server, ingest run, or cron
fails, there must be a persisted, queryable record. It is new, and it is the one plane that
introduces risk, so its contract ([ADR-105](../../adr/105-diagnostic-plane.md)) is strict:

- **Memoria's own Python MCP and Operations only.** Agent reasoning, prompts, and retries
  live inside the external unmodified Hermes runtime
  ([ADR-22](../../adr/22-build-on-hermes-runtime.md)) and the MCP-only sandbox
  ([ADR-46](../../adr/46-seven-layer-architecture.md)) — unreachable. The plane diagnoses
  Memoria-side failures, not whole-system behavior, and does not pretend otherwise.
- **Outside the vault, outside Git.** It lives under an OS state directory, never in the
  Git-tracked, sync-tracked vault — so a forgotten flag plus a `git push` cannot exfiltrate
  it.
- **Content-light by default.** Typed error codes plus a hash + length of any payload, never
  the payload itself; paths and titles are treated as content in anything shareable. Raw
  payloads need a deliberate, ephemeral, self-disarming capture — there is no standing
  "log content" toggle.
- **Rotated and disposable**, errors-and-warnings by default with per-component levels,
  bounded footprint.
- **No remote telemetry.** Sharing is a user-triggered, human-reviewable, redaction-tested
  bundle — never automatic.

---

## One spine, lightly

All three planes share a single event envelope (timestamp in UTC, schema version, plane,
event name, `machine`, `task_id` where a card exists) and a small emit helper per language —
not a heavyweight observability framework. There is deliberately **no** correlation-ID
propagated across processes: it cannot be threaded through the external Hermes runtime, and
at single-user local scale there is no service mesh to reconstruct. `task_id` is the join
key wherever a card exists.

---

## Multi-machine: partition, don't chain

Memoria is multi-machine single-user ([ADR-63](../../adr/63-multi-machine-deployment.md)):
the vault syncs by Git, exactly one dispatcher runs per vault, but the dispatching machine
changes over time. That sets a global invariant: **every Git-synced plane writes per-machine
files** — a `machine` stamp in the envelope and the filename — so two machines appending
across a sync never collide and Git merges stay conflict-free. This generalizes the
per-session-file naming already used for digests. The diagnostic plane is out of Git, so it
is per-machine by construction. This same property is *why* in-file hash-chaining is the
wrong integrity mechanism — a single linear chain has no conflict-free multi-writer form,
whereas Git merges do.

---

## Related

- Decisions: [ADR-104 (telemetry three planes)](../../adr/104-telemetry-three-planes.md),
  [ADR-105 (diagnostic plane)](../../adr/105-diagnostic-plane.md),
  [ADR-106 (cost and disposition capture)](../../adr/106-cost-and-disposition-capture.md)
- The audit plane in detail: [Session logging](session-logging.md)
- Exact schemas: [Telemetry log schemas](../../reference/telemetry-logs.md)
- The integrity threat model: [ADR-24 (single-researcher scope)](../../adr/24-single-researcher-scope.md)
- The sync substrate: [ADR-63 (multi-machine deployment)](../../adr/63-multi-machine-deployment.md)
