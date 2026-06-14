# Engines

Deterministic runtime processors live here. They may read canonical schemas from
`../schemas/` and share implementation helpers through `lib/`; they must not
redefine profile permissions or bypass the policy gate for vault writes.

- `ingest/` owns capture, extraction, resolution, and linking.
- `linter/` owns schema/content diagnostics, golden restore, and commit checks.
- `sweeps/` owns deterministic recovery and reconciliation jobs.
- `lib/` contains cross-engine schema and Inbox-card primitives.

Add focused tests under `tests/` for each behavior change. A new cross-engine
contract belongs in `lib/` only when at least two engines genuinely consume it.
