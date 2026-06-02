---
release: 0.1.0
status: draft
released: false
---

# Release plan — v0.1.0

**Current status: pre-release — v0.1.0 has _not_ shipped.** No `v0.1.0` tag or
GitHub release exists, and the build ledger lists nothing as `approved`. **All
three earlier P0 blockers are now closed:** #39 (obsidian bridge key delivery —
live reads/writes, Tier-4 HTTP 204, read-back OK), #51 (policy-gate capability
scope), and [#58](https://github.com/eranroseman/memoria-vault/issues/58) (the
review gate firing live). #58 was resolved by
[ADR-27](../decisions/27-hermes-native-config-and-gate-enforcement.md): the gate
read as a no-op only because the `obsidian` MCP never loaded (it shipped in a
standalone `mcp.json`, which Hermes never reads), so writes went through
`code_execution`/`file` paths the `obsidian.*` matcher couldn't cover. With
`mcp_servers` in `config.yaml` and a per-lane toolset allowlist (obsidian = the
only write path), the gate enforces live — validated in oneshot on Memoria-test.
**No open P0 remains.** [#59](https://github.com/eranroseman/memoria-vault/issues/59)
(official skills on install) is resolved — those skills are bundled with Hermes,
not hub-installed. What's left for the cut is **verification, not construction:**
dashboards (G4), telemetry cron (G5), the changelog (G8), the GUI tier (T5), and a
fresh-clone candidate re-run of the live gate across run modes (G2/T4). `released:`
flips to `true` only when every gate in §2 is `done`.

> **The core reframing.** Per [implementation-status.md](implementation-status.md),
> most artifacts are `shipped` — but its legend defines `shipped` as _in the vault,
> not verified end-to-end_. So v0.1 is overwhelmingly **built but unverified**, and
> #58 was a textbook case of the danger of stopping at `shipped`: a gate that existed
> but didn't fire (ADR-27 fixed it). The release gate is **verification, not
> construction** — turning `shipped` rows into `approved` ones (§3).

## State values

| Value | Meaning |
| --- | --- |
| **done** | Verified green. Ship-ready. |
| **in-progress** | Actively being built/wired right now. |
| **awaiting-verify** | Code/config landed; needs a live re-run to confirm (not a defect). |
| **blocked** | Cannot proceed — gated on an open issue or another row. |
| **todo** | Not yet started. |
| **deferred** | Consciously out of this release's scope. |

## 1. Scope — what this release is

The whole repo is the install unit (the bootstrap installer + the runtime
`vault/`). v0.1 is the **complete system on a single machine** (`local-only`): the
schema contract, the full vault structure, all **seven** profiles (`librarian`,
`mapper`, `socratic`, `writer`, `verifier`, `coder`, `linter`), the policy gate,
the bundled Obsidian plugins, the Kanban board, and the six-signal telemetry
capture. Density-gated automation and multi-device are later phases (see §8 and the
spillover), not v0.1 scope.

## 2. Definition of done — gates

v0.1.0 ships when **all eight gates (G1–G8) are green.**
_(Proposed gates — confirm/adjust the thresholds.)_

| Gate | State | Proves | Verified by | Issue |
| --- | --- | --- | --- | --- |
| G1 | done | Installer runs end-to-end on a clean Ubuntu/WSL2 box; all 7 profiles register | Tier 0–3 | — |
| G2 | awaiting-verify | Policy gate enforced live **in all run modes**: review-gated zones blocked, allowed pass, fail-closed on missing `task_id`. Validated live in oneshot on Memoria-test (ADR-27); needs the fresh-clone candidate re-run to confirm across gateway/cron | Tier 4 | — |
| G3 | done | An agent can read **and** write the vault through the obsidian bridge (gated-write enforcement is G2) | Tier 4 | [#39](https://github.com/eranroseman/memoria-vault/issues/39) |
| G4 | todo | All ten dashboards render on real data (Dataview queries resolve) | Tier 5 | — |
| G5 | todo | Six-signal telemetry emits once the board-export cron is wired (emitters exist; cron unwired) | Tier 4–5 + cron | — |
| G6 | done | CI green on `main`: `docs-doctor`, `shellcheck`, `PSScriptAnalyzer`, `python-selftest`, `docs-links` | CI | — |
| G7 | done | No open **P0** (release-blocking) issues (#39/#51/#58 closed; #59 resolved) | tracker | — |
| G8 | todo | `CHANGELOG.md` `[0.1.0]` entry written at cut; version `0.1.0` consistent across the 7 `distribution.yaml` | manual | — |

## 3. Validation — tiers

The tiered install-testing plan turns `shipped` rows into `approved` ones. A
release candidate must re-run **T0–T5 green from a fresh clone** on a clean
Ubuntu/WSL2 box.

| Tier | State | Proves |
| --- | --- | --- |
| T0 | done | Static: parse, LF endings, profile files present |
| T1 | done | Python `--self-test` (112/112 green: policy_mcp 34, policy_hook 32, board_export 26, metrics_aggregate 20) |
| T2 | done | Installer dry-runs (`--dry-run`), `{{VAULT_PATH}}` substitution |
| T3 | done | Real install into a throwaway vault; 7 profiles register; venv; idempotent re-run (re-confirmed from a fresh clone). **[#59](https://github.com/eranroseman/memoria-vault/issues/59) resolved:** the installer verifies the bundled official skills (present after the Hermes install) instead of hub-installing them — no 404s |
| T4 | awaiting-verify | Live: model connectivity + REST bridge **passed** (#39); **policy-gate enforcement now fires** ([#58](https://github.com/eranroseman/memoria-vault/issues/58) resolved via ADR-27, validated live in oneshot on Memoria-test). Needs the fresh-clone candidate live re-run to record green for the cut |
| T5 | todo | Obsidian + Zotero GUI: plugins load, dashboards render, Better BibTeX export |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers
are** any gate in §2 not yet `done`, plus the `pending`/`broken` rows in the build
ledger ([implementation-status.md](implementation-status.md)) and any open
**P0** issue in the [tracker](https://github.com/eranroseman/memoria-vault/issues).

**No open P0 remains** — #39, #51, and
[#58](https://github.com/eranroseman/memoria-vault/issues/58) are all closed (#58
resolved via ADR-27: the gate now fires because obsidian is each lane's only write
path). #59 is resolved (skills are bundled, not hub-installed). The remaining
blockers are the not-yet-`done` gates in §2 (G2, G4, G5, G8) and tiers in §3 (T4,
T5) — verification work, not defects.

## 5. Out of scope (deferred)

The per-artifact deferred set lives in the `deferred` rows of
[implementation-status.md](implementation-status.md) and in
[proposals/](../proposals/) — not duplicated here. At the scope level:
multi-device (Phase 4) and density-gated automation (Phase 3) are post-v0.1.

## 6. Known limitations (state in the release notes)

- **Single-user, single-device.** Multi-device sync is Phase 4.
- **Runtime is Linux/WSL2 only.** Windows is the editing surface; Hermes runs in WSL2.
- **Obsidian-on-Windows + Hermes-on-WSL2 requires WSL2 mirrored networking** (`networkingMode=mirrored`) for the REST bridge to reach `127.0.0.1:27124` (a Tier-4 finding).
- **Official skills ship bundled with Hermes**, not via the skills hub ([#59](https://github.com/eranroseman/memoria-vault/issues/59)) — the installer verifies they're present after the Hermes install rather than fetching them (a hub-install 404s by design); it warns-not-fails if any is missing.
- **`shipped` ≠ `approved`.** Most components are unverified until a release candidate re-runs Tier 0–5.

## 7. Cut procedure

1. **Every gate (§2) and tier (§3) `done`; no P0 issues open.** (No P0 open; the remaining non-`done` gates are verification: G2/T4 the fresh-clone live re-run, G4/G5/G8/T5 the dashboards/telemetry/changelog/GUI.)
2. **Re-run Tier 0–5 from a fresh clone** on a clean Ubuntu/WSL2 box → all green; record results in §3.
3. **Confirm version `0.1.0`** across the seven `distribution.yaml` (lockstep with the Memoria release version).
4. **Cut the `[0.1.0]` section in `CHANGELOG.md`:** move the `[Unreleased]` items into a dated `[0.1.0]` section and re-point the links.
5. **Flip `released: false` → `true`** in this file's frontmatter.
6. **Tag `v0.1.0`** and create the GitHub release with the curated notes (§6 limitations included).
7. **Flip the relevant `shipped` rows to `approved`** in [implementation-status.md](implementation-status.md) once the candidate passes.

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Phase 1 — Full system setup | Weeks 1–2 | Install every v0.1 component on one machine (this release). |
| Phase 2 — Seed & synthesize | Weeks 3–8 | Ingest the corpus; establish classification + claim-note rhythms against real data. |
| Phase 3 — Activate, scale, automate | Month 3+ | Turn on density-gated features; automate the edges; migrate the full corpus. |
| Phase 4 — Multi-device | When a 2nd device enters regular use | Extend to a second machine without fragmenting dispatch ownership. |

Full phase steps, exit criteria, and the week-by-week ramp:
[release-plan-v0.1-spillover.md](release-plan-v0.1-spillover.md).

## 9. Spillover

Detailed phase steps, exit criteria, and migration detail live in
[release-plan-v0.1-spillover.md](release-plan-v0.1-spillover.md). This plan
summarizes (§8) and links rather than absorbing them.
