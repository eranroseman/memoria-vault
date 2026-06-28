---
topic: tests
title: Runtime Gate
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 30
---

# Runtime Gate

The Runtime Gate proves the live local system is wired: Hermes, profiles, MCP,
Obsidian, policy gate, model endpoint, and cron.

## Automated Prefix

```bash
scripts/verify runtime
```

This runs Source, Package, then the opt-in live Hermes smoke.

## Preconditions

- Throwaway vault installed.
- Hermes profiles registered.
- Obsidian open on the same host/filesystem as the test vault.
- Local REST API HTTPS enabled with `OBSIDIAN_MCP_PORT` and
  `OBSIDIAN_MCP_SSL_VERIFY`.
- Required profile `.env` keys present, without printing values.

## Manual Checks

| Check | Pass criteria |
| --- | --- |
| Profile registry | `hermes profile list` shows all five Memoria profiles. |
| Model endpoint | A trivial Hermes chat returns. |
| Obsidian MCP bridge | Read and write succeed over verified HTTPS. |
| Gate allow path | Allowed Obsidian write logs `allow_with_log` and `write_complete`. |
| Gate deny path | Forbidden write creates no file and logs `deny`. |
| Run modes | Gate enforcement holds in `hermes -z`, gateway, and cron. |
| Hermes drift | `python vault-template/.memoria/mcp/hermes_contract_doctor.py --vault <vault>` exits 0. |
| Cron | `hermes cron list` shows installed Memoria crons; one safe cron runs. |

## Evidence Home

Record Runtime Gate evidence in the release readiness/stage issue. Keep secrets
out of logs.
