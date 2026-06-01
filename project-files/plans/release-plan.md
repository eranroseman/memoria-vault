---
topic: plans
status: draft
---

# v0.1 release plan

**Current status: pre-release — v0.1.0 has _not_ shipped.** No `v0.1.0` tag or
GitHub release exists; the build ledger lists nothing as `approved`; and a
release-blocking bug is open ([#39](https://github.com/eranroseman/memoria-vault/issues/39)).
This document defines what "released" means, how it's validated, and how it gets
cut. It does **not** track per-artifact status or the blocker inventory — that
lives in [implementation-status.md](implementation-status.md), the single source
of truth for build state; this plan points to it rather than restating it.

> **The core reframing.** Per [implementation-status.md](implementation-status.md),
> most artifacts are `shipped` — but its own legend defines `shipped` as *in the
> vault, **not** verified end-to-end*. So v0.1 is overwhelmingly **built but
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
| G8 | `CHANGELOG.md` `[0.1.0]` entry written at cut; version `0.1.0` consistent across the 7 `distribution.yaml` | manual | ⏳ changelog now under `[Unreleased]`; cut the `[0.1.0]` section at release (§7) |

## 3. Release blockers

Not enumerated here — a second list would drift from the ledger. **By definition,
the blockers are:**

- the **`pending`** and **`shipped (… broken)`** rows in
  [implementation-status.md](implementation-status.md) (the single source of truth
  for build state), plus
- any open **P0** issue in the [tracker](https://github.com/eranroseman/memoria-vault/issues).

Consult those two for the live, authoritative set. (At time of writing the P0 is
[#39](https://github.com/eranroseman/memoria-vault/issues/39) — obsidian bridge
key delivery, gate G3.)

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

The per-artifact deferred set lives in the `deferred` rows of
[implementation-status.md](implementation-status.md) and in [proposals/](../proposals/) —
not duplicated here. At the scope level: multi-device (Phase 4) and density-gated
automation (Phase 3) are post-v0.1.

## 6. Known limitations to state in the release notes

- **Single-user, single-device.** Multi-device sync is Phase 4.
- **Runtime is Linux/WSL2 only.** Windows is the editing surface; Hermes runs in WSL2.
- **Obsidian-on-Windows + Hermes-on-WSL2 requires WSL2 mirrored networking** (`networkingMode=mirrored`) for the REST bridge to reach `127.0.0.1:27124` — a Tier-4 finding; document it in setup.
- **`shipped` ≠ `approved`.** Most components are unverified until a release candidate re-runs Tier 0–5.

## 7. Cut procedure

1. **All §2 gates green; no P0 issues open** (currently: #39 blocks).
2. **Re-run Tier 0–5 from a fresh clone** on a clean Ubuntu/WSL2 box → all green.
3. **Confirm version `0.1.0`** across the seven `distribution.yaml` (lockstep with the Memoria release version).
4. **Cut the `[0.1.0]` section in `CHANGELOG.md`:** move the `[Unreleased]` items into a dated `[0.1.0]` section and re-point the links. (The earlier fictional `[0.1.0]` entry was already removed; the changelog now accumulates under `[Unreleased]`.)
5. **Tag `v0.1.0`** and create the GitHub release with the curated notes (§6 limitations included).
6. **Flip the relevant `shipped` rows to `approved`** in [implementation-status.md](implementation-status.md) once the candidate passes.
