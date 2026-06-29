# alpha.12 disposable test results

Scratch: `/home/eranr/memoria-vault/scratch/releases/0.1.0-alpha.12/alpha12-fixture`

## Summary

- PASS: 4
- FAIL: 3

## Results

### FAIL: Persistence authority and crash replay

- Hash-only derived events cannot replay materialization after staging is lost.
- Replay succeeds when the derived event carries durable payloads.
- Alpha.12 must specify event payloads or durable staging retention; hashes alone are insufficient.

### FAIL: Catalog recovery from committed artifacts

- Periodic export loses Memoria-owned catalog changes made after the last export.
- Recovery is complete only when export is regenerated before the DB is lost.
- Alpha.12 needs atomic tracked export per catalog commit or a SQLite backup/snapshot rule.

### FAIL: Cross-store same-operation citation lifecycle

- A strict 'citation target must already be checked' oracle deadlocks source+digest in one operation.
- A staged-aware oracle can validate the same operation atomically.
- Alpha.12 should say citations may target checked rows or same-operation staged rows.

### PASS: Checked promotion and machine read barrier

- Machine output stays outside knowledge until checked promotion.
- PI live edit can exist in knowledge while machine consumers filter it out.

### PASS: Journal vocabulary and queue/flag projection rebuild

- requested, derived, check-fired, checked, and resolved can rebuild queue/flag/status views.
- The design should keep this full vocabulary in the journal contract.

### PASS: Canonical model with independently versioned adapters

- LLM output adapter can change without changing file or DB persistence shape.
- MCP schema is separately versioned from the LLM adapter.

### PASS: SQLite oracle and recursive rollback fixture

- UNIQUE, FK, type enum, DAG check, and recursive blast-radius query all worked.
- The blast radius spans DB and file-backed concepts via the journal projection.
