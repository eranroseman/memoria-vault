---
title: Diagnostics
parent: Pipelines and I/O
grand_parent: Reference
---

# Diagnostics

Local troubleshooting records for Memoria-owned Python MCP servers and Operations. These records are not audit memory and never live under the vault or `system/logs/`.

## Contract

| Item | Contract |
| --- | --- |
| Default location | `$XDG_STATE_HOME/memoria/diagnostics/`, or `~/.local/state/memoria/diagnostics/` when `XDG_STATE_HOME` is unset |
| Override | `MEMORIA_DIAGNOSTICS_DIR`, still rejected when a caller supplies a vault path and the target is inside that vault |
| File pattern | `diagnostics-YYYY-MM-DD.jsonl`, rotated to bounded `.gz` backups |
| Default level | `warn` and `error`; raise with `MEMORIA_DIAGNOSTIC_LEVEL` or `MEMORIA_DIAGNOSTIC_LEVEL_<COMPONENT>` |
| Default content | typed `code`, `component`, `level`, timestamp, payload SHA-256, payload byte length, and content-light details |
| Raw capture | one process only with `MEMORIA_DIAGNOSTIC_RAW_ONCE=1`; the flag is consumed after one event and stored only as redacted text |
| Bundle command | `python -m memoria_vault.runtime.diagnostics --bundle ~/memoria-diagnostics.tgz` |
| Redaction self-test | `python -m memoria_vault.runtime.diagnostics --self-test` |

Diagnostic detail fields hash strings and paths instead of writing them verbatim.
The user-triggered bundle is a compressed archive with a README and redacted JSONL
files; review it before sharing. Use `--include-raw` only when a one-shot raw
capture was deliberately enabled and the redacted payload is needed for support.

## Related

- Operational telemetry inventory: [Telemetry & logs](telemetry.md)
- Log schemas: [Telemetry log schemas](telemetry-logs.md)
