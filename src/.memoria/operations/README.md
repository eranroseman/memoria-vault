# Operations

Deterministic runtime processors live here. They may read canonical schemas from
`../schemas/` and share implementation helpers through `lib/`; they must not
redefine profile permissions or bypass the policy gate for vault writes.

- `processing/ingest/` owns capture, extraction, resolution, and linking.
- `integrity/linter/` owns schema/content diagnostics, golden restore, and commit checks.
- `integrity/retraction/` owns retraction lookup and alerting.
- `cleanup/` owns deterministic recovery and reconciliation jobs.
- `telemetry/eval/` owns vault-eval dispatch and scoring.
- `lib/` contains cross-operation schema and Inbox-card primitives.

Add focused tests under `tests/` for each behavior change. A new cross-operation
contract belongs in `lib/` only when at least two operations genuinely consume it.
