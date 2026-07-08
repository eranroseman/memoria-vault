---
title: System action scheduled tasks
parent: Commands and transports
nav_order: 5
grand_parent: Reference
---

# System action scheduled tasks

Optional scheduled jobs wrap the CLI/runtime package. They are operator wiring,
not a separate product authority. For the guarded operation ID list, see
[System actions](system-actions.md).

## Scheduled tasks (`.memoria/scripts/`)

The deterministic scheduled jobs are optional operator wiring around the CLI and
runtime package. `.memoria/scripts/cron-runner.sh` dispatches `worker`, `lint`,
`eval`, and `retraction-refresh`. No scheduler is required for a one-shot CLI
workflow; a systemd timer, cron entry, launchd job, or another local scheduler
can call the runner when always-on maintenance is desired.
