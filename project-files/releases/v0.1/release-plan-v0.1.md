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
review gate firing live). #58 took two passes:
[ADR-27](../../decisions/27-hermes-native-config-and-gate-enforcement.md) loaded the
`obsidian` MCP and locked each lane to obsidian-only writes, and
[ADR-28](../../decisions/28-write-gate-as-plugin.md) replaced the never-firing shell
hook with a Python plugin — the shell hook's `obsidian.*` `re.fullmatch` never
matched Hermes' real `mcp_obsidian_*` tool name (and shell hooks are consent-gated
+ fail-open). The gate now **enforces live**: validated in `hermes -z` on
installer-deployed lanes (allowed write logs `allow`+`write_complete`; denied write
blocked, no file; simulated policy outage fails closed).
[#59](https://github.com/eranroseman/memoria-vault/issues/59)
(official skills on install) is resolved — those skills are bundled with Hermes,
not hub-installed. **No open P0 remains in the tracker — but what's left for the cut
is not only verification; part of it is the product itself.** The *infrastructure*
(installer, gate, bridge, dashboards, telemetry, CI) is built and largely verified —
the remaining infra work is re-runs: dashboards (G4), telemetry cron (G5), the
changelog (G8), the GUI tier (T5), and a fresh-clone re-run of the live gate (G2/T4).
**Operability is now built and proven live:** the deterministic ingest pipeline
([ADR-30](../../decisions/30-deterministic-ingest-pipeline.md), #100–#116) ran a real
paper end-to-end on installer-deployed lanes — dispatch → `ingest_pipeline` MCP tool →
vocabulary-constrained classify + `[!brief]` → ID-keyed entity links → gated writes →
`review_status: requested`. What remains for operability is the fresh-clone candidate
re-run and closing the **human** half of the review loop (G11). This plan therefore
separates two kinds of done — the infrastructure **floor** (§2, G1–G8) and the
**operability** gates that prove a workflow actually runs (§2, G9–G11) — with the bar
and critical path detailed in the
[shippability assessment](shippability-assessment-2026-06-03.md). `released:` flips to
`true` only when **every** gate, floor and operability, is `done`.

> **The core reframing.** Most of v0.1 is **built but not verified end-to-end** —
> present in the vault, but never exercised against a live Hermes. So v0.1 is
> overwhelmingly **built but unverified**, and
> #58 was a textbook case of the danger of stopping at `shipped`: a gate that existed
> but didn't fire (it took ADR-27 _and_ the ADR-28 plugin to actually fire it).
> **But "verify what's built" is only half the gate.** The other half is
> **operability**: the command/invocation surface that lets an agent actually run a
> workflow. The **ingest value loop (ADR-30) is now built and ran end-to-end live**
> (#100–#116) — vocabulary-constrained classify + `[!brief]` + gated multi-writes
> through the `ingest_pipeline` MCP tool; what remains is the fresh-clone re-run and
> the human review-approval half (G11). So the release gate is **both** — turn
> `shipped` infrastructure into `approved` (§2 G1–G8, §3), **and** record the operable
> workflow green from a candidate (§2 G9–G11). Shipping on green plumbing alone would
> ship zero proven research value.

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

**Operability bar (what "shippable" means).** The bundle above is what *installs*;
it is not what makes v0.1 *usable*. v0.1 is shippable when **one agent workflow runs
end-to-end — through a real trigger, gated, audited, queued for human review — on the
hand-usable vault scaffold.** Not seven polished agents; one *operable, verified loop*
plus the scaffold underneath it. The seven profiles are *configured*; one workflow must
be *operable*. See the [shippability assessment](shippability-assessment-2026-06-03.md)
for the bar and its dependency-ordered critical path.

## 2. Definition of done — gates

v0.1.0 ships when **both gate groups are green** — the infrastructure floor (G1–G8)
**and** the operability gates (G9–G11). The floor proves the plumbing; the operability
gates prove a workflow actually runs on it. **Green plumbing alone is not a release.**
_(Proposed gates — confirm/adjust the thresholds.)_

### Infrastructure gates (G1–G8) — the floor

| Gate | State | Proves | Verified by | Issue |
| --- | --- | --- | --- | --- |
| G1 | done | Installer runs end-to-end on a clean Ubuntu/WSL2 box; all 7 profiles register | Tier 0–3 | — |
| G2 | awaiting-verify | Policy gate enforced live **in all run modes**: review-gated zones blocked, allowed pass, fail-closed. Now enforced by the `memoria-policy-gate` plugin (ADR-28), validated live in **`-z`, gateway (api_server), and cron** on installer-deployed lanes (librarian+writer): allowed pass, denied/`dry_run` blocked no-file, fail-closed on policy outage. Only the fresh-clone candidate re-run remains for the cut | Tier 4 | — |
| G3 | done | An agent can read **and** write the vault through the obsidian bridge (gated-write enforcement is G2) | Tier 4 | [#39](https://github.com/eranroseman/memoria-vault/issues/39) |
| G4 | awaiting-verify | All **eleven** dashboards render on real data (Dataview queries resolve) — run [gui-test-protocol.md](../../tests/protocols/gui-test-protocol.md) Part C. A GUI run **was recorded** ([gui-test-protocol_v0.1.md](gui-test-protocol_v0.1.md) Part C ticks all eleven), but the run is **PARTIAL** — its Results table is not yet fully filled in, so this is not a clean pass; a complete re-run is still needed for the cut | Tier 5 | — |
| G5 | awaiting-verify | Six-signal telemetry — **four signals working live; two gated on an upstream Hermes change**. The board-export cron is wired (installer `wire_telemetry_cron`, `--no-agent`, 1-min) and validated against real ingest-card activity: `board-state` (snapshots), `board-transitions` (status changes), audit deny-reasons (policy gate), and Linter FAMA all emit. `disposition` + `cost` **cannot emit on the current Hermes**: `board_export.py` reads them from the card `metadata` overlay (`review_status`/`cost`/`tokens`), which this Hermes version does not surface in its serialized card JSON (verified — a card driven to `review_status: approved` logged a status transition but no disposition row). The exporter is correct and ready to consume both the instant Hermes exposes the overlay; tracked as a known limitation (§6). Only the fresh-clone candidate re-run of the four working signals remains | Tier 4–5 + cron | — |
| G6 | done | CI green on `main`: `docs-doctor`, `shellcheck`, `PSScriptAnalyzer`, `python-selftest`, `docs-links` | CI | — |
| G7 | done | No open **P0** (release-blocking) issues (#39/#51/#58 closed; #59 resolved) | tracker | — |
| G8 | todo | `CHANGELOG.md` `[0.1.0]` entry written at cut; version `0.1.0` consistent across the 7 `distribution.yaml` | manual | — |

### Operability gates (G9–G11) — the product (the real release blockers)

These prove an agent completes real work end-to-end, not that components exist. Sourced from the [shippability assessment](shippability-assessment-2026-06-03.md) Gates 1–3 — the dependency-ordered critical path. **These are the substantive distance to a shippable cut.**

| Gate | State | Proves | Verified by | Issue |
| --- | --- | --- | --- | --- |
| G9 | awaiting-verify | **Deterministic spine.** The dispatch → claim → run → gated write → audit → `done` loop is now **proven live** — the G10 ingest card completed it end-to-end on installer-deployed lanes. The dedicated zero-LLM run (Linter/Verifier, per the protocol) and the fresh-clone candidate re-run remain to record it cleanly | [G9 protocol](../../tests/protocols/g9-spine-protocol.md) | — |
| G10 | awaiting-verify | **Ingest value loop** (the product) — **built and proven live.** A real paper ingested end-to-end on installer-deployed lanes: dispatch → `ingest_pipeline` MCP tool (Tier-0 capture + Tier-1 S2+OpenAlex+Crossref merge / extract / link) → the two LLM judgments (classify constrained to `vocabulary.md`; the comparative `[!brief]`) → gated multi-writes (paper-note + ID-keyed entity notes) → `lifecycle: proposed`, `ingest_status: complete`, `review_status: requested`. Delivered #100–#116 — the pipeline is reached as an **MCP tool** (#110, because the Librarian's allowlist disables `code_execution`), with 429-retry + capture-intake robustness (#114) and the re-ingest sweeps on cron (#116). The Tier-1 merge is grounded by the 867-paper spike. Only the fresh-clone candidate re-run remains; **ADR-30 is implemented — mark it `accepted`** | [G10 protocol](../../tests/protocols/g10-ingest-protocol.md) | — |
| G11 | awaiting-verify | **Review loop closes — proven end-to-end.** The G10 ingest card reached `done` + `review_status: requested`; a human review then promoted `_proposed_classification` into the main `study_design`/`methods`/`topic` fields and flipped `lifecycle: proposed → current` (proposal block removed), live on the sandbox. Only the fresh-clone candidate re-run remains | live agent run | — |

## 3. Validation — tiers

The tiered install-testing plan turns `shipped` rows into `approved` ones. A
release candidate must re-run **T0–T5 green from a fresh clone** on a clean
Ubuntu/WSL2 box. The tiers validate the **infrastructure floor**; the **operability
gates (G9–G11)** are validated by live *agent* runs — an extension of Tier 4 from
"the gate fires" to "a workflow completes" — and are tracked in §2, not duplicated
as tiers here.

| Tier | State | Proves |
| --- | --- | --- |
| T0 | done | Static: parse, LF endings, profile files present |
| T1 | done | Python `--self-test`: all five suites green (policy_mcp, policy_hook, board_export, metrics_aggregate, detectors) |
| T2 | done | Installer dry-runs (`--dry-run`), `{{VAULT_PATH}}` substitution |
| T3 | done | Real install into a throwaway vault; 7 profiles register; venv; idempotent re-run (re-confirmed from a fresh clone of the gate candidate — the `memoria-policy-gate` plugin deploys, substitutes `{{PROFILE}}`/`{{VAULT_PATH}}` per lane, and enables for all 7). **[#59](https://github.com/eranroseman/memoria-vault/issues/59) resolved:** the installer verifies the bundled official skills (present after the Hermes install) instead of hub-installing them — no 404s |
| T4 | awaiting-verify | Live: model connectivity + REST bridge **passed** (#39); **policy-gate enforcement now fires** ([#58](https://github.com/eranroseman/memoria-vault/issues/58) resolved via ADR-27 + the ADR-28 plugin; validated live in **`-z`, gateway, and cron** on installer-deployed librarian + writer — allowed pass, denied blocked no-file, policy outage fails closed). Needs the fresh-clone candidate live re-run to record green for the cut |
| T5 | awaiting-verify | Obsidian + Zotero GUI: plugins load, dashboards render, Better BibTeX export — step-by-step in [gui-test-protocol.md](../../tests/protocols/gui-test-protocol.md) (runs on the Windows side). A GUI run **was recorded** ([gui-test-protocol_v0.1.md](gui-test-protocol_v0.1.md): the 8 plugins enabled, REST round-trip, dashboards, Zotero export, and ACP all ticked) — but it is **PARTIAL**: the Results table is not fully completed and A carries a caveat ("didn't verify the settings"), so it is not yet a clean pass; a complete re-run is needed for the cut |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers
are** any gate in §2 not yet `done`, plus any open **P0** issue in the
[tracker](https://github.com/eranroseman/memoria-vault/issues).

**No open P0 remains** — #39, #51, and
[#58](https://github.com/eranroseman/memoria-vault/issues/58) are all closed (#58
resolved via ADR-27 + the ADR-28 plugin: obsidian is each lane's only write path,
and the `memoria-policy-gate` plugin enforces on it — validated live,
installer-deployed). #59 is resolved (skills are bundled, not hub-installed).

The remaining blockers split in two:
- **Infrastructure (verification, not defects):** the not-yet-`done` floor gates (G2, G4, G5, G8) and tiers (T4, T5) — re-runs to confirm what's built.
- **Operability (retired, pending only the candidate re-run):** **G9** (spine), **G10** (ingest value loop), and **G11** (review loop) are all **built and proven live** — a real paper ran the full dispatch → ingest → classify + `[!brief]` → gated write → `review_status: requested` → **human-promote → `lifecycle: current`** loop end-to-end on installer-deployed lanes (#100–#123). All that remains is recording them green from the fresh-clone candidate (with G2/T4). The substantive construction risk the [shippability assessment](shippability-assessment-2026-06-03.md) flagged is resolved. Evidence per subsystem: [validation-log.md](validation-log.md).

## 5. Out of scope (deferred)

The deferred set lives in [proposals/](../../proposals/) — not duplicated here. At
the scope level:
multi-device (Phase 4) and density-gated automation (Phase 3) are post-v0.1.

**Cut from the first operable slice** — what keeps "ship one loop" (G9–G11) tractable. None blocks a defensible v0.1; re-open each once a workflow ships:

- The **ACP-pane interactive surface** for Mapper/Writer/Verifier — and therefore the **session-skill / pane-readonly hardening** (the ephemeral-engine + unwired `set_session_skill` gap found this session). The pane isn't advertised in v0.1; a dispatched-only slice doesn't need it.
- The **other six agents' full command sets** — prove one workflow, not seven.
- **ADR-30 Tier 2** (NLI contradiction, KeyBERT) and heavy NLP. _(The comparative `[!brief]` was **not** cut — it shipped as the second hole of the loop.)_
- **Multi-source merge** was **not** cut after all — the S2 + OpenAlex + Crossref per-field best-source merge (reference union deduped by DOI) shipped, grounded by the 867-paper spike. _(Originally planned as single-source-with-fallback.)_
- **API-POST capture transport** — the script/CLI/QuickAdd front-end ships first.

## 6. Known limitations (state in the release notes)

- **Single-user, single-device.** Multi-device sync is Phase 4.
- **Runtime is Linux/WSL2 only.** Windows is the editing surface; Hermes runs in WSL2.
- **Obsidian-on-Windows + Hermes-on-WSL2 requires WSL2 mirrored networking** (`networkingMode=mirrored`) for the REST bridge to reach `127.0.0.1:27124` (a Tier-4 finding).
- **Official skills ship bundled with Hermes**, not via the skills hub ([#59](https://github.com/eranroseman/memoria-vault/issues/59)) — the installer verifies they're present after the Hermes install rather than fetching them (a hub-install 404s by design); it warns-not-fails if any is missing.
- **Per-card `disposition` and `cost` telemetry await an upstream Hermes change.** Two of the six signals read the card `metadata` overlay (`review_status`, `cost`, `tokens`), which the current Hermes does not surface in its serialized card JSON — so `disposition.jsonl` and `cost.jsonl` stay empty. The other four signals work, and `board_export.py` is wired to emit both as soon as Hermes exposes the overlay.
- **`shipped` ≠ `approved`.** Most components are unverified until a release candidate re-runs Tier 0–5.

## 7. Cut procedure

1. **Every gate (§2 — floor G1–G8 *and* operability G9–G11) and tier (§3) `done`; no P0 issues open.** The floor gates are verification (G2/T4 fresh-clone live re-run; G4/G5/G8/T5 dashboards/telemetry/changelog/GUI). The operability gates require a real workflow proven end-to-end: **G9** deterministic spine, **G10** ingest value loop, **G11** review loop closes — a release on green floor gates alone ships zero proven research value.
2. **Re-run Tier 0–5 from a fresh clone** on a clean Ubuntu/WSL2 box → all green; record results in §3. Follow the [candidate-run checklist](candidate-run-checklist.md) — the ordered T0–T5 + G9–G11 run sheet with exact commands and a per-gate sign-off table.
3. **Confirm version `0.1.0`** across the seven `distribution.yaml` (lockstep with the Memoria release version).
4. **Cut the `[0.1.0]` section in `CHANGELOG.md`:** move the `[Unreleased]` items into a dated `[0.1.0]` section and re-point the links.
5. **Flip `released: false` → `true`** in this file's frontmatter.
6. **Tag `v0.1.0`** and create the GitHub release with the curated notes (§6 limitations included).
7. **Close the `v0.1` milestone** once the candidate passes, rolling any unfinished issues to the next milestone.

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
