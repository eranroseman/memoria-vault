---
topic: releases
title: v0.1 validation log
parent: 0.1.0
grand_parent: Releasing
nav_order: 9
---

# v0.1 validation log

> **Frozen record.** Captures v0.1.0-alpha.1 as tested; terminology (e.g. seven profiles, numbered folders) reflects that point in time and is not current. See current docs for present-day naming.

The **evidence** behind v0.1 gate sign-off: what has actually been exercised, by
what method, with what result. Gate/stage *readiness* status lives in
[Release plan — v0.1.0-alpha.1](release-plan-0.1.0.md) §2/§3; build *gaps* are
[GitHub issues](https://github.com/eranroseman/memoria-vault/issues). This log is the
detail those point at. Distilled from the retired build ledger on retirement; the
blow-by-blow remains in git history.

All "verified" entries are against a **live Hermes on WSL2** unless noted.

## Write gate & control plane

- **obsidian MCP write bridge — verified** (2026-06-01, Hermes v0.14.0). A
  `memoria-writer` run wrote `10-inbox/02-answers/…` through `uvx mcp-obsidian`
  (Local REST API :27124): HTTP 204, file on disk, read back OK. The earlier 401 was
  root-caused — Hermes profile runs read only the profile's own `.env`, and the key
  sat only in the global `.env`; fixed by the installer's `seed_profile_env`.
  ([#39](https://github.com/eranroseman/memoria-vault/issues/39) resolved.)
- **Policy write-gate (ADR-28 plugin) — verified live** (librarian + writer,
  `hermes -z`): allowed write → `allow` + `write_complete`; review-gated/denied write
  → blocked, no file on disk, no filesystem fallback; simulated policy outage → fails
  **closed**. The retired shell-hook never fired on live writes (`re.fullmatch` vs the
  registered `mcp_obsidian_…` tool name).
  ([#51](https://github.com/eranroseman/memoria-vault/issues/51),
  [#58](https://github.com/eranroseman/memoria-vault/issues/58) resolved.)
- **Decision cores — self-tests green:** `policy_mcp.py` (34 + 32 checks) and
  `policy_hook.py` (file-toolset gating + pre→post roundtrip) — the Phase-1 gate.
  `--decide` one-shots pass against all 7 lane-overrides.
- *Unverified:* HTTPS self-signed cert handling; per-profile read-only `tools`
  filters; web/browser capability enforcement beyond the terminal/file split.

## Installer (`scripts/install.sh`)

- **Tier-3 verified:** `bash -n` clean; full install `EXIT=0`; all 7 profiles register
  at 0.1.0; `agent.disabled_toolsets: [terminal, file]` lands typed correctly on the 5
  non-terminal lanes; idempotent `--profiles-only` re-run clean.
- **Env-key seeding (Tier-4) verified:** `memoria-mapper` runs with no manual `.env`
  editing after a clean install.
- *Open findings:* two official skills fail to fetch (`ocr-and-documents`,
  `github-repo-management`) — installer warns, doesn't fail; `scripts/install.ps1` not
  yet run end-to-end against a live WSL2.

## Ingest + lifecycle loop (G9 / G10 / G11)

- **Proven live end-to-end** ([#100–#123](https://github.com/eranroseman/memoria-vault/issues)):
  a real paper ran dispatch → ingest (Tier-0/1) → classify + `[!brief]` → gated write →
  `review_status: requested` → human-promote → `lifecycle: current`, on
  installer-deployed lanes.
- All ADR-30 pipeline scripts pass `--self-test`; delivered as the `ingest_pipeline`
  MCP tool ([#110](https://github.com/eranroseman/memoria-vault/issues/110)).
- *Unverified:* Tier-1 correctness — multi-source merge (R2-1) and tag precision
  (R2-4) — the spike that gate **G10** requires before reliance.

## Deterministic detectors & telemetry

- `detectors.py` — `--self-test` 15/15 (9 zero-LLM checks).
- `board_export.py` — `--self-test` 26 checks; cron wired (G5), validated live (forced
  tick → fresh `board-state.jsonl`).
- `metrics_aggregate.py` — `--self-test` 20 checks. Cron **deferred to Phase 3** (needs
  run-volume — [#205](https://github.com/eranroseman/memoria-vault/issues/205)).

## Still unverified at large (→ gates / runs)

- GUI / dashboards (11) / Zotero bridge / ACP pane: attended per release (S5, G4) — see
  the [GUI run record](gui-test-run_0.1.0.md).
- Full clean-install candidate run from a fresh clone (G2 / S4) — see the
  [release-candidate runbook](../../testing/plans/release-candidate-runbook.md).
