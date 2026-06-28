---
release: 0.1.0-alpha.2
status: draft
released: false
title: Release plan — v0.1.0-alpha.2
parent: 0.1.0-alpha.2
grand_parent: Releasing
nav_order: 2
---

# Release plan — v0.1.0-alpha.2

**Internal checkpoint (draft).** alpha.2 is the **consolidation checkpoint** — an internal
milestone, **not a formal, published release**: there is no tag, no GitHub Release, and
`released:` stays `false` for every alpha. It marks where the seven-profile, numbered-folder,
three-layer model of alpha.1 is replaced by five posture-defined profiles, type-first folders,
and the seven-layer stack, all built on deterministic engines behind the policy gate. The
checkpoint is *reached* when every gate in §2 is green on `main` via a fresh-clone candidate
run (S0–S5).

## 1. Scope — what this release is

alpha.2 delivers the **consolidated system**: one conversational Co-PI plus four background
lanes (librarian, writer, peer-reviewer, engineer) — five profiles, down from seven
([ADR-48](../../adr/48-copi-and-agent-consolidation.md)); the seven-layer architecture
PI · Interface · Co-PI · Tasks · MCP · Engines · Vault
([ADR-46](../../adr/46-seven-layer-architecture.md)); type-first category folders
`catalog/ notes/ projects/ inbox/ system/` ([ADR-47](../../adr/47-type-first-category-folders.md));
deterministic ingest / linter / sweeps **engines** that write while agents judge
([ADR-57](../../adr/57-engines-write-agents-judge.md)); the policy-gate Hermes plugin
([ADR-28](../../adr/28-write-gate-as-plugin.md)) over the native Obsidian MCP
([ADR-31](../../adr/31-native-obsidian-mcp.md)); twelve Bases-backed dashboards
([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)); and the Desk / Library / Studio
workspaces with the `home.md` control panel ([ADR-68](../../adr/68-workspaces-desk-library-studio.md)).
It is **not** the Project-workspace checkpoint: `projects/` ships empty, and the full Writer /
Peer-reviewer / Engineer project workflows arrive in alpha.4 (alpha.3 is a UI-build checkpoint).

## 2. Definition of done — gates

v0.1.0-alpha.2 is complete when **every gate sub-issue under the Release
v0.1.0-alpha.2 parent issue is closed** (issue: open per [Releasing](../README.md)).
Definitions — state lives in the sub-issues, never a column here:

| Gate | Proves | Verified by |
| --- | --- | --- |
| G1 | Installer runs clean on Ubuntu/WSL2 from `src/`; all **five** profiles register; the golden copy is staged; idempotent re-run | S0–S3 · [Installer test plan](../../testing/plans/package-gate.md) |
| G2 | The agent spine runs live: dispatch → claim → run → gated write → audit → `done`, with no human-review step | [G9 spine plan](../../testing/plans/product-gate.md) |
| G3 | The ingest value loop: capture → ingest → Tier-1 enrich → classify → gated write → a correct `proposed` paper entity | [G10 ingest plan](../../testing/plans/product-gate.md) |
| G4 | All **twelve** dashboards render on real data (every Dataview / Bases query resolves) | S5 · [GUI test plan](../../testing/plans/manual-gui-checks.md) Part C |
| G5 | Telemetry signals emit live (board-state, transitions, audit, lint-findings) | [Release-candidate runbook](../../testing/plans/release-gate.md) |
| G6 | The review loop closes: a card flows `ready → running → done (awaiting review) → approved → current`; the gate holds at the review boundary | [Golden-path plan](../../testing/plans/product-gate.md) |
| G7 | Workspaces load (Desk / Library / Studio) and the `home.md` control panel + command Buttons work ([ADR-68](../../adr/68-workspaces-desk-library-studio.md)) | S5 · [GUI test plan](../../testing/plans/manual-gui-checks.md) |

## 3. Validation — stages

The staged test plan that turns built artifacts into verified ones. A candidate re-runs
**all stages green from a fresh clone** on a clean target box (track the runs in the
relevant gate/stage sub-issues).

