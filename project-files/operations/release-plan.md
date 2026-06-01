---
topic: operations
status: draft
---

# v0.1 release plan

**Current status: pre-release — v0.1.0 has _not_ shipped.** Despite the
`CHANGELOG.md` `[0.1.0]` entry, nothing is released yet: the build ledger lists
*nothing* as `approved` (everything is `shipped` = built-but-unverified), and a
release-blocking bug is open ([#39](https://github.com/eranroseman/memoria-vault/issues/39)).
This document defines what "released" means, what blocks it, how it's validated,
and how it gets cut.

> **The core reframing.** [implementation-status.md](implementation-status.md)
> counts ~48 artifacts as `shipped`, but its own legend defines `shipped` as *in
> the vault, **not** verified end-to-end*. So v0.1 is overwhelmingly **built but
> unverified**. The release gate is therefore **verification, not construction** —
> turning `shipped` rows into `approved` ones. The Tier 0–5 install testing
> (`notes/install-test-checklist.md`) is that verification work.

---

## 1. Scope — what v0.1 is

The whole repo is the install unit (the bootstrap installer + the runtime
`vault/`). v0.1 is the **complete system on a single machine** (`local-only`):
the schema contract, the full vault structure, all **seven** profiles
(`librarian`, `mapper`, `socratic`, `writer`, `verifier`, `coder`, `linter`), the
policy gate, the bundled Obsidian plugins, the Kanban board, and the six-signal
telemetry capture. Density-gated automation and multi-device are later phases (see
[timeline.md](timeline.md)), not v0.1 scope.

## 2. Release criteria (definition of done)

v0.1.0 ships when **all** gates are green. Each maps to a validation tier
(§4) or an artifact in [implementation-status.md](implementation-status.md).
*(Proposed gate — confirm/adjust the thresholds.)*

| # | Gate | How it's verified | State |
| --- | --- | --- | --- |
| G1 | Installer runs end-to-end on a clean Ubuntu/WSL2 box; all 7 profiles register | Tier 0–3 | ✅ done (this session) |
| G2 | Policy gate enforced live: review-gated zones blocked, allowed zones pass, fail-closed on missing `task_id` | Tier 4 (deployed `policy_hook`) | ✅ done |
| G3 | An agent can **read and write** the vault through the obsidian bridge under the gate | Tier 4 (live model write) | ❌ **blocked by [#39](https://github.com/eranroseman/memoria-vault/issues/39)** |
| G4 | All ten dashboards render on real data (Dataview queries resolve) | Tier 5 | ⏳ not yet run |
| G5 | Six-signal telemetry emits (board-state/transitions/disposition/cost + audit + fama) once the board-export cron is wired | Tier 4–5 + cron | ⏳ partial (emitters exist; cron unwired) |
| G6 | CI green on `main`: `docs-doctor`, `shellcheck`, `PSScriptAnalyzer`, `python-selftest`, `docs-links` | CI | ✅ enforced (required checks) |
| G7 | No open **P0** (release-blocking) issues | issue tracker | ❌ #39 open |
| G8 | `CHANGELOG.md` `[0.1.0]` entry is accurate; version `0.1.0` consistent across the 7 `distribution.yaml` | manual | ⚠️ changelog entry currently wrong (see §7) |

## 3. Release blockers

**P0 — must fix before cut:**

- **[#39](https://github.com/eranroseman/memoria-vault/issues/39) — obsidian bridge never receives `OBSIDIAN_API_KEY`.** Agents can't write to the vault (G3). The policy gate and REST transport are proven; only key delivery is broken. Fix the shipped `mcp.json` ×7 + the installer.

**P1 — should fix or consciously waive:**

- **Board-export cron unwired.** `board_export.py` must run (~60 s cadence) for board markdown + telemetry to populate (G5, and dashboards that read board state). Phase-1 task in [timeline.md](timeline.md).
- **`quickadd` command surface incomplete.** 2 of ~20 catalog commands wired; the rest need QuickAdd macros + user `.js` that POST to the Hermes API.
- **Skills availability.** The lane-overrides name 28 skills; only ~7 are installable from K-Dense + the official Hermes registry today. Decide which the v0.1 profiles actually require vs. degrade-gracefully.

**Not blockers (runtime-created / optional):**

- `00-meta/02-logs/audit.jsonl` — created by the policy MCP on first logged decision; absence pre-run is expected.
- `obsidian-homepage` — recommended, optional post-clone install.

## 4. Validation plan

Formalizes the tiered install testing in `notes/install-test-checklist.md`
(currently a working note; promote a copy here when v0.1 cuts).

| Tier | What it proves | Result this session |
| --- | --- | --- |
| 0 | Static: parse, LF endings, profile files present | ✅ pass |
| 1 | Python `--self-test` (policy_mcp 34, policy_hook 18, board_export 26, metrics 20, detectors 15) | ✅ pass |
| 2 | Installer dry-runs (`--dry-run`), `{{VAULT_PATH}}` substitution | ✅ pass (fixed 4 bugs) |
| 3 | Real install into a throwaway vault; 7 profiles register; venv; idempotent re-run | ✅ pass (fixed venv + profile-install bugs) |
| 4 | Live: model connectivity, REST bridge, **policy gate enforcement** | ✅ mostly — **G3 blocked by #39** |
| 5 | Obsidian + Zotero GUI: plugins load, dashboards render, Better BibTeX export | ⏳ not yet run |

A release candidate must re-run **Tier 0–5 green** on a clean machine (the
fixes found mid-session mean the earlier tiers should be re-run from a fresh
clone before cut).

## 5. Explicitly **not** in v0.1 (deferred)

Per the `deferred` rows in [implementation-status.md](implementation-status.md):
`tasks_mcp.py` (the native Hermes Kanban covers it), `.obsidian/workspaces.json`,
the `skill-lifecycle` dashboard, the profile-compilation build step, and the
analysis harnesses in the proposals (CiteME fixture, fleet dashboard, etc.).
Multi-device (Phase 4) and density-gated automation (Phase 3) are post-v0.1.

## 6. Known limitations to state in the release notes

- **Single-user, single-device.** Multi-device sync is Phase 4.
- **Runtime is Linux/WSL2 only.** Windows is the editing surface; Hermes runs in WSL2.
- **Obsidian-on-Windows + Hermes-on-WSL2 requires WSL2 mirrored networking** (`networkingMode=mirrored`) for the REST bridge to reach `127.0.0.1:27124` — a Tier-4 finding; document it in setup.
- **`shipped` ≠ `approved`.** Most components are unverified until a release candidate re-runs Tier 0–5.

## 7. Cut procedure

1. **All §2 gates green; no P0 issues open** (currently: #39 blocks).
2. **Re-run Tier 0–5 from a fresh clone** on a clean Ubuntu/WSL2 box → all green.
3. **Confirm version `0.1.0`** across the seven `distribution.yaml` (lockstep with the Memoria release version).
4. **Rewrite the `CHANGELOG.md` `[0.1.0]` entry** to be accurate. The current entry is wrong — it lists nonexistent profiles ("researcher, developer, analyst, strategist, educator, operator") instead of the real seven, and asserts a 2026-05-25 release that didn't happen. Set the real date and contents at cut time; move the `[Unreleased]` items in.
5. **Tag `v0.1.0`** and create the GitHub release with the curated notes (§6 limitations included).
6. **Flip the relevant `shipped` rows to `approved`** in [implementation-status.md](implementation-status.md) once the candidate passes.

## 8. Snapshot

Build ledger at time of writing: **~48 shipped (unverified) · 4 pending · 3
deferred · 0 approved.** Authoritative per-artifact state lives in
[implementation-status.md](implementation-status.md); this plan tracks the gate to
turn that into a release.