| Stage | Proves |
| --- | --- |
| S0 | Static: parse, schema-correctness, docs link/title integrity ([Headless test plan](../../testing/plans/source-gate.md) Parts B/C/E) |
| S1 | Pytest component suite — policy, hook, board-export, metrics, detectors ([Headless test plan](../../testing/plans/source-gate.md) Part A) |
| S2 | Agent wiring + per-lane policy-gate enforcement ([Hermes CLI test plan](../../testing/plans/runtime-gate.md)) |
| S3 | Real install into a throwaway vault; profiles register; idempotent re-run ([Installer test plan](../../testing/plans/package-gate.md)) |
| S4 | Live connectivity + gate enforcement (Obsidian MCP round-trip; a denied write is blocked and audited) |
| S5 | End-to-end + GUI: dashboards render, the golden path traverses, Zotero export ([GUI test plan](../../testing/plans/manual-gui-checks.md) + [Golden-path plan](../../testing/plans/product-gate.md)) |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers are** any open
gate/stage sub-issue, plus any open High-priority blocker in Memoria Issue Tracker.

## 5. Out of scope (deferred)

The **Project workspace** and the full compose / draft / verify / code project workflows
(alpha.4) — `projects/` ships empty this checkpoint. The per-artifact deferred set lives in the
deferred-status ADRs in [Decision records](../../adr/README.md): the cluster MCP
implementation ([ADR-33](../../adr/33-cluster-mcp-bertopic.md)), the nightly discovery loop
([ADR-61](../../adr/61-nightly-discovery-loop.md)), multi-machine
([ADR-63](../../adr/63-multi-machine-deployment.md)) and native-Windows
([ADR-64](../../adr/64-native-windows-support.md)) support, and the retrieval / schema
extensions ([ADR-65](../../adr/65-retrieval-and-schema-extensions.md)).

## 6. Known limitations (state in the release notes)

- No installable release is cut yet — release automation is paused and the release-please
  manifest stays at `0.0.0` until the first real cut (see `CHANGELOG.md`).
- `projects/` ships empty; the Project workspace and its agent workflows arrive in alpha.4.
- The cluster MCP (BERTopic topic modelling) is a tracked follow-up — the graph / canvas
  tools work without it; `cluster_model_topics` errors cleanly when the optional stack is absent.
- `fleet-health` is a prose placeholder until the observability aggregator lands.
- The messaging gateway (out-of-band CRITICAL push) is deferred; CRITICAL surfaces on Home.

## 7. Reaching the checkpoint

alpha.2 is an **internal checkpoint, not a formal release** — there is no release-please cut,
version tag, or GitHub Release. The checkpoint is reached when:

1. Every gate + stage sub-issue under "Release v0.1.0-alpha.2" is closed; required CI is green on `main`; no open High-priority blocker.
2. All stages re-run green from a fresh clone on a clean target box.
3. The ADRs are retire-swept ([retirement criteria](../../adr/README.md)) as their own small PR.

Record it by setting `status: complete` and noting the date here; `released:` stays `false`
(alphas are never formally released). Close the milestone and release parent issue, rolling
unfinished issues forward to alpha.3. The first **formal** release — a release-please tag and
GitHub Release — is the beta (§8).

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| v0.1.0-alpha.3 | next | **UI build** — resolve the Obsidian UX issues surfaced reviewing alpha.2 (command / ribbon access, capture forms, workspace panes, dashboard discoverability) before layering on project functionality |
| v0.1.0-alpha.4 | after | The **Project workspace** — Writer / Peer-reviewer / Engineer compose, draft, verify, and code workflows over `projects/` |
| v0.1.0 (beta) | later | First **formally released** version — release-please tag + GitHub Release; release automation un-paused |

## 9. Appendix

No appendix yet. Long-form per-phase steps or investigation notes, if they become needed,
live in a sibling `release-plan-0.1.0-alpha.2-appendix.md` that this plan links to rather
than absorbing.
